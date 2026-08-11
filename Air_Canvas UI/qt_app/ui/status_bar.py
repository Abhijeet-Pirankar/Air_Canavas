from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QStatusBar::item { border: none; padding: 0 10px; }
        """)

        def lbl(text, color="#A0A5B5"):
            l = QLabel(text)
            l.setStyleSheet(f"color:{color}; font-family:'Segoe UI',sans-serif; font-size:12px; padding-right:16px;")
            return l

        self.tool_lbl    = lbl("TOOL: PENCIL")
        self.size_lbl    = lbl("SIZE: 10px")
        self.zoom_lbl    = lbl("ZOOM: 1.0x")
        self.fps_lbl     = lbl("FPS: --")
        self.cam_lbl     = lbl("CAM: WAIT", "#00E5FF")
        self.track_lbl   = lbl("● HAND TRACKING: ACTIVE", "#00FF66")
        self.notify_lbl  = lbl("", "#00E5FF")

        for l in [self.tool_lbl, self.size_lbl, self.zoom_lbl, self.fps_lbl, self.cam_lbl, self.notify_lbl]:
            self.addWidget(l)
        self.addPermanentWidget(self.track_lbl)

        self._notify_timer = QTimer(self)
        self._notify_timer.setSingleShot(True)
        self._notify_timer.timeout.connect(lambda: self.notify_lbl.setText(""))

    def update_tool(self, tool: str):
        self.tool_lbl.setText(f"TOOL: {tool.upper()}")

    def update_size(self, size: int):
        self.size_lbl.setText(f"SIZE: {size}px")

    def update_fps(self, fps: int):
        self.fps_lbl.setText(f"FPS: {fps}")

    def update_tracking(self, active: bool):
        if active:
            self.track_lbl.setText("● HAND TRACKING: ACTIVE")
            self.track_lbl.setStyleSheet("color:#00FF66; font-size:12px; padding-right:10px;")
        else:
            self.track_lbl.setText("● HAND NOT DETECTED")
            self.track_lbl.setStyleSheet("color:#FF5555; font-size:12px; padding-right:10px;")

    def update_camera(self, ok: bool):
        if ok:
            self.cam_lbl.setText("CAM: OK")
            self.cam_lbl.setStyleSheet("color:#00E5FF; font-size:12px; padding-right:16px;")
        else:
            self.cam_lbl.setText("CAM: FAILED")
            self.cam_lbl.setStyleSheet("color:#FF5555; font-size:12px; padding-right:16px;")

    def notify(self, msg: str, duration_ms: int = 2500):
        self.notify_lbl.setText(f"  •  {msg}")
        self._notify_timer.start(duration_ms)
