# ==========================
#  IMPORTS AND CONFIGS
# ==========================

import os
import streamlit as st
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import re
from PIL import Image
import time
import io
import base64
import spacy

# Load the pre-trained spaCy model
nlp = spacy.load("en_core_web_sm")

# Function to process the user query and extract intent and entities
def process_query_spacy(query):
    doc = nlp(query)
    
    # Extract entities (e.g., table names, column names, etc.)
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    # Extract verbs (which can represent actions like SELECT, JOIN, etc.)
    actions = [token.text for token in doc if token.pos_ == "VERB"]

    return entities, actions


# Load environment variables (for API key, DB credentials, etc.)
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq API Client
client = Groq(api_key=api_key)

import streamlit as st

db_config = {
    "host": st.secrets["mysql"]["host"],
    "user": st.secrets["mysql"]["user"],
    "password": st.secrets["mysql"]["password"],
    "database": st.secrets["mysql"]["database"],
    "port": st.secrets["mysql"]["port"]
}


# User Authentication Credentials
VALID_USERNAME = st.secrets["auth"]["username"]
VALID_PASSWORD = st.secrets["auth"]["password"]


# ==========================
#  DATABASE CONNECTION
# ==========================

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return None



def get_database_schema():
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE()")
    schema = {}
    for table, column in cursor.fetchall():
        if table not in schema:
            schema[table] = []
        schema[table].append(column)
    cursor.close()
    conn.close()
    return schema


def extract_sql_from_response(response_text):
    sql_match = re.search(r"SELECT .*?;", response_text, re.DOTALL | re.IGNORECASE)
    return sql_match.group(0).strip() if sql_match else None
def generate_sql_query(user_input, schema):
    # Restrict non-database questions
    restricted_keywords = ["tell me about", "prime minister", "president of", "country", "world record", "who is", "what is", "where is", "capital of", "define"]
    if any(keyword in user_input.lower() for keyword in restricted_keywords):
        st.error("❌ Invalid query! This tool only supports database-related questions.")
        return None, 0

    # Process user input using spaCy to extract entities and actions
    entities, actions = process_query_spacy(user_input)
    
    # Convert schema into a format that can be used in the prompt
    schema_text = "\n".join([f"Table: {table}, Columns: {', '.join(cols)}" for table, cols in schema.items()])
    
    # Create the prompt for the LLM based on the extracted entities and actions
    prompt = f"""
    You are an expert in converting English questions to SQL queries. 
    Here is the database schema:
    {schema_text}
    Convert the following question into an SQL query. Only return the SQL query, without any explanations or additional text:
    "{user_input}"

    Extracted Entities: {entities}
    Extracted Actions: {actions}
    """
    
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        generation_time = time.time() - start_time
        sql_query = extract_sql_from_response(response.choices[0].message.content.strip())
        return sql_query, generation_time
    except Exception as e:
        st.error(f"LLM Error: {str(e)}")
        return None, 0
def construct_sql_from_entities_and_actions(entities, actions, schema):
    # Assuming the user wants a SELECT query (you can expand this logic to support different actions)
    columns = [entity[0] for entity in entities if entity[1] == 'COLUMN']  # Extract column names
    tables = [entity[0] for entity in entities if entity[1] == 'TABLE']  # Extract table names
    
    # Construct the SELECT part of the query
    select_clause = "SELECT " + ", ".join(columns) if columns else "*"

    # Construct the FROM part of the query
    from_clause = "FROM " + ", ".join(tables)
    
    # You can add additional filtering logic based on actions or entities, like WHERE, JOIN, etc.
    where_clause = ""
    for entity in entities:
        if entity[1] == "DATE":  # Example: looking for dates to filter by
            where_clause = f"WHERE date_column > '{entity[0]}'"  # Adjust for actual column names
    
    # Complete SQL query
    sql_query = f"{select_clause} {from_clause} {where_clause}"
    return sql_query


# ==================================
# CUSTOM STYLING & UI Enhancements
# ================================== 

st.set_page_config(page_title="Nielit QueryNova", page_icon="✨", layout="wide")
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


# ==========================
#  AUTHENTICATION SYSTEM
# ==========================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "logout_triggered" not in st.session_state:
    st.session_state["logout_triggered"] = False

def login():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔒 Welcome to Nielit QueryNova")
        st.markdown("<h2 class='subheading'>Your Smart Database Assistant</h2>", unsafe_allow_html=True)
    with col2:
        logo = Image.open("logo.png")
        st.image(logo, width=100)
    
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            st.session_state["authenticated"] = True
            st.session_state["logout_triggered"] = False
        else:
            st.error("Invalid username or password!")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["logout_triggered"] = True

if not st.session_state["authenticated"]:
    login()
    st.stop()



# ==========================
#  MAIN APP INTERFACE
# ==========================


col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("<h1 class='heading'>Nielit QueryNova</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='subheading'>Smart Database Assistant</h2>", unsafe_allow_html=True)
with col2:
    logo = Image.open("logo.png")
    st.image(logo, width=80)

# Sidebar & Logout
st.sidebar.button("Logout", on_click=logout)

schema = get_database_schema()
if schema:
    st.sidebar.subheader("📂 Database Tables")

    with st.sidebar.expander("📌 Select a Table", expanded=False):
        for table in schema.keys():
            if st.button(f"📄 {table}"):
                st.sidebar.write(f"**Columns in `{table}`:**")
                st.sidebar.write(", ".join(schema[table]))

# =============================
#  QUESTION INPUT + SQL OUTPUT
# =============================

st.markdown("### 📝 Ask a Question About Your Database")
user_input = st.text_input("Type your database-related question:")

if "query_history" not in st.session_state:
    st.session_state.query_history = []



if st.button("Generate SQL & Fetch Data"):
    if user_input:
        sql_query, generation_time = generate_sql_query(user_input, schema)
        if sql_query:
            st.session_state.query_history.append((sql_query, generation_time))
            st.success("Generated SQL Query:")
            st.code(sql_query, language="sql")
            st.write(f"⏱ Query Generation Time: {generation_time:.2f} seconds")
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    start_time = time.time()
                    cursor.execute(sql_query)
                    execution_time = time.time() - start_time
                    columns = [desc[0] for desc in cursor.description]
                    result = cursor.fetchall()
                    df = pd.DataFrame(result, columns=columns)
                    st.success(f"Query Result (Execution Time: {execution_time:.2f} seconds)")
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Download as CSV", df.to_csv(index=False), "data.csv", "text/csv")
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_buffer.seek(0)
                    st.download_button("Download as Excel", excel_buffer, "data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except mysql.connector.Error as err:
                    st.error(f"SQL Execution Error: {err}")
                finally:
                    cursor.close()
                    conn.close()




import base64
import streamlit as st


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

add_bg_with_overlay("images/bg.png")  
