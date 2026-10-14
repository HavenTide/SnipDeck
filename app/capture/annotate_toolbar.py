"""标注工具栏 — 浮在选区下方的工具条"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QColorDialog, QComboBox, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QPixmap, QPainter, QPen, QAction


def _make_icon(shape, color=QColor(40, 40, 40), size=20):
    """简单绘制图标"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(color, 2))
    if shape == "rect":
        p.drawRect(3, 3, size - 6, size - 6)
    elif shape == "ellipse":
        p.drawEllipse(3, 3, size - 6, size - 6)
    elif shape == "arrow":
        p.drawLine(4, size - 4, size - 4, 4)
        p.drawLine(size - 8, 4, size - 4, 4)
        p.drawLine(size - 4, 8, size - 4, 4)
    elif shape == "pen":
        p.drawLine(4, size - 4, size - 4, 4)
    elif shape == "text":
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    elif shape == "mosaic":
        for i in range(3):
            for j in range(3):
                p.fillRect(4 + i * 5, 4 + j * 5, 4, 4, QColor(150, 150, 150))
    elif shape == "eraser":
        p.drawRect(5, 5, size - 10, size - 10)
    p.end()
    return QIcon(pix)


class AnnotateToolbar(QWidget):
    tool_selected = pyqtSignal(str)   # rect / ellipse / arrow / pen / text / mosaic / eraser
    color_changed = pyqtSignal(QColor)
    width_changed = pyqtSignal(int)
    copy_requested = pyqtSignal()
    save_requested = pyqtSignal()
    ocr_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget { background: #2b2b2b; border-radius: 8px; }
            QPushButton {
                background: transparent; border: none; padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:checked { background: #0078d4; }
            QComboBox {
                background: #3b3b3b; color: white; border: none;
                padding: 4px; border-radius: 4px; min-width: 50px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # 工具按钮
        self.buttons = {}
        tools = [
            ("rect", "rect", "矩形"),
            ("ellipse", "ellipse", "椭圆"),
            ("arrow", "arrow", "箭头"),
            ("pen", "pen", "画笔"),
            ("text", "text", "文字"),
            ("mosaic", "mosaic", "马赛克"),
            ("eraser", "eraser", "橡皮"),
        ]
        for key, shape, tip in tools:
            btn = QPushButton()
            btn.setIcon(_make_icon(shape))
            btn.setIconSize(QSize(18, 18))
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._on_tool_click(k))
            layout.addWidget(btn)
            self.buttons[key] = btn

        # 分隔
        line = QLabel("|")
        line.setStyleSheet("color: #666;")
        layout.addWidget(line)

        # 颜色选择
        self.color_btn = QPushButton("颜色")
        self.color_btn.setStyleSheet("background: #ff3b30; color: white; padding: 4px 10px; border-radius: 4px;")
        self.color_btn.clicked.connect(self._pick_color)
        layout.addWidget(self.color_btn)

        # 粗细
        self.width_combo = QComboBox()
        self.width_combo.addItems(["1", "2", "3", "5"])
        self.width_combo.setCurrentText("2")
        self.width_combo.currentTextChanged.connect(lambda t: self.width_changed.emit(int(t)))
        layout.addWidget(self.width_combo)

        # 分隔
        line2 = QLabel("|")
        line2.setStyleSheet("color: #666;")
        layout.addWidget(line2)

        # OCR
        ocr_btn = QPushButton("OCR")
        ocr_btn.setStyleSheet("color: white; padding: 4px 10px;")
        ocr_btn.clicked.connect(self.ocr_requested.emit)
        layout.addWidget(ocr_btn)

        # 复制
        copy_btn = QPushButton("复制")
        copy_btn.setStyleSheet("background: #0078d4; color: white; padding: 4px 12px; border-radius: 4px;")
        copy_btn.clicked.connect(self.copy_requested.emit)
        layout.addWidget(copy_btn)

        # 保存
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("background: #107c10; color: white; padding: 4px 12px; border-radius: 4px;")
        save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(save_btn)

        # 取消
        cancel_btn = QPushButton("✕")
        cancel_btn.setStyleSheet("color: #ff6b6b; padding: 4px 8px;")
        cancel_btn.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(cancel_btn)

        self._current_tool = None

    def _on_tool_click(self, tool):
        if self._current_tool == tool:
            # 取消选中
            self.buttons[tool].setChecked(False)
            self._current_tool = None
            self.tool_selected.emit(None)
        else:
            self._current_tool = tool
            for k, btn in self.buttons.items():
                btn.setChecked(k == tool)
            self.tool_selected.emit(tool)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(255, 59, 48), self, "选择颜色")
        if color.isValid():
            self.color_btn.setStyleSheet(f"background: {color.name()}; color: white; padding: 4px 10px; border-radius: 4px;")
            self.color_changed.emit(color)
