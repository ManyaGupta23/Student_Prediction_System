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
st.set_page_config(page_title="Student Analytics", layout="wide", page_icon="🎓")

# =========================
# UI STYLE
# =========================
st.markdown("""
<style>
.main { background-color: #f0f2f6; }
.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.user-icon { font-size: 50px; text-align: center; color: #4A90E2; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

FILE_NAME = "student_performance.xlsx"

# =========================
# LOAD DATA (SAFE)
# =========================
def load_all_data():
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    df_students = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    df_users = pd.read_excel(FILE_NAME, sheet_name="Users")

    try:
        df_preds = pd.read_excel(FILE_NAME, sheet_name="Predictions")
    except:
        df_preds = pd.DataFrame()

    return df_students, df_users, df_preds

# =========================
# SAVE DATA (FIXED)
# =========================
def save_all_data(s_df, u_df, p_df):
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl', mode='w') as writer:
        s_df.to_excel(writer, sheet_name="Students_Data", index=False)
        u_df.to_excel(writer, sheet_name="Users", index=False)
        p_df.to_excel(writer, sheet_name="Predictions", index=False)  # ✅ FIXED

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("SHERNI ACADEMY REPORT CARD", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"<b>Name:</b> {row['Name']} | <b>ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1, 12)
    ]

    data = [
        ["Subject/Metric", "Score"],
        ["Attendance", f"{row['Attendence']}%"],
        ["Internal Marks", row['Internal_Marks']],
        ["Assignment", row.get('Assignment_Score', 'N/A')],
        ["Final Grade", row['Final_Result']]
    ]

    table = Table(data, colWidths=[200, 120])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.blue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.grey)
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return buffer

# =========================
# LOAD DATA
# =========================
df_students, df_users, df_preds = load_all_data()

# =========================
# SESSION
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

# =========================
# LOGIN
# =========================
with st.sidebar:
    st.title("Portal")

    if not st.session_state.login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Sign In"):
            df_users['Username'] = df_users['Username'].astype(str).str.strip()
            df_users['Password'] = df_users['Password'].astype(str).str.strip()

            match = df_users[(df_users['Username']==u) & (df_users['Password']==p)]

            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role']
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid Credentials ❌")

    else:
        st.success(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# =========================
# MAIN
# =========================
if st.session_state.login:

    role = st.session_state.role.lower()

    # =========================
    # ADMIN
    # =========================
    if role == "admin":
        st.markdown('<div class="user-icon">👤</div>', unsafe_allow_html=True)
        st.title("Admin Dashboard")

        tab1, tab2 = st.tabs(["➕ Add Student", "🗑️ Delete Student"])

        with tab1:
            with st.form("add_student"):
                sid = st.text_input("Student ID")
                name = st.text_input("Name")
                att = st.slider("Attendance", 0, 100)
                marks = st.number_input("Marks", 0, 100)
                grade = st.selectbox("Grade", ["A", "B", "C", "Fail"])

                if st.form_submit_button("Add"):
                    new_s = pd.DataFrame([{
                        "Student_ID": sid,
                        "Name": name,
                        "Attendence": att,
                        "Internal_Marks": marks,
                        "Final_Result": grade
                    }])

                    df_students = pd.concat([df_students, new_s], ignore_index=True)

                    new_u = pd.DataFrame([{
                        "Username": sid,
                        "Password": "123",
                        "Role": "student"  # ✅ FIXED
                    }])

                    df_users = pd.concat([df_users, new_u], ignore_index=True)

                    new_p = pd.DataFrame([{
                        "Student_ID": sid,
                        "Predicted_Result": "TBD"
                    }])

                    df_preds = pd.concat([df_preds, new_p], ignore_index=True)

                    save_all_data(df_students, df_users, df_preds)
                    st.success("Student added successfully ✅")

        with tab2:
            st.dataframe(df_students)
            del_id = st.text_input("Enter ID to delete")

            if st.button("Delete"):
                df_students = df_students[df_students['Student_ID'].astype(str)!=del_id]
                df_users = df_users[df_users['Username'].astype(str)!=del_id]
                df_preds = df_preds[df_preds['Student_ID'].astype(str)!=del_id]

                save_all_data(df_students, df_users, df_preds)
                st.warning("Deleted ❌")
                st.rerun()

    # =========================
    # TEACHER
    # =========================
    elif role == "teacher":
        st.markdown('<div class="user-icon">👨‍🏫</div>', unsafe_allow_html=True)
        st.title("Teacher Dashboard")

        st.metric("Total Students", len(df_students))
        st.metric("Average Attendance", f"{df_students['Attendence'].mean():.1f}%")

        st.bar_chart(df_students.set_index("Name")["Internal_Marks"])

    # =========================
    # STUDENT
    # =========================
    elif role == "student":
        st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
        st.title("My Report Card")

        student_row = df_students[df_students['Student_ID'].astype(str)==st.session_state.username]

        if not student_row.empty:
            row = student_row.iloc[0]

            st.metric("Attendance", row["Attendence"])
            st.metric("Marks", row["Internal_Marks"])
            st.metric("Result", row["Final_Result"])

            st.progress(int(row["Attendence"]))

            pdf = generate_pdf(row)

            st.download_button(
                "📥 Download Marksheet",
                pdf,
                file_name=f"{row['Student_ID']}_marksheet.pdf"
            )
        else:
            st.warning("No data found")
