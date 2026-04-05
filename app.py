import streamlit as st
import pandas as pd
import os
import glob
from io import BytesIO
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Student Performance System", layout="wide")

FILE_NAME = "student_performance.xlsx"
REPORT_FOLDER = "report_cards"
os.makedirs(REPORT_FOLDER, exist_ok=True)

# =========================
# FUNCTIONS
# =========================
def load_all_data():
    # Create empty file if not exists
    if not os.path.exists(FILE_NAME):
        s_df = pd.DataFrame(columns=["Student_ID","Name","Attendence","Internal_Marks",
                                     "Assignment_Score","Study_Hours","Final_Result"])
        u_df = pd.DataFrame(columns=["Username","Password","Role"])
        p_df = pd.DataFrame(columns=["Student_ID","Prediction"])
        save_to_excel(s_df, u_df, p_df)
    
    s_df = pd.read_excel(FILE_NAME, sheet_name="Students_Data")
    u_df = pd.read_excel(FILE_NAME, sheet_name="Users")
    # Predictions sheet optional
    try:
        p_df = pd.read_excel(FILE_NAME, sheet_name="Predictions")
    except:
        p_df = pd.DataFrame(columns=["Student_ID","Prediction"])
    
    # Strip headers
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
        st.error(f"Save Failed: Close Excel file. Error: {e}")
        return False

def predict_risk(row):
    idx = row['Performance_Index']
    if idx < 40:
        return "HIGH RISK"
    elif idx < 70:
        return "MEDIUM RISK"
    else:
        return "LOW RISK"

