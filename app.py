import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. CORE BUSINESS LOGIC LAYER (OOP)
# ==========================================
class PerformanceEngine:
    """Academic Intelligence Engine for calculations and predictions."""
    
    @staticmethod
    def calculate_pi(att, marks, assign, study):
        """Calculates a weighted Performance Index (0-100)."""
        # Normalizing study hours (capped at 12 for 100%)
        study_score = min((study / 12) * 100, 100)
        # Weights: Marks 40%, Assign 20%, Att 20%, Study 20%
        pi = (marks * 0.4) + (assign * 0.2) + (att * 0.2) + (study_score * 0.2)
        return round(pi, 2)

    @staticmethod
    def get_ai_insights(att, marks, extra):
        """Heuristic-based engine to generate Risk Level and Suggestions."""
        if att < 75:
            return "Critical: Low attendance. Mandatory counseling required.", "High"
        elif marks < 45:
            return "Academic Alert: Subject-wise remediation suggested.", "Moderate"
        elif extra == "No":
            return "Holistic Growth: Engage in technical/cultural activities.", "Low"
        else:
            return "Excellent Progress: Maintain consistency.", "Low"

    @classmethod
    def process_dataframe(cls, df):
        """Transforms raw input data into processed ERP data."""
        s_list, u_list, p_list = [], [], []
        for _, row in df.iterrows():
            pi = cls.calculate_pi(row['Attendance'], row['Internal_Marks'], 
                                   row['Assignment_Score'], row['Study_Hours'])
            sugg, risk = cls.get_ai_insights(row['Attendance'], row['Internal_Marks'], 
                                             row['Extra_Activity'])
            
            s_list.append({**row, "Performance_Index": pi})
            p_list.append({"Student_ID": row['Student_ID'], "Predicted_Result": row['Final_Result'],
                           "Risk_Level": risk, "Suggestion": sugg})
            u_list.append({"Username": str(row['Student_ID']), "Password": "123", "Role": "student"})
            
        return pd.DataFrame(s_list), pd.DataFrame(u_list), pd.DataFrame(p_list)

# ==========================================
# 2. DATA ACCESS LAYER
# ==========================================
FILE_NAME = "student_erp_db.xlsx"

def load_system_data():
    if not os.path.exists(FILE_NAME):
        # Create default schema
        s = pd.DataFrame(columns=["Student_ID", "Name", "Attendance", "Study_Hours", "Internal_Marks", "Assignment_Score", "Extra_Activity", "Final_Result", "Performance_Index"])
        u = pd.DataFrame([{"Username": "admin", "Password": "admin123", "Role": "admin"},
                          {"Username": "teacher", "Password": "teacher123", "Role": "teacher"}])
        p = pd.DataFrame(columns=["Student_ID", "Predicted_Result", "Risk_Level", "Suggestion"])
        return s, u, p

    xls = pd.ExcelFile(FILE_NAME)
    return (pd.read_excel(xls, "Students_Data"), 
            pd.read_excel(xls, "Users"), 
            pd.read_excel(xls, "Predictions"))

def save_system_data(s, u, p):
    with pd.ExcelWriter(FILE_NAME, engine="openpyxl") as writer:
        s.to_excel(writer, sheet_name="Students_Data", index=False)
        u.to_excel(writer, sheet_name="Users", index=False)
        p.to_excel(writer, sheet_name="Predictions", index=False)

# ==========================================
# 3. UI COMPONENTS & VISUALS
# ==========================================
def render_radar(row):
    categories = ['Attendance', 'Marks', 'Assignments', 'Study Factor']
    values = [row['Attendance'], row['Internal_Marks'], row['Assignment_Score'], min((row['Study_Hours']/12)*100, 100)]
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='teal'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=350)
    return fig

# ==========================================
# 4. MAIN APPLICATION ROUTING
# ==========================================
st.set_page_config(page_title="IntelliStudent ERP", layout="wide")
df_students, df_users, df_preds = load_system_data()

if "auth" not in st.session_state:
    st.session_state.auth = {"status": False, "user": None, "role": None}

# --- LOGIN SCREEN ---
if not st.session_state.auth["status"]:
    st.title("🏛️ University ERP System")
    col1, col2 = st.columns([1, 1.5])
    with col1:
        with st.form("login_form"):
            uid = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Authenticate"):
                user_match = df_users[(df_users["Username"].astype(str) == uid) & (df_users["Password"].astype(str) == pwd)]
                if not user_match.empty:
                    st.session_state.auth = {"status": True, "user": uid, "role": user_match.iloc[0]["Role"].lower()}
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    with col2:
        st.info("### System Notice\n- Admins can manage student records.\n- Teachers can view class analytics.\n- Students can track personal progress.")

