import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# PAGE CONFIG & UI STYLE
# =========================
st.set_page_config(page_title="Sherni Student Analytics", layout="wide", page_icon="🎓")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .user-icon { font-size: 80px; text-align: center; margin-bottom: 5px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "student_performance.xlsx"

# =========================
# DATA ENGINE (Auto-Fixes Headers)
# =========================
def load_and_sync_data():
    if not os.path.exists(FILE_NAME):
        st.error(f"Critical Error: {FILE_NAME} not found in the directory.")
        return None, None, None

    # Load all 3 sheets
    try:
        s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
        u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
        p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")
    except Exception as e:
        st.error(f"Error reading sheets: {e}. Check if sheet names are correct.")
        return None, None, None

    # REPAIR: Standardize all column names (removes spaces, fixes casing)
    for df in [s_df, u_df, p_df]:
        df.columns = df.columns.str.strip()

    return s_df, u_df, p_df

def save_all_sheets(s_df, u_df, p_df):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        s_df.to_excel(writer, sheet_name="Students_Data", index=False)
        u_df.to_excel(writer, sheet_name="Users", index=False)
        p_df.to_excel(writer, sheet_name="Prediction", index=False)

df_students, df_users, df_preds = load_and_sync_data()

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("SHERNI ACADEMY OFFICIAL MARKSHEET", styles['Title']),
        Spacer(1, 20),
        Paragraph(f"<b>Student Name:</b> {row['Name']}", styles['Normal']),
        Paragraph(f"<b>Student ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1, 15)
    ]
    data = [
        ["Subject/Metric", "Score"],
        ["Attendance", f"{row['Attendence']}%"],
        ["Internal Marks", row['Internal_Marks']],
        ["Assignment Score", row['Assignment_Score']],
        ["Study Hours", row['Study_Hours']],
        ["Final Grade", row['Final_Result']]
    ]
    table = Table(data, colWidths=[200, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.blue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# LOGIN SYSTEM
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

with st.sidebar:
    st.title("🦁 Sherni Portal")
    if not st.session_state.login:
        u_input = st.text_input("Username / ID")
        p_input = st.text_input("Password", type="password")
        if st.button("Login"):
            # Ensure ID comparison is string-based
            match = df_users[(df_users['Username'].astype(str) == u_in) & 
                             (df_users['Password'].astype(str) == p_in)]
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = u_input
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    else:
        st.success(f"Access: {st.session_state.role.upper()}")
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

# =========================
# DASHBOARDS
# =========================
if st.session_state.login:
    role = st.session_state.role

    # --- ADMIN / TEACHER DASHBOARD ---
    if role in ["admin", "teacher"]:
        icon = "👤" if role == "admin" else "👨‍🏫"
        st.markdown(f'<div class="user-icon">{icon}</div>', unsafe_allow_html=True)
        st.title(f"{role.capitalize()} Portal")

        tab1, tab2 = st.tabs(["📊 Data Management", "➕ Add New Student"])

        with tab1:
            st.subheader("Complete Records List")
            # Show the student data table with all columns
            st.dataframe(df_students, use_container_width=True)
            
            st.divider()
            st.subheader("🗑️ Delete Student")
            del_id = st.text_input("Enter Student ID to permanently remove:")
            if st.button("Delete from All Sheets", type="primary"):
                if del_id:
                    # Remove from all 3 Dataframes
                    df_students = df_students[df_students['Student_ID'].astype(str) != str(del_id)]
                    df_users = df_users[df_users['Username'].astype(str) != str(del_id)]
                    df_preds = df_preds[df_preds['Student_ID'].astype(str) != str(del_id)]
                    
                    save_all_sheets(df_students, df_users, df_preds)
                    st.success(f"ID {del_id} wiped from database.")
                    st.rerun()

        with tab2:
            st.subheader("Register New Student")
            with st.form("student_reg"):
                c1, c2 = st.columns(2)
                nid = c1.text_input("Student ID (Unique)")
                nname = c2.text_input("Full Name")
                
                c3, c4, c5 = st.columns(3)
                natt = c3.number_input("Attendance %", 0, 100, 75)
                nhrs = c4.number_input("Study Hours", 0, 24, 4)
                nim = c5.number_input("Internal Marks", 0, 100, 50)
                
                c6, c7 = st.columns(2)
                nas = c6.number_input("Assignment Score", 0, 100, 50)
                nprev = c7.selectbox("Previous Result", ["A", "B", "C", "Fail"])
                
                nextra = st.selectbox("Extra Activities", ["Yes", "No"])
                nfinal = st.selectbox("Final Result", ["A", "B", "C", "Fail"])
                nperf = st.number_input("Performance Index", 0.0, 100.0, 50.0)

                if st.form_submit_button("Save Student to Excel"):
                    # 1. Update Students Data
                    new_s = pd.DataFrame([{"Student_ID": nid, "Name": nname, "Attendence": natt, "Study_Hours": nhrs, "Internal_Marks": nim, "Assignment_Score": nas, "Previous_Result": nprev, "Extra_Activities": nextra, "Final_Result": nfinal, "Performance_Index": nperf}])
                    df_students = pd.concat([df_students, new_s], ignore_index=True)
                    
                    # 2. Update Users (Login credentials)
                    new_u = pd.DataFrame([{"Username": nid, "Password": "123", "Role": "student"}])
                    df_users = pd.concat([df_users, new_u], ignore_index=True)
                    
                    # 3. Update Predictions
                    new_p = pd.DataFrame([{"Student_ID": nid, "Predicted_Result": "AWAITING"}])
                    df_preds = pd.concat([df_preds, new_p], ignore_index=True)
                    
                    save_all_sheets(df_students, df_users, df_preds)
                    st.success("Registration complete! Login: ID / Pass: 123")

    # --- STUDENT DASHBOARD ---
    elif role == "student":
        st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
        st.title("My Academic Portal")
        
        # Pull data for the logged-in ID
        curr_user = str(st.session_state.username)
        my_record = df_students[df_students['Student_ID'].astype(str) == curr_user]

        if not my_record.empty:
            row = my_record.iloc[0]
            st.subheader(f"Welcome back, {row['Name']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Current Attendance", f"{row['Attendence']}%")
            c2.metric("Latest Grade", row['Final_Result'])
            c3.metric("Performance Index", row['Performance_Index'])
            
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
