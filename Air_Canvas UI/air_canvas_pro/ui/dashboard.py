import cv2
import time
from air_canvas_pro.ui.theme import Theme

class Dashboard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fps = 0
        self.frames = 0
        self.last_time = time.time()
        self.toast_msg = None
        self.toast_time = 0
        
        self.bottom_h = 40

    def update_fps(self):
        self.frames += 1
        now = time.time()
        if now - self.last_time >= 1.0:
            self.fps = self.frames
            self.frames = 0
            self.last_time = now

    def notify(self, msg):
        self.toast_msg = msg
        self.toast_time = time.time()

    def render(self, frame, active_tool, brush_size, zoom, color):
        self.update_fps()
        
        # Bottom Status Bar
        y_bot = self.height - self.bottom_h
        Theme.draw_glass_panel(frame, 0, y_bot, self.width, self.height, radius=0) # Flat at bottom
        
        # Tool Status
        status_text = f"ACTIVE TOOL: {active_tool.upper()}      SIZE: {brush_size}px      ZOOM: {zoom:.1f}x"
        cv2.putText(frame, status_text, (30, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, Theme.WHITE, 1, cv2.LINE_AA)
        
        # Active Color preview circle
        color_x = self.width // 2
        cv2.putText(frame, "COLOR: ", (color_x - 60, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, Theme.GRAY, 1, cv2.LINE_AA)
        cv2.circle(frame, (color_x + 10, self.height - 20), 10, color, -1)
        cv2.circle(frame, (color_x + 10, self.height - 20), 10, Theme.WHITE, 1)
        
        # Tracking & FPS
        tracking_text = f"TRACKING: ACTIVE      FPS: {self.fps}"
        cv2.putText(frame, tracking_text, (self.width - 250, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, Theme.SUCCESS, 1, cv2.LINE_AA)

        # Toast notifications
        if self.toast_msg and time.time() - self.toast_time < 2.0:
            alpha = max(0, 1.0 - (time.time() - self.toast_time) / 2.0)
            y_toast = y_bot - 60
            
            # Estimate text width
            (tw, th), _ = cv2.getTextSize(self.toast_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            tx = (self.width - tw) // 2
            
            x1, y1 = tx - 20, y_toast - th - 15
            x2, y2 = tx + tw + 20, y_toast + 15
            
            overlay = frame.copy()
            Theme.draw_rounded_rect(overlay, (x1, y1), (x2, y2), Theme.PANEL_BG, -1, 16)
            Theme.draw_rounded_rect(overlay, (x1, y1), (x2, y2), Theme.CYAN, 1, 16)
            
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.putText(frame, self.toast_msg, (tx, y_toast), cv2.FONT_HERSHEY_SIMPLEX, 0.5, Theme.WHITE, 1, cv2.LINE_AA)
