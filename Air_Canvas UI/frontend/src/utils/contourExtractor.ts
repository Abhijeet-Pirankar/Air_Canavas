import { contours } from "d3-contour";
import simplify from "simplify-js";

export function extractContourFromCanvas(canvas: HTMLCanvasElement): {x: number, y: number}[] {
  const ctx = canvas.getContext('2d');
  if (!ctx) return [];
  const { width, height } = canvas;
  const imageData = ctx.getImageData(0, 0, width, height);
  const data = imageData.data;

  const values = new Array(width * height);
  // Alpha thresholding: value is 1 if alpha > 10, else 0
  for (let i = 0, n = data.length; i < n; i += 4) {
    values[i / 4] = data[i + 3] > 10 ? 1 : 0;
  }

  // Get polygons for threshold 0.5
  const multiPolygons = contours().size([width, height]).thresholds([0.5])(values);
  
  if (multiPolygons.length === 0) return [];
  const polygons = multiPolygons[0].coordinates; // Array of polygons (exterior + holes)
  
  if (polygons.length === 0) return [];

  // Find the largest polygon by number of points (rough estimation of area/importance)
  let largestPolygon = polygons[0];
  let maxLen = 0;
  for (const poly of polygons) {
    if (poly[0] && poly[0].length > maxLen) {
      maxLen = poly[0].length;
      largestPolygon = poly;
    }
  }

  // The first array in a polygon is the exterior ring
  const exteriorRing = largestPolygon[0];
  
  if (!exteriorRing || exteriorRing.length < 3) return [];

  // Convert to format for simplify-js
  const points = exteriorRing.map((p: any) => ({ x: p[0], y: p[1] }));
  
  // Simplify to reduce vertex count for Three.js (tolerance of 2 pixels, high quality)
  const simplified = simplify(points, 2, true);
  
  return simplified;
}
