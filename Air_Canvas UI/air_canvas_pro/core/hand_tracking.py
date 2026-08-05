import time
import numpy as np
import mediapipe as mp

class OneEuroFilter:
    """Reduces hand jitter while keeping responsiveness.
    Uses two exponential smoothing filters (for position and velocity)."""
    def __init__(self, min_cutoff=0.5, beta=0.08, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.t_prev = None
        self.x_prev = None
        self.dx_prev = 0.0

    def _smoothing_factor(self, cutoff):
        tau = 1.0 / (2.0 * np.pi * cutoff)
        return 1.0 / (1.0 + tau)

    def filter(self, x, t):
        if self.t_prev is None:
            self.t_prev = t
            self.x_prev = x
            self.dx_prev = 0.0
            return x
        dt = max(t - self.t_prev, 1e-5)
        dx = (x - self.x_prev) / dt
        edx = self._smoothing_factor(self.d_cutoff) * dx + \
              (1 - self._smoothing_factor(self.d_cutoff)) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self._smoothing_factor(cutoff)
        x_filtered = alpha * x + (1 - alpha) * self.x_prev
        self.t_prev = t
        self.x_prev = x_filtered
        self.dx_prev = edx
        return x_filtered


class HandTracker:
    def __init__(self, model_asset_path=None):
        import os
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        # Locate the model file
        if model_asset_path is None or not os.path.exists(model_asset_path):
            # Try common fallback locations
            candidates = [
                os.path.join(os.path.dirname(__file__), '..', '..', 'hand_landmarker.task'),
                os.path.join(os.getcwd(), 'hand_landmarker.task'),
            ]
            model_asset_path = next((os.path.abspath(p) for p in candidates if os.path.exists(p)), None)

        if not model_asset_path or not os.path.exists(model_asset_path):
            raise FileNotFoundError(
                "hand_landmarker.task not found. Download it from:\n"
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task\n"
                "and place it in the project root folder."
            )

        base_options = mp_python.BaseOptions(model_asset_path=model_asset_path)
        # VIDEO mode tracks across frames — much faster than IMAGE mode
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self._frame_ts_ms = 0   # incremented each frame

        self.filt_x = OneEuroFilter(min_cutoff=0.5, beta=0.08)
        self.filt_y = OneEuroFilter(min_cutoff=0.5, beta=0.08)

    def process_frame(self, img_rgb):
        """Detect hand landmarks. img_rgb must be a uint8 numpy array."""
        self._frame_ts_ms += 33   # ~30 fps assumed; keeps timestamps monotonic

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        result = self.detector.detect_for_video(mp_image, self._frame_ts_ms)

        h, w = img_rgb.shape[:2]
        lmList = []
        if result.hand_landmarks:
            for hand_lm in result.hand_landmarks:
                for idx, lm in enumerate(hand_lm):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append((idx, cx, cy, lm.z))
        return lmList

    def get_filtered_index(self, raw_x, raw_y):
        now = time.time()
        x1 = int(self.filt_x.filter(raw_x, now))
        y1 = int(self.filt_y.filter(raw_y, now))
        return x1, y1

    def reset_filters(self):
        self.filt_x.t_prev = None
        self.filt_y.t_prev = None

    def close(self):
        self.detector.close()
