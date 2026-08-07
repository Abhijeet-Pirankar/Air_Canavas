import urllib.request
import os

icons = {
    "draw": "270f",       # Pencil
    "eraser": "1f9fd",    # Sponge/Eraser
    "spray": "1f58c",     # Paintbrush (substitute for spray)
    "crayon": "1f58d",    # Crayon
    "shapes": "1f53a",    # Triangle shape
    "save": "1f4be",      # Floppy disk
    "export_3d": "1f9ca", # Ice cube
    "settings": "2699",   # Gear
    "undo": "21a9",       # Left curved arrow
    "redo": "21aa",       # Right curved arrow
    "clear": "1f5d1"      # Wastebasket
}

# The Twemoji repo is robust for emojis
base_url = "https://raw.githubusercontent.com/jdecked/twemoji/master/assets/72x72/"
icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
os.makedirs(icon_dir, exist_ok=True)

for name, code in icons.items():
    url = f"{base_url}{code}.png"
    out_path = os.path.join(icon_dir, f"{name}.png")
    try:
        urllib.request.urlretrieve(url, out_path)
        print(f"Downloaded {name}.png")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
