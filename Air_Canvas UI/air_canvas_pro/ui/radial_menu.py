import cv2
import numpy as np
import time
from air_canvas_pro.ui.theme import Theme

class RadialMenu:
    def __init__(self):
        self.is_active = False
        self.center = (0, 0)
        self.radius = 80
        self.options = ["Clear", "Undo", "Redo", "Close"]
        self.hover_idx = -1
        self.anim_progress = 0.0
        self.open_time = 0

    def open(self, x, y):
        self.is_active = True
        self.center = (x, y)
        self.anim_progress = 0.0
        self.open_time = time.time()
        self.hover_idx = -1

    def close(self):
        self.is_active = False

    def hit_test(self, x, y):
        if not self.is_active: return -1
        dx = x - self.center[0]
        dy = y - self.center[1]
        dist = np.hypot(dx, dy)
        
        if dist > self.radius - 20 and dist < self.radius + 30:
            angle = np.degrees(np.arctan2(dy, dx))
            if angle < 0: angle += 360
            
            # 4 options, each 90 degrees
            idx = int(((angle + 45) % 360) // 90)
            return idx
        return -1

    def update(self, x, y, is_selecting):
        if not self.is_active: return None
        
        # Simple animation
        elapsed = time.time() - self.open_time
        self.anim_progress = min(1.0, elapsed * 3) # Fast pop-in
        
        idx = self.hit_test(x, y)
        self.hover_idx = idx
        
        # If user stops pinching, execute the hovered option and close
        if not is_selecting:
            self.close()
            if idx != -1:
                return self.options[idx].lower()
        return None

    def render(self, frame):
        if not self.is_active: return
        
        cx, cy = self.center
        r = int(self.radius * self.anim_progress)
        if r <= 0: return

        # Draw central hub
        cv2.circle(frame, (cx, cy), int(15 * self.anim_progress), Theme.PANEL_BG, -1)
        cv2.circle(frame, (cx, cy), int(15 * self.anim_progress), Theme.CYAN, 1)
        
        # We need a copy for transparency
        overlay = frame.copy()
        
        for i, opt in enumerate(self.options):
            angle = np.radians(i * 90)
            nx = int(cx + r * np.cos(angle))
            ny = int(cy + r * np.sin(angle))
            
            # Connecting line
            cv2.line(overlay, (cx, cy), (nx, ny), Theme.PANEL_BG, 2)
            
            # Node background
            color = Theme.CYAN if i == self.hover_idx else Theme.PANEL_BG
            text_color = Theme.BACKGROUND if i == self.hover_idx else Theme.WHITE
            
            cv2.circle(overlay, (nx, ny), 30, color, -1)
            cv2.circle(overlay, (nx, ny), 30, (90, 90, 90), 1)
            
            # Node text
            font = cv2.FONT_HERSHEY_SIMPLEX
            (tw, th), _ = cv2.getTextSize(opt, font, 0.4, 1)
            cv2.putText(overlay, opt, (nx - tw//2, ny + th//2), font, 0.4, text_color, 1, cv2.LINE_AA)
            
        cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)
