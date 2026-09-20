from typing import Union
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from gui.icons import get_icon_pixmap, SVG_PATHS


class StatCard(QFrame):
    """Modern metric card with vector icon, dynamic counter, and label."""

    def __init__(self, title: str, icon_name: str, accent_color: str = "#58a6ff", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.accent_color = accent_color
        self.icon_name = icon_name
        self._count = 0

        self.setStyleSheet(f"""
            QFrame#card:hover {{
                border-color: {accent_color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Header row: Title + Icon
        top_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("subtitleLabel")
        self.title_label.setStyleSheet("font-size: 13px; font-weight: 600;")

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self._render_icon()

        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.icon_label)

        # Large Count Display
        self.val_label = QLabel("0")
        self.val_label.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {accent_color};")

        layout.addLayout(top_layout)
        layout.addWidget(self.val_label)

    def _render_icon(self):
        """Render icon using vector SVG pixmap or fallback."""
        if self.icon_name in SVG_PATHS:
            pix = get_icon_pixmap(self.icon_name, color=self.accent_color, size=20)
            self.icon_label.setPixmap(pix)
        else:
            self.icon_label.setText(self.icon_name)
            self.icon_label.setStyleSheet(f"font-size: 18px; color: {self.accent_color};")

    def set_icon(self, icon_name: str):
        self.icon_name = icon_name
        self._render_icon()

    def set_value(self, val: int):
        self._count = val
        self.val_label.setText(str(val))

    def increment(self, amount: int = 1):
        self._count += amount
        self.val_label.setText(str(self._count))

    def get_value(self) -> int:
        return self._count
