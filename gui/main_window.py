import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar, QMessageBox, QApplication
)

from gui.styles import DARK_THEME
from gui.auth_view import AuthView
from gui.dashboard_view import DashboardView
from gui.settings_dialog import SettingsDialog
from core.worker import TelethonWorker
from core.config import load_config, save_config, APP_DIR


class MainWindow(QMainWindow):
    """Main application window for SecPhoto."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecPhoto - Telegram Self-Destructive Media Interceptor")
        self.resize(1100, 720)
        self.setMinimumSize(880, 600)
        self.setStyleSheet(DARK_THEME)

        self.config = load_config()
        self.current_session_name = "secret"
        self.user_info: Dict[str, Any] = {}

        # Worker & Thread management
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[TelethonWorker] = None

        # Root Stacked Widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Views
        self.auth_view = AuthView()
        self.dashboard_view = DashboardView()

        self.stack.addWidget(self.auth_view)       # Index 0
        self.stack.addWidget(self.dashboard_view)  # Index 1
        self.stack.setCurrentIndex(0)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Select a login option to begin.")

        # Wire UI Actions & Signals
        self.worker = TelethonWorker(self)
        self.worker.start_worker()
        self._connect_signals()

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
            self.auth_view.add_session_status_lbl.setText("❌ Session is expired or unauthorized. Please Login New.")
            self.auth_view.add_session_status_lbl.setStyleSheet("color: #f85149;")
            self.auth_view.btn_load_session.setEnabled(True)

    def _enter_dashboard(self):
        """Transition from Auth View to Dashboard."""
        self.dashboard_view.set_user(self.user_info, self.current_session_name)
        self.stack.setCurrentIndex(1)
        self.status_bar.showMessage(f"Connected as {self.user_info.get('first_name', 'User')} (@{self.user_info.get('username', '')})")
        self.dashboard_view.log_viewer.append_log("success", f"Session ready: {self.current_session_name}.session")

    def _handle_logout(self):
        """Disconnect and return to session selection screen."""
        self.worker.stop_monitoring()
        self.stack.setCurrentIndex(0)
        self.auth_view.refresh_saved_sessions_list()
        self.status_bar.showMessage("Logged out.")

    def _open_settings_dialog(self):
        """Open settings dialog."""
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.dashboard_view.log_viewer.append_log("info", "Settings updated.")

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

    def closeEvent(self, event: QCloseEvent):
        """Gracefully terminate Telethon client and event loop on exit."""
        if self.worker:
            self.worker.shutdown()
        event.accept()
