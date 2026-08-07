import cv2
import numpy as np
import math
from air_canvas_pro.ui.theme import Theme

class ColorPicker:
    def __init__(self, radius=70):
        self.cx = 0
        self.cy = 0
        self.radius = radius
        self.active_color = Theme.CYAN
        self.is_visible = False
        
        # 8 Predefined Discrete Colors (BGR)
        self.swatches = [
            (60, 60, 255),    # Red
            (60, 150, 255),   # Orange
            (60, 255, 255),   # Yellow
            (100, 255, 100),  # Green
            (255, 229, 0),    # Cyan
            (255, 100, 50),   # Blue
            (255, 0, 191),    # Purple
            (248, 249, 250)   # White
        ]
        self.swatch_radius = 20
        self.hover_idx = -1

    def toggle(self, x=None, y=None):
        if x is not None and y is not None:
            self.cx = x
            self.cy = y
        self.is_visible = not self.is_visible
        self.hover_idx = -1

    def hit_test(self, x, y):
        if not self.is_visible: return None
        
        # Check center (active color, closes if clicked)
        if math.hypot(x - self.cx, y - self.cy) < self.swatch_radius:
            self.is_visible = False
            return self.active_color
            
        # Check swatches
        for i, color in enumerate(self.swatches):
            angle = math.radians(i * (360 / len(self.swatches)))
            sx = int(self.cx + self.radius * math.cos(angle))
            sy = int(self.cy + self.radius * math.sin(angle))
            
            if math.hypot(x - sx, y - sy) < self.swatch_radius + 5:
                self.active_color = color
                self.is_visible = False
                return self.active_color
                
        return None

    def update(self, x, y, is_selecting):
        if not self.is_visible: return None
        
        # Update hover state
        self.hover_idx = -1
        for i, color in enumerate(self.swatches):
            angle = math.radians(i * (360 / len(self.swatches)))
            sx = int(self.cx + self.radius * math.cos(angle))
            sy = int(self.cy + self.radius * math.sin(angle))
            if math.hypot(x - sx, y - sy) < self.swatch_radius + 5:
                self.hover_idx = i
                break
                
        if is_selecting:
            return self.hit_test(x, y)
        return None

    def render(self, frame):
        if not self.is_visible: return
        
        # Draw background glass panel for the entire radial area
        pad = self.radius + self.swatch_radius + 15
        Theme.draw_glass_panel(frame, self.cx - pad, self.cy - pad, self.cx + pad, self.cy + pad, alpha=0.9, radius=100)
        
        # Draw center active color
        cv2.circle(frame, (self.cx, self.cy), self.swatch_radius, self.active_color, -1)
        cv2.circle(frame, (self.cx, self.cy), self.swatch_radius, Theme.CYAN, 2)
        
        # Draw 8 surrounding swatches
        for i, color in enumerate(self.swatches):
            angle = math.radians(i * (360 / len(self.swatches)))
            sx = int(self.cx + self.radius * math.cos(angle))
            sy = int(self.cy + self.radius * math.sin(angle))
            
            cv2.circle(frame, (sx, sy), self.swatch_radius, color, -1)
            
            if i == self.hover_idx or color == self.active_color:
                cv2.circle(frame, (sx, sy), self.swatch_radius + 4, Theme.CYAN, 2)
            else:
                cv2.circle(frame, (sx, sy), self.swatch_radius, (90, 90, 90), 1)
