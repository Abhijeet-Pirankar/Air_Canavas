import cv2
import numpy as np

class Theme:
    # Colors (BGR format for OpenCV)
    BACKGROUND = (23, 17, 15)   # #0F1117 Deep space navy/black
    PANEL_BG = (34, 26, 23)     # #171A22 Elevated dark navy
    CYAN = (255, 229, 0)        # #00E5FF Neon Cyan
    PURPLE = (255, 0, 191)      # Secondary Accent
    WHITE = (248, 249, 250)     # #F8F9FA Clean white
    GRAY = (191, 170, 160)      # #A0AABF Muted gray-blue (Secondary text)
    DARK_GRAY = (80, 80, 80)
    RED = (102, 51, 255)        # #FF3366 Warning/Error
    SUCCESS = (136, 255, 0)     # #00FF88

    @staticmethod
    def draw_rounded_rect(img, top_left, bottom_right, color, thickness=1, radius=16):
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        # Ensure radius isn't too large for the box
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        
        if thickness < 0: # Filled
            cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
            cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
            cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
            cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
            cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
        else: # Outline
            cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
            cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
            cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
            cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
            cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
            cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

    @staticmethod
    def draw_glass_panel(frame, x1, y1, x2, y2, alpha=0.85, radius=16):
        """Draws a premium 2026 dark panel with rounded glassmorphism feel."""
        h, w = frame.shape[:2]
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            return

        overlay = frame.copy()
        Theme.draw_rounded_rect(overlay, (x1, y1), (x2, y2), Theme.PANEL_BG, -1, radius)
        
        # We only want to blend where the rounded rect was drawn
        # A simple addWeighted on the whole frame works because overlay is a copy of frame
        # everywhere except the rounded rect.
        cv2.addWeighted(overlay, 1 - alpha, frame, alpha, 0, frame)
        
        # Soft subtle border for glass effect
        Theme.draw_rounded_rect(frame, (x1, y1), (x2, y2), (60, 60, 60), 1, radius)

    @staticmethod
    def draw_tooltip(frame, text, x, y):
        """Draws a sleek tooltip below the given coordinate."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.4
        thickness = 1
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        
        pad_x, pad_y = 10, 6
        x1, y1 = x - tw // 2 - pad_x, y + 10
        x2, y2 = x + tw // 2 + pad_x, y + 10 + th + pad_y * 2
        
        Theme.draw_glass_panel(frame, x1, y1, x2, y2, alpha=0.9, radius=6)
        cv2.putText(frame, text, (x - tw // 2, y1 + pad_y + th), font, scale, Theme.WHITE, thickness, cv2.LINE_AA)

    @staticmethod
    def draw_glowing_text(frame, text, pos, scale=0.6, color=CYAN, thickness=2, align="left"):
        """Draws text with a soft neon glow."""
        x, y = pos
        if align == "center":
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0]
            x = x - text_size[0] // 2
            
        # Glow
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness + 4, cv2.LINE_AA)
        # Core
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, Theme.WHITE, thickness, cv2.LINE_AA)
