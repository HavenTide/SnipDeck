"""SnipDeck 全局配置管理"""
import json
import os
from pathlib import Path

APP_NAME = "SnipDeck"
APP_VERSION = "0.1.0"

# 用户数据目录
USER_HOME = Path(os.environ.get("APPDATA", Path.home()))
CONFIG_DIR = USER_HOME / APP_NAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path.home() / "Pictures" / APP_NAME
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = CONFIG_DIR / "history.json"


DEFAULT_CONFIG = {
    "hotkeys": {
        "region_capture": "ctrl+shift+a",
        "fullscreen_capture": "ctrl+shift+b",
        "window_capture": "ctrl+shift+w",
        "start_stop_record": "ctrl+shift+r",
        "pin_clipboard": "ctrl+shift+t",
        "ocr_capture": "ctrl+shift+o",
    },
    "save": {
        "output_dir": str(DEFAULT_OUTPUT_DIR),
        "image_format": "png",
        "video_format": "mp4",
        "auto_copy": True,
        "auto_save": False,
    },
    "record": {
        "fps": 30,
        "include_audio": True,
        "include_mic": False,
        "cursor_highlight": True,
    },
    "capture": {
        "show_magnifier": True,
        "show_ruler": True,
        "shadow_effect": True,
    },
    "general": {
        "auto_start": False,
        "minimize_to_tray": True,
        "theme": "dark",
    },
}


class Config:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # 合并默认配置，防止新增字段缺失
                merged = self._deep_merge(DEFAULT_CONFIG.copy(), saved)
                return merged
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _deep_merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, *keys, default=None):
        node = self.data
        for k in keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                return default
        return node

    def set(self, value, *keys):
        node = self.data
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value
        self.save()


config = Config()
