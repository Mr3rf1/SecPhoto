from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from core.config import APP_DIR

THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_THEME = THEME_DARK


def get_app_icon() -> QIcon:
    """Return QIcon of application logo for title bars, taskbars and windows."""
    for name in ["logo.ico", "logo.jpg", "secphoto.jpg"]:
        p = APP_DIR / name
        if p.exists():
            return QIcon(str(p))
    return QIcon()


def get_logo_pixmap(size: int = 44, radius: int = 12) -> Optional[QPixmap]:
    """Return a high-quality anti-aliased rounded QPixmap of the logo for UI headers and app bars."""
    for name in ["logo.jpg", "logo.ico", "secphoto.jpg"]:
        p = APP_DIR / name
        if p.exists():
            orig = QPixmap(str(p))
            if not orig.isNull():
                scaled = orig.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                target = QPixmap(size, size)
                target.fill(Qt.GlobalColor.transparent)
                painter = QPainter(target)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, size, size, radius, radius)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                return target
    return None


DARK_THEME = """
/* Global Application Styles */
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

/* Theme Toggle Button */
QPushButton#themeToggleBtn {
    background-color: #21262d;
    color: #f0f6fc;
    border: 1px solid #30363d;
    border-radius: 8px;
    font-size: 15px;
    padding: 8px 12px;
}

QPushButton#themeToggleBtn:hover {
    background-color: #30363d;
    border-color: #58a6ff;
    color: #ffffff;
}

QPushButton#themeToggleBtn:pressed {
    background-color: #161b22;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #161b22;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #161b22;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    min-width: 25px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #58a6ff;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Window & Panels */
QMainWindow {
    background-color: #0d1117;
}

QFrame#card, QFrame.card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
}

QFrame#glassCard {
    background-color: rgba(22, 27, 34, 0.85);
    border: 1px solid rgba(88, 166, 255, 0.2);
    border-radius: 14px;
}

QFrame#heroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #161b22, stop:1 #1f242c);
    border: 1px solid #30363d;
    border-radius: 16px;
}

/* Typography & Headings */
QLabel {
    color: #e6edf3;
    background: transparent;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #8b949e;
}

QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#badge {
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Line Inputs */
QLineEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 14px;
    color: #ffffff;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #58a6ff;
    background-color: #13171e;
}

QLineEdit:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

/* Push Buttons */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #30363d;
    color: #ffffff;
    border-color: #8b949e;
}

QPushButton:pressed {
    background-color: #161b22;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

/* Primary Action Button (Telegram Blue) */
QPushButton#primaryBtn, QPushButton.primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #238636);
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
    font-weight: 700;
}

QPushButton#primaryBtn:hover, QPushButton.primary:hover {
    background-color: #388bfd;
    border-color: #58a6ff;
}

/* Success Green Button */
QPushButton#successBtn, QPushButton.success {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
    font-weight: 700;
}

QPushButton#successBtn:hover, QPushButton.success:hover {
    background-color: #2ea043;
    border-color: #3fb950;
}

/* Danger / Stop Red Button */
QPushButton#dangerBtn, QPushButton.danger {
    background-color: #da3633;
    color: #ffffff;
    border: 1px solid #f85149;
    font-weight: 700;
}

QPushButton#dangerBtn:hover, QPushButton.danger:hover {
    background-color: #f85149;
    border-color: #ff7b72;
}

/* Power / Toggle Button for Monitor */
QPushButton#powerBtnRunning {
    background-color: #da3633;
    color: #ffffff;
    border: 2px solid #f85149;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton#powerBtnIdle {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #238636, stop:1 #1f6feb);
    color: #ffffff;
    border: 2px solid #3fb950;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
}

/* Big Action Choice Cards in Auth View */
QPushButton#choiceCard {
    background-color: #161b22;
    border: 2px solid #30363d;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}

QPushButton#choiceCard:hover {
    border: 2px solid #58a6ff;
    background-color: #1c2128;
}

/* Lists & Tables */
QListWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 6px;
    color: #e6edf3;
}

QListWidget::item {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    margin: 4px 0px;
    padding: 10px;
}

QListWidget::item:hover {
    background-color: #1c2128;
    border-color: #58a6ff;
}

QListWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
    border-color: #58a6ff;
}

/* Combo Box */
QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
    color: #e6edf3;
    padding: 4px;
}

/* Plain Text & Log Console */
QPlainTextEdit#logConsole {
    background-color: #05080c;
    border: 1px solid #30363d;
    border-radius: 10px;
    color: #7ee787;
    font-family: "Consolas", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    padding: 10px;
}

/* Checkbox */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #30363d;
    background-color: #0d1117;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #58a6ff;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 10px;
    background-color: #161b22;
    top: -1px;
}

QTabBar::tab {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 4px;
    color: #8b949e;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #161b22;
    color: #58a6ff;
    border-color: #30363d;
}

QTabBar::tab:hover:!selected {
    background-color: #161b22;
    color: #c9d1d9;
}

/* Dialogs & Message Boxes */
QDialog, QMessageBox {
    background-color: #0d1117;
    color: #e6edf3;
}

QMessageBox QLabel {
    color: #e6edf3;
}

/* Donation / Support Banner Box */
QFrame#donationBox {
    background-color: rgba(22, 27, 34, 0.85);
    border: 1px solid #30363d;
    border-radius: 8px;
}

QLabel#donationLabel {
    color: #8b949e;
    font-size: 11px;
}

QPushButton#donationCloseBtn {
    background-color: transparent;
    color: #8b949e;
    border: none;
    font-size: 11px;
    font-weight: bold;
    padding: 0px;
    margin: 0px;
    border-radius: 9px;
}

QPushButton#donationCloseBtn:hover {
    color: #f85149;
    background-color: rgba(248, 81, 73, 0.15);
}

/* Status Bar */
QStatusBar {
    background-color: #161b22;
    border-top: 1px solid #30363d;
    color: #8b949e;
    font-size: 12px;
}
"""

