from typing import Callable, Optional

from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QTextEdit,
)
from PyQt5.QtGui import QIcon, QTextCursor, QPixmap, QMovie, QPainter, QBrush, QColor, QPen, QRadialGradient
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtSvg import QSvgWidget
import os


class LogoWidget(QLabel):
    def __init__(self, size: int = 120, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # image sources (prefer the provided om1.png asset)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.png_path = os.path.join(base_dir, "assets", "om1.png")
        self.jpg_fallback = os.path.join(base_dir, "assets", "om.jpg")

        self._pix = None
        if os.path.exists(self.png_path):
            self._pix = QPixmap(self.png_path)
        elif os.path.exists(self.jpg_fallback):
            self._pix = QPixmap(self.jpg_fallback)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self._size
        center = w // 2

        # Draw Instagram-like radial gradient ring with no black border
        gradient = QRadialGradient(self.rect().center(), w / 2)
        gradient.setColorAt(0.0, QColor("#feda75"))
        gradient.setColorAt(0.25, QColor("#fa7e1e"))
        gradient.setColorAt(0.5, QColor("#d62976"))
        gradient.setColorAt(0.75, QColor("#962fbf"))
        gradient.setColorAt(1.0, QColor("#4f5bd5"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))

        # outer colored disk
        outer_rect = self.rect()
        painter.drawEllipse(outer_rect)

        # inner white circle to create ring effect
        inner_margin = int(w * 0.10)
        inner_rect = outer_rect.adjusted(inner_margin, inner_margin, -inner_margin, -inner_margin)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(inner_rect)

        # draw pixmap masked as circle
        if self._pix and not self._pix.isNull():
            img_size = inner_rect.size()
            scaled = self._pix.scaled(img_size.width(), img_size.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # create circular mask
            mask = QPixmap(img_size)
            mask.fill(Qt.transparent)
            m_p = QPainter(mask)
            m_p.setRenderHint(QPainter.Antialiasing)
            m_p.setBrush(QBrush(QColor("white")))
            m_p.drawEllipse(0, 0, img_size.width(), img_size.height())
            m_p.end()

            cropped = scaled.copy((scaled.width() - img_size.width()) // 2, (scaled.height() - img_size.height()) // 2, img_size.width(), img_size.height())
            cropped.setMask(mask.createMaskFromColor(QColor("transparent"), Qt.MaskInColor))

            painter.drawPixmap(inner_rect.topLeft(), cropped)

        painter.end()


class SplashScreen(QWidget):
    def __init__(self, on_done: Callable[[], None]):
        super().__init__()
        self.on_done = on_done
        
        # Make window frameless and fully transparent
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("QWidget { background: transparent; }")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Backdrop to ensure visibility on any desktop background
        content_card = QWidget()
        content_card.setObjectName("splash-content")
        content_card.setStyleSheet(
            "#splash-content { background-color: rgba(0,0,0,0.35); border-radius: 18px; }"
        )
        content_layout = QVBoxLayout(content_card)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        
        # App logo widget (circular with gradient ring)
        logo_container = QWidget()
        logo_container.setFixedSize(180, 180)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo = LogoWidget(size=160)
        
        if logo is None:
            # Fallback logo
            logo = QLabel()
            logo.setFixedSize(160, 160)
            logo.setStyleSheet(
                "background-color: white; border-radius: 11px; "
                "color: #1f3a93; font-size: 48px; font-weight: bold; "
                "border: 0px solid rgba(255, 255, 255, 0.9);"
            )
            logo.setAlignment(Qt.AlignCenter)
            logo.setText("📚\nAI")
        
        logo_layout.addWidget(logo, 0, Qt.AlignCenter)
        
        # App title with enhanced styling
        title = QLabel("ACADIX SCAN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 42px; font-weight: bold; color: #FFFFFF; "
            "letter-spacing: 3px;"
        )
        # Add drop shadow effect since QSS does not support text-shadow
        title_shadow = QGraphicsDropShadowEffect()
        title_shadow.setBlurRadius(14)
        title_shadow.setOffset(2, 3)
        title_shadow.setColor(QColor(0, 0, 0, 200))
        title.setGraphicsEffect(title_shadow)
        
        # App subtitle
        subtitle_line1 = QLabel("SCAN")
        subtitle_line1.setAlignment(Qt.AlignCenter)
        subtitle_line1.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #FFFFFF; "
            "letter-spacing: 2px; margin-bottom: 10px;"
        )
        
        # Description
        description = QLabel("AI-Powered Facial Recognition\nAttendance Management System")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet(
            "font-size: 16px; color: #F8F9FA; "
            "line-height: 1.4;"
        )
        desc_shadow = QGraphicsDropShadowEffect()
        desc_shadow.setBlurRadius(10)
        desc_shadow.setOffset(2, 2)
        desc_shadow.setColor(QColor(0, 0, 0, 180))
        description.setGraphicsEffect(desc_shadow)
        
        # Loading section with animated dots
        loading_container = QWidget()
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 20, 0, 0)
        loading_layout.setSpacing(10)
        
        loading_text = QLabel("Initializing System")
        loading_text.setAlignment(Qt.AlignCenter)
        loading_text.setStyleSheet(
            "font-size: 14px; color: #FFFFFF; "
            "font-weight: 600;"
        )
        
        # Animated loading dots
        self.loading_dots = QLabel("●○○")
        self.loading_dots.setAlignment(Qt.AlignCenter)
        self.loading_dots.setStyleSheet(
            "font-size: 16px; color: rgba(255, 255, 255, 0.6); "
            "letter-spacing: 3px;"
        )
        
        loading_layout.addWidget(loading_text)
        loading_layout.addWidget(self.loading_dots)
        
        # Version info
        version = QLabel("Version 1.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(
            "font-size: 12px; color: rgba(255, 255, 255, 0.5); "
            "margin-top: 20px;"
        )
        
        # Add all elements to centered content card, then to root layout
        content_layout.addWidget(logo_container, 0, Qt.AlignCenter)
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle_line1)
        content_layout.addWidget(description)
        content_layout.addWidget(loading_container)
        content_layout.addWidget(version)

        layout.addWidget(content_card, 0, Qt.AlignCenter)
        self.setLayout(layout)
        
        # Animate loading dots
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.animate_dots)
        self.dot_timer.start(500)  # Update every 500ms
        self.dot_state = 0
        
        # Close splash screen after 4 seconds
        QTimer.singleShot(4000, self.close_splash)
    
    def animate_dots(self):
        """Animate the loading dots"""
        dots = ["●○○", "○●○", "○○●", "●●○", "●●●"]
        self.loading_dots.setText(dots[self.dot_state])
        self.dot_state = (self.dot_state + 1) % len(dots)
    
    def close_splash(self):
        """Close splash screen and proceed"""
        if hasattr(self, 'dot_timer'):
            self.dot_timer.stop()
        self.on_done()


