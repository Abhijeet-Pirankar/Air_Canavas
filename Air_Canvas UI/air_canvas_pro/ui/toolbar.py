import cv2
import time
import numpy as np
import os
from air_canvas_pro.ui.theme import Theme

class Toolbar:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        
        self.panel_h = 70
        self.margin_top = 20
        self.margin_side = 200 # Centered toolbar
        
        self.is_visible = True
        self.last_interaction = time.time()
        
        self.tools = ["draw", "eraser", "spray", "crayon", "shapes", "undo", "redo", "clear", "save", "export_3d"]
        self.active_tool = "draw"
        
        # Animations
        self.hover_idx = -1
        self.dwell_start = None
        self.DWELL_TIME = 0.4 # Quick selection
        
        self.tooltips = {
            "draw": "Draw", "eraser": "Eraser", "spray": "Airbrush", 
            "crayon": "Palette", "shapes": "Shapes", "undo": "Undo", 
            "redo": "Redo", "clear": "Clear", "save": "Save", "export_3d": "3D Export"
        }

        self.icons = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_dir = os.path.join(base_dir, "assets", "icons")
        
        for t in self.tools:
            path = os.path.join(icon_dir, f"{t}.png")
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if len(img.shape) == 3 and img.shape[2] == 4:
                        img = cv2.resize(img, (32, 32))
                        self.icons[t] = img
                    elif len(img.shape) == 3 and img.shape[2] == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                        img = cv2.resize(img, (32, 32))
                        self.icons[t] = img

    def hit_test(self, x, y):
        self.last_interaction = time.time()
        panel_w = self.width - 2 * self.margin_side
        if self.margin_top <= y <= self.margin_top + self.panel_h and self.margin_side <= x <= self.width - self.margin_side:
            btn_w = panel_w // len(self.tools)
            idx = (x - self.margin_side) // btn_w
            return min(max(idx, 0), len(self.tools) - 1)
        return -1

    def update(self, x, y, is_selecting):
        action = None
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
                    action = selected
                    # We do NOT reset dwell_start here so that if they hold it, it can trigger Radial Menu later!
                    # But to avoid triggering action repeatedly, we need to handle it.
                    # We will return the action once, and then set a flag or just let `air_canvas.py` debounce it.
                    # Simple fix: return the action, but don't reset dwell_start.
                    # Wait, if we return `selected` every frame after DWELL_TIME, save/undo will trigger 30 times a second.
                    # We need a `has_triggered` flag.
                    if not getattr(self, '_triggered_idx', None) == idx:
                        self._triggered_idx = idx
                        return selected
                    return None
            else:
                self.hover_idx = -1
                self.dwell_start = None
                self._triggered_idx = None
        else:
            self.hover_idx = -1
            self.dwell_start = None
            self._triggered_idx = None
            
        return None

    def draw_icon(self, frame, tool, cx, cy, color, is_active=False, scale=1.0):
        if tool in self.icons:
            icon = self.icons[tool].copy()
            
            if is_active:
                alpha_mask = icon[:, :, 3] > 0
                icon[alpha_mask, 0] = Theme.CYAN[0]
                icon[alpha_mask, 1] = Theme.CYAN[1]
                icon[alpha_mask, 2] = Theme.CYAN[2]

            if scale != 1.0:
                h, w = icon.shape[:2]
                new_size = (int(w * scale), int(h * scale))
                icon = cv2.resize(icon, new_size, interpolation=cv2.INTER_LINEAR)

            h, w = icon.shape[:2]
            top, left = int(cy - h // 2), int(cx - w // 2)
            
            if top >= 0 and left >= 0 and top+h <= frame.shape[0] and left+w <= frame.shape[1]:
                roi = frame[top:top+h, left:left+w]
                alpha_icon = icon[:, :, 3] / 255.0
                alpha_frame = 1.0 - alpha_icon
                
                # Draw subtle drop shadow for 3D effect
                sy, sx = 3, 2
                shadow_alpha = alpha_icon * 0.4
                shadow_frame_alpha = 1.0 - shadow_alpha
                if top+sy >= 0 and left+sx >= 0 and top+sy+h <= frame.shape[0] and left+sx+w <= frame.shape[1]:
                    s_roi = frame[top+sy:top+sy+h, left+sx:left+sx+w]
                    for c in range(3):
                        s_roi[:, :, c] = (shadow_frame_alpha * s_roi[:, :, c])
                
                for c in range(3):
                    roi[:, :, c] = (alpha_icon * icon[:, :, c] + alpha_frame * roi[:, :, c])

    def render(self, frame):
        panel_w = self.width - 2 * self.margin_side
        
        Theme.draw_glass_panel(frame, self.margin_side, self.margin_top, 
                               self.width - self.margin_side, self.margin_top + self.panel_h, radius=16)
        
        btn_w = panel_w // len(self.tools)
        
        for i, tool in enumerate(self.tools):
            x_start = self.margin_side + i * btn_w
            x_end = self.margin_side + (i + 1) * btn_w
            cx = x_start + btn_w // 2
            cy = self.margin_top + self.panel_h // 2
            
            color = Theme.WHITE
            is_active = (tool == self.active_tool)
            icon_scale = 1.0
            
            if is_active:
                # Cyan glow border for active tool
                Theme.draw_rounded_rect(frame, (x_start + 4, self.margin_top + 4), 
                                        (x_end - 4, self.margin_top + self.panel_h - 4), 
                                        Theme.CYAN, 2, radius=12)
                color = Theme.CYAN
            
            if i == self.hover_idx:
                icon_scale = 1.2
                # Highlight background
                Theme.draw_rounded_rect(frame, (x_start + 4, self.margin_top + 4), 
                                        (x_end - 4, self.margin_top + self.panel_h - 4), 
                                        (50, 45, 40), -1, radius=12)
                
                # Draw tooltip below
                Theme.draw_tooltip(frame, self.tooltips.get(tool, tool), cx, self.margin_top + self.panel_h)
            
            self.draw_icon(frame, tool, cx, cy, color, is_active=is_active, scale=icon_scale)
