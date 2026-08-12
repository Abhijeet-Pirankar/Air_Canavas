"""
generate_icons.py
Generates crisp 64x64 RGBA PNG icons for Air Canvas Pro toolbar.
Icon style: Lucide/Feather — white stroke, 2px, round caps, transparent background.
Run once: python generate_icons.py
"""

from PIL import Image, ImageDraw
import os, math

ICON_SIZE = 64
STROKE = 2.5
WHITE = (220, 220, 220, 255)
ALPHA = (0, 0, 0, 0)
OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
os.makedirs(OUT_DIR, exist_ok=True)


def new_canvas():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), ALPHA)
    d = ImageDraw.Draw(img)
    return img, d


def save(img, name):
    path = os.path.join(OUT_DIR, f"{name}.png")
    img.save(path)
    print(f"  Saved: {path}")


def line(d, x0, y0, x1, y1, w=STROKE):
    d.line([(x0, y0), (x1, y1)], fill=WHITE, width=int(w))


def circle(d, cx, cy, r, w=STROKE):
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=WHITE, width=int(w))


def rect(d, x0, y0, x1, y1, r=4, w=STROKE):
    d.rounded_rectangle([(x0, y0), (x1, y1)], radius=r, outline=WHITE, width=int(w))


def arc(d, cx, cy, r, start, end, w=STROKE):
    bb = [(cx - r, cy - r), (cx + r, cy + r)]
    d.arc(bb, start=start, end=end, fill=WHITE, width=int(w))


# ── draw (pencil) ────────────────────────────────────────────────────────────
def icon_draw():
    img, d = new_canvas()
    # Pencil body
    pts = [(18, 46), (20, 34), (44, 10), (54, 20), (30, 44)]
    d.polygon(pts, outline=WHITE, width=int(STROKE))
    # Pencil tip
    line(d, 18, 46, 14, 50)
    line(d, 14, 50, 18, 46)
    # Middle line on pencil
    line(d, 24, 40, 42, 22, 1.5)
    save(img, "draw")


# ── eraser ───────────────────────────────────────────────────────────────────
def icon_eraser():
    img, d = new_canvas()
    # Eraser rectangle angled
    pts = [(12, 42), (26, 20), (52, 34), (38, 56)]
    d.polygon(pts, outline=WHITE, width=int(STROKE))
    # Eraser band
    line(d, 26, 20, 12, 42, STROKE)
    line(d, 32, 22, 18, 44, 1.5)
    # Base line
    line(d, 12, 54, 52, 54, STROKE)
    save(img, "eraser")


# ── spray (airbrush) ─────────────────────────────────────────────────────────
def icon_spray():
    img, d = new_canvas()
    # Nozzle body
    rect(d, 14, 28, 38, 50, r=4)
    # Nozzle tip
    line(d, 38, 36, 50, 36, STROKE)
    line(d, 50, 36, 50, 28, STROKE)
    # Spray dots
    dots = [(46, 16), (52, 22), (40, 14), (56, 30), (44, 22), (50, 12)]
    for x, y in dots:
        d.ellipse([(x-2, y-2), (x+2, y+2)], fill=WHITE)
    save(img, "spray")


# ── color_picker (color wheel) ───────────────────────────────────────────────
def icon_color_picker():
    img, d = new_canvas()
    # Outer ring
    circle(d, 32, 32, 20, STROKE)
    # Inner circle
    circle(d, 32, 32, 6, STROKE)
    # 6 color segment lines
    for i in range(6):
        angle = math.radians(i * 60)
        x1 = 32 + 8 * math.cos(angle)
        y1 = 32 + 8 * math.sin(angle)
        x2 = 32 + 19 * math.cos(angle)
        y2 = 32 + 19 * math.sin(angle)
        line(d, x1, y1, x2, y2, 1.5)
    save(img, "color_picker")


