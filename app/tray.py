"""系统托盘"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QAction
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction as QActionGui
from PyQt6.QtCore import Qt
from app.config import APP_NAME


def _make_tray_icon():
    """生成一个简单的托盘图标"""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # 蓝色圆角矩形
    p.setBrush(QColor(0, 120, 255))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(8, 8, 48, 48, 12, 12)
    # 白色相机图标（简化矩形）
    p.setBrush(QColor(255, 255, 255))
    p.drawRoundedRect(18, 24, 28, 20, 3, 3)
    p.end()
    return QIcon(pix)


class TrayManager:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.tray = QSystemTrayIcon(_make_tray_icon())
        self.tray.setToolTip(f"{APP_NAME} — 截屏录屏工具")
        self._build_menu()
        self.tray.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #2b2b2b; color: white; border: 1px solid #555; padding: 6px; }
            QMenu::item { padding: 6px 24px; border-radius: 4px; }
            QMenu::item:selected { background: #0078d4; }
            QMenu::separator { height: 1px; background: #555; margin: 4px 8px; }
        """)

        # 动作由外部注入回调
        self.actions = {}

        def add_act(name, text, callback):
            act = QAction(text, menu)
            act.triggered.connect(callback)
            menu.addAction(act)
            self.actions[name] = act
            return act

        add_act("region_capture", "📐 区域截图", self._emit("region_capture"))
        add_act("fullscreen_capture", "🖥️ 全屏截图", self._emit("fullscreen_capture"))
        add_act("record", "⏺ 开始/停止录屏", self._emit("toggle_record"))
        add_act("pin", "📌 贴图（剪贴板）", self._emit("pin_clipboard"))

        menu.addSeparator()

        add_act("history", "🕘 历史记录", self._emit("show_history"))
        add_act("settings", "⚙️ 设置", self._emit("show_settings"))

        menu.addSeparator()

        add_act("quit", "❌ 退出", QApplication.quit)

        self.tray.setContextMenu(menu)

    def _emit(self, name):
        """返回一个回调，触发 main_window 的对应方法"""
        def handler():
            if self.main_window and hasattr(self.main_window, "on_tray_action"):
                self.main_window.on_tray_action(name)
        return handler

    def _on_activated(self, reason):
        # 左键点击托盘：弹出主窗口/设置
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.main_window and hasattr(self.main_window, "on_tray_action"):
                self.main_window.on_tray_action("show_settings")

    def show(self):
        self.tray.show()

    def notify(self, title, message):
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
