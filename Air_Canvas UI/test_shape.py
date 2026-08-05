import numpy as np
import cv2
from air_canvas_pro.core.shape_ai import ShapeAI

img = np.zeros((720, 1280, 3), dtype=np.uint8)
shape_ai = ShapeAI()

# Feed it a circle
for i in range(36):
    angle = i * 10 * np.pi / 180
    x = int(640 + 100 * np.cos(angle))
    y = int(360 + 100 * np.sin(angle))
    shape_ai.add_point((x, y))

res = shape_ai.process_stroke(img, (255, 255, 255), 5)
print("Process stroke returned:", res)
print("Image sum:", np.sum(img))
