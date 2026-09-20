from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QCheckBox
)


class LogViewer(QFrame):
    """Terminal-like color log console widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header toolbar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        from gui.icons import get_icon, get_icon_pixmap
        icon_label = QLabel()
        icon_label.setPixmap(get_icon_pixmap("terminal", color="#58a6ff", size=16))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Live Engine Logs")
        title_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.autoscroll_chk = QCheckBox("Auto-scroll")
        self.autoscroll_chk.setChecked(True)
        header_layout.addWidget(self.autoscroll_chk)

        copy_btn = QPushButton("Copy")
        copy_btn.setIcon(get_icon("copy"))
        copy_btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        copy_btn.clicked.connect(self.copy_logs)
        header_layout.addWidget(copy_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Console Text Edit
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #05080c;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px;
                color: #e6edf3;
            }
        """)
        layout.addWidget(self.text_edit)

    def append_log(self, level: str, message: str):
        """Append a color-coded log message."""
        ts = datetime.now().strftime("%H:%M:%S")
        lvl = level.lower()

        if lvl == "success":
            color = "#3fb950"
            tag = "SUCCESS"
        elif lvl in ("warning", "warn"):
            color = "#d29922"
            tag = "WARN"
        elif lvl in ("error", "fatal"):
            color = "#f85149"
            tag = "ERROR"
        elif lvl == "special":
            color = "#a371f7"
            tag = "MEDIA"
        else:
            color = "#58a6ff"
            tag = "INFO"

        html = f"<div style='margin-bottom: 3px; font-family: Consolas, monospace;'>" \
               f"<span style='color: #8b949e;'>[{ts}]</span> " \
               f"<span style='color: {color}; font-weight: bold;'>[{tag}]</span> " \
               f"<span style='color: #e6edf3;'>{message}</span>" \
               f"</div>"

        self.text_edit.append(html)

        if self.autoscroll_chk.isChecked():
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.text_edit.setTextCursor(cursor)

    def clear_logs(self):
        self.text_edit.clear()

    def copy_logs(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.text_edit.toPlainText())
