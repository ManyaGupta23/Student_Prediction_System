import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

CONFIG

=========================

st.set_page_config(page_title="EduPredict Pro", layout="wide") FILE_NAME = "student_performance_system.xlsx" LOGIN_IMAGE = "portal_image.png"

=========================

DATABASE FUNCTIONS

=========================

def load_all_data(): if not os.path.exists(FILE_NAME): with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer: pd.DataFrame(columns=[ "Student_ID", "Name", "Attendance", "Internal_Marks", "Assignment_Score", "Study_Hours", "Final_Result", "Performance_Index", "Risk" ]).to_excel(writer, sheet_name="Students_Data", index=False)

pd.DataFrame([
            {"Username": "admin", "Password": "123", "Role": "admin"},
            {"Username": "teacher", "Password": "123", "Role": "teacher"}
        ]).to_excel(writer, sheet_name="Users", index=False)

        pd.DataFrame(columns=["Student_ID", "Prediction"]).to_excel(
            writer, sheet_name="Predictions", index=False
        )

xls = pd.ExcelFile(FILE_NAME)
s_df = pd.read_excel(xls, "Students_Data")
u_df = pd.read_excel(xls, "Users")
p_df = pd.read_excel(xls, "Predictions")

s_df["Student_ID"] = s_df["Student_ID"].astype(str)
u_df["Username"] = u_df["Username"].astype(str)

return s_df, u_df, p_df

def save_all_data(s_df, u_df, p_df): with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer: s_df.to_excel(writer, sheet_name="Students_Data", index=False) u_df.to_excel(writer, sheet_name="Users", index=False) p_df.to_excel(writer, sheet_name="Predictions", index=False)

=========================

UTILITY FUNCTIONS

=========================

def calculate_risk(idx): if idx < 40: return "HIGH RISK" elif idx < 70: return "MEDIUM RISK" return "LOW RISK"

def generate_pdf_report(row): buffer = BytesIO() doc = SimpleDocTemplate(buffer) styles = getSampleStyleSheet()

elements = [
    Paragraph(f"Student Report Card - {row['Name']}", styles['Title']),
    Spacer(1, 20),
    Table([
        ["Student ID", row['Student_ID']],
        ["Attendence", f"{row['Attendence']}%"],
        ["Internal Marks", row['Internal_Marks']],
        ["Assignment Score", row['Assignment_Score']],
        ["Performance Index", f"{row['Performance_Index']:.2f}"],
        ["Risk", row['Risk']]
    ], style=[
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
    ])
]

doc.build(elements)
buffer.seek(0)
return buffer

=========================

SESSION SETUP

=========================

if "auth" not in st.session_state: st.session_state.auth = { "logged_in": False, "user": None, "role": None }

=========================

LOAD DATA

=========================

df_students, df_users, df_preds = load_all_data()

=========================

CUSTOM CSS

=========================

st.markdown("""

<style>
.stButton > button {
    width: 100%;
    background: #2563EB;
    color: white;
    border-radius: 10px;
    height: 45px;
    border: none;
    font-weight: bold;
}
.login-box {
    background: white;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    margin-top: 60px;
}
.title-text {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 10px;
}
.subtitle {
    color: gray;
    margin-bottom: 25px;
}
</style>""", unsafe_allow_html=True)

=========================

LOGIN SCREEN

=========================

if not st.session_state.auth["logged_in"]: left, right = st.columns([1.1, 1.4])

with left:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<div class="title-text">Dashboard Portal</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Login to continue</div>', unsafe_allow_html=True)

    username = st.text_input("Username / ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        match = df_users[
            (df_users["Username"] == username) &
            (df_users["Password"].astype(str) == password)
        ]

        if not match.empty:
            st.session_state.auth = {
                "logged_in": True,
                "user": username,
                "role": match.iloc[0]["Role"].lower()
            }
            st.rerun()
        else:
            st.error("Invalid Username or Password")

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    if os.path.exists(LOGIN_IMAGE):
        st.image(LOGIN_IMAGE, use_container_width=True)
    else:
        st.warning("Add portal_image.png in project folder")

=========================

DASHBOARDS

=========================

else: role = st.session_state.auth["role"] user = st.session_state.auth["user"]

with st.sidebar:
    st.success(f"Logged in as: {user}")
    if st.button("Logout"):
        st.session_state.auth = {
            "logged_in": False,
            "user": None,
            "role": None
        }
        st.rerun()

# ADMIN DASHBOARD
if role == "admin":
    st.title("Admin Dashboard")
    tab1, tab2 = st.tabs(["Database", "Register Student"])

    with tab1:
        st.dataframe(df_students, use_container_width=True)
        if not df_students.empty:
            del_id = st.selectbox("Delete Student", df_students["Student_ID"].unique())
            if st.button("Delete Student"):
                df_students = df_students[df_students["Student_ID"] != del_id]
                df_users = df_users[df_users["Username"] != del_id]
                save_all_data(df_students, df_users, df_preds)
                st.success("Student deleted")
                st.rerun()

    with tab2:
        with st.form("student_form"):
            sid = st.text_input("Student ID")
            name = st.text_input("Student Name")
            spass = st.text_input("Password", value="123")
            atteneance = st.slider("Attendence", 0, 100, 75)
            marks = st.number_input("Internal Marks", 0, 100, 50)
            assignment = st.number_input("Assignment Score", 0, 100, 50)
            study_hours = st.number_input("Study Hours", 0, 15, 5)

            if st.form_submit_button("Register"):
                if sid in df_students["Student_ID"].values:
                    st.error("Student ID already exists")
                else:
                    idx = marks*0.5 + assignment*0.3 + attendence*0.2
                    final_result = "Pass" if idx >= 40 else "Fail"

                    new_student = pd.DataFrame([{
                        "Student_ID": sid,
                        "Name": name,
                        "Attendence": attendence,
                        "Internal_Marks": marks,
                        "Assignment_Score": assignment,
                        "Study_Hours": study_hours,
                        "Final_Result": final_result,
                        "Performance_Index": idx,
                        "Risk": calculate_risk(idx)
                    }])

                    new_user = pd.DataFrame([{
                        "Username": sid,
                        "Password": spass,
                        "Role": "student"
                    }])

                    df_students = pd.concat([df_students, new_student], ignore_index=True)
                    df_users = pd.concat([df_users, new_user], ignore_index=True)
                    save_all_data(df_students, df_users, df_preds)
                    st.success("Student Registered Successfully")
                    st.rerun()

# TEACHER DASHBOARD
elif role == "teacher":
    st.title("Teacher Insights")
    st.subheader("Risk Distribution")
    st.bar_chart(df_students["Risk"].value_counts())

    st.subheader("Attendence vs Performance")
    st.scatter_chart(df_students, x="Attendence", y="Performance_Index")

# STUDENT DASHBOARD
elif role == "student":
    st.title("My Performance")
    student = df_students[df_students["Student_ID"] == user]

    if not student.empty:
        row = student.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Attendence", f"{row['Attendence']}%")
        c2.metric("Performance Index", f"{row['Performance_Index']:.1f}")
        c3.metric("Risk", row['Risk'])

        st.download_button(
            "Download Report Card",
            generate_pdf_report(row),
            file_name=f"Report_{user}.pdf"
        )
