import cv2
import numpy as np

class Theme:
    # Colors (BGR)
    BACKGROUND = (25, 15, 11)   # Dark Blue / Black
    PANEL_BG = (42, 30, 20)     # Panel background
    CYAN = (255, 240, 0)        # Primary Accent #00F0FF in BGR
    PURPLE = (255, 0, 191)      # Secondary Accent #BF00FF in BGR
    WHITE = (245, 245, 245)
    GRAY = (150, 150, 150)
    DARK_GRAY = (80, 80, 80)
    RED = (60, 60, 255)         # Warning/Delete

    @staticmethod
    def draw_glass_panel(frame, x1, y1, x2, y2, alpha=0.75, blur_radius=15):
        """Draws a premium dark panel — optimized for real-time performance."""
        h, w = frame.shape[:2]
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(w, int(x2)), min(h, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            return

        roi = frame[y1:y2, x1:x2]
        
        # Fast: alpha-blend a dark color overlay (no blur = much faster)
        color_overlay = np.full(roi.shape, Theme.PANEL_BG, dtype=np.uint8)
        frame[y1:y2, x1:x2] = cv2.addWeighted(roi, 1 - alpha, color_overlay, alpha, 0)
        
        # Soft border
        cv2.rectangle(frame, (x1, y1), (x2, y2), (90, 90, 100), 1)
        # Top-left highlight for 3D feel
        cv2.line(frame, (x1, y1), (x2, y1), (150, 150, 160), 1)
        cv2.line(frame, (x1, y1), (x1, y2), (150, 150, 160), 1)

    @staticmethod
    def draw_glowing_text(frame, text, pos, scale=0.6, color=CYAN, thickness=2):
        """Draws text with a soft neon glow."""
        x, y = pos
        # Glow
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness + 4, cv2.LINE_AA)
        # Core
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, Theme.WHITE, thickness, cv2.LINE_AA)
