import cv2
import mediapipe as mp
import numpy as np
import random
import json
import os
import webbrowser
import threading
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTTP_PORT = 8000
_http_server = None

def create_toolbar(width=640, height=90):
    toolbar = np.full((height, width, 3), (30, 30, 42), np.uint8)
    labels = ["DRAW", "ERASE", "SPRAY", "CRAYON", "COLOR", "SIZE", "SAVE"]
    section_w = width // len(labels)
    for i, label in enumerate(labels):
        x1 = i * section_w
        x2 = x1 + section_w - 1
        cv2.rectangle(toolbar, (x1 + 4, 4), (x2 - 4, height - 4), (45, 45, 58), -1)
        cv2.rectangle(toolbar, (x1 + 4, 4), (x2 - 4, height - 4), (80, 80, 95), 1)
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
        tx = x1 + (section_w - text_size[0]) // 2
        ty = (height + text_size[1]) // 2
        cv2.putText(toolbar, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
    return toolbar

def start_http_server():
    global _http_server
    if _http_server is not None:
        return
    handler = functools.partial(SimpleHTTPRequestHandler, directory=BASE_DIR)
    _http_server = HTTPServer(("localhost", HTTP_PORT), handler)
    threading.Thread(target=_http_server.serve_forever, daemon=True).start()
    print(f"Serving 3D viewer at http://localhost:{HTTP_PORT}/")

def show_save_popup(filename):
    popup = np.full((480, 640, 3), (18, 18, 25), np.uint8)
    while True:
        popup[:] =(18, 18, 25)
        cv2.putText(popup, "IMAGE SAVED", (170, 140),cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 180), 3, cv2.LINE_AA)
        cv2.putText(popup, filename, (180, 195),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2, cv2.LINE_AA)
        cv2.putText(popup, "Press 3 to Convert to 3D", (150, 285),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2, cv2.LINE_AA)
        cv2.putText(popup, "Press Q to Quit", (220, 340),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 210), 2, cv2.LINE_AA)
        cv2.imshow("Saved", popup)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('3'):
            cv2.destroyWindow("Saved")
            return "convert_3d"
        elif key == ord('q'):
            cv2.destroyWindow("Saved")
            return "quit"
