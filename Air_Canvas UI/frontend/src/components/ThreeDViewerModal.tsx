import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { X, AlertCircle } from 'lucide-react';

interface Props {
  points: {x: number, y: number}[];
  onClose: () => void;
}

export function ThreeDViewerModal({ points, onClose }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (points.length < 3) {
      setError("Not enough points to create a 3D shape. Please draw something more substantial.");
      return;
    }

    const currentMount = mountRef.current;
    if (!currentMount) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#05060a'); 
    scene.fog = new THREE.FogExp2('#05060a', 0.001);

    // Camera setup
    const camera = new THREE.PerspectiveCamera(45, currentMount.clientWidth / currentMount.clientHeight, 1, 10000);
    camera.position.set(0, 0, 1500);

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    currentMount.appendChild(renderer.domElement);

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 2.0;

    // Create Shape from points
    const shape = new THREE.Shape();
    
    // Find center of bounding box to center the geometry
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    points.forEach(p => {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    });
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    shape.moveTo(points[0].x - centerX, -(points[0].y - centerY));
    for (let i = 1; i < points.length; i++) {
      shape.lineTo(points[i].x - centerX, -(points[i].y - centerY));
    }

    // Extrude settings
    const extrudeSettings = {
      depth: 60,
      bevelEnabled: true,
      bevelSegments: 4,
      steps: 2,
      bevelSize: 6,
      bevelThickness: 6
    };

    let geometry: THREE.ExtrudeGeometry;
    try {
      geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
      geometry.computeVertexNormals();
      geometry.center(); 
    } catch (e) {
      setError("Failed to extrude 3D shape. The contour might be self-intersecting.");
      return;
    }

    // Premium purple/pink material
    const material = new THREE.MeshPhysicalMaterial({
      color: 0xe066ff, // Brighter purple
      emissive: 0xff2a9d, // Pinkish emissive
      emissiveIntensity: 0.1, // Subtle glow
      metalness: 0.2, // Lower metalness to avoid looking black
      roughness: 0.4, // Higher roughness to make edges readable
      clearcoat: 0.8,
      clearcoatRoughness: 0.2,
      side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    
    // Initial isometric rotation
    mesh.rotation.x = Math.PI / 6;
    mesh.rotation.y = -Math.PI / 6;

    scene.add(mesh);

    // Add ground plane for shadows
    const planeGeo = new THREE.PlaneGeometry(5000, 5000);
    const planeMat = new THREE.ShadowMaterial({ opacity: 0.4 });
    const plane = new THREE.Mesh(planeGeo, planeMat);
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = -400; // Place below the object
    plane.receiveShadow = true;
    scene.add(plane);

    // Lighting
    // Significantly increase ambient lighting with HemisphereLight for better tone
    const ambientLight = new THREE.HemisphereLight(0xffffff, 0x444455, 1.8);
    scene.add(ambientLight);

    // Large soft key light from upper-left/front
    const keyLight = new THREE.DirectionalLight(0xffffff, 3.0);
    keyLight.position.set(-300, 500, 400);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.bias = -0.001;
    keyLight.shadow.camera.top = 1000;
    keyLight.shadow.camera.bottom = -1000;
    keyLight.shadow.camera.left = -1000;
    keyLight.shadow.camera.right = 1000;
    scene.add(keyLight);
    
    // Softer fill light from opposite side
    const fillLight = new THREE.DirectionalLight(0xaaccff, 1.5);
    fillLight.position.set(400, 200, 300);
    scene.add(fillLight);

    // Rim light behind the object for a premium glow
    const rimLight = new THREE.DirectionalLight(0xff2a9d, 3.0);
    rimLight.position.set(0, 300, -500);
    scene.add(rimLight);

    // Automatically frame/center the object
    geometry.computeBoundingSphere();
    const radius = geometry.boundingSphere ? geometry.boundingSphere.radius : 500;
    const fov = camera.fov * (Math.PI / 180);
    const cameraZ = Math.abs(radius / Math.sin(fov / 2)) * 1.8; // padding factor
    camera.position.set(0, 0, cameraZ);
    controls.target.set(0, 0, 0);
    controls.update();

    // Animation Loop
    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!currentMount) return;
      camera.aspect = currentMount.clientWidth / currentMount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(currentMount.clientWidth, currentMount.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      currentMount.removeChild(renderer.domElement);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      controls.dispose();
    };
  }, [points]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
      <div className="relative w-[80vw] h-[80vh] max-w-[1200px] bg-[#05060a] rounded-[32px] border border-white/10 shadow-[0_0_50px_rgba(157,42,255,0.15)] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-10 pointer-events-none">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center backdrop-blur-md shadow-[0_4px_12px_rgba(0,0,0,0.5)]">
              <span className="text-[#ff2a9d] font-bold text-lg">3D</span>
            </div>
            <div>
              <h2 className="text-white font-semibold text-lg tracking-wide">3D Viewer</h2>
              <p className="text-white/50 text-xs mt-0.5">Drag to rotate • Scroll to zoom</p>
            </div>
          </div>
          
          <button 
            onClick={onClose}
            className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-all pointer-events-auto shadow-[0_4px_12px_rgba(0,0,0,0.5)]"
          >
            <X size={24} strokeWidth={2} />
          </button>
        </div>

        {/* Content */}
        {error ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center p-8">
            <AlertCircle size={64} className="text-amber-500 opacity-50 mb-4" />
            <div>
              <h3 className="text-white font-semibold text-xl mb-3">Generation Failed</h3>
              <p className="text-white/60 text-sm max-w-md mx-auto leading-relaxed">{error}</p>
            </div>
          </div>
        ) : (
          <div ref={mountRef} className="flex-1 w-full h-full cursor-grab active:cursor-grabbing relative">
            <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_100px_rgba(0,0,0,0.8)]" />
          </div>
        )}
      </div>
    </div>
  );
}
