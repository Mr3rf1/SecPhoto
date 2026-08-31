import os
import subprocess
from pathlib import Path
from typing import Dict, Any

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


class MediaCard(QFrame):
    """Card widget representing an intercepted self-destructing media item."""

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.data = data
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        media_type = data.get("type", "photo")
        ttl = data.get("ttl_seconds")
        chat_title = data.get("chat_title", "Unknown Chat")
        username = data.get("username")
        chat_id = data.get("chat_id", 0)
        timestamp = data.get("timestamp", "")
        count = data.get("count", 1)
        is_reply = data.get("is_reply", False)
        local_files = data.get("local_files", [])

        # Border color based on type
        if media_type == "video":
            border_color = "#f0883e"
            type_label_text = "🎥 Secret Video"
            type_badge_bg = "rgba(240, 136, 62, 0.2)"
            type_badge_color = "#ffa657"
        else:
            border_color = "#58a6ff"
            type_label_text = "📸 Secret Photo"
            type_badge_bg = "rgba(88, 166, 255, 0.2)"
            type_badge_color = "#79c0ff"

        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-left: 4px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
            QFrame#card:hover {{
                background-color: #1c2128;
                border-color: #58a6ff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header Row: Type Badge + TTL Badge + Timestamp
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        type_badge = QLabel(f"  {type_label_text}  ")
        type_badge.setStyleSheet(f"""
            background-color: {type_badge_bg};
            color: {type_badge_color};
            font-weight: 700;
            font-size: 11px;
            border-radius: 6px;
            padding: 4px 6px;
        """)
        header_row.addWidget(type_badge)

        if ttl:
            ttl_badge = QLabel(f"⏱️ TTL: {ttl}s")
            ttl_badge.setStyleSheet("""
                background-color: rgba(248, 81, 73, 0.2);
                color: #ff7b72;
                font-weight: 600;
                font-size: 11px;
                border-radius: 6px;
                padding: 4px 6px;
            """)
            header_row.addWidget(ttl_badge)

        if is_reply:
            reply_badge = QLabel("↩️ Replied Message")
            reply_badge.setStyleSheet("""
                background-color: rgba(210, 153, 34, 0.2);
                color: #e3b341;
                font-size: 11px;
                font-weight: 600;
                border-radius: 6px;
                padding: 4px 6px;
            """)
            header_row.addWidget(reply_badge)

        header_row.addStretch()

        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        header_row.addWidget(time_label)
        layout.addLayout(header_row)

        # Chat / Sender Info
        info_row = QHBoxLayout()
        user_display = f"👤 <b>{chat_title}</b>"
        if username:
            user_display += f" (<span style='color:#58a6ff;'>@{username}</span>)"
        user_display += f"  <span style='color:#8b949e;'>[ID: {chat_id}]</span>"

        sender_label = QLabel(user_display)
        sender_label.setTextFormat(Qt.RichText)
        sender_label.setStyleSheet("font-size: 13px; color: #e6edf3;")
        info_row.addWidget(sender_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        # Action / Status Footer
        footer_row = QHBoxLayout()
        footer_row.setSpacing(10)

        saved_label = QLabel("✓ Saved to Telegram 'Saved Messages'")
        saved_label.setStyleSheet("color: #3fb950; font-weight: 600; font-size: 11px;")
        footer_row.addWidget(saved_label)
        footer_row.addStretch()

        if local_files and os.path.exists(local_files[0]):
            open_btn = QPushButton("📂 Open File")
            open_btn.setStyleSheet("""
                background-color: #21262d;
                color: #58a6ff;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            open_btn.clicked.connect(lambda: self.open_local_file(local_files[0]))
            footer_row.addWidget(open_btn)

        copy_btn = QPushButton("📋 Copy Link")
        copy_btn.setStyleSheet("""
            background-color: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
        """)
        copy_btn.clicked.connect(lambda: self.copy_chat_link(chat_id, username))
        footer_row.addWidget(copy_btn)

        layout.addLayout(footer_row)

    def open_local_file(self, file_path: str):
        """Open the saved media file with default system viewer or show in folder."""
        p = Path(file_path)
        if p.exists():
            try:
                if os.name == 'nt':
                    subprocess.run(['explorer', '/select,', str(p.resolve())], check=False)
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.resolve())))
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.resolve())))

    def copy_chat_link(self, chat_id: int, username: str):
        """Copy Telegram user / chat link to clipboard."""
        link = f"https://t.me/{username}" if username else f"tg://user?id={chat_id}"
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(link)
