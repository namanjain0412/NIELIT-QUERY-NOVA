import re
import time
import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["groq_api_key"])

def extract_sql_from_response(response_text):
    sql_match = re.search(r"SELECT .*?;", response_text, re.DOTALL | re.IGNORECASE)
    return sql_match.group(0).strip() if sql_match else None

def generate_sql_query(user_input, schema):
    restricted_keywords = ["who is", "what is", "where is", "capital of", "define", "tell me about", "prime minister", "president of", "country", "world record"]
    if any(keyword in user_input.lower() for keyword in restricted_keywords):
        st.error("❌ Invalid query! This tool only supports database-related questions.")
        return None, 0

    schema_text = "\n".join([f"Table: {table}, Columns: {', '.join(cols)}" for table, cols in schema.items()])
    prompt = f"""
    You are an expert in converting English questions to SQL queries. 
    Here is the database schema:
    {schema_text}
    Convert the following question into an SQL query. Only return the SQL query, without any explanations or additional text:
    "{user_input}"
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