class RoleSelection(QWidget):
    def __init__(self, on_student: Callable[[], None], on_teacher: Callable[[], None], on_admin: Callable[[], None]):
        super().__init__()
        
        # Set background color
        self.setStyleSheet("background-color: #f5f7fa;")
        
        # Main container
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(30, 40, 30, 40)
        main_layout.setSpacing(30)
        
        # Circular logo centered above welcome text
        role_logo = LogoWidget(size=120)
        main_layout.addWidget(role_logo, 0, Qt.AlignCenter)

        # Header with shadow effect
        header = QLabel("Welcome to Acadix Scan")
        header.setObjectName("heading")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        
        # Add shadow effect to header
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(10)
        header_shadow.setColor(QColor(0, 0, 0, 30))
        header_shadow.setOffset(0, 2)
        header.setGraphicsEffect(header_shadow)
        
        # Subtitle
        subtitle = QLabel("Please select your role to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #6C757D; margin-bottom: 30px;")
        
        # Role cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        
        # Student card with shadow effect
        student_card = QWidget()
        student_card.setObjectName("card")
        student_card.setCursor(Qt.PointingHandCursor)
        student_card.setFixedSize(280, 320)
        student_card.setStyleSheet("""
            QWidget#card {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e9ecef;
            }
            QWidget#card:hover {
                border: 1px solid #4361ee;
                background-color: #f8f9fa;
            }
        """)
        
        # Add shadow effect to student card
        student_shadow = QGraphicsDropShadowEffect()
        student_shadow.setBlurRadius(20)
        student_shadow.setColor(QColor(0, 0, 0, 40))
        student_shadow.setOffset(0, 4)
        student_card.setGraphicsEffect(student_shadow)
        
        student_layout = QVBoxLayout(student_card)
        student_layout.setAlignment(Qt.AlignCenter)
        student_layout.setContentsMargins(20, 30, 20, 30)
        student_layout.setSpacing(15)
        
        # Student icon with colored background
        student_icon_container = QWidget()
        student_icon_container.setFixedSize(80, 80)
        student_icon_container.setStyleSheet("""
            background-color: rgba(67, 97, 238, 0.1);
            border-radius: 40px;
        """)
        student_icon_layout = QVBoxLayout(student_icon_container)
        student_icon_layout.setContentsMargins(0, 0, 0, 0)
        
        student_icon = QLabel("👨‍🎓")
        student_icon.setAlignment(Qt.AlignCenter)
        student_icon.setStyleSheet("font-size: 36px; margin-bottom: 0px;")
        student_icon_layout.addWidget(student_icon)
        
        student_title = QLabel("Student")
        student_title.setAlignment(Qt.AlignCenter)
        student_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #212529; margin-top: 5px;")
        
        student_desc = QLabel("Login to mark attendance\nand view your records")
        student_desc.setAlignment(Qt.AlignCenter)
        student_desc.setStyleSheet("font-size: 14px; color: #6C757D; margin: 10px 0; line-height: 1.4;")
        
        student_btn = QPushButton("Continue as Student")
        student_btn.setObjectName("primary")
        student_btn.setCursor(Qt.PointingHandCursor)
        student_btn.setStyleSheet("""
            QPushButton#primary {
                background-color: #4361ee;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#primary:hover {
                background-color: #3a56d4;
            }
            QPushButton#primary:pressed {
                background-color: #2e46c0;
            }
        """)
        student_btn.clicked.connect(on_student)
        
        student_layout.addWidget(student_icon_container, 0, Qt.AlignCenter)
        student_layout.addWidget(student_title)
        student_layout.addWidget(student_desc)
        student_layout.addStretch()
        student_layout.addWidget(student_btn)
        
        # Teacher card (middle)
        teacher_card = QWidget()
        teacher_card.setObjectName("card")
        teacher_card.setCursor(Qt.PointingHandCursor)
        teacher_card.setFixedSize(280, 320)
        teacher_card.setStyleSheet("""
            QWidget#card {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e9ecef;
            }
            QWidget#card:hover {
                border: 1px solid #20c997;
                background-color: #f8f9fa;
            }
        """)

        teacher_shadow = QGraphicsDropShadowEffect()
        teacher_shadow.setBlurRadius(20)
        teacher_shadow.setColor(QColor(0, 0, 0, 40))
        teacher_shadow.setOffset(0, 4)
        teacher_card.setGraphicsEffect(teacher_shadow)

        teacher_layout = QVBoxLayout(teacher_card)
        teacher_layout.setAlignment(Qt.AlignCenter)
        teacher_layout.setContentsMargins(20, 30, 20, 30)
        teacher_layout.setSpacing(15)

        teacher_icon_container = QWidget()
        teacher_icon_container.setFixedSize(80, 80)
        teacher_icon_container.setStyleSheet("""
            background-color: rgba(67, 97, 238, 0.08);
            border-radius: 40px;
        """)
        teacher_icon_layout = QVBoxLayout(teacher_icon_container)
        teacher_icon_layout.setContentsMargins(0, 0, 0, 0)

        teacher_icon = QLabel("👩‍🏫")
        teacher_icon.setAlignment(Qt.AlignCenter)
        teacher_icon.setStyleSheet("font-size: 36px; margin-bottom: 0px;")
        teacher_icon_layout.addWidget(teacher_icon)

        teacher_title = QLabel("Teacher / Faculty")
        teacher_title.setAlignment(Qt.AlignCenter)
        teacher_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #212529; margin-top: 5px;")

        teacher_desc = QLabel("Sign up or login to manage classes\nand mark attendance")
        teacher_desc.setAlignment(Qt.AlignCenter)
        teacher_desc.setStyleSheet("font-size: 14px; color: #6C757D; margin: 10px 0; line-height: 1.4;")

        teacher_btn = QPushButton("Continue as Teacher")
        teacher_btn.setObjectName("primary")
        teacher_btn.setCursor(Qt.PointingHandCursor)
        teacher_btn.setStyleSheet("""
            QPushButton#primary {
                background-color: #20c997;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#primary:hover { background-color: #1ba37e; }
        """)
        teacher_btn.clicked.connect(on_teacher)

        teacher_layout.addWidget(teacher_icon_container, 0, Qt.AlignCenter)
        teacher_layout.addWidget(teacher_title)
        teacher_layout.addWidget(teacher_desc)
        teacher_layout.addStretch()
        teacher_layout.addWidget(teacher_btn)

        # Admin card with shadow effect
        admin_card = QWidget()
        admin_card.setObjectName("card")
        admin_card.setCursor(Qt.PointingHandCursor)
        admin_card.setFixedSize(280, 320)
        admin_card.setStyleSheet("""
            QWidget#card {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e9ecef;
            }
            QWidget#card:hover {
                border: 1px solid #4361ee;
                background-color: #f8f9fa;
            }
        """)
        
        # Add shadow effect to admin card
        admin_shadow = QGraphicsDropShadowEffect()
        admin_shadow.setBlurRadius(20)
        admin_shadow.setColor(QColor(0, 0, 0, 40))
        admin_shadow.setOffset(0, 4)
        admin_card.setGraphicsEffect(admin_shadow)
        
        admin_layout = QVBoxLayout(admin_card)
        admin_layout.setAlignment(Qt.AlignCenter)
        admin_layout.setContentsMargins(20, 30, 20, 30)
        admin_layout.setSpacing(15)
        
        # Admin icon with colored background
        admin_icon_container = QWidget()
        admin_icon_container.setFixedSize(80, 80)
        admin_icon_container.setStyleSheet("""
            background-color: rgba(32, 201, 151, 0.1);
            border-radius: 40px;
        """)
        admin_icon_layout = QVBoxLayout(admin_icon_container)
        admin_icon_layout.setContentsMargins(0, 0, 0, 0)
        
        admin_icon = QLabel("👨‍💼")
        admin_icon.setAlignment(Qt.AlignCenter)
        admin_icon.setStyleSheet("font-size: 36px; margin-bottom: 0px;")
        admin_icon_layout.addWidget(admin_icon)
        
        admin_title = QLabel("Administrator")
        admin_title.setAlignment(Qt.AlignCenter)
        admin_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #212529; margin-top: 5px;")
        
        admin_desc = QLabel("Manage students, view\nattendance reports")
        admin_desc.setAlignment(Qt.AlignCenter)
        admin_desc.setStyleSheet("font-size: 14px; color: #6C757D; margin: 10px 0; line-height: 1.4;")
        
        admin_btn = QPushButton("Continue as Admin")
        admin_btn.setObjectName("success")
        admin_btn.setCursor(Qt.PointingHandCursor)
        admin_btn.setStyleSheet("""
            QPushButton#success {
                background-color: #20c997;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#success:hover {
                background-color: #1ba37e;
            }
            QPushButton#success:pressed {
                background-color: #158765;
            }
        """)
        admin_btn.clicked.connect(on_admin)
        
        admin_layout.addWidget(admin_icon_container, 0, Qt.AlignCenter)
        admin_layout.addWidget(admin_title)
        admin_layout.addWidget(admin_desc)
        admin_layout.addStretch()
        admin_layout.addWidget(admin_btn)
        
        # Add cards to layout (student, teacher, admin) - centered
        cards_layout.addWidget(student_card)
        cards_layout.addWidget(teacher_card)
        cards_layout.addWidget(admin_card)
        cards_layout.setAlignment(Qt.AlignCenter)
        
        # Wrapper for cards to ensure proper centering
        cards_container = QWidget()
        cards_wrapper = QVBoxLayout(cards_container)
        cards_wrapper.addLayout(cards_layout)
        cards_wrapper.setAlignment(cards_layout, Qt.AlignCenter)
        cards_wrapper.setContentsMargins(0, 0, 0, 0)
        
        # Add all elements to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(cards_container)
        main_layout.addStretch()
        
        self.setLayout(main_layout)


