import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.version import get_app_user_model_id

# Ensure Windows Taskbar displays the custom app icon rather than the generic Python executable icon
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(get_app_user_model_id())
    except Exception:
        pass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles import get_app_icon, apply_windows_native_icon


def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SecPhoto")
    app.setOrganizationName("Mr3rf1")
    app.setWindowIcon(get_app_icon())

    window = MainWindow()
    window.show()
    apply_windows_native_icon(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
