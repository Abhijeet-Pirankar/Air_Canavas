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

        # Keep previous point as float for sub-pixel accuracy
        self._xp: float = 0.0
        self._yp: float = 0.0

        # --- INTERPOLATION CONFIG ---
        # Draw an intermediate point every N pixels of movement.
        # Lower = smoother (but more CPU). 4.0 is a good balance.
        self.INTERPOLATION_DISTANCE: float = 4.0

    # ------------------------------------------------------------------ tool
    def set_tool(self, tool: str):
        self.active_tool = tool

    def set_color_bgr(self, bgr: tuple):
        self.color = bgr

    def set_brush_size(self, size: int):
        self.brush_size = max(1, size)

    # ------------------------------------------------------------ main update
    def update(self, x: float, y: float, is_drawing: bool, img_display=None):
        """
        Called every frame with the smoothed float fingertip position.
        Internally interpolates movement for gap-free continuous drawing.
        Only casts to int at the cv2 drawing call boundary.
        """
        tool = self.active_tool

        if not is_drawing:
            # Lift-pen: commit shapes, reset prev point
            if tool == "shapes" and (self._xp or self._yp):
                self.shape_ai.process_stroke(self.canvas.drawing_layer,
                                             self.color, self.brush_size)
            self._xp, self._yp = 0.0, 0.0
            return self.canvas.drawing_layer

        # ---- drawing is active ----
        has_prev = bool(self._xp or self._yp)

        if not has_prev:
            # Start of a new stroke — take a snapshot for undo
            self.canvas.snapshot()
            self._xp, self._yp = x, y
            return self.canvas.drawing_layer

        # Compute distance and generate interpolated steps
        dx = x - self._xp
        dy = y - self._yp
        dist = (dx * dx + dy * dy) ** 0.5

        # Number of intermediate steps — more steps for fast movements
        steps = max(1, int(dist / self.INTERPOLATION_DISTANCE))

        for i in range(1, steps + 1):
            t = i / steps
            ix = self._xp + dx * t
            iy = self._yp + dy * t

            # Integer pixel coords for cv2 calls
            ix_i = int(round(ix))
            iy_i = int(round(iy))
            pxi  = int(round(self._xp + dx * (i - 1) / steps))
            pyi  = int(round(self._yp + dy * (i - 1) / steps))

            if tool == "pencil":
                cv2.line(self.canvas.drawing_layer,
                         (pxi, pyi), (ix_i, iy_i),
                         self.color, self.brush_size, cv2.LINE_AA)

            elif tool == "eraser":
                cv2.line(self.canvas.drawing_layer,
                         (pxi, pyi), (ix_i, iy_i),
                         (0, 0, 0), self.eraser_size)

            elif tool == "spray":
                for _ in range(max(2, 18 // steps)):
                    ox = random.randint(-self.brush_size, self.brush_size)
                    oy = random.randint(-self.brush_size, self.brush_size)
                    sx, sy = ix_i + ox, iy_i + oy
                    if 0 <= sx < self.width and 0 <= sy < self.height:
                        cv2.circle(self.canvas.drawing_layer, (sx, sy), 1,
                                   self.color, -1)

            elif tool == "crayon":
                for _ in range(max(1, 4 // steps)):
                    jx1 = pxi + random.randint(-3, 3)
                    jy1 = pyi + random.randint(-3, 3)
                    jx2 = ix_i + random.randint(-3, 3)
                    jy2 = iy_i + random.randint(-3, 3)
                    cv2.line(self.canvas.drawing_layer,
                             (jx1, jy1), (jx2, jy2),
                             self.color, max(1, self.brush_size // 2))

            elif tool == "shapes":
                self.shape_ai.add_point((ix_i, iy_i))
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
