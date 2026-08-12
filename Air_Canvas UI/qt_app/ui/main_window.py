"""
ui/main_window.py
Root application window — wires the camera worker, drawing engine,
toolbar, color picker, layers panel, brush slider, and status bar together.
"""
import os, sys
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGraphicsDropShadowEffect, QMessageBox, QGraphicsBlurEffect,
    QPushButton
)
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer
import time

# ---- Project root so air_canvas_pro is importable ----
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.drawing_engine import DrawingEngine
from core.hand_tracking import HandTracker
from ui.widgets.camera_worker import CameraWorker
from ui.widgets.canvas_widget import CanvasWidget
from ui.toolbar import TopToolbar
from ui.color_picker import RadialColorPicker
from ui.layers_panel import LayersPanel
from ui.brush_slider import BrushSlider
from ui.status_bar import StatusBar


# Tool name mapping: Qt toolbar key → DrawingEngine tool name
_TOOL_MAP = {
    "pencil":      "pencil",
    "eraser":      "eraser",
    "crayon":      "crayon",
    "spray":       "spray",
    "shapes":      "shapes",
    "color_wheel": None,   # handled separately
    "brush_size":  None,   # no-op; slider handles this
    "undo":        None,
    "redo":        None,
    "save":        None,
    "clear":       None,
    "convert_3d":  None,
    "settings":    None,
}

