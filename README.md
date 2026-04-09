# 🎓 Student Prediction System
A multi-user Streamlit web application designed for educational institutions to manage student records, calculate performance indices, and generate digital report cards. The system features a role-based access control (RBAC) system for Admins, Teachers, and Students.
# ✨ Features
 - **🛡️ Admin Dashboard**
* User Management: Add or delete student records from the database.
* Automatic Account Creation: New students are automatically assigned login credentials.
* Database Sync: Manage the Excel-based data storage directly from the UI.
- **👨‍🏫 Teacher Dashboard**
* Performance Analytics: View total student count, class toppers, and students needing attention.
* Comparative Analysis: Compare two students side-by-side across multiple metrics (Attendance, Marks, Assignments, etc.).
* Data Visualization: Interactive bar charts showing class performance distributions.
- **🎓 Student Dashboard**
* Personalized View: Students can only view their own performance metrics.
* Progress Tracking: Interactive progress bars for attendance and line charts for performance trends.
* PDF Report Cards: One-click download of official digital report cards generated via ReportLab.
# 🛠️ Technology Stack
- Frontend/Backend: Streamlit
- Data Handling: Pandas & Openpyxl
- PDF Generation: ReportLab
- Database: Excel (.xlsx)
**🚀 Getting Started**
Prerequisites
Python 3.8 or higher
Pip (Python package manager)
