import streamlit as st
from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY
from .adaptive_agent import AdaptiveAgent
import random
from datetime import date, timedelta
import logging

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_student_dashboard():
    
    st.sidebar.title("Dashboard")

    # Set default selection to "Home"
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Home"

    # Full-width buttons
    if st.sidebar.button("Home", key="home_button"):
        st.session_state.selected_tab = "Home"
    
    if st.sidebar.button("Academic Test", key="academic_test_button"):
        st.session_state.selected_tab = "Academic Test"

    # Show the selected tab
    if st.session_state.selected_tab == "Home":
        show_home_page(st.session_state.user['custom_id'])  # Call the home page function
        return
    elif st.session_state.selected_tab == "Academic Test":
        show_academic_test(st.session_state.user['custom_id'])  # Call the academic test function
        return


def show_home_page(user_id):
    st.header("Welcome to Your Student Dashboard")

    # Create two columns
    col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

    with col1:
        st.subheader("Leaderboard")
        leaderboard_data = get_leaderboard_data()  # Function to fetch leaderboard data
        if leaderboard_data:
            for index, user in enumerate(leaderboard_data):
                st.write(f"{index + 1}. {user['name']} - {user['overall_progress']}%")
        else:
            st.write("No leaderboard data available.")

    with col2:
        overall_progress = calculate_overall_progress(user_id)
        
        if overall_progress > 0:
            st.progress(overall_progress / 100)
            st.write(f"Overall Progress: {overall_progress}%")
        else:
            st.info("No progress to show yet. Start your learning journey by enrolling in subjects and completing lessons!")

        badges = get_user_badges(user_id)
        st.subheader("Your Achievements")
        if badges:
            for badge in badges:
                st.write(f"{badge['icon']} {badge['name']}")
        else:
            st.write("No badges earned yet. Keep learning to earn achievements!")

        update_study_streak(user_id)
        streak = get_study_streak(user_id)
        st.write(f"Current study streak: {streak} days")

        subjects = get_student_subjects(user_id)
        if subjects:
            for subject in subjects:
                subject_name = subject.get('name', 'Unnamed Subject')  # Use a default name if 'name' is missing
                with st.expander(f"{subject_name} - Click to expand"):
                    total_lessons = supabase.table("lessons").select("id").eq("subject_id", subject['id']).execute()
                    if total_lessons.data:
                        progress = get_subject_progress(user_id, subject['id'])
                        st.progress(progress / 100)
                        st.write(f"Progress: {progress:.2f}%")
                    else:
                        st.info(f"No lessons available for {subject_name} yet. Check back soon!")

                    # skills = get_subject_skills(subject['id'])
                    # for skill in skills:
                    #     mastery_level = get_skill_mastery(user_id, skill['id'])
                    #     st.write(f"{skill['name']}: {mastery_level}")

                    recent_scores = get_recent_test_scores(user_id, subject['id'])
                    if recent_scores:
                        st.line_chart(recent_scores)

                    # study_time = get_subject_study_time(user_id, subject['id'])
                    # st.write(f"Total study time: {study_time} hours")

                    # if st.button("Start Next Lesson", key=f"next_{subject['id']}"):
                    #     start_next_lesson(user_id, subject['id'])
                    #     st.rerun()
        else:
            st.info("You're not enrolled in any subjects yet. Contact your administrator to get started!")

        current_challenge = get_current_challenge(user_id)
        st.subheader("Weekly Challenge")
        if current_challenge:
            st.write(current_challenge['description'])
            st.progress(current_challenge['progress'] / 100)
            st.write(f"Progress: {current_challenge['progress']:.2f}%")
        else:
            st.write("No active challenge available. Keep learning to unlock challenges!")

