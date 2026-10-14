"""截图/录屏历史记录"""
import json
import time
from pathlib import Path
from app.config import HISTORY_FILE


class History:
    MAX_ITEMS = 100

    def __init__(self):
        self.items = self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def add(self, item_type, file_path, thumbnail=None):
        """item_type: image / video / gif"""
        entry = {
            "type": item_type,
            "path": str(file_path),
            "time": time.time(),
            "name": Path(file_path).name,
        }
        self.items.insert(0, entry)
        self.items = self.items[: self.MAX_ITEMS]
        self._save()

    def _save(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

    def clear(self):
        self.items = []
        self._save()

    def recent(self, n=20):
        return self.items[:n]


history = History()
