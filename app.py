import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# 1. Page Setup
st.set_page_config(page_title="Sherni Student Analytics", layout="wide")

st.markdown("""
<style>
    .user-icon { font-size: 70px; text-align: center; }
    .stMetric { border: 1px solid #ddd; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "student_performance.xlsx"

# 2. Load Data
@st.cache_data
def load_all_data():
    if not os.path.exists(FILE_NAME):
        return None, None, None
    s = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u = pd.read_excel(FILE_NAME, sheet_name="Users")
    p = pd.read_excel(FILE_NAME, sheet_name="Predictions")
    # Clean headers
    for d in [s, u, p]: d.columns = d.columns.str.strip()
    return s, u, p

df_students, df_users, df_preds = load_all_data()

# 3. Session State
if "login" not in st.session_state:
    st.session_state.login = False

# 4. Login Sidebar
with st.sidebar:
    st.title("🦁 Sherni Portal")
    if not st.session_state.login:
        user_id_input = st.text_input("User ID")
        pass_input = st.text_input("Password", type="password")
        if st.button("Login"):
            # FIXED: Variables match the input fields exactly
            match = df_users[(df_users['Username'].astype(str) == user_id_input) & 
                             (df_users['Password'].astype(str) == pass_input)]
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = user_id_input
                st.rerun()
            else:
                st.error("❌ Wrong ID or Password")
    else:
        st.write(f"Logged in as: **{st.session_state.role.upper()}**")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# 5. Dashboards
if st.session_state.login:
    role = st.session_state.role

    # ADMIN / TEACHER PORTAL
    if role in ["admin", "teacher"]:
        icon = "👤" if role == "admin" else "👨‍🏫"
        st.markdown(f'<div class="user-icon">{icon}</div>', unsafe_allow_html=True)
        st.title(f"{role.capitalize()} Dashboard")
        
        tab1, tab2 = st.tabs(["Data Records", "Register Student"])
        
        with tab1:
            st.dataframe(df_students, use_container_width=True)
            target = st.text_input("Enter ID to Delete")
            if st.button("Delete Record"):
                # Logic to drop from s, u, p and save
                st.success("Deleted!")

        with tab2:
            with st.form("add_student"):
                st.write("Fill Student Details")
                # Add your input fields for Internal_Marks, Study_Hours etc here
                if st.form_submit_button("Save"):
                    st.success("Added!")

    # STUDENT PORTAL
    elif role == "student":
        st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
        st.title("My Report Card")
        
        # Match current user to data
        me = df_students[df_students['Student_ID'].astype(str) == str(st.session_state.username)]
        
        if not me.empty:
            data = me.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Attendance", f"{data['Attendence']}%")
            c2.metric("Grade", data['Final_Result'])
            c3.metric("Study Hours", data['Study_Hours'])
            
            st.progress(int(data['Attendence']))
        else:
            st.error("No record found for your ID.")
            st.divider()
            
            # Show Details with Progress bar
            st.write("**Attendance Analysis**")
            st.progress(int(row['Attendence']))
            
            # Display other info
            st.write(f"**Study Habits:** {row['Study_Hours']} hours/day | **Assignments:** {row['Assignment_Score']}/100")
            
            # PDF Download
            pdf_file = generate_pdf(row)
            st.download_button("📥 Download Official Report Card", pdf_file, file_name=f"Report_{row['Student_ID']}.pdf")
        else:
            st.error(f"No record found for ID: {curr_user}. Please contact the Administration.")
