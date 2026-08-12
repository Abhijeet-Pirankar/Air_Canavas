import math

class AdvancedCursorFilter:
    """
    Advanced temporal smoothing filter for cursor movement.
    Implements an adaptive One Euro-style algorithm:
    - Slow movements are heavily smoothed to remove micro-jitter.
    - Fast movements reduce smoothing to stay responsive.
    """

    # --- CONFIGURATION ---
    
    # Minimum smoothing factor (0.0 to 1.0). Used when moving slowly.
    # Lower values = more smoothing (heavier cursor).
    SMOOTHING_MIN = 0.15 
    
    # Maximum smoothing factor. Used when moving quickly.
    # 1.0 = instant snap (no smoothing).
    SMOOTHING_MAX = 0.85
    
    # Deadzone in pixels. Movements smaller than this are completely ignored
    # to eliminate hand trembling when hovering.
    DEADZONE = 1.5
    
    # Maximum realistic jump in a single frame. If MediaPipe spits out a 
    # completely wild coordinate (e.g. hand swapping), we dampen the jump.
    MAX_JUMP_DISTANCE = 150.0
    
    # Velocity scale to normalize distance into an interpolation alpha.
    VELOCITY_SCALE = 40.0

    def __init__(self):
        self.prev_x = None
        self.prev_y = None

    def reset(self):
        self.prev_x = None
        self.prev_y = None

    def update(self, raw_x: float, raw_y: float) -> tuple[float, float]:
        """
        Takes raw MediaPipe coordinates and returns smoothed sub-pixel coordinates.
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x = raw_x
            self.prev_y = raw_y
            return raw_x, raw_y

        dx = raw_x - self.prev_x
        dy = raw_y - self.prev_y
        dist = math.hypot(dx, dy)

        # 1. Deadzone: Ignore micro jitter
        if dist < self.DEADZONE:
            return self.prev_x, self.prev_y

        # 2. Jitter Protection: Clamp massive erroneous jumps
        if dist > self.MAX_JUMP_DISTANCE:
            # Dampen the jump significantly to avoid teleporting
            dx = (dx / dist) * self.MAX_JUMP_DISTANCE
            dy = (dy / dist) * self.MAX_JUMP_DISTANCE
            dist = self.MAX_JUMP_DISTANCE

        # 3. Adaptive Smoothing: calculate alpha based on movement speed
        # The faster the movement, the closer alpha gets to 1.0
        speed_factor = min(1.0, dist / self.VELOCITY_SCALE)
        alpha = self.SMOOTHING_MIN + speed_factor * (self.SMOOTHING_MAX - self.SMOOTHING_MIN)

        # Apply exponential moving average
        smoothed_x = self.prev_x + alpha * dx
        smoothed_y = self.prev_y + alpha * dy

        self.prev_x = smoothed_x
        self.prev_y = smoothed_y

        return smoothed_x, smoothed_y