def show_academic_test(user_id):
    st.header("Academic Test")

    if 'adaptive_agent' not in st.session_state:
        st.session_state.adaptive_agent = AdaptiveAgent(user_id)

    subject = st.selectbox("Choose a subject", ["Math", "English", "Science", "History"])
    subject_id = get_subject_id(subject)

    chapters = fetch_chapters(subject)
    if not chapters:
        st.warning("No chapters available for this subject.")
        return
    chapter = st.selectbox("Choose a chapter", chapters)

    levels = {
        "Level 1": "Easy",
        "Level 2": "Medium",
        "Level 3": "Hard"
    }

    for level, difficulty in levels.items():
        with st.expander(level, expanded=True):
            if difficulty == "Medium" and not st.session_state.get('completed_Easy', False):
                st.warning("You must complete Level 1 to unlock Level 2.")
                continue
            if difficulty == "Hard" and not (st.session_state.get('completed_Easy', False) and st.session_state.get('completed_Medium', False)):
                st.warning("You must complete Level 1 and Level 2 to unlock Level 3.")
                continue

            questions = fetch_questions(subject, chapter, difficulty)
            if not questions:
                st.warning(f"No questions available for {difficulty} level in {subject}, {chapter}. Please try another selection.")
                continue

            questions = questions[:10]  # Limit to 10 questions

            if f'test_started_{difficulty}' not in st.session_state:
                if st.button(f"Start {level} Test"):
                    st.session_state[f'test_started_{difficulty}'] = True
                    st.session_state[f'question_index_{difficulty}'] = 0
                    st.session_state[f'score_{difficulty}'] = 0
                    st.session_state[f'total_questions_{difficulty}'] = len(questions)
                    st.session_state[f'current_questions_{difficulty}'] = questions
                    st.session_state[f'completed_{difficulty}'] = False
                    st.session_state[f'available_questions_{difficulty}'] = questions.copy()
                    st.rerun()

            if st.session_state.get(f'test_started_{difficulty}', False):
                if st.session_state[f'question_index_{difficulty}'] < st.session_state[f'total_questions_{difficulty}']:
                    display_question(st.session_state[f'current_questions_{difficulty}'][st.session_state[f'question_index_{difficulty}']], difficulty)
                else:
                    st.session_state[f'completed_{difficulty}'] = True
                    show_test_results(user_id, subject_id, chapter, difficulty)
                    continue

    if all(st.session_state.get(f'completed_{difficulty}', False) for difficulty in levels.values()):
        st.success("Congratulations! You have completed all tests for this chapter.")


def display_question(question, difficulty):
    question_index_key = f'question_index_{difficulty}'
    total_questions_key = f'total_questions_{difficulty}'

    st.write(f"Question {st.session_state[question_index_key] + 1} of {st.session_state[total_questions_key]}")
    st.write(question['question_text'])

    answer_key = f"answer_{st.session_state[question_index_key]}"
    submitted_key = f"submitted_{st.session_state[question_index_key]}"

    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False

    if answer_key not in st.session_state:
        st.session_state[answer_key] = ""

    def submit_answer():
        st.session_state[submitted_key] = True
        st.rerun()

    if not st.session_state[submitted_key]:
        with st.form(key=f"question_form_{st.session_state[question_index_key]}"):
            question_type = question.get('question_type', 'Short Answer')
            
            if question_type == 'Multiple Choice':
                options = question.get('options', [])
                if options and isinstance(options, list) and all(option.strip() for option in options):
                    user_answer = st.radio("Choose your answer:", options, key=answer_key)
                else:
                    st.error("No valid options available for this multiple choice question.")
                    user_answer = st.text_input("Enter your answer:", key=answer_key)
            elif question_type == 'True/False':
                user_answer = st.radio("Choose your answer:", ['True', 'False'], key=answer_key)
            elif question_type in ['Short Answer', 'Fill in the Blanks']:
                user_answer = st.text_input("Enter your answer:", key=answer_key)
            elif question_type == 'Essay':
                user_answer = st.text_area("Enter your essay:", key=answer_key)
            else:
                st.error(f"Unsupported question type: {question_type}")
                user_answer = st.text_input("Enter your answer:", key=answer_key)

            st.form_submit_button("Submit Answer", on_click=submit_answer)
    else:
        user_answer = st.session_state[answer_key]

        if user_answer is not None and user_answer.strip():
            correct_answer = question['correct_answer']
            is_correct = user_answer.lower() == correct_answer.lower()  # Case-insensitive comparison
            if is_correct:
                st.success("Correct!")
                st.session_state[f'score_{difficulty}'] += 1
            else:
                st.error("Incorrect")
                st.write(f"Correct answer: {correct_answer}")

        if st.button("Next Question", key=f"next_{st.session_state[question_index_key]}"):
            st.session_state[question_index_key] += 1
            st.session_state[submitted_key] = False  # Reset submitted state for the next question
            st.rerun()