class StudentLogin(QWidget):
    def __init__(self, on_login: Callable[[str, str], None], on_signup: Callable[[], None], on_forgot: Callable[[str], None], on_back: Callable[[], None] = None):
        super().__init__()
        
        # Main container with centered content
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a card for the login form
        login_card = QWidget()
        login_card.setObjectName("card")
        login_card.setFixedWidth(400)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(15)
        # Logo (centered)
        logo_widget = LogoWidget(size=80)
        card_layout.addWidget(logo_widget, 0, Qt.AlignCenter)

        # Header
        header = QLabel("Student Login")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        
        # Subtitle
        subtitle = QLabel("Enter your credentials to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        
        # Student ID field with icon
        id_container = QWidget()
        id_layout = QHBoxLayout(id_container)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(10)
        
        id_icon = QLabel("👤")
        id_icon.setStyleSheet("font-size: 16px;")
        
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Student ID")
        
        id_layout.addWidget(id_icon)
        id_layout.addWidget(self.id_edit)
        
        # Password field with icon
        pwd_container = QWidget()
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)
        
        pwd_icon = QLabel("🔒")
        pwd_icon.setStyleSheet("font-size: 16px;")
        
        # Password input container
        pwd_input_container = QWidget()
        pwd_input_layout = QHBoxLayout(pwd_input_container)
        pwd_input_layout.setContentsMargins(0, 0, 0, 0)
        pwd_input_layout.setSpacing(5)
        
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("Password")
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        
        # Password visibility toggle button
        self.pwd_toggle = QPushButton("👁")
        self.pwd_toggle.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 16px; padding: 5px; }"
            "QPushButton:hover { background-color: rgba(67, 97, 238, 0.1); border-radius: 3px; }"
        )
        self.pwd_toggle.setFixedSize(30, 30)
        self.pwd_toggle.setCursor(Qt.PointingHandCursor)
        self.pwd_toggle.clicked.connect(self.toggle_password_visibility)
        
        pwd_input_layout.addWidget(self.pwd_edit)
        pwd_input_layout.addWidget(self.pwd_toggle)
        
        pwd_layout.addWidget(pwd_icon)
        pwd_layout.addWidget(pwd_input_container)
        
        # Login button
        btn_login = QPushButton("Login")
        btn_login.setObjectName("primary")
        btn_login.clicked.connect(lambda: on_login(self.id_edit.text(), self.pwd_edit.text()))
        
        # Forgot password link
        forgot_container = QWidget()
        forgot_layout = QHBoxLayout(forgot_container)
        forgot_layout.setContentsMargins(0, 0, 0, 0)
        forgot_layout.setAlignment(Qt.AlignRight)
        
        btn_forgot = QPushButton("Forgot Password?")
        btn_forgot.setStyleSheet(
            "background: transparent; color: #4361EE; border: none; "
            "text-decoration: underline; font-size: 12px; padding: 5px;"
        )
        btn_forgot.setCursor(Qt.PointingHandCursor)
        btn_forgot.clicked.connect(lambda: on_forgot(self.id_edit.text()))
        
        forgot_layout.addWidget(btn_forgot)
        
        # Divider
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #DEE2E6; margin: 15px 0;")
        
        # Sign up section
        signup_container = QWidget()
        signup_layout = QHBoxLayout(signup_container)
        signup_layout.setContentsMargins(0, 10, 0, 0)
        signup_layout.setAlignment(Qt.AlignCenter)
        
        signup_label = QLabel("Don't have an account?")
        signup_label.setStyleSheet("color: #6C757D; font-size: 14px;")
        
        btn_signup = QPushButton("Sign up")
        btn_signup.setStyleSheet(
            "background: transparent; color: #4361EE; border: none; "
            "text-decoration: underline; font-size: 14px; font-weight: bold; padding: 5px;"
        )
        btn_signup.setCursor(Qt.PointingHandCursor)
        btn_signup.clicked.connect(on_signup)
        
        signup_layout.addWidget(signup_label)
        signup_layout.addWidget(btn_signup)
        
        # Back to main button
        back_container = QWidget()
        back_layout = QHBoxLayout(back_container)
        back_layout.setContentsMargins(0, 10, 0, 0)
        back_layout.setAlignment(Qt.AlignLeft)
        
        if on_back:
            btn_back = QPushButton("← Back to Main")
            btn_back.setStyleSheet(
                "background: transparent; color: #6C757D; border: none; "
                "font-size: 13px; padding: 5px; text-align: left;"
            )
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.clicked.connect(on_back)
            back_layout.addWidget(btn_back)
            back_layout.addStretch()
        
        # Add all elements to card layout
        card_layout.addWidget(header)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(id_container)
        card_layout.addWidget(pwd_container)
        card_layout.addWidget(btn_login)
        card_layout.addWidget(forgot_container)
        card_layout.addWidget(divider)
        card_layout.addWidget(signup_container)
        if on_back:
            card_layout.addWidget(back_container)
        
        # Add card to main layout
        main_layout.addWidget(login_card)
        self.setLayout(main_layout)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.pwd_edit.echoMode() == QLineEdit.Password:
            self.pwd_edit.setEchoMode(QLineEdit.Normal)
            self.pwd_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.pwd_edit.setEchoMode(QLineEdit.Password)
            self.pwd_toggle.setText("👁")  # Eye


