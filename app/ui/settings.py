"""设置窗口"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QFileDialog, QTabWidget,
    QWidget, QSpinBox
)
from PyQt6.QtCore import Qt
from app.config import config, APP_NAME, APP_VERSION


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} 设置")
        self.setMinimumSize(520, 480)
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: #eee; }
            QGroupBox {
                border: 1px solid #444; border-radius: 6px; margin-top: 12px;
                padding-top: 12px; font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QLineEdit, QComboBox, QSpinBox {
                background: #2d2d2d; border: 1px solid #555; border-radius: 4px;
                padding: 5px; color: #eee;
            }
            QPushButton {
                background: #0078d4; border: none; border-radius: 4px;
                padding: 6px 16px; color: white;
            }
            QPushButton:hover { background: #1084d9; }
            QCheckBox { spacing: 6px; }
        """)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel(f"⚙️ {APP_NAME}  v{APP_VERSION}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # === 快捷键页 ===
        tab_hk = QWidget()
        hk_layout = QFormLayout(tab_hk)
        self.hk_edits = {}
        hk_items = [
            ("region_capture", "区域截图"),
            ("fullscreen_capture", "全屏截图"),
            ("window_capture", "窗口截图"),
            ("start_stop_record", "开始/停止录屏"),
            ("pin_clipboard", "贴图（剪贴板）"),
            ("ocr_capture", "OCR 文字识别"),
        ]
        hk = config.get("hotkeys", default={})
        for key, label in hk_items:
            edit = QLineEdit(hk.get(key, ""))
            edit.setPlaceholderText("如 ctrl+shift+a")
            hk_layout.addRow(label, edit)
            self.hk_edits[key] = edit
        tabs.addTab(tab_hk, "⌨️ 快捷键")

        # === 保存页 ===
        tab_save = QWidget()
        save_layout = QFormLayout(tab_save)

        self.dir_edit = QLineEdit(config.get("save", "output_dir", default=""))
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.dir_edit)
        dir_row.addWidget(browse_btn)
        dir_widget = QWidget()
        dir_widget.setLayout(dir_row)
        save_layout.addRow("保存目录", dir_widget)

        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["png", "jpg", "bmp"])
        self.fmt_combo.setCurrentText(config.get("save", "image_format", default="png"))
        save_layout.addRow("图片格式", self.fmt_combo)

        self.auto_copy = QCheckBox("截图后自动复制到剪贴板")
        self.auto_copy.setChecked(config.get("save", "auto_copy", default=True))
        save_layout.addRow("", self.auto_copy)

        self.auto_save = QCheckBox("截图后自动保存到目录")
        self.auto_save.setChecked(config.get("save", "auto_save", default=False))
        save_layout.addRow("", self.auto_save)

        tabs.addTab(tab_save, "💾 保存")

        # === 录屏页 ===
        tab_rec = QWidget()
        rec_layout = QFormLayout(tab_rec)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "24", "30", "60"])
        self.fps_combo.setCurrentText(str(config.get("record", "fps", default=30)))
        rec_layout.addRow("默认帧率", self.fps_combo)

        self.auto_start = QCheckBox("开机自动启动")
        self.auto_start.setChecked(config.get("general", "auto_start", default=False))
        rec_layout.addRow("", self.auto_start)

        tabs.addTab(tab_rec, "⏺ 录屏")

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if d:
            self.dir_edit.setText(d)

    def _save(self):
        # 快捷键
        for key, edit in self.hk_edits.items():
            config.set(edit.text().strip(), "hotkeys", key)
        # 保存
        config.set(self.dir_edit.text(), "save", "output_dir")
        config.set(self.fmt_combo.currentText(), "save", "image_format")
        config.set(self.auto_copy.isChecked(), "save", "auto_copy")
        config.set(self.auto_save.isChecked(), "save", "auto_save")
        # 录屏
        config.set(int(self.fps_combo.currentText()), "record", "fps")
        config.set(self.auto_start.isChecked(), "general", "auto_start")

        # 设置开机自启
        self._set_autostart(self.auto_start.isChecked())
        self.accept()

    def _set_autostart(self, enable):
        """Windows 开机自启（注册表）"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            import sys
            if enable:
                winreg.SetValueEx(key, "SnipDeck", 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try:
                    winreg.DeleteValue(key, "SnipDeck")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"设置开机自启失败: {e}")