CANVAS_W, CANVAS_H = 1280, 720


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Air Canvas Pro")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #0F1117;")

        # ---- Core engine ----
        self._engine = DrawingEngine(CANVAS_W, CANVAS_H, _ROOT)

        # ---- Build UI ----
        self._build_ui()
        self._connect_signals()

        # ---- Start camera / tracking thread ----
        self._start_tracking()

    # ==================================================================
    # UI Construction
    # ==================================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Outer layout: toolbar row on top, camera+side panels below
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── TOP TOOLBAR (floating glass panel) ──────────────────────
        self.toolbar = TopToolbar()
        self.toolbar.setObjectName("glassPanel")
        # Ensure toolbar uses the glassPanel style
        self.toolbar.setStyleSheet("")
        _shadow(self.toolbar, blur=20, offset=(0, 4))
        
        toolbar_container = QHBoxLayout()
        toolbar_container.setContentsMargins(32, 16, 32, 16)
        toolbar_container.addStretch(1)
        toolbar_container.addWidget(self.toolbar)
        toolbar_container.addStretch(1)
        outer.addLayout(toolbar_container)

        # ── BODY: camera canvas + right sidebar ─────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #080B12;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Canvas fills the left/center area
        self.canvas_widget = CanvasWidget()
        body_layout.addWidget(self.canvas_widget, stretch=1)

        # Collapse button
        self.collapse_btn = QPushButton(">")
        self.collapse_btn.setFixedSize(20, 60)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(18,24,34,0.82);
                border: 1px solid rgba(255,255,255,0.12);
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                border-right: none;
                color: #00E5FF;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 229, 255, 0.15);
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_sidebar)
        
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        btn_layout.addWidget(self.collapse_btn)
        btn_layout.addStretch()

        body_layout.addLayout(btn_layout)

        # Right sidebar: Layers + Brush Slider
        self.right_panel = QWidget()
        self.right_panel.setMaximumWidth(240)
        self.right_panel.setStyleSheet("background: rgba(10,13,20,0.95); border-left: 1px solid rgba(255,255,255,0.08);")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(12, 16, 12, 16)
        right_layout.setSpacing(16)

        self.layers = LayersPanel()
        _shadow(self.layers)
        right_layout.addWidget(self.layers)

        self.brush_slider = BrushSlider()
        _shadow(self.brush_slider)
        right_layout.addWidget(self.brush_slider)
        right_layout.addStretch()

        body_layout.addWidget(self.right_panel)
        outer.addWidget(body, stretch=1)

        # STATUS BAR
        self.status = StatusBar(self)
        self.setStatusBar(self.status)

        # FLOATING COLOR PICKER (hidden by default)
        self.color_picker = RadialColorPicker(self)
        self.color_picker.hide()

    # ==================================================================
    # Signal wiring
    # ==================================================================
    def _connect_signals(self):
        # Toolbar buttons
        for key, btn in self.toolbar.buttons.items():
            btn.clicked.connect(lambda checked, k=key: self._on_tool_clicked(k))

        # Brush slider
        self.brush_slider.slider.valueChanged.connect(self._on_brush_changed)
        
        # Color picker
        self.color_picker.color_selected.connect(self._apply_color)

        # Status bar reflects initial state
        self.status.update_tool("Pencil")
        self.status.update_size(self._engine.brush_size)

    # ==================================================================
    # Camera / tracking
    # ==================================================================
    def _start_tracking(self):
        model_path = os.path.join(_ROOT, 'hand_landmarker.task')
        try:
            tracker = HandTracker(model_path)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Model Missing", str(e))
            return

        self._worker = CameraWorker(tracker, CANVAS_W, CANVAS_H)
        self._worker.frame_ready.connect(self._on_frame)
        self._worker.fps_updated.connect(self.status.update_fps)
        self._worker.tracking_changed.connect(self.status.update_tracking)
        self._worker.camera_status_changed.connect(self.status.update_camera)
        self._worker.start()

    # ==================================================================
    # Per-frame callback (main thread, signal-slot)
    # ==================================================================
    def _on_frame(self, cam_frame, lmList, is_drawing, is_selecting,
                  x1: float, y1: float):
        try:
            effective_drawing = is_drawing and not self.color_picker.isVisible()

            if lmList:
                now = time.time()
                if now - getattr(self, '_last_print_time', 0) > 1.0:
                    print(f"[HAND] Fingertip: {x1}, {y1}")
                    if effective_drawing:
                        print(f"[DRAW] Drawing at {x1}, {y1}")
                    self._last_print_time = now

            self._engine.update(x1, y1, effective_drawing, cam_frame)

            # Refresh canvas widget
            self.canvas_widget.update_frame(
                cam_frame, self._engine.get_layer(),
                lmList, is_drawing, is_selecting, x1, y1)
        except Exception:
            import traceback, os as _os
            err = traceback.format_exc()
            print(f"[FRAME ERROR]\n{err}")
            log_path = _os.path.join(_os.path.dirname(__file__), '..', 'qt_error.log')
            with open(log_path, 'a') as f:
                f.write(err + '\n')

    # ==================================================================
    # Toolbar actions
    # ==================================================================
    def _on_tool_clicked(self, key: str):
        if key in ("pencil", "eraser", "crayon", "spray", "shapes"):
            self._engine.set_tool(key)
            self.status.update_tool(key.capitalize())
            print(f"[TOOL] {key.capitalize()} selected")

        elif key == "color_wheel":
            self._toggle_color_picker()

        elif key == "undo":
            self._engine.undo()
            self.status.notify("Undo")
            print("[UNDO] Undo")

        elif key == "redo":
            self._engine.redo()
            self.status.notify("Redo")
            print("[REDO] Redo")

        elif key == "save":
            path = self._engine.save()
            self.status.notify(f"Saved: {os.path.basename(path)}")
            print("[SAVE] Drawing saved")

        elif key == "clear":
            self._engine.clear()
            self.status.notify("Canvas Cleared")
            print("[CLEAR] Canvas cleared")

        elif key == "convert_3d":
            result = self._engine.export_3d(_ROOT)
            if result:
                self.status.notify("3D Export: viewer opened")
                print("[3D] Viewer opened")
            else:
                self.status.notify("3D Export: nothing to export")

    # ==================================================================
    # Color picker
    # ==================================================================
    def _toggle_color_picker(self):
        if self.color_picker.isHidden():
            btn = self.toolbar.buttons.get("color_wheel")
            if btn:
                pos = btn.mapTo(self, btn.rect().center())
                self.color_picker.move(
                    pos.x() - self.color_picker.width() // 2,
                    pos.y() + 20)
            self.color_picker.show()
            self.color_picker.raise_()
        else:
            self.color_picker.hide()

    def _apply_color(self, qt_color: QColor):
        bgr = (qt_color.blue(), qt_color.green(), qt_color.red())
        self._engine.set_color_bgr(bgr)
        self.canvas_widget.set_active_color(bgr)
        
        # Update color dot on toolbar
        for w in self.toolbar.findChildren(QWidget):
            if hasattr(w, 'set_color_indicator') and getattr(w, 'lbl', None) and w.lbl.text() == "Color":
                w.set_color_indicator(qt_color.name())
                
        print(f"[TOOL] Color changed to {bgr}")

    # ==================================================================
    # Right Sidebar Toggle
    # ==================================================================
    def _toggle_sidebar(self):
        if self.right_panel.isVisible():
            self.right_panel.hide()
            self.collapse_btn.setText("<")
        else:
            self.right_panel.show()
            self.collapse_btn.setText(">")

    # ==================================================================
    # Brush slider
    # ==================================================================
    def _on_brush_changed(self, value: int):
        self._engine.set_brush_size(value)
        self.status.update_size(value)

    # ==================================================================
    # Cleanup on close
    # ==================================================================
    def closeEvent(self, event):
        if hasattr(self, '_worker'):
            self._worker.stop()
            self._worker.wait(2000)
        super().closeEvent(event)


# ------------------------------------------------------------------
def _shadow(widget: QWidget, blur: int = 40, offset=(0, 10)):
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setColor(QColor(0, 0, 0, 120))
    fx.setOffset(*offset)
    widget.setGraphicsEffect(fx)

def _blur(widget: QWidget):
    """Note: True background blur behind transparent widgets is complex in PyQt6 without 
    native OS calls, so we rely on the QSS translucency to give the glass feel over the canvas."""
    pass