class AdminLogin(QWidget):
    def __init__(self, on_login: Callable[[str, str], None], on_back: Callable[[], None] = None):
        super().__init__()
        
        # Main container with centered content
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a card for the login form
        login_card = QWidget()
        login_card.setObjectName("card")
        login_card.setFixedWidth(400)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(15)
        
        # Header
        header = QLabel("Admin Login")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        
        # Subtitle
        subtitle = QLabel("Enter your admin credentials")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        
        # Username field with icon
        username_container = QWidget()
        username_layout = QHBoxLayout(username_container)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(10)
        
        username_icon = QLabel("👤")
        username_icon.setStyleSheet("font-size: 16px;")
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        
        username_layout.addWidget(username_icon)
        username_layout.addWidget(self.username_edit)
        
        # Password field with icon
        pwd_container = QWidget()
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)
        
        pwd_icon = QLabel("🔒")
        pwd_icon.setStyleSheet("font-size: 16px;")
        
        # Password input container
        pwd_input_container = QWidget()
        pwd_input_layout = QHBoxLayout(pwd_input_container)
        pwd_input_layout.setContentsMargins(0, 0, 0, 0)
        pwd_input_layout.setSpacing(5)
        
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("Password")
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        
        # Password visibility toggle button
        self.pwd_toggle = QPushButton("👁")
        self.pwd_toggle.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 16px; padding: 5px; }"
            "QPushButton:hover { background-color: rgba(67, 97, 238, 0.1); border-radius: 3px; }"
        )
        self.pwd_toggle.setFixedSize(30, 30)
        self.pwd_toggle.setCursor(Qt.PointingHandCursor)
        self.pwd_toggle.clicked.connect(self.toggle_password_visibility)
        
        pwd_input_layout.addWidget(self.pwd_edit)
        pwd_input_layout.addWidget(self.pwd_toggle)
        
        pwd_layout.addWidget(pwd_icon)
        pwd_layout.addWidget(pwd_input_container)
        
        # Login button
        btn_login = QPushButton("Login")
        btn_login.setObjectName("primary")
        btn_login.clicked.connect(lambda: on_login(self.username_edit.text(), self.pwd_edit.text()))
        
        # Back to main button
        back_container = QWidget()
        back_layout = QHBoxLayout(back_container)
        back_layout.setContentsMargins(0, 10, 0, 0)
        back_layout.setAlignment(Qt.AlignLeft)
        
        if on_back:
            btn_back = QPushButton("← Back to Main")
            btn_back.setStyleSheet(
                "background: transparent; color: #6C757D; border: none; "
                "font-size: 13px; padding: 5px; text-align: left;"
            )
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.clicked.connect(on_back)
            back_layout.addWidget(btn_back)
            back_layout.addStretch()
        
        # Add all elements to card layout
        card_layout.addWidget(header)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(username_container)
        card_layout.addWidget(pwd_container)
        card_layout.addWidget(btn_login)
        if on_back:
            card_layout.addWidget(back_container)
        
        # Add card to main layout
        main_layout.addWidget(login_card)
        self.setLayout(main_layout)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.pwd_edit.echoMode() == QLineEdit.Password:
            self.pwd_edit.setEchoMode(QLineEdit.Normal)
            self.pwd_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.pwd_edit.setEchoMode(QLineEdit.Password)
            self.pwd_toggle.setText("👁")  # Eye


