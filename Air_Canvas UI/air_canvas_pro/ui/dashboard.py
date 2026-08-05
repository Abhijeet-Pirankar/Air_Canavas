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
        
        # Dashboard just below the top toolbar
        dash_w = 220
        dash_h = 70
        x1 = self.width - dash_w - 20
        y1 = 120
        
        Theme.draw_glass_panel(frame, x1, y1, x1 + dash_w, y1 + dash_h)
        
        # Content
        Theme.draw_glowing_text(frame, f"TOOL: {active_tool.upper()}", (x1 + 15, y1 + 25), scale=0.5)
        cv2.putText(frame, f"SIZE: {brush_size} | ZOOM: {zoom:.1f}x", (x1 + 15, y1 + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, Theme.WHITE, 1, cv2.LINE_AA)
        
        # Color preview
        cv2.circle(frame, (x1 + dash_w - 25, y1 + 35), 12, color, -1)
        cv2.circle(frame, (x1 + dash_w - 25, y1 + 35), 12, Theme.WHITE, 1)
        
        # FPS Counter (bottom right)
        cv2.putText(frame, f"{self.fps} FPS", (self.width - 60, self.height - 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, Theme.GRAY, 1, cv2.LINE_AA)
                    
        # Toast notifications
        if self.toast_msg and time.time() - self.toast_time < 2.0:
            alpha = max(0, 1.0 - (time.time() - self.toast_time) / 2.0)
            y_toast = self.height - 80
            
            # Estimate text width
            (tw, th), _ = cv2.getTextSize(self.toast_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            tx = (self.width - tw) // 2
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (tx - 20, y_toast - th - 10), (tx + tw + 20, y_toast + 10), Theme.PANEL_BG, -1)
            cv2.rectangle(overlay, (tx - 20, y_toast - th - 10), (tx + tw + 20, y_toast + 10), Theme.CYAN, 1)
            
            frame[:] = cv2.addWeighted(overlay, alpha * 0.8, frame, 1 - alpha * 0.8, 0)
            cv2.putText(frame, self.toast_msg, (tx, y_toast), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Theme.CYAN, 2, cv2.LINE_AA)
