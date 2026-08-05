import cv2
import numpy as np
import os
import json
import datetime

# Conditional imports for advanced exports
try:
    from stl import mesh
    HAS_STL = True
except ImportError:
    HAS_STL = False

try:
    import svgwrite
    HAS_SVG = True
except ImportError:
    HAS_SVG = False

try:
    from reportlab.pdfgen import canvas as pdf_canvas
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


class ExportEngine:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.export_dir = os.path.join(base_dir, "exports")
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def _get_filename(self, ext):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.export_dir, f"aircanvas_{timestamp}.{ext}")

    def export_image(self, drawing_layer, ext="png"):
        """Exports the canvas to PNG or JPG."""
        filename = self._get_filename(ext)
        # Create a solid dark background instead of black for premium feel
        bg = np.full(drawing_layer.shape, (25, 15, 11), dtype=np.uint8)
        
        # Mask where drawing exists
        mask = cv2.cvtColor(drawing_layer, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        
        # Overlay
        bg[mask == 255] = drawing_layer[mask == 255]
        
        cv2.imwrite(filename, bg)
        return filename

    def export_svg(self, drawing_layer):
        if not HAS_SVG:
            print("svgwrite not installed. Skipping SVG export.")
            return None
            
        filename = self._get_filename("svg")
        h, w = drawing_layer.shape[:2]
        dwg = svgwrite.Drawing(filename, size=(f"{w}px", f"{h}px"))
        
        # Find contours
        gray = cv2.cvtColor(drawing_layer, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            if len(points) > 2:
                # We can sample the color from the center of the contour
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    b, g, r = drawing_layer[cy, cx]
                    color = svgwrite.rgb(int(r), int(g), int(b))
                else:
                    color = svgwrite.rgb(255, 255, 255)
                    
                dwg.add(dwg.polygon(points, fill=color, opacity=0.8))
                
        dwg.save()
        return filename

    def export_pdf(self, drawing_layer):
        if not HAS_PDF:
            print("reportlab not installed. Skipping PDF export.")
            return None
            
        # Temporarily save as PNG to embed in PDF
        temp_png = self.export_image(drawing_layer, "png")
        
        filename = self._get_filename("pdf")
        h, w = drawing_layer.shape[:2]
        
        c = pdf_canvas.Canvas(filename, pagesize=(w, h))
        c.drawImage(temp_png, 0, 0, width=w, height=h)
        c.save()
        
        # Clean up temp
        if os.path.exists(temp_png):
            os.remove(temp_png)
            
        return filename

    def export_3d(self, drawing_layer, base_dir):
        """
        Extracts drawing contours, saves to points.json,
        and opens viewer.html in the browser — original workflow.
        """
        import webbrowser
        
        gray = cv2.cvtColor(drawing_layer, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Use the largest contour
        contour = max(contours, key=cv2.contourArea)
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Build points list for viewer.html
        points = [{"x": int(pt[0][0]), "y": int(pt[0][1])} for pt in approx]
        
        if len(points) < 3:
            return None
        
        # Save points.json next to viewer.html
        points_path = os.path.join(base_dir, "points.json")
        with open(points_path, "w") as f:
            json.dump(points, f)
        
        # Open the viewer
        viewer_path = os.path.join(base_dir, "viewer.html")
        if os.path.exists(viewer_path):
            import threading
            import http.server
            import socketserver
            
            # Start server on dynamic port if not already started
            if not hasattr(self, '_httpd_port'):
                class Handler(http.server.SimpleHTTPRequestHandler):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, directory=base_dir, **kwargs)
                try:
                    httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
                    self._httpd_port = httpd.server_address[1]
                    threading.Thread(target=httpd.serve_forever, daemon=True).start()
                except OSError as e:
                    print(f"Failed to start local server: {e}")
            
            if hasattr(self, '_httpd_port'):
                webbrowser.open(f"http://localhost:{self._httpd_port}/viewer.html")
        
        return points_path

    def export_3d_stl(self, drawing_layer):
        """Legacy alias — now calls export_3d using base_dir."""
        return self.export_3d(drawing_layer, self.base_dir)
