from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel


class StatCard(QFrame):
    """Modern metric card with icon, dynamic counter, and label."""

    def __init__(self, title: str, icon_str: str, accent_color: str = "#58a6ff", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.accent_color = accent_color
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
        
        self.icon_label = QLabel(icon_str)
        self.icon_label.setStyleSheet(f"font-size: 18px; color: {accent_color};")

        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.icon_label)

        # Large Count Display
        self.val_label = QLabel("0")
        self.val_label.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {accent_color};")

        layout.addLayout(top_layout)
        layout.addWidget(self.val_label)

    def set_value(self, val: int):
        self._count = val
        self.val_label.setText(str(val))

    def increment(self, amount: int = 1):
        self._count += amount
        self.val_label.setText(str(self._count))

    def get_value(self) -> int:
        return self._count
