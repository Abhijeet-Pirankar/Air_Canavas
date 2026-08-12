import cv2
import time
import math
import numpy as np
import os
from air_canvas_pro.ui.theme import Theme


class Toolbar:
    """
    Premium floating toolbar with per-button glassmorphism.
    Visual design: Figma + Photoshop + Apple Vision Pro aesthetic.
    """

    # Layout constants
    BTN_SIZE   = 52          # Square button side (px)
    BTN_RADIUS = 14          # Rounded corner radius
    BTN_GAP    = 16          # Gap between buttons
    MARGIN_TOP = 20          # Distance from top edge
    MARGIN_H   = 40          # Left/right outer margin from canvas edges
    PAD_V      = 14          # Vertical padding inside the toolbar container
    PAD_H      = 16          # Horizontal padding inside the toolbar container
    ICON_SIZE  = 26          # Icon render size (px)

    # Glassmorphism palette (BGR)
    # Glass buttons use addWeighted with low overlay weight for true translucency
    GLASS_BTN_NORMAL  = (52, 42, 38)     # Dark tinted glass base
    GLASS_BTN_HOVER   = (72, 62, 56)     # Slightly brighter on hover
    GLASS_BTN_ACTIVE  = (65, 55, 50)     # Active state base
    BORDER_NORMAL     = (80, 75, 72)     # rgba(255,255,255,0.12) equivalent
    BORDER_ACTIVE     = (255, 229, 0)    # Cyan #00E5FF in BGR
    BORDER_HOVER      = (120, 110, 105)  # Brighter border on hover
    ICON_DEFAULT      = (205, 205, 208)  # Light gray — never black
    ICON_ACTIVE       = (255, 229, 0)    # Cyan
    ICON_HOVER        = (240, 240, 242)  # Near-white on hover
    GLOW_CYAN         = (180, 155,  10)  # Soft cyan glow (BGR)

    def __init__(self, width=1280, height=720):
        self.width  = width
        self.height = height

        self.tools = [
            "draw", "eraser", "spray", "crayon", "color_picker",
            "shapes", "undo", "redo", "clear", "save", "export_3d"
        ]
        self.active_tool = "draw"

        self.is_visible       = True
        self.last_interaction = time.time()

        # Hover / dwell state
        self.hover_idx    = -1
        self.dwell_start  = None
        self.DWELL_TIME   = 0.4

        # Smooth hover scale animation
        self._hover_scales = [1.0] * len(self.tools)
        self._last_tick    = time.time()

        self.tooltips = {
            "draw":      "Draw",
            "eraser":    "Eraser",
            "spray":     "Airbrush",
            "crayon":    "Crayon",
            "color_picker": "Colors",
            "shapes":    "Shapes",
            "undo":      "Undo",
            "redo":      "Redo",
            "clear":     "Clear",
            "save":      "Save",
            "export_3d": "3D Export",
        }

        # Load icons (RGBA PNGs) — load at native size, then downscale for crispness
        self.icons = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_dir = os.path.join(base_dir, "assets", "icons")
        for t in self.tools:
            path = os.path.join(icon_dir, f"{t}.png")
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if len(img.shape) == 3 and img.shape[2] == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                    elif len(img.shape) == 2:
                        # Grayscale — convert to BGRA
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                    # Downscale with AREA for maximum anti-aliasing quality
                    img = cv2.resize(img, (self.ICON_SIZE, self.ICON_SIZE),
                                     interpolation=cv2.INTER_AREA)
                    self.icons[t] = img

        # Compute layout geometry
        self._compute_layout()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _compute_layout(self):
        """Compute per-button bounding boxes and toolbar container rect."""
        n = len(self.tools)
        total_btns_w    = n * self.BTN_SIZE + (n - 1) * self.BTN_GAP
        toolbar_inner_w = total_btns_w + 2 * self.PAD_H
        toolbar_h       = self.BTN_SIZE + 2 * self.PAD_V

        # Center the toolbar horizontally
        cx = self.width // 2
        self.panel_x1 = cx - toolbar_inner_w // 2
        self.panel_x2 = cx + toolbar_inner_w // 2
        self.panel_y1 = self.MARGIN_TOP
        self.panel_y2 = self.MARGIN_TOP + toolbar_h

        # Per-button bounding boxes (evenly distributed)
        self.btn_rects = []
        for i in range(n):
            bx = self.panel_x1 + self.PAD_H + i * (self.BTN_SIZE + self.BTN_GAP)
            by = self.panel_y1 + self.PAD_V
            self.btn_rects.append((bx, by, bx + self.BTN_SIZE, by + self.BTN_SIZE))

        # Compatibility aliases used by air_canvas.py drawing guard
        self.margin_top  = self.panel_y1
        self.margin_side = self.panel_x1
        self.panel_h     = toolbar_h

    # ------------------------------------------------------------------
    # Hit testing
    # ------------------------------------------------------------------

    def hit_test(self, x, y):
        self.last_interaction = time.time()
        for i, (bx1, by1, bx2, by2) in enumerate(self.btn_rects):
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return i
        return -1

    # ------------------------------------------------------------------
    # Update (dwell selection — unchanged logic)
    # ------------------------------------------------------------------

    def update(self, x, y, is_selecting):
        if is_selecting:
            idx = self.hit_test(x, y)
            if idx != -1:
                if self.hover_idx != idx:
                    self.hover_idx   = idx
                    self.dwell_start = time.time()
                elif self.dwell_start and time.time() - self.dwell_start > self.DWELL_TIME:
                    selected = self.tools[idx]
                    if selected not in ["undo", "redo", "clear", "save", "export_3d", "color_picker"]:
                        self.active_tool = selected
                    if not getattr(self, '_triggered_idx', None) == idx:
                        self._triggered_idx = idx
                        return selected
                    return None
            else:
                self.hover_idx      = -1
                self.dwell_start    = None
                self._triggered_idx = None
        else:
            self.hover_idx      = -1
            self.dwell_start    = None
            self._triggered_idx = None
        return None

    # ------------------------------------------------------------------
    # Per-button glass panel
    # ------------------------------------------------------------------

    def _draw_glass_button(self, frame, bx1, by1, bx2, by2,
                            bg_color, border_color, border_thickness=1,
                            glass_alpha=0.14, glow_color=None):
        """
        Render a single glassmorphism button.

        glass_alpha: how much of the DARK FILL is blended in (0.10–0.22).
                     Lower = more transparent (camera shows through more).
                     Higher = more opaque dark glass.
        The camera feed always remains the dominant layer.
        """
        fh, fw = frame.shape[:2]
        x1 = max(0, int(bx1))
        y1 = max(0, int(by1))
        x2 = min(fw, int(bx2))
        y2 = min(fh, int(by2))
        if x2 <= x1 or y2 <= y1:
            return

        # ── Soft drop shadow (elevation effect below button) ─────────
        shadow_offset = 3
        shadow = frame.copy()
        Theme.draw_rounded_rect(
            shadow,
            (x1 + shadow_offset, y1 + shadow_offset),
            (x2 + shadow_offset, y2 + shadow_offset),
            (10, 8, 7), -1, self.BTN_RADIUS
        )
        cv2.addWeighted(shadow, 0.30, frame, 0.70, 0, frame)

        # ── Outer soft glow (active = cyan, hover = faint cyan) ──────
        if glow_color is not None:
            glow = frame.copy()
            for spread in (8, 5, 3):
                Theme.draw_rounded_rect(
                    glow,
                    (x1 - spread, y1 - spread),
                    (x2 + spread, y2 + spread),
                    glow_color, 1, self.BTN_RADIUS + spread
                )
            cv2.addWeighted(glow, 0.22, frame, 0.78, 0, frame)

        # ── True glass fill — low alpha so camera shows through ──────
        overlay = frame.copy()
        Theme.draw_rounded_rect(overlay, (x1, y1), (x2, y2), bg_color, -1, self.BTN_RADIUS)

        # Inner top highlight — 1/5 height, lighter strip (glass sheen)
        hl_color = tuple(min(255, c + 35) for c in bg_color)
        hl_h = max(3, (y2 - y1) // 5)
        Theme.draw_rounded_rect(
            overlay,
            (x1 + 3, y1 + 2), (x2 - 3, y1 + hl_h),
            hl_color, -1, self.BTN_RADIUS
        )

        # Blend: glass_alpha controls glass opacity (0.10–0.22 recommended)
        cv2.addWeighted(overlay, glass_alpha, frame, 1.0 - glass_alpha, 0, frame)

        # ── Border ───────────────────────────────────────────────────
        Theme.draw_rounded_rect(
            frame, (x1, y1), (x2, y2),
            border_color, border_thickness, self.BTN_RADIUS
        )

    # ------------------------------------------------------------------
    # Icon blitting with tint
    # ------------------------------------------------------------------

    def _draw_icon_centered(self, frame, tool, cx, cy, tint_color,
                             scale=1.0, color_dot=None):
        """Blit an RGBA icon centered at (cx, cy) with single-color tint."""
        if tool not in self.icons:
            return

        icon = self.icons[tool].copy()

        # Tint non-transparent pixels
        alpha_mask = icon[:, :, 3] > 20
        icon[alpha_mask, 0] = tint_color[0]
        icon[alpha_mask, 1] = tint_color[1]
        icon[alpha_mask, 2] = tint_color[2]

        # Scale animation
        if abs(scale - 1.0) > 0.005:
            h_i, w_i = icon.shape[:2]
            new_w = max(1, int(w_i * scale))
            new_h = max(1, int(h_i * scale))
            icon  = cv2.resize(icon, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        h_i, w_i = icon.shape[:2]
        top  = int(cy - h_i // 2)
        left = int(cx - w_i // 2)

        fh, fw = frame.shape[:2]
        if top < 0 or left < 0 or top + h_i > fh or left + w_i > fw:
            return

        roi = frame[top:top + h_i, left:left + w_i]
        a   = icon[:, :, 3:4].astype(np.float32) / 255.0
        for c in range(3):
            roi[:, :, c] = (
                a[:, :, 0] * icon[:, :, c]
                + (1 - a[:, :, 0]) * roi[:, :, c]
            ).astype(np.uint8)

        # Small glowing color indicator dot (palette/crayon tool)
        if color_dot is not None:
            dot_r = 5
            dot_x = int(cx + w_i // 2 - dot_r - 1)
            dot_y = int(cy + h_i // 2 - dot_r - 1)
            cv2.circle(frame, (dot_x, dot_y), dot_r, color_dot, -1)
            cv2.circle(frame, (dot_x, dot_y), dot_r + 1, (200, 200, 200), 1)

    # ------------------------------------------------------------------
    # Smooth hover animation tick
    # ------------------------------------------------------------------

    def _tick_animations(self):
        now = time.time()
        dt  = min(now - self._last_tick, 0.05)
        self._last_tick = now
        speed = 9.0
        for i in range(len(self.tools)):
            target = 1.14 if i == self.hover_idx else 1.0
            self._hover_scales[i] += (target - self._hover_scales[i]) * speed * dt

    # ------------------------------------------------------------------
    # Main render
    # ------------------------------------------------------------------

    def render(self, frame, active_draw_color=None):
        """
        Render the premium floating toolbar.

        Parameters
        ----------
        frame            : np.ndarray  — display frame (modified in place)
        active_draw_color: tuple (BGR) — current drawing color for palette dot
        """
        self._tick_animations()

        # ── Toolbar container drop shadow ─────────────────────────────
        s_off = 4
        shadow_c = frame.copy()
        Theme.draw_rounded_rect(
            shadow_c,
            (self.panel_x1 - 2 + s_off, self.panel_y1 - 2 + s_off),
            (self.panel_x2 + 2 + s_off, self.panel_y2 + 2 + s_off),
            (8, 6, 5), -1, radius=22
        )
        cv2.addWeighted(shadow_c, 0.40, frame, 0.60, 0, frame)

        # ── Toolbar container (dark glass pill) ───────────────────────
        # Uses 0.55 opacity: dock is more visible than individual buttons
        Theme.draw_glass_panel(
            frame,
            self.panel_x1 - 2, self.panel_y1 - 2,
            self.panel_x2 + 2, self.panel_y2 + 2,
            alpha=0.55, radius=22
        )
        # Thin white outer border (rgba(255,255,255,0.18))
        Theme.draw_rounded_rect(
            frame,
            (self.panel_x1 - 2, self.panel_y1 - 2),
            (self.panel_x2 + 2, self.panel_y2 + 2),
            (100, 95, 92), 1, radius=22
        )

        # ── Individual glass buttons ──────────────────────────────────
        for i, tool in enumerate(self.tools):
            bx1, by1, bx2, by2 = self.btn_rects[i]
            cx = (bx1 + bx2) // 2
            cy = (by1 + by2) // 2

            is_active = (tool == self.active_tool)
            is_hover  = (i == self.hover_idx)
            scale     = self._hover_scales[i]

            # ── Visual state ─────────────────────────────────────────
            if is_active:
                bg_color     = self.GLASS_BTN_ACTIVE
                border_color = self.BORDER_ACTIVE
                border_thick = 2
                icon_color   = self.ICON_ACTIVE
                glass_alpha  = 0.20   # Slightly more visible active glass
                glow         = self.GLOW_CYAN
            elif is_hover:
                bg_color     = self.GLASS_BTN_HOVER
                border_color = self.BORDER_HOVER
                border_thick = 1
                icon_color   = self.ICON_HOVER
                glass_alpha  = 0.16   # Hover: slightly brighter glass
                glow         = (100, 90, 5)   # Very faint cyan glow
            else:
                bg_color     = self.GLASS_BTN_NORMAL
                border_color = self.BORDER_NORMAL
                border_thick = 1
                icon_color   = self.ICON_DEFAULT
                glass_alpha  = 0.12   # Normal: mostly transparent, spec-compliant
                glow         = None

            self._draw_glass_button(
                frame, bx1, by1, bx2, by2,
                bg_color, border_color, border_thick,
                glass_alpha=glass_alpha,
                glow_color=glow
            )

            # Color dot only on color picker tool
            color_dot = active_draw_color if tool == "color_picker" else None

            self._draw_icon_centered(
                frame, tool, cx, cy, icon_color,
                scale=scale, color_dot=color_dot
            )

            # Tooltip (shown below toolbar container)
            if is_hover:
                Theme.draw_tooltip(
                    frame, self.tooltips.get(tool, tool),
                    cx, self.panel_y2 + 10
                )

        # ── Dwell progress arc ────────────────────────────────────────
        if self.hover_idx != -1 and self.dwell_start is not None:
            elapsed  = time.time() - self.dwell_start
            progress = min(1.0, elapsed / self.DWELL_TIME)
            if 0.05 < progress < 1.0:
                bx1, by1, bx2, by2 = self.btn_rects[self.hover_idx]
                cx_arc = (int(bx1) + int(bx2)) // 2
                cy_arc = (int(by1) + int(by2)) // 2
                r_arc  = self.BTN_SIZE // 2 - 3
                end_angle = int(-90 + 360 * progress)
                cv2.ellipse(
                    frame, (cx_arc, cy_arc), (r_arc, r_arc),
                    0, -90, end_angle, self.BORDER_ACTIVE, 2
                )
