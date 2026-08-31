from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QFrame, QComboBox,
    QMessageBox, QApplication
)
from core.config import load_config, save_config, APP_DIR


class SettingsDialog(QDialog):
    """Settings modal dialog for configuring save destinations, proxy, and timezones."""

    def __init__(self, parent=None, worker=None):
        super().__init__(parent)
        self.worker = worker
        self.setWindowTitle("⚙️ SecPhoto Settings")
        self.setFixedWidth(520)
        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title
        title_label = QLabel("⚙️ Interceptor & Save Settings")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        layout.addWidget(title_label)

        # ----------------------------------------------------
        # 1. Save Destinations Card
        # ----------------------------------------------------
        dest_card = QFrame()
        dest_card.setObjectName("card")
        dest_layout = QVBoxLayout(dest_card)
        dest_layout.setSpacing(12)

        dest_header = QLabel("💾 Save Destinations")
        dest_header.setStyleSheet("font-size: 13px; font-weight: 700; color: #79c0ff;")
        dest_layout.addWidget(dest_header)

        # --- A. Save to Local Directory ---
        self.chk_local_backup = QCheckBox("📁 Save to local directory")
        self.chk_local_backup.setChecked(self.config.get("save_local_backup", True))
        self.chk_local_backup.toggled.connect(self._toggle_local_fields)
        dest_layout.addWidget(self.chk_local_backup)

        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(20, 0, 0, 0)
        self.input_backup_dir = QLineEdit(self.config.get("local_backup_dir", str(APP_DIR / "saved_media")))
        self.input_backup_dir.setPlaceholderText("Path to local backup directory...")
        self.btn_browse_folder = QPushButton("Browse...")
        self.btn_browse_folder.clicked.connect(self._browse_backup_dir)
        folder_row.addWidget(self.input_backup_dir)
        folder_row.addWidget(self.btn_browse_folder)
        dest_layout.addLayout(folder_row)

        dest_layout.addSpacing(4)

        # --- B. Send to Telegram Chat ---
        self.chk_send_to_chat = QCheckBox("📤 Send to Chat")
        self.chk_send_to_chat.setChecked(self.config.get("send_to_chat", True))
        self.chk_send_to_chat.toggled.connect(self._toggle_chat_fields)
        dest_layout.addWidget(self.chk_send_to_chat)

        chat_row = QHBoxLayout()
        chat_row.setContentsMargins(20, 0, 0, 0)
        self.lbl_chat_label = QLabel("Destination:")
        self.input_target_chat = QLineEdit(str(self.config.get("target_chat", "saved messages")))
        self.input_target_chat.setPlaceholderText("saved messages (default), @username, or chat ID")
        chat_row.addWidget(self.lbl_chat_label)
        chat_row.addWidget(self.input_target_chat)
        dest_layout.addLayout(chat_row)

        self.lbl_chat_status = QLabel("")
        self.lbl_chat_status.setStyleSheet("font-size: 11px; margin-left: 20px; color: #8b949e;")
        dest_layout.addWidget(self.lbl_chat_status)

        layout.addWidget(dest_card)

        # ----------------------------------------------------
        # 2. Proxy Settings Card
        # ----------------------------------------------------
        proxy_card = QFrame()
        proxy_card.setObjectName("card")
        p_layout = QVBoxLayout(proxy_card)
        p_layout.setSpacing(10)

        self.chk_proxy = QCheckBox("🌐 Enable SOCKS5 Proxy (Tor / Shadowsocks)")
        self.chk_proxy.setChecked(self.config.get("proxy_enabled", False))
        self.chk_proxy.toggled.connect(self._toggle_proxy_fields)
        p_layout.addWidget(self.chk_proxy)

        host_port_layout = QHBoxLayout()
        host_port_layout.setContentsMargins(20, 0, 0, 0)
        self.input_proxy_host = QLineEdit(self.config.get("proxy_host", "127.0.0.1"))
        self.input_proxy_host.setPlaceholderText("127.0.0.1")
        self.input_proxy_port = QLineEdit(str(self.config.get("proxy_port", 9050)))
        self.input_proxy_port.setPlaceholderText("9050")
        self.input_proxy_port.setFixedWidth(80)

        host_port_layout.addWidget(QLabel("Host:"))
        host_port_layout.addWidget(self.input_proxy_host)
        host_port_layout.addWidget(QLabel("Port:"))
        host_port_layout.addWidget(self.input_proxy_port)
        p_layout.addLayout(host_port_layout)

        layout.addWidget(proxy_card)

        # ----------------------------------------------------
        # 3. Timezone Card
        # ----------------------------------------------------
        adv_card = QFrame()
        adv_card.setObjectName("card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setSpacing(10)

        tz_row = QHBoxLayout()
        tz_row.addWidget(QLabel("🕒 Timezone for Captions:"))
        self.combo_tz = QComboBox()
        self.combo_tz.addItems(["Asia/Tehran", "UTC", "Local"])
        current_tz = self.config.get("timezone", "Asia/Tehran")
        idx = self.combo_tz.findText(current_tz)
        if idx >= 0:
            self.combo_tz.setCurrentIndex(idx)
        tz_row.addWidget(self.combo_tz)
        adv_layout.addLayout(tz_row)

        layout.addWidget(adv_card)

        # ----------------------------------------------------
        # Footer Action Buttons
        # ----------------------------------------------------
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("primaryBtn")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_box.addWidget(self.btn_save)

        layout.addLayout(btn_box)

        # Initialize frozen / enabled state of dynamic inputs
        self._toggle_local_fields(self.chk_local_backup.isChecked())
        self._toggle_chat_fields(self.chk_send_to_chat.isChecked())
        self._toggle_proxy_fields(self.chk_proxy.isChecked())

    def _toggle_local_fields(self, enabled: bool):
        """Freeze or enable local backup directory fields."""
        self.input_backup_dir.setEnabled(enabled)
        self.btn_browse_folder.setEnabled(enabled)
        if not enabled:
            self.input_backup_dir.setStyleSheet("opacity: 0.5;")
        else:
            self.input_backup_dir.setStyleSheet("")

    def _toggle_chat_fields(self, enabled: bool):
        """Freeze or enable send-to-chat destination field."""
        self.input_target_chat.setEnabled(enabled)
        self.lbl_chat_label.setEnabled(enabled)
        if not enabled:
            self.input_target_chat.setStyleSheet("opacity: 0.5;")
            self.lbl_chat_status.setText("")
        else:
            self.input_target_chat.setStyleSheet("")

    def _toggle_proxy_fields(self, enabled: bool):
        """Freeze or enable proxy fields."""
        self.input_proxy_host.setEnabled(enabled)
        self.input_proxy_port.setEnabled(enabled)

    def _browse_backup_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Local Media Backup Folder", str(APP_DIR))
        if folder:
            self.input_backup_dir.setText(folder)

    def _save_and_close(self):
        """Validate settings and target chat accessibility before saving."""
        send_to_chat = self.chk_send_to_chat.isChecked()
        target_chat = self.input_target_chat.text().strip()
        if not target_chat:
            target_chat = "saved messages"

        save_local = self.chk_local_backup.isChecked()
        local_dir = self.input_backup_dir.text().strip()

        # At least one destination should preferably be selected
        if not save_local and not send_to_chat:
            res = QMessageBox.question(
                self,
                "No Save Destination",
                "You have unchecked both 'Save to local' and 'Send to Chat'.\n"
                "Captured media will not be saved anywhere.\n\nDo you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if res != QMessageBox.Yes:
                return

        # Validate target chat accessibility if enabled
        if send_to_chat and target_chat.lower() not in ("saved messages", "me", "saved_messages"):
            if self.worker and self.worker.engine:
                self.btn_save.setEnabled(False)
                self.btn_save.setText("Checking chat...")
                self.lbl_chat_status.setStyleSheet("font-size: 11px; margin-left: 20px; color: #58a6ff;")
                self.lbl_chat_status.setText("⏳ Checking chat accessibility in Telegram...")
                QApplication.processEvents()

                accessible, msg = self.worker.validate_target_chat(target_chat)
                self.btn_save.setEnabled(True)
                self.btn_save.setText("Save Settings")

                if not accessible:
                    self.lbl_chat_status.setStyleSheet("font-size: 11px; margin-left: 20px; color: #f85149;")
                    self.lbl_chat_status.setText(f"❌ {msg}")
                    QMessageBox.warning(
                        self,
                        "Chat Inaccessible",
                        f"Could not verify destination chat '{target_chat}':\n\n{msg}\n\n"
                        "Please check the username or numeric ID and make sure you can send messages to it."
                    )
                    return
                else:
                    self.lbl_chat_status.setStyleSheet("font-size: 11px; margin-left: 20px; color: #3fb950;")
                    self.lbl_chat_status.setText(f"✅ {msg}")

        # Parse proxy port
        try:
            port = int(self.input_proxy_port.text().strip())
        except ValueError:
            port = 9050

        # Save to configuration
        self.config["save_local_backup"] = save_local
        self.config["local_backup_dir"] = local_dir if local_dir else str(APP_DIR / "saved_media")
        self.config["send_to_chat"] = send_to_chat
        self.config["target_chat"] = target_chat
        self.config["forward_to_saved_messages"] = send_to_chat
        self.config["proxy_enabled"] = self.chk_proxy.isChecked()
        self.config["proxy_host"] = self.input_proxy_host.text().strip()
        self.config["proxy_port"] = port
        self.config["timezone"] = self.combo_tz.currentText()

        save_config(self.config)
        self.accept()