# ── crayon (thick drawing tool) ──────────────────────────────────────────────
def icon_crayon():
    img, d = new_canvas()
    # Crayon body
    pts = [(16, 48), (22, 36), (44, 14), (50, 20), (28, 42)]
    d.polygon(pts, outline=WHITE, width=int(STROKE))
    # Crayon tip (flat/rounded)
    arc(d, 16, 48, 6, 45, 225, STROKE)
    line(d, 12, 44, 20, 52, STROKE)
    # Wrapper lines
    line(d, 26, 32, 32, 38, 1.5)
    line(d, 40, 18, 46, 24, 1.5)
    save(img, "crayon")


# ── shapes ───────────────────────────────────────────────────────────────────
def icon_shapes():
    img, d = new_canvas()
    # Square (top-left)
    rect(d, 10, 10, 30, 30, r=3)
    # Triangle (bottom-right)
    pts = [(34, 54), (54, 54), (44, 36)]
    d.polygon(pts, outline=WHITE, width=int(STROKE))
    # Circle (bottom-left)
    circle(d, 20, 44, 9, STROKE)
    save(img, "shapes")


# ── undo ─────────────────────────────────────────────────────────────────────
def icon_undo():
    img, d = new_canvas()
    # Arc (CCW arrow)
    arc(d, 32, 34, 18, 190, 360, STROKE)
    arc(d, 32, 34, 18, 0,   40,  STROKE)
    # Arrowhead at start
    line(d, 14, 34, 10, 26, STROKE)
    line(d, 14, 34, 22, 28, STROKE)
    save(img, "undo")


# ── redo ─────────────────────────────────────────────────────────────────────
def icon_redo():
    img, d = new_canvas()
    # Arc (CW arrow)
    arc(d, 32, 34, 18, 140, 360, STROKE)
    arc(d, 32, 34, 18, 0,   10,  STROKE)
    # Arrowhead at end
    line(d, 50, 34, 54, 26, STROKE)
    line(d, 50, 34, 42, 28, STROKE)
    save(img, "redo")


# ── clear ────────────────────────────────────────────────────────────────────
def icon_clear():
    img, d = new_canvas()
    # Trash can body
    rect(d, 16, 22, 48, 54, r=3)
    # Lid
    line(d, 10, 22, 54, 22, STROKE)
    # Handle
    rect(d, 24, 14, 40, 22, r=2)
    # Inner lines
    line(d, 24, 30, 24, 46, 1.5)
    line(d, 32, 30, 32, 46, 1.5)
    line(d, 40, 30, 40, 46, 1.5)
    save(img, "clear")


# ── save ─────────────────────────────────────────────────────────────────────
def icon_save():
    img, d = new_canvas()
    # Floppy disk body
    rect(d, 10, 10, 54, 54, r=3)
    # Label area
    rect(d, 18, 10, 46, 28, r=2)
    # Bottom storage slot
    rect(d, 18, 36, 46, 52, r=2)
    # Slot notch
    line(d, 36, 10, 36, 28, STROKE)
    save(img, "save")


# ── export_3d ────────────────────────────────────────────────────────────────
def icon_export_3d():
    img, d = new_canvas()
    # Cube wireframe (isometric-ish)
    # Top face
    top = [(32, 10), (52, 22), (32, 34), (12, 22)]
    d.polygon(top, outline=WHITE, width=int(STROKE))
    # Left face
    left = [(12, 22), (32, 34), (32, 54), (12, 42)]
    d.polygon(left, outline=WHITE, width=int(STROKE))
    # Right face
    right = [(52, 22), (52, 42), (32, 54), (32, 34)]
    d.polygon(right, outline=WHITE, width=int(STROKE))
    save(img, "export_3d")


if __name__ == "__main__":
    print("Generating Air Canvas Pro icons...")
    icon_draw()
    icon_eraser()
    icon_spray()
    icon_crayon()
    icon_color_picker()
    icon_shapes()
    icon_undo()
    icon_redo()
    icon_clear()
    icon_save()
    icon_export_3d()
    print("Done! All icons saved to assets/icons/")
