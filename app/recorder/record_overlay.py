"""录屏选区窗口 + 录制浮动控制条"""
from PyQt6.QtWidgets import (
    QWidget, QApplication, QLabel, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QMouseEvent
from app.recorder.recorder import recorder


class RecordOverlay(QWidget):
    """录屏前的选区遮罩（复用截图选区逻辑，简化版）"""

    region_selected = pyqtSignal(tuple)  # (left, top, width, height)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen()
        geo = screen.virtualGeometry()
        self.setGeometry(geo)
        self.full_pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())

        self.origin = QPoint()
        self.current = QPoint()
        self.selecting = False
        self.selection_rect = QRect()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.current = event.pos()
            self.selecting = True

    def mouseMoveEvent(self, event: QMouseEvent):
        self.current = event.pos()
        if self.selecting:
            self.selection_rect = QRect(self.origin, self.current).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
            r = self.selection_rect
            if r.width() < 10 or r.height() < 10:
                # 点击全屏 = 录制整个屏幕
                screen = QApplication.primaryScreen().geometry()
                self.region_selected.emit((screen.x(), screen.y(), screen.width(), screen.height()))
            else:
                self.region_selected.emit((r.x(), r.y(), r.width(), r.height()))
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.full_pixmap)
        dim = QColor(0, 0, 0, 120)
        painter.fillRect(self.rect(), dim)
        if not self.selection_rect.isNull():
            r = self.selection_rect
            # 清除选区
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(r, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(QColor(255, 59, 48), 2))
            painter.drawRect(r)


class RecordDock(QWidget):
    """录制中浮动控制条"""
    stop_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget { background: #2b2b2b; border-radius: 20px; }
            QLabel { color: white; padding: 4px 12px; font-family: Consolas; font-size: 13px; }
            QPushButton {
                background: #ff3b30; color: white; border: none;
                border-radius: 12px; padding: 6px 14px; font-weight: bold;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #ff3b30; font-size: 14px;")
        layout.addWidget(self.dot)

        self.time_label = QLabel("00:00")
        layout.addWidget(self.time_label)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_btn)

        self.dragging = False
        self.drag_pos = QPoint()

        # 初始位置：屏幕底部居中
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center().x() - self.sizeHint().width() // 2, screen.bottom() - 80)

    def set_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        self.time_label.setText(f"{m:02d}:{s:02d}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.dragging = False
