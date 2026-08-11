"""
core/drawing_engine.py
All drawing logic isolated here — no UI knowledge.
Receives gestures and mutates the numpy drawing layer.
"""
import cv2
import numpy as np
import random

from air_canvas_pro.core.canvas_manager import CanvasManager
from air_canvas_pro.core.shape_ai import ShapeAI
from air_canvas_pro.utils.export_engine import ExportEngine


class DrawingEngine:
    # BGR colours for the engine
    CYAN = (255, 229, 0)

    def __init__(self, width: int, height: int, base_dir: str):
        self.width = width
        self.height = height
        self.canvas = CanvasManager(width, height)
        self.shape_ai = ShapeAI()
        self.exporter = ExportEngine(base_dir)

        # Drawing state
        self.active_tool: str = "pencil"
        self.color: tuple = self.CYAN          # BGR
        self.brush_size: int = 10
        self.eraser_size: int = 40
        self._xp: int = 0
        self._yp: int = 0

    # ------------------------------------------------------------------ tool
    def set_tool(self, tool: str):
        self.active_tool = tool

    def set_color_bgr(self, bgr: tuple):
        self.color = bgr

    def set_brush_size(self, size: int):
        self.brush_size = max(1, size)

    # ------------------------------------------------------------ main update
    def update(self, x: int, y: int, is_drawing: bool, img_display=None):
        """
        Called every frame with the filtered fingertip position.
        img_display is the combined frame (for shape preview overlay only).
        Returns the current drawing_layer (numpy array).
        """
        tool = self.active_tool

        if not is_drawing:
            # Lift-pen: commit shapes, reset prev point
            if tool == "shapes" and (self._xp or self._yp):
                self.shape_ai.process_stroke(self.canvas.drawing_layer,
                                             self.color, self.brush_size)
            self._xp, self._yp = 0, 0
            return self.canvas.drawing_layer

        # ---- drawing is active ----
        if tool == "pencil":
            if self._xp or self._yp:
                cv2.line(self.canvas.drawing_layer,
                         (self._xp, self._yp), (x, y),
                         self.color, self.brush_size, cv2.LINE_AA)
            else:
                self.canvas.snapshot()
            self._xp, self._yp = x, y

        elif tool == "eraser":
            if self._xp or self._yp:
                cv2.line(self.canvas.drawing_layer,
                         (self._xp, self._yp), (x, y),
                         (0, 0, 0), self.eraser_size)
            else:
                self.canvas.snapshot()
            self._xp, self._yp = x, y

        elif tool == "spray":
            if not (self._xp or self._yp):
                self.canvas.snapshot()
            for _ in range(18):
                ox = random.randint(-self.brush_size, self.brush_size)
                oy = random.randint(-self.brush_size, self.brush_size)
                sx, sy = x + ox, y + oy
                if 0 <= sx < self.width and 0 <= sy < self.height:
                    cv2.circle(self.canvas.drawing_layer, (sx, sy), 1,
                               self.color, -1)
            self._xp, self._yp = x, y

        elif tool == "crayon":
            if not (self._xp or self._yp):
                self.canvas.snapshot()
            if self._xp or self._yp:
                for _ in range(4):
                    jx1 = self._xp + random.randint(-3, 3)
                    jy1 = self._yp + random.randint(-3, 3)
                    jx2 = x + random.randint(-3, 3)
                    jy2 = y + random.randint(-3, 3)
                    cv2.line(self.canvas.drawing_layer,
                             (jx1, jy1), (jx2, jy2),
                             self.color, max(1, self.brush_size // 2))
            self._xp, self._yp = x, y

        elif tool == "shapes":
            if not (self._xp or self._yp):
                self.canvas.snapshot()
                self.shape_ai.reset()
            self.shape_ai.add_point((x, y))
            # Preview overlay
            if img_display is not None and len(self.shape_ai.current_stroke) > 1:
                pts = np.array(self.shape_ai.current_stroke, np.int32)\
                              .reshape((-1, 1, 2))
                cv2.polylines(img_display, [pts], False,
                              self.color, self.brush_size)
            self._xp, self._yp = x, y

        return self.canvas.drawing_layer

    # ------------------------------------------------------------ commands
    def undo(self) -> bool:
        return self.canvas.undo()

    def redo(self) -> bool:
        return self.canvas.redo()

    def clear(self) -> bool:
        return self.canvas.clear()

    def save(self) -> str:
        return self.exporter.export_image(self.canvas.drawing_layer)

    def export_3d(self, base_dir: str):
        return self.exporter.export_3d(self.canvas.drawing_layer, base_dir)

    def get_layer(self) -> np.ndarray:
        return self.canvas.drawing_layer
