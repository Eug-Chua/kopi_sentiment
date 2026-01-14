"use client";

import { useEffect, useRef } from "react";

interface TravelingDot {
  row: number;
  col: number;
  direction: "horizontal" | "vertical";
  progress: number; // 0 to 1 along the line
  speed: number;
  opacity: number;
}

export default function GridLights() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let dots: TravelingDot[] = [];
    const cellSize = 80;
    let cols = 0;
    let rows = 0;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      cols = Math.ceil(canvas.width / cellSize) + 1;
      rows = Math.ceil(canvas.height / cellSize) + 1;
    };

    const spawnDot = () => {
      const row = Math.floor(Math.random() * rows);
      const col = Math.floor(Math.random() * cols);
      const direction = Math.random() < 0.5 ? "horizontal" : "vertical";

      dots.push({
        row,
        col,
        direction,
        progress: 0,
        speed: 0.005 + Math.random() * 0.01,
        opacity: 0.5 + Math.random() * 0.5,
      });
    };

    const updateDots = () => {
      // Spawn new dots occasionally
      if (Math.random() < 0.02 && dots.length < 15) {
        spawnDot();
      }

      // Update existing dots
      dots = dots.filter((dot) => {
        dot.progress += dot.speed;

        // Fade out as it approaches the end
        if (dot.progress > 0.7) {
          dot.opacity *= 0.95;
        }

        // Remove when it reaches the end
        return dot.progress < 1 && dot.opacity > 0.01;
      });
    };

    const drawGrid = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw base grid (very subtle)
      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 0.5;
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * cellSize;
          const y = row * cellSize;
          ctx.strokeRect(x, y, cellSize, cellSize);
        }
      }

      // Draw corner dots (static)
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * cellSize;
          const y = row * cellSize;
          ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
          ctx.beginPath();
          ctx.arc(x, y, 1.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Draw traveling dots
      for (const dot of dots) {
        const startX = dot.col * cellSize;
        const startY = dot.row * cellSize;

        let x: number, y: number;
        if (dot.direction === "horizontal") {
          x = startX + dot.progress * cellSize;
          y = startY;
        } else {
          x = startX;
          y = startY + dot.progress * cellSize;
        }

        // Draw glow
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, 12);
        gradient.addColorStop(0, `rgba(255, 255, 255, ${dot.opacity * 0.6})`);
        gradient.addColorStop(0.5, `rgba(255, 255, 255, ${dot.opacity * 0.2})`);
        gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, 12, 0, Math.PI * 2);
        ctx.fill();

        // Draw core dot
        ctx.fillStyle = `rgba(255, 255, 255, ${dot.opacity})`;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    const animate = () => {
      updateDots();
      drawGrid();
      animationFrameId = requestAnimationFrame(animate);
    };

    resizeCanvas();
    animate();

    window.addEventListener("resize", resizeCanvas);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 -z-10"
      aria-hidden="true"
    />
  );
}