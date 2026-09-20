import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QThread, Slot, QTimer
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar, QMessageBox, QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)

from gui.styles import (
    THEME_DARK, THEME_LIGHT, get_theme_stylesheet, get_theme_icon,
    get_theme_tooltip, get_app_icon, get_logo_pixmap, apply_windows_native_icon
)
from gui.auth_view import AuthView
from gui.dashboard_view import DashboardView
from gui.settings_dialog import SettingsDialog
from core.worker import TelethonWorker
from core.config import load_config, save_config, APP_DIR, SESSIONS_DIR
from core.version import get_window_title, get_app_user_model_id


class MainWindow(QMainWindow):
    """Main application window for SecPhoto."""

    def __init__(self):
        super().__init__()
        if sys.platform == "win32":
            import ctypes
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(get_app_user_model_id())
            except Exception:
                pass

        self.setWindowTitle(get_window_title())
        self.setWindowIcon(get_app_icon())
        apply_windows_native_icon(self)
        self.resize(1100, 720)
        self.setMinimumSize(880, 600)
        self.center_on_screen()

        self.config = load_config()
        self.current_theme = self.config.get("theme", THEME_DARK)
        if self.current_theme not in (THEME_DARK, THEME_LIGHT):
            self.current_theme = THEME_DARK

        self.current_session_name = self.config.get("last_session", "secret")
        self.user_info: Dict[str, Any] = {}

        # Worker & Thread management
        self.worker: Optional[TelethonWorker] = None

        # Root Stacked Widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Apply persisted theme to application
        self.apply_theme(self.current_theme)

        # Check if saved session exists for instant dashboard display
        self.has_saved_session = False
        last_session = self.config.get("last_session")
        if self.config.get("auto_login", True) and last_session:
            session_file = APP_DIR / f"{last_session}.session"
            alt_session_file = SESSIONS_DIR / f"{last_session}.session"
            if session_file.exists() or alt_session_file.exists():
                self.has_saved_session = True

        # Views
        self.auth_view = AuthView()
        self.dashboard_view = DashboardView()

        self.stack.addWidget(self.auth_view)       # Index 0
        self.stack.addWidget(self.dashboard_view)  # Index 1

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        if self.has_saved_session:
            # Start DIRECTLY on Dashboard without showing login window
            self.dashboard_view.set_user({"first_name": "Account", "username": ""}, self.current_session_name)
            self.stack.setCurrentIndex(1)
            self.status_bar.showMessage(f"Session: {self.current_session_name}.session")
        else:
            self.stack.setCurrentIndex(0)
            self.status_bar.showMessage("Ready. Select a login option to begin.")

        # Wire UI Actions & Signals
        self.worker = TelethonWorker(self)
        self.worker.start_worker()
        self._connect_signals()

        # Connect session in background
        if self.has_saved_session:
            QTimer.singleShot(50, self._check_auto_login)

    def _connect_signals(self):
        """Connect UI signals with worker slots and vice versa."""
        # Worker -> UI Signals
        self.worker.sig_log.connect(self._on_worker_log)
        self.worker.sig_status_changed.connect(self._on_worker_status_changed)
        self.worker.sig_code_sent.connect(self.auth_view.on_code_request_result)
        self.worker.sig_auth_result.connect(self._on_auth_result)
        self.worker.sig_session_checked.connect(self._on_session_checked)
        self.worker.sig_media_captured.connect(self._on_media_captured)

        # AuthView -> MainWindow / Worker
        self.auth_view.sig_request_code.connect(self._handle_request_code)
        self.auth_view.sig_submit_code.connect(self.worker.submit_verification_code)
        self.auth_view.sig_submit_2fa.connect(self.worker.submit_2fa_password)
        self.auth_view.sig_load_session.connect(self._handle_load_session)

        # DashboardView -> MainWindow / Worker
        self.dashboard_view.sig_start_monitor.connect(self.worker.start_monitoring)
        self.dashboard_view.sig_stop_monitor.connect(self.worker.stop_monitoring)
        self.dashboard_view.sig_logout.connect(self._handle_logout)
        self.dashboard_view.sig_open_settings.connect(self._open_settings_dialog)
        self.dashboard_view.sig_toggle_theme.connect(self._on_toggle_theme)

    @Slot()
    def _on_toggle_theme(self):
        """Toggle between dark and light themes and persist the preference."""
        new_theme = THEME_LIGHT if self.current_theme == THEME_DARK else THEME_DARK
        self.current_theme = new_theme
        self.config["theme"] = new_theme
        save_config(self.config)
        self.apply_theme(new_theme)

    def apply_theme(self, theme: str):
        """Apply theme QSS globally to application and update views."""
        stylesheet = get_theme_stylesheet(theme)
        QApplication.instance().setStyleSheet(stylesheet)
        if hasattr(self, "dashboard_view") and hasattr(self.dashboard_view, "update_theme_ui"):
            self.dashboard_view.update_theme_ui(theme)

    def _get_proxy_tuple(self) -> Optional[tuple]:
        """Read proxy configuration from config."""
        self.config = load_config()
        if self.config.get("proxy_enabled"):
            from socks import SOCKS5
            host = self.config.get("proxy_host", "127.0.0.1")
            port = int(self.config.get("proxy_port", 9050))
            return (SOCKS5, host, port)
        return None

    def _handle_request_code(self, phone: str, api_id: int, api_hash: str, session_name: str, proxy_str: str):
        """Setup engine and request verification code."""
        self.current_session_name = session_name
        self.config["api_id"] = api_id
        self.config["api_hash"] = api_hash
        self.config["last_session"] = session_name
        save_config(self.config)

        # Session file path in app dir
        session_file_path = str(APP_DIR / session_name)

        self.worker.init_engine(
            session_name_or_path=session_file_path,
            api_id=api_id,
            api_hash=api_hash,
            proxy=self._get_proxy_tuple(),
            save_local_backup=self.config.get("save_local_backup", True),
            local_backup_dir=self.config.get("local_backup_dir", str(APP_DIR / "saved_media")),
            send_to_chat=self.config.get("send_to_chat", True),
            target_chat=self.config.get("target_chat", "saved messages"),
            timezone_str=self.config.get("timezone", "Asia/Tehran")
        )
        self.worker.request_login_code(phone)

    def _handle_load_session(self, session_name_or_path: str, api_id: int, api_hash: str, proxy_str: str):
        """Validate existing session."""
        self.current_session_name = Path(session_name_or_path).stem
        self.config["api_id"] = api_id
        self.config["api_hash"] = api_hash
        self.config["last_session"] = self.current_session_name
        save_config(self.config)

        # If it's just a name, point to APP_DIR
        p = Path(session_name_or_path)
        if not p.is_absolute() and not str(session_name_or_path).startswith(str(APP_DIR)):
            target_path = str(APP_DIR / session_name_or_path)
        else:
            target_path = str(p.with_suffix(''))

        self.worker.init_engine(
            session_name_or_path=target_path,
            api_id=api_id,
            api_hash=api_hash,
            proxy=self._get_proxy_tuple(),
            save_local_backup=self.config.get("save_local_backup", True),
            local_backup_dir=self.config.get("local_backup_dir", str(APP_DIR / "saved_media")),
            send_to_chat=self.config.get("send_to_chat", True),
            target_chat=self.config.get("target_chat", "saved messages"),
            timezone_str=self.config.get("timezone", "Asia/Tehran")
        )
        self.worker.validate_session(self.current_session_name)

    @Slot(bool, bool, str, dict)
    def _on_auth_result(self, success: bool, requires_2fa: bool, error_msg: str, user_info: dict):
        self.auth_view.on_auth_result(success, requires_2fa, error_msg, user_info)
        if success:
            self.user_info = user_info
            self._enter_dashboard()

    @Slot(bool, dict, str)
    def _on_session_checked(self, is_authorized: bool, user_info: dict, session_name: str):
        if is_authorized:
            self.user_info = user_info
            self._enter_dashboard()
        else:
            self.stack.setCurrentIndex(0)
            self.auth_view.add_session_status_lbl.setText("Session is expired or unauthorized. Please Login New.")
            self.auth_view.add_session_status_lbl.setStyleSheet("color: #f85149;")
            self.auth_view.btn_load_session.setEnabled(True)
            self.status_bar.showMessage("Session unauthorized. Please log in.")

    def _check_auto_login(self):
        """Automatically log in with the last used session if available."""
        if not self.config.get("auto_login", True):
            return

        last_session = self.config.get("last_session")
        if not last_session:
            return

        # Check if session file exists
        session_file = APP_DIR / f"{last_session}.session"
        alt_session_file = SESSIONS_DIR / f"{last_session}.session"

        target_path = None
        if session_file.exists():
            target_path = str(session_file.with_suffix(''))
        elif alt_session_file.exists():
            target_path = str(alt_session_file.with_suffix(''))

        if target_path:
            self.status_bar.showMessage(f"Auto-connecting with last session: {last_session}...")
            api_id = int(self.config.get("api_id", 1234567))
            api_hash = str(self.config.get("api_hash", "82bd7b4562f7ju24d182bdc38huj9352"))
            self._handle_load_session(target_path, api_id, api_hash, "")

    def _enter_dashboard(self):
        """Transition from Auth View to Dashboard."""
        self.config["last_session"] = self.current_session_name
        self.config["auto_login"] = True
        save_config(self.config)

        self.dashboard_view.set_user(self.user_info, self.current_session_name)
        self.stack.setCurrentIndex(1)
        self.status_bar.showMessage(f"Connected as {self.user_info.get('first_name', 'User')} (@{self.user_info.get('username', '')})")
        self.dashboard_view.log_viewer.append_log("success", f"Session ready: {self.current_session_name}.session")

    def _handle_logout(self):
        """Disconnect and return to session selection screen."""
        self.config["auto_login"] = False
        save_config(self.config)

        self.worker.stop_monitoring()
        self.stack.setCurrentIndex(0)
        self.auth_view.refresh_saved_sessions_list()
        self.status_bar.showMessage("Logged out.")

    def _open_settings_dialog(self):
        """Open settings dialog with active worker validation and runtime sync."""
        dlg = SettingsDialog(self, worker=self.worker)
        if dlg.exec():
            self.config = load_config()
            if self.worker:
                self.worker.update_engine_settings(
                    save_local_backup=self.config.get("save_local_backup", True),
                    local_backup_dir=self.config.get("local_backup_dir", str(APP_DIR / "saved_media")),
                    send_to_chat=self.config.get("send_to_chat", True),
                    target_chat=self.config.get("target_chat", "saved messages"),
                    timezone_str=self.config.get("timezone", "Asia/Tehran"),
                    proxy=self._get_proxy_tuple()
                )
            self.dashboard_view.log_viewer.append_log("info", "Settings updated & synced with interceptor engine.")

    @Slot(str, str)
    def _on_worker_log(self, level: str, message: str):
        self.dashboard_view.log_viewer.append_log(level, message)
        self.status_bar.showMessage(message)

    @Slot(str)
    def _on_worker_status_changed(self, status: str):
        self.dashboard_view.update_status(status)

    @Slot(dict)
    def _on_media_captured(self, data: dict):
        self.dashboard_view.add_intercepted_media(data)

    def center_on_screen(self):
        """Center the window in the middle of the user's active screen resolution."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            # If screen work area is smaller than target dimensions, adapt gracefully
            target_w = min(self.width(), int(geo.width() * 0.95))
            target_h = min(self.height(), int(geo.height() * 0.95))
            if target_w != self.width() or target_h != self.height():
                self.resize(target_w, target_h)

            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(max(geo.x(), x), max(geo.y(), y))

    def showEvent(self, event):
        """Ensure Windows OS title bar and taskbar icons are applied to HWND upon display, and window is centered."""
        super().showEvent(event)
        if not hasattr(self, "_initially_centered"):
            self.center_on_screen()
            self._initially_centered = True
        apply_windows_native_icon(self)

    def closeEvent(self, event: QCloseEvent):
        """Gracefully terminate Telethon client and event loop on exit."""
        try:
            if self.worker:
                self.worker.shutdown()
        except Exception:
            pass
        event.accept()
