import base64
import streamlit as st

def set_custom_styles():
    st.markdown("""
        <style>
            body { background-color: #f4f4f4; color: #333; }
            .stButton>button { background-color: #0056b3; color: white; border-radius: 10px; font-size: 18px; transition: 0.3s; }
            .stButton>button:hover { background-color: #003d80; }
            .stTextInput>div>div>input { font-size: 18px; padding: 10px; }
            .stCode { font-size: 16px; }
            .heading { text-align: center; font-size: 36px; font-weight: bold; }
            .subheading { text-align: center; font-size: 24px; color: #007BFF; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

def add_bg_with_overlay(image_file_path):
    with open(image_file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6)),
                              url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
