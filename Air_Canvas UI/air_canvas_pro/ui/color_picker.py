import cv2
import numpy as np
import math
from air_canvas_pro.ui.theme import Theme

class ColorPicker:
    def __init__(self, cx, cy, radius=80):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.active_color = Theme.CYAN
        self.is_visible = False
        
        # Precompute color wheel
        self.wheel_img = np.zeros((radius*2, radius*2, 3), dtype=np.uint8)
        for y in range(radius*2):
            for x in range(radius*2):
                dx = x - radius
                dy = y - radius
                r = math.hypot(dx, dy)
                if r <= radius:
                    angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
                    sat = r / radius
                    hsv = np.uint8([[[angle / 2, sat * 255, 255]]])
                    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
                    self.wheel_img[y, x] = bgr

    def toggle(self):
        self.is_visible = not self.is_visible

    def hit_test(self, x, y):
        if not self.is_visible: return None
        dx = x - self.cx
        dy = y - self.cy
        r = math.hypot(dx, dy)
        if r <= self.radius:
            angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
            sat = r / self.radius
            hsv = np.uint8([[[angle / 2, sat * 255, 255]]])
            self.active_color = tuple(int(c) for c in cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0])
            self.is_visible = False
            return self.active_color
        return None

    def render(self, frame):
        if not self.is_visible:
            return
            
        x1 = self.cx - self.radius
        y1 = self.cy - self.radius
        x2 = self.cx + self.radius
        y2 = self.cy + self.radius
        
        # Don't draw if out of bounds
        if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
            return
            
        # Draw glass background for color picker
        Theme.draw_glass_panel(frame, x1-20, y1-20, x2+20, y2+60, alpha=0.9, blur_radius=25)
        
        # Overlay the wheel (mask out background)
        roi = frame[y1:y2, x1:x2]
        mask = np.zeros((self.radius*2, self.radius*2), dtype=np.uint8)
        cv2.circle(mask, (self.radius, self.radius), self.radius, 255, -1)
        
        for c in range(3):
            roi[:, :, c] = np.where(mask == 255, self.wheel_img[:, :, c], roi[:, :, c])
            
        # Draw current color preview
        cv2.circle(frame, (self.cx, y2 + 25), 15, self.active_color, -1)
        cv2.circle(frame, (self.cx, y2 + 25), 15, Theme.WHITE, 2)
