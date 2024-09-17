import streamlit as st
from ..admin.ai_agent import generate_homework, generate_practice_questions, save_homework_to_supabase, save_practice_questions_to_supabase, generate_rag_based_questions, save_rag_questions_to_supabase, load_chapter_names
import re
import json

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Test Questions"

if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = None

if 'approved_questions' not in st.session_state:
    st.session_state.approved_questions = []

def parse_questions(raw_output):
    questions = []
    current_question = None
    for line in raw_output.split('\n'):
        line = line.strip()
        if line.startswith('**Question'):
            if current_question:
                questions.append(current_question)
            current_question = {'question_text': '', 'options': [], 'difficulty': line.split(':')[-1].strip()[:-2]}
        elif line.startswith('Options:'):
            continue
        elif re.match(r'^[A-D]\)', line):
            if current_question is None:
                current_question = {'question_text': '', 'options': [], 'difficulty': 'Unknown'}
            current_question['options'].append(line)
        elif line.startswith('Correct Answer:') or line.startswith('Answer:'):
            if current_question is None:
                current_question = {'question_text': '', 'options': [], 'difficulty': 'Unknown'}
            current_question['correct_answer'] = line.split(':', 1)[1].strip()
        elif current_question:
            if '_________' in line:
                current_question['question_text'] = line
            elif not current_question['question_text']:
                current_question['question_text'] = line
    
    if current_question:
        questions.append(current_question)
    
    # Post-processing to ensure correct_answer is set for all questions
    for question in questions:
        if 'correct_answer' not in question:
            if question['options']:
                # For multiple-choice, set the first option as default if no correct answer was found
                question['correct_answer'] = question['options'][0]
            else:
                # For other types, set a default message
                question['correct_answer'] = "Correct answer not provided"
        elif question['options']:
            # For multiple-choice, ensure the correct_answer matches one of the options
            correct_option = next((opt for opt in question['options'] if question['correct_answer'] in opt), None)
            if correct_option:
                question['correct_answer'] = correct_option
            else:
                # If no match found, set the first option as default
                question['correct_answer'] = question['options'][0]
    
    return questions

def show_teacher_dashboard():
    st.header("Teacher Dashboard")
    st.write("Welcome to the Teacher Dashboard")

    tab1, tab2, tab3 = st.tabs(["Generate Homework", "Generate Practice Questions", "Generate RAG-based Test"])

    with tab1:
        show_homework_tab()

    with tab2:
        show_practice_questions_tab()

    with tab3:
        show_rag_based_test_tab()

def show_homework_tab():
    st.subheader("Generate Homework")
    subject = st.selectbox("Subject", ["Math", "English", "Science", "History"])
    grade = st.number_input("Grade", min_value=1, max_value=12, step=1)
    topic = st.text_input("Topic")
    vark_preference = st.selectbox("VARK Preference", ["Visual", "Auditory", "Reading/Writing", "Kinesthetic"])
    learning_stage = st.selectbox("Learning Stage", ["Beginner", "Intermediate", "Proficient", "Advanced"])
    learning_objective = st.text_input("Specific Learning Objective")
    time_allocation = st.selectbox("Time Allocation", ["15 minutes", "20 minutes", "30 minutes", "45 minutes"])
    difficulty_level = st.slider("Difficulty Level", 1, 5, 3)
    required_materials = st.selectbox("Required Materials", ["Common household items", "Digital resources", "Printable worksheets", "No special materials"])
    previous_knowledge = st.text_input("Previous Knowledge")
    curriculum_standards = st.selectbox("Curriculum Standards", ["Common Core", "State-specific standards", "International Baccalaureate", "None"])
    cultural_context = st.selectbox("Cultural Context", ["Global", "Local community", "Specific culture", "None"])
    
    if cultural_context == "Specific culture":
        cultural_context = st.text_input("Specify culture")

    if st.button("Generate Homework"):
        with st.spinner("Generating homework..."):
            homework = generate_homework(
                subject, grade, topic, vark_preference, learning_stage,
                learning_objective, time_allocation, difficulty_level,
                required_materials, previous_knowledge, curriculum_standards,
                cultural_context
            )
        st.text_area("Generated Homework", homework, height=300)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Homework"):
                result = save_homework_to_supabase(subject, grade, topic, homework, vark_preference, learning_stage)
                st.success("Homework saved successfully!")
        with col2:
            if st.button("Reject Homework"):
                st.warning("Homework rejected. Generate a new one.")