# --- DASHBOARD ---
else:
    role = st.session_state.auth["role"]
    user = st.session_state.auth["user"]

    with st.sidebar:
        st.title("Navigation")
        st.write(f"**Account:** {user.upper()}")
        st.write(f"**Role:** {role.capitalize()}")
        if st.button("🚪 System Logout", use_container_width=True):
            st.session_state.auth = {"status": False, "user": None, "role": None}
            st.rerun()

    # ADMIN MODULE
    if role == "admin":
        st.header("🛡️ Administrator Command Center")
        tab1, tab2 = st.tabs(["Individual Enrollment", "Bulk Data Import"])
        
        with tab1:
            with st.form("add_student"):
                c1, c2, c3 = st.columns(3)
                sid = c1.text_input("Student ID")
                name = c2.text_input("Name")
                extra = c3.selectbox("Extra Activity", ["Yes", "No"])
                
                c4, c5, c6, c7 = st.columns(4)
                att = c4.number_input("Attendance %", 0, 100, 75)
                mks = c5.number_input("Marks", 0, 100, 50)
                asg = c6.number_input("Assignment", 0, 100, 50)
                std = c7.number_input("Study Hours", 0, 15, 4)
                
                res = st.selectbox("Current Result", ["Pass", "Fail", "Pending"])
                if st.form_submit_button("Create Record"):
                    temp_df = pd.DataFrame([{"Student_ID": sid, "Name": name, "Attendance": att, "Study_Hours": std, "Internal_Marks": mks, "Assignment_Score": asg, "Extra_Activity": extra, "Final_Result": res}])
                    ns, nu, np = PerformanceEngine.process_dataframe(temp_df)
                    save_system_data(pd.concat([df_students, ns]), pd.concat([df_users, nu]), pd.concat([df_preds, np]))
                    st.success("Record Created!")
                    st.rerun()

        with tab2:
            st.write("Upload CSV/Excel with columns: `Student_ID, Name, Attendance, Study_Hours, Internal_Marks, Assignment_Score, Extra_Activity, Final_Result`")
            up_file = st.file_uploader("Select File")
            if up_file:
                input_df = pd.read_csv(up_file) if up_file.name.endswith('.csv') else pd.read_excel(up_file)
                if st.button("Commit Bulk Data"):
                    ns, nu, np = PerformanceEngine.process_dataframe(input_df)
                    save_system_data(pd.concat([df_students, ns]).drop_duplicates(subset="Student_ID"), 
                                     pd.concat([df_users, nu]).drop_duplicates(subset="Username"), 
                                     pd.concat([df_preds, np]).drop_duplicates(subset="Student_ID"))
                    st.success("Database Updated!")

    # TEACHER MODULE
    elif role == "teacher":
        st.header("👨‍🏫 Academic Analytics Dashboard")
        if not df_students.empty:
            merged = pd.merge(df_students, df_preds, on="Student_ID")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Class Average PI", round(merged["Performance_Index"].mean(), 2))
            c2.metric("High Risk Students", len(merged[merged["Risk_Level"] == "High"]))
            c3.metric("Total Enrollments", len(merged))
            
            st.divider()
            col_a, col_b = st.columns([1.5, 1])
            with col_a:
                st.write("#### Performance vs Attendance (Scatter Analysis)")
                fig = px.scatter(merged, x="Attendance", y="Performance_Index", color="Risk_Level", size="Study_Hours", hover_name="Name")
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                st.write("#### Data View")
                st.dataframe(merged[["Name", "Performance_Index", "Risk_Level"]], height=400)

    # STUDENT MODULE
    elif role == "student":
        st.header(f"🎓 Student Portal: {user}")
        s_rec = df_students[df_students["Student_ID"].astype(str) == user]
        p_rec = df_preds[df_preds["Student_ID"].astype(str) == user]
        
        if not s_rec.empty:
            data = s_rec.iloc[0]
            pred = p_rec.iloc[0]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Attendance", f"{data['Attendance']}%")
            m2.metric("Performance Index", data['Performance_Index'])
            m3.metric("Result Status", data['Final_Result'])
            
            st.divider()
            col_x, col_y = st.columns(2)
            with col_x:
                st.write("#### Performance Radar")
                st.plotly_chart(render_radar(data))
            with col_y:
                st.write("#### 🤖 AI Academic Insights")
                color = "red" if pred['Risk_Level'] == "High" else "orange" if pred['Risk_Level'] == "Moderate" else "green"
                st.markdown(f"""<div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 10px solid {color};">
                    <h3 style="color:{color}; margin-top:0;">{pred['Risk_Level']} Risk</h3>
                    <p><b>Predicted Outcome:</b> {pred['Predicted_Result']}</p>
                    <p><b>Recommendation:</b> {pred['Suggestion']}</p>
                </div>""", unsafe_allow_safe=True)
        else:
            st.warning("No academic records found for this ID.")
