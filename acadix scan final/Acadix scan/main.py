import sys
from datetime import datetime

import pandas as pd
from PyQt5.QtCore import Qt, QDate
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QScrollArea,
    QGridLayout,
    QProgressBar,
    QFrame,
)
from PyQt5.QtGui import QFontDatabase, QFont

from data_manager import (
    register_student,
    authenticate_student,
    forgot_password_flow,
    list_all_students,
    total_registered_students,
    attendance_summary_for_date,
    attendance_in_range,
    editable_student_fields,
    save_students_dataframe,
    update_student_profile,
    get_internal_marks,
    get_student_internal_marks,
    upsert_internal_marks,
    low_attendance_report,
    send_alert,
)
from ui_components import SplashScreen, RoleSelection, StudentLogin, AdminLogin, StudentSignup, AssistantWidget
from face_utils import capture_faces_from_ipcam, train_model, recognize_from_ipcam_and_mark


ADMIN_ID = "teacher@coe"
ADMIN_PWD = "Python@313"


# Load application stylesheet
def load_stylesheet():
    stylesheet = ""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(base_dir, "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                stylesheet = f.read()
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
    return stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acadix Scan")
        self.resize(1200, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Auth flow
        self.splash = SplashScreen(self.to_role_selection)
        self.role = RoleSelection(self.to_student_login, self.to_admin_login)
        self.student_login = StudentLogin(self.student_do_login, self.to_student_signup, self.student_forgot)
        self.admin_login = AdminLogin(self.admin_do_login)
        self.student_signup = StudentSignup(self.student_do_signup)

        self.stack.addWidget(self.splash)
        self.stack.addWidget(self.role)
        self.stack.addWidget(self.student_login)
        self.stack.addWidget(self.admin_login)
        self.stack.addWidget(self.student_signup)

        # Main app containers
        self.app_container = QWidget()
        self.stack.addWidget(self.app_container)

        self.current_user = None  # dict for student, or None for admin
        self.is_admin = False

        self.stack.setCurrentWidget(self.splash)

    # Navigation helpers
    def to_role_selection(self):
        self.stack.setCurrentWidget(self.role)

    def to_student_login(self):
        self.stack.setCurrentWidget(self.student_login)

    def to_admin_login(self):
        self.stack.setCurrentWidget(self.admin_login)

    def to_student_signup(self):
        self.stack.setCurrentWidget(self.student_signup)

    # Auth actions
    def student_do_signup(self, data: dict):
        ok, msg = register_student(data)
        QMessageBox.information(self, "Signup", msg if ok else msg)
        if ok:
            self.to_student_login()

    def student_do_login(self, student_id: str, password: str):
        ok, user = authenticate_student(student_id, password)
        if not ok:
            QMessageBox.warning(self, "Login", "Invalid credentials.")
            return
        self.current_user = user
        self.is_admin = False
        self.init_main_app()

    def student_forgot(self, student_id: str):
        if not student_id:
            QMessageBox.information(self, "Forgot Password", "Enter Student ID first.")
            return
        # Simple prompt via input dialogs
        from PyQt5.QtWidgets import QInputDialog

        answer, ok = QInputDialog.getText(self, "Security Question", "What is your best friend's name?")
        if not ok:
            return
        ok2, user = forgot_password_flow(student_id, answer)
        if ok2 and user:
            self.current_user = user
            self.is_admin = False
            self.init_main_app()
        else:
            QMessageBox.warning(self, "Forgot Password", "Security answer incorrect or user not found.")

    def admin_do_login(self, admin_id: str, password: str):
        if admin_id == ADMIN_ID and password == ADMIN_PWD:
            self.current_user = None
            self.is_admin = True
            self.init_main_app()
        else:
            QMessageBox.warning(self, "Admin Login", "Invalid admin credentials.")

    # Main app UI
    def init_main_app(self):
        # Main window after login
        self.setWindowTitle("Acadix - Face Recognition Attendance System")
        self.resize(1000, 700)  # Larger default size for better UI experience
        
        # Main layout with splitter for resizable panels
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create AI Assistant widget
        self.assistant = AssistantWidget()
        self.assistant.setParent(main_widget)
        
        # Create a splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Navigation sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(
            "#sidebar { background-color: #0000ff; border: none; }"
        )
        
        nav_layout = QVBoxLayout(sidebar)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # App logo/branding with image and text
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(15, 20, 15, 20)
        logo_layout.setSpacing(10)
        
        # Try to add app logo
        logo_added = False
        try:
            from PyQt5.QtGui import QPixmap
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Prioritize om1.png as requested, then logo.png, then om.jpg
            logo_candidates = [
                os.path.join(base_dir, "assets", "om1.png"),
                os.path.join(base_dir, "assets", "logo.png"),
                os.path.join(base_dir, "assets", "om.jpg"),
            ]

            for path in logo_candidates:
                if os.path.exists(path):
                    try:
                        logo_image = QLabel()
                        pixmap = QPixmap(path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            logo_image.setPixmap(scaled_pixmap)
                            logo_image.setFixedSize(40, 40)
                            logo_layout.addWidget(logo_image)
                            logo_added = True
                            break
                    except Exception:
                        pass
                    
        except ImportError:
            pass  # SVG not available, try PNG only
            
        if not logo_added:
            # Add a small icon as fallback
            fallback_icon = QLabel("🎦")
            fallback_icon.setStyleSheet("font-size: 24px; color: white;")
            fallback_icon.setFixedSize(40, 40)
            fallback_icon.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(fallback_icon)
        
        # Logo text container
        logo_text_container = QWidget()
        logo_text_layout = QVBoxLayout(logo_text_container)
        logo_text_layout.setContentsMargins(0, 0, 0, 0)
        logo_text_layout.setSpacing(0)
        
        logo_label = QLabel("ACADIX")
        logo_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white; letter-spacing: 1px;"
        )
        
        logo_subtitle = QLabel("SCAN")
        logo_subtitle.setStyleSheet(
            "font-size: 12px; font-weight: 500; color: rgba(255, 255, 255, 0.8); "
            "letter-spacing: 1px;"
        )
        
        logo_text_layout.addWidget(logo_label)
        logo_text_layout.addWidget(logo_subtitle)
        
        logo_layout.addWidget(logo_text_container)
        logo_layout.addStretch()
        nav_layout.addWidget(logo_container)
        
        # Navigation buttons container
        nav_buttons = QWidget()
        nav_buttons_layout = QVBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 10, 0, 10)
        nav_buttons_layout.setSpacing(5)
        
        # Create navigation buttons with icons (using emoji as placeholders)
        btn_dashboard = QPushButton("  Dashboard")
        btn_dashboard.setObjectName("nav-button")
        btn_dashboard.setProperty("class", "nav-button")
        btn_dashboard.clicked.connect(self.show_dashboard)
        btn_dashboard.setCheckable(True)
        btn_dashboard.setChecked(True)  # Default selected
        
        btn_train = QPushButton("  Train Face Data")
        btn_train.setObjectName("nav-button")
        btn_train.setProperty("class", "nav-button")
        btn_train.setCheckable(True)
        
        # Recognize button removed for students - moved to admin only
        
        btn_attendance = QPushButton("  Attendance")
        btn_attendance.setObjectName("nav-button")
        btn_attendance.setProperty("class", "nav-button")
        btn_attendance.clicked.connect(self.show_attendance)
        btn_attendance.setCheckable(True)
        
        btn_settings = QPushButton("  Settings")
        btn_settings.setObjectName("nav-button")
        btn_settings.setProperty("class", "nav-button")
        btn_settings.clicked.connect(self.show_settings)
        btn_settings.setCheckable(True)
        
        btn_logout = QPushButton("  Logout")
        btn_logout.setObjectName("nav-button")
        btn_logout.setProperty("class", "nav-button")
        btn_logout.clicked.connect(self.logout)
        
        if not self.is_admin:
            btn_train.clicked.connect(self.show_train)
            # Recognize functionality moved to admin only
        
        # Add buttons to navigation layout
        nav_buttons_layout.addWidget(btn_dashboard)
        if not self.is_admin:
            nav_buttons_layout.addWidget(btn_train)
        else:
            # Admin gets recognize functionality
            btn_recognize = QPushButton("  Recognize Face")
            btn_recognize.setObjectName("nav-button")
            btn_recognize.setProperty("class", "nav-button")
            btn_recognize.setCheckable(True)
            btn_recognize.clicked.connect(self.show_recognize)
            nav_buttons_layout.addWidget(btn_recognize)
            # Admin-only management buttons
            btn_add_student = QPushButton("  Manage Students")
            btn_add_student.setObjectName("nav-button")
            btn_add_student.setProperty("class", "nav-button")
            btn_add_student.setCheckable(False)
            btn_add_student.clicked.connect(self.show_add_student)
            nav_buttons_layout.addWidget(btn_add_student)

            # Admin-only academic records button
            btn_internal = QPushButton("  Academic Records")
            btn_internal.setObjectName("nav-button")
            btn_internal.setProperty("class", "nav-button")
            btn_internal.setCheckable(True)
            btn_internal.clicked.connect(self.show_internal_marks)
            nav_buttons_layout.addWidget(btn_internal)
            # Admin-only low attendance button
            btn_low_att = QPushButton("  Low Attendance")
            btn_low_att.setObjectName("nav-button")
            btn_low_att.setProperty("class", "nav-button")
            btn_low_att.setCheckable(True)
            btn_low_att.clicked.connect(self.show_low_attendance)
            nav_buttons_layout.addWidget(btn_low_att)
        # Student academic records button (view only)
        if not self.is_admin:
            btn_internal = QPushButton("  Academic Records")
            btn_internal.setObjectName("nav-button")
            btn_internal.setProperty("class", "nav-button")
            btn_internal.setCheckable(True)
            btn_internal.clicked.connect(self.show_internal_marks)
            nav_buttons_layout.addWidget(btn_internal)

        nav_buttons_layout.addWidget(btn_attendance)
        nav_buttons_layout.addWidget(btn_settings)
        nav_buttons_layout.addStretch(1)
        nav_buttons_layout.addWidget(btn_logout)
        
        nav_layout.addWidget(nav_buttons)
        
        # User info at bottom of sidebar
        if not self.is_admin and self.current_user:
            user_info = QWidget()
            user_info.setObjectName("user-info")
            user_info.setStyleSheet(
                "#user-info { background-color: rgba(255, 255, 255, 0.05); border-top: 1px solid rgba(255, 255, 255, 0.1); }"
            )
            user_layout = QHBoxLayout(user_info)
            
            # User avatar placeholder
            user_avatar = QLabel("👤")
            user_avatar.setStyleSheet("font-size: 18px; color: white;")
            
            # User name
            user_name = QLabel(self.current_user.get("FullName", "User"))
            user_name.setStyleSheet("color: white; font-weight: bold;")
            
            user_layout.addWidget(user_avatar)
            user_layout.addWidget(user_name)
            
            nav_layout.addWidget(user_info)
        
        # Content area
        content_widget = QWidget()
        content_widget.setObjectName("content")
        content_widget.setStyleSheet(
            "#content { background-color: #F8F9FA; border: none; }"
        )
        
        self.content = QVBoxLayout(content_widget)
        
        # Add widgets to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(content_widget)
        
        # Set initial sizes (sidebar: 250px, content: rest)
        splitter.setSizes([250, 750])
        splitter.setStretchFactor(1, 1)
        
        # Assistant widget (visible in main app) - moved to right bottom
        self.assistant = AssistantWidget()
        self.assistant.setParent(self)
        self.assistant.move(self.width() - 320, self.height() - 280)  # Right bottom corner
        self.assistant.show()
        
        # Set layout
        ct = QWidget(); ct.setLayout(QVBoxLayout())
        ct.layout().addWidget(splitter)
        self.app_container = ct
        self.stack.addWidget(ct)
        self.stack.setCurrentWidget(ct)
        
        # Show default view
        self.show_dashboard()

    def clear_content(self):
        while self.content.count():
            item = self.content.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def show_dashboard(self):
        self.clear_content()
        
        # Create a scroll area for the dashboard content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F8F9FA; }")
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # Dashboard header
        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        scroll_layout.addWidget(header)
        
        # Current date display
        current_date = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        current_date.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        scroll_layout.addWidget(current_date)
        
        if self.is_admin:
            # Admin dashboard
            
            # Stats row with cards
            stats_container = QWidget()
            stats_layout = QHBoxLayout(stats_container)
            stats_layout.setContentsMargins(0, 0, 0, 0)
            stats_layout.setSpacing(20)
            
            # Total students card
            total = total_registered_students()
            students_card = QWidget()
            students_card.setObjectName("card")
            students_card.setStyleSheet(
                "#card { border-left: 4px solid #4361EE; }"
            )
            students_layout = QVBoxLayout(students_card)
            
            students_icon = QLabel("👨‍🎓")
            students_icon.setStyleSheet("font-size: 24px;")
            
            students_count = QLabel(str(total))
            students_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #212529;")
            
            students_label = QLabel("Total Students")
            students_label.setStyleSheet("font-size: 14px; color: #6C757D;")
            
            students_layout.addWidget(students_icon)
            students_layout.addWidget(students_count)
            students_layout.addWidget(students_label)
            
            # Attendance today card
            today = datetime.now().strftime("%d-%m-%Y")
            summary = attendance_summary_for_date(today)
            
            attendance_card = QWidget()
            attendance_card.setObjectName("card")
            attendance_card.setStyleSheet(
                "#card { border-left: 4px solid #20C997; }"
            )
            attendance_layout = QVBoxLayout(attendance_card)
            
            attendance_icon = QLabel("📊")
            attendance_icon.setStyleSheet("font-size: 24px;")
            
            attendance_count = QLabel(f"{summary['present']} / {summary['total']}")
            attendance_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #212529;")
            
            attendance_label = QLabel("Today's Attendance")
            attendance_label.setStyleSheet("font-size: 14px; color: #6C757D;")
            
            attendance_layout.addWidget(attendance_icon)
            attendance_layout.addWidget(attendance_count)
            attendance_layout.addWidget(attendance_label)
            
            # Add cards to stats row
            stats_layout.addWidget(students_card)
            stats_layout.addWidget(attendance_card)
            
            # Add stats row to main layout
            scroll_layout.addWidget(stats_container)
            
            # Attendance Records section
            attendance_section = QWidget()
            attendance_section.setObjectName("card")
            attendance_layout = QVBoxLayout(attendance_section)
            
            attendance_header = QLabel("Attendance Records")
            attendance_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 15px;")
            
            import data_manager as dm
            att_df = dm._load_attendance_df()  # intentionally use internal for displaying full CSV
            att_table = self._df_to_table(att_df, editable=True)  # Make attendance table editable
            att_table.setStyleSheet(
                "QTableView { border: none; alternate-background-color: #F1F3F5; }"
                "QHeaderView::section { background-color: #4361EE; color: white; padding: 6px; }"
            )
            
            # Save attendance changes button
            save_att_btn = QPushButton("Save Attendance Changes")
            save_att_btn.setObjectName("primary")
            save_att_btn.setFixedWidth(200)
            
            def save_att_changes():
                updated_att = self._table_to_df(att_table)
                dm._save_attendance_df(updated_att)
                QMessageBox.information(self, "Success", "Attendance records saved successfully.")
                self.show_dashboard()  # Refresh dashboard
            
            save_att_btn.clicked.connect(save_att_changes)

            # Export buttons for attendance
            export_att_xlsx = QPushButton("Export Attendance to Excel")
            export_att_xlsx.setFixedWidth(200)
            export_att_csv = QPushButton("Export Attendance to CSV")
            export_att_csv.setFixedWidth(160)
            export_att_pdf = QPushButton("Save Attendance as PDF")
            export_att_pdf.setFixedWidth(180)

            def export_att_excel_handler():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Attendance as Excel', 'attendance.xlsx', 'Excel Files (*.xlsx)')
                if not path:
                    return
                try:
                    att_df.to_excel(path, index=False)
                    QMessageBox.information(self, 'Exported', f'Attendance exported to {path}')
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Export failed: {e}')

            def export_att_csv_handler():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Attendance as CSV', 'attendance.csv', 'CSV Files (*.csv)')
                if not path:
                    return
                try:
                    att_df.to_csv(path, index=False)
                    QMessageBox.information(self, 'Exported', f'Attendance exported to {path}')
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Export failed: {e}')

            def export_att_pdf_handler():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Attendance as PDF', 'attendance.pdf', 'PDF Files (*.pdf)')
                if not path:
                    return
                try:
                    # Try reportlab
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    c = canvas.Canvas(path, pagesize=letter)
                    text = c.beginText(40, 750)
                    rows = [att_df.columns.tolist()] + att_df.values.tolist()
                    for row in rows:
                        line = ' | '.join([str(x) for x in row])
                        text.textLine(line)
                    c.drawText(text)
                    c.save()
                    QMessageBox.information(self, 'Exported', f'Attendance saved to PDF: {path}')
                except Exception:
                    # Fallback: save HTML
                    html_path = path.replace('.pdf', '.html')
                    att_df.to_html(html_path, index=False)
                    QMessageBox.information(self, 'Fallback', f'Reportlab not available. Saved HTML to {html_path}. Convert to PDF externally.')

            export_att_xlsx.clicked.connect(export_att_excel_handler)
            export_att_csv.clicked.connect(export_att_csv_handler)
            export_att_pdf.clicked.connect(export_att_pdf_handler)

            # Add export buttons row
            att_export_row = QWidget()
            att_export_layout = QHBoxLayout(att_export_row)
            att_export_layout.setContentsMargins(0, 0, 0, 0)
            att_export_layout.addStretch()
            att_export_layout.addWidget(export_att_xlsx)
            att_export_layout.addWidget(export_att_csv)
            att_export_layout.addWidget(export_att_pdf)
            attendance_layout.addWidget(att_export_row)
            
            attendance_layout.addWidget(attendance_header)
            attendance_layout.addWidget(att_table)
            attendance_layout.addWidget(save_att_btn, 0, Qt.AlignRight)
            
            scroll_layout.addWidget(attendance_section)
            
            # Student Records section
            students_section = QWidget()
            students_section.setObjectName("card")
            students_layout = QVBoxLayout(students_section)
            
            students_header = QLabel("Student Records")
            students_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 15px;")
            
            students_df = list_all_students()
            table2 = self._df_to_table(students_df, editable=True)
            table2.setStyleSheet(
                "QTableView { border: none; alternate-background-color: #F1F3F5; }"
                "QHeaderView::section { background-color: #4361EE; color: white; padding: 6px; }"
            )
            
            save_btn = QPushButton("Save Changes")
            save_btn.setObjectName("primary")
            save_btn.setFixedWidth(150)
            
            def save_changes():
                updated = self._table_to_df(table2)
                save_students_dataframe(updated)
                QMessageBox.information(self, "Success", "Student records saved successfully.")
            
            save_btn.clicked.connect(save_changes)
            # Edit selected student button
            edit_btn = QPushButton("Edit Selected")
            edit_btn.setFixedWidth(150)

            def on_edit_selected():
                selected = table2.currentRow()
                if selected < 0:
                    QMessageBox.information(self, "Select", "Please select a student row to edit.")
                    return
                # Get StudentID from table
                cols = [table2.horizontalHeaderItem(i).text() for i in range(table2.columnCount())]
                try:
                    sid_index = cols.index('StudentID')
                except ValueError:
                    QMessageBox.warning(self, "Error", "StudentID column not found.")
                    return
                sid_item = table2.item(selected, sid_index)
                student_id = sid_item.text() if sid_item else ""
                if not student_id:
                    QMessageBox.warning(self, "Error", "Selected row has no StudentID.")
                    return

                # Load current student record
                import data_manager as dm
                student = dm.get_student_by_id(student_id)
                if not student:
                    QMessageBox.warning(self, "Not Found", "Student not found in database.")
                    return

                # Show simple edit dialog
                from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

                dlg = QDialog(self)
                dlg.setWindowTitle(f"Edit Student: {student.get('FullName','')}")
                form = QFormLayout(dlg)

                phone_edit = QLineEdit(student.get('StudentPhone',''))
                parent_edit = QLineEdit(student.get('ParentPhone',''))
                address_edit = QLineEdit(student.get('Address',''))
                password_edit = QLineEdit('')
                password_edit.setPlaceholderText('(leave blank to keep)')
                pwd_confirm = QLineEdit('')
                pwd_confirm.setPlaceholderText('(confirm if changing)')
                security_edit = QLineEdit(student.get('SecurityAnswer',''))

                form.addRow('Student Phone', phone_edit)
                form.addRow("Parent's Phone", parent_edit)
                form.addRow('Address', address_edit)
                form.addRow('New Password', password_edit)
                form.addRow('Confirm Password', pwd_confirm)
                form.addRow('Security Answer', security_edit)

                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dlg.accept)
                buttons.rejected.connect(dlg.reject)
                form.addRow(buttons)

                if dlg.exec_() == QDialog.Accepted:
                    updates = {
                        'StudentPhone': phone_edit.text().strip(),
                        'ParentPhone': parent_edit.text().strip(),
                        'Address': address_edit.text().strip(),
                        'SecurityAnswer': security_edit.text().strip(),
                    }
                    new_pwd = password_edit.text().strip()
                    confirm_pwd = pwd_confirm.text().strip()
                    if new_pwd:
                        if new_pwd != confirm_pwd:
                            QMessageBox.warning(self, 'Password', 'New password and confirm password do not match.')
                            return
                        updates['Password'] = new_pwd

                    ok, msg = update_student_profile(student_id, updates)
                    if ok:
                        QMessageBox.information(self, 'Updated', msg)
                        # refresh dashboard which will reload the students table
                        self.show_dashboard()
                    else:
                        QMessageBox.warning(self, 'Error', msg)

            edit_btn.clicked.connect(on_edit_selected)
            # Place edit and save buttons side by side
            btn_row = QWidget()
            btn_layout = QHBoxLayout(btn_row)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.addStretch()
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(save_btn)

            students_layout.addWidget(students_header)
            students_layout.addWidget(table2)
            students_layout.addWidget(btn_row, 0, Qt.AlignRight)

            # Export buttons for students
            export_st_xlsx = QPushButton('Export Students to Excel')
            export_st_xlsx.setFixedWidth(200)
            export_st_csv = QPushButton('Export Students to CSV')
            export_st_csv.setFixedWidth(160)
            export_st_pdf = QPushButton('Save Students as PDF')
            export_st_pdf.setFixedWidth(180)

            def export_st_excel():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Students as Excel', 'students.xlsx', 'Excel Files (*.xlsx)')
                if not path:
                    return
                try:
                    students_df.to_excel(path, index=False)
                    QMessageBox.information(self, 'Exported', f'Students exported to {path}')
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Export failed: {e}')

            def export_st_csv_handler():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Students as CSV', 'students.csv', 'CSV Files (*.csv)')
                if not path:
                    return
                try:
                    students_df.to_csv(path, index=False)
                    QMessageBox.information(self, 'Exported', f'Students exported to {path}')
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Export failed: {e}')

            def export_st_pdf_handler():
                from PyQt5.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(self, 'Save Students as PDF', 'students.pdf', 'PDF Files (*.pdf)')
                if not path:
                    return
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    c = canvas.Canvas(path, pagesize=letter)
                    text = c.beginText(40, 750)
                    rows = [students_df.columns.tolist()] + students_df.values.tolist()
                    for row in rows:
                        line = ' | '.join([str(x) for x in row])
                        text.textLine(line)
                    c.drawText(text)
                    c.save()
                    QMessageBox.information(self, 'Exported', f'Students saved to PDF: {path}')
                except Exception:
                    html_path = path.replace('.pdf', '.html')
                    students_df.to_html(html_path, index=False)
                    QMessageBox.information(self, 'Fallback', f'Reportlab not available. Saved HTML to {html_path}. Convert to PDF externally.')

            export_st_xlsx.clicked.connect(export_st_excel)
            export_st_csv.clicked.connect(export_st_csv_handler)
            export_st_pdf.clicked.connect(export_st_pdf_handler)

            st_export_row = QWidget()
            st_export_layout = QHBoxLayout(st_export_row)
            st_export_layout.setContentsMargins(0, 0, 0, 0)
            st_export_layout.addStretch()
            st_export_layout.addWidget(export_st_xlsx)
            st_export_layout.addWidget(export_st_csv)
            st_export_layout.addWidget(export_st_pdf)
            students_layout.addWidget(st_export_row)
            
            scroll_layout.addWidget(students_section)
            
        else:
            # Student dashboard
            
            # Welcome message
            welcome = QLabel(f"Welcome back, {self.current_user.get('FullName', '')}!")
            welcome.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 20px;")
            scroll_layout.addWidget(welcome)
            
            # Stats row with cards
            stats_container = QWidget()
            stats_layout = QHBoxLayout(stats_container)
            stats_layout.setContentsMargins(0, 0, 0, 0)
            stats_layout.setSpacing(20)
            
            # Attendance card - show student's personal attendance
            today = datetime.now().strftime("%d-%m-%Y")
            from data_manager import student_attendance_summary_for_date
            student_prn = self.current_user.get("PRN", "")
            summary = student_attendance_summary_for_date(today, student_prn)
            
            attendance_card = QWidget()
            attendance_card.setObjectName("card")
            attendance_card.setStyleSheet(
                "#card { border-left: 4px solid #20C997; }"
            )
            attendance_layout = QVBoxLayout(attendance_card)
            
            attendance_icon = QLabel("📊")
            attendance_icon.setStyleSheet("font-size: 24px;")
            
            # Show Present/Absent status for students
            if summary['present'] > 0:
                status_text = "Present"
                status_color = "#20C997"  # Green
                status_icon = "✅"
            else:
                status_text = "Absent"
                status_color = "#DC3545"  # Red
                status_icon = "❌"
            
            attendance_count = QLabel(f"{status_icon} {status_text}")
            attendance_count.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {status_color};")
            
            attendance_label = QLabel("My Attendance Today")
            attendance_label.setStyleSheet("font-size: 14px; color: #6C757D;")
            
            attendance_layout.addWidget(attendance_icon)
            attendance_layout.addWidget(attendance_count)
            attendance_layout.addWidget(attendance_label)
            
            # Add cards to stats row
            stats_layout.addWidget(attendance_card)
            
            # Add stats row to main layout
            scroll_layout.addWidget(stats_container)
            
            # Replace personal details with Upcoming Events & Notices and Alerts
            events_card = QWidget()
            events_card.setObjectName("card")
            events_layout = QVBoxLayout(events_card)
            events_header = QLabel("Upcoming Events & Notices")
            events_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 15px;")
            events_layout.addWidget(events_header)

            notices = [
                "Internal assessment schedule will be announced soon.",
                "Mid-sem examination tentative window next month.",
                "Attend workshop on AI/ML this Friday, 3 PM.",
            ]
            for note in notices:
                lbl = QLabel("• " + note)
                lbl.setStyleSheet("color: #495057; margin: 4px 0;")
                events_layout.addWidget(lbl)

            # Import the entire data_manager module instead of just the function
            import data_manager as dm
            prn = self.current_user.get("PRN", "")
            alerts_df = dm.get_alerts_for_student(prn)
            if not alerts_df.empty:
                alerts_header = QLabel("Low Attendance Alerts")
                alerts_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #DC3545; margin-top: 10px;")
                events_layout.addWidget(alerts_header)
                for _, a in alerts_df.iterrows():
                    msg = a.get("Message", "Low attendance alert")
                    albl = QLabel("• " + msg)
                    albl.setStyleSheet("color: #DC3545; margin: 2px 0;")
                    events_layout.addWidget(albl)

            scroll_layout.addWidget(events_card)
            
            # Academic performance placeholder
            performance_card = QWidget()
            performance_card.setObjectName("card")
            performance_layout = QVBoxLayout(performance_card)
            
            performance_header = QLabel("Academic Performance")
            performance_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 15px;")
            
            performance_placeholder = QLabel("Your academic performance data will be displayed here.")
            performance_placeholder.setStyleSheet("color: #6C757D; font-style: italic;")
            
            performance_layout.addWidget(performance_header)
            performance_layout.addWidget(performance_placeholder)
            
            scroll_layout.addWidget(performance_card)
        
        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the main content layout
        self.content.addWidget(scroll_area)

    def show_train(self):
        self.clear_content()
        
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F8F9FA; }")
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # Header
        header = QLabel("Train Your Face Model")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        scroll_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Capture your face to create a recognition model for attendance")
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        scroll_layout.addWidget(subtitle)
        
        # Main card
        main_card = QWidget()
        main_card.setObjectName("card")
        main_layout = QVBoxLayout(main_card)
        
        # Instructions
        instructions = QLabel("Follow these steps to train your face model:")
        instructions.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-bottom: 15px;")
        main_layout.addWidget(instructions)
        
        # Steps
        steps_container = QWidget()
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(10)
        
        steps = [
            "1. Enter your IP Webcam URL below (e.g., http://ip:port/shot.jpg)",
            "2. Click 'Start Training' to begin the face capture process",
            "3. Look directly at the camera and move your head slightly to capture different angles",
            "4. The system will automatically capture multiple images of your face",
            "5. Wait for the training process to complete"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet("color: #495057; margin-left: 10px;")
            steps_layout.addWidget(step_label)
        
        main_layout.addWidget(steps_container)
        main_layout.addSpacing(15)
        
        # Form container
        form_container = QWidget()
        form_layout = QHBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # URL input with icon
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        url_icon = QLabel("🌐")
        url_icon.setStyleSheet(
            "font-size: 16px; padding: 10px; background-color: #E9ECEF; "
            "border: 1px solid #CED4DA; border-right: none; border-radius: 4px 0 0 4px;"
        )
        
        url_edit = QLineEdit()
        url_edit.setPlaceholderText("IP Webcam URL (e.g., http://ip:port/shot.jpg)")
        url_edit.setStyleSheet(
            "border-radius: 0 4px 4px 0; height: 38px;"
        )
        
        input_layout.addWidget(url_icon)
        input_layout.addWidget(url_edit)
        
        # Start training button
        train_btn = QPushButton("Start Training")
        train_btn.setObjectName("primary")
        train_btn.setFixedWidth(150)
        
        form_layout.addWidget(input_container, 1)
        form_layout.addWidget(train_btn)
        
        main_layout.addWidget(form_container)
        
        # Status container
        status_container = QWidget()
        status_container.setVisible(False)  # Initially hidden
        status_layout = QVBoxLayout(status_container)
        
        status_label = QLabel("Capturing face images...")
        status_label.setStyleSheet("font-size: 14px; color: #495057; margin-top: 15px;")
        
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setStyleSheet(
            "QProgressBar { border: 1px solid #CED4DA; border-radius: 4px; text-align: center; }"
            "QProgressBar::chunk { background-color: #4361EE; }"
        )
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(progress)
        
        main_layout.addWidget(status_container)
        
        # Add the main card to the scroll layout
        scroll_layout.addWidget(main_card)
        
        # Add a spacer to push content to the top
        scroll_layout.addStretch()
        
        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the main content layout
        self.content.addWidget(scroll_area)
        
        def run():
            # Show status container
            status_container.setVisible(True)
            status_label.setText("Capturing face images...")
            progress.setValue(25)
            QApplication.processEvents()  # Update UI
            
            ok, msg = capture_faces_from_ipcam(url_edit.text().strip(), self.current_user.get("FullName", ""))
            if ok:
                status_label.setText("Training model...")
                progress.setValue(75)
                QApplication.processEvents()  # Update UI
                
                ok2, msg2 = train_model()
                progress.setValue(100)
                status_container.setVisible(False)
                QMessageBox.information(self, "Training", msg2 if ok2 else msg2)
            else:
                status_container.setVisible(False)
                QMessageBox.warning(self, "Training", msg)
        
        train_btn.clicked.connect(run)

    def show_recognize(self):
        self.clear_content()
        
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F8F9FA; }")
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # Header
        header = QLabel("Recognize Faces & Mark Attendance")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        scroll_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Use your IP webcam to recognize faces and automatically mark attendance")
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        scroll_layout.addWidget(subtitle)
        
        # Main card
        main_card = QWidget()
        main_card.setObjectName("card")
        main_layout = QVBoxLayout(main_card)
        
        # Instructions
        instructions = QLabel("Follow these steps to recognize faces:")
        instructions.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-bottom: 15px;")
        main_layout.addWidget(instructions)
        
        # Steps
        steps_container = QWidget()
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(10)
        
        steps = [
            "1. Enter your IP Webcam URL below (e.g., http://ip:port/shot.jpg)",
            "2. Click 'Start Recognition' to begin the face recognition process",
            "3. The system will automatically identify faces and mark attendance",
            "4. Results will be saved to the attendance database"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet("color: #495057; margin-left: 10px;")
            steps_layout.addWidget(step_label)
        
        main_layout.addWidget(steps_container)
        main_layout.addSpacing(15)
        
        # Form container
        form_container = QWidget()
        form_layout = QHBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # URL input with icon
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)
        
        url_icon = QLabel("🌐")
        url_icon.setStyleSheet(
            "font-size: 16px; padding: 10px; background-color: #E9ECEF; "
            "border: 1px solid #CED4DA; border-right: none; border-radius: 4px 0 0 4px;"
        )
        
        url_edit = QLineEdit()
        url_edit.setPlaceholderText("IP Webcam URL (e.g., http://ip:port/shot.jpg)")
        url_edit.setStyleSheet(
            "border-radius: 0 4px 4px 0; height: 38px;"
        )
        
        input_layout.addWidget(url_icon)
        input_layout.addWidget(url_edit)
        
        # Start recognition button
        recognize_btn = QPushButton("Start Recognition")
        recognize_btn.setObjectName("primary")
        recognize_btn.setFixedWidth(180)
        
        form_layout.addWidget(input_container, 1)
        form_layout.addWidget(recognize_btn)
        
        main_layout.addWidget(form_container)
        
        # Status container
        status_container = QWidget()
        status_container.setVisible(False)  # Initially hidden
        status_layout = QVBoxLayout(status_container)
        
        status_label = QLabel("Recognition in progress...")
        status_label.setStyleSheet("font-size: 14px; color: #495057; margin-top: 15px;")
        
        # Recent recognitions container
        recent_container = QWidget()
        recent_container.setVisible(False)  # Initially hidden
        recent_layout = QVBoxLayout(recent_container)
        
        recent_header = QLabel("Recent Recognitions:")
        recent_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-top: 20px; margin-bottom: 10px;")
        
        recent_list = QLabel("No recognitions yet")
        recent_list.setStyleSheet("color: #6C757D; font-style: italic;")
        
        recent_layout.addWidget(recent_header)
        recent_layout.addWidget(recent_list)
        
        status_layout.addWidget(status_label)
        main_layout.addLayout(status_layout)
        main_layout.addWidget(recent_container)
        
        # Add the main card to the scroll layout
        scroll_layout.addWidget(main_card)
        
        # Add a spacer to push content to the top
        scroll_layout.addStretch()
        
        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the main content layout
        self.content.addWidget(scroll_area)
        
        def run():
            # Show status container
            status_container.setVisible(True)
            status_label.setText("Recognition in progress... Please wait.")
            QApplication.processEvents()  # Update UI
            
            # Start recognition
            ok, msg = recognize_from_ipcam_and_mark(url_edit.text().strip())
            
            if ok:
                status_label.setText("Recognition completed successfully!")
                
                # Show recent recognitions
                recent_container.setVisible(True)
                
                # Update recent list with recognized names (placeholder)
                if "recognized" in msg.lower():
                    names = msg.split(":")[1].strip() if ":" in msg else "Unknown"
                    recent_list.setText(names)
                else:
                    recent_list.setText(msg)
                QMessageBox.information(self, "Recognition", msg)
            else:
                status_label.setText("Recognition failed!")
                QMessageBox.warning(self, "Recognition", msg)
        
        recognize_btn.clicked.connect(run)

    def show_attendance(self):
        self.clear_content()
        
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F8F9FA; }")
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)
        
        # Header
        header = QLabel("Attendance Records")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        scroll_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("View and analyze attendance data")
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        scroll_layout.addWidget(subtitle)
        
        # Today's summary card
        today_card = QWidget()
        today_card.setObjectName("card")
        today_layout = QVBoxLayout(today_card)
        
        today_header = QLabel("Today's Summary")
        today_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-bottom: 15px;")
        today_layout.addWidget(today_header)
        
        # Today's stats
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Get attendance summary based on user role
        if not self.is_admin and self.current_user:
            # Student view - show only their attendance
            from data_manager import student_attendance_summary_for_date
            student_prn = self.current_user.get("PRN", "")
            summary = student_attendance_summary_for_date(today, student_prn)
            
            # Update header and subtitle for student view
            header.setText("My Attendance Records")
            subtitle.setText("View your personal attendance data")
        else:
            # Admin view - show all students
            summary = attendance_summary_for_date(today)
        
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        
        # Present count
        present_container = QWidget()
        present_layout = QVBoxLayout(present_container)
        
        present_count = QLabel(str(summary['present']))
        present_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #20C997; text-align: center;")
        present_count.setAlignment(Qt.AlignCenter)
        
        present_label = QLabel("Present")
        present_label.setStyleSheet("font-size: 14px; color: #6C757D; text-align: center;")
        present_label.setAlignment(Qt.AlignCenter)
        
        present_layout.addWidget(present_count)
        present_layout.addWidget(present_label)
        
        # Absent count
        absent_container = QWidget()
        absent_layout = QVBoxLayout(absent_container)
        
        absent_count = QLabel(str(summary['absent']))
        absent_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #DC3545; text-align: center;")
        absent_count.setAlignment(Qt.AlignCenter)
        
        absent_label = QLabel("Absent")
        absent_label.setStyleSheet("font-size: 14px; color: #6C757D; text-align: center;")
        absent_label.setAlignment(Qt.AlignCenter)
        
        absent_layout.addWidget(absent_count)
        absent_layout.addWidget(absent_label)
        
        # Total count
        total_container = QWidget()
        total_layout = QVBoxLayout(total_container)
        
        total_count = QLabel(str(summary['total']))
        total_count.setStyleSheet("font-size: 32px; font-weight: bold; color: #4361EE; text-align: center;")
        total_count.setAlignment(Qt.AlignCenter)
        
        total_label = QLabel("Total")
        total_label.setStyleSheet("font-size: 14px; color: #6C757D; text-align: center;")
        total_label.setAlignment(Qt.AlignCenter)
        
        total_layout.addWidget(total_count)
        total_layout.addWidget(total_label)
        
        # Add all containers to stats layout
        stats_layout.addWidget(present_container)
        stats_layout.addWidget(absent_container)
        stats_layout.addWidget(total_container)
        
        today_layout.addWidget(stats_container)
        
        # Add today's card to main layout
        scroll_layout.addWidget(today_card)
        
        # Filter card
        filter_card = QWidget()
        filter_card.setObjectName("card")
        filter_layout = QVBoxLayout(filter_card)
        
        filter_header = QLabel("Attendance History")
        filter_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-bottom: 15px;")
        filter_layout.addWidget(filter_header)
        
        # Filter dropdown
        filter_container = QWidget()
        filter_container_layout = QHBoxLayout(filter_container)
        filter_container_layout.setContentsMargins(0, 0, 0, 0)
        
        filter_label = QLabel("Time Period:")
        filter_label.setStyleSheet("color: #495057;")
        
        filter_box = QComboBox()
        filter_box.addItems(["Today's Attendance", "Last 7 Days", "Last 30 Days", "Last 90 Days"])
        filter_box.setStyleSheet(
            "QComboBox { border: 1px solid #CED4DA; border-radius: 4px; padding: 8px; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
        )
        
        filter_container_layout.addWidget(filter_label)
        filter_container_layout.addWidget(filter_box, 1)
        
        filter_layout.addWidget(filter_container)
        
        # Table container
        table_holder = QWidget()
        table_layout = QVBoxLayout(table_holder)
        table_layout.setContentsMargins(0, 15, 0, 0)
        
        filter_layout.addWidget(table_holder)
        
        # Add filter card to main layout
        scroll_layout.addWidget(filter_card)
        
        # Set the scroll content as the widget for the scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the main content layout
        self.content.addWidget(scroll_area)
        
        def refresh_table():
            choice = filter_box.currentText()
            
            # Get student PRN for filtering if logged in as student
            student_prn = None
            if not self.is_admin and self.current_user:
                student_prn = self.current_user.get("PRN", "")
            
            # Get attendance data with optional student filtering
            if choice.startswith("Today"):
                df = attendance_in_range(1, student_prn)
            elif "7" in choice:
                df = attendance_in_range(7, student_prn)
            elif "30" in choice:
                df = attendance_in_range(30, student_prn)
            else:
                df = attendance_in_range(90, student_prn)
            
            # Create table (editable only for admin)
            is_editable = self.is_admin
            tbl = self._df_to_table(df, editable=is_editable)
            tbl.setStyleSheet(
                "QTableView { border: none; alternate-background-color: #F1F3F5; }"
                "QHeaderView::section { background-color: #4361EE; color: white; padding: 6px; }"
            )
            
            # Clear previous table
            while table_layout.count():
                item = table_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            table_layout.addWidget(tbl)
        
        filter_box.currentIndexChanged.connect(refresh_table)
        refresh_table()

    def show_low_attendance(self):
        # Admin-only
        if not self.is_admin:
            QMessageBox.warning(self, "Access Denied", "Only admins can view low attendance.")
            return
        self.clear_content()

        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(); layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(20)

        header = QLabel("Low Attendance")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        layout.addWidget(header)

        filter_row = QWidget(); fr = QHBoxLayout(filter_row)
        fr.setContentsMargins(0,0,0,0)
        fr.addWidget(QLabel("Range:"))
        range_box = QComboBox(); range_box.addItems(["Last 7 Days", "Last 15 Days"]) ; fr.addWidget(range_box)
        fr.addStretch()
        layout.addWidget(filter_row)

        table_holder = QWidget(); tl = QVBoxLayout(table_holder); tl.setContentsMargins(0,0,0,0)
        layout.addWidget(table_holder)

        def refresh():
            days = 7 if "7" in range_box.currentText() else 15
            df = low_attendance_report(days)
            tbl = self._df_to_table(df, editable=False)
            # Add Send Alert column with buttons
            if not df.empty:
                # extend table by 1 column
                current_cols = tbl.columnCount()
                tbl.setColumnCount(current_cols + 1)
                tbl.setHorizontalHeaderItem(current_cols, QTableWidgetItem("Send Alert"))
                for r in range(tbl.rowCount()):
                    prn_item = tbl.item(r, 0)
                    prn_val = prn_item.text() if prn_item else ""
                    btn = QPushButton("Send Alert")
                    def make_handler(p=prn_val):
                        def handler():
                            self._open_alert_dialog(p)
                        return handler
                    btn.clicked.connect(make_handler())
                    tbl.setCellWidget(r, current_cols, btn)

            while tl.count():
                it = tl.takeAt(0)
                w = it.widget()
                if w: w.deleteLater()
            tl.addWidget(tbl)

        range_box.currentIndexChanged.connect(refresh)
        refresh()

        scroll_area.setWidget(scroll_content)
        self.content.addWidget(scroll_area)

    def _open_alert_dialog(self, prn: str):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        import data_manager as dm
        students = dm._load_students_df()
        row = students[students["PRN"] == str(prn)]
        if row.empty:
            QMessageBox.information(self, "Not Found", "Student not found")
            return
        s = row.iloc[0]
        dlg = QDialog(self); dlg.setWindowTitle("Send Low Attendance Alert")
        form = QFormLayout(dlg)
        student_phone = QLineEdit(str(s.get("StudentPhone", "")))
        parent_phone = QLineEdit(str(s.get("ParentPhone", "")))
        message = QLineEdit("Your attendance is low. Please attend classes regularly.")
        form.addRow("Student Phone", student_phone)
        form.addRow("Parent Phone", parent_phone)
        form.addRow("Message", message)

        btns = QWidget(); hb = QHBoxLayout(btns); hb.setContentsMargins(0,0,0,0)
        send_student = QPushButton("Send to Student")
        send_parent = QPushButton("Send to Parent")
        hb.addWidget(send_student); hb.addWidget(send_parent)
        form.addRow(btns)

        def send_to(target: str):
            result = dm.send_alert(prn, target, message.text().strip())
            # Handle both old and new return types for backward compatibility
            if isinstance(result, tuple):
                ok, msg = result
            else:
                ok, msg = result, "Alert sent successfully"
            QMessageBox.information(self, "Alert", msg)

        send_student.clicked.connect(lambda: send_to("student"))
        send_parent.clicked.connect(lambda: send_to("parent"))

        close_box = QDialogButtonBox(QDialogButtonBox.Close)
        close_box.rejected.connect(dlg.reject)
        form.addRow(close_box)
        dlg.exec_()

    def show_internal_marks(self):
        self.clear_content()
        import data_manager as dm
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F8F9FA; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        header = QLabel("Academic Records")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        scroll_layout.addWidget(header)

        # If student, show read-only table of their marks grouped by semester
        if not self.is_admin and self.current_user:
            viewer_card = QWidget()
            viewer_card.setObjectName("card")
            vlayout = QVBoxLayout(viewer_card)
            vheader = QLabel("My Academic Records (Semester-wise)")
            vheader.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 15px;")
            vlayout.addWidget(vheader)

            prn = self.current_user.get("PRN", "")
            df = get_student_internal_marks(prn)
            if df.empty:
                lbl = QLabel("No internal marks available yet.")
                lbl.setStyleSheet("color: #6C757D;")
                vlayout.addWidget(lbl)
            else:
                # Ensure column order
                cols = ["Semester", "Year", "Branch", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total", "UpdatedAt"]
                for c in cols:
                    if c not in df.columns:
                        df[c] = ""
                df = df[["Semester", "Year", "Branch", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total", "UpdatedAt"]]
                tbl = self._df_to_table(df, editable=False)
                vlayout.addWidget(tbl)

            scroll_layout.addWidget(viewer_card)
            scroll_area.setWidget(scroll_content)
            self.content.addWidget(scroll_area)
            return

        # Admin editor UI
        filter_card = QWidget()
        filter_card.setObjectName("card")
        filter_layout = QVBoxLayout(filter_card)
        filter_header = QLabel("Select Branch and Semester")
        filter_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529; margin-bottom: 15px;")
        filter_layout.addWidget(filter_header)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        # Removed year dropdown as requested
        branch_box = QComboBox(); branch_box.addItems(["Computer", "IT", "AI/ML", "Mechanical", "Civil", "ENTC"])
        sem_box = QComboBox(); sem_box.addItems([f"Sem {i}" for i in range(1, 9)])

        row_layout.addWidget(QLabel("Branch:")); row_layout.addWidget(branch_box)
        row_layout.addWidget(QLabel("Semester:")); row_layout.addWidget(sem_box)

        filter_layout.addWidget(row)

        table_holder = QWidget(); table_layout = QVBoxLayout(table_holder); table_layout.setContentsMargins(0, 10, 0, 0)
        filter_layout.addWidget(table_holder)

        # Buttons
        btn_row = QWidget(); btn_layout = QHBoxLayout(btn_row); btn_layout.addStretch()
        save_btn = QPushButton("Save Marks"); save_btn.setObjectName("primary"); save_btn.setFixedWidth(140)
        btn_layout.addWidget(save_btn)
        filter_layout.addWidget(btn_row)

        scroll_layout.addWidget(filter_card)
        scroll_area.setWidget(scroll_content)
        self.content.addWidget(scroll_area)

        def load_students_and_marks():
            branch = branch_box.currentText(); sem = sem_box.currentText()
            students_df = list_all_students()
            if students_df.empty:
                df = pd.DataFrame(columns=["PRN", "Name", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total"])
            else:
                # Filter only by branch since year dropdown was removed
                filtered = students_df[students_df["Branch"] == branch].copy()
                filtered = filtered[["PRN", "FullName", "Year"]].rename(columns={"FullName": "Name"})
                # Get all years for this branch and semester
                existing = get_internal_marks("", branch, sem)  # Empty string for year to get all years
                df = filtered
                if not existing.empty:
                    df = df.merge(existing[["PRN", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total"]], on="PRN", how="left")
                # Ensure numeric columns present
                for c in ["CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total"]:
                    if c not in df.columns:
                        df[c] = ""

            # Reorder columns
            df = df[["PRN", "Name", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total"]]
            table = self._df_to_table(df, editable=True)
            # Lock PRN and Name columns from editing
            for r in range(table.rowCount()):
                for c in [0, 1]:
                    itm = table.item(r, c)
                    if itm:
                        itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)

            # Replace holder
            while table_layout.count():
                item = table_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            table_layout.addWidget(table)
            return table

        marks_table = load_students_and_marks()
        # Removed year_box reference as requested
        branch_box.currentIndexChanged.connect(lambda: load_students_and_marks())
        sem_box.currentIndexChanged.connect(lambda: load_students_and_marks())

        def on_save():
            tbl = marks_table
            # If table was reloaded, get latest widget
            if table_layout.count():
                w = table_layout.itemAt(0).widget()
                if w:
                    tbl = w
            df = self._table_to_df(tbl)
            # Validate and compute totals
            def to_int(x):
                try:
                    return max(0, int(float(str(x).strip() or "0")))
                except Exception:
                    return 0
            df["CA1"] = df["CA1"].map(to_int).clip(upper=10)
            df["CA2"] = df["CA2"].map(to_int).clip(upper=10)
            df["MidSem"] = df["MidSem"].map(to_int).clip(upper=20)
            df["SemesterExam"] = df["SemesterExam"].map(to_int)
            df["MaxTotal"] = df["MaxTotal"].map(to_int)
            df.loc[df["MaxTotal"] <= 0, "MaxTotal"] = 100
            df["Obtained"] = (df["CA1"].astype(int) + df["CA2"].astype(int) + df["MidSem"].astype(int) + df["SemesterExam"].astype(int))
            df.loc[df["Obtained"] > df["MaxTotal"], "Obtained"] = df["MaxTotal"]
            df["Total"] = df["Obtained"].astype(int)

            # Attach meta columns - use existing Year from student record
            # Year column is already included from the filtered dataframe
            df["Branch"] = branch_box.currentText()
            df["Semester"] = sem_box.currentText()

            # Reorder for API
            cols = ["PRN", "Name", "Branch", "Semester", "CA1", "CA2", "MidSem", "SemesterExam", "Obtained", "MaxTotal", "Total"]
            df = df[cols]
            try:
                upsert_internal_marks(df)
                QMessageBox.information(self, "Saved", "Academic records saved successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save marks: {e}")

        save_btn.clicked.connect(on_save)

    def show_add_student(self):
        # Admin-only: show signup form prefilled for admin to add student
        if not self.is_admin:
            QMessageBox.warning(self, "Access Denied", "Only admins can add students.")
            return

        self.clear_content()
        from ui_components import StudentSignup

        def on_submit(data: dict):
            ok, msg = register_student(data)
            if ok:
                QMessageBox.information(self, "Success", msg)
                self.show_dashboard()
            else:
                QMessageBox.warning(self, "Error", msg)

        def on_back():
            self.show_dashboard()

        # Make sure all fields are editable for admin
        signup = StudentSignup(on_submit=on_submit, on_back=on_back)
        # Enable all input fields to be editable
        for field in [signup.student_id, signup.full_name, signup.email, signup.roll_no, 
                     signup.prn, signup.student_phone, signup.parent_phone, signup.address, 
                     signup.security_answer, signup.password, signup.confirm]:
            field.setReadOnly(False)
            field.setEnabled(True)
        
        # Wrap signup with a small top bar for admin actions
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        # Align manage student actions: Add form on left, Remove button on right
        left_spacer = QWidget(); left_spacer.setSizePolicy(left_spacer.sizePolicy().Expanding, left_spacer.sizePolicy().Preferred)
        top_layout.addWidget(left_spacer)
        remove_btn = QPushButton('Remove Student')
        remove_btn.setFixedWidth(150)
        remove_btn.clicked.connect(self.show_remove_student)
        top_layout.addWidget(remove_btn)

        container_layout.addWidget(top_row)
        container_layout.addWidget(signup)
        self.content.addWidget(container)

    def show_remove_student(self):
        # Admin-only: prompt for PRN and remove student after confirmation
        if not self.is_admin:
            QMessageBox.warning(self, "Access Denied", "Only admins can remove students.")
            return

        # Ask for PRN
        from PyQt5.QtWidgets import QInputDialog
        prn, ok = QInputDialog.getText(self, "Remove Student", "Enter PRN of student to remove:")
        if not ok or not prn.strip():
            return
        prn = prn.strip()

        # Load students and find by PRN
        import data_manager as dm
        df = dm._load_students_df()
        matches = df[df['PRN'] == prn]
        if matches.empty:
            QMessageBox.information(self, "Not Found", f"No student found with PRN {prn}")
            return

        # If multiple matches (shouldn't happen), show first
        student_row = matches.iloc[0].to_dict()
        name = student_row.get('FullName', '')

        # Confirm
        resp = QMessageBox.question(self, "Confirm Removal", f"Remove student {name} (PRN: {prn})?", QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        # Remove and save
        df2 = df[df['PRN'] != prn].copy()
        dm._save_students_df(df2)
        QMessageBox.information(self, "Removed", f"Student {name} (PRN: {prn}) removed.")
        self.show_dashboard()

    def show_settings(self):
        self.clear_content()
        
        # Create a scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container widget
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # Profile section (student only)
        if not self.is_admin and self.current_user:
            # Profile card
            profile_card = QWidget()
            profile_card.setObjectName("card")
            profile_layout = QVBoxLayout(profile_card)
            
            # Card header
            profile_header = QLabel("Profile Information")
            profile_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
            profile_layout.addWidget(profile_header)
            
            # Form fields
            form_widget = QWidget()
            form_layout = QGridLayout(form_widget)
            form_layout.setContentsMargins(0, 10, 0, 10)
            form_layout.setSpacing(10)
            
            # Row 0: StudentID (read-only), Full Name
            sid_label = QLabel("Student ID:")
            sid_label.setStyleSheet("font-weight: 500;")
            sid = QLineEdit(self.current_user.get("StudentID", ""))
            sid.setReadOnly(True)
            name_label = QLabel("Full Name:")
            name_label.setStyleSheet("font-weight: 500;")
            name = QLineEdit(self.current_user.get("FullName", ""))
            
            # Row 1: Email, Roll No
            email_label = QLabel("Email:")
            email_label.setStyleSheet("font-weight: 500;")
            email = QLineEdit(self.current_user.get("Email", ""))
            roll_label = QLabel("Roll No:")
            roll_label.setStyleSheet("font-weight: 500;")
            roll = QLineEdit(self.current_user.get("RollNo", ""))
            
            # Row 2: PRN, Year (combo)
            prn_label = QLabel("PRN:")
            prn_label.setStyleSheet("font-weight: 500;")
            prn = QLineEdit(self.current_user.get("PRN", ""))
            year_label = QLabel("Year:")
            year_label.setStyleSheet("font-weight: 500;")
            year = QComboBox()
            year.addItems(["First Year", "Second Year", "Third Year", "Final Year"])
            y_cur = self.current_user.get("Year", "")
            if y_cur:
                idx = year.findText(y_cur)
                if idx >= 0:
                    year.setCurrentIndex(idx)
            
            # Row 3: Branch (combo), Student Phone
            branch_label = QLabel("Branch:")
            branch_label.setStyleSheet("font-weight: 500;")
            branch = QComboBox()
            branch.addItems(["Computer", "IT", "AI/ML", "Mechanical", "Civil", "ENTC"])
            b_cur = self.current_user.get("Branch", "")
            if b_cur:
                bidx = branch.findText(b_cur)
                if bidx >= 0:
                    branch.setCurrentIndex(bidx)
            phone_label = QLabel("Phone:")
            phone_label.setStyleSheet("font-weight: 500;")
            phone = QLineEdit(self.current_user.get("StudentPhone", ""))
            phone.setPlaceholderText("Enter your phone number")
            
            # Row 4: Parent Phone, Address
            parent_label = QLabel("Parent's Phone:")
            parent_label.setStyleSheet("font-weight: 500;")
            parent = QLineEdit(self.current_user.get("ParentPhone", ""))
            addr_label = QLabel("Address:")
            addr_label.setStyleSheet("font-weight: 500;")
            addr = QLineEdit(self.current_user.get("Address", ""))
            addr.setPlaceholderText("Enter your address")
            
            # Row 5: Security Answer, New Password
            sec_label = QLabel("Security Answer:")
            sec_label.setStyleSheet("font-weight: 500;")
            sec = QLineEdit(self.current_user.get("SecurityAnswer", ""))
            pwd_label = QLabel("New Password:")
            pwd_label.setStyleSheet("font-weight: 500;")
            pwd = QLineEdit()
            pwd.setPlaceholderText("Enter new password (leave blank to keep current)")
            pwd.setEchoMode(QLineEdit.Password)
            
            # Add to grid (two columns label-value pairs)
            form_layout.addWidget(sid_label, 0, 0)
            form_layout.addWidget(sid, 0, 1)
            form_layout.addWidget(name_label, 0, 2)
            form_layout.addWidget(name, 0, 3)
            form_layout.addWidget(email_label, 1, 0)
            form_layout.addWidget(email, 1, 1)
            form_layout.addWidget(roll_label, 1, 2)
            form_layout.addWidget(roll, 1, 3)
            form_layout.addWidget(prn_label, 2, 0)
            form_layout.addWidget(prn, 2, 1)
            form_layout.addWidget(year_label, 2, 2)
            form_layout.addWidget(year, 2, 3)
            form_layout.addWidget(branch_label, 3, 0)
            form_layout.addWidget(branch, 3, 1)
            form_layout.addWidget(phone_label, 3, 2)
            form_layout.addWidget(phone, 3, 3)
            form_layout.addWidget(parent_label, 4, 0)
            form_layout.addWidget(parent, 4, 1)
            form_layout.addWidget(addr_label, 4, 2)
            form_layout.addWidget(addr, 4, 3)
            form_layout.addWidget(sec_label, 5, 0)
            form_layout.addWidget(sec, 5, 1)
            form_layout.addWidget(pwd_label, 5, 2)
            form_layout.addWidget(pwd, 5, 3)
            
            profile_layout.addWidget(form_widget)
            
            # Save button
            save = QPushButton("Save Profile")
            save.setFixedWidth(200)
            
            def do_save():
                updates = {
                    "FullName": name.text().strip(),
                    "Email": email.text().strip(),
                    "RollNo": roll.text().strip(),
                    "PRN": prn.text().strip(),
                    "Year": year.currentText().strip(),
                    "Branch": branch.currentText().strip(),
                    "StudentPhone": phone.text().strip(),
                    "ParentPhone": parent.text().strip(),
                    "Address": addr.text().strip(),
                    "SecurityAnswer": sec.text().strip(),
                }
                if pwd.text().strip():
                    updates["Password"] = pwd.text().strip()
                ok, msg = update_student_profile(self.current_user.get("StudentID", ""), updates)
                QMessageBox.information(self, "Profile", msg)
                if ok:
                    # Refresh in-memory user data to reflect changes
                    self.current_user.update(updates)
            
            save.clicked.connect(do_save)
            profile_layout.addWidget(save, alignment=Qt.AlignRight)
            
            main_layout.addWidget(profile_card)
        
        # Appearance card
        appearance_card = QWidget()
        appearance_card.setObjectName("card")
        appearance_layout = QVBoxLayout(appearance_card)
        
        # Card header
        appearance_header = QLabel("Appearance")
        appearance_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        appearance_layout.addWidget(appearance_header)
        
        # Theme options
        theme_widget = QWidget()
        theme_layout = QVBoxLayout(theme_widget)
        theme_layout.setContentsMargins(0, 10, 0, 10)
        
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet("font-weight: 500;")
        theme_layout.addWidget(theme_label)
        
        # Theme buttons container
        theme_buttons = QWidget()
        theme_buttons_layout = QHBoxLayout(theme_buttons)
        theme_buttons_layout.setContentsMargins(0, 0, 0, 0)
        theme_buttons_layout.setSpacing(10)
        
        light = QPushButton("Light Mode")
        light.setFixedWidth(150)
        light.setCheckable(True)
        light.setChecked(True)  # Default
        
        dark = QPushButton("Dark Mode")
        dark.setFixedWidth(150)
        dark.setCheckable(True)
        
        # Connect theme buttons
        light.clicked.connect(lambda: (self.apply_theme("light"), dark.setChecked(False)))
        dark.clicked.connect(lambda: (self.apply_theme("dark"), light.setChecked(False)))
        
        theme_buttons_layout.addWidget(light)
        theme_buttons_layout.addWidget(dark)
        theme_buttons_layout.addStretch()
        
        theme_layout.addWidget(theme_buttons)
        appearance_layout.addWidget(theme_widget)
        
        # Language selection
        lang_widget = QWidget()
        lang_layout = QVBoxLayout(lang_widget)
        lang_layout.setContentsMargins(0, 10, 0, 0)
        
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("font-weight: 500;")
        lang_layout.addWidget(lang_label)
        
        lang = QComboBox()
        lang.addItems(["English", "Hindi", "Marathi"])
        lang.setFixedWidth(200)
        lang_layout.addWidget(lang)
        
        appearance_layout.addWidget(lang_widget)
        main_layout.addWidget(appearance_card)
        
        # About card
        about_card = QWidget()
        about_card.setObjectName("card")
        about_layout = QVBoxLayout(about_card)
        
        # Card header
        about_header = QLabel("About")
        about_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        about_layout.addWidget(about_header)
        
        # About content
        about_content = QLabel("Acadix Scan - Face Recognition Attendance System\nVersion 1.0\nDeveloped by O.H.G.M.P")
        about_content.setStyleSheet("line-height: 1.5; margin: 10px 0;")
        about_layout.addWidget(about_content)
        
        # Update button
        update_btn = QPushButton("Check for Updates")
        update_btn.setFixedWidth(200)
        about_layout.addWidget(update_btn, alignment=Qt.AlignLeft)
        
        main_layout.addWidget(about_card)
        main_layout.addStretch()
        
        # Set the container as the scroll area widget
        scroll.setWidget(container)
        self.content.addWidget(scroll)

    def apply_theme(self, mode: str):
        # Load stylesheet safely
        stylesheet = ""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(base_dir, "styles.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    stylesheet = f.read()
            except Exception:
                stylesheet = ""
        else:
            print("Warning: styles.qss not found, using default styling")

        if mode == "dark":
            self.setProperty("theme", "dark")
            if hasattr(self, 'assistant'):
                self.assistant.setProperty("theme", "dark")
        else:
            self.setProperty("theme", "")
            if hasattr(self, 'assistant'):
                self.assistant.setProperty("theme", "")

        # Apply stylesheet if available
        if stylesheet:
            # Apply to whole app
            app = QApplication.instance()
            if app:
                app.setStyleSheet("")
                app.setStyleSheet(stylesheet)
        else:
            # Minimal fallback styling to keep UI usable
            fallback = "QWidget { font-family: Segoe UI, Arial; font-size: 12px; } QPushButton#primary { background-color: #4361EE; color: white; padding: 8px; border-radius: 6px; }"
            app = QApplication.instance()
            if app:
                app.setStyleSheet(fallback)

        # Refresh UI
        try:
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
        except Exception:
            pass

    def logout(self):
        self.current_user = None
        self.is_admin = False
        # Hide assistant
        if hasattr(self, 'assistant') and self.assistant:
            self.assistant.hide()
        self.stack.setCurrentWidget(self.role)

    # Helpers
    def _df_to_table(self, df: pd.DataFrame, editable: bool = False) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(df.columns))
        table.setRowCount(len(df.index))
        table.setHorizontalHeaderLabels(list(df.columns))
        for r in range(len(df.index)):
            for c, col in enumerate(df.columns):
                item = QTableWidgetItem(str(df.iloc[r][col]))
                if not editable:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(r, c, item)
        table.setSortingEnabled(True)
        return table

    def _table_to_df(self, table: QTableWidget) -> pd.DataFrame:
        rows = table.rowCount()
        cols = table.columnCount()
        headers = [table.horizontalHeaderItem(i).text() for i in range(cols)]
        data = []
        for r in range(rows):
            row = {}
            for c in range(cols):
                itm = table.item(r, c)
                row[headers[c]] = itm.text() if itm else ""
            data.append(row)
        return pd.DataFrame(data)


def load_stylesheet():
    """Load and return the application stylesheet"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(base_dir, "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            print("Warning: styles.qss not found, using default styling")
            return ""
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""

def main():
    app = QApplication(sys.argv)
    
    # Try to load and apply modern fonts
    try:
        # Set default font
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        # Add custom fonts if available
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(base_dir, "assets", "fonts")
        if os.path.exists(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, font_file))
    except Exception as e:
        print(f"Error loading fonts: {e}")
    
    # Apply global stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Set application metadata
    app.setApplicationName("Acadix Scan")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Acadix")
    app.setOrganizationDomain("acadix.scan")
    
    # Create and show main window
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


