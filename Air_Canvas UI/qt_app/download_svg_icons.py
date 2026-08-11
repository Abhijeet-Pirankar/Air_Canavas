import urllib.request
import os

icons = {
    "pencil": "pencil",
    "eraser": "eraser",
    "crayon": "paint-bucket",  # proxy for crayon
    "spray": "spray-can",
    "shapes": "box",
    "color_wheel": "palette",
    "brush_size": "ruler",
    "undo": "undo",
    "redo": "redo",
    "save": "save",
    "clear": "trash-2",
    "convert_3d": "cuboid",
    "settings": "settings",
    "layers": "layers",
    "eye": "eye",
    "eye_off": "eye-off",
    "lock": "lock",
    "plus": "plus"
}

base_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(base_dir, "assets", "icons")
os.makedirs(assets_dir, exist_ok=True)

for name, lucide_name in icons.items():
    url = f"https://unpkg.com/lucide-static@0.244.0/icons/{lucide_name}.svg"
    out_path = os.path.join(assets_dir, f"{name}.svg")
    try:
        urllib.request.urlretrieve(url, out_path)
        print(f"Downloaded {name}.svg")
    except Exception as e:
        print(f"Failed to download {name}.svg: {e}")
