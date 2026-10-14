"""SnipDeck — Windows 截屏录屏工具 主入口"""
import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt6.QtCore import QTimer, Qt
from app.config import APP_NAME, APP_VERSION
from app.tray import TrayManager
from app.hotkey import hotkey_manager
from app.capture.snipper import SnipperOverlay
from app.capture.pin import pin_clipboard_image
from app.recorder.recorder import recorder
from app.recorder.record_overlay import RecordOverlay, RecordDock
from app.ui.settings import SettingsDialog
from app.ui.history_panel import HistoryDialog


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退，留托盘

        # 全局遮罩窗口引用（避免被GC）
        self.snipper = None
        self.record_overlay = None
        self.record_dock = None
        self.settings_dlg = None
        self.history_dlg = None

        # 系统托盘
        self.tray = TrayManager(self)
        self.tray.show()

        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(None, APP_NAME, "系统托盘不可用，程序将无法最小化运行。")

        # 注册快捷键
        self._register_hotkeys()

        # 录屏信号
        recorder.tick.connect(self._on_record_tick)
        recorder.finished.connect(self._on_record_finished)
        recorder.failed.connect(self._on_record_failed)

    def _register_hotkeys(self):
        actions = {
            "region_capture": self.start_region_capture,
            "fullscreen_capture": self.start_fullscreen_capture,
            "window_capture": self.start_window_capture,
            "start_stop_record": self.toggle_record,
            "pin_clipboard": self.pin_clipboard,
            "ocr_capture": self.start_ocr_capture,
        }
        hotkey_manager.register_all(actions)

    # ============ 截图动作 ============

    def start_region_capture(self):
        if self.snipper:
            self.snipper.close()
        self.snipper = SnipperOverlay()
        self.snipper.show()
        self.snipper.activateWindow()
        self.snipper.setFocus()

    def start_fullscreen_capture(self):
        # 直接截取全屏到剪贴板
        screen = self.app.primaryScreen()
        pix = screen.grabWindow(0)
        self.app.clipboard().setPixmap(pix)
        self.tray.notify("截图完成", "全屏截图已复制到剪贴板")
        from app.history import history
        history.add("image", "(clipboard)")

    def start_window_capture(self):
        # 窗口截图 = 区域截图，简化为弹出选区
        self.start_region_capture()

    def start_ocr_capture(self):
        # 弹出选区，选完自动OCR
        self.start_region_capture()

    def pin_clipboard(self):
        win = pin_clipboard_image()
        if win:
            self.tray.notify("已贴图", "图片已钉在屏幕上，右键关闭")

    # ============ 录屏动作 ============

    def toggle_record(self):
        if recorder.recording:
            recorder.stop()
        else:
            self._start_record_selection()

    def _start_record_selection(self):
        if self.record_overlay:
            self.record_overlay.close()
        self.record_overlay = RecordOverlay()
        self.record_overlay.region_selected.connect(self._on_record_region)
        self.record_overlay.show()
        self.record_overlay.activateWindow()
        self.record_overlay.setFocus()

    def _on_record_region(self, region):
        recorder.start(region=region)
        self.record_dock = RecordDock()
        self.record_dock.stop_clicked.connect(recorder.stop)
        self.record_dock.show()

    def _on_record_tick(self, seconds):
        if self.record_dock:
            self.record_dock.set_time(seconds)

    def _on_record_finished(self, path):
        if self.record_dock:
            self.record_dock.close()
            self.record_dock = None
        self.tray.notify("录屏完成", f"已保存：{path}")

    def _on_record_failed(self, msg):
        if self.record_dock:
            self.record_dock.close()
            self.record_dock = None
        self.tray.notify("录屏失败", msg)

    # ============ 托盘回调 ============

    def on_tray_action(self, name):
        handlers = {
            "region_capture": self.start_region_capture,
            "fullscreen_capture": self.start_fullscreen_capture,
            "toggle_record": self.toggle_record,
            "pin_clipboard": self.pin_clipboard,
            "show_history": self.show_history,
            "show_settings": self.show_settings,
        }
        h = handlers.get(name)
        if h:
            h()

    def show_settings(self):
        if self.settings_dlg:
            self.settings_dlg.raise_()
            return
        self.settings_dlg = SettingsDialog()
        self.settings_dlg.finished.connect(self._on_settings_closed)
        self.settings_dlg.show()

    def _on_settings_closed(self):
        self.settings_dlg = None
        # 重新注册快捷键（用户可能改了）
        hotkey_manager.unregister_all()
        self._register_hotkeys()

    def show_history(self):
        if self.history_dlg:
            self.history_dlg.raise_()
            return
        self.history_dlg = HistoryDialog()
        self.history_dlg.finished.connect(lambda: setattr(self, "history_dlg", None))
        self.history_dlg.show()

    # ============ 运行 ============

    def run(self):
        self.tray.notify(
            f"{APP_NAME} 已启动",
            "按 Ctrl+Shift+A 开始区域截图\n点击托盘图标查看更多功能"
        )
        return self.app.exec()


def main():
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = MainApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
