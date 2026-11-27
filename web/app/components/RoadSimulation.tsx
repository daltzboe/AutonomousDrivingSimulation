"use client";

import { useEffect, useRef, useState } from "react";

type Controller = "baseline" | "safety" | "steering";
type Scenario = "clear" | "center" | "edge" | "outside" | "multiple";
type Props = {
  running: boolean;
  controller: Controller;
  scenario: Scenario;
  resetToken: number;
  onTelemetry: (value: { speed: number; progress: number; elapsed: number; lane: number; signal: string; collisions: number }) => void;
};

type TrafficCar = { id: number; lane: number; s: number; speed: number; color: string };
type Hazard = { s: number; lane: number; kind: "barrier" | "cone" };
type Signal = { s: number; phase: "green" | "yellow" | "red" };

const ROUTE_LENGTH = 2800;
const LANE_WIDTH = 3.6;
const COLORS = ["#e1a45e", "#a8b9c9", "#d86f72", "#7f9bd6", "#a5c88d", "#b5a0d6"];

function clamp(v: number, min: number, max: number) { return Math.max(min, Math.min(max, v)); }

export default function RoadSimulation({ running, controller, scenario, resetToken, onTelemetry }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ distance: 0, speed: 0, elapsed: 0, lane: 2, laneTarget: 2, collisions: 0, signal: "GREEN", crashed: false, traffic: [] as TrafficCar[] });
  const telemetryRef = useRef(onTelemetry);
  const runningRef = useRef(running);
  telemetryRef.current = onTelemetry;
  runningRef.current = running;
  const [hud, setHud] = useState({ speed: 0, distance: 0, lane: 2, signal: "GREEN", collisions: 0, status: "READY AT START" });

  useEffect(() => {
    stateRef.current = { distance: 0, speed: 0, elapsed: 0, lane: 2, laneTarget: 2, collisions: 0, signal: "GREEN", crashed: false, traffic: [] };
    setHud({ speed: 0, distance: 0, lane: 2, signal: "GREEN", collisions: 0, status: "READY AT START" });
  }, [resetToken, controller, scenario]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let frame = 0;
    let last = 0;
    let lastTelemetry = 0;
    let spawnId = 0;
    let hazards: Hazard[] = [];
    let signals: Signal[] = [];
    const s = stateRef.current;

    const createWorld = () => {
      hazards = [];
      if (scenario === "center") hazards.push({ s: 330, lane: 2, kind: "barrier" }, { s: 1120, lane: 3, kind: "cone" }, { s: 1920, lane: 2, kind: "barrier" });
      if (scenario === "edge") hazards.push({ s: 390, lane: 2, kind: "cone" }, { s: 960, lane: 3, kind: "barrier" }, { s: 1660, lane: 3, kind: "cone" });
      if (scenario === "outside") hazards.push({ s: 520, lane: 1, kind: "barrier" }, { s: 1180, lane: 0, kind: "cone" }, { s: 2080, lane: 2, kind: "barrier" });
      if (scenario === "multiple") hazards.push({ s: 300, lane: 2, kind: "barrier" }, { s: 345, lane: 3, kind: "cone" }, { s: 760, lane: 3, kind: "barrier" }, { s: 1280, lane: 2, kind: "cone" }, { s: 1810, lane: 3, kind: "barrier" }, { s: 2250, lane: 2, kind: "cone" });
      signals = [480, 1040, 1580, 2180, 2580].map((distance, i) => ({ s: distance, phase: i % 3 === 0 ? "red" : "green" }));
      s.traffic = [
        { id: 1, lane: 0, s: 180, speed: 16, color: COLORS[0] },
        { id: 2, lane: 1, s: 270, speed: 19, color: COLORS[1] },
        { id: 3, lane: 3, s: 150, speed: 12, color: COLORS[2] },
        { id: 4, lane: 0, s: 430, speed: 18, color: COLORS[3] },
        { id: 5, lane: 1, s: 620, speed: 15, color: COLORS[4] },
        { id: 6, lane: 3, s: 540, speed: 16, color: COLORS[5] },
      ];
      spawnId = 7;
    };
    createWorld();

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);

    const drawCar = (x: number, y: number, width: number, height: number, color: string, ego = false, opposite = false) => {
      ctx.save();
      ctx.translate(x, y);
      if (opposite) ctx.rotate(Math.PI);
      ctx.shadowColor = ego ? "#55baff" : "#00000055";
      ctx.shadowBlur = ego ? 16 : 5;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(-width / 2, -height / 2, width, height, 7);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = ego ? "#17344c" : "#25313c";
      ctx.beginPath();
      ctx.roundRect(-width * 0.31, -height * 0.22, width * 0.62, height * 0.34, 4);
      ctx.fill();
      ctx.fillStyle = "#f8e6b0";
      ctx.fillRect(-width * 0.34, -height * 0.43, width * 0.18, 3);
      ctx.fillRect(width * 0.16, -height * 0.43, width * 0.18, 3);
      ctx.fillStyle = "#ef6c6c";
      ctx.fillRect(-width * 0.34, height * 0.38, width * 0.18, 3);
      ctx.fillRect(width * 0.16, height * 0.38, width * 0.18, 3);
      ctx.restore();
    };

    const draw = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      const d = Math.min(width, 960);
      const roadWidth = Math.min(width * 0.76, d * 0.72);
      const left = (width - roadWidth) / 2;
      const pxPerMeter = Math.min(roadWidth / (LANE_WIDTH * 4), 20);
      const egoY = height * 0.76;
      const current = stateRef.current;

      ctx.clearRect(0, 0, width, height);
      const grass = ctx.createLinearGradient(0, 0, 0, height);
      grass.addColorStop(0, "#152c28"); grass.addColorStop(1, "#0d1d1b");
      ctx.fillStyle = grass; ctx.fillRect(0, 0, width, height);
      // subtle roadside texture
      ctx.fillStyle = "#28453b";
      for (let i = 0; i < 34; i++) {
        const y = ((i * 91 + current.distance * 2.7) % (height + 30)) - 15;
        ctx.fillRect(left - 26 - (i % 3) * 13, y, 3, 7);
        ctx.fillRect(left + roadWidth + 22 + (i % 3) * 13, y, 3, 7);
      }
      ctx.fillStyle = "#303943";
      ctx.fillRect(left, 0, roadWidth, height);
      ctx.fillStyle = "#404a54";
      ctx.fillRect(left + 4, 0, roadWidth - 8, height);
      // road shoulder and boundary
      ctx.fillStyle = "#e0b75d";
      ctx.fillRect(left + 3, 0, 3, height);
      ctx.fillRect(left + roadWidth - 6, 0, 3, height);
      const lanePx = roadWidth / 4;
      const dashOffset = (current.distance * pxPerMeter * 0.9) % 62;
      ctx.lineWidth = 2;
      for (let lane = 1; lane < 4; lane++) {
        const x = left + lane * lanePx;
        ctx.strokeStyle = lane === 2 ? "#f0d06b" : "#d3d9dc";
        ctx.setLineDash(lane === 2 ? [] : [25, 24]);
        ctx.lineDashOffset = -dashOffset;
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
        if (lane === 2) {
          ctx.strokeStyle = "#f0d06b"; ctx.beginPath(); ctx.moveTo(x + 5, 0); ctx.lineTo(x + 5, height); ctx.stroke();
        }
      }
      ctx.setLineDash([]);
      // Direction arrows: the left two lanes travel toward the viewer; right two travel away.
      for (let y = -70 + dashOffset; y < height + 90; y += 130) {
        for (let lane = 0; lane < 4; lane++) {
          const x = left + lanePx * (lane + 0.5);
          ctx.save(); ctx.translate(x, y); if (lane < 2) ctx.rotate(Math.PI);
          ctx.strokeStyle = "#aebbc4"; ctx.globalAlpha = 0.42; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(0, 15); ctx.lineTo(0, -13); ctx.lineTo(-7, -4); ctx.moveTo(0, -13); ctx.lineTo(7, -4); ctx.stroke(); ctx.restore();
        }
      }

      // Fixed hazards are placed in route coordinates, so the ego car meets them ahead.
      for (const hazard of hazards) {
        const relative = hazard.s - current.distance;
        const y = egoY - relative * pxPerMeter;
        if (y < -60 || y > height + 60) continue;
        const x = left + lanePx * (hazard.lane + 0.5);
        if (hazard.kind === "barrier") {
          ctx.fillStyle = "#f4f1e8"; ctx.fillRect(x - 18, y - 9, 36, 18);
          ctx.fillStyle = "#df6a48"; for (let k = -14; k <= 14; k += 14) ctx.fillRect(x + k, y - 9, 7, 18);
          ctx.strokeStyle = "#fff1ce"; ctx.strokeRect(x - 18, y - 9, 36, 18);
        } else {
          ctx.fillStyle = "#f5a14e"; ctx.beginPath(); ctx.moveTo(x, y - 13); ctx.lineTo(x - 10, y + 11); ctx.lineTo(x + 10, y + 11); ctx.closePath(); ctx.fill();
          ctx.fillStyle = "#fff1d0"; ctx.fillRect(x - 6, y + 2, 12, 3);
        }
      }

      // Signal gantries and stop lines, with a time-based red/amber/green cycle.
      let nearestSignal = "GREEN";
      for (const signal of signals) {
        const relative = signal.s - current.distance;
        const y = egoY - relative * pxPerMeter;
        if (y < -55 || y > height + 55) continue;
        const cycle = (current.elapsed + signal.s * 0.013) % 24;
        signal.phase = cycle < 10 ? "green" : cycle < 14 ? "yellow" : "red";
        if (relative > 0 && relative < 85) nearestSignal = signal.phase.toUpperCase();
        ctx.fillStyle = "#1c252d"; ctx.fillRect(left + lanePx * 2 - 4, y - 32, lanePx * 2 + 8, 6);
        ctx.fillStyle = "#252e37"; ctx.fillRect(left + lanePx * 2 - 5, y - 28, 10, 40);
        const colors = ["#df5754", "#e5b34e", "#51c77d"];
        const active = signal.phase === "red" ? 0 : signal.phase === "yellow" ? 1 : 2;
        colors.forEach((color, i) => {
          ctx.fillStyle = i === active ? color : "#4b555d";
          ctx.beginPath(); ctx.arc(left + lanePx * 2, y - 20 + i * 10, 4, 0, Math.PI * 2); ctx.fill();
        });
        ctx.strokeStyle = "#f1d477"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(left + lanePx * 2, y + 12); ctx.lineTo(left + roadWidth, y + 12); ctx.stroke();
        if (relative > 0 && relative < 34 && signal.phase !== "green") {
          ctx.fillStyle = "#f4d16f"; ctx.font = "600 10px sans-serif"; ctx.textAlign = "center"; ctx.fillText("STOP LINE", left + lanePx * 3, y + 27);
        }
      }
      current.signal = nearestSignal;

      // Traffic: opposite-direction vehicles approach; same-direction cars pace the ego vehicle.
      for (const car of current.traffic) {
        const relative = car.s - current.distance;
        const y = egoY - relative * pxPerMeter;
        if (y < -70 || y > height + 70) continue;
        const x = left + lanePx * (car.lane + 0.5);
        drawCar(x, y, lanePx * 0.48, 42, car.color, false, car.lane < 2);
      }

      const egoX = left + lanePx * (current.lane + 0.5);
      drawCar(egoX, egoY, lanePx * 0.52, 50, current.crashed ? "#bd4d4d" : "#3b9be0", true);
      // Start marker and distance labels make direction obvious.
      if (current.distance < 85) {
        ctx.fillStyle = "#79d5a6"; ctx.font = "700 12px monospace"; ctx.textAlign = "center";
        ctx.fillText("START  →  ROUTE 0", width / 2, height - 18);
      }
      ctx.fillStyle = "#e5edf4"; ctx.font = "11px monospace"; ctx.textAlign = "left";
      ctx.fillText("4-LANE TWO-WAY ROAD", 14, 22);
      ctx.fillStyle = "#aab9c7"; ctx.fillText(Math.max(0, ROUTE_LENGTH - current.distance).toFixed(0) + " m TO FINISH", 14, 40);
      ctx.textAlign = "right"; ctx.fillStyle = "#9fb4c5"; ctx.fillText("← ONCOMING  |  YOUR DIRECTION →", width - 14, 22);
      if (current.crashed) {
        ctx.fillStyle = "#7b1f27cc"; ctx.fillRect(width * 0.18, height * 0.38, width * 0.64, 62);
        ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.font = "700 18px sans-serif"; ctx.fillText("CONTACT DETECTED · RESET TO CONTINUE", width / 2, height * 0.38 + 37);
      } else if (!running) {
        ctx.fillStyle = "#07121dcc"; ctx.fillRect(width * 0.28, height * 0.43, width * 0.44, 42);
        ctx.fillStyle = "#dceaf4"; ctx.textAlign = "center"; ctx.font = "600 13px sans-serif";
        ctx.fillText(current.distance === 0 ? "PRESS PLAY TO START FROM START" : "PREVIEW PAUSED", width / 2, height * 0.43 + 26);
      }
    };

    const tick = (timestamp: number) => {
      const dt = last ? clamp((timestamp - last) / 1000, 0, 0.05) : 0;
      last = timestamp;
      const current = stateRef.current;
      if (runningRef.current && !current.crashed && current.distance < ROUTE_LENGTH) {
        current.elapsed += dt;
        const egoLane = Math.round(current.laneTarget);
        const aheadHazard = hazards.find(h => h.lane === egoLane && h.s >= current.distance && h.s - current.distance < 115);
        const sameLaneTraffic = current.traffic.find(c => c.lane === egoLane && c.s > current.distance && c.s - current.distance < 48);
        const upcomingSignal = signals.find(signal => signal.s >= current.distance && signal.s - current.distance < 45);
        let brake = false;
        let desiredLane = current.laneTarget;
        if (upcomingSignal) {
          const cycle = (current.elapsed + upcomingSignal.s * 0.013) % 24;
          const phase = cycle < 10 ? "green" : cycle < 14 ? "yellow" : "red";
          const distanceToSignal = upcomingSignal.s - current.distance;
          if (phase === "red" || (phase === "yellow" && current.speed * current.speed / 8 + 7 > distanceToSignal)) brake = true;
        }
        if (aheadHazard) {
          const gap = aheadHazard.s - current.distance;
          if (controller === "steering") {
            const otherLane = egoLane === 2 ? 3 : 2;
            const laneBlocked = current.traffic.some(c => c.lane === otherLane && Math.abs(c.s - current.distance) < 70) || hazards.some(h => h.lane === otherLane && Math.abs(h.s - current.distance) < 55);
            if (!laneBlocked && gap < 92) desiredLane = otherLane;
            else if (gap < current.speed * current.speed / 10 + 15) brake = true;
          } else if (gap < current.speed * current.speed / 10 + (controller === "safety" ? 22 : 8)) {
            brake = true;
          }
        }
        if (sameLaneTraffic && sameLaneTraffic.s - current.distance < 24) {
          if (controller === "steering") {
            const otherLane = egoLane === 2 ? 3 : 2;
            const blocked = current.traffic.some(c => c.lane === otherLane && Math.abs(c.s - current.distance) < 55) || hazards.some(h => h.lane === otherLane && Math.abs(h.s - current.distance) < 45);
            if (!blocked) desiredLane = otherLane; else brake = true;
          } else brake = true;
        }
        current.laneTarget = desiredLane;
        current.lane += (current.laneTarget - current.lane) * Math.min(1, dt * 1.25);
        const targetSpeed = brake ? 0 : (controller === "safety" ? 16 : controller === "baseline" ? 20 : 19);
        const acceleration = brake ? 9 : 3.1;
        current.speed += clamp(targetSpeed - current.speed, -acceleration * dt, acceleration * dt);
        current.distance += current.speed * dt;
        current.traffic.forEach(car => { car.s += (car.lane < 2 ? -car.speed : car.speed) * dt; });
        current.traffic = current.traffic.filter(car => car.s > current.distance - 130 && car.s < current.distance + 260);
        if (current.distance > 180 && current.traffic.length < 9 && Math.random() < dt * 0.45) {
          const lane = Math.floor(Math.random() * 4);
          current.traffic.push({ id: spawnId++, lane, s: current.distance + 110 + Math.random() * 180, speed: lane < 2 ? 15 + Math.random() * 8 : 10 + Math.random() * 9, color: COLORS[Math.floor(Math.random() * COLORS.length)] });
        }
        for (const hazard of hazards) {
          if (Math.abs(hazard.s - current.distance) < 3.2 && Math.abs(current.lane - hazard.lane) < 0.42) {
            current.crashed = true; current.collisions += 1; current.speed = 0;
          }
        }
        if (current.distance >= ROUTE_LENGTH) current.speed = 0;
      }
      draw();
      if (timestamp - lastTelemetry > 160) {
        lastTelemetry = timestamp;
        const progress = Math.min(100, current.distance / ROUTE_LENGTH * 100);
        setHud({ speed: current.speed, distance: current.distance, lane: current.lane, signal: current.signal, collisions: current.collisions, status: current.crashed ? "COLLISION · RESET" : current.distance >= ROUTE_LENGTH ? "ROUTE COMPLETE" : runningRef.current ? "DRIVING" : current.distance > 0 ? "PAUSED" : "READY AT START" });
        telemetryRef.current({ speed: current.speed, progress, elapsed: current.elapsed, lane: current.lane, signal: current.signal, collisions: current.collisions });
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); };
  }, [controller, scenario, resetToken]);

  return (
    <div className="road-sim-wrap">
      <canvas ref={canvasRef} className="road-sim-canvas" aria-label="Animated four-lane autonomous driving preview. The ego vehicle travels forward from start, traffic flows in both directions, and signal and obstacle behavior is visualized." />
      <div className="road-sim-hud">
        <span className="road-hud-status"><i className={hud.status === "DRIVING" ? "road-hud-dot active" : "road-hud-dot"} />{hud.status}</span>
        <span>{(hud.speed * 3.6).toFixed(0)} km/h</span>
        <span>{hud.distance.toFixed(0)} / {ROUTE_LENGTH} m</span>
        <span>LANE {Math.round(hud.lane) + 1}</span>
        <span className={hud.signal === "RED" ? "signal-red" : hud.signal === "YELLOW" ? "signal-yellow" : "signal-green"}>SIGNAL {hud.signal}</span>
        <span>CONTACTS {hud.collisions}</span>
      </div>
    </div>
  );
}
