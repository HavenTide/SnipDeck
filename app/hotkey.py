"""全局快捷键注册"""
from pynput import keyboard
from app.config import config
from PyQt6.QtWidgets import QApplication


class HotkeyManager:
    def __init__(self):
        self.listeners = []
        self.callbacks = {}

    def register(self, hotkey_str, callback):
        """hotkey_str 格式如 'ctrl+shift+a'"""
        try:
            # 转成 pynput 需要的 KeyCombination
            parts = [p.strip().lower() for p in hotkey_str.split("+")]
            combo = keyboard.HotKey.parse(hotkey_str)
            self.callbacks[hotkey_str] = (combo, callback)
        except Exception as e:
            print(f"注册快捷键失败 {hotkey_str}: {e}")

    def start(self):
        """启动监听"""
        # 构建全局热键映射
        hotkeys = {}
        for hotkey_str, (combo, callback) in self.callbacks.items():
            hotkeys[combo] = callback

        def on_press(key):
            for combo, cb in hotkeys.items():
                # pynput HotKey 方式更可靠
                pass

        # 用更可靠的方式：维护当前按下的键集合
        self._pressed = set()

        def on_press(key):
            try:
                self._pressed.add(key)
            except Exception:
                pass
            self._check_hotkeys()

        def on_release(key):
            try:
                self._pressed.discard(key)
            except Exception:
                pass

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()

    def _check_hotkeys(self):
        """检查当前按键集合是否匹配某个热键"""
        for combo, callback in self.callbacks.values():
            # combo 是 HotKey.parse 的结果，比较麻烦，改用简单字符串匹配
            pass

    def stop(self):
        if hasattr(self, "listener"):
            self.listener.stop()


# 改用 keyboard 库更简单可靠
import keyboard as kb


class SimpleHotkeyManager:
    def __init__(self):
        self.hotkeys = {}

    def register_all(self, actions: dict):
        """actions: {'region_capture': callback, ...}"""
        hk = config.get("hotkeys", default={})
        key_map = {
            "region_capture": actions.get("region_capture"),
            "fullscreen_capture": actions.get("fullscreen_capture"),
            "window_capture": actions.get("window_capture"),
            "start_stop_record": actions.get("start_stop_record"),
            "pin_clipboard": actions.get("pin_clipboard"),
            "ocr_capture": actions.get("ocr_capture"),
        }
        for name, cb in key_map.items():
            if cb and name in hk:
                try:
                    kb.add_hotkey(hk[name], cb)
                    self.hotkeys[name] = hk[name]
                except Exception as e:
                    print(f"注册快捷键 {name} ({hk[name]}) 失败: {e}")

    def unregister_all(self):
        for hk_name in self.hotkeys.values():
            try:
                kb.remove_hotkey(hk_name)
            except Exception:
                pass
        self.hotkeys.clear()


hotkey_manager = SimpleHotkeyManager()
