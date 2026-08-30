from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QFrame, QSpinBox, QComboBox,
    QMessageBox
)
from core.config import load_config, save_config, APP_DIR


class SettingsDialog(QDialog):
    """Settings modal dialog for configuring proxy, backup folder, and engine options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ SecPhoto Settings")
        self.setFixedWidth(480)
        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title_label = QLabel("⚙️ Application & Engine Settings")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #58a6ff;")
        layout.addWidget(title_label)

        # 1. Proxy Card
        proxy_card = QFrame()
        proxy_card.setObjectName("card")
        p_layout = QVBoxLayout(proxy_card)
        p_layout.setSpacing(10)

        self.chk_proxy = QCheckBox("Enable SOCKS5 Proxy (e.g. Tor or Shadowsocks)")
        self.chk_proxy.setChecked(self.config.get("proxy_enabled", False))
        self.chk_proxy.toggled.connect(self._toggle_proxy_fields)
        p_layout.addWidget(self.chk_proxy)

        host_port_layout = QHBoxLayout()
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

        # 2. Storage & Backup Card
        storage_card = QFrame()
        storage_card.setObjectName("card")
        s_layout = QVBoxLayout(storage_card)
        s_layout.setSpacing(10)

        self.chk_local_backup = QCheckBox("Save local file copy in addition to Telegram Saved Messages")
        self.chk_local_backup.setChecked(self.config.get("save_local_backup", True))
        s_layout.addWidget(self.chk_local_backup)

        folder_row = QHBoxLayout()
        self.input_backup_dir = QLineEdit(self.config.get("local_backup_dir", str(APP_DIR / "saved_media")))
        btn_browse_folder = QPushButton("Browse...")
        btn_browse_folder.clicked.connect(self._browse_backup_dir)
        folder_row.addWidget(self.input_backup_dir)
        folder_row.addWidget(btn_browse_folder)
        s_layout.addLayout(folder_row)

        layout.addWidget(storage_card)

        # 3. Timezone & Debounce
        adv_card = QFrame()
        adv_card.setObjectName("card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setSpacing(10)

        tz_row = QHBoxLayout()
        tz_row.addWidget(QLabel("Timezone for Captions:"))
        self.combo_tz = QComboBox()
        self.combo_tz.addItems(["Asia/Tehran", "UTC", "Local"])
        current_tz = self.config.get("timezone", "Asia/Tehran")
        idx = self.combo_tz.findText(current_tz)
        if idx >= 0:
            self.combo_tz.setCurrentIndex(idx)
        tz_row.addWidget(self.combo_tz)
        adv_layout.addLayout(tz_row)

        layout.addWidget(adv_card)

        # Footer Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("primaryBtn")
        btn_save.clicked.connect(self._save_and_close)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)
        self._toggle_proxy_fields(self.chk_proxy.isChecked())

    def _toggle_proxy_fields(self, enabled: bool):
        self.input_proxy_host.setEnabled(enabled)
        self.input_proxy_port.setEnabled(enabled)

    def _browse_backup_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Local Media Backup Folder", str(APP_DIR))
        if folder:
            self.input_backup_dir.setText(folder)

    def _save_and_close(self):
        try:
            port = int(self.input_proxy_port.text().strip())
        except ValueError:
            port = 9050

        self.config["proxy_enabled"] = self.chk_proxy.isChecked()
        self.config["proxy_host"] = self.input_proxy_host.text().strip()
        self.config["proxy_port"] = port
        self.config["save_local_backup"] = self.chk_local_backup.isChecked()
        self.config["local_backup_dir"] = self.input_backup_dir.text().strip()
        self.config["timezone"] = self.combo_tz.currentText()

        save_config(self.config)
        self.accept()
