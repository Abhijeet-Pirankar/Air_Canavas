import { useEffect, useRef, useState } from 'react';
import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

export function useHandTracking(
  videoElement: HTMLVideoElement | null,
  onResults: (results: any) => void,
  cameraActive: boolean
) {
  const onResultsRef = useRef(onResults);
  const requestRef = useRef<number>(0);
  const landmarkerRef = useRef<HandLandmarker | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    onResultsRef.current = onResults;
  }, [onResults]);

  useEffect(() => {
    if (!videoElement || !cameraActive) {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
        requestRef.current = 0;
      }
      return;
    }

    let isSubscribed = true;
    const video = videoElement;
    setError(null);

    async function init() {
      try {
        console.log("[Tracking] Loading MediaPipe FilesetResolver...");
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        console.log("[Tracking] FilesetResolver loaded successfully.");

        if (!isSubscribed) return;

        console.log("[Tracking] Loading HandLandmarker model from /hand_landmarker.task...");
        const handLandmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: "/hand_landmarker.task",
            delegate: "GPU"
          },
          runningMode: "VIDEO",
          numHands: 1,
          minHandDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });
        console.log("[Tracking] Model loaded successfully.");
        landmarkerRef.current = handLandmarker;

        let lastVideoTime = -1;
        let lastLogTime = 0;

        const renderLoop = () => {
          if (!isSubscribed) return;
          
          if (video.readyState >= 2 && video.videoWidth > 0) {
            if (lastVideoTime === -1) {
               console.log(`[Tracking] Camera started. Video dimensions: ${video.videoWidth}x${video.videoHeight}`);
            }
            
            if (lastVideoTime !== video.currentTime) {
              lastVideoTime = video.currentTime;
              const startTimeMs = performance.now();
              const results = handLandmarker.detectForVideo(video, startTimeMs);
              
              const now = performance.now();
              if (now - lastLogTime > 1000) {
                 if (results && results.landmarks && results.landmarks.length > 0) {
                     console.log(`[Tracking] Detection result: ${results.landmarks.length} hands detected.`);
                     console.log(`[Tracking] Index fingertip (landmark 8):`, results.landmarks[0][8]);
                 } else {
                     console.log(`[Tracking] Detection result: 0 hands detected.`);
                 }
                 lastLogTime = now;
              }
              onResultsRef.current(results);
            }
          }
          requestRef.current = requestAnimationFrame(renderLoop);
        };

        if (isSubscribed) {
           renderLoop();
        }
      } catch (err: any) {
        console.error("Failed to initialize MediaPipe tasks-vision:", err);
        if (isSubscribed) setError(err.message || String(err));
      }
    }

    init();

    return () => {
      isSubscribed = false;
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
        requestRef.current = 0;
      }
      if (landmarkerRef.current) {
        landmarkerRef.current.close();
        landmarkerRef.current = null;
      }
    };
  }, [cameraActive, videoElement]);

  return { error };
}
