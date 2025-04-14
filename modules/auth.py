import streamlit as st
from PIL import Image

def login(valid_username, valid_password):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔒 Welcome to Nielit QueryNova")
        st.markdown("<h2 class='subheading'>Your Smart Database Assistant</h2>", unsafe_allow_html=True)
    with col2:
        logo = Image.open("assets/logo.png")
        st.image(logo, width=100)

    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        if username == valid_username and password == valid_password:
            st.session_state["authenticated"] = True
            st.session_state["logout_triggered"] = False
        else:
            st.error("Invalid username or password!")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["logout_triggered"] = True
