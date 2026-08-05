import urllib.request
import os

icons = {
    "draw": "edit",
    "shapes": "rectangular",
    "color": "paint-palette",
    "brush": "paint-brush",
    "eraser": "eraser",
    "undo": "undo",
    "redo": "redo",
    "clear": "trash",
    "save": "save",
    "export_3d": "sugar-cube"
}

os.makedirs('assets/icons', exist_ok=True)
print("Downloading icons...")
for name, icon_id in icons.items():
    url = f"https://img.icons8.com/ios-filled/50/ffffff/{icon_id}.png"
    filepath = f"assets/icons/{name}.png"
    if not os.path.exists(filepath):
        print(f"Downloading {name}...")
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            print(f"Failed {name}: {e}")
print("Done.")
