"""全局快捷键注册（基于 keyboard 库）"""
import keyboard as kb
from app.config import config


class SimpleHotkeyManager:
    def __init__(self):
        self.hotkeys = {}

    def register_all(self, actions: dict):
        """actions: {'region_capture': callback, ...}"""
        hk = config.get("hotkeys", default={})
        for name, cb in actions.items():
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