class StudentSignup(QWidget):
    def __init__(self, on_submit: Callable[[dict], None], on_back_to_main: Callable[[], None] = None, on_back_to_login: Callable[[], None] = None):
        super().__init__()
        
        # Main container with centered content
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a card for the signup form
        signup_card = QWidget()
        signup_card.setObjectName("card")
        signup_card.setFixedWidth(500)
        
        card_layout = QVBoxLayout(signup_card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(15)
        # Header
        header = QLabel("Create Student Account")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        
        # Subtitle
        subtitle = QLabel("Fill in your details to get started")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")
        
        # Form fields with icons
        # Student ID field
        id_container = QWidget()
        id_layout = QHBoxLayout(id_container)
        id_layout.setContentsMargins(0, 0, 0, 0)
        id_layout.setSpacing(10)
        
        id_icon = QLabel("🆔")
        id_icon.setStyleSheet("font-size: 16px;")
        
        self.student_id = QLineEdit()
        self.student_id.setPlaceholderText("Student ID")
        
        id_layout.addWidget(id_icon)
        id_layout.addWidget(self.student_id)
        
        # Full Name field
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(10)
        
        name_icon = QLabel("👤")
        name_icon.setStyleSheet("font-size: 16px;")
        
        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Full Name")
        
        name_layout.addWidget(name_icon)
        name_layout.addWidget(self.full_name)
        
        # Email field
        email_container = QWidget()
        email_layout = QHBoxLayout(email_container)
        email_layout.setContentsMargins(0, 0, 0, 0)
        email_layout.setSpacing(10)
        
        email_icon = QLabel("✉️")
        email_icon.setStyleSheet("font-size: 16px;")
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        
        email_layout.addWidget(email_icon)
        email_layout.addWidget(self.email)
        
        # Roll No field
        roll_container = QWidget()
        roll_layout = QHBoxLayout(roll_container)
        roll_layout.setContentsMargins(0, 0, 0, 0)
        roll_layout.setSpacing(10)
        
        roll_icon = QLabel("🔢")
        roll_icon.setStyleSheet("font-size: 16px;")
        
        self.roll_no = QLineEdit()
        self.roll_no.setPlaceholderText("Roll No")
        
        roll_layout.addWidget(roll_icon)
        roll_layout.addWidget(self.roll_no)
        
        # PRN field
        prn_container = QWidget()
        prn_layout = QHBoxLayout(prn_container)
        prn_layout.setContentsMargins(0, 0, 0, 0)
        prn_layout.setSpacing(10)
        
        prn_icon = QLabel("🔢")
        prn_icon.setStyleSheet("font-size: 16px;")
        
        self.prn = QLineEdit()
        self.prn.setPlaceholderText("PRN")
        
        prn_layout.addWidget(prn_icon)
        prn_layout.addWidget(self.prn)
        
        # Year, Branch and Semester in one row
        year_branch_container = QWidget()
        year_branch_layout = QHBoxLayout(year_branch_container)
        year_branch_layout.setContentsMargins(0, 0, 0, 0)
        year_branch_layout.setSpacing(10)
        
        year_icon = QLabel("📅")
        year_icon.setStyleSheet("font-size: 16px;")
        
        self.year = QComboBox()
        self.year.addItems(["First Year", "Second Year", "Third Year", "Final Year"])
        
        branch_icon = QLabel("🏢")
        branch_icon.setStyleSheet("font-size: 16px;")
        
        self.branch = QComboBox()
        self.branch.addItems(["Computer", "IT", "AI/ML", "Mechanical", "Civil", "ENTC"])

        sem_icon = QLabel("📘")
        sem_icon.setStyleSheet("font-size: 16px;")
        self.semester = QComboBox()
        self.semester.addItems([str(i) for i in range(1, 9)])
        
        year_branch_layout.addWidget(year_icon)
        year_branch_layout.addWidget(self.year)
        year_branch_layout.addWidget(branch_icon)
        year_branch_layout.addWidget(self.branch)
        year_branch_layout.addWidget(sem_icon)
        year_branch_layout.addWidget(self.semester)
        
        # Phone fields
        phone_container = QWidget()
        phone_layout = QHBoxLayout(phone_container)
        phone_layout.setContentsMargins(0, 0, 0, 0)
        phone_layout.setSpacing(10)
        
        phone_icon = QLabel("📱")
        phone_icon.setStyleSheet("font-size: 16px;")
        
        self.student_phone = QLineEdit()
        self.student_phone.setPlaceholderText("Student Phone No")
        
        parent_phone_icon = QLabel("☎️")
        parent_phone_icon.setStyleSheet("font-size: 16px;")
        
        self.parent_phone = QLineEdit()
        self.parent_phone.setPlaceholderText("Parent's Phone No")
        
        phone_layout.addWidget(phone_icon)
        phone_layout.addWidget(self.student_phone)
        phone_layout.addWidget(parent_phone_icon)
        phone_layout.addWidget(self.parent_phone)
        
        # Address field
        address_container = QWidget()
        address_layout = QHBoxLayout(address_container)
        address_layout.setContentsMargins(0, 0, 0, 0)
        address_layout.setSpacing(10)
        
        address_icon = QLabel("🏠")
        address_icon.setStyleSheet("font-size: 16px;")
        
        self.address = QLineEdit()
        self.address.setPlaceholderText("Address")
        
        address_layout.addWidget(address_icon)
        address_layout.addWidget(self.address)
        
        # Security Question field
        sec_container = QWidget()
        sec_layout = QHBoxLayout(sec_container)
        sec_layout.setContentsMargins(0, 0, 0, 0)
        sec_layout.setSpacing(10)
        
        sec_icon = QLabel("❓")
        sec_icon.setStyleSheet("font-size: 16px;")
        
        sec_label = QLabel("What is your best friend's name?")
        sec_label.setStyleSheet("font-size: 14px; color: #6C757D;")
        
        self.security_answer = QLineEdit()
        
        sec_layout.addWidget(sec_icon)
        sec_layout.addWidget(sec_label)
        sec_layout.addWidget(self.security_answer)
        
        # Password field with visibility toggle
        pwd_container = QWidget()
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)
        
        pwd_icon = QLabel("🔒")
        pwd_icon.setStyleSheet("font-size: 16px;")
        
        # Password input container
        pwd_input_container = QWidget()
        pwd_input_layout = QHBoxLayout(pwd_input_container)
        pwd_input_layout.setContentsMargins(0, 0, 0, 0)
        pwd_input_layout.setSpacing(5)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Set Password")
        self.password.setEchoMode(QLineEdit.Password)
        
        # Password visibility toggle button
        self.pwd_toggle = QPushButton("👁")
        self.pwd_toggle.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 16px; padding: 5px; }"
            "QPushButton:hover { background-color: rgba(67, 97, 238, 0.1); border-radius: 3px; }"
        )
        self.pwd_toggle.setFixedSize(30, 30)
        self.pwd_toggle.setCursor(Qt.PointingHandCursor)
        self.pwd_toggle.clicked.connect(self.toggle_password_visibility)
        
        pwd_input_layout.addWidget(self.password)
        pwd_input_layout.addWidget(self.pwd_toggle)
        
        pwd_layout.addWidget(pwd_icon)
        pwd_layout.addWidget(pwd_input_container)
        
        # Confirm Password field with visibility toggle
        confirm_pwd_container = QWidget()
        confirm_pwd_layout = QHBoxLayout(confirm_pwd_container)
        confirm_pwd_layout.setContentsMargins(0, 0, 0, 0)
        confirm_pwd_layout.setSpacing(10)
        
        confirm_pwd_icon = QLabel("🔒")
        confirm_pwd_icon.setStyleSheet("font-size: 16px;")
        
        # Confirm password input container
        confirm_input_container = QWidget()
        confirm_input_layout = QHBoxLayout(confirm_input_container)
        confirm_input_layout.setContentsMargins(0, 0, 0, 0)
        confirm_input_layout.setSpacing(5)
        
        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Confirm Password")
        self.confirm.setEchoMode(QLineEdit.Password)
        
        # Confirm password visibility toggle button
        self.confirm_toggle = QPushButton("👁")
        self.confirm_toggle.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 16px; padding: 5px; }"
            "QPushButton:hover { background-color: rgba(67, 97, 238, 0.1); border-radius: 3px; }"
        )
        self.confirm_toggle.setFixedSize(30, 30)
        self.confirm_toggle.setCursor(Qt.PointingHandCursor)
        self.confirm_toggle.clicked.connect(self.toggle_confirm_password_visibility)
        
        confirm_input_layout.addWidget(self.confirm)
        confirm_input_layout.addWidget(self.confirm_toggle)
        
        confirm_pwd_layout.addWidget(confirm_pwd_icon)
        confirm_pwd_layout.addWidget(confirm_input_container)
        
        # Register button
        submit = QPushButton("Register")
        submit.setObjectName("primary")
        submit.clicked.connect(lambda: on_submit({
            "StudentID": self.student_id.text(),
            "FullName": self.full_name.text(),
            "Email": self.email.text(),
            "RollNo": self.roll_no.text(),
            "PRN": self.prn.text(),
            "StudentPhone": self.student_phone.text(),
            "ParentPhone": self.parent_phone.text(),
            "Address": self.address.text(),
            "Year": self.year.currentText(),
            "Branch": self.branch.currentText(),
            "Semester": self.semester.currentText(),
            "SecurityAnswer": self.security_answer.text(),
            "Password": self.password.text(),
            "ConfirmPassword": self.confirm.text(),
        }))
        
        # Back to login button (if provided)
        if on_back_to_login:
            # Divider
            divider = QWidget()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #DEE2E6; margin: 15px 0;")

            back_container = QWidget()
            back_layout = QHBoxLayout(back_container)
            back_layout.setContentsMargins(0, 10, 0, 0)
            back_layout.setAlignment(Qt.AlignCenter)

            back_label = QLabel("Already have an account?")
            back_label.setStyleSheet("color: #6C757D; font-size: 14px;")

            btn_back = QPushButton("Back to Login")
            btn_back.setStyleSheet(
                "background: transparent; color: #4361EE; border: none; "
                "text-decoration: underline; font-size: 14px; font-weight: bold; padding: 5px;"
            )
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.clicked.connect(on_back_to_login)

            back_layout.addWidget(back_label)
            back_layout.addWidget(btn_back)
            card_layout.addWidget(divider)
            card_layout.addWidget(back_container)
        
        # Back to main page button
        main_back_container = QWidget()
        main_back_layout = QHBoxLayout(main_back_container)
        main_back_layout.setContentsMargins(0, 10, 0, 0)
        main_back_layout.setAlignment(Qt.AlignLeft)
        
        if on_back_to_main:
            btn_main_back = QPushButton("← Back to Main")
            btn_main_back.setStyleSheet(
                "background: transparent; color: #6C757D; border: none; "
                "font-size: 13px; padding: 5px; text-align: left;"
            )
            btn_main_back.setCursor(Qt.PointingHandCursor)
            btn_main_back.clicked.connect(on_back_to_main)
            main_back_layout.addWidget(btn_main_back)
            main_back_layout.addStretch()
            card_layout.addWidget(main_back_container)
        
        # Add all elements to card layout
        card_layout.addWidget(header)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(id_container)
        card_layout.addWidget(name_container)
        card_layout.addWidget(email_container)
        card_layout.addWidget(roll_container)
        card_layout.addWidget(prn_container)
        card_layout.addWidget(year_branch_container)
        card_layout.addWidget(phone_container)
        card_layout.addWidget(address_container)
        card_layout.addWidget(sec_container)
        card_layout.addWidget(pwd_container)
        card_layout.addWidget(confirm_pwd_container)
        card_layout.addWidget(submit)
        
        # Add card to main layout
        main_layout.addWidget(signup_card)
        self.setLayout(main_layout)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password.echoMode() == QLineEdit.Password:
            self.password.setEchoMode(QLineEdit.Normal)
            self.pwd_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.pwd_toggle.setText("👁")  # Eye
    
    def toggle_confirm_password_visibility(self):
        """Toggle confirm password visibility"""
        if self.confirm.echoMode() == QLineEdit.Password:
            self.confirm.setEchoMode(QLineEdit.Normal)
            self.confirm_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.confirm.setEchoMode(QLineEdit.Password)
            self.confirm_toggle.setText("👁")  # Eye


