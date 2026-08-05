import cv2
import time
import numpy as np
import os
from air_canvas_pro.ui.theme import Theme

class Toolbar:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.panel_h = 110 # Increased for icons + text
        self.is_visible = True
        self.last_interaction = time.time()
        
        self.tools = ["draw", "eraser", "spray", "crayon", "shapes", "undo", "redo", "clear", "save", "export_3d"]
        self.active_tool = "draw"
        
        # Animations
        self.slide_y = 0
        self.hover_idx = -1
        self.dwell_start = None
        self.DWELL_TIME = 0.8   # Snappier: 0.8s instead of 1.0s

        # Load and cache icons to prevent FPS drops
        self.icons = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_dir = os.path.join(base_dir, "assets", "icons")
        
        for t in self.tools:
            path = os.path.join(icon_dir, f"{t}.png")
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if len(img.shape) == 3 and img.shape[2] == 4:
                        img = cv2.resize(img, (34, 34))
                        self.icons[t] = img
                    elif len(img.shape) == 3 and img.shape[2] == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                        img = cv2.resize(img, (34, 34))
                        self.icons[t] = img

    def hit_test(self, x, y):
        self.last_interaction = time.time()
        if y < self.panel_h + 5:
            btn_w = self.width // len(self.tools)
            return min(max(x // btn_w, 0), len(self.tools) - 1)
        return -1

    def update(self, x, y, is_selecting):
        if is_selecting:
            idx = self.hit_test(x, y)
            if idx != -1:
                if self.hover_idx != idx:
                    self.hover_idx = idx
                    self.dwell_start = time.time()
                elif self.dwell_start and time.time() - self.dwell_start > self.DWELL_TIME:
                    selected = self.tools[idx]
                    if selected not in ["undo", "redo", "clear", "save", "export_3d"]:
                        self.active_tool = selected
                    self.dwell_start = None
                    return selected
            else:
                self.hover_idx = -1
                self.dwell_start = None
        else:
            self.hover_idx = -1
            self.dwell_start = None
            
        return None

    def draw_icon(self, frame, tool, cx, cy, color, is_active=False):
        # We shift the icon up slightly to leave space for the text label below
        if tool in self.icons:
            icon = self.icons[tool].copy()
            
            if is_active:
                # Tint icon Cyan to match the active state
                alpha_mask = icon[:, :, 3] > 0
                icon[alpha_mask, 0] = Theme.CYAN[0]
                icon[alpha_mask, 1] = Theme.CYAN[1]
                icon[alpha_mask, 2] = Theme.CYAN[2]

            h, w = icon.shape[:2]
            top, left = cy - h // 2 - 8, cx - w // 2
            
            if top >= 0 and left >= 0 and top+h <= frame.shape[0] and left+w <= frame.shape[1]:
                roi = frame[top:top+h, left:left+w]
                alpha_icon = icon[:, :, 3] / 255.0
                alpha_frame = 1.0 - alpha_icon
                for c in range(3):
                    roi[:, :, c] = (alpha_icon * icon[:, :, c] + alpha_frame * roi[:, :, c])
            
            # Draw professional label below the icon
            label = tool.replace("_", " ").title()
            if label == "Export 3d":
                label = "3D Export"
            if label == "Spray":
                label = "Brush"
            if label == "Crayon":
                label = "Palette"
                
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            tx = cx - text_size[0] // 2
            ty = cy + h // 2 + 12
            cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

    def render(self, frame):
        self.slide_y = 0
        y_offset = self.slide_y
        Theme.draw_glass_panel(frame, 0, y_offset, self.width, y_offset + self.panel_h)
        
        btn_w = self.width // len(self.tools)
        
        for i, tool in enumerate(self.tools):
            x_start = i * btn_w
            x_end = (i + 1) * btn_w
            cx = x_start + btn_w // 2
            cy = y_offset + self.panel_h // 2
            
            color = Theme.WHITE
            is_active = (tool == self.active_tool)
            
            # Rounded button coordinates with proper spacing
            pad = 8
            bx1, by1 = x_start + pad, y_offset + pad
            bx2, by2 = x_end - pad, y_offset + self.panel_h - pad
            
            if is_active:
                # Active highlight (cyan glow border + brighter bg)
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (90, 80, 70), -1)
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), Theme.CYAN, 2)
                color = Theme.CYAN
            elif i == self.hover_idx:
                # Smooth hover effect
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (70, 60, 50), -1)
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (120, 110, 100), 1)
                if self.dwell_start:
                    progress = min(1.0, (time.time() - self.dwell_start) / self.DWELL_TIME)
                    w = int(progress * (bx2 - bx1))
                    cv2.rectangle(frame, (bx1, by2 - 4), (bx1 + w, by2), Theme.CYAN, -1)
            
            # Draw the cached icon + label
            self.draw_icon(frame, tool, cx, cy, color, is_active=is_active)
