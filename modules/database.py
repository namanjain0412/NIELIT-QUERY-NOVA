import streamlit as st
import mysql.connector

def get_db_connection(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return None

def get_database_schema(db_config):
    conn = get_db_connection(db_config)
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
