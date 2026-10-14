"""贴图功能 — 把图片钉在屏幕上置顶"""
from PyQt6.QtWidgets import QWidget, QMenu, QApplication
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction, QCursor, QPainter, QPen


class PinWindow(QWidget):
    """置顶贴图窗口"""

    def __init__(self, pixmap: QPixmap, title="SnipDeck Pin"):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pixmap = pixmap
        self.scale = 1.0
        self.dragging = False
        self.drag_pos = QPoint()

        # 初始尺寸
        w = min(pixmap.width(), 800)
        h = int(pixmap.height() * w / pixmap.width())
        self.resize(w, h)

        # 居中偏上显示
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - w // 2,
            screen.center().y() - h // 2 - 50
        )

        self.setWindowTitle(title)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scaled = self.pixmap.scaled(
            self.size() * self.scale,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        # 居中绘制
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        # 边框
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def wheelEvent(self, event):
        # 滚轮缩放
        delta = event.angleDelta().y() / 120
        self.scale = max(0.1, min(5.0, self.scale + delta * 0.1))
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def _show_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #2b2b2b; color: white; border: 1px solid #555; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #0078d4; }
        """)

        act_copy = QAction("复制图片", self)
        act_copy.triggered.connect(lambda: QApplication.clipboard().setPixmap(self.pixmap))
        menu.addAction(act_copy)

        act_save = QAction("另存为...", self)
        act_save.triggered.connect(self._save)
        menu.addAction(act_save)

        menu.addSeparator()

        act_close = QAction("关闭", self)
        act_close.triggered.connect(self.close)
        menu.addAction(act_close)

        menu.exec(pos)

    def _save(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "保存贴图", "", "PNG 图片 (*.png)")
        if path:
            self.pixmap.save(path)


def pin_clipboard_image():
    """把剪贴板里的图片钉出来"""
    pix = QApplication.clipboard().pixmap()
    if not pix.isNull():
        win = PinWindow(pix)
        win.show()
        return win
    return None
