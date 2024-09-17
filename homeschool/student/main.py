import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from homeschool.student.login import show_student_login
from homeschool.student.dashboard import show_student_dashboard

# Set page config at the very beginning, before any other Streamlit commands
st.set_page_config(page_title="Homeschool Student App", page_icon="🏫", layout="wide")

def student_main():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show login if user is not logged in
    if st.session_state.user is None:
        show_student_login()
    else:
        user = st.session_state.user
        if user['role'] == 'student':
            show_student_dashboard()
        else:
            st.error("Invalid user role. Only students are allowed.")

    # Add a logout button
    if st.session_state.user is not None:
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

if __name__ == "__main__":
    student_main()
