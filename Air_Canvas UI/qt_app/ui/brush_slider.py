from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class BrushSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setFixedWidth(70)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)
        
        title = QLabel("BRUSH SIZE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 11px; color: #F5F7FA; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title)
        
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(2, 50) # Updated range to match normal brush size bounds
        self.slider.setValue(10)
        layout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Live preview circle
        self.preview_container = QWidget()
        self.preview_container.setFixedSize(50, 50)
        pc_layout = QVBoxLayout(self.preview_container)
        pc_layout.setContentsMargins(0,0,0,0)
        pc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview = QLabel()
        self._update_preview(10)
        pc_layout.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.preview_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        self.val_label = QLabel("10px")
        self.val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_label.setStyleSheet("color: white; font-size: 11px;")
        layout.addWidget(self.val_label)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
    def _on_value_changed(self, v):
        self.val_label.setText(f"{v}px")
        self._update_preview(v)
        
    def _update_preview(self, size):
        self.preview.setFixedSize(size, size)
        self.preview.setStyleSheet(f"background-color: #00E5FF; border-radius: {size//2}px; border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 0 8px rgba(0,229,255,0.5);")
