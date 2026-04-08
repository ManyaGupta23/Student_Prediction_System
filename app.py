import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="  Student Analytics", layout="wide", page_icon="🎓")

# Custom CSS for modern cards and icons
st.markdown("""
<style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .user-icon { font-size: 50px; text-align: center; color: #4A90E2; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "student_performance.xlsx"

# =========================
# DATA CORE
# =========================
def load_all_data():
    if not os.path.exists(FILE_NAME):
        # Create dummy structure if file missing for first run
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    df_students = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    df_users = pd.read_excel(FILE_NAME, sheet_name="Users")
    df_preds = pd.read_excel(FILE_NAME, sheet_name="Prediction")
    return df_students, df_users, df_preds

def save_all_data(s_df, u_df, p_df):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        s_df.to_excel(writer, sheet_name="Students_Data", index=False)
        u_df.to_excel(writer, sheet_name="Users", index=False)
        p_df.to_excel(writer, sheet_name="Prediction", index=False)

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSf6sw76aampleStyleSheet()
    elements = [
        Paragraph("SHERNI ACADEMY REPORT CARD", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"<b>Name:</b> {row['Name']} | <b>ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1, 12)
    ]
    data = [["Subject/Metric", "Score"], 
            ["Attendance", f"{row['Attendence']}%"], 
            ["Internal Marks", row['Internal_Marks']],
            ["Assignment", row['Assignment_Score']],
            ["Final Grade", row['Final_Result']]]
    t = Table(data, colWidths=[200, 100])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.blue), ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke), ('GRID',(0,0),(-1,-1),1,colors.grey)]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# MAIN APP
# =========================
df_students, df_users, df_preds = load_all_data()

if "login" not in st.session_state:
    st.session_state.login = False

# Sidebar Login
with st.sidebar:
    st.title("Portal")
    if not st.session_state.login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            match = df_users[(df_users['Username'].astype(str)==u) & (df_users['Password'].astype(str)==p)]
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role']
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid Credentials")
    else:
        st.success(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# Dashboard Content
if st.session_state.login:
    role = st.session_state.role.lower()

    # --- ADMIN PAGE ---
    if role == "admin":
        st.markdown('<div class="user-icon">👤</div>', unsafe_allow_html=True)
        st.title("Admin Dashboard")
        
        tab1, tab2 = st.tabs(["➕ Add Student", "🗑️ Delete Student"])
        
        with tab1:
            with st.form("add_student"):
                c1, c2 = st.columns(2)
                sid = c1.text_input("New ID")
                sname = c2.text_input("Name")
                satt = c1.slider("Attendance", 0, 100)
                smarks = c2.number_input("Marks", 0, 100)
                sgrade = st.selectbox("Grade", ["A", "B", "C", "Fail"])
                if st.form_submit_button("Add Record"):
                    # Add to Students_Data
                    new_s = pd.DataFrame([{"Student_ID": sid, "Name": sname, "Attendence": satt, "Internal_Marks": smarks, "Final_Result": sgrade}])
                    df_students = pd.concat([df_students, new_s], ignore_index=True)
                    # Add to Users
                    new_u = pd.DataFrame([{"Username": sid, "Password": "123", "Role": "Student"}])
                    df_users = pd.concat([df_users, new_u], ignore_index=True)
                    # Add to Prediction Placeholder
                    new_p = pd.DataFrame([{"Student_ID": sid, "Predicted_Result": "TBD"}])
                    df_preds = pd.concat([df_preds, new_p], ignore_index=True)
                    
                    save_all_data(df_students, df_users, df_preds)
                    st.success("Student added successfully across all sheets!")

        with tab2:
            st.dataframe(df_students)
            del_id = st.text_input("Enter Student ID to Delete")
            if st.button("Delete Permanently"):
                df_students = df_students[df_students['Student_ID'].astype(str) != del_id]
                df_users = df_users[df_users['Username'].astype(str) != del_id]
                df_preds = df_preds[df_preds['Student_ID'].astype(str) != del_id]
                save_all_data(df_students, df_users, df_preds)
                st.warning(f"ID {del_id} deleted.")
                st.rerun()

    # --- TEACHER PAGE ---
    elif role == "teacher":
        st.markdown('<div class="user-icon">👨‍🏫</div>', unsafe_allow_html=True)
        st.title("Teacher Analytics")
        col1, col2 = st.columns(2)
        col1.metric("Total Students", len(df_students))
        col2.metric("Avg Attendance", f"{df_students['Attendence'].mean():.1f}%")
        st.bar_chart(df_students.set_index('Name')['Internal_Marks'])

    # --- STUDENT PAGE ---
    elif role == "student":
        st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
        st.title("Student Portal")
        s_row = df_students[df_students['Student_ID'].astype(str) == st.session_state.username]
        if not s_row.empty:
            row = s_row.iloc[0]
            st.metric("My Performance Index", row['Final_Result'])
            st.progress(int(row['Attendence']))
            pdf = generate_pdf(row)
            st.download_button("📥 Download Report Card", pdf, file_name="report.pdf")
