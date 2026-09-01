export type Tool = 'pencil' | 'eraser' | 'crayon' | 'spray' | 'shapes';

export function drawOnCanvas(
  ctx: CanvasRenderingContext2D,
  tool: Tool,
  color: string,
  size: number,
  x: number,
  y: number,
  prevX: number | null,
  prevY: number | null
) {
  if (prevX === null || prevY === null) {
    return; // Start of stroke
  }

  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  if (tool === 'eraser') {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.lineWidth = size;
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.globalCompositeOperation = 'source-over';
    return;
  }

  ctx.globalCompositeOperation = 'source-over';
  ctx.lineWidth = size;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;

  if (tool === 'pencil') {
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(x, y);
    ctx.stroke();
  } else if (tool === 'spray') {
    const density = 40;
    for (let i = 0; i < density; i++) {
      const offsetX = (Math.random() - 0.5) * size * 2;
      const offsetY = (Math.random() - 0.5) * size * 2;
      if (offsetX * offsetX + offsetY * offsetY <= size * size) {
        ctx.fillRect(x + offsetX, y + offsetY, 1, 1);
      }
    }
  } else if (tool === 'crayon') {
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.moveTo(prevX, prevY);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.lineWidth = size * 0.8;
    ctx.globalAlpha = 0.2;
    ctx.beginPath();
    ctx.moveTo(prevX + (Math.random() * 4 - 2), prevY + (Math.random() * 4 - 2));
    ctx.lineTo(x + (Math.random() * 4 - 2), y + (Math.random() * 4 - 2));
    ctx.stroke();
    ctx.globalAlpha = 1.0;
  } else if (tool === 'shapes') {
    // Repeated circles
    ctx.beginPath();
    ctx.arc(x, y, size / 2, 0, Math.PI * 2);
    ctx.fill();
  }
}
