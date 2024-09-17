import streamlit as st
from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_student_login():
    st.title("Student Login")

    custom_id = st.text_input("Student ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            st.write(f"Attempting login with Student ID: {custom_id}")  # Debug print
            
            # First, fetch the user data using the custom_id
            user_response = supabase.from_('users').select('*').eq('custom_id', custom_id).single().execute()
            st.write(f"User query response: {user_response}")  # Debug print
            
            if user_response.data:
                user_data = user_response.data
                
                # Check if the password matches
                if user_data['password'] == password:  # Note: In a real app, use hashed passwords
                    if user_data['role'] == 'student':
                        # Set the user in session state
                        st.session_state.user = {
                            'custom_id': custom_id,
                            'email': user_data.get('email'),
                            'role': 'student'
                        }
                        st.success("Logged in successfully!")
                        st.experimental_rerun()
                    else:
                        st.error(f"User role is not student. Role: {user_data['role']}")
                else:
                    st.error("Invalid password")
            else:
                st.error("Student ID not found")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.write(f"Error details: {type(e).__name__}, {str(e)}")  # More detailed error info

    st.write("Don't have an account? Contact your administrator to sign up.")
