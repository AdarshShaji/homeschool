import streamlit as st
from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY
from ..admin.ai_agent import GeminiProLLM
from crewai import Agent, Task, Crew
import json
import re

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_vark_questions():
    debug_info = []
    debug_info.append("Starting question generation")

    vark_question_agent = Agent(
        role='VARK Assessment Creator for Children',
        goal='Create engaging and effective VARK assessment questions suitable for children',
        backstory='You are an expert in child education and learning styles, specializing in VARK (Visual, Auditory, Reading/Writing, Kinesthetic) assessments for young students.',
        verbose=True,
        allow_delegation=False,
        llm=GeminiProLLM()
    )

    task = Task(
        description="""Create 10 simple, child-friendly questions for a VARK (Visual, Auditory, Reading/Writing, Kinesthetic) learning style assessment. Each question should have four options, one for each VARK category. The questions should be easy to understand and relate to everyday activities or school experiences of children.

        For each question:
        1. The question text should be simple and direct.
        2. Provide four options labeled V, A, R, and K.
        3. Use language and scenarios that children can easily understand and relate to.

        Ensure that:
        1. Questions are very simple and concise.
        2. Options clearly represent each VARK category but in a way children can understand.
        3. Questions cover various aspects of a child's daily life and learning experiences.
        4. The language is appropriate for children aged 7-12.
        5. The assessment as a whole provides a balanced representation of all VARK categories.

        Example format:
        1. When you're learning about animals, what do you like best?
        V: Looking at pictures of animals
        A: Listening to animal sounds
        R: Reading stories about animals
        K: Petting or playing with toy animals

        Provide 10 questions in this format.""",
        agent=vark_question_agent,
        expected_output="A list of 10 child-friendly questions, each with 4 VARK options."
    )

    crew = Crew(
        agents=[vark_question_agent],
        tasks=[task],
        verbose=2
    )

    try:
        result = crew.kickoff()
        
        # Convert CrewOutput to string
        result_str = str(result)
        
        debug_info.append(f"Raw AI output: {result_str}")

        # Try to extract questions and options
        questions = []
        current_question = None
        for line in result_str.split('\n'):
            debug_info.append(f"Processing line: {line}")
            if re.match(r'^\d+\.', line):  # New question
                debug_info.append("Found new question")
                if current_question:
                    questions.append(current_question)
                current_question = {"question": line.strip(), "options": {}}
            elif line.strip().startswith(('V:', 'A:', 'R:', 'K:')):
                debug_info.append("Found option")
                key, value = line.strip().split(':', 1)
                current_question["options"][key.strip()] = value.strip()
        
        if current_question:
            questions.append(current_question)

        debug_info.append(f"Extracted {len(questions)} questions")
        debug_info.append(f"Extracted questions: {json.dumps(questions, indent=2)}")

        # Validate questions
        if len(questions) == 10 and all(len(q["options"]) == 4 for q in questions):
            debug_info.append("Validation successful")
            return questions, debug_info
        else:
            debug_info.append(f"Validation failed: Generated {len(questions)} questions instead of 10, or some questions don't have all VARK options.")
            return [], debug_info

    except Exception as e:
        debug_info.append(f"An error occurred: {str(e)}")
        return [], debug_info

def vark_assessment():
    st.title("VARK Learning Style Assessment")

    # Add a button to force regeneration of questions
    if st.button("Regenerate Questions"):
        st.session_state.pop('vark_questions', None)
        st.session_state.pop('debug_info', None)
        st.experimental_rerun()

    if 'vark_questions' not in st.session_state or 'debug_info' not in st.session_state:
        with st.spinner("Generating assessment questions..."):
            questions, debug_info = generate_vark_questions()
            st.session_state.vark_questions = questions
            st.session_state.debug_info = debug_info

    questions = st.session_state.vark_questions
    debug_info = st.session_state.debug_info

    # Display debug information
    st.write("Debug Information:")
    for info in debug_info:
        st.write(info)

    if not questions:
        st.error("Failed to generate valid questions. Please check the debug output above and try again.")
        return

    responses = []

    for i, q in enumerate(questions):
        st.write(f"**{q['question']}**")
        response = st.radio("Choose one:", list(q["options"].values()), key=f"q{i}")
        responses.append(list(q["options"].keys())[list(q["options"].values()).index(response)])

    if st.button("Submit Assessment"):
        vark_result = calculate_vark_preference(responses)
        save_vark_result(st.session_state.user['custom_id'], vark_result)
        st.success(f"Your VARK preference: {vark_result}")
        st.session_state.vark_completed = True

def calculate_vark_preference(responses):
    counts = {'V': 0, 'A': 0, 'R': 0, 'K': 0}
    for r in responses:
        counts[r] += 1
    return max(counts, key=counts.get)

def save_vark_result(user_id, vark_result):
    supabase.table("user_profiles").upsert({"user_id": user_id, "vark_preference": vark_result}).execute()

def get_vark_preference(user_id):
    response = supabase.table("user_profiles").select("vark_preference").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]['vark_preference']
    else:
        # If no profile exists, create one
        create_user_profile(user_id)
        return None

def create_user_profile(user_id):
    supabase.table("user_profiles").insert({"user_id": user_id}).execute()
