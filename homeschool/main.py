import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Set page config at the very beginning, before any other Streamlit commands
st.set_page_config(page_title="Homeschool App", page_icon="🏫", layout="wide")

from homeschool.student.login import show_student_login
from homeschool.teacher.login import show_teacher_login
from homeschool.admin.login import show_admin_login
from homeschool.student.dashboard import show_student_dashboard
from homeschool.teacher.dashboard import show_teacher_dashboard
from homeschool.admin.dashboard import show_admin_dashboard

def main():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show role selection if user is not logged in
    if st.session_state.user is None:
        role = st.selectbox("Select your role", ["Student", "Teacher", "Admin"])
        if role == "Student":
            show_student_login()
        elif role == "Teacher":
            show_teacher_login()
        elif role == "Admin":
            show_admin_login()
    else:

        user = st.session_state.user
        if user['role'] == 'student':
            show_student_dashboard()
        elif user['role'] == 'teacher':
            show_teacher_dashboard()
        elif user['role'] == 'admin':
            show_admin_dashboard()
        else:
            st.error("Invalid user role")

    # Add a logout button
    if st.session_state.user is not None:
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()