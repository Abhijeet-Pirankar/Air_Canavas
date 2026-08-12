"""
ui/widgets/camera_worker.py
QThread that captures webcam frames, runs hand tracking,
and emits signals to the main thread — keeps UI responsive.
"""
import time
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from core.smooth_cursor import AdvancedCursorFilter


class CameraWorker(QThread):
    # Emits: (display_frame_bgr, lmList, is_drawing, is_selecting, x1, y1)
    frame_ready = pyqtSignal(np.ndarray, list, bool, bool, float, float)
    fps_updated = pyqtSignal(int)
    tracking_changed = pyqtSignal(bool)
    camera_status_changed = pyqtSignal(bool)

    def __init__(self, tracker, canvas_w: int, canvas_h: int):
        super().__init__()
        self.tracker = tracker
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self._running = True
        self.cursor_filter = AdvancedCursorFilter()
        self._cap = None  # accessible for early release on stop()

        # CLAHE for subtle enhancement
        self._clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
        self._last_tracking = None
        self._last_cam_status = None

    def stop(self):
        self._running = False
        # Release cap immediately to unblock cap.read() in the run loop
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def run(self):
        print("[CAMERA] CameraWorker starting...")
        cap = self._open_camera()
        if cap is None:
            print("[CAMERA] Could not open camera. Exiting worker.")
            return
        self._cap = cap

        frame_count = 0
        fps_t = time.time()
        consecutive_fails = 0
        MAX_FAILS = 30

        while self._running:
            ok, img = cap.read()

            # ---- Handle read failure ----
            if not ok:
                consecutive_fails += 1
                if self._last_cam_status is not False:
                    self.camera_status_changed.emit(False)
                    self._last_cam_status = False
                    print("[CAMERA] Frame read failed — attempting recovery...")

                # After too many consecutive failures, try to re-open
                if consecutive_fails >= MAX_FAILS:
                    print("[CAMERA] Re-opening camera...")
                    cap.release()
                    time.sleep(1.0)
                    cap = self._open_camera()
                    if cap is None:
                        print("[CAMERA] Re-open failed. Stopping.")
                        return
                    consecutive_fails = 0

                time.sleep(0.05)
                continue

            # ---- Successful frame ----
            consecutive_fails = 0
            if self._last_cam_status is not True:
                self.camera_status_changed.emit(True)
                self._last_cam_status = True

            img = cv2.flip(img, 1)
            img = cv2.resize(img, (self.canvas_w, self.canvas_h))

            # ---- Subtle enhancement (CLAHE) ----
            try:
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l = self._clahe.apply(l)
                img_disp = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
                img_disp = cv2.convertScaleAbs(img_disp, alpha=1.05, beta=0)
            except Exception as e:
                print(f"[CAMERA] Frame enhancement failed: {e}")
                img_disp = img

            # ---- Hand tracking (run on clean frame) ----
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            lmList = self.tracker.process_frame(img_rgb)

            is_drawing = is_selecting = False
            x1: float = 0.0
            y1: float = 0.0

            if lmList:
                index_up  = lmList[8][2]  < lmList[6][2]
                middle_up = lmList[12][2] < lmList[10][2]
                raw_x, raw_y = float(lmList[8][1]), float(lmList[8][2])
                
                # Apply advanced floating-point smoothing
                x1, y1 = self.cursor_filter.update(raw_x, raw_y)
                
                # Clamp safely within canvas boundaries
                x1 = max(0.0, min(float(self.canvas_w - 1), x1))
                y1 = max(0.0, min(float(self.canvas_h - 1), y1))
                
                is_selecting = index_up and middle_up
                is_drawing   = index_up and not middle_up
            else:
                self.tracker.reset_filters()
                self.cursor_filter.reset()

            # ---- Tracking status change ----
            tracking_now = bool(lmList)
            if tracking_now != self._last_tracking:
                self.tracking_changed.emit(tracking_now)
                self._last_tracking = tracking_now
                print("[HAND] Hand detected" if tracking_now else "[HAND] Hand lost")

            # ---- FPS counter ----
            frame_count += 1
            now = time.time()
            if now - fps_t >= 1.0:
                self.fps_updated.emit(frame_count)
                frame_count = 0
                fps_t = now

            self.frame_ready.emit(img_disp, lmList, is_drawing, is_selecting, x1, y1)

        cap.release()
        print("[CAMERA] Camera released.")

    # ------------------------------------------------------------------
    def _open_camera(self, max_retries: int = 10):
        """Try to open camera index 0 with exponential back-off. Returns cap or None."""
        delay = 0.5
        for attempt in range(1, max_retries + 1):
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.canvas_w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.canvas_h)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(f"[CAMERA] Camera opened (attempt {attempt})")
                self.camera_status_changed.emit(True)
                self._last_cam_status = True
                return cap
            cap.release()
            print(f"[CAMERA] Open failed (attempt {attempt}/{max_retries}), retry in {delay:.1f}s...")
            if self._last_cam_status is not False:
                self.camera_status_changed.emit(False)
                self._last_cam_status = False
            if not self._running:
                return None
            time.sleep(delay)
            delay = min(delay * 1.5, 4.0)
        return None
