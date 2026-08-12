"""
ui/widgets/canvas_widget.py
QLabel subclass that composites the camera feed + drawing layer
and overlays the hand cursor — all in the main thread.
"""
import time
import math
import numpy as np
import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


def _bgr_to_qpixmap(frame: np.ndarray) -> QPixmap:
    h, w, ch = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


class CanvasWidget(QLabel):
    CYAN_BGR = (255, 229, 0)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #0D0F13; border-radius: 16px;")
        self.setMinimumSize(640, 360)

        self._cursor_pos = None
        self._is_selecting = False
        self._active_color = self.CYAN_BGR

    def set_active_color(self, bgr: tuple):
        self._active_color = bgr

    def update_frame(self, cam_frame: np.ndarray,
                     drawing_layer: np.ndarray,
                     lmList: list, is_drawing: bool,
                     is_selecting: bool, x1: float, y1: float):
        """Composite camera + drawing layer, draw cursor, push to QPixmap."""
        # Convert float fingertip coords to int only for OpenCV rendering
        cx, cy = int(round(x1)), int(round(y1))
        # Print a debug log occasionally
        if not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        if self._debug_counter % 30 == 0:
            print("[DEBUG] CanvasWidget: Received frame and updating QPixmap.")
        self._debug_counter += 1

        display = cam_frame.copy()

        # ---- Premium Styling: Vignette ----
        h, w = display.shape[:2]
        if not hasattr(self, '_vignette') or self._vignette.shape[:2] != (h, w):
            X = cv2.getGaussianKernel(w, w/2)
            Y = cv2.getGaussianKernel(h, h/2)
            kernel = Y * X.T
            mask_v = kernel / kernel.max()
            # Fade edges to 60% brightness
            self._vignette = (mask_v * 0.4 + 0.6).astype(np.float32)
            self._vignette = np.stack([self._vignette]*3, axis=2)
            
        display = (display * self._vignette).astype(np.uint8)

        # ---- Overlay drawing layer (with Neon Glow) ----
        mask = cv2.cvtColor(drawing_layer, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        if np.any(mask):
            # Create glow blur
            glow = cv2.GaussianBlur(drawing_layer, (15, 15), 0)
            # Additive blend for neon effect
            display = cv2.addWeighted(display, 1.0, glow, 0.8, 0)
            # Overlay sharp core lines
            display[mask == 255] = drawing_layer[mask == 255]

        # ---- Draw cursor ----
        if lmList:
            cyan_color = (255, 229, 0)   # BGR: 0x00E5FF
            color = (255, 255, 255) if is_selecting else cyan_color

            # Outer glow rings — concentric circles at decreasing opacity
            cv2.circle(display, (cx, cy), 14, (100, 90, 0),  1)
            cv2.circle(display, (cx, cy), 10, (200, 180, 0), 2)
            # Solid core
            cv2.circle(display, (cx, cy),  6, color,         -1)

            if is_selecting:
                pulse_r = 16 + int(5 * math.sin(time.time() * 10))
                cv2.circle(display, (cx, cy), pulse_r, (255, 255, 255), 2)

        # ---- Premium Styling: Rounded Corners Mask ----
        if not hasattr(self, '_corner_mask') or self._corner_mask.shape[:2] != (h, w):
            r = 24  # Corner radius
            mask_c = np.zeros((h, w), dtype=np.uint8)
            cv2.rectangle(mask_c, (r, 0), (w - r, h), 255, -1)
            cv2.rectangle(mask_c, (0, r), (w, h - r), 255, -1)
            cv2.circle(mask_c, (r, r), r, 255, -1)
            cv2.circle(mask_c, (w - r, r), r, 255, -1)
            cv2.circle(mask_c, (r, h - r), r, 255, -1)
            cv2.circle(mask_c, (w - r, h - r), r, 255, -1)
            self._corner_mask = mask_c
            
        # Make outside of mask match the main window background (#080B12 -> BGR: 18, 11, 8)
        display[self._corner_mask == 0] = (18, 11, 8)

        self.setPixmap(_bgr_to_qpixmap(display).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
