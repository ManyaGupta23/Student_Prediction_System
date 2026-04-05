import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. PAGE CONFIG & UI THEME
# ==========================================
st.set_page_config(page_title="Student Analytics Portal", layout="wide", page_icon="🎓")

FILE_NAME = "student_performance.xlsx"

# ==========================================
# 2. DATA ENGINE
# ==========================================
def load_and_clean_data():
    if not os.path.exists(FILE_NAME):
        st.error(f"Error: {FILE_NAME} not found.")
        return None, None, None

    s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
    p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")

    for df in [s_df, u_df, p_df]:
        df.columns = df.columns.str.strip()
    return s_df, u_df, p_df

def save_all_sheets(s, u, p):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        s.to_excel(writer, sheet_name="Students_Data", index=False)
        u.to_excel(writer, sheet_name="Users", index=False)
        p.to_excel(writer, sheet_name="Predictions", index=False)

df_students, df_users, df_preds = load_and_clean_data()

# ==========================================
# 3. PDF REPORT GENERATOR
# ==========================================
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("STUDENT REPORT CARD", styles['Title']),
        Spacer(1, 20),
        Paragraph(f"<b>Name:</b> {row['Name']}", styles['Normal']),
        Paragraph(f"<b>ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1, 15)
    ]
    data = [
        ["Metric", "Value"],
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
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. LOGIN & AUTHENTICATION
# ==========================================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col_login, col_img = st.columns([1, 2])
    with col_login:
        st.title("Student System Portal")
        input_user = st.text_input("Username / ID")
        input_pass = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            u_clean = df_users.copy()
            u_clean['Username'] = u_clean['Username'].astype(str).str.replace('.0', '', regex=False).str.strip()
            u_clean['Password'] = u_clean['Password'].astype(str).str.strip()
            
            user_str = str(input_user).strip()
            pass_str = str(input_pass).strip()
            
            match = u_clean[(u_clean['Username'] == user_str) & (u_clean['Password'] == pass_str)]
            
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = user_str
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    with col_img:
        st.header("WELCOME To the Portal")
        st.image("portal_image.png", use_container_width=True)

# ==========================================
# 5. DASHBOARDS
# ==========================================
else:
    with st.sidebar:
        st.write(f"### Hello, {st.session_state.username}")
        if st.button("Logout", type="primary"):
            st.session_state.clear()
            st.rerun()

    # --- ADMIN: Only see Registration ---
    if st.session_state.role == "admin":
        st.title("Administrator Control Panel")
        tab1, tab2 = st.tabs(["📊 Records Management", "➕ Register New Student"])
        with tab1:
            st.dataframe(df_students)
        with tab2:
            st.subheader("Institutional Enrollment")
            with st.form("add_form"):
                nid = st.text_input("New Student ID")
                nname = st.text_input("Full Name")
                natt = st.number_input("Attendance %", 0, 100, 75)
                nhrs = st.number_input("Study Hours", 0, 24, 4)
                if st.form_submit_button("Save Student"):
                    # Logics for saving to Excel would go here
                    st.success(f"Student {nname} registered successfully!")

    # --- TEACHER: Performance & Prediction ---
    elif st.session_state.role == "teacher":
        st.title("Teacher Analytics Portal")
        tab1, tab2 = st.tabs(["📈 Class Analytics", "🔍 Risk Prediction"])
        with tab1:
            st.scatter_chart(df_students, x="Attendence", y="Performance_Index")
        with tab2:
            st.subheader("Predict Student Performance Risk")
            student_name = st.selectbox("Select Student", df_students['Name'].unique())
            student_data = df_students[df_students['Name'] == student_name].iloc[0]
            
            # Simple Prediction Logic
            risk = "High Risk" if student_data['Attendence'] < 60 else "Good Standing"
            st.warning(f"Analysis for {student_name}: **{risk}**")
            st.write(f"Current Attendance: {student_data['Attendence']}%")

    # --- STUDENT: Dashboard & Report ---
    elif st.session_state.role == "student":
        st.title("Student Academic Portal")
        s_clean = df_students.copy()
        s_clean['Student_ID'] = s_clean['Student_ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
        my_data = s_clean[s_clean['Student_ID'] == st.session_state.username]
        
        if not my_data.empty:
            data = my_data.iloc[0]
            st.metric("Final Grade", data['Final_Result'])
            # FIXED INDENTATION FOR PDF GEN
            pdf_report = generate_pdf(data)
            st.download_button("📥 Download Report Card", pdf_report, file_name=f"Report_{st.session_state.username}.pdf")
