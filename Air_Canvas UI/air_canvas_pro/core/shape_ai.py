import cv2
import numpy as np

class ShapeAI:
    def __init__(self):
        # We can store the current stroke here
        self.current_stroke = []

    def add_point(self, pt):
        self.current_stroke.append(pt)

    def reset(self):
        self.current_stroke = []

    def _is_circle(self, contour):
        """Check if contour is roughly circular."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return False
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        return 0.7 < circularity < 1.2

    def process_stroke(self, image, color, thickness):
        """Analyzes the current stroke and replaces it with a perfect shape if it matches one."""
        if len(self.current_stroke) < 10:
            # Too short to be a shape, just draw it normally
            self._draw_raw(image, color, thickness)
            self.reset()
            return False

        # Convert stroke to contour
        contour = np.array(self.current_stroke).reshape((-1, 1, 2)).astype(np.int32)
        
        # Check if it's closed (distance between start and end is small)
        start_pt = self.current_stroke[0]
        end_pt = self.current_stroke[-1]
        dist = np.hypot(end_pt[0] - start_pt[0], end_pt[1] - start_pt[1])
        
        is_closed = dist < 50
        
        if is_closed and self._is_circle(contour):
            # Draw a perfect circle
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius)
            cv2.circle(image, center, radius, color, thickness)
            self.reset()
            return True
            
        # Check if it's a straight line
        # If the contour length is close to the bounding box diagonal
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        width = rect[1][0]
        height = rect[1][1]
        
        if min(width, height) < 20 and max(width, height) > 50:
            # Draw a perfect line
            vx, vy, x, y = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
            # Find extreme points
            pts = np.array(self.current_stroke)
            dists = np.dot(pts - [x[0], y[0]], [vx[0], vy[0]])
            min_idx = np.argmin(dists)
            max_idx = np.argmax(dists)
            p1 = tuple(pts[min_idx].astype(int))
            p2 = tuple(pts[max_idx].astype(int))
            cv2.line(image, p1, p2, color, thickness)
            self.reset()
            return True
            
        # If no shape matched, just draw raw
        self._draw_raw(image, color, thickness)
        self.reset()
        return False

    def _draw_raw(self, image, color, thickness):
        if len(self.current_stroke) < 2:
            if self.current_stroke:
                cv2.circle(image, self.current_stroke[0], thickness//2, color, -1)
            return
            
        pts = np.array(self.current_stroke, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], False, color, thickness)
