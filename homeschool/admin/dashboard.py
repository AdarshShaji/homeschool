import streamlit as st
from supabase import create_client, Client
from admin.ai_agent import load_chapter_names
from ..config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_admin_dashboard():
    st.header("Admin Dashboard")
    st.write("Welcome to the Admin Dashboard")

    st.subheader("Populate Lessons")
    
    # Get unique subjects
    subjects_response = supabase.table("subjects").select("id", "name").execute()
    subjects = {subject['name']: subject['id'] for subject in subjects_response.data}
    
    subject = st.selectbox("Select Subject", list(subjects.keys()))
    subject_id = subjects[subject]
    
    grade = st.selectbox("Grade", list(range(1, 13)), key="rag_grade")

    chapter_names = load_chapter_names(subject, grade)
    chapter_name = st.selectbox("Chapter Name", chapter_names, key="rag_chapter")
    lesson_order = st.number_input("Lesson Order", min_value=1, step=1)
    lesson_difficulty = st.selectbox("Difficulty", ["beginner", "intermediate", "advanced"])
    lesson_duration = st.number_input("Estimated Duration (minutes)", min_value=5, step=5)
    
    if st.button("Add Lesson"):
        if chapter_name and lesson_order:
            new_lesson = {
                "subject_id": subject_id,
                "grade": grade,
                "title": chapter_name,
                "lesson_order": lesson_order,
                "difficulty": lesson_difficulty,
                "estimated_duration": lesson_duration
            }
            result = supabase.table("lessons").insert(new_lesson).execute()
            if result.data:
                st.success(f"Lesson '{chapter_name}' added successfully!")
            else:
                st.error("Failed to add lesson. Please try again.")
        else:
            st.warning("Please fill in all required fields.")

    # Display existing lessons
    st.subheader("Existing Chapters in the Database")
    for chapter_name in chapter_names:
        st.write(f"- {chapter_name}")

    # Add more admin functionality here
