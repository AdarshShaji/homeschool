import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Set page config at the very beginning, before any other Streamlit commands
st.set_page_config(page_title="Homeschool Admin", page_icon="🏫", layout="wide")

from homeschool.admin.login import show_admin_login
from homeschool.admin.dashboard import show_admin_dashboard

def admin_main():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show login if user is not logged in
    if st.session_state.user is None:
        show_admin_login()
    else:
        user = st.session_state.user
        if user['role'] == 'admin':
            show_admin_dashboard()
        else:
            st.error("Invalid user role. Only admins are allowed.")

    # Add a logout button
    if st.session_state.user is not None:
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()

if __name__ == "__main__":
    admin_main()