def generate_pdf(row):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    
    elements = [
        Paragraph("OFFICIAL STUDENT REPORT CARD", styles['Title']),
        Spacer(1,20),
        Paragraph(f"<b>Name:</b> {row['Name']}", styles['Normal']),
        Paragraph(f"<b>Student ID:</b> {row['Student_ID']}", styles['Normal']),
        Spacer(1,20)
    ]
    
    data = [
        ["Metric","Score"],
        ["Attendance", f"{row['Attendence']}%"],
        ["Internal Marks", row['Internal_Marks']],
        ["Assignment Score", row['Assignment_Score']],
        ["Study Hours", row['Study_Hours']],
        ["Final Result", row['Final_Result']],
        ["Performance Index", f"{row['Performance_Index']:.2f}"],
        ["Predicted Risk", row['Risk']],
        ["Extra Activities", row.get('Extra_Activities',"N/A")],
        ["Previous Results", row.get('Previous_Results',"N/A")]
    ]
    
    table = Table(data, colWidths=[200,120])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('ALIGN',(0,0),(-1,-1),'CENTER')
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    # Save PDF with timestamp
    pdf_path = os.path.join(REPORT_FOLDER, f"Report_{row['Student_ID']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    with open(pdf_path,"wb") as f:
        f.write(buffer.getbuffer())
    buffer.seek(0)
    return buffer

def save_student_result(student_row):
    # Compute Performance Index and Risk
    student_row['Performance_Index'] = (
        student_row['Internal_Marks']*0.5 +
        student_row['Assignment_Score']*0.3 +
        student_row['Attendence']*0.2
    )
    student_row['Risk'] = predict_risk(student_row)
    student_row['Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save to Results_History sheet
    try:
        df_history = pd.read_excel(FILE_NAME, sheet_name="Results_History")
    except:
        df_history = pd.DataFrame()
    
    df_history = pd.concat([df_history, pd.DataFrame([student_row])], ignore_index=True)
    
    with pd.ExcelWriter(FILE_NAME, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_history.to_excel(writer, sheet_name="Results_History", index=False)

# =========================
# LOAD DATA
# =========================
df_students, df_users, df_preds = load_all_data()

# Compute Performance Index & Risk for display
if not df_students.empty:
    df_students['Performance_Index'] = (
        df_students['Internal_Marks']*0.5 +
        df_students['Assignment_Score']*0.3 +
        df_students['Attendence']*0.2
    )
    df_students['Risk'] = df_students.apply(predict_risk, axis=1)
    
# Add placeholders
if 'Previous_Results' not in df_students.columns:
    df_students['Previous_Results'] = "N/A"
if 'Extra_Activities' not in df_students.columns:
    df_students['Extra_Activities'] = "N/A"

# =========================
# LOGIN SESSION
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    c1,c2 = st.columns([1,2])
    with c1:
        st.title("Student Performance System Login")
        u_in = st.text_input("Username / ID")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In"):
            u_clean = df_users.copy()
            u_clean['Username'] = u_clean['Username'].astype(str).str.strip().str.lower()
            user_val = str(u_in).strip().lower()
            pass_val = str(p_in).strip()
            match = u_clean[(u_clean['Username']==user_val) & (u_clean['Password'].astype(str)==pass_val)]
            if not match.empty:
                st.session_state.login=True
                st.session_state.role = match.iloc[0]['Role'].strip().lower()
                st.session_state.username = user_val
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    with c2:
        if os.path.exists("portal_image.png"):
            st.image("portal_image.png", use_container_width=True)

# =========================
# PROTECTED DASHBOARD
# =========================
else:
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state.username}**")
        st.write(f"Role: **{st.session_state.role.upper()}**")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    
    # --- ADMIN ---
    if st.session_state.role=="admin":
        st.title("Administrator Control Panel")
        t1,t2 = st.tabs(["📊 Records Management","➕ Add New Student"])
        with t1:
            st.dataframe(df_students,use_container_width=True)
            st.download_button("📥 Download All Students CSV", df_students.to_csv(index=False).encode('utf-8'), file_name="students.csv")
        with t2:
            st.subheader("Add New Student")
            with st.form("add_form",clear_on_submit=True):
                new_id = st.text_input("Student ID")
                new_name = st.text_input("Full Name")
                new_att = st.number_input("Attendance %",0,100,75)
                new_pass = st.text_input("Password","1111")
                if st.form_submit_button("Save"):
                    if new_id and new_name:
                        # Reload latest data
                        df_students, df_users, df_preds = load_all_data()
                        new_s = pd.DataFrame([{
                            "Student_ID": new_id,
                            "Name": new_name,
                            "Attendence": new_att,
                            "Internal_Marks": 0,
                            "Assignment_Score": 0,
                            "Study_Hours":0,
                            "Final_Result":"Pending",
                            "Previous_Results":"N/A",
                            "Extra_Activities":"N/A"
                        }])
                        new_u = pd.DataFrame([{
                            "Username": new_id,
                            "Password": new_pass,
                            "Role":"student"
                        }])
                        df_students = pd.concat([df_students,new_s],ignore_index=True)
                        df_users = pd.concat([df_users,new_u],ignore_index=True)
                        if save_to_excel(df_students,df_users,df_preds):
                            st.success(f"Student {new_name} added successfully!")
                            st.rerun()
                    else:
                        st.warning("Fill all fields")
    
    # --- TEACHER ---
    elif st.session_state.role=="teacher":
        st.title("Teacher Dashboard")
        t1,t2 = st.tabs(["📊 Class Analytics","🎯 Predict Student Risk"])
        with t1:
            if not df_students.empty:
                st.bar_chart(df_students['Risk'].value_counts())
        with t2:
            sel_name = st.selectbox("Select Student", df_students['Name'].unique())
            stud = df_students[df_students['Name']==sel_name].iloc[0]
            st.warning(f"{sel_name} Risk: {stud['Risk']}")
            st.write(f"Attendance {stud['Attendence']}%, Internal Marks {stud['Internal_Marks']}, Assignments {stud['Assignment_Score']}")
            # Previous reports
            st.subheader(f"Previous Report Cards for {sel_name}")
            pdf_files = glob.glob(f"{REPORT_FOLDER}/Report_{stud['Student_ID']}_*.pdf")
            if pdf_files:
                for f in pdf_files:
                    st.download_button(os.path.basename(f), data=open(f,"rb"), file_name=os.path.basename(f))
            else:
                st.info("No previous reports found.")
    
    # --- STUDENT ---
    elif st.session_state.role=="student":
        st.title("Student Dashboard")
        search_id = st.session_state.username.replace("user_","")
        s_clean = df_students.copy()
        s_clean['Student_ID'] = s_clean['Student_ID'].astype(str).str.strip()
        my_record = s_clean[s_clean['Student_ID']==search_id]
        if not my_record.empty:
            data = my_record.iloc[0]
            st.subheader(f"Welcome, {data['Name']}")
            c1,c2,c3 = st.columns(3)
            c1.metric("Attendance",f"{data['Attendence']}%")
            c2.metric("Grade",data['Final_Result'])
            c3.metric("Study Hours",f"{data['Study_Hours']} hrs")
            st.metric("Performance Index",f"{data['Performance_Index']:.2f}")
            st.metric("Predicted Risk",data['Risk'])
            # Generate PDF
            pdf = generate_pdf(data)
            st.download_button("📥 Download Latest Report Card", pdf, file_name=f"Report_{search_id}.pdf")
            # Previous PDFs
            st.subheader("Previous Report Cards")
            pdf_files = glob.glob(f"{REPORT_FOLDER}/Report_{search_id}_*.pdf")
            if pdf_files:
                for f in pdf_files:
                    st.download_button(os.path.basename(f), data=open(f,"rb"), file_name=os.path.basename(f))
            else:
                st.info("No previous reports found.")
