import cv2
import os
import sys
import random
import numpy as np

# Add project root to sys path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from air_canvas_pro.core.hand_tracking import HandTracker
from air_canvas_pro.core.canvas_manager import CanvasManager
from air_canvas_pro.core.shape_ai import ShapeAI
from air_canvas_pro.ui.toolbar import Toolbar
from air_canvas_pro.ui.color_picker import ColorPicker
from air_canvas_pro.ui.dashboard import Dashboard
from air_canvas_pro.ui.theme import Theme
from air_canvas_pro.utils.export_engine import ExportEngine
from air_canvas_pro.ui.radial_menu import RadialMenu

def main():
    # Setup Window
    CANVAS_W, CANVAS_H = 1280, 720
    cv2.namedWindow("Air Canvas Pro", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Air Canvas Pro", CANVAS_W, CANVAS_H)

    # Initialize Modules
    model_path = os.path.join(BASE_DIR, 'hand_landmarker.task')
    tracker = HandTracker(model_path)
    canvas = CanvasManager(CANVAS_W, CANVAS_H)
    canvas.show_grid = False
    shape_ai = ShapeAI()
    
    toolbar = Toolbar(CANVAS_W, CANVAS_H)
    color_picker = ColorPicker(80)
    dashboard = Dashboard(CANVAS_W, CANVAS_H)
    radial_menu = RadialMenu()
    exporter = ExportEngine(BASE_DIR)

    # State
    brush_size = 10
    eraser_size = 40
    color = Theme.CYAN
    xp, yp = 0, 0
    running = True

    # Image Enhancement (Gentle CLAHE for natural look)
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8,8))

    cap = cv2.VideoCapture(0)
    # Try to request higher resolution from camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while running:
        success, img = cap.read()
        if not success:
            break
            
        img = cv2.flip(img, 1)
        img = cv2.resize(img, (CANVAS_W, CANVAS_H))
        
        # --- Image Enhancement Pipeline ---
        # 1. Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        
        # 2. Apply Gentle CLAHE to L channel for balanced exposure
        l_channel = clahe.apply(l_channel)
        
        # 3. Merge back to BGR
        enhanced_lab = cv2.merge((l_channel, a, b))
        img_enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # 4. Enhance Brightness and Contrast (Very subtle, no overexposure)
        img_enhanced = cv2.convertScaleAbs(img_enhanced, alpha=1.05, beta=0)
        # ----------------------------------
        
        # Display the enhanced camera feed directly (feels like original camera)
        img_display = img_enhanced.copy()
        
        # Grid
        canvas.draw_grid(img_display)

        # Process Hands (Unmodified image to preserve MediaPipe performance and accuracy)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        lmList = tracker.process_frame(img_rgb)
        
        is_drawing = False
        is_selecting = False
        
        if lmList:
            # Gesture detection
            index_up = lmList[8][2] < lmList[6][2]
            middle_up = lmList[12][2] < lmList[10][2]
            
            raw_x, raw_y = lmList[8][1], lmList[8][2]
            x1, y1 = tracker.get_filtered_index(raw_x, raw_y)
            x1 = max(0, min(CANVAS_W - 1, x1))
            y1 = max(0, min(CANVAS_H - 1, y1))
            
            is_selecting = (index_up and middle_up)
            is_drawing = (index_up and not middle_up)
            
            # Draw cursor
            import time # ensure time is available for sin wave
            cursor_color = Theme.WHITE if is_selecting else color
            cv2.circle(img_display, (x1, y1), 6, cursor_color, -1)
            if is_selecting:
                pulse_r = 16 + int(5 * np.sin(time.time() * 10))
                cv2.circle(img_display, (x1, y1), pulse_r, Theme.CYAN, 2)
            else:
                cv2.circle(img_display, (x1, y1), 12, cursor_color, 1)
            
            # --- UI Interactions ---
            if radial_menu.is_active:
                action = radial_menu.update(x1, y1, is_selecting)
                if action:
                    if action == "clear":
                        canvas.clear()
                        dashboard.notify("Canvas Cleared")
                    elif action == "undo":
                        canvas.undo()
                        dashboard.notify("Undo")
                    elif action == "redo":
                        canvas.redo()
                        dashboard.notify("Redo")
            elif color_picker.is_visible:
                if is_selecting:
                    new_col = color_picker.hit_test(x1, y1)
                    if new_col:
                        color = new_col
                        toolbar.active_tool = "draw"
                        dashboard.notify("Color Selected")
            else:
                action = toolbar.update(x1, y1, is_selecting)
                if action:
                    if action == "clear":
                        canvas.clear()
                        dashboard.notify("Canvas Cleared")
                    elif action == "undo":
                        canvas.undo()
                        dashboard.notify("Undo")
                    elif action == "redo":
                        canvas.redo()
                        dashboard.notify("Redo")
                    elif action == "save":
                        fname = exporter.export_image(canvas.drawing_layer)
                        dashboard.notify(f"Saved: {os.path.basename(fname)}")
                    elif action == "export_3d":
                        fname = exporter.export_3d_stl(canvas.drawing_layer)
                        if fname:
                            dashboard.notify(f"Exported 3D: {os.path.basename(fname)}")
                        else:
                            dashboard.notify("Failed to export 3D (No drawing found)")
                    elif action == "color_picker":
                        color_picker.toggle(x1, y1 + 120)
                
                if is_selecting and toolbar.dwell_start and time.time() - toolbar.dwell_start > 1.0:
                    radial_menu.open(x1, y1)
                    toolbar.dwell_start = None
                
                # --- Drawing Interactions ---
                elif is_drawing and not color_picker.is_visible and not radial_menu.is_active and y1 > (toolbar.margin_top + toolbar.panel_h) and y1 < (CANVAS_H - dashboard.bottom_h):
                    tool = toolbar.active_tool
                    
                    if tool == "draw":
                        if xp != 0 or yp != 0:
                            cv2.line(canvas.drawing_layer, (xp, yp), (x1, y1), color, brush_size, cv2.LINE_AA)
                        else:
                            # Start stroke
                            canvas.snapshot()
                        xp, yp = x1, y1
                    elif tool == "eraser":
                        if xp != 0 or yp != 0:
                            cv2.line(canvas.drawing_layer, (xp, yp), (x1, y1), (0, 0, 0), eraser_size)
                        else:
                            canvas.snapshot()
                        xp, yp = x1, y1
                    elif tool == "spray":
                        if xp == 0 and yp == 0:
                            canvas.snapshot()
                        for _ in range(15):
                            ox = random.randint(-brush_size, brush_size)
                            oy = random.randint(-brush_size, brush_size)
                            sx, sy = x1 + ox, y1 + oy
                            if 0 <= sx < CANVAS_W and 0 <= sy < CANVAS_H:
                                cv2.circle(canvas.drawing_layer, (sx, sy), 1, color, -1)
                        xp, yp = x1, y1
                    elif tool == "crayon":
                        if xp == 0 and yp == 0:
                            canvas.snapshot()
                        if xp != 0 or yp != 0:
                            for _ in range(3):
                                jx1 = xp + random.randint(-3, 3)
                                jy1 = yp + random.randint(-3, 3)
                                jx2 = x1 + random.randint(-3, 3)
                                jy2 = y1 + random.randint(-3, 3)
                                cv2.line(canvas.drawing_layer, (jx1, jy1), (jx2, jy2), color, max(1, brush_size // 2))
                        xp, yp = x1, y1
                    elif tool == "shapes":
                        if xp == 0 and yp == 0:
                            canvas.snapshot()
                            shape_ai.reset()
                        shape_ai.add_point((x1, y1))
                        # Draw preview
                        if len(shape_ai.current_stroke) > 1:
                            pts = np.array(shape_ai.current_stroke, np.int32).reshape((-1, 1, 2))
                            cv2.polylines(img_display, [pts], False, color, brush_size)
                        xp, yp = x1, y1
                else:
                    if toolbar.active_tool == "shapes" and xp != 0 and yp != 0:
                        # User stopped drawing shapes, process it
                        shape_ai.process_stroke(canvas.drawing_layer, color, brush_size)
                    xp, yp = 0, 0
                    
        else:
            if toolbar.active_tool == "shapes" and xp != 0 and yp != 0:
                shape_ai.process_stroke(canvas.drawing_layer, color, brush_size)
            tracker.reset_filters()
            xp, yp = 0, 0
            
        # Get zoomed view if active (for now we keep zoom = 1.0)
        zoomed_layer, _, _, _, _ = canvas.get_zoom_view()
        
        # Combine Canvas with Display
        mask = cv2.cvtColor(zoomed_layer, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        img_display[mask == 255] = zoomed_layer[mask == 255]
        
        # Render UI
        toolbar.render(img_display)
        color_picker.render(img_display)
        radial_menu.render(img_display)
        dashboard.render(img_display, toolbar.active_tool, brush_size, canvas.zoom, color)

        cv2.imshow("Air Canvas Pro", img_display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            running = False
        elif key == ord('c'):
            color_picker.toggle()
        elif key == ord('g'):
            canvas.show_grid = not canvas.show_grid
        elif key == ord(']'):
            brush_size = min(50, brush_size + 2)
        elif key == ord('['):
            brush_size = max(2, brush_size - 2)

    tracker.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
