import numpy as np
import cv2

class UndoRedoManager:
    """Snapshot-based undo/redo with a history stack."""
    def __init__(self, max_states=50):
        self.undo_stack = []
        self.redo_stack = []
        self.max_states = max_states

    def snapshot(self, layer):
        self.undo_stack.append(layer.copy())
        if len(self.undo_stack) > self.max_states:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, layer):
        if self.undo_stack:
            self.redo_stack.append(layer.copy())
            return self.undo_stack.pop()
        return layer

    def redo(self, layer):
        if self.redo_stack:
            self.undo_stack.append(layer.copy())
            return self.redo_stack.pop()
        return layer

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0


class CanvasManager:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.drawing_layer = np.zeros((height, width, 3), np.uint8)
        self.undo_mgr = UndoRedoManager()
        self.zoom = 1.0
        self.zoom_min, self.zoom_max = 0.6, 2.5
        self.show_grid = False

    def clear(self):
        if np.any(self.drawing_layer):
            self.undo_mgr.snapshot(self.drawing_layer)
            self.drawing_layer[:] = 0
            return True
        return False

    def undo(self):
        if self.undo_mgr.can_undo():
            self.drawing_layer = self.undo_mgr.undo(self.drawing_layer)
            return True
        return False

    def redo(self):
        if self.undo_mgr.can_redo():
            self.drawing_layer = self.undo_mgr.redo(self.drawing_layer)
            return True
        return False

    def snapshot(self):
        self.undo_mgr.snapshot(self.drawing_layer)

    def draw_grid(self, frame):
        """Draws a subtle dot grid for infinite canvas feel."""
        if not self.show_grid:
            return
        
        spacing = 40
        dot_color = (220, 220, 220)
        for x in range(0, self.width, spacing):
            for y in range(0, self.height, spacing):
                cv2.circle(frame, (x, y), 1, dot_color, -1)

    def get_zoom_view(self):
        """Returns the zoomed and cropped version of the drawing layer."""
        h, w = self.height, self.width
        new_w = int(w / self.zoom)
        new_h = int(h / self.zoom)
        cx, cy = w // 2, h // 2
        x_start = max(0, cx - new_w // 2)
        y_start = max(0, cy - new_h // 2)
        x_end = min(w, x_start + new_w)
        y_end = min(h, y_start + new_h)
        cropped = self.drawing_layer[y_start:y_end, x_start:x_end]
        zoomed = cv2.resize(cropped, (w, h))
        return zoomed, x_start, y_start, new_w, new_h

    def map_to_canvas(self, x, y, x_start, y_start, new_w, new_h):
        canvas_x = int(x_start + (x / self.width) * new_w)
        canvas_y = int(y_start + (y / self.height) * new_h)
        return canvas_x, canvas_y
