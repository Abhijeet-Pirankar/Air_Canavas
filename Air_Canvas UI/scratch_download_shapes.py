import urllib.request
import os

icons = {
    "shapes": "rectangle"
}

for name, icon_id in icons.items():
    url = f"https://img.icons8.com/ios-filled/50/ffffff/{icon_id}.png"
    filepath = f"assets/icons/{name}.png"
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"Downloaded {name}")
    except Exception as e:
        print(f"Failed {name}: {e}")
