import streamlit as st
from homeschool.database import get_user

def show_admin_login():
    st.header("Admin Login")
    custom_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = get_user(custom_id, password, 'admin')
        if user:
            st.session_state.user = user
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid User ID or password")
