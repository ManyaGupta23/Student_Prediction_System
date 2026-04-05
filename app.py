import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. PAGE CONFIG & THEMING
# ==========================================
st.set_page_config(page_title="Student Analytics", layout="wide", page_icon="🎓")

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
# 2. DATA ENGINE (Multi-Sheet Sync)
# ==========================================
def load_and_clean_data():
    if not os.path.exists(FILE_NAME):
        st.error(f"Error: {FILE_NAME} not found. Please upload the Excel file.")
        return None, None, None

    # Load all 3 sheets
    s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
    p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")

    # CLEANING: Remove invisible spaces from column headers
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
# 4. LOGIN SYSTEM (Updated with Image & Logic Fix)
# ==========================================
# ==========================================
# 4. LOGIN SYSTEM (Layout with Logout)
# ==========================================
if "login" not in st.session_state:
    st.session_state.login = False

# CASE 1: USER IS NOT LOGGED IN -> Show Portal Image & Login Form
if not st.session_state.login:
    col_login, col_img = st.columns([1, 2])
    
    with col_login:
        st.title("Student System Portal")
        input_user = st.text_input("Username / ID")
        input_pass = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            u_df_clean = df_users.copy()
            u_df_clean['Username'] = u_df_clean['Username'].astype(str).str.strip()
            
            match = u_df_clean[(u_df_clean['Username'] == str(input_user).strip()) & 
                               (u_df_clean['Password'].astype(str).str.strip() == str(input_pass).strip())]
            
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = str(input_user).strip()
                st.rerun()
            else:
                st.error("Invalid Username or Password")
                
    with col_img:
        st.header("WELCOME To the Portal")
        if os.path.exists("portal_image.png"):
            st.image("portal_image.png", use_container_width=True)
        else:
            st.info("💡 Place 'portal_image.png' in folder for the welcome visual.")

# CASE 2: USER IS LOGGED IN -> Show Logout Button in Sidebar
else:
    with st.sidebar:
        st.write(f"### Welcome, {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role.upper()}")
        st.divider()
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            st.session_state.login = False
            st.session_state.clear()
            st.rerun()
  # ==========================================
# 5. DASHBOARDS (RBAC Implementation)
# ==========================================
if st.session_state.login:
    role = st.session_state.role

    # --- ADMIN DASHBOARD (Full Access) ---
    if role == "admin":
        st.markdown('<div class="user-icon">👤</div>', unsafe_allow_html=True)
        st.title("Administrator Control Panel")

        tab1, tab2 = st.tabs(["📊 Records Management", "➕ Register New Student"])

        with tab1:
            st.subheader("Master Student Database")
            st.dataframe(df_students, use_container_width=True)
            # ... (Your existing Delete logic here) ...

        with tab2:
            st.subheader("Institutional Enrollment")
            # The Add Student form remains here, exclusive to Admin
            with st.form("add_form"):
                # ... (Your existing form code here) ...
                if st.form_submit_button("Save Student"):
                    # ... (Your existing save logic here) ...
                    st.success("Student added to system successfully.")

    # --- TEACHER DASHBOARD (Analytics & Predictions) ---
    elif role == "teacher":
        st.markdown('<div class="user-icon">👨‍🏫</div>', unsafe_allow_html=True)
        st.title("Teacher Analytics Portal")

        tab1, tab2 = st.tabs(["📈 Performance Analytics", "🔍 Individual Prediction"])

        with tab1:
            st.subheader("Class-Wide Performance Trends")
            # Adding Graphs for Teacher
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**Attendance vs. Performance Index**")
                st.scatter_chart(data=df_students, x="Attendence", y="Performance_Index", color="#ff4b4b")
            
            with col_b:
                st.write("**Grade Distribution**")
                grade_counts = df_students['Final_Result'].value_counts()
                st.bar_chart(grade_counts)

        with tab2:
            st.subheader("Predict Student Risk")
            selected_student = st.selectbox("Select Student for Analysis", df_students['Name'].unique())
            # Logic to show specific student graph or prediction result
            student_data = df_students[df_students['Name'] == selected_student].iloc[0]
            st.info(f"Predicting performance for {selected_student} based on current metrics...")
            # ... (Your Random Forest Prediction code here) ...
# ==========================================
# 5. STUDENT DASHBOARD (Cleaned & Fixed)
# ==========================================
elif st.session_state.login and st.session_state.role == "student":
    st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
    st.title("Student Academic Portal")
    
    # Robust ID Matching
    curr_id = str(st.session_state.username).strip()
    
    # Clean the dataframe IDs for comparison to handle Excel float issues (e.g., 101.0 -> 101)
    df_students_temp = df_students.copy()
    df_students_temp['Student_ID'] = df_students_temp['Student_ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
    
    my_row = df_students_temp[df_students_temp['Student_ID'] == curr_id]

    if not my_row.empty:
        data = my_row.iloc[0]
        st.subheader(f"Welcome, {data['Name']}")
        
        # Dashboard Layout
        c1, c2, c3 = st.columns(3)
        
        # Formatting Attendance safely
        try:
            att_val = f"{int(float(data['Attendence']))}%"
        except:
            att_val = f"{data['Attendence']}%"
            
        c1.metric("Attendance", att_val)
        c2.metric("Grade", data['Final_Result'])
        c3.metric("Study Hours", data['Study_Hours'])
        
        st.divider()
        
        # Visual progress bar
        try:
            st.write("**Attendance Progress**")
            st.progress(int(float(data['Attendence'])) / 100)
        except:
            pass

        # Generate and Download PDF
        # We wrap this in a button to ensure it only generates when needed
        pdf_report = generate_pdf(data)
        st.download_button(
            label="📥 Download Official Report Card",
            data=pdf_report,
            file_name=f"Report_{curr_id}.pdf",
            mime="application/pdf",
            key="student_download_pdf"
        )
    else:
        st.error(f"Record for ID {curr_id} not found in Student_Data. Please contact the administrator.")
            
