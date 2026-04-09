import streamlit as st
import pandas as pd
import os
from io import BytesIO
from PIL import Image
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

# ================= CONFIG =================
FILE_NAME = "student_performance.xlsx"
PIC_FOLDER = "profile_pics"
LOGIN_IMAGE = "portal_image.png"
DEFAULT_AVATAR = "default_avatar.png"

os.makedirs(PIC_FOLDER, exist_ok=True)
st.set_page_config(page_title="EduPredict Pro", layout="wide")

# ================= LOAD =================
def load_data():
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
    s = pd.read_excel(xls, "Students_Data")
    u = pd.read_excel(xls, "Users")
    p = pd.read_excel(xls, "Predictions")

    s["Student_ID"] = s["Student_ID"].astype(str).str.strip()
    u["Username"] = u["Username"].astype(str).str.strip()

    return s,u,p

def save_data(s,u,p):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
        s.to_excel(writer, sheet_name="Students_Data", index=False)
        u.to_excel(writer, sheet_name="Users", index=False)
        p.to_excel(writer, sheet_name="Predictions", index=False)

# ================= UTILS =================
def calculate_risk(idx):
    if idx < 40: return "HIGH RISK"
    elif idx < 70: return "MEDIUM RISK"
    return "LOW RISK"

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

# ================= SESSION =================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in":False,"user":None,"role":None}

df_students, df_users, df_preds = load_data()

# ================= LOGIN =================
if not st.session_state.auth["logged_in"]:
    col1,col2 = st.columns([1,1.3])

    with col1:
        st.title("🎓 EduPredict Pro")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            match = df_users[(df_users["Username"]==u) & (df_users["Password"].astype(str)==p)]
            if not match.empty:
                st.session_state.auth={"logged_in":True,"user":u,"role":match.iloc[0]["Role"]}
                st.rerun()
            else:
                st.error("Invalid login")

    with col2:
        if os.path.exists(LOGIN_IMAGE):
            st.image(LOGIN_IMAGE, use_container_width=True)

# ================= MAIN =================
else:
    role = st.session_state.auth["role"]
    user = st.session_state.auth["user"]

    # SIDEBAR
    with st.sidebar:
        pic = os.path.join(PIC_FOLDER,f"{user}.png")
        if os.path.exists(pic):
            st.image(pic,width=100)
        elif os.path.exists(DEFAULT_AVATAR):
            st.image(DEFAULT_AVATAR,width=100)

        st.write(f"👋 {user}")
        if st.button("Logout"):
            st.session_state.auth={"logged_in":False,"user":None,"role":None}
            st.rerun()

    # ================= ADMIN =================
    if role == "admin":
        st.title("🛡️ Admin Dashboard")

        if not df_students.empty:

            # 🏆 RANKING
            df_students["Rank"] = df_students["Performance_Index"].rank(ascending=False, method="dense")

            # 🥇 TOPPER
            topper = df_students.loc[df_students["Performance_Index"].idxmax()]
            lowest = df_students.loc[df_students["Performance_Index"].idxmin()]

            c1, c2 = st.columns(2)
            with c1:
                st.success(f"🥇 Topper: {topper['Name']} ({topper['Performance_Index']:.1f})")
            with c2:
                st.error(f"⚠️ Lowest: {lowest['Name']} ({lowest['Performance_Index']:.1f})")

            st.dataframe(df_students, use_container_width=True)

        # ADD STUDENT
        with st.form("add"):
            sid = st.text_input("Student ID")
            name = st.text_input("Name")
            att = st.slider("Attendence",0,100,80)
            marks = st.slider("Marks",0,100,50)
            assign = st.slider("Assignment",0,100,50)
            study = st.slider("Study Hours",0,12,5)
            result = st.selectbox("Final Result",["Pending","Pass","Fail"])

            if st.form_submit_button("Add"):
                idx = (marks*0.4)+(assign*0.3)+(att*0.2)+(study*2)

                new = pd.DataFrame([{
                    "Student_ID":sid,
                    "Name":name,
                    "Attendence":att,
                    "Internal_Marks":marks,
                    "Assignment_Score":assign,
                    "Study_Hours":study,
                    "Final_Result":result,
                    "Performance_Index":idx,
                    "Risk":calculate_risk(idx)
                }])

                df_students = pd.concat([df_students,new], ignore_index=True)

                df_users = pd.concat([df_users,pd.DataFrame([{
                    "Username":sid,"Password":"123","Role":"student"
                }])], ignore_index=True)

                save_data(df_students,df_users,df_preds)
                st.success("Added")
                st.rerun()

    # ================= TEACHER =================
    elif role == "teacher":
        st.title("👨‍🏫 Teacher Dashboard")

        if not df_students.empty:

            # 🏆 RANKING
            df_students["Rank"] = df_students["Performance_Index"].rank(ascending=False, method="dense")

            st.dataframe(df_students.sort_values("Rank"), use_container_width=True)

            st.bar_chart(df_students.set_index("Name")["Performance_Index"])

            # COMPARE
            s1 = st.selectbox("Student 1", df_students["Student_ID"])
            s2 = st.selectbox("Student 2", df_students["Student_ID"])

            if s1 and s2:
                d1 = df_students[df_students["Student_ID"]==s1].iloc[0]
                d2 = df_students[df_students["Student_ID"]==s2].iloc[0]

                comp = pd.DataFrame({
                    "Metric":["Attendence","Marks","Performance"],
                    s1:[d1["Attendence"],d1["Internal_Marks"],d1["Performance_Index"]],
                    s2:[d2["Attendance"],d2["Internal_Marks"],d2["Performance_Index"]]
                })

                st.bar_chart(comp.set_index("Metric"))

    # ================= STUDENT =================
    elif role == "student":
        st.title("📝 My Performance")

        my = df_students[df_students["Student_ID"]==user]

        if not my.empty:
            row = my.iloc[0]

            st.metric("Attendence",row["Attendence"])
            st.metric("Score",row["Performance_Index"])
            st.metric("Risk",row["Risk"])

            st.download_button("Download PDF", generate_pdf(row), "report.pdf")
        else:
            st.error("No record found")
