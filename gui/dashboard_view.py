import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QLineEdit, QComboBox, QSizePolicy
)

from gui.components.stat_card import StatCard
from gui.components.media_card import MediaCard
from gui.components.log_viewer import LogViewer
from core.config import load_config, APP_DIR

# Repository & Donation links (customize as needed)
GITHUB_REPO_URL = "https://github.com/Mr3rf1/SecPhoto"
DONATE_URL = "https://github.com/Mr3rf1/Mr3rf1/blob/main/DONATION.md"



class DashboardView(QWidget):
    """Main Dashboard for live self-destructive media monitoring and history."""

    sig_start_monitor = Signal()
    sig_stop_monitor = Signal()
    sig_logout = Signal()
    sig_open_settings = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.user_info: Dict[str, Any] = {}
        self.session_name: str = ""
        self.is_monitoring: bool = False
        self.media_items: List[Dict[str, Any]] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # 1. Top Header Bar (User profile + Session + Power button)
        header_card = self._build_header_card()
        main_layout.addWidget(header_card)

        # 2. Stats Metric Row
        stats_row = self._build_stats_row()
        main_layout.addLayout(stats_row)

        # 3. Main Splitter: Intercepted Media Feed (Left) & Terminal Console (Right)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle { background: #30363d; width: 2px; }")

        # Left Column: Media Feed
        feed_panel = self._build_media_feed_panel()
        splitter.addWidget(feed_panel)

        # Right Column: Console Log Viewer
        self.log_viewer = LogViewer()
        splitter.addWidget(self.log_viewer)

        # Set initial splitter proportions (60% feed, 40% logs)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter, 1)

    def _build_header_card(self) -> QFrame:
        """Build top navigation and profile bar."""
        card = QFrame()
        card.setObjectName("heroCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # Profile Avatar / Icon
        avatar_label = QLabel("🛡️")
        avatar_label.setStyleSheet("""
            background-color: #21262d;
            border: 2px solid #58a6ff;
            border-radius: 22px;
            font-size: 22px;
            padding: 8px;
        """)
        layout.addWidget(avatar_label)

        # User Info Column
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        
        self.lbl_user_name = QLabel("Telegram Account")
        self.lbl_user_name.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        
        self.lbl_user_meta = QLabel("ID: - | @username")
        self.lbl_user_meta.setStyleSheet("font-size: 12px; color: #8b949e;")

        user_info_layout.addWidget(self.lbl_user_name)
        user_info_layout.addWidget(self.lbl_user_meta)
        layout.addLayout(user_info_layout)

        layout.addSpacing(15)

        # Session & Status Badges
        badge_layout = QVBoxLayout()
        badge_layout.setSpacing(4)

        self.lbl_session_badge = QLabel("📱 Session: secret")
        self.lbl_session_badge.setStyleSheet("""
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            color: #79c0ff;
        """)
        
        self.lbl_status_badge = QLabel("🔴 Idle")
        self.lbl_status_badge.setStyleSheet("""
            background-color: rgba(248, 81, 73, 0.15);
            border: 1px solid #f85149;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
            color: #ff7b72;
        """)

        badge_layout.addWidget(self.lbl_session_badge)
        badge_layout.addWidget(self.lbl_status_badge)
        layout.addLayout(badge_layout)

        layout.addStretch()

        # Action Buttons
        btn_open_folder = QPushButton("📂 Saved Folder")
        btn_open_folder.setToolTip("Open local backup folder")
        btn_open_folder.clicked.connect(self._open_saved_folder)
        layout.addWidget(btn_open_folder)

        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.clicked.connect(lambda: self.sig_open_settings.emit())
        layout.addWidget(btn_settings)

        btn_logout = QPushButton("🚪 Logout")
        btn_logout.setStyleSheet("color: #f85149;")
        btn_logout.clicked.connect(lambda: self.sig_logout.emit())
        layout.addWidget(btn_logout)

        # Main Power Button (Start / Stop)
        self.btn_power = QPushButton("▶️ Start Monitoring")
        self.btn_power.setObjectName("powerBtnIdle")
        self.btn_power.setCursor(Qt.PointingHandCursor)
        self.btn_power.clicked.connect(self._toggle_monitor)
        layout.addWidget(self.btn_power)

        return card

    def _build_stats_row(self) -> QHBoxLayout:
        """Metric Counter Cards Row."""
        row = QHBoxLayout()
        row.setSpacing(14)

        self.card_photos = StatCard("Secret Photos", "📸", accent_color="#58a6ff")
        self.card_videos = StatCard("Secret Videos", "🎥", accent_color="#f0883e")
        self.card_total = StatCard("Total Saved", "⚡", accent_color="#3fb950")

        row.addWidget(self.card_photos)
        row.addWidget(self.card_videos)
        row.addWidget(self.card_total)

        return row

    def _build_media_feed_panel(self) -> QWidget:
        """Left panel with filter toolbar and scrollable list of media cards."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(12)

        # Feed Toolbar: Title + Filter ComboBox + Search
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        feed_title = QLabel("🖼️ Intercepted Media Feed")
        feed_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        toolbar.addWidget(feed_title)
        toolbar.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Media", "Photos", "Videos"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        toolbar.addWidget(self.filter_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search chat or @user...")
        self.search_input.setFixedWidth(190)
        self.search_input.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.search_input)

        layout.addLayout(toolbar)

        # Scroll Area for Media Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")

        self.feed_container = QWidget()
        self.feed_layout = QVBoxLayout(self.feed_container)
        self.feed_layout.setContentsMargins(0, 0, 6, 0)
        self.feed_layout.setSpacing(10)
        self.feed_layout.setAlignment(Qt.AlignTop)

        # Placeholder Banner when no items
        self.empty_label = QLabel("🛰️ Interceptor Ready.\nListening for incoming secret photos & videos in all chats...")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #8b949e;
            font-size: 14px;
            border: 2px dashed #30363d;
            border-radius: 12px;
            padding: 40px;
            margin-top: 20px;
        """)
        self.feed_layout.addWidget(self.empty_label)

        self.scroll_area.setWidget(self.feed_container)
        layout.addWidget(self.scroll_area, 1)

        # Support & Donation footer notice
        self.footer_frame = QFrame()
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(10, 5, 8, 5)
        footer_layout.setSpacing(8)

        footer_label = QLabel(
            f'⭐ If you find SecPhoto useful, please <a href="{GITHUB_REPO_URL}" style="color: #58a6ff; text-decoration: none; font-weight: 600;">Star the GitHub Repo</a> '
            f'or <a href="{DONATE_URL}" style="color: #3fb950; text-decoration: none; font-weight: 600;">Donate</a> to support development!'
        )
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        footer_layout.addWidget(footer_label, 1)

        btn_close_footer = QPushButton("✕")
        btn_close_footer.setToolTip("Dismiss")
        btn_close_footer.setCursor(Qt.PointingHandCursor)
        btn_close_footer.setFixedSize(18, 18)
        btn_close_footer.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 11px;
                font-weight: bold;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                color: #f85149;
                background-color: rgba(248, 81, 73, 0.15);
                border-radius: 9px;
            }
        """)
        btn_close_footer.clicked.connect(lambda: self.footer_frame.hide())
        footer_layout.addWidget(btn_close_footer)

        self.footer_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 27, 34, 0.7);
                border: 1px solid #21262d;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.footer_frame)

        return panel

    def set_user(self, user_info: Dict[str, Any], session_name: str):
        """Update dashboard with authenticated user details."""
        self.user_info = user_info
        self.session_name = session_name

        first_name = user_info.get("first_name", "Telegram User")
        last_name = user_info.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        username = user_info.get("username", "")
        user_id = user_info.get("id", "-")

        self.lbl_user_name.setText(full_name if full_name else "Telegram Account")
        user_meta_text = f"ID: {user_id}"
        if username:
            user_meta_text += f" | @{username}"
        self.lbl_user_meta.setText(user_meta_text)
        self.lbl_session_badge.setText(f"📱 Session: {session_name}")

    def update_status(self, status: str):
        """Update monitor status badge and button state."""
        st = status.lower()
        if st in ("listening", "monitoring"):
            self.is_monitoring = True
            self.lbl_status_badge.setText("🟢 Monitoring Active")
            self.lbl_status_badge.setStyleSheet("""
                background-color: rgba(63, 185, 80, 0.15);
                border: 1px solid #3fb950;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
                color: #3fb950;
            """)
            self.btn_power.setText("⏹️ Stop Monitoring")
            self.btn_power.setObjectName("powerBtnRunning")
            self.btn_power.setStyleSheet("""
                background-color: #da3633;
                color: #ffffff;
                border: 2px solid #f85149;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
            """)
        elif st in ("connecting", "sending_code", "verifying_code", "checking_session"):
            self.lbl_status_badge.setText("🟡 Connecting...")
            self.lbl_status_badge.setStyleSheet("""
                background-color: rgba(210, 153, 34, 0.15);
                border: 1px solid #d29922;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
                color: #e3b341;
            """)
        else:
            self.is_monitoring = False
            self.lbl_status_badge.setText("🔴 Idle")
            self.lbl_status_badge.setStyleSheet("""
                background-color: rgba(248, 81, 73, 0.15);
                border: 1px solid #f85149;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
                color: #ff7b72;
            """)
            self.btn_power.setText("▶️ Start Monitoring")
            self.btn_power.setObjectName("powerBtnIdle")
            self.btn_power.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #238636, stop:1 #1f6feb);
                color: #ffffff;
                border: 2px solid #3fb950;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
            """)

    def add_intercepted_media(self, media_data: Dict[str, Any]):
        """Add newly intercepted media card to feed and update stats counters."""
        self.media_items.insert(0, media_data)

        # Update stats
        m_type = media_data.get("type", "photo")
        if m_type == "video":
            self.card_videos.increment(1)
        else:
            self.card_photos.increment(1)

        self.card_total.increment(1)

        # Re-render feed
        self._refresh_feed_cards()

    def _refresh_feed_cards(self):
        """Render media items based on current search & filter."""
        # Hide placeholder
        self.empty_label.setVisible(len(self.media_items) == 0)

        # Clear existing card widgets (except empty_label)
        for i in reversed(range(self.feed_layout.count())):
            item = self.feed_layout.itemAt(i)
            widget = item.widget()
            if widget and widget != self.empty_label:
                widget.setParent(None)

        filter_type = self.filter_combo.currentText()
        query = self.search_input.text().strip().lower()

        for data in self.media_items:
            # Filter by type
            m_type = data.get("type", "photo")
            if filter_type == "Photos" and m_type != "photo":
                continue
            if filter_type == "Videos" and m_type != "video":
                continue

            # Filter by search query
            if query:
                chat_title = str(data.get("chat_title", "")).lower()
                username = str(data.get("username", "")).lower()
                chat_id = str(data.get("chat_id", ""))
                if query not in chat_title and query not in username and query not in chat_id:
                    continue

            card = MediaCard(data)
            self.feed_layout.addWidget(card)

    def _apply_filter(self):
        self._refresh_feed_cards()

    def _toggle_monitor(self):
        if self.is_monitoring:
            self.sig_stop_monitor.emit()
        else:
            self.sig_start_monitor.emit()

    def _open_saved_folder(self):
        folder = Path(self.config.get("local_backup_dir", APP_DIR / "saved_media"))
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == 'nt':
                os.startfile(str(folder.resolve()))
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))
        except Exception as e:
            self.log_viewer.append_log("error", f"Could not open folder: {e}")
