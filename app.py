import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. PAGE SETUP & DATA ENGINE
# ==========================================
st.set_page_config(page_title="Student Performance System", layout="wide")

FILE_NAME = "student_performance.xlsx"

def load_all_data():
    if not os.path.exists(FILE_NAME):
        st.error(f"Excel file '{FILE_NAME}' not found!")
        return None, None, None
    
    # Load and clean headers immediately
    s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
    p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")
    
    s_df.columns = s_df.columns.str.strip()
    u_df.columns = u_df.columns.str.strip()
    p_df.columns = p_df.columns.str.strip()
    
    return s_df, u_df, p_df

def save_to_excel(s, u, p):
    try:
        with pd.ExcelWriter(FILE_NAME, engine='openpyxl') as writer:
            s.to_excel(writer, sheet_name="Students_Data", index=False)
            u.to_excel(writer, sheet_name="Users", index=False)
            p.to_excel(writer, sheet_name="Predictions", index=False)
        return True
    except Exception as e:
        st.error(f"Save Failed: Ensure the Excel file is CLOSED. Error: {e}")
        return False

# Initial Load
df_students, df_users, df_preds = load_all_data()

# ==========================================
# 2. PDF GENERATION LOGIC
# ==========================================
def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    
    elements = [
        Paragraph("OFFICIAL STUDENT REPORT CARD", styles['Title']),
        Spacer(1, 20),
        Paragraph(f"<b>Name:</b> {row['Name']}", styles['Normal']),
        Paragraph(f"<b>Student ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1, 20)
    ]
    
    data = [
        ["Metric", "Score"],
        ["Attendance", f"{row['Attendence']}%"],
        ["Internal Marks", row['Internal_Marks']],
        ["Assignment Score", row['Assignment_Score']],
        ["Study Hours", row['Study_Hours']],
        ["Final Result", row['Final_Result']]
    ]
    
    table = Table(data, colWidths=[200, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# 3. LOGIN & AUTHENTICATION
# ==========================================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.title("System Portal")
        u_in = st.text_input("Username / ID")
        p_in = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            u_clean = df_users.copy()
            u_clean['Username'] = u_clean['Username'].astype(str).str.replace('.0', '', regex=False).str.strip().str.lower()
            
            user_val = str(u_in).strip().lower()
            pass_val = str(p_in).strip()
            
            match = u_clean[(u_clean['Username'] == user_val) & (u_clean['Password'].astype(str) == pass_val)]
            
            if not match.empty:
                st.session_state.login = True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = user_val
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    with c2:
        if os.path.exists("portal_image.png"):
            st.image("portal_image.png", use_container_width=True)

# ==========================================
# 4. PROTECTED CONTENT (ROLES)
# ==========================================
else:
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state.username}**")
        st.write(f"Role: **{st.session_state.role.upper()}**")
        if st.button("🚪 Logout", type="primary"):
            st.session_state.clear()
            st.rerun()

    # --- ADMIN DASHBOARD ---
    if st.session_state.role == "admin":
        st.title("Administrator Control Panel")
        t1, t2 = st.tabs(["📊 Records Management", "➕ Register New Student"])
        
        with t1:
            st.dataframe(df_students, use_container_width=True)
            
        with t2:
            st.subheader("Add New Student to Database")
            with st.form("add_student_form", clear_on_submit=True):
                new_id = st.text_input("Assign Student ID")
                new_name = st.text_input("Full Name")
                new_att = st.number_input("Starting Attendance %", 0, 100, 75)
                new_pass = st.text_input("Assign Password", "1111")
                
                if st.form_submit_button("Save to Excel"):
                    if new_id and new_name:
                        # Add to Students_Data
                        new_s = pd.DataFrame([{"Student_ID": new_id, "Name": new_name, "Attendence": new_att, 
                                               "Internal_Marks": 0, "Assignment_Score": 0, "Study_Hours": 0, "Final_Result": "Pending"}])
                        # Add to Users
                        new_u = pd.DataFrame([{"Username": new_id, "Password": new_pass, "Role": "student"}])
                        
                        updated_s = pd.concat([df_students, new_s], ignore_index=True)
                        updated_u = pd.concat([df_users, new_u], ignore_index=True)
                        
                        if save_to_excel(updated_s, updated_u, df_preds):
                            st.success(f"Student {new_name} saved successfully!")
                            st.rerun()
                    else:
                        st.warning("Please fill all required fields.")

    # --- TEACHER DASHBOARD ---
    elif st.session_state.role == "teacher":
        st.title("Teacher Analytics Portal")
        t1, t2 = st.tabs(["📉 Class Analytics", "🎯 Prediction Risk"])
        
        with t1:
            st.write("### Attendance vs. Performance Index")
            st.scatter_chart(df_students, x="Attendence", y="Performance_Index")
            st.bar_chart(df_students['Final_Result'].value_counts())
            
        with t2:
            st.subheader("Predict Student Performance Risk")
            sel_name = st.selectbox("Select Student for Analysis", df_students['Name'].unique())
            stud = df_students[df_students['Name'] == sel_name].iloc[0]
            
            risk = "HIGH RISK" if stud['Attendence'] < 70 else "LOW RISK"
            st.warning(f"Prediction for {sel_name}: **{risk}**")
            st.write(f"Current Metrics: Attendance {stud['Attendence']}%, Score {stud['Internal_Marks']}")

    # --- STUDENT DASHBOARD ---
    elif st.session_state.role == "student":
        st.title("Student Academic Portal")
        
        # ID Normalization (Matches user_101 to 101)
        search_id = st.session_state.username.replace('user_', '')
        s_clean = df_students.copy()
        s_clean['Student_ID'] = s_clean['Student_ID'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        my_record = s_clean[s_clean['Student_ID'] == search_id]
        
        if not my_record.empty:
            data = my_record.iloc[0]
            st.subheader(f"Welcome, {data['Name']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Attendance", f"{data['Attendence']}%")
            c2.metric("Grade", data['Final_Result'])
            c3.metric("Study Hours", f"{data['Study_Hours']} hrs")
            
            st.divider()
            pdf = generate_pdf(data)
            st.download_button(label="📥 Download My Report Card (PDF)", data=pdf, file_name=f"Report_{search_id}.pdf")
        else:
            st.error(f"No record found for ID: {search_id}. Please contact Admin.")
