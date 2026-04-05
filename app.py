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

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .user-icon { font-size: 80px; text-align: center; margin-bottom: 5px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

FILE_NAME = "student_performance.xlsx"

# ==========================================
# 2. DATA ENGINE
# ==========================================
def load_and_clean_data():
    if not os.path.exists(FILE_NAME):
        st.error(f"Error: {FILE_NAME} not found. Please ensure the Excel file is in the project folder.")
        return None, None, None

    s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
    p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")

    # Strip column spaces
    s_df.columns = s_df.columns.str.strip()
    u_df.columns = u_df.columns.str.strip()
    p_df.columns = p_df.columns.str.strip()

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
        Paragraph(f"<b>Student Name:</b> {row['Name']}", styles['Normal']),
        Paragraph(f"<b>Student ID:</b> {row['Student_ID']}", styles['Normal']),
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
            # NORMALIZATION: Handles the 101.0 vs 101 issue
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
        if os.path.exists("portal_image.png"):
            st.image("portal_image.png", use_container_width=True)
        else:
            st.info("💡 Note: Place 'portal_image.png' in folder to show the welcome image.")

# ==========================================
# 5. DASHBOARD ROUTING
# ==========================================
else:
    # --- Sidebar (Persistent Logout) ---
    with st.sidebar:
        st.markdown('<div class="user-icon">👤</div>', unsafe_allow_html=True)
        st.write(f"### Hello, {st.session_state.username}")
        st.write(f"Access: **{st.session_state.role.upper()}**")
        st.divider()
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state.role == "admin":
        st.title("Administrator Control Panel")
        tab1, tab2 = st.tabs(["📊 Records Management", "➕ Register New Student"])
        
        with tab1:
            st.subheader("Master Student Database")
            st.dataframe(df_students, use_container_width=True)
            
            st.divider()
            del_id = st.text_input("Enter Student ID to delete:")
            if st.button("Delete Permanently", type="primary"):
                if del_id:
                    # Sync removal across all sheets
                    df_students = df_students[df_students['Student_ID'].astype(str).str.replace('.0', '', regex=False) != str(del_id)]
                    df_users = df_users[df_users['Username'].astype(str).str.replace('.0', '', regex=False) != str(del_id)]
                    df_preds = df_preds[df_preds['Student_ID'].astype(str).str.replace('.0', '', regex=False) != str(del_id)]
                    save_all_sheets(df_students, df_users, df_preds)
                    st.success(f"Record {del_id} deleted.")
                    st.rerun()

        with tab2:
            st.subheader("Institutional Enrollment")
            with st.form("add_form"):
                c1, c2 = st.columns(2)
                nid = c1.text_input("New Student ID")
                nname = c2.text_input("Full Name")
                # ... add other inputs as needed ...
                if st.form_submit_button("Save Student"):
                    # Add Logic to Append Dataframe and save_all_sheets()
                    st.success("New Student Registered!")

    # --- TEACHER DASHBOARD ---
    elif st.session_state.role == "teacher":
        st.title("Teacher Analytics Portal")
        tab1, tab2 = st.tabs(["📈 Performance Analytics", "🔍 Individual Prediction"])
        
        with tab1:
            st.subheader("Class-Wide Performance Trends")
            st.scatter_chart(data=df_students, x="Attendence", y="Performance_Index", color="#ff4b4b")
            st.bar_chart(df_students['Final_Result'].value_counts())

        with tab2:
            st.subheader("Predict Student Performance")
            selected_student = st.selectbox("Select Student", df_students['Name'].unique())
            st.info(f"Analyzing metrics for {selected_student}...")

    # --- STUDENT DASHBOARD ---
    elif st.session_state.role == "student":
        st.title("Student Academic Portal")
        
        # Normalize IDs for previous students
        s_clean = df_students.copy()
        s_clean['Student_ID'] = s_clean['Student_ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        my_row = s_clean[s_clean['Student_ID'] == st.session_state.username]

        if not my_row.empty:
            data = my_row.iloc[0]
            st.subheader(f"Welcome, {data['Name']}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Attendance", f"{data['Attendence']}%")
            col2.metric("Grade", data['Final_Result'])
            col3.metric("Study Hours", data['Study_Hours'])
            
            st.divider()
            pdf_report = generate_pdf(data)
            st.download_button("📥 Download Official Report Card", pdf_report, file_name=f"Report_{st.session_state.username}.pdf")
        else:
            st.error("Data not found for your ID. Please contact Admin.")
