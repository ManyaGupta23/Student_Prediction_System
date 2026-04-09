import streamlit as st
import pandas as pd
import os
from io import BytesIO
from PIL import Image
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================
FILE_NAME = "student_performance.xlsx"
PIC_FOLDER = "profile_pics"
LOGIN_IMAGE = "portal_image.png"

os.makedirs(PIC_FOLDER, exist_ok=True)
st.set_page_config(page_title="EduPredict Pro", layout="wide")

# =========================
# LOAD DATA
# =========================
def load_all_data():
    if not os.path.exists(FILE_NAME):
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            pd.DataFrame(columns=[
                "Student_ID","Name","Attendence","Internal_Marks",
                "Assignment_Score","Study_Hours","Final_Result",
                "Performance_Index","Risk"
            ]).to_excel(writer, sheet_name="Students_Data", index=False)

            pd.DataFrame([
                {"Username":"admin","Password":"123","Role":"admin"},
                {"Username":"teacher","Password":"123","Role":"teacher"}
            ]).to_excel(writer, sheet_name="Users", index=False)

            pd.DataFrame(columns=["Student_ID","Prediction"]).to_excel(writer, sheet_name="Predictions", index=False)

    xls = pd.ExcelFile(FILE_NAME)
    return (
        pd.read_excel(xls, "Students_Data"),
        pd.read_excel(xls, "Users"),
        pd.read_excel(xls, "Predictions")
    )

def save_to_excel(s,u,p):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        s.to_excel(writer, sheet_name="Students_Data", index=False)
        u.to_excel(writer, sheet_name="Users", index=False)
        p.to_excel(writer, sheet_name="Predictions", index=False)

# =========================
# UTILS
# =========================
def calculate_risk(idx):
    if idx < 40: return "HIGH RISK"
    elif idx < 70: return "MEDIUM RISK"
    else: return "LOW RISK"

def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph(f"Report: {row['Name']}", styles['Title']),
        Spacer(1,20),
        Table([
            ["ID", row["Student_ID"]],
            ["Attendence", f"{row['Attendence']}%"],
            ["Score", f"{row['Performance_Index']:.2f}"],
            ["Risk", row["Risk"]]
        ])
    ]

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# SESSION
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in":False,"user":None,"role":None}

df_students, df_users, df_preds = load_all_data()

# =========================
# LOGIN SCREEN (PREMIUM)
# =========================
if not st.session_state.auth["logged_in"]:

    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg,#667eea,#764ba2);
    }
    .login-box {
        background:white;
        padding:30px;
        border-radius:15px;
        box-shadow:0 8px 20px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1,1.3])

    # LEFT
    with col1:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)

        st.title("🎓 EduPredict Pro")
        st.caption("Smart Student Performance System")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            match = df_users[
                (df_users['Username']==u) &
                (df_users['Password'].astype(str)==p)
            ]
            if not match.empty:
                st.session_state.auth={
                    "logged_in":True,
                    "user":u,
                    "role":match.iloc[0]["Role"]
                }
                st.rerun()
            else:
                st.error("Invalid Login")

        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT
    with col2:
        if os.path.exists(LOGIN_IMAGE):
            st.image(LOGIN_IMAGE, use_container_width=True)
        else:
            st.markdown("## 📊 Predict • Track • Improve")

# =========================
# MAIN APP
# =========================
else:
    role = st.session_state.auth["role"]
    user = st.session_state.auth["user"]

    # Sidebar
    with st.sidebar:
        st.write(f"👋 {user}")
        if st.button("Logout"):
            st.session_state.auth={"logged_in":False,"user":None,"role":None}
            st.rerun()

    # ADMIN
    if role == "admin":
        st.title("Admin Dashboard")

        st.dataframe(df_students)

        with st.form("add"):
            sid = st.text_input("ID")
            name = st.text_input("Name")
            marks = st.slider("Marks",0,100,50)
            att = st.slider("Attendence",0,100,80)

            if st.form_submit_button("Add"):
                idx = marks*0.6 + att*0.4
                new = pd.DataFrame([{
                    "Student_ID":sid,
                    "Name":name,
                    "Attendence":att,
                    "Internal_Marks":marks,
                    "Assignment_Score":50,
                    "Study_Hours":5,
                    "Final_Result":"Pending",
                    "Performance_Index":idx,
                    "Risk":calculate_risk(idx)
                }])

                df_students = pd.concat([df_students,new])
                df_users = pd.concat([df_users,pd.DataFrame([{
                    "Username":sid,"Password":"123","Role":"student"
                }])])

                save_to_excel(df_students,df_users,df_preds)
                st.success("Added!")

    # TEACHER
    elif role == "teacher":
        st.title("Teacher Dashboard")

        st.bar_chart(df_students["Risk"].value_counts())
        st.scatter_chart(df_students,x="Attendence",y="Performance_Index")

    # STUDENT
    elif role == "student":
        st.title("My Performance")

        row = df_students[df_students["Student_ID"]==user].iloc[0]

        st.metric("Attendence",row["Attendence"])
        st.metric("Score",row["Performance_Index"])
        st.metric("Risk",row["Risk"])

        st.download_button("Download PDF", generate_pdf(row), "report.pdf")