class TeacherSignup(QWidget):
    def __init__(self, on_submit: Callable[[dict], None], on_back_to_login: Callable[[], None] = None, on_back_to_main: Callable[[], None] = None):
        super().__init__()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        signup_card = QWidget()
        signup_card.setObjectName("card")
        signup_card.setFixedWidth(500)
        card_layout = QVBoxLayout(signup_card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(15)

        header = QLabel("Teacher / Faculty Signup")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")

        subtitle = QLabel("Register your faculty account — admin approval required")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")

        # TeacherID
        id_container = QWidget()
        id_layout = QHBoxLayout(id_container)
        id_layout.setContentsMargins(0,0,0,0)
        tid_icon = QLabel("🆔")
        tid_icon.setStyleSheet("font-size: 16px;")
        self.teacher_id = QLineEdit()
        self.teacher_id.setPlaceholderText("Teacher ID")
        id_layout.addWidget(tid_icon); id_layout.addWidget(self.teacher_id)

        # Full name
        name_container = QWidget(); name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0,0,0,0)
        name_icon = QLabel("👤"); name_icon.setStyleSheet("font-size:16px;")
        self.teacher_name = QLineEdit(); self.teacher_name.setPlaceholderText("Full Name")
        name_layout.addWidget(name_icon); name_layout.addWidget(self.teacher_name)

        # Email
        email_container = QWidget(); email_layout = QHBoxLayout(email_container)
        email_icon = QLabel("✉️"); email_icon.setStyleSheet("font-size:16px;")
        self.teacher_email = QLineEdit(); self.teacher_email.setPlaceholderText("Email")
        email_layout.addWidget(email_icon); email_layout.addWidget(self.teacher_email)

        # Phone & Department
        pd_container = QWidget(); pd_layout = QHBoxLayout(pd_container)
        phone_icon = QLabel("📱"); phone_icon.setStyleSheet("font-size:16px;")
        self.teacher_phone = QLineEdit(); self.teacher_phone.setPlaceholderText("Phone")
        dept_icon = QLabel("🏢"); dept_icon.setStyleSheet("font-size:16px;")
        self.teacher_dept = QLineEdit(); self.teacher_dept.setPlaceholderText("Department")
        pd_layout.addWidget(phone_icon); pd_layout.addWidget(self.teacher_phone); pd_layout.addWidget(dept_icon); pd_layout.addWidget(self.teacher_dept)

        # Designation
        des_container = QWidget(); des_layout = QHBoxLayout(des_container)
        des_icon = QLabel("💼"); des_icon.setStyleSheet("font-size:16px;")
        self.teacher_desig = QLineEdit(); self.teacher_desig.setPlaceholderText("Designation (e.g., Lecturer)")
        des_layout.addWidget(des_icon); des_layout.addWidget(self.teacher_desig)

        # Password
        pwd_container = QWidget(); pwd_layout = QHBoxLayout(pwd_container)
        pwd_icon = QLabel("🔒"); pwd_icon.setStyleSheet("font-size:16px;")
        self.teacher_password = QLineEdit(); self.teacher_password.setPlaceholderText("Password"); self.teacher_password.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(pwd_icon); pwd_layout.addWidget(self.teacher_password)

        # Confirm
        c_container = QWidget(); c_layout = QHBoxLayout(c_container)
        c_icon = QLabel("🔒"); c_icon.setStyleSheet("font-size:16px;")
        self.teacher_confirm = QLineEdit(); self.teacher_confirm.setPlaceholderText("Confirm Password"); self.teacher_confirm.setEchoMode(QLineEdit.Password)
        c_layout.addWidget(c_icon); c_layout.addWidget(self.teacher_confirm)

        submit = QPushButton("Register (Wait for Admin Approval)")
        submit.setObjectName("primary")
        submit.clicked.connect(lambda: on_submit({
            "TeacherID": self.teacher_id.text(),
            "FullName": self.teacher_name.text(),
            "Email": self.teacher_email.text(),
            "Phone": self.teacher_phone.text(),
            "Department": self.teacher_dept.text(),
            "Designation": self.teacher_desig.text(),
            "Password": self.teacher_password.text(),
            "ConfirmPassword": self.teacher_confirm.text(),
        }))

        if on_back_to_login:
            divider = QWidget(); divider.setFixedHeight(1); divider.setStyleSheet("background-color: #DEE2E6; margin: 15px 0;")
            back_container = QWidget(); back_layout = QHBoxLayout(back_container); back_layout.setContentsMargins(0,10,0,0); back_layout.setAlignment(Qt.AlignCenter)
            back_label = QLabel("Already have an account?"); back_label.setStyleSheet("color:#6C757D;font-size:14px;")
            btn_back = QPushButton("Back to Login"); btn_back.setStyleSheet("background:transparent; color:#4361EE; border:none; text-decoration:underline;"); btn_back.clicked.connect(on_back_to_login)
            back_layout.addWidget(back_label); back_layout.addWidget(btn_back)
            card_layout.addWidget(divider); card_layout.addWidget(back_container)
        
        # Back to main button
        main_back_container = QWidget(); main_back_layout = QHBoxLayout(main_back_container); main_back_layout.setContentsMargins(0, 10, 0, 0); main_back_layout.setAlignment(Qt.AlignLeft)
        if on_back_to_main:
            btn_main_back = QPushButton("← Back to Main"); btn_main_back.setStyleSheet("background: transparent; color: #6C757D; border: none; font-size: 13px; padding: 5px; text-align: left;"); btn_main_back.setCursor(Qt.PointingHandCursor); btn_main_back.clicked.connect(on_back_to_main)
            main_back_layout.addWidget(btn_main_back); main_back_layout.addStretch()
            card_layout.addWidget(main_back_container)

        card_layout.addWidget(header); card_layout.addWidget(subtitle); card_layout.addWidget(id_container); card_layout.addWidget(name_container); card_layout.addWidget(email_container)
        card_layout.addWidget(pd_container); card_layout.addWidget(des_container); card_layout.addWidget(pwd_container); card_layout.addWidget(c_container); card_layout.addWidget(submit)

        main_layout.addWidget(signup_card)
        self.setLayout(main_layout)


