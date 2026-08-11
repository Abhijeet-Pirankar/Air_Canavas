from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
import math


class RadialColorPicker(QWidget):
    color_selected = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.setWindowFlags(Qt.WindowType.Popup)

        self.swatches = [
            QColor(255, 60, 60),    # Red
            QColor(255, 150, 60),   # Orange
            QColor(255, 230, 60),   # Yellow
            QColor(80, 230, 80),    # Green
            QColor(0, 229, 255),    # Cyan
            QColor(60, 100, 255),   # Blue
            QColor(191, 0, 255),    # Purple
            QColor(248, 249, 250),  # White
        ]
        self.active_color = self.swatches[4]  # Cyan default
        self.hover_idx = -1
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        ring_r = 78
        sw_r   = 22

        # Background - match the dark futuristic glassmorphism rgba(20, 25, 35, 0.65)
        painter.setBrush(QColor(20, 25, 35, 180)) 
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
        painter.drawEllipse(QRectF(cx - 108, cy - 108, 216, 216))

        # Outer swatches
        for i, color in enumerate(self.swatches):
            angle = math.radians(i * 45)  # 8 swatches, 45° each
            sx = cx + ring_r * math.cos(angle)
            sy = cy + ring_r * math.sin(angle)

            is_active = (color == self.active_color)
            is_hovered = (i == self.hover_idx)

            if is_active or is_hovered:
                glow_r = sw_r + 5
                glow_col = QColor("#00E5FF")
                glow_col.setAlpha(160 if is_active else 90)
                painter.setBrush(glow_col)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(sx-glow_r, sy-glow_r, glow_r*2, glow_r*2))

            painter.setBrush(color)
            border_col = QColor("#00E5FF") if (is_active or is_hovered) else QColor(80, 80, 80)
            painter.setPen(QPen(border_col, 2))
            painter.drawEllipse(QRectF(sx-sw_r, sy-sw_r, sw_r*2, sw_r*2))

        # Centre active color
        painter.setBrush(self.active_color)
        painter.setPen(QPen(QColor("#00E5FF"), 2))
        painter.drawEllipse(QRectF(cx-22, cy-22, 44, 44))

    def mouseMoveEvent(self, event):
        self.hover_idx = self._swatch_at(event.pos().x(), event.pos().y())
        self.update()

    def mousePressEvent(self, event):
        idx = self._swatch_at(event.pos().x(), event.pos().y())
        if idx != -1:
            self.active_color = self.swatches[idx]
            self.color_selected.emit(self.active_color)
            self.update()
            self.hide()

    def _swatch_at(self, mx, my) -> int:
        cx, cy = self.width() / 2, self.height() / 2
        ring_r, sw_r = 78, 22
        for i in range(len(self.swatches)):
            angle = math.radians(i * 45)
            sx = cx + ring_r * math.cos(angle)
            sy = cy + ring_r * math.sin(angle)
            if math.hypot(mx - sx, my - sy) < sw_r + 6:
                return i
        return -1
