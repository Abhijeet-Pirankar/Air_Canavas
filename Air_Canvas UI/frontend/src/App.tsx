import { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
  PenLine, Eraser, Paintbrush, SprayCan, Shapes, CircleDot, Undo2, Redo2,
  Save, Trash2, Cuboid, Settings2, Plus, Eye, EyeOff, CameraOff, ChevronDown
} from 'lucide-react';
import { useHandTracking } from './hooks/useHandTracking';
import { drawOnCanvas } from './utils/drawingEngine';
import type { Tool } from './utils/drawingEngine';
import { ThreeDViewerModal } from './components/ThreeDViewerModal';
import { extractContourFromCanvas } from './utils/contourExtractor';

type Layer = {
  id: number;
  name: string;
  active: boolean;
  visible: boolean;
};

export default function App() {
  const [activeTool, setActiveTool] = useState<Tool>('pencil');
  const [brushSize, setBrushSize] = useState<number>(10);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [activeColor, setActiveColor] = useState('#ff2a9d');
  
  const [show3DViewer, setShow3DViewer] = useState(false);
  const [extractedPoints, setExtractedPoints] = useState<{x: number, y: number}[]>([]);

  const [cameraActive, setCameraActive] = useState(false);
  const [trackingActive, setTrackingActive] = useState(false);
  const [fps, setFps] = useState(0);
  const [videoReady, setVideoReady] = useState(false);

  const [layers, setLayers] = useState<Layer[]>([
    { id: 3, name: 'Layer 3', active: true, visible: true },
    { id: 2, name: 'Layer 2', active: false, visible: true },
    { id: 1, name: 'Layer 1', active: false, visible: true },
  ]);

  const webcamRef = useRef<Webcam>(null);
  const cursorCanvasRef = useRef<HTMLCanvasElement>(null);
  
  // Create a ref array for layer canvases
  const layerCanvasesRef = useRef<{ [key: number]: HTMLCanvasElement | null }>({});

  const prevPosRef = useRef<{ x: number, y: number } | null>(null);
  const smoothPosRef = useRef<{ x: number, y: number }>({ x: 0, y: 0 });
  const isDrawingRef = useRef<boolean>(false);
  
  const lastFrameTime = useRef<number>(performance.now());
  const frameCount = useRef<number>(0);

  const activeLayerId = layers.find(l => l.active)?.id || 1;

  const onResults = useCallback((results: any) => {
    // Calculate FPS
    const now = performance.now();
    frameCount.current++;
    if (now - lastFrameTime.current >= 1000) {
      setFps(frameCount.current);
      frameCount.current = 0;
      lastFrameTime.current = now;
    }

    const cursorCanvas = cursorCanvasRef.current;
    if (!cursorCanvas) return;
    const ctx = cursorCanvas.getContext('2d');
    if (!ctx) return;

    // Clear cursor canvas
    ctx.clearRect(0, 0, cursorCanvas.width, cursorCanvas.height);

    if (results.landmarks && results.landmarks.length > 0) {
      setTrackingActive(true);
      const landmarks = results.landmarks[0];
      
      const indexTip = landmarks[8];
      
      // Mirror x coordinate because camera feed is usually mirrored
      const rawX = (1 - indexTip.x) * cursorCanvas.width;
      const rawY = indexTip.y * cursorCanvas.height;
      
      // Smoothing (matches python smoothening = 0.35)
      const smoothening = 0.35;
      if (smoothPosRef.current.x === 0 && smoothPosRef.current.y === 0) {
        smoothPosRef.current = { x: rawX, y: rawY };
      }
      smoothPosRef.current.x += smoothening * (rawX - smoothPosRef.current.x);
      smoothPosRef.current.y += smoothening * (rawY - smoothPosRef.current.y);
      
      const x = smoothPosRef.current.x;
      const y = smoothPosRef.current.y;

      // Highly visible marker at rawX, rawY to debug the raw tracking
      ctx.beginPath();
      ctx.arc(rawX, rawY, 15, 0, 2 * Math.PI);
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 4;
      ctx.stroke();
      
      ctx.beginPath();
      ctx.arc(rawX, rawY, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#ff0000';
      ctx.fill();

      // Draw Cursor (glowing fingertip)
      ctx.beginPath();
      ctx.arc(x, y, brushSize / 2, 0, 2 * Math.PI);
      ctx.fillStyle = activeColor;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'white';
      ctx.shadowColor = activeColor;
      ctx.shadowBlur = 15;
      ctx.stroke();
      ctx.shadowBlur = 0; // reset

      // Gesture detection matching Python `air_canvas.py`
      // index_up = lmList[8][2] < lmList[6][2]
      // middle_up = lmList[12][2] < lmList[10][2]
      // Drawing mode: index_up and not middle_up
      const indexUp = landmarks[8].y < landmarks[6].y;
      const middleUp = landmarks[12].y < landmarks[10].y;
      
      const isDrawing = indexUp && !middleUp;

      if (isDrawing) {
        if (!isDrawingRef.current) {
          // Just started drawing
          prevPosRef.current = { x, y };
          isDrawingRef.current = true;
        }

        const activeCanvas = layerCanvasesRef.current[activeLayerId];
        if (activeCanvas) {
          const drawCtx = activeCanvas.getContext('2d');
          if (drawCtx) {
            drawOnCanvas(
              drawCtx,
              activeTool,
              activeColor,
              brushSize,
              x,
              y,
              prevPosRef.current ? prevPosRef.current.x : x,
              prevPosRef.current ? prevPosRef.current.y : y
            );
          }
        }
        prevPosRef.current = { x, y };
      } else {
        isDrawingRef.current = false;
        prevPosRef.current = null;
      }
    } else {
      setTrackingActive(false);
      isDrawingRef.current = false;
      prevPosRef.current = null;
    }
  }, [activeTool, activeColor, brushSize, activeLayerId]);

  // Pass webcam video element to MediaPipe hook
  const { error: trackingError } = useHandTracking(
    videoReady && webcamRef.current ? (webcamRef.current.video as HTMLVideoElement) : null,
    onResults,
    cameraActive
  );

  const handleClear = () => {
    const activeCanvas = layerCanvasesRef.current[activeLayerId];
    if (activeCanvas) {
      const ctx = activeCanvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
      }
    }
  };

  const handleSave = () => {
    // Combine visible layers and download
    const combineCanvas = document.createElement('canvas');
    combineCanvas.width = 1280;
    combineCanvas.height = 720;
    const ctx = combineCanvas.getContext('2d');
    if (ctx) {
      // Draw background from webcam if we want, but usually just transparent drawing
      [...layers].reverse().forEach(layer => {
        if (layer.visible) {
          const lCanvas = layerCanvasesRef.current[layer.id];
          if (lCanvas) {
            ctx.drawImage(lCanvas, 0, 0);
          }
        }
      });
      const link = document.createElement('a');
      link.download = 'air_canvas_export.png';
      link.href = combineCanvas.toDataURL();
      link.click();
    }
  };

  const handle3DExport = () => {
    setShowMoreMenu(false);
    const combineCanvas = document.createElement('canvas');
    combineCanvas.width = 1280;
    combineCanvas.height = 720;
    const ctx = combineCanvas.getContext('2d');
    if (ctx) {
      [...layers].reverse().forEach(layer => {
        if (layer.visible) {
          const lCanvas = layerCanvasesRef.current[layer.id];
          if (lCanvas) {
            ctx.drawImage(lCanvas, 0, 0);
          }
        }
      });
      const points = extractContourFromCanvas(combineCanvas);
      setExtractedPoints(points);
      setShow3DViewer(true);
    }
  };

  const toggleLayerVisibility = (id: number) => {
    setLayers(layers.map(l => l.id === id ? { ...l, visible: !l.visible } : l));
  };

  const setActiveLayer = (id: number) => {
    setLayers(layers.map(l => ({ ...l, active: l.id === id })));
  };

  const addLayer = () => {
    const newId = Math.max(...layers.map(l => l.id)) + 1;
    setLayers([{ id: newId, name: `Layer ${newId}`, active: true, visible: true }, ...layers.map(l => ({ ...l, active: false }))]);
  };

  // --- UI Components ---
  const drawingTools = [
    { id: 'pencil', icon: PenLine, label: 'Pencil' },
    { id: 'eraser', icon: Eraser, label: 'Eraser' },
    { id: 'crayon', icon: Paintbrush, label: 'Crayon' },
    { id: 'spray', icon: SprayCan, label: 'Spray' },
    { id: 'shapes', icon: Shapes, label: 'Shapes' },
  ] as const;

  const historyActions = [
    { id: 'undo', icon: Undo2, label: 'Undo' },
    { id: 'redo', icon: Redo2, label: 'Redo' },
  ];

  const Tooltip = ({ label }: { label: string }) => (
    <span className="absolute -bottom-9 opacity-0 group-hover:opacity-100 transition-opacity duration-200 delay-150 bg-[#0c101a]/95 backdrop-blur-md text-[10px] font-medium tracking-wide text-gray-200 px-2 py-1 rounded border border-white/10 shadow-[0_4px_12px_rgba(0,0,0,0.4)] pointer-events-none whitespace-nowrap z-50">
      {label}
    </span>
  );

  const Divider = () => (
    <div className="w-[1px] h-8 bg-white/5 mx-2 shadow-[1px_0_0_rgba(0,0,0,0.3)] self-center" />
  );

  return (
    <div className="relative w-screen h-screen flex flex-col p-6 gap-6 box-border font-sans antialiased text-gray-200 overflow-hidden z-0 bg-[#0a0a0c]">
      
      {/* Background Cinematic Glows */}
      <div className="absolute inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[40vw] h-[40vw] rounded-full bg-[#9d2aff] opacity-[0.015] blur-[160px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[40vw] h-[40vw] rounded-full bg-[#00dfff] opacity-[0.015] blur-[150px]" />
      </div>

      {/* Top Toolbar */}
      <div className="flex justify-center w-full mt-2 z-20">
        <div className="glass-toolbar-compact rounded-[20px] px-6 py-4 flex items-center justify-between relative w-full max-w-[1200px]">
          
          {/* GROUP: DRAWING */}
          <div className="flex flex-col items-center relative">
            <div className="flex items-center gap-2">
              {drawingTools.map((tool) => {
                const Icon = tool.icon;
                const isActive = activeTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setActiveTool(tool.id)}
                    className={`relative group w-11 h-11 rounded-xl ${isActive ? 'glass-button-active' : 'glass-button'}`}
                  >
                    <Icon size={24} strokeWidth={1.8} className={isActive ? 'icon-active' : 'icon-normal'} />
                    <Tooltip label={tool.label} />
                  </button>
                );
              })}
            </div>
          </div>

          <Divider />

          {/* GROUP: APPEARANCE */}
          <div className="flex flex-col items-center relative z-30">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="relative group w-11 h-11 rounded-xl glass-button"
              >
                <div
                  className="w-[24px] h-[24px] rounded-full border-2 border-white/20 shadow-[inset_0_2px_4px_rgba(0,0,0,0.5),0_0_8px_rgba(0,0,0,0.3)] transition-transform duration-200 group-hover:scale-110"
                  style={{ backgroundColor: activeColor }}
                />
                <Tooltip label="Color" />
              </button>

              {showColorPicker && (
                <div className="absolute top-[56px] left-0 glass-panel p-3 rounded-xl w-40 flex flex-col items-center gap-3 origin-top animate-in fade-in zoom-in-95 duration-200 z-50">
                  <div className="w-full flex justify-between px-1 gap-2">
                    {['#ff2a9d', '#9d2aff', '#00dfff', '#ffcc00', '#ffffff'].map((color) => (
                      <button
                        key={color}
                        onClick={() => { setActiveColor(color); setShowColorPicker(false); }}
                        className="w-5 h-5 rounded-full hover:scale-110 transition-transform"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <button className="relative group w-11 h-11 rounded-xl glass-button">
                <CircleDot size={20} strokeWidth={1.8} className="icon-normal" />
                <Tooltip label="Brush Size" />
              </button>
            </div>
          </div>

          <Divider />

          {/* GROUP: HISTORY */}
          <div className="flex flex-col items-center relative">
            <div className="flex items-center gap-2">
              {historyActions.map((action) => (
                <button key={action.id} className="relative group w-11 h-11 rounded-xl glass-button">
                  <action.icon size={20} strokeWidth={1.8} className="icon-normal" />
                  <Tooltip label={action.label} />
                </button>
              ))}
            </div>
          </div>

          <Divider />

          {/* GROUP: ACTIONS */}
          <div className="flex flex-col items-center relative">
            <div className="flex items-center gap-2">
              <button onClick={handleSave} className="relative group w-11 h-11 rounded-xl glass-button">
                <Save size={20} strokeWidth={1.8} className="icon-normal" />
                <Tooltip label="Save" />
              </button>
              <button onClick={handleClear} className="relative group w-11 h-11 rounded-xl glass-button">
                <Trash2 size={20} strokeWidth={1.8} className="icon-normal" />
                <Tooltip label="Clear" />
              </button>
            </div>
          </div>
          
          <Divider />

          {/* GROUP: MORE */}
          <div className="flex flex-col items-center relative z-40">
            <div className="flex items-center gap-2">
              <div className="relative">
                <button
                  onClick={() => setShowMoreMenu(!showMoreMenu)}
                  className={`relative group px-4 h-11 rounded-xl flex items-center gap-2 ${showMoreMenu ? 'glass-button-active' : 'glass-button'}`}
                >
                  <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">More</span>
                  <ChevronDown size={16} strokeWidth={2} className={showMoreMenu ? 'icon-active' : 'icon-normal'} />
                </button>
                {showMoreMenu && (
                  <div className="absolute top-[56px] right-0 glass-panel p-2 rounded-xl w-48 flex flex-col gap-1 origin-top-right animate-in fade-in zoom-in-95 duration-200 z-50">
                    <button onClick={handle3DExport} className="flex items-center gap-3 w-full p-2.5 rounded-lg glass-button justify-start text-sm font-medium">
                      <Cuboid size={18} strokeWidth={1.8} className="icon-normal" />
                      <span className="text-gray-200">3D Export</span>
                    </button>
                    <button className="flex items-center gap-3 w-full p-2.5 rounded-lg glass-button justify-start text-sm font-medium">
                      <Settings2 size={18} strokeWidth={1.8} className="icon-normal" />
                      <span className="text-gray-200">Settings</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Middle Layout */}
      <div className="flex-1 flex gap-6 min-h-0 w-full max-w-[1800px] mx-auto z-10 pt-4 pb-2">
        
        {/* Main Canvas / Camera Workspace */}
        <div className="flex-1 glass-canvas rounded-[24px] relative overflow-hidden flex items-center justify-center">
          <div className="absolute top-0 left-8 right-8 h-px bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none" />
          
          {cameraActive ? (
            <div className="relative w-full h-full">
              {/* Webcam Feed - Flipped horizontally so the user sees a mirror */}
              <Webcam
                ref={webcamRef}
                audio={false}
                videoConstraints={{ facingMode: 'user', width: 1280, height: 720 }}
                className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
                onUserMedia={() => setVideoReady(true)}
              />
              
              {/* Drawing Layers Container */}
              <div className="absolute inset-0 pointer-events-none">
                {/* The drawing layers must match the aspect ratio and flip state if needed, 
                    but since we manually map coordinates with a flipped X, we don't need to CSS flip the canvas. 
                    We just stretch them to fill the container and manage resolution via JS. */}
                {[...layers].reverse().map(layer => (
                  <canvas
                    key={layer.id}
                    ref={el => { layerCanvasesRef.current[layer.id] = el; }}
                    width={1280}
                    height={720}
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ opacity: layer.visible ? 1 : 0 }}
                  />
                ))}
              </div>
              
              {/* Cursor Layer (always on top) */}
              <canvas
                ref={cursorCanvasRef}
                width={1280}
                height={720}
                className="absolute inset-0 w-full h-full object-cover pointer-events-none z-50"
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-4 text-white/30 cursor-pointer hover:text-white/50 transition-colors" onClick={() => setCameraActive(true)}>
              <CameraOff size={44} strokeWidth={1.5} className="opacity-50 drop-shadow-md" />
              <div className="flex flex-col items-center text-center">
                <span className="font-semibold tracking-[0.2em] text-sm mb-1 text-white/60">CAMERA FEED</span>
                <span className="text-[11px] font-light text-white/40">Waiting for camera... Click to start.</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <div className="w-[260px] flex flex-col gap-5 shrink-0 z-10">
          
          {/* Layers Card */}
          <div className="glass-panel rounded-2xl p-4 flex flex-col gap-3 flex-1 relative">
            <h3 className="text-xs font-semibold tracking-wider text-gray-500 uppercase">Layers</h3>
            
            <div className="flex flex-col gap-2 flex-1 overflow-y-auto pr-1">
              {layers.map((layer) => (
                <div
                  key={layer.id}
                  onClick={() => setActiveLayer(layer.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer ${
                    layer.active ? 'glass-layer-active text-white' : 'glass-layer text-gray-400'
                  }`}
                >
                  <button onClick={(e) => { e.stopPropagation(); toggleLayerVisibility(layer.id); }} className="opacity-70 hover:opacity-100 transition-opacity">
                    {layer.visible ? (
                      <Eye size={16} strokeWidth={1.8} className={layer.active ? 'text-white' : 'text-gray-400'} />
                    ) : (
                      <EyeOff size={16} strokeWidth={1.8} className="text-gray-600" />
                    )}
                  </button>
                  <span className="flex-1 text-sm font-medium">{layer.name}</span>
                </div>
              ))}
            </div>

            <div className="h-px bg-white/5 w-full my-1" />

            <button onClick={addLayer} className="w-full py-2.5 rounded-lg glass-button gap-2 text-sm font-medium">
              <Plus size={16} strokeWidth={2} className="icon-normal" />
              <span className="text-gray-300">New Layer</span>
            </button>
          </div>

          {/* Brush Card */}
          <div className="glass-panel rounded-2xl p-4 flex flex-col gap-4 shrink-0 relative">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-semibold tracking-wider text-gray-500 uppercase">Brush</h3>
              <span className="text-xs font-medium text-gray-300">{brushSize}px</span>
            </div>
            
            <div className="flex items-center justify-center h-16 bg-black/20 rounded-xl border border-white/5">
              <div 
                className="rounded-full transition-all duration-200"
                style={{ width: brushSize, height: brushSize, backgroundColor: activeColor }}
              />
            </div>

            <div>
              <input
                type="range"
                min="1"
                max="50"
                value={brushSize}
                onChange={(e) => setBrushSize(parseInt(e.target.value))}
                className="w-full h-1.5 bg-black/40 rounded-lg appearance-none cursor-pointer border border-white/5"
                style={{ accentColor: activeColor }}
              />
            </div>
          </div>

        </div>
      </div>

      {/* Slim Status Bar */}
      <div className="h-10 shrink-0 w-full max-w-[1200px] mx-auto flex items-center justify-between px-6 text-[11px] font-semibold tracking-wider text-gray-400 z-10 glass-panel rounded-xl">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">TOOL</span>
            <span className="text-gray-200 uppercase">{activeTool}</span>
          </div>
          <div className="w-[1px] h-3 bg-white/10" />
          <div className="flex items-center gap-2">
            <span className="text-gray-500">SIZE</span>
            <span className="text-gray-200">{brushSize}px</span>
          </div>
          <div className="w-[1px] h-3 bg-white/10" />
          <div className="flex items-center gap-2">
            <span className="text-gray-500">FPS</span>
            <span className={fps > 20 ? 'text-gray-200' : 'text-amber-500'}>{fps}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {trackingError ? (
            <>
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-red-500 max-w-[200px] truncate" title={trackingError}>
                ERROR: {trackingError}
              </span>
            </>
          ) : (
            <>
              <div className={`w-1.5 h-1.5 rounded-full ${trackingActive ? 'bg-[#9d2aff] animate-pulse' : 'bg-amber-500'}`} />
              <span className={`${trackingActive ? 'text-gray-200' : 'text-amber-500'}`}>
                {trackingActive ? 'TRACKING ACTIVE' : 'TRACKING LOST'}
              </span>
            </>
          )}
        </div>
      </div>

      {show3DViewer && (
        <ThreeDViewerModal points={extractedPoints} onClose={() => setShow3DViewer(false)} />
      )}
    </div>
  );
}
