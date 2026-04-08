import streamlit as st
import pandas as pd
import os
from io import BytesIO
from PIL import Image
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# 1. DATABASE & FOLDER CONFIG
# =========================
FILE_NAME = "student_performance_system.xlsx"
PIC_FOLDER = "profile_pics"
LOGIN_IMAGE = "portal_image.png"  # Your launch image name
os.makedirs(PIC_FOLDER, exist_ok=True)
st.set_page_config(page_title="EduPredict Pro", layout="wide")

def load_all_data():
    if not os.path.exists(FILE_NAME):
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            pd.DataFrame(columns=["Student_ID", "Name", "Attendance", "Internal_Marks", "Assignment_Score", "Study_Hours", "Final_Result", "Performance_Index", "Risk"]).to_excel(writer, sheet_name="Students_Data", index=False)
            pd.DataFrame([{"Username": "admin", "Password": "123", "Role": "admin"},{"Username": "teacher", "Password": "123", "Role": "teacher"}]).to_excel(writer, sheet_name="Users", index=False)
            pd.DataFrame(columns=["Student_ID", "Prediction"]).to_excel(writer, sheet_name="Predictions", index=False)

    xls = pd.ExcelFile(FILE_NAME)
    s_df = pd.read_excel(xls, "Students_Data")
    u_df = pd.read_excel(xls, "Users")
    p_df = pd.read_excel(xls, "Predictions") if "Predictions" in xls.sheet_names else pd.DataFrame(columns=["Student_ID", "Prediction"])
    
    s_df["Student_ID"] = s_df["Student_ID"].astype(str)
    u_df["Username"] = u_df["Username"].astype(str)
    return s_df, u_df, p_df

def save_to_excel(s, u, p):
    try:
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            s.to_excel(writer, sheet_name="Students_Data", index=False)
            u.to_excel(writer, sheet_name="Users", index=False)
            p.to_excel(writer, sheet_name="Predictions", index=False)
        return True
    except Exception as e:
        st.error(f"Error: Close Excel! {e}")
        return False

# =========================
# 2. UTILITY FUNCTIONS
# =========================
def calculate_risk(idx):
    if idx < 40: return "HIGH RISK"
    elif idx < 70: return "MEDIUM RISK"
    else: return "LOW RISK"

def generate_pdf_report(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"REPORT CARD: {row['Name']}", styles['Title']),
        Spacer(1, 20),
        Table([["ID", row['Student_ID']], ["Attendance", f"{row['Attendance']}%"], ["Score", f"{row['Performance_Index']:.2f}"], ["Risk", row['Risk']]], 
              colWidths=[150, 150], style=[('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)])
    ]
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# 3. AUTH & SESSION
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "user": None, "role": None}

df_students, df_users, df_preds = load_all_data()

# --- LOGIN SCREEN ---
if not st.session_state.auth["logged_in"]:
    # Center the login UI
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # Check if login image exists
        if os.path.exists(LOGIN_IMAGE):
            st.image(LOGIN_IMAGE, use_container_width=True)
        else:
            st.title("🎓 EduPredict Pro")
            st.info("Place 'portal_image.png' in the folder to see the launch banner.")
            
        with st.container(border=True):
            st.subheader("Login to Portal")
            u_input = st.text_input("Username / ID")
            p_input = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                match = df_users[(df_users['Username'] == u_input) & (df_users['Password'].astype(str) == p_input)]
                if not match.empty:
                    st.session_state.auth = {"logged_in": True, "user": u_input, "role": match.iloc[0]['Role'].lower()}
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

# =========================
# 4. PORTALS (AUTHENTICATED)
# =========================
else:
    role = st.session_state.auth["role"]
    username = st.session_state.auth["user"]

    with st.sidebar:
        st.header(f"Hello, {username}")
        # Display student profile pic if it exists
        pic_path = os.path.join(PIC_FOLDER, f"{username}.png")
        if os.path.exists(pic_path):
            st.image(pic_path, width=100)
        if st.button("🚪 Log Out"):
            st.session_state.auth = {"logged_in": False, "user": None, "role": None}
            st.rerun()

    # --- ADMIN PORTAL ---
    if role == "admin":
        st.title("🛡️ Admin Dashboard")
        tab1, tab2 = st.tabs(["📊 Database", "➕ Register Student"])
        
        with tab1:
            st.dataframe(df_students, use_container_width=True)
            if not df_students.empty:
                del_id = st.selectbox("Delete Student", df_students["Student_ID"].unique())
                if st.button("Confirm Delete", type="primary"):
                    df_students = df_students[df_students["Student_ID"] != del_id]
                    df_users = df_users[df_users["Username"] != del_id]
                    save_to_excel(df_students, df_users, df_preds)
                    st.rerun()

        with tab2:
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                sid = c1.text_input("Student ID")
                sname = c2.text_input("Full Name")
                spass = c1.text_input("Password", value="123")
                up_file = c2.file_uploader("Upload Profile Pic", type=['png', 'jpg'])
                
                att = st.slider("Attendance %", 0, 100, 80)
                marks = st.number_input("Internal Marks", 0, 100, 50)
                score = st.number_input("Assignment Score", 0, 100, 50)
                
                if st.form_submit_button("Save Student"):
                    if sid and sname:
                        if up_file:
                            img = Image.open(up_file)
                            img.save(os.path.join(PIC_FOLDER, f"{sid}.png"))
                        
                        idx = (marks * 0.5) + (score * 0.3) + (att * 0.2)
                        new_s = pd.DataFrame([{"Student_ID":sid, "Name":sname, "Attendance":att, "Internal_Marks":marks, "Assignment_Score":score, "Study_Hours":5, "Final_Result":"Pending", "Performance_Index":idx, "Risk":calculate_risk(idx)}])
                        new_u = pd.DataFrame([{"Username":sid, "Password":spass, "Role":"student"}])
                        df_students = pd.concat([df_students, new_s], ignore_index=True)
                        df_users = pd.concat([df_users, new_u], ignore_index=True)
                        save_to_excel(df_students, df_users, df_preds)
                        st.success("Registration Successful!")
                        st.rerun()

    # --- TEACHER PORTAL ---
    elif role == "teacher":
        st.title("👨‍🏫 Teacher Insights")
        if not df_students.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Risk Levels")
                st.bar_chart(df_students["Risk"].value_counts())
            with c2:
                st.subheader("Performance Trend")
                st.scatter_chart(df_students, x="Attendance", y="Performance_Index", color="Risk")
        else:
            st.info("Database is empty.")

    # --- STUDENT PORTAL ---
    elif role == "student":
        st.title("📝 My Performance")
        my_record = df_students[df_students["Student_ID"] == username]
        if not my_record.empty:
            row = my_record.iloc[0]
            c_img, c_txt = st.columns([1, 4])
            with c_img:
                p_path = os.path.join(PIC_FOLDER, f"{username}.png")
                if os.path.exists(p_path): st.image(p_path, width=150)
            with c_txt:
                st.subheader(row['Name'])
                st.caption(f"Student ID: {row['Student_ID']}")
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Attendance", f"{row['Attendance']}%")
            m2.metric("Performance", f"{row['Performance_Index']:.1f}")
            m3.metric("Status", row['Risk'])
            
            st.download_button("📥 Download Report Card", generate_pdf_report(row), f"Report_{username}.pdf")
