"""选区截图遮罩窗口 — 全屏变暗、拖拽选区、放大镜、标注工具栏"""
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMenu, QColorDialog, QFontDialog,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QRect, QPoint, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPixmap, QImage, QCursor, QPainterPath,
    QPolygon, QFont, QMouseEvent, QKeyEvent, QGuiApplication, QAction
)
import mss
import numpy as np
from PIL import Image
from app.config import config, DEFAULT_OUTPUT_DIR
from app.history import history
from app.capture.annotate_toolbar import AnnotateToolbar


class SnipperOverlay(QWidget):
    """全屏截图选区遮罩"""

    capture_done = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # 截取整个虚拟桌面（所有显示器）
        screen = QApplication.primaryScreen()
        geo = screen.virtualGeometry()
        self.setGeometry(geo)

        # 截取全屏作为背景图
        self.full_pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())

        # 选区状态
        self.origin = QPoint()
        self.current = QPoint()
        self.selecting = False
        self.selection_rect = QRect()

        # 放大镜
        self.magnifier_size = 120
        self.magnifier_zoom = 3

        # 标注图层（在选区之上绘制）
        self.annotations = []  # list of dict: {tool, points, color, width, text, ...}
        self.current_annotation = None
        self.active_tool = None  # rect / ellipse / arrow / pen / text / mosaic / eraser
        self.pen_color = QColor(255, 59, 48)  # 默认红色
        self.pen_width = 2

        # 工具栏
        self.toolbar = None
        self.annotated_pixmap = None  # 标注完成后的图

        # 马赛克块大小
        self.mosaic_block = 12

        # 标注图层缓存
        self._current_pix = None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            self.capture_done.emit(QPixmap())
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.finish_capture()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.annotations:
                self.annotations.pop()
                self.update()
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果已经有选区，且点击在选区内部 —— 开始画标注
            if not self.selection_rect.isNull() and self.selection_rect.contains(event.pos()):
                if self.active_tool:
                    self._start_annotation(event.pos())
                return
            # 否则开始新选区
            self.origin = event.pos()
            self.current = event.pos()
            self.selecting = True
            self.selection_rect = QRect()
            self.annotations = []
            self._hide_toolbar()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.current = event.pos()
        if self.selecting:
            self.selection_rect = QRect(self.origin, self.current).normalized()
        elif self.current_annotation is not None:
            self._update_annotation(event.pos())
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.selecting:
                self.selecting = False
                self.selection_rect = QRect(self.origin, self.current).normalized()
                if self.selection_rect.width() < 5 or self.selection_rect.height() < 5:
                    self.selection_rect = QRect()
                    self.update()
                    return
                # 弹出工具栏
                self._show_toolbar()
            elif self.current_annotation is not None:
                self._end_annotation()
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键退出
            self.close()
            self.capture_done.emit(QPixmap())

    def _start_annotation(self, pos):
        rel = pos - self.selection_rect.topLeft()
        if self.active_tool == "text":
            text, ok = QInputDialog.getText(self, "输入文字", "文字内容:")
            if ok and text:
                self.annotations.append({
                    "tool": "text", "pos": rel, "text": text,
                    "color": self.pen_color, "width": self.pen_width
                })
                self.update()
            return
        self.current_annotation = {
            "tool": self.active_tool,
            "points": [rel],
            "color": self.pen_color,
            "width": self.pen_width,
        }
        if self.active_tool == "mosaic":
            self.current_annotation["points"] = [rel]

    def _update_annotation(self, pos):
        rel = pos - self.selection_rect.topLeft()
        if self.active_tool in ("rect", "ellipse", "arrow"):
            self.current_annotation["points"] = [
                self.current_annotation["points"][0], rel
            ]
        elif self.active_tool in ("pen", "eraser", "mosaic"):
            self.current_annotation["points"].append(rel)

    def _end_annotation(self):
        if self.current_annotation and self.current_annotation["points"]:
            self.annotations.append(self.current_annotation)
        self.current_annotation = None
        self.update()

    def _show_toolbar(self):
        self._hide_toolbar()
        self.toolbar = AnnotateToolbar(self)
        # 定位到选区下方居中
        tw = self.toolbar.sizeHint().width()
        x = self.selection_rect.center().x() - tw // 2
        y = self.selection_rect.bottom() + 8
        # 防止超出屏幕
        x = max(0, min(x, self.width() - tw))
        if y + self.toolbar.sizeHint().height() > self.height():
            y = self.selection_rect.top() - self.toolbar.sizeHint().height() - 8
        self.toolbar.move(x, y)
        self.toolbar.tool_selected.connect(self._on_tool_selected)
        self.toolbar.color_changed.connect(self._on_color_changed)
        self.toolbar.width_changed.connect(self._on_width_changed)
        self.toolbar.copy_requested.connect(self._copy_to_clipboard)
        self.toolbar.save_requested.connect(self._save_to_file)
        self.toolbar.ocr_requested.connect(self._run_ocr)
        self.toolbar.cancel_requested.connect(self.close)
        self.toolbar.show()

    def _hide_toolbar(self):
        if self.toolbar:
            self.toolbar.hide()
            self.toolbar = None

    def _on_tool_selected(self, tool):
        self.active_tool = tool

    def _on_color_changed(self, color):
        self.pen_color = color

    def _on_width_changed(self, w):
        self.pen_width = w

    def _capture_selection(self) -> QPixmap:
        """根据选区生成最终图片（含标注）"""
        if self.selection_rect.isNull():
            return QPixmap()
        rect = self.selection_rect
        pix = self.full_pixmap.copy(rect)
        if self.annotations:
            painter = QPainter(pix)
            self._draw_annotations(painter, QPoint(0, 0))
            painter.end()
        return pix

    def _draw_annotations(self, painter, offset):
        for ann in self.annotations:
            tool = ann["tool"]
            color = ann["color"]
            w = ann["width"]
            pts = ann["points"]
            pen = QPen(color, w)
            painter.setPen(pen)

            if tool == "rect" and len(pts) >= 2:
                r = QRect(pts[0], pts[1]).normalized()
                painter.drawRect(r)
            elif tool == "ellipse" and len(pts) >= 2:
                r = QRect(pts[0], pts[1]).normalized()
                painter.drawEllipse(r)
            elif tool == "arrow" and len(pts) >= 2:
                p1, p2 = pts[0], pts[1]
                painter.drawLine(p1, p2)
                # 箭头头部
                import math
                angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                arrow_len = 12
                a1 = angle + math.radians(150)
                a2 = angle - math.radians(150)
                h1 = QPoint(
                    int(p2.x() + arrow_len * math.cos(a1)),
                    int(p2.y() + arrow_len * math.sin(a1))
                )
                h2 = QPoint(
                    int(p2.x() + arrow_len * math.cos(a2)),
                    int(p2.y() + arrow_len * math.sin(a2))
                )
                painter.drawLine(p2, h1)
                painter.drawLine(p2, h2)
            elif tool == "pen" and len(pts) >= 2:
                painter.drawPoly(QPolygon(pts))
            elif tool == "eraser" and len(pts) >= 2:
                pen.setColor(QColor(0, 0, 0, 0))
                pen.setWidth(w * 3)
                painter.setPen(pen)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.drawPoly(QPolygon(pts))
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            elif tool == "text":
                font = QFont("Microsoft YaHei", ann.get("width", 2) * 4 + 8)
                painter.setFont(font)
                painter.drawText(ann["pos"], ann.get("text", ""))
            elif tool == "mosaic" and len(pts) >= 2:
                # 对每个点周围做马赛克
                for p in pts:
                    bx = p.x() - self.mosaic_block
                    by = p.y() - self.mosaic_block
                    block = QRect(bx, by, self.mosaic_block * 2, self.mosaic_block * 2)
                    painter.fillRect(block, QColor(180, 180, 180, 200))

    def paintEvent(self, event):
        painter = QPainter(self)
        # 绘制全屏截图
        painter.drawPixmap(0, 0, self.full_pixmap)

        # 遮罩：选区外变暗
        if not self.selection_rect.isNull():
            # 选区外半透明黑
            dim = QColor(0, 0, 0, 120)
            r = self.selection_rect
            # 上
            painter.fillRect(0, 0, self.width(), r.top(), dim)
            # 下
            painter.fillRect(0, r.bottom() + 1, self.width(), self.height() - r.bottom() - 1, dim)
            # 左
            painter.fillRect(0, r.top(), r.left(), r.height(), dim)
            # 右
            painter.fillRect(r.right() + 1, r.top(), self.width() - r.right() - 1, r.height(), dim)
            # 选区边框
            painter.setPen(QPen(QColor(0, 120, 255), 2))
            painter.drawRect(r)
            # 尺寸标签
            size_text = f"{r.width()} × {r.height()}"
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont("Microsoft YaHei", 9)
            painter.setFont(font)
            tw = painter.fontMetrics().horizontalAdvance(size_text)
            label_rect = QRect(r.center().x() - tw // 2 - 6, r.top() - 24, tw + 12, 20)
            painter.fillRect(label_rect, QColor(0, 120, 255))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, size_text)
        else:
            # 没选区，全变暗
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # 绘制标注（在选区坐标系内）
        if not self.selection_rect.isNull():
            painter.save()
            painter.translate(self.selection_rect.topLeft())
            self._current_pix = self.full_pixmap.copy(self.selection_rect)
            self._draw_annotations(painter, QPoint(0, 0))
            if self.current_annotation:
                # 实时绘制当前正在画的
                temp = self.annotations + [self.current_annotation]
                # 已经在_draw_annotations里处理了，这里不需要
                pass
            painter.restore()

        # 放大镜
        if config.get("capture", "show_magnifier", default=True):
            self._draw_magnifier(painter)

    def _draw_magnifier(self, painter):
        pos = self.current
        # 取鼠标周围区域放大
        crop_size = 30
        src = QRect(pos.x() - crop_size // 2, pos.y() - crop_size // 2, crop_size, crop_size)
        # 放大镜位置：鼠标右下
        mg_x = pos.x() + 20
        mg_y = pos.y() + 20
        mg_size = self.magnifier_size
        if mg_x + mg_size > self.width():
            mg_x = pos.x() - mg_size - 20
        if mg_y + mg_size > self.height():
            mg_y = pos.y() - mg_size - 20

        target = QRect(mg_x, mg_y, mg_size, mg_size)
        # 绘制放大内容
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawPixmap(target, self.full_pixmap, src)
        # 边框
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(target)
        # 中心十字线
        cx = mg_x + mg_size // 2
        cy = mg_y + mg_size // 2
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawLine(cx - 6, cy, cx + 6, cy)
        painter.drawLine(cx, cy - 6, cx, cy + 6)

    def _copy_to_clipboard(self):
        pix = self._capture_selection()
        if not pix.isNull():
            QApplication.clipboard().setPixmap(pix)
            from app.history import history
            history.add("image", "(clipboard)")
        self.close()
        self.capture_done.emit(pix)

    def _save_to_file(self):
        from PyQt6.QtWidgets import QFileDialog
        pix = self._capture_selection()
        if pix.isNull():
            return
        default_dir = config.get("save", "output_dir", default=str(DEFAULT_OUTPUT_DIR))
        fmt = config.get("save", "image_format", default="png")
        path, _ = QFileDialog.getSaveFileName(
            self, "保存截图", default_dir, f"图片 (*.{fmt})"
        )
        if path:
            pix.save(path)
            history.add("image", path)
        self.close()
        self.capture_done.emit(pix)

    def _run_ocr(self):
        pix = self._capture_selection()
        if pix.isNull():
            return
        # 转 numpy
        img = pix.toImage()
        bits = img.constBits()
        bits.setsize(img.height() * img.bytesPerLine())
        arr = np.frombuffer(bits, np.uint8).reshape((img.height(), img.width(), 4))
        arr = arr[:, :, :3]  # RGBA -> RGB

        QMessageBox.information(self, "OCR", "正在识别文字，请稍候...")
        try:
            import easyocr
            reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
            results = reader.readtext(arr)
            text = "\n".join([r[1] for r in results])
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "OCR 完成", f"已复制到剪贴板：\n\n{text[:500]}")
        except Exception as e:
            QMessageBox.warning(self, "OCR 失败", f"识别失败：{e}\n（首次运行需下载模型）")
        self.close()

    def finish_capture(self):
        pix = self._capture_selection()
        if pix.isNull():
            self.close()
            return
        if config.get("save", "auto_copy", default=True):
            QApplication.clipboard().setPixmap(pix)
        if config.get("save", "auto_save", default=False):
            from PyQt6.QtWidgets import QFileDialog
            default_dir = config.get("save", "output_dir", default=str(DEFAULT_OUTPUT_DIR))
            path, _ = QFileDialog.getSaveFileName(self, "保存截图", default_dir, "图片 (*.png)")
            if path:
                pix.save(path)
                history.add("image", path)
        else:
            history.add("image", "(clipboard)")
        self.close()
        self.capture_done.emit(pix)

    def closeEvent(self, event):
        self._hide_toolbar()
        super().closeEvent(event)