def show_test_results(user_id, subject_id, chapter, difficulty):
    st.header("Test Complete!")
    # Access the score and total questions for the specific difficulty level
    score = st.session_state.get(f'score_{difficulty}', 0)
    total_questions = st.session_state.get(f'total_questions_{difficulty}', 0)
    
    st.write(f"Your score: {score} out of {total_questions}")
    if total_questions > 0:
        percentage = (score / total_questions) * 100
        st.write(f"Percentage: {percentage:.2f}%")
    else:
        st.write("No questions were attempted.")

    summary = st.session_state.adaptive_agent.generate_summary()
    st.write(summary)

    completion_date = date.today().isoformat()
    save_test_results(user_id, subject_id, chapter, score, total_questions)
    populate_user_lessons_table(user_id, subject_id, chapter, percentage, completion_date)

    if st.button("Start New Test"):
        for key in st.session_state.keys():
            if key.startswith(('question_index', 'score', 'total_questions', 'current_questions', 'user_answers', 'feedbacks', 'adaptive_agent', 'available_questions', 'answer_', 'submitted_', 'test_started')):
                del st.session_state[key]
        st.rerun()

def fetch_chapters(subject):
    response = supabase.table("test_questions").select("topic").eq("subject", subject).execute()
    if response.data:
        chapters = list(set([q['topic'] for q in response.data if q['topic']]))
        return chapters
    return []

def fetch_questions(subject, chapter, difficulty):
    response = supabase.table("test_questions").select("*").eq("subject", subject).eq("topic", chapter).eq("difficulty", difficulty).execute()
    questions = response.data if response.data else []
    
    for question in questions:
        question_type = question.get('question_type', 'Short Answer')
        if question_type in ['Multiple Choice', 'True/False']:
            if isinstance(question.get('options'), str):
                try:
                    question['options'] = eval(question['options'])
                except Exception as e:
                    logging.error(f"Error evaluating options: {e}")
                    question['options'] = []
            # Ensure options is a list and remove any empty options
            question['options'] = [opt for opt in question.get('options', []) if isinstance(opt, str) and opt.strip()]
            # If it's a True/False question and options are empty, set default options
            if question_type == 'True/False' and not question['options']:
                question['options'] = ['True', 'False']
            # If options are still empty for Multiple Choice, provide a fallback
            if question_type == 'Multiple Choice' and not question['options']:
                question['options'] = ['Option 1', 'Option 2', 'Option 3', 'Option 4']  # Default options

    logging.info(f"Fetched {len(questions)} questions for {subject}, {chapter}, {difficulty}.")
    for q in questions:
        logging.info(f"Question: {q['question_text']}, Type: {q.get('question_type', 'Unknown')}, Options: {q.get('options', 'No options')}")

    return questions

def save_test_results(user_id, subject_id, chapter, score, total_questions):
    data = {
        "custom_id": user_id,
        "subject_id": subject_id,
        "chapter": chapter,
        "score": score,
        "total_questions": total_questions,
        "percentage": (score / total_questions) * 100
    }
    result = supabase.table("test_results").insert(data).execute()
    if result.data:
        st.success("Test results saved successfully!")
    else:
        st.error("Failed to save test results. Please try again.")

def get_student_subjects(user_id):
    response = supabase.table("user_lessons").select("subject_id").eq("user_id", user_id).execute()
    subject_ids = {lesson['subject_id'] for lesson in response.data} if response.data else []

    # Fetch subject details based on the subject IDs
    if subject_ids:
        subjects_response = supabase.table("subjects").select("*").in_("id", list(subject_ids)).execute()
        return subjects_response.data
    return []

def get_current_lesson(user_id, subject_id):
    response = supabase.table("user_lessons").select("*").eq("user_id", user_id).eq("subject_id", subject_id).eq("status", "in_progress").limit(1).execute()
    return response.data[0] if response.data else None

def get_subject_progress(user_id, subject_id):
    total_lessons = supabase.table("lessons").select("id").eq("subject_id", subject_id).execute()
    if not total_lessons.data:
        return 0
    
    completed_lessons = supabase.table("user_lessons").select("id").eq("user_id", user_id).eq("subject_id", subject_id).eq("status", "completed").execute()
    progress = (len(completed_lessons.data) / len(total_lessons.data)) * 100 if total_lessons.data else 0
    
    # Skip inserting performance metrics for now
    # supabase.table("performance_metrics").insert({
    #     "user_id": user_id,
    #     "subject_id": subject_id,
    #     "metric_type": "subject_progress",
    #     "value": progress
    # }).execute()
    
    return progress

def start_next_lesson(user_id, subject_id):
    current_lesson = get_current_lesson(user_id, subject_id)
    if current_lesson:
        supabase.table("user_lessons").update({"status": "completed"}).eq("id", current_lesson['id']).execute()
    
    next_lesson = supabase.table("lessons").select("*").eq("subject_id", subject_id).gt("order", current_lesson['order']).order("order").limit(1).execute()
    if next_lesson.data:
        supabase.table("user_lessons").insert({"user_id": user_id, "lesson_id": next_lesson.data[0]['id'], "status": "in_progress"}).execute()

