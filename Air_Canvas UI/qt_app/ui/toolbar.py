"""
ui/toolbar.py
Premium full-width top toolbar with large icons, labels, and separate tool groups.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolButton,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtGui import QIcon, QColor, QPixmap, QPainter, QFont
from PyQt6.QtCore import Qt, QSize
import os


def colorize_icon(path: str, color_hex: str) -> QPixmap:
    """Return a recoloured copy of the SVG pixmap."""
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return QPixmap()
    result = pixmap.copy()
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color_hex))
    painter.end()
    return result


def create_stateful_icon(path: str) -> QIcon:
    """Build a QIcon with Normal/Active/Checked states from one SVG."""
    icon = QIcon()
    if not os.path.exists(path):
        return icon
    icon.addPixmap(colorize_icon(path, "#C8D0DC"), QIcon.Mode.Normal,  QIcon.State.Off)
    icon.addPixmap(colorize_icon(path, "#FFFFFF"), QIcon.Mode.Active,  QIcon.State.Off)
    icon.addPixmap(colorize_icon(path, "#00E5FF"), QIcon.Mode.Normal,  QIcon.State.On)
    icon.addPixmap(colorize_icon(path, "#66F4FF"), QIcon.Mode.Active,  QIcon.State.On)
    return icon


def _divider() -> QFrame:
    """Thin vertical divider between tool groups."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFixedWidth(1)
    line.setFixedHeight(60)
    line.setStyleSheet("background: rgba(255,255,255,0.10); border: none;")
    return line


class ToolBtn(QWidget):
    """Icon + label stacked vertically, looks like a pro tool button."""

    def __init__(self, icon_path: str, label: str, checkable: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedSize(QSize(72, 82))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 6, 0, 6)
        vlay.setSpacing(4)
        vlay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Button (icon only) ---
        self.btn = QToolButton()
        self.btn.setFixedSize(QSize(48, 48))
        self.btn.setIconSize(QSize(28, 28))
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setIcon(create_stateful_icon(icon_path))
        self.btn.setCheckable(checkable)
        self.btn.setAutoExclusive(False)   # managed by TopToolbar
        self.btn.setStyleSheet("""
            QToolButton {
                background: rgba(30, 38, 52, 0.55);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 14px;
            }
            QToolButton:hover {
                background: rgba(45, 55, 72, 0.80);
                border: 1px solid rgba(0,229,255,0.35);
            }
            QToolButton:checked {
                background: rgba(0, 229, 255, 0.14);
                border: 1px solid #00E5FF;
            }
        """)

        # --- Label ---
        self.lbl = QLabel(label)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setStyleSheet(
            "color: rgba(180,190,210,1); font-family:'Segoe UI','Inter',sans-serif; font-size:10px; font-weight:500; letter-spacing:0.5px;"
        )
        self.lbl.setFixedWidth(72)

        vlay.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        vlay.addWidget(self.lbl)

    def setChecked(self, state: bool):
        self.btn.setChecked(state)
        color = "rgba(0,229,255,1)" if state else "rgba(180,190,210,1)"
        self.lbl.setStyleSheet(
            f"color:{color}; font-family:'Segoe UI','Inter',sans-serif; font-size:10px; font-weight:{'700' if state else '500'}; letter-spacing:0.5px;"
        )

    def isChecked(self) -> bool:
        return self.btn.isChecked()


class TopToolbar(QWidget):
    """
    Full-width dedicated top bar.
    Left group  → Drawing tools (pencil, eraser, crayon, spray, shapes)
    Center group→ Color + Brush size
    Right group → Actions (undo, redo, save, clear, 3D, settings)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topToolbarBg")
        self.setFixedHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QWidget#topToolbarBg {
                background: rgba(12, 16, 25, 0.92);
                border-bottom: 1px solid rgba(255,255,255,0.10);
            }
        """)

        main = QHBoxLayout(self)
        main.setContentsMargins(20, 0, 20, 0)
        main.setSpacing(0)

        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icons"
        )

        def icon(name):
            return os.path.join(assets_dir, f"{name}.svg")

        # ── Drawing tools (left, checkable) ────────────────────────────
        drawing_tools = [
            ("pencil",     "Draw",   True),
            ("eraser",     "Eraser", True),
            ("crayon",     "Crayon", True),
            ("spray",      "Spray",  True),
            ("shapes",     "Shapes", True),
        ]
        self._checkable_widgets: list[ToolBtn] = []
        self.buttons = {}

        draw_grp = QHBoxLayout()
        draw_grp.setSpacing(4)
        for key, label, checkable in drawing_tools:
            w = ToolBtn(icon(key), label, checkable)
            w.btn.clicked.connect(lambda _, k=key, ww=w: self._on_draw_tool(k, ww))
            self.buttons[key] = w.btn
            draw_grp.addWidget(w)
            if checkable:
                self._checkable_widgets.append(w)
        main.addLayout(draw_grp)

        main.addWidget(_divider())

        # ── Color / Brush (center) ──────────────────────────────────────
        mid_tools = [
            ("color_wheel", "Color",      False),
            ("brush_size",  "Brush Size", False),
        ]
        mid_grp = QHBoxLayout()
        mid_grp.setSpacing(4)
        for key, label, checkable in mid_tools:
            w = ToolBtn(icon(key), label, checkable)
            w.btn.clicked.connect(lambda _, k=key: self._fire(k))
            self.buttons[key] = w.btn
            mid_grp.addWidget(w)
        main.addLayout(mid_grp)

        main.addStretch(1)   # push actions to far right

        main.addWidget(_divider())

        # ── Action tools (right, non-checkable) ────────────────────────
        action_tools = [
            ("undo",        "Undo",      False),
            ("redo",        "Redo",      False),
            ("save",        "Save",      False),
            ("clear",       "Clear",     False),
            ("convert_3d",  "3D",        False),
            ("settings",    "Settings",  False),
        ]
        act_grp = QHBoxLayout()
        act_grp.setSpacing(4)
        for key, label, checkable in action_tools:
            w = ToolBtn(icon(key), label, checkable)
            w.btn.clicked.connect(lambda _, k=key: self._fire(k))
            self.buttons[key] = w.btn
            act_grp.addWidget(w)
        main.addLayout(act_grp)

        # Select pencil by default
        self._select_draw("pencil")

    # ------------------------------------------------------------------
    def _on_draw_tool(self, key: str, widget: ToolBtn):
        """Ensure radio-button behaviour for drawing tools."""
        for w in self._checkable_widgets:
            w.setChecked(False)
            w.btn.setChecked(False)
        widget.setChecked(True)
        widget.btn.setChecked(True)
        self._fire(key)

    def _select_draw(self, key: str):
        for w in self._checkable_widgets:
            checked = (self.buttons[key] is w.btn)
            w.setChecked(checked)
            w.btn.setChecked(checked)

    def _fire(self, key: str):
        """Emit the clicked signal (used internally; main_window connects directly)."""
        pass   # signals wired externally via self.buttons[key].clicked
