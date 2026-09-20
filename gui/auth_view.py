import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QStackedWidget, QFrame, QMessageBox,
    QProgressBar, QScrollArea, QListWidget, QListWidgetItem
)

from core.config import (
    load_config, save_config, list_saved_sessions, SESSIONS_DIR, APP_DIR,
    DEFAULT_API_ID, DEFAULT_API_HASH
)
from gui.icons import get_icon, get_icon_pixmap


class AuthView(QWidget):
    """Authentication and Session selection view."""

    # Signals to parent / controller
    sig_request_code = Signal(str, int, str, str, str)  # phone, api_id, api_hash, session_name, proxy_str
    sig_submit_code = Signal(str)  # code
    sig_submit_2fa = Signal(str)   # password
    sig_load_session = Signal(str, int, str, str)  # session_path, api_id, api_hash, proxy_str
    sig_auth_success = Signal(dict, str)  # user_info, session_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Build Sub-pages
        self.page_choice = self._build_choice_page()
        self.page_login_new = self._build_login_new_page()
        self.page_add_session = self._build_add_session_page()

        self.stack.addWidget(self.page_choice)       # Index 0
        self.stack.addWidget(self.page_login_new)    # Index 1
        self.stack.addWidget(self.page_add_session)  # Index 2

        self.stack.setCurrentIndex(0)
        self.refresh_saved_sessions_list()

    def _build_choice_page(self) -> QWidget:
        """Page 0: Initial choice between 'Login New' and 'Add logged in session'."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)

        # App Brand & Hero Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)

        title = QLabel("SecPhoto Interceptor")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #58a6ff;")

        subtitle = QLabel("Auto-detect & save self-destructing Telegram photos, videos & albums in real-time")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #8b949e;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # Two Big Action Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignCenter)

        # 1. "Login New" Card
        btn_login_new = QPushButton()
        btn_login_new.setObjectName("choiceCard")
        btn_login_new.setFixedSize(300, 180)
        btn_login_new.setCursor(Qt.PointingHandCursor)
        
        card1_layout = QVBoxLayout(btn_login_new)
        card1_layout.setAlignment(Qt.AlignCenter)
        card1_layout.setSpacing(10)

        icon1 = QLabel()
        icon1.setAlignment(Qt.AlignCenter)
        icon1.setPixmap(get_icon_pixmap("user-plus", color="#58a6ff", size=32))
        lbl1_title = QLabel("Login New")
        lbl1_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        lbl1_title.setAlignment(Qt.AlignCenter)
        lbl1_desc = QLabel("Sign in with Phone number,\nTelegram Code & 2FA")
        lbl1_desc.setStyleSheet("font-size: 12px; color: #8b949e;")
        lbl1_desc.setAlignment(Qt.AlignCenter)

        card1_layout.addWidget(icon1)
        card1_layout.addWidget(lbl1_title)
        card1_layout.addWidget(lbl1_desc)
        btn_login_new.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        # 2. "Add Logged In Session" Card
        btn_add_session = QPushButton()
        btn_add_session.setObjectName("choiceCard")
        btn_add_session.setFixedSize(300, 180)
        btn_add_session.setCursor(Qt.PointingHandCursor)

        card2_layout = QVBoxLayout(btn_add_session)
        card2_layout.setAlignment(Qt.AlignCenter)
        card2_layout.setSpacing(10)

        icon2 = QLabel()
        icon2.setAlignment(Qt.AlignCenter)
        icon2.setPixmap(get_icon_pixmap("folder", color="#58a6ff", size=32))
        lbl2_title = QLabel("Add Logged In Session")
        lbl2_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        lbl2_title.setAlignment(Qt.AlignCenter)
        lbl2_desc = QLabel("Import existing Telethon\n.session file or choose saved")
        lbl2_desc.setStyleSheet("font-size: 12px; color: #8b949e;")
        lbl2_desc.setAlignment(Qt.AlignCenter)

        card2_layout.addWidget(icon2)
        card2_layout.addWidget(lbl2_title)
        card2_layout.addWidget(lbl2_desc)
        btn_add_session.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        cards_layout.addWidget(btn_login_new)
        cards_layout.addWidget(btn_add_session)
        layout.addLayout(cards_layout)

        # Quick Launch Existing Sessions Section
        self.saved_sessions_frame = QFrame()
        self.saved_sessions_frame.setObjectName("card")
        self.saved_sessions_frame.setFixedWidth(620)
        sessions_layout = QVBoxLayout(self.saved_sessions_frame)
        sessions_layout.setContentsMargins(16, 14, 16, 14)
        sessions_layout.setSpacing(8)

        quick_header = QHBoxLayout()
        quick_title = QLabel("Quick Launch Detected Session")
        quick_title.setStyleSheet("font-weight: 700; color: #e6edf3; font-size: 13px;")
        quick_header.addWidget(quick_title)
        quick_header.addStretch()

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(get_icon("refresh-cw"))
        btn_refresh.setIconSize(QSize(12, 12))
        btn_refresh.setStyleSheet("padding: 2px 8px; font-size: 11px;")
        btn_refresh.clicked.connect(self.refresh_saved_sessions_list)
        quick_header.addWidget(btn_refresh)
        sessions_layout.addLayout(quick_header)

        self.sessions_list = QListWidget()
        self.sessions_list.setFixedHeight(110)
        self.sessions_list.itemDoubleClicked.connect(self._on_saved_session_double_click)
        sessions_layout.addWidget(self.sessions_list)

        btn_quick_launch = QPushButton("Connect Selected Session")
        btn_quick_launch.setIcon(get_icon("arrow-right", color="#ffffff"))
        btn_quick_launch.setIconSize(QSize(16, 16))
        btn_quick_launch.setObjectName("primaryBtn")
        btn_quick_launch.clicked.connect(self._on_quick_launch_clicked)
        sessions_layout.addWidget(btn_quick_launch)

        layout.addWidget(self.saved_sessions_frame, alignment=Qt.AlignCenter)

        return page

    def _build_login_new_page(self) -> QWidget:
        """Page 1: Login New Form with dynamic fields for code and 2FA password."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(14)

        # Header with Back Button
        top_bar = QHBoxLayout()
        btn_back = QPushButton("Back")
        btn_back.setIcon(get_icon("corner-down-left"))
        btn_back.setIconSize(QSize(12, 12))
        btn_back.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        btn_back.clicked.connect(self._on_back_from_login_clicked)
        top_bar.addWidget(btn_back)
        top_bar.addStretch()
        
        form_title = QLabel("Login New Telegram Account")
        form_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        top_bar.addWidget(form_title)
        card_layout.addLayout(top_bar)

        # Field 1: API ID
        card_layout.addWidget(QLabel("Telegram API ID:"))
        self.input_api_id = QLineEdit(str(self.config.get("api_id", DEFAULT_API_ID)))
        self.input_api_id.setPlaceholderText("e.g. 1234567")
        card_layout.addWidget(self.input_api_id)

        # Field 2: API Hash
        card_layout.addWidget(QLabel("Telegram API Hash:"))
        self.input_api_hash = QLineEdit(str(self.config.get("api_hash", DEFAULT_API_HASH)))
        self.input_api_hash.setPlaceholderText("e.g. 82bd7b4562f7ju24d182bdc38huj9352")
        card_layout.addWidget(self.input_api_hash)

        # Field 3: Phone Number
        card_layout.addWidget(QLabel("Phone Number (with Country Code):"))
        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("+1234567890")
        card_layout.addWidget(self.input_phone)

        # Field 4: Session Name
        card_layout.addWidget(QLabel("Session File Name (saved to app directory):"))
        self.input_session_name = QLineEdit("secret")
        self.input_session_name.setPlaceholderText("e.g. secret or my_account")
        card_layout.addWidget(self.input_session_name)

        # Action: Request Code Button
        self.btn_send_code = QPushButton("Send Telegram Verification Code")
        self.btn_send_code.setIcon(get_icon("send", color="#ffffff"))
        self.btn_send_code.setIconSize(QSize(16, 16))
        self.btn_send_code.setObjectName("primaryBtn")
        self.btn_send_code.clicked.connect(self._on_send_code_clicked)
        card_layout.addWidget(self.btn_send_code)

        # --- Dynamic Step 2: Verification Code Input (Shown after code is sent) ---
        self.code_frame = QFrame()
        self.code_frame.setStyleSheet("""
            background-color: #0d1117;
            border: 1px solid #388bfd;
            border-radius: 10px;
            padding: 12px;
        """)
        code_layout = QVBoxLayout(self.code_frame)
        code_layout.setSpacing(10)

        code_title = QLabel("Step 2: Telegram Verification Code")
        code_title.setStyleSheet("font-weight: 700; color: #58a6ff; font-size: 13px;")
        code_layout.addWidget(code_title)

        self.lbl_code_prompt = QLabel("Enter Verification Code (sent to your Telegram app / SMS):")
        code_layout.addWidget(self.lbl_code_prompt)

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("e.g. 12345")
        self.input_code.returnPressed.connect(self._on_verify_code_clicked)
        code_layout.addWidget(self.input_code)

        self.btn_verify_code = QPushButton("Verify Code")
        self.btn_verify_code.setIcon(get_icon("check", color="#ffffff"))
        self.btn_verify_code.setIconSize(QSize(16, 16))
        self.btn_verify_code.setObjectName("primaryBtn")
        self.btn_verify_code.clicked.connect(self._on_verify_code_clicked)
        code_layout.addWidget(self.btn_verify_code)

        self.code_frame.setVisible(False)
        card_layout.addWidget(self.code_frame)

        # --- Dynamic Step 3: 2FA Password Input (Shown ONLY if account has 2FA) ---
        self.password_frame = QFrame()
        self.password_frame.setStyleSheet("""
            background-color: #0d1117;
            border: 1px solid #a371f7;
            border-radius: 10px;
            padding: 12px;
        """)
        pwd_layout = QVBoxLayout(self.password_frame)
        pwd_layout.setSpacing(10)

        pwd_title = QLabel("Step 3: Two-Step Verification (2FA)")
        pwd_title.setStyleSheet("font-weight: 700; color: #d2a8ff; font-size: 13px;")
        pwd_layout.addWidget(pwd_title)

        self.lbl_password = QLabel("This account has 2FA enabled. Enter your Cloud Password:")
        self.lbl_password.setStyleSheet("color: #e6edf3;")
        pwd_layout.addWidget(self.lbl_password)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setPlaceholderText("Enter your 2FA password")
        self.input_password.returnPressed.connect(self._on_submit_password_clicked)
        pwd_layout.addWidget(self.input_password)

        self.btn_verify_password = QPushButton("Submit 2FA Password & Log In")
        self.btn_verify_password.setIcon(get_icon("unlock", color="#ffffff"))
        self.btn_verify_password.setIconSize(QSize(16, 16))
        self.btn_verify_password.setObjectName("successBtn")
        self.btn_verify_password.clicked.connect(self._on_submit_password_clicked)
        pwd_layout.addWidget(self.btn_verify_password)

        self.password_frame.setVisible(False)
        card_layout.addWidget(self.password_frame)

        # Status Message Box
        self.login_status_lbl = QLabel("")
        self.login_status_lbl.setAlignment(Qt.AlignCenter)
        self.login_status_lbl.setWordWrap(True)
        card_layout.addWidget(self.login_status_lbl)

        layout.addWidget(card)
        scroll.setWidget(container)
        return scroll

    def _build_add_session_page(self) -> QWidget:
        """Page 2: Add Logged in Session (import .session file or use existing)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(520)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(14)

        # Header with Back Button
        top_bar = QHBoxLayout()
        btn_back = QPushButton("Back")
        btn_back.setIcon(get_icon("corner-down-left"))
        btn_back.setIconSize(QSize(12, 12))
        btn_back.setStyleSheet("padding: 4px 10px; font-size: 12px;")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top_bar.addWidget(btn_back)
        top_bar.addStretch()

        form_title = QLabel("Add Logged In Session")
        form_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        top_bar.addWidget(form_title)
        card_layout.addLayout(top_bar)

        # Pick File Row
        card_layout.addWidget(QLabel("Select .session File:"))
        file_row = QHBoxLayout()
        self.input_session_file_path = QLineEdit()
        self.input_session_file_path.setPlaceholderText("Select path to .session file...")
        btn_browse = QPushButton("Browse...")
        btn_browse.setIcon(get_icon("folder"))
        btn_browse.setIconSize(QSize(14, 14))
        btn_browse.clicked.connect(self._on_browse_session_file)
        file_row.addWidget(self.input_session_file_path)
        file_row.addWidget(btn_browse)
        card_layout.addLayout(file_row)

        # API ID
        card_layout.addWidget(QLabel("Telegram API ID:"))
        self.input_add_api_id = QLineEdit(str(self.config.get("api_id", DEFAULT_API_ID)))
        card_layout.addWidget(self.input_add_api_id)

        # API Hash
        card_layout.addWidget(QLabel("Telegram API Hash:"))
        self.input_add_api_hash = QLineEdit(str(self.config.get("api_hash", DEFAULT_API_HASH)))
        card_layout.addWidget(self.input_add_api_hash)

        # Submit / Load
        self.btn_load_session = QPushButton("Load & Validate Session")
        self.btn_load_session.setIcon(get_icon("arrow-right", color="#ffffff"))
        self.btn_load_session.setIconSize(QSize(16, 16))
        self.btn_load_session.setObjectName("primaryBtn")
        self.btn_load_session.clicked.connect(self._on_load_session_clicked)
        card_layout.addWidget(self.btn_load_session)

        self.add_session_status_lbl = QLabel("")
        self.add_session_status_lbl.setAlignment(Qt.AlignCenter)
        self.add_session_status_lbl.setWordWrap(True)
        card_layout.addWidget(self.add_session_status_lbl)

        layout.addWidget(card)
        scroll.setWidget(container)
        return scroll

    def refresh_saved_sessions_list(self):
        """Scan directory for available .session files and populate list."""
        self.sessions_list.clear()
        sessions = list_saved_sessions()
        if not sessions:
            item = QListWidgetItem("No saved .session files found yet.")
            item.setFlags(Qt.NoItemFlags)
            self.sessions_list.addItem(item)
            return

        for s in sessions:
            size_kb = max(1, s['size_bytes'] // 1024)
            item_text = f"{s['name']}.session  ({size_kb} KB)"
            item = QListWidgetItem(item_text)
            item.setIcon(get_icon("key"))
            item.setData(Qt.UserRole, s)
            self.sessions_list.addItem(item)

        # Select first item by default
        self.sessions_list.setCurrentRow(0)

    def _on_saved_session_double_click(self, item: QListWidgetItem):
        self._on_quick_launch_clicked()

    def _on_quick_launch_clicked(self):
        item = self.sessions_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return

        session_name = data["name"]
        api_id = int(self.config.get("api_id", DEFAULT_API_ID))
        api_hash = str(self.config.get("api_hash", DEFAULT_API_HASH))
        self.sig_load_session.emit(session_name, api_id, api_hash, "")

    def _on_browse_session_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Telethon .session File", str(APP_DIR), "Telegram Session Files (*.session);;All Files (*)"
        )
        if path:
            self.input_session_file_path.setText(path)

    def _on_load_session_clicked(self):
        path_str = self.input_session_file_path.text().strip()
        if not path_str:
            self.add_session_status_lbl.setText("Please select a .session file first.")
            self.add_session_status_lbl.setStyleSheet("color: #f85149;")
            return

        try:
            api_id = int(self.input_add_api_id.text().strip())
            api_hash = self.input_add_api_hash.text().strip()
        except ValueError:
            self.add_session_status_lbl.setText("API ID must be a number.")
            self.add_session_status_lbl.setStyleSheet("color: #f85149;")
            return

        p = Path(path_str)
        # If imported from outside app directory, copy it into sessions folder
        if p.parent != APP_DIR and p.parent != SESSIONS_DIR:
            dest = SESSIONS_DIR / p.name
            try:
                shutil.copy2(p, dest)
                path_str = str(dest.with_suffix(''))  # Telethon adds .session automatically
            except Exception as e:
                print(f"Error copying session: {e}")
        else:
            # Strip .session extension as Telethon expects session name or stem
            if path_str.endswith(".session"):
                path_str = path_str[:-8]

        self.add_session_status_lbl.setText("Connecting and validating session...")
        self.add_session_status_lbl.setStyleSheet("color: #58a6ff;")
        self.btn_load_session.setEnabled(False)

        self.sig_load_session.emit(path_str, api_id, api_hash, "")

    def _on_send_code_clicked(self):
        phone = self.input_phone.text().strip()
        if not re.match(r'^\+[1-9]\d{1,14}$', phone):
            self.login_status_lbl.setText("Invalid phone format. Use international format (e.g. +1234567890)")
            self.login_status_lbl.setStyleSheet("color: #f85149;")
            return

        try:
            api_id = int(self.input_api_id.text().strip())
            api_hash = self.input_api_hash.text().strip()
        except ValueError:
            self.login_status_lbl.setText("API ID must be a valid integer.")
            self.login_status_lbl.setStyleSheet("color: #f85149;")
            return

        session_name = self.input_session_name.text().strip() or "secret"

        self.btn_send_code.setEnabled(False)
        self.login_status_lbl.setText("Sending verification code via Telegram...")
        self.login_status_lbl.setStyleSheet("color: #58a6ff;")

        self.sig_request_code.emit(phone, api_id, api_hash, session_name, "")

    def _on_back_from_login_clicked(self):
        self._reset_login_form()
        self.stack.setCurrentIndex(0)

    def _reset_login_form(self):
        """Reset dynamic login frames and inputs."""
        self.code_frame.setVisible(False)
        self.password_frame.setVisible(False)
        self.input_code.clear()
        self.input_password.clear()
        self.login_status_lbl.setText("")
        self.btn_send_code.setEnabled(True)
        self.btn_verify_code.setEnabled(True)
        self.btn_verify_password.setEnabled(True)

    def on_code_request_result(self, success: bool, message: str):
        self.btn_send_code.setEnabled(True)
        if success:
            self.login_status_lbl.setText(f"{message}")
            self.login_status_lbl.setStyleSheet("color: #3fb950;")
            self.code_frame.setVisible(True)
            self.password_frame.setVisible(False)
            self.input_code.setFocus()
        else:
            self.login_status_lbl.setText(f"{message}")
            self.login_status_lbl.setStyleSheet("color: #f85149;")

    def _on_verify_code_clicked(self):
        code = self.input_code.text().strip()
        if not code:
            self.login_status_lbl.setText("Please enter the verification code.")
            self.login_status_lbl.setStyleSheet("color: #f85149;")
            return

        self.btn_verify_code.setEnabled(False)
        self.login_status_lbl.setText("Verifying Telegram code...")
        self.login_status_lbl.setStyleSheet("color: #58a6ff;")

        self.sig_submit_code.emit(code)

    def _on_submit_password_clicked(self):
        password = self.input_password.text()
        if not password:
            self.login_status_lbl.setText("Please enter your 2FA password.")
            self.login_status_lbl.setStyleSheet("color: #f85149;")
            return

        self.btn_verify_password.setEnabled(False)
        self.login_status_lbl.setText("Verifying 2FA password...")
        self.login_status_lbl.setStyleSheet("color: #58a6ff;")

        self.sig_submit_2fa.emit(password)

    def on_auth_result(self, success: bool, requires_2fa: bool, error_msg: str, user_info: dict):
        self.btn_verify_code.setEnabled(True)
        self.btn_verify_password.setEnabled(True)
        self.btn_load_session.setEnabled(True)

        if success:
            self.login_status_lbl.setText("Logged in successfully!")
            self.login_status_lbl.setStyleSheet("color: #3fb950;")
        elif requires_2fa:
            self.login_status_lbl.setText("Two-Step Verification Required. Please enter your 2FA password below.")
            self.login_status_lbl.setStyleSheet("color: #d2a8ff; font-weight: 600;")
            self.password_frame.setVisible(True)
            self.input_password.setFocus()
        else:
            self.login_status_lbl.setText(f"{error_msg}")
            self.login_status_lbl.setStyleSheet("color: #f85149;")
            self.add_session_status_lbl.setText(f"{error_msg}")
            self.add_session_status_lbl.setStyleSheet("color: #f85149;")