class TeacherLogin(QWidget):
    def __init__(self, on_login: Callable[[str, str], None], on_signup: Callable[[], None], on_back: Callable[[], None] = None):
        super().__init__()
        main_layout = QVBoxLayout(); main_layout.setAlignment(Qt.AlignCenter); main_layout.setContentsMargins(0,0,0,0)
        login_card = QWidget(); login_card.setObjectName("card"); login_card.setFixedWidth(420)
        card_layout = QVBoxLayout(login_card); card_layout.setContentsMargins(30,40,30,40); card_layout.setSpacing(15)
        logo_widget = LogoWidget(size=80); card_layout.addWidget(logo_widget, 0, Qt.AlignCenter)
        header = QLabel("Teacher Login"); header.setAlignment(Qt.AlignCenter); header.setStyleSheet("font-size:24px;font-weight:bold;color:#212529;margin-bottom:10px;")
        subtitle = QLabel("Login after admin approval") ; subtitle.setAlignment(Qt.AlignCenter); subtitle.setStyleSheet("font-size:14px;color:#6C757D;margin-bottom:20px;")
        id_container = QWidget(); id_layout = QHBoxLayout(id_container); id_layout.setContentsMargins(0,0,0,0); id_icon = QLabel("👩‍🏫"); id_icon.setStyleSheet("font-size:16px;"); self.id_edit = QLineEdit(); self.id_edit.setPlaceholderText("Teacher ID"); id_layout.addWidget(id_icon); id_layout.addWidget(self.id_edit)
        pwd_container = QWidget(); pwd_layout = QHBoxLayout(pwd_container); pwd_layout.setContentsMargins(0,0,0,0); pwd_icon = QLabel("🔒"); pwd_icon.setStyleSheet("font-size:16px;"); self.pwd_edit = QLineEdit(); self.pwd_edit.setPlaceholderText("Password"); self.pwd_edit.setEchoMode(QLineEdit.Password); pwd_layout.addWidget(pwd_icon); pwd_layout.addWidget(self.pwd_edit)
        btn_login = QPushButton("Login"); btn_login.setObjectName("primary"); btn_login.clicked.connect(lambda: on_login(self.id_edit.text(), self.pwd_edit.text()))
        divider = QWidget(); divider.setFixedHeight(1); divider.setStyleSheet("background-color: #DEE2E6; margin: 15px 0;")
        signup_container = QWidget(); signup_layout = QHBoxLayout(signup_container); signup_layout.setContentsMargins(0,10,0,0); signup_layout.setAlignment(Qt.AlignCenter)
        signup_label = QLabel("Don't have an account?"); signup_label.setStyleSheet("color:#6C757D;font-size:14px;")
        btn_signup = QPushButton("Sign up"); btn_signup.setStyleSheet("background:transparent; color:#4361EE; border:none; text-decoration:underline;"); btn_signup.clicked.connect(on_signup)
        signup_layout.addWidget(signup_label); signup_layout.addWidget(btn_signup)
        
        # Back to main button
        back_container = QWidget()
        back_layout = QHBoxLayout(back_container)
        back_layout.setContentsMargins(0, 10, 0, 0)
        back_layout.setAlignment(Qt.AlignLeft)
        
        if on_back:
            btn_back = QPushButton("← Back to Main")
            btn_back.setStyleSheet(
                "background: transparent; color: #6C757D; border: none; "
                "font-size: 13px; padding: 5px; text-align: left;"
            )
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.clicked.connect(on_back)
            back_layout.addWidget(btn_back)
            back_layout.addStretch()
        
        card_layout.addWidget(header); card_layout.addWidget(subtitle); card_layout.addWidget(id_container); card_layout.addWidget(pwd_container); card_layout.addWidget(btn_login); card_layout.addWidget(divider); card_layout.addWidget(signup_container)
        if on_back:
            card_layout.addWidget(back_container)
        main_layout.addWidget(login_card); self.setLayout(main_layout)
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password.echoMode() == QLineEdit.Password:
            self.password.setEchoMode(QLineEdit.Normal)
            self.pwd_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.pwd_toggle.setText("👁")  # Eye
    
    def toggle_confirm_password_visibility(self):
        """Toggle confirm password visibility"""
        if self.confirm.echoMode() == QLineEdit.Password:
            self.confirm.setEchoMode(QLineEdit.Normal)
            self.confirm_toggle.setText("🙈")  # See-no-evil monkey
        else:
            self.confirm.setEchoMode(QLineEdit.Password)
            self.confirm_toggle.setText("👁")  # Eye


class AdminSignup(QWidget):
    def __init__(self, on_submit: Callable[[dict], None], on_back_to_login: Callable[[], None] = None, on_back_to_main: Callable[[], None] = None):
        super().__init__()

        # Main container with centered content
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Card for admin signup
        signup_card = QWidget()
        signup_card.setObjectName("card")
        signup_card.setFixedWidth(500)

        card_layout = QVBoxLayout(signup_card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(15)

        header = QLabel("Create Admin Account")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529; margin-bottom: 10px;")

        subtitle = QLabel("Register an administrator account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #6C757D; margin-bottom: 20px;")

        # Username
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)

        user_icon = QLabel("👤")
        user_icon.setStyleSheet("font-size: 16px;")

        self.admin_username = QLineEdit()
        self.admin_username.setPlaceholderText("Username")

        user_layout.addWidget(user_icon)
        user_layout.addWidget(self.admin_username)

        # Full name
        name_container = QWidget()
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(10)

        name_icon = QLabel("👔")
        name_icon.setStyleSheet("font-size: 16px;")

        self.admin_fullname = QLineEdit()
        self.admin_fullname.setPlaceholderText("Full Name")

        name_layout.addWidget(name_icon)
        name_layout.addWidget(self.admin_fullname)

        # Email
        email_container = QWidget()
        email_layout = QHBoxLayout(email_container)
        email_layout.setContentsMargins(0, 0, 0, 0)
        email_layout.setSpacing(10)

        email_icon = QLabel("✉️")
        email_icon.setStyleSheet("font-size: 16px;")

        self.admin_email = QLineEdit()
        self.admin_email.setPlaceholderText("Email")

        email_layout.addWidget(email_icon)
        email_layout.addWidget(self.admin_email)

        # Password
        pwd_container = QWidget()
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)

        pwd_icon = QLabel("🔒")
        pwd_icon.setStyleSheet("font-size: 16px;")

        self.admin_password = QLineEdit()
        self.admin_password.setPlaceholderText("Password")
        self.admin_password.setEchoMode(QLineEdit.Password)

        self.admin_pwd_toggle = QPushButton("👁")
        self.admin_pwd_toggle.setFixedSize(30, 30)
        self.admin_pwd_toggle.setCursor(Qt.PointingHandCursor)
        self.admin_pwd_toggle.clicked.connect(self.toggle_password_visibility)

        pwd_input_container = QWidget()
        pwd_input_layout = QHBoxLayout(pwd_input_container)
        pwd_input_layout.setContentsMargins(0, 0, 0, 0)
        pwd_input_layout.setSpacing(5)
        pwd_input_layout.addWidget(self.admin_password)
        pwd_input_layout.addWidget(self.admin_pwd_toggle)

        pwd_layout.addWidget(pwd_icon)
        pwd_layout.addWidget(pwd_input_container)

        # Confirm password
        confirm_container = QWidget()
        confirm_layout = QHBoxLayout(confirm_container)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(10)

        confirm_icon = QLabel("🔒")
        confirm_icon.setStyleSheet("font-size: 16px;")

        self.admin_confirm = QLineEdit()
        self.admin_confirm.setPlaceholderText("Confirm Password")
        self.admin_confirm.setEchoMode(QLineEdit.Password)

        self.admin_confirm_toggle = QPushButton("👁")
        self.admin_confirm_toggle.setFixedSize(30, 30)
        self.admin_confirm_toggle.setCursor(Qt.PointingHandCursor)
        self.admin_confirm_toggle.clicked.connect(self.toggle_confirm_visibility)

        confirm_input_container = QWidget()
        confirm_input_layout = QHBoxLayout(confirm_input_container)
        confirm_input_layout.setContentsMargins(0, 0, 0, 0)
        confirm_input_layout.setSpacing(5)
        confirm_input_layout.addWidget(self.admin_confirm)
        confirm_input_layout.addWidget(self.admin_confirm_toggle)

        confirm_layout.addWidget(confirm_icon)
        confirm_layout.addWidget(confirm_input_container)

        # Submit button
        submit = QPushButton("Register")
        submit.setObjectName("primary")
        submit.clicked.connect(lambda: on_submit({
            "Username": self.admin_username.text(),
            "FullName": self.admin_fullname.text(),
            "Email": self.admin_email.text(),
            "Password": self.admin_password.text(),
            "ConfirmPassword": self.admin_confirm.text(),
        }))

        # Back button
        if on_back:
            divider = QWidget()
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #DEE2E6; margin: 15px 0;")

            back_container = QWidget()
            back_layout = QHBoxLayout(back_container)
            back_layout.setContentsMargins(0, 10, 0, 0)
            back_layout.setAlignment(Qt.AlignCenter)

            back_label = QLabel("Already have an account?")
            back_label.setStyleSheet("color: #6C757D; font-size: 14px;")

            btn_back = QPushButton("Back to Login")
            btn_back.setStyleSheet(
                "background: transparent; color: #4361EE; border: none; "
                "text-decoration: underline; font-size: 14px; font-weight: bold; padding: 5px;"
            )
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.clicked.connect(on_back)

            back_layout.addWidget(back_label)
            back_layout.addWidget(btn_back)

            card_layout.addWidget(divider)
            card_layout.addWidget(back_container)

        card_layout.addWidget(header)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(user_container)
        card_layout.addWidget(name_container)
        card_layout.addWidget(email_container)
        card_layout.addWidget(pwd_container)
        card_layout.addWidget(confirm_container)
        card_layout.addWidget(submit)

        main_layout.addWidget(signup_card)
        self.setLayout(main_layout)

    def toggle_password_visibility(self):
        if self.admin_password.echoMode() == QLineEdit.Password:
            self.admin_password.setEchoMode(QLineEdit.Normal)
            self.admin_pwd_toggle.setText("🙈")
        else:
            self.admin_password.setEchoMode(QLineEdit.Password)
            self.admin_pwd_toggle.setText("👁")

    def toggle_confirm_visibility(self):
        if self.admin_confirm.echoMode() == QLineEdit.Password:
            self.admin_confirm.setEchoMode(QLineEdit.Normal)
            self.admin_confirm_toggle.setText("🙈")
        else:
            self.admin_confirm.setEchoMode(QLineEdit.Password)
            self.admin_confirm_toggle.setText("👁")


class AssistantWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_expanded = False
        
        # Create the main widget that will contain both the chat and the toggle button
        self.container = QWidget(self)
        
        # Main layout for the container
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Create the chat widget
        self.chat_widget = QWidget()
        self.chat_widget.setVisible(False)  # Initially hidden
        
        # Main layout for the chat
        main_layout = QVBoxLayout(self.chat_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("assistant-header")
        header.setStyleSheet(
            "#assistant-header { background-color: #4361EE; color: white; border-radius: 10px 10px 0 0; padding: 10px; }"
        )
        header.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        # Assistant icon
        assistant_icon = QLabel("🤖")
        assistant_icon.setStyleSheet("font-size: 20px; margin-right: 10px;")
        
        # Title
        title = QLabel("AI Assistant")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        
        # Close button
        close_button = QPushButton("×")
        close_button.setStyleSheet(
            "QPushButton { background: transparent; color: white; font-size: 20px; font-weight: bold; border: none; }"
            "QPushButton:hover { color: #f8f9fa; }"
        )
        close_button.setFixedSize(30, 30)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.toggle_assistant)
        
        header_layout.addWidget(assistant_icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        
        # Chat container
        chat_container = QWidget()
        chat_container.setObjectName("chat-container")
        chat_container.setStyleSheet(
            "#chat-container { background-color: #F8F9FA; border-left: 1px solid #DEE2E6; "
            "border-right: 1px solid #DEE2E6; }"
        )
        
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setStyleSheet(
            "QTextEdit { border: none; background-color: #F8F9FA; padding: 15px; }"
        )
        
        # Custom document to handle the chat styling
        self.chat_display.setHtml(
            "<style>"
            ".message { margin-bottom: 15px; display: flex; }"
            ".assistant { justify-content: flex-start; }"
            ".user { justify-content: flex-end; }"
            ".bubble { padding: 10px 15px; border-radius: 18px; max-width: 80%; }"
            ".assistant .bubble { background-color: #E9ECEF; color: #212529; border-bottom-left-radius: 5px; }"
            ".user .bubble { background-color: #4361EE; color: white; border-bottom-right-radius: 5px; }"
            ".time { font-size: 11px; color: #6C757D; margin-top: 5px; }"
            "</style>"
        )
        
        chat_layout.addWidget(self.chat_display)
        
        # Input container
        input_container = QWidget()
        input_container.setObjectName("input-container")
        input_container.setStyleSheet(
            "#input-container { background-color: white; border: 1px solid #DEE2E6; "
            "border-radius: 0 0 10px 10px; padding: 10px; }"
        )
        input_container.setFixedHeight(60)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 0, 10, 0)
        
        # Input field
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Ask me anything...")
        self.input_edit.setStyleSheet(
            "QLineEdit { border: 1px solid #DEE2E6; border-radius: 20px; padding: 10px 15px; }"
            "QLineEdit:focus { border-color: #4361EE; }"
        )
        self.input_edit.returnPressed.connect(self.process_input)
        
        # Send button
        send_button = QPushButton("")
        send_button.setIcon(QIcon.fromTheme("document-send"))  # Using system icon
        send_button.setText("➤")
        send_button.setStyleSheet(
            "QPushButton { background-color: #4361EE; color: white; border-radius: 18px; "
            "font-size: 16px; min-width: 36px; min-height: 36px; }"
            "QPushButton:hover { background-color: #3A56D4; }"
            "QPushButton:pressed { background-color: #2A46C4; }"
        )
        send_button.clicked.connect(self.process_input)
        
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(send_button)
        
        # Add all components to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(chat_container, 1)  # 1 = stretch factor
        main_layout.addWidget(input_container)
        
        # Create the circular toggle button
        self.toggle_button = QPushButton("🤖")
        self.toggle_button.setObjectName("assistant-toggle")
        self.toggle_button.setStyleSheet(
            "#assistant-toggle { background-color: #4361EE; color: white; border-radius: 30px; "
            "font-size: 24px; min-width: 60px; min-height: 60px; }"
            "#assistant-toggle:hover { background-color: #3A56D4; }"
        )
        self.toggle_button.setFixedSize(60, 60)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_assistant)
        
        # Add the chat widget and toggle button to the container layout
        container_layout.addWidget(self.chat_widget)
        container_layout.addWidget(self.toggle_button, 0, Qt.AlignRight | Qt.AlignBottom)
        
        # Set up the main widget layout
        main_widget_layout = QVBoxLayout(self)
        main_widget_layout.setContentsMargins(0, 0, 0, 0)
        main_widget_layout.addWidget(self.container)
        
        # Set fixed size for the chat widget
        self.chat_widget.setFixedSize(350, 450)
        
        # Response dictionary
        self.responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! How can I assist you?",
            "help": "I can help you with attendance tracking, face recognition, and system navigation. What do you need?",
            "attendance": "You can view and manage attendance in the Attendance section of the dashboard.",
            "face": "To register your face, go to the 'Train Face Data' section. For recognition, use the 'Recognize Face' feature.",
            "thanks": "You're welcome! Is there anything else you need help with?",
            "thank you": "You're welcome! Is there anything else you need help with?",
            "bye": "Goodbye! Have a great day!"
        }
        self.default_response = "I'm not sure how to help with that. Try asking about attendance, face recognition, or system navigation."
        
        # Add initial message
        self.add_message("Assistant", "Hello! I'm your AI assistant. How can I help you today?")
        
    def toggle_assistant(self):
        self.is_expanded = not self.is_expanded
        self.chat_widget.setVisible(self.is_expanded)
        self.toggle_button.setVisible(not self.is_expanded)

    def process_input(self):
        user_input = self.input_edit.text().strip()
        if not user_input:
            return
        
        self.add_message("You", user_input)
        self.input_edit.clear()
        
        # Find the best matching response
        response = self.default_response
        user_input_lower = user_input.lower()
        for key, value in self.responses.items():
            if key in user_input_lower:
                response = value
                break
        
        # Simulate typing delay
        QTimer.singleShot(800, lambda: self.add_message("Assistant", response))

    def add_message(self, sender, message):
        # Get current time
        current_time = QTime.currentTime().toString("hh:mm")
        
        # Create HTML for the message
        if sender == "Assistant":
            html = f"""
            <div class="message assistant">
                <div class="bubble">{message}
                    <div class="time">{current_time}</div>
                </div>
            </div>
            """
        else:  # User message
            html = f"""
            <div class="message user">
                <div class="bubble">{message}
                    <div class="time">{current_time}</div>
                </div>
            </div>
            """
        
        # Insert the HTML at the end of the document
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


