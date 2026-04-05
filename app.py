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
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    # Use columns to put the login on the left and image on the right
    col_login, col_img = st.columns([1, 2])
    
    with col_login:
        st.title("Student System Portal")
        input_user = st.text_input("Username / ID")
        input_pass = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            # FIX: Convert both sides to string and strip whitespace
            u_df_clean = df_users.copy()
            u_df_clean['Username'] = u_df_clean['Username'].astype(str).str.strip()
            
            match = u_df_clean[(u_df_clean['Username'] == str(input_user).strip()) & 
                               (u_df_clean['Password'].astype(str).str.strip() == str(input_pass).strip())]
            
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = str(input_user).strip() # Store as clean string
                st.rerun()
            else:
                st.error("Invalid Username or Password")
                
    with col_img:
        st.header("WELCOME, To the Portal")
        # Ensure 'portal_image.png' is in your project folder
        if os.path.exists("portal_image.png"):
            st.image("portal_image.png", use_container_width=True, caption="Engaged Learning Environment")
        else:
            st.info("💡 Tip: Save your project image as 'portal_image.png' to see it here.")


# ==========================================
# 5. DASHBOARDS
# ==========================================
if st.session_state.login:
    role = st.session_state.role

    # --- ADMIN & TEACHER DASHBOARD ---
    if role in ["admin", "teacher"]:
        icon = "👤" if role == "admin" else "👨‍🏫"
        st.markdown(f'<div class="user-icon">{icon}</div>', unsafe_allow_html=True)
        st.title(f"{role.capitalize()} Dashboard")

        tab1, tab2 = st.tabs(["📊 Records & Management", "➕ Register New Student"])

        with tab1:
            st.subheader("Student Database Overview")
            st.dataframe(df_students, use_container_width=True)
            
            st.divider()
            st.subheader("🗑️ Delete Student Record")
            del_id = st.text_input("Enter Student ID to delete from all 3 sheets:")
            if st.button("Delete Permanently", type="primary"):
                if del_id:
                    # Sync removal across all dataframes
                    df_students = df_students[df_students['Student_ID'].astype(str) != str(del_id)]
                    df_users = df_users[df_users['Username'].astype(str) != str(del_id)]
                    df_preds = df_preds[df_preds['Student_ID'].astype(str) != str(del_id)]
                    
                    save_all_sheets(df_students, df_users, df_preds)
                    st.success(f"Record {del_id} deleted successfully.")
                    st.rerun()

        with tab2:
            st.subheader("Add Student to System")
            with st.form("add_form"):
                c1, c2 = st.columns(2)
                nid = c1.text_input("New Student ID")
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

                if st.form_submit_button("Save Student"):
                    # Update all 3 sheets
                    new_s = pd.DataFrame([{"Student_ID": nid, "Name": nname, "Attendence": natt, "Study_Hours": nhrs, "Internal_Marks": nim, "Assignment_Score": nas, "Previous_Result": nprev, "Extra_Activities": nextra, "Final_Result": nfinal, "Performance_Index": nperf}])
                    df_students = pd.concat([df_students, new_s], ignore_index=True)
                    
                    new_u = pd.DataFrame([{"Username": nid, "Password": "123", "Role": "student"}])
                    df_users = pd.concat([df_users, new_u], ignore_index=True)
                    
                    new_p = pd.DataFrame([{"Student_ID": nid, "Predicted_Result": "PENDING"}])
                    df_preds = pd.concat([df_preds, new_p], ignore_index=True)
                    
                    save_all_sheets(df_students, df_users, df_preds)
                    st.success(f"Student Registered! User ID: {nid} | Pass: 123")
# ==========================================
# 5. STUDENT DASHBOARD (Fixed Download Logic)
# ==========================================
elif st.session_state.login and st.session_state.role == "student":
    st.markdown('<div class="user-icon">🧑‍🎓</div>', unsafe_allow_html=True)
    st.title("Student Academic Portal")
    
    # FIX: Robust ID Matching
    curr_id = st.session_state.username
    # Clean the dataframe IDs for comparison
    df_students_temp = df_students.copy()
    df_students_temp['Student_ID'] = df_students_temp['Student_ID'].astype(str).str.strip().str.replace('.0', '', regex=False)
    
    my_row = df_students_temp[df_students_temp['Student_ID'] == curr_id]

    if not my_row.empty:
        data = my_row.iloc[0]
        st.subheader(f"Welcome, {data['Name']}")
        
        # Dashboard Layout
        c1, c2, c3 = st.columns(3)
        # Using .get() or direct access with error handling for the PDF
        try:
            c1.metric("Attendance", f"{int(float(data['Attendence']))}%")
        except:
            c1.metric("Attendance", f"{data['Attendence']}%")
            
        c2.metric("Grade", data['Final_Result'])
        c3.metric("Study Hours", data['Study_Hours'])
        
        st.divider()
        # Generate and Download
        pdf_report = generate_pdf(data)
        st.download_button(
            label="📥 Download Official Report Card",
            data=pdf_report,
            file_name=f"Report_{curr_id}.pdf",
            mime="application/pdf",
            key="download-btn"
        )
    else:
        st.error(f"Record for ID {curr_id} not found in Student_Data sheet. Please contact Admin.")

            
            # PDF Generation
            pdf_report = generate_pdf(data)
            st.download_button("📥 Download Official Report Card", pdf_report, file_name=f"Report_{curr_id}.pdf")
        else:
            st.error(f"Data not found for ID {curr_id}. Please contact Admin.")