LIGHT_THEME = """
/* Global Application Styles - Modern Clean Light */
QWidget {
    background-color: #f6f8fa;
    color: #1f2328;
    font-family: "Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #0969da;
    selection-color: #ffffff;
}

/* Theme Toggle Button */
QPushButton#themeToggleBtn {
    background-color: #f6f8fa;
    color: #1f2328;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    font-size: 15px;
    padding: 8px 12px;
}

QPushButton#themeToggleBtn:hover {
    background-color: #eaeef2;
    border-color: #0969da;
    color: #0969da;
}

QPushButton#themeToggleBtn:pressed {
    background-color: #d0d7de;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #f6f8fa;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #d0d7de;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #0969da;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #f6f8fa;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #d0d7de;
    min-width: 25px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #0969da;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Window & Panels */
QMainWindow {
    background-color: #f6f8fa;
}

QFrame#card, QFrame.card {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 12px;
}

QFrame#glassCard {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(9, 105, 218, 0.25);
    border-radius: 14px;
}

QFrame#heroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f6f8fa);
    border: 1px solid #d0d7de;
    border-radius: 16px;
}

/* Typography & Headings */
QLabel {
    color: #1f2328;
    background: transparent;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: 700;
    color: #1f2328;
    letter-spacing: 0.5px;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #656d76;
}

QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 600;
    color: #1f2328;
}

QLabel#badge {
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Line Inputs */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 10px 14px;
    color: #1f2328;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #0969da;
    background-color: #ffffff;
}

QLineEdit:disabled {
    background-color: #f6f8fa;
    color: #8c959f;
    border-color: #d0d7de;
}

/* Push Buttons */
QPushButton {
    background-color: #f6f8fa;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #eaeef2;
    color: #1f2328;
    border-color: #8c959f;
}

QPushButton:pressed {
    background-color: #d0d7de;
}

QPushButton:disabled {
    background-color: #f6f8fa;
    color: #8c959f;
    border-color: #d0d7de;
}

/* Primary Action Button (Telegram Blue) */
QPushButton#primaryBtn, QPushButton.primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0969da, stop:1 #1a7f37);
    background-color: #0969da;
    color: #ffffff;
    border: 1px solid #0969da;
    font-weight: 700;
}

QPushButton#primaryBtn:hover, QPushButton.primary:hover {
    background-color: #0854b0;
    border-color: #0854b0;
}

/* Success Green Button */
QPushButton#successBtn, QPushButton.success {
    background-color: #1a7f37;
    color: #ffffff;
    border: 1px solid #1a7f37;
    font-weight: 700;
}

QPushButton#successBtn:hover, QPushButton.success:hover {
    background-color: #176f30;
    border-color: #176f30;
}

/* Danger / Stop Red Button */
QPushButton#dangerBtn, QPushButton.danger {
    background-color: #cf222e;
    color: #ffffff;
    border: 1px solid #cf222e;
    font-weight: 700;
}

QPushButton#dangerBtn:hover, QPushButton.danger:hover {
    background-color: #a40e26;
    border-color: #a40e26;
}

/* Power / Toggle Button for Monitor */
QPushButton#powerBtnRunning {
    background-color: #cf222e;
    color: #ffffff;
    border: 2px solid #a40e26;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton#powerBtnIdle {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a7f37, stop:1 #0969da);
    color: #ffffff;
    border: 2px solid #1a7f37;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 700;
}

/* Big Action Choice Cards in Auth View */
QPushButton#choiceCard {
    background-color: #ffffff;
    border: 2px solid #d0d7de;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}

QPushButton#choiceCard:hover {
    border: 2px solid #0969da;
    background-color: #f6f8fa;
}

/* Lists & Tables */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    padding: 6px;
    color: #1f2328;
}

QListWidget::item {
    background-color: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    margin: 4px 0px;
    padding: 10px;
}

QListWidget::item:hover {
    background-color: #edf2f7;
    border-color: #0969da;
}

QListWidget::item:selected {
    background-color: #0969da;
    color: #ffffff;
    border-color: #0969da;
}

/* Combo Box */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1f2328;
}

QComboBox:hover {
    border-color: #0969da;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    selection-background-color: #0969da;
    selection-color: #ffffff;
    color: #1f2328;
    padding: 4px;
}

/* Plain Text & Log Console */
QPlainTextEdit#logConsole {
    background-color: #0d1117;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    color: #58a6ff;
    font-family: "Consolas", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    padding: 10px;
}

/* Checkbox */
QCheckBox {
    color: #1f2328;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #d0d7de;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 10px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 4px;
    color: #656d76;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0969da;
    border-color: #d0d7de;
}

QTabBar::tab:hover:!selected {
    background-color: #eaeef2;
    color: #1f2328;
}

/* Dialogs & Message Boxes */
QDialog, QMessageBox {
    background-color: #ffffff;
    color: #1f2328;
}

QMessageBox QLabel {
    color: #1f2328;
}

/* Donation / Support Banner Box */
QFrame#donationBox {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
}

QLabel#donationLabel {
    color: #57606a;
    font-size: 11px;
}

QPushButton#donationCloseBtn {
    background-color: transparent;
    color: #57606a;
    border: none;
    font-size: 11px;
    font-weight: bold;
    padding: 0px;
    margin: 0px;
    border-radius: 9px;
}

QPushButton#donationCloseBtn:hover {
    color: #cf222e;
    background-color: rgba(207, 34, 46, 0.12);
}

/* Status Bar */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #d0d7de;
    color: #656d76;
    font-size: 12px;
}
"""


def get_theme_stylesheet(theme: str) -> str:
    """Return the complete QSS stylesheet for the given theme ('dark' or 'light')."""
    if theme == THEME_LIGHT:
        return LIGHT_THEME
    return DARK_THEME


def get_theme_icon(theme: str) -> str:
    """Return the opposing display symbol for the toggle button."""
    if theme == THEME_LIGHT:
        return "🌙"
    return "☀️"


def get_theme_tooltip(theme: str) -> str:
    """Return user-facing tooltip text for the theme toggle button."""
    if theme == THEME_LIGHT:
        return "Switch to Dark Mode"
    return "Switch to Light Mode"
