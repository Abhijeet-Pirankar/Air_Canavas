from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton, QToolButton
from PyQt6.QtCore import Qt, QSize

class LayerItemWidget(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        self.lbl = QLabel(name)
        
        self.btn_vis = QToolButton()
        self.btn_vis.setText("👁")
        self.btn_vis.setStyleSheet("background:transparent; border:none; color:#F5F7FA; font-size:14px;")
        
        self.btn_lock = QToolButton()
        self.btn_lock.setText("🔒")
        self.btn_lock.setStyleSheet("background:transparent; border:none; color:#F5F7FA; font-size:14px;")
        
        layout.addWidget(self.lbl)
        layout.addStretch()
        layout.addWidget(self.btn_vis)
        layout.addWidget(self.btn_lock)

class LayersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setFixedWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("LAYERS")
        title.setStyleSheet("font-weight: bold; color: #F5F7FA; letter-spacing: 2px; font-size: 13px; font-family: 'Inter', sans-serif;")
        layout.addWidget(title)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Add some mock layers
        layer_names = ["Layer 3", "Layer 2", "Layer 1", "Background"]
        for i, name in enumerate(layer_names):
            item = QListWidgetItem()
            item.setSizeHint(QSize(200, 48)) 
            self.list_widget.addItem(item)
            
            widget = LayerItemWidget(name)
            if name == "Background":
                widget.btn_vis.hide()
            else:
                widget.btn_lock.hide()
                
            if name == "Layer 1":
                widget.lbl.setStyleSheet("color: white; font-weight: bold;")
                item.setSelected(True)
            self.list_widget.setItemWidget(item, widget)
                
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ New Layer")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08); 
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px; 
                padding: 10px;
                color: #F5F7FA;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(35, 42, 55, 0.88);
                border: 1px solid rgba(0, 229, 255, 0.45);
            }
        """)
        btn_layout.addWidget(add_btn)
        
        layout.addLayout(btn_layout)