def show_practice_questions_tab():
    st.subheader("Generate Practice Questions")
    subject = st.selectbox("Subject", ["Math", "English", "Science", "History"], key="practice_subject")
    grade = st.number_input("Grade", min_value=1, max_value=12, step=1, key="practice_grade")
    topic = st.text_input("Topic", key="practice_topic")
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)
    vark_preference = st.selectbox("VARK Preference", ["Visual", "Auditory", "Reading/Writing", "Kinesthetic"], key="practice_vark")
    learning_stage = st.selectbox("Learning Stage", ["Beginner", "Intermediate", "Proficient", "Advanced"], key="practice_stage")
    question_types = st.multiselect("Question Types", ["Multiple-choice", "Open-ended", "Problem-solving"], default=["Multiple-choice"])
    skill_focus = st.selectbox("Skill Focus", ["Critical thinking", "Memory recall", "Application", "Analysis"])
    difficulty_distribution = st.selectbox("Difficulty Distribution", ["Even distribution", "More easy", "More challenging"])
    time_per_question = st.selectbox("Time per Question", ["30 seconds", "1 minute", "2 minutes", "Varied"])
    use_visuals = st.selectbox("Use of Visuals", ["Yes", "No", "Where appropriate"])
    real_world_application = st.selectbox("Real-world Application", ["Theoretical", "Practical scenarios", "Mix of both"])
    blooms_taxonomy_level = st.selectbox("Bloom's Taxonomy Level", ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"])

    if st.button("Generate Practice Questions"):
        with st.spinner("Generating practice questions..."):
            questions = generate_practice_questions(
                subject, grade, topic, num_questions, vark_preference,
                learning_stage, ", ".join(question_types), skill_focus,
                difficulty_distribution, time_per_question, use_visuals,
                real_world_application, blooms_taxonomy_level
            )
        st.text_area("Generated Practice Questions", questions, height=300)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Questions"):
                result = save_practice_questions_to_supabase(subject, grade, topic, questions)
                st.success("Practice questions saved successfully!")
        with col2:
            if st.button("Reject Questions"):
                st.warning("Practice questions rejected. Generate new ones.")

def show_rag_based_test_tab():
    st.subheader("Generate RAG-based Test Questions")
    subject = st.selectbox("Subject", ["Math", "English", "Science", "History"], key="rag_subject")
    grade = st.selectbox("Grade", list(range(1, 13)), key="rag_grade")
    
    chapter_names = load_chapter_names(subject, grade)
    chapter_name = st.selectbox("Chapter Name", chapter_names, key="rag_chapter")
    
    question_types = ["Multiple Choice", "Fill in the Blank", "Short Answer", "True/False", "Essay"]
    selected_type = st.selectbox("Question Type", question_types, key="rag_question_type")
    
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5, key="rag_num_questions")
    
    if st.button("Generate RAG-based Questions"):
        raw_output = generate_rag_based_questions(subject, grade, chapter_name, num_questions, selected_type)
        st.session_state.generated_questions = parse_questions(raw_output)
        st.session_state.approved_questions = []  # Reset approved questions
    
    if st.session_state.generated_questions:
        st.write(f"Questions for {subject} Grade {grade}, Chapter: {chapter_name}")
        st.write("These questions are based strictly on the chapter's content.")
        for i, q in enumerate(st.session_state.generated_questions, 1):
            with st.expander(f"Question {i}"):
                st.write(f"[{q.get('difficulty', 'Unknown')}] {q.get('question_text', 'No question text available')}")
                if q.get('options'):
                    st.write("Options:")
                    for option in q['options']:
                        st.write(f"   {option}")
                st.write(f"Correct Answer: {q.get('correct_answer', 'Not provided')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{i}"):
                        st.session_state.approved_questions.append(q)
                        st.success(f"Question {i} approved!")
                with col2:
                    if st.button("Reject", key=f"reject_{i}"):
                        st.session_state.generated_questions.remove(q)
                        st.warning(f"Question {i} rejected.")
        
        if st.session_state.approved_questions:
            if st.button("Save Approved Questions"):
                result = save_rag_questions_to_supabase(subject, grade, chapter_name, st.session_state.approved_questions, selected_type)
                st.success(result)
                # Clear the generated and approved questions after saving
                st.session_state.generated_questions = None
                st.session_state.approved_questions = []
        
        if st.button("Reject All and Generate New Questions"):
            st.session_state.generated_questions = None
            st.session_state.approved_questions = []
            st.rerun()

    elif st.session_state.generated_questions is not None:
        st.error("Failed to parse questions from the AI output.")