def calculate_overall_progress(user_id):
    subjects = get_student_subjects(user_id)
    
    if not subjects:
        logging.info(f"No subjects found for user {user_id}")
        return 0

    total_weighted_progress = 0
    total_lessons = 0
    
    for subject in subjects:
        subject_id = subject['id']

        total_subject_lessons = supabase.table("lessons").select("id").eq("subject_id", subject_id).execute()
        completed_lessons = supabase.table("user_lessons").select("id").eq("user_id", user_id).eq("subject_id", subject_id).eq("status", "completed").execute()
        
        subject_total_lessons = len(total_subject_lessons.data)
        subject_completed_lessons = len(completed_lessons.data)
        
        if subject_total_lessons > 0:
            subject_progress = (subject_completed_lessons / subject_total_lessons) * 100
            total_weighted_progress += subject_progress * subject_total_lessons
            total_lessons += subject_total_lessons
    
    if total_lessons > 0:
        overall_progress = total_weighted_progress / total_lessons
    else:
        logging.info(f"No lessons found for user {user_id}")
        overall_progress = 0
    
    overall_progress = round(overall_progress, 2)
    
    logging.info(f"Calculated overall progress for user {user_id}: {overall_progress}%")
    
    # Update the student's profile with the new overall progress
    update_result = supabase.table("student_profiles").update({"overall_progress": overall_progress}).eq("custom_id", user_id).execute()
    logging.info(f"Update result: {update_result}")
    
    return overall_progress

def update_study_streak(user_id):
    profile = supabase.table("student_profiles").select("*").eq("custom_id", user_id).single().execute().data
    
    today = date.today()
    last_study_date = profile.get('last_study_date')
    current_streak = profile.get('study_streak', 0)
    
    if last_study_date == today - timedelta(days=1):
        new_streak = current_streak + 1
    elif last_study_date == today:
        new_streak = current_streak
    else:
        new_streak = 1
    
    supabase.table("student_profiles").update({
        "study_streak": new_streak,
        "last_study_date": str(today)
    }).eq("custom_id", user_id).execute()

def get_study_streak(user_id):
    response = supabase.table("student_profiles").select("study_streak").eq("custom_id", user_id).execute()
    return response.data[0]['study_streak'] if response.data else 0

def get_user_badges(user_id):
    profile = supabase.table("student_profiles").select("*").eq("custom_id", user_id).single().execute().data
    test_results = supabase.table("test_results").select("*").eq("custom_id", user_id).execute().data
    
    badges = []
    
    overall_progress = profile.get('overall_progress', 0)
    if overall_progress >= 25:
        badges.append({"name": "Quarter Way There", "icon": "🥉"})
    if overall_progress >= 50:
        badges.append({"name": "Halfway Hero", "icon": "🥈"})
    if overall_progress >= 75:
        badges.append({"name": "Almost There", "icon": "🥇"})
    if overall_progress == 100:
        badges.append({"name": "Completion Champion", "icon": "🏆"})

    streak = profile.get('study_streak', 0)
    if streak >= 7:
        badges.append({"name": "Week Warrior", "icon": "📅"})
    if streak >= 30:
        badges.append({"name": "Monthly Master", "icon": "🌙"})

    if test_results:
        perfect_scores = sum(1 for result in test_results if result['percentage'] == 100)
        if perfect_scores >= 1:
            badges.append({"name": "Perfect Score", "icon": "⭐"})
        if perfect_scores >= 5:
            badges.append({"name": "Perfection Prodigy", "icon": "🌟"})

    return badges

def get_leaderboard_data():
    # Fetch leaderboard data from the database
    student_profiles_response = supabase.table("student_profiles").select("custom_id, overall_progress").order("overall_progress", desc=True).execute()
    
    # Fetch user names from the users table
    users_response = supabase.table("users").select("custom_id, full_name").execute()

    # Create a dictionary for quick lookup of user names
    user_names = {user['custom_id']: user['full_name'] for user in users_response.data}

    # Combine the data
    leaderboard_data = []
    for profile in student_profiles_response.data:
        custom_id = profile['custom_id']
        overall_progress = profile['overall_progress']
        name = user_names.get(custom_id, "Unknown User")  # Default to "Unknown User" if not found
        leaderboard_data.append({
            "custom_id": custom_id,
            "name": name,
            "overall_progress": overall_progress
        })

    return leaderboard_data

