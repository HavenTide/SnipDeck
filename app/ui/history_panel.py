"""历史记录面板"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFileIconProvider, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from app.history import history
from pathlib import Path
import time


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🕘 SnipDeck 历史记录")
        self.setMinimumSize(560, 440)
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: #eee; }
            QListWidget {
                background: #252525; border: 1px solid #444; border-radius: 6px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #333;
            }
            QListWidget::item:hover { background: #333; }
            QPushButton {
                background: #0078d4; border: none; border-radius: 4px;
                padding: 6px 14px; color: white;
            }
        """)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("最近的截图和录屏")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(title)

        # 列表
        self.list = QListWidget()
        self.list.setIconSize(QSize(48, 48))
        self.list.itemDoubleClicked.connect(self._open_item)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_menu)
        layout.addWidget(self.list)

        # 底部
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("清空历史")
        clear_btn.clicked.connect(self._clear)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self.list.clear()
        for item in history.recent(50):
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(item["time"]))
            type_icon = "🖼️" if item["type"] == "image" else "🎬"
            text = f"{type_icon}  {item['name']}\n     {ts}"
            li = QListWidgetItem(text)
            li.setData(Qt.ItemDataRole.UserRole, item)
            # 图片缩略图
            p = item.get("path", "")
            if item["type"] == "image" and p and Path(p).exists():
                pix = QPixmap(p)
                if not pix.isNull():
                    li.setIcon(QIcon(pix.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio)))
            self.list.addItem(li)

    def _open_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        p = data.get("path", "")
        if p and Path(p).exists() and p != "(clipboard)":
            import os
            os.startfile(p)

    def _show_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.setStyleSheet("background: #2b2b2b; color: white; padding: 4px;")

        act_open = menu.addAction("打开文件")
        act_copy = menu.addAction("复制路径")
        menu.addSeparator()
        act_del = menu.addAction("从历史删除")

        chosen = menu.exec(self.list.viewport().mapToGlobal(pos))
        if chosen == act_open:
            self._open_item(item)
        elif chosen == act_copy:
            QApplication.clipboard().setText(data.get("path", ""))
        elif chosen == act_del:
            history.items = [h for h in history.items if h != data]
            history._save()
            self._refresh()

    def _clear(self):
        history.clear()
        self._refresh()