def extract_contour_points(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No visible drawing found.")
        return None
    contour = max(contours, key=cv2.contourArea)
    epsilon = 0.002 * cv2.arcLength(contour, True)
    contour = cv2.approxPolyDP(contour, epsilon, True)
    points = []
    for pt in contour:
        x, y = pt[0]
        points.append((x, y))
    print(f"Extracted {len(points)} final visible contour points.")
    return points
def export_points_to_json(points, filename=None):
    if points is None or len(points) < 3:
        print("Not enough points to convert to 3D.")
        return False
    if filename is None:
        filename = os.path.join(BASE_DIR, "points.json")
    data = [{"x": int(x), "y": int(y)} for x, y in points]
    with open(filename, "w") as f:
        json.dump(data, f)
    print(f"Saved {len(points)} points to {filename}")
    return True

def open_3d_viewer():
    start_http_server()
    webbrowser.open(f"http://localhost:{HTTP_PORT}/viewer.html")
cap = cv2.VideoCapture(0)
model_path = os.path.join(BASE_DIR, 'hand_landmarker.task')
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
hands = vision.HandLandmarker.create_from_options(options)
DARK_BG = (18, 18, 25)
drawing_layer = np.zeros((480, 640, 3), np.uint8)
toolbar_height = 90
toolbar_path = os.path.join(BASE_DIR, "toolbar.png")
toolbar_img = cv2.imread(toolbar_path)
if toolbar_img is None:
    print("toolbar.png not found — using built-in toolbar.")
    toolbar_img = create_toolbar(640, toolbar_height)
else:
    toolbar_img = cv2.resize(toolbar_img, (640, toolbar_height))
tool = "draw"
draw_color = (80, 180, 255)
brush_thickness = 8
eraser_thickness = 35
xp, yp = 0, 0
save_count = 0
zoom = 1.0
zoom_min, zoom_max = 0.6, 2.5
prev_zoom_dist = 0
show_size_slider = False
smooth_x, smooth_y = 0, 0
smoothening = 0.35
running = True
palette_colors = [(0, 0, 255), (0, 165, 255), (0, 255, 255),(0, 255, 0), (255, 255, 0), (255, 0, 0),(255, 0, 255), (255, 255, 255)]
def get_zoom_view(layer, zoom_value):
    h, w = layer.shape[:2]
    new_w = int(w / zoom_value)
    new_h = int(h / zoom_value)
    cx, cy = w // 2, h // 2
    x_start = max(0, cx - new_w // 2)
    y_start = max(0, cy - new_h // 2)
    x_end = min(w, x_start + new_w)
    y_end = min(h, y_start + new_h)
    cropped = layer[y_start:y_end, x_start:x_end]
    zoomed = cv2.resize(cropped, (w, h))
    return zoomed, x_start, y_start, new_w, new_h
while running:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    img = cv2.resize(img, (640, 480))
    img_display = img.copy()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
    detection_result = hands.detect(mp_image)
    lmList = []
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            for idx, lm in enumerate(hand_landmarks):
                h, w, _ = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((idx, cx, cy))
    zoomed_layer, crop_x, crop_y, crop_w, crop_h = get_zoom_view(drawing_layer, zoom)
    if lmList:
        index_up = lmList[8][2] < lmList[6][2]
        middle_up = lmList[12][2] < lmList[10][2]
        ring_up = lmList[16][2] < lmList[14][2]
        raw_x, raw_y = lmList[8][1], lmList[8][2]
        if smooth_x == 0 and smooth_y == 0:
            smooth_x, smooth_y = raw_x, raw_y
        smooth_x = int(smooth_x + smoothening * (raw_x - smooth_x))
        smooth_y = int(smooth_y + smoothening * (raw_y - smooth_y))
        x1, y1 = smooth_x, smooth_y
        canvas_x = int(crop_x + (x1 / 640) * crop_w)
        canvas_y = int(crop_y + (y1 / 480) * crop_h)
        # ---------- Zoom Gesture ----------
        if index_up and middle_up and ring_up and y1 > toolbar_height + 20:
            x_thumb, y_thumb = lmList[4][1], lmList[4][2]
            x_index, y_index = lmList[8][1], lmList[8][2]
            zoom_dist = ((x_index - x_thumb) ** 2 + (y_index - y_thumb) ** 2) ** 0.5
            if prev_zoom_dist != 0:
                delta = zoom_dist - prev_zoom_dist
                if abs(delta) > 4:
                    zoom += delta * 0.0025
                    zoom = max(zoom_min, min(zoom_max, zoom))
            prev_zoom_dist = zoom_dist
            cv2.putText(img_display, f"Zoom: {zoom:.1f}x", (20, 140),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2)
        else:
            prev_zoom_dist = 0
        # ---------- Selection Mode ----------
        if index_up and middle_up and not ring_up:
            xp, yp = 0, 0
            if y1 < toolbar_height:
                section = x1 // 91
                if section == 0:
                    tool = "draw"
                    show_size_slider = False
                elif section == 1:
                    tool = "eraser"
                    show_size_slider = False
                elif section == 2:
                    tool = "spray"
                    show_size_slider = False
                elif section == 3:
                    tool = "crayon"
                    show_size_slider = False
                elif section == 4:
                    tool = "color"
                    show_size_slider = False
                elif section == 5:
                    tool = "size"
                    show_size_slider = True
                elif section == 6:
                    filename = os.path.join(BASE_DIR, f"aircanvas_{save_count}.png")
                    save_img = np.full((480, 640, 3), DARK_BG, np.uint8)
                    save_img = cv2.add(save_img, drawing_layer)
                    cv2.imwrite(filename, save_img)
                    print(f"Saved: {filename}")
                    save_count += 1
                    result = show_save_popup(filename)
                    if result == "convert_3d":
                        contour_points = extract_contour_points(drawing_layer)
                        if contour_points is not None:
                            saved = export_points_to_json(contour_points)
                            if saved:
                                open_3d_viewer()
                    elif result == "quit":
                        running = False
                        break
                    tool = "draw"
                    show_size_slider = False
            # ---------- Color Palette ----------
            if tool == "color":
                start_x, start_y = 120, toolbar_height + 20
                box = 45
                for i, color in enumerate(palette_colors):
                    xs = start_x + i * (box + 8)
                    ys = start_y
                    xe = xs + box
                    ye = ys + box
                    cv2.rectangle(img_display, (xs, ys), (xe, ye), color, -1)
                    cv2.rectangle(img_display, (xs, ys), (xe, ye), (230, 230, 230), 2)
                    if xs < x1 < xe and ys < y1 < ye:
                        draw_color = color
                        tool = "draw"
        # ---------- Size Slider ----------
        if show_size_slider:
            slider_x = 600
            slider_top = 120
            slider_bottom = 390
            cv2.rectangle(img_display, (570, slider_top - 20),(630, slider_bottom + 20), (30, 30, 42), -1)
            cv2.line(img_display, (slider_x, slider_top),(slider_x, slider_bottom), (180, 180, 190), 5)
            knob_y = int(slider_bottom - ((brush_thickness - 2) / 28) * (slider_bottom - slider_top))
            cv2.circle(img_display, (slider_x, knob_y), 15, (0, 255, 180), -1)
            cv2.putText(img_display, "SIZE", (570, slider_top - 35),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 2)
            if tool == "size" and index_up and 550 < x1 < 640 and slider_top < y1 < slider_bottom:
                brush_thickness = int(np.interp(y1, [slider_bottom, slider_top], [2, 30]))
        # ---------- Drawing Mode ----------
        elif index_up and not middle_up and tool != "size":
            if y1 > toolbar_height:
                if tool == "draw":
                    if xp == 0 and yp == 0:
                        xp, yp = canvas_x, canvas_y
                    steps = 8
                    for i in range(steps + 1):
                        xi = int(xp + (canvas_x - xp) * i / steps)
                        yi = int(yp + (canvas_y - yp) * i / steps)
                        cv2.circle(drawing_layer, (xi, yi),max(1, brush_thickness // 2),draw_color, -1)
                    xp, yp = canvas_x, canvas_y
                elif tool == "eraser":
                    if xp == 0 and yp == 0:
                        xp, yp = canvas_x, canvas_y
                    cv2.line(drawing_layer, (xp, yp), (canvas_x, canvas_y),(0, 0, 0), eraser_thickness)
                    xp, yp = canvas_x, canvas_y
                elif tool == "spray":
                    xp, yp = 0, 0
                    for _ in range(25):
                        ox = random.randint(-brush_thickness, brush_thickness)
                        oy = random.randint(-brush_thickness, brush_thickness)
                        sx, sy = canvas_x + ox, canvas_y + oy
                        if 0 <= sx < 640 and 0 <= sy < 480:
                            cv2.circle(drawing_layer, (sx, sy), 1, draw_color, -1)
                elif tool == "crayon":
                    if xp == 0 and yp == 0:
                        xp, yp = canvas_x, canvas_y
                    for _ in range(5):
                        jx1 = xp + random.randint(-3, 3)
                        jy1 = yp + random.randint(-3, 3)
                        jx2 = canvas_x + random.randint(-3, 3)
                        jy2 = canvas_y + random.randint(-3, 3)
                        cv2.line(drawing_layer, (jx1, jy1), (jx2, jy2),draw_color, max(1, brush_thickness // 3))
                    xp, yp = canvas_x, canvas_y
        else:
            xp, yp = 0, 0
    else:
        xp, yp = 0, 0
        smooth_x, smooth_y = 0, 0
    # ---------- Display ----------
    img_display = cv2.add(img_display, zoomed_layer)
    img_display[0:toolbar_height, 0:640] = toolbar_img
    if lmList:
        cv2.circle(img_display, (x1, y1), 18, draw_color, 2)
        cv2.circle(img_display, (x1, y1), 7, draw_color, -1)
    overlay = img_display.copy()
    cv2.rectangle(overlay, (10, 425), (630, 475), (22, 22, 34), -1)
    img_display = cv2.addWeighted(overlay, 0.7, img_display, 0.3, 0)
    cv2.putText(img_display, f"TOOL: {tool.upper()}", (25, 457),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
    cv2.putText(img_display, f"SIZE: {brush_thickness}", (260, 457),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
    cv2.putText(img_display, f"ZOOM: {zoom:.1f}x", (410, 457),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
    cv2.circle(img_display, (585, 452), 17, draw_color, -1)
    cv2.circle(img_display, (585, 452), 20, (230, 230, 230), 2)
    cv2.imshow("Air Canvas Pro", img_display)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    if key == ord('r'):
        drawing_layer = np.zeros((480, 640, 3), np.uint8)
        xp, yp = 0, 0
        zoom = 1.0
        tool = "draw"
        show_size_slider = False
        print("Canvas reset.")
    if key == ord('3'):
        contour_points = extract_contour_points(drawing_layer)
        if contour_points is not None:
            saved = export_points_to_json(contour_points)

            if saved:
                open_3d_viewer()

cap.release()
hands.close()
cv2.destroyAllWindows()
if _http_server is not None:
    _http_server.shutdown()