def get_subject_skills(subject_id):
    response = supabase.table("subject_skills").select("*").eq("subject_id", subject_id).execute()
    return response.data

def get_skill_mastery(user_id, skill_id):
    response = supabase.table("performance_metrics").select("value").eq("user_id", user_id).eq("metric_type", f"skill_mastery_{skill_id}").order("timestamp", desc=True).limit(1).execute()
    return response.data[0]['value'] if response.data else 0

def get_recent_test_scores(user_id, subject_id, limit=5):
    response = supabase.table("test_results").select("percentage").eq("custom_id", user_id).eq("subject_id", subject_id).order("created_at", desc=True).limit(limit).execute()
    return [score['percentage'] for score in response.data]

def get_subject_study_time(user_id, subject_id):
    response = supabase.table("performance_metrics").select("value").eq("user_id", user_id).eq("subject_id", subject_id).eq("metric_type", "study_time").execute()
    return sum([entry['value'] for entry in response.data])

def get_current_challenge(user_id):
    profile = supabase.table("student_profiles").select("*").eq("custom_id", user_id).single().execute().data

    if not profile:
        return None

    recent_tests = supabase.table("test_results").select("*").eq("custom_id", user_id).order("created_at", desc=True).limit(5).execute().data

    avg_performance = sum(test['percentage'] for test in recent_tests) / len(recent_tests) if recent_tests else 0

    overall_progress = profile.get('overall_progress', 0)

    if overall_progress < 25:
        challenge_type = "beginner"
    elif overall_progress < 50:
        challenge_type = "intermediate"
    elif overall_progress < 75:
        challenge_type = "advanced"
    else:
        challenge_type = "expert"

    if avg_performance < 60:
        focus = "improvement"
    elif avg_performance < 80:
        focus = "consistency"
    else:
        focus = "excellence"

    challenges = {
        "beginner": {
            "improvement": "Complete 3 lessons this week to boost your progress!",
            "consistency": "Maintain your current pace and complete 4 lessons this week!",
            "excellence": "Great job! Try to complete 5 lessons this week to keep excelling!"
        },
        "intermediate": {
            "improvement": "Aim to score above 70% on your next test!",
            "consistency": "Complete 5 lessons and score above 75% on your next test!",
            "excellence": "Push yourself! Complete 6 lessons and score above 85% on your next test!"
        },
        "advanced": {
            "improvement": "Focus on your weak areas. Complete 3 lessons in your lowest-scoring subject!",
            "consistency": "Maintain your progress by scoring above 80% on your next two tests!",
            "excellence": "You're doing great! Try to achieve a perfect score on your next test!"
        },
        "expert": {
            "improvement": "Challenge yourself! Complete an advanced lesson in each subject this week!",
            "consistency": "Keep up the excellent work! Maintain your streak of high scores for another week!",
            "excellence": "You're a star! Can you mentor a fellow student this week while maintaining your own excellence?"
        }
    }

    challenge_description = challenges[challenge_type][focus]
    progress = min(100, max(0, overall_progress + (avg_performance / 2)))

    return {
        "description": challenge_description,
        "progress": progress
    }

def populate_user_lessons_table(user_id, subject_id, topic, score, completion_date):
    # Find the corresponding lesson
    lesson_response = supabase.table("lessons").select("id").eq("subject_id", subject_id).eq("title", topic).execute()
    if lesson_response.data:
        lesson_id = lesson_response.data[0]['id']
        
        # Check if an entry already exists
        existing_entry = supabase.table("user_lessons").select("id").eq("user_id", user_id).eq("lesson_id", lesson_id).execute()
        
        if not existing_entry.data:
            # Create a new entry in user_lessons
            user_lesson_data = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "subject_id": subject_id,
                "topic": topic,
                "status": "completed",
                "progress": 100,
                "score": score,
                "completion_date": completion_date
            }
            result = supabase.table("user_lessons").insert(user_lesson_data).execute()

            # Check the result of the insert operation
            if result.data:
                print(f"User lesson entry added for user {user_id}, subject {subject_id}, topic {topic}")
            else:
                print(f"Failed to add user lesson entry: {result.error}")
        else:
            print(f"Entry already exists for user {user_id}, lesson {lesson_id}.")
    else:
        print(f"No lesson found for subject {subject_id} and topic {topic}.")

def get_subject_id(subject_name):
    response = supabase.table("subjects").select("id").eq("name", subject_name).execute()
    return response.data[0]['id'] if response.data else None
