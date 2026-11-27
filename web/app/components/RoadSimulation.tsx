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

type TrafficCar = { id: number; lane: number; laneTarget?: number; laneChangeCooldown?: number; s: number; speed: number; color: string };
type Hazard = { s: number; lane: number; kind: "barrier" | "cone" };
type Signal = { s: number; phase: "green" | "yellow" | "red" };

const ROUTE_LENGTH = 2800;
const LANE_WIDTH = 3.6;
const COLORS = ["#e1a45e", "#a8b9c9", "#d86f72", "#7f9bd6", "#a5c88d", "#b5a0d6"];
const SPEED_LIMIT_KMH = 60;
const SPEED_LIMIT_MS = SPEED_LIMIT_KMH / 3.6;

function clamp(v: number, min: number, max: number) { return Math.max(min, Math.min(max, v)); }

export default function RoadSimulation({ running, controller, scenario, resetToken, onTelemetry }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ distance: 0, speed: 0, elapsed: 0, lane: 3, laneTarget: 3, collisions: 0, signal: "GREEN", crashed: false, traffic: [] as TrafficCar[] });
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
    let nextTrafficSpawnDistance = 190;
    let midRouteTrafficAdded = false;
    let hazards: Hazard[] = [];
    let signals: Signal[] = [];
    const s = stateRef.current;

    const createWorld = () => {
      hazards = [];
      if (scenario === "center") hazards.push({ s: 330, lane: 3, kind: "barrier" }, { s: 1120, lane: 2, kind: "cone" }, { s: 1920, lane: 3, kind: "barrier" });
      if (scenario === "edge") hazards.push({ s: 390, lane: 3, kind: "cone" }, { s: 960, lane: 2, kind: "barrier" }, { s: 1660, lane: 2, kind: "cone" });
      if (scenario === "outside") hazards.push({ s: 520, lane: 1, kind: "barrier" }, { s: 1180, lane: 0, kind: "cone" }, { s: 2080, lane: 3, kind: "barrier" });
      if (scenario === "multiple") hazards.push({ s: 300, lane: 3, kind: "barrier" }, { s: 345, lane: 2, kind: "cone" }, { s: 760, lane: 2, kind: "barrier" }, { s: 1280, lane: 3, kind: "cone" }, { s: 1810, lane: 2, kind: "barrier" }, { s: 2250, lane: 3, kind: "cone" });
      signals = [480, 1040, 1580, 2180, 2580].map((distance, i) => ({ s: distance, phase: i % 3 === 0 ? "red" : "green" }));
      // Start with a balanced stream of traffic in every lane. Vehicles are
      // staggered longitudinally so the road feels populated without spawning
      // cars on top of one another or immediately in the ego vehicle's path.
      s.traffic = [
        { id: 1, lane: 0, laneTarget: 0, s: 470, speed: 16, color: COLORS[0] },
        { id: 2, lane: 0, laneTarget: 0, s: 890, speed: 18, color: COLORS[1] },
        { id: 3, lane: 0, laneTarget: 0, s: 1320, speed: 15, color: COLORS[2] },
        { id: 4, lane: 0, laneTarget: 0, s: 1740, speed: 19, color: COLORS[3] },
        { id: 5, lane: 1, laneTarget: 1, s: 620, speed: 19, color: COLORS[4] },
        { id: 6, lane: 1, laneTarget: 1, s: 1040, speed: 15, color: COLORS[5] },
        { id: 7, lane: 1, laneTarget: 1, s: 1460, speed: 17, color: COLORS[0] },
        { id: 8, lane: 1, laneTarget: 1, s: 1880, speed: 14, color: COLORS[1] },
        { id: 9, lane: 2, laneTarget: 2, s: 430, speed: 12, color: COLORS[2] },
        { id: 10, lane: 2, laneTarget: 2, s: 820, speed: 16, color: COLORS[3] },
        { id: 11, lane: 2, laneTarget: 2, s: 1210, speed: 13, color: COLORS[4] },
        { id: 12, lane: 2, laneTarget: 2, s: 1610, speed: 17, color: COLORS[5] },
        { id: 13, lane: 3, laneTarget: 3, s: 300, speed: 12, color: COLORS[0] },
        { id: 14, lane: 3, laneTarget: 3, s: 700, speed: 16, color: COLORS[1] },
        { id: 15, lane: 3, laneTarget: 3, s: 1100, speed: 13, color: COLORS[2] },
        { id: 16, lane: 3, laneTarget: 3, s: 1510, speed: 17, color: COLORS[3] },
      ];
      spawnId = 17;
      nextTrafficSpawnDistance = 150;
      midRouteTrafficAdded = false;
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

    // Top-down passenger-car silhouette: tapered hood, cabin glass, mirrors,
    // four tires, headlights and tail lamps make vehicle orientation readable.
    const drawCar = (x: number, y: number, width: number, height: number, color: string, ego = false, opposite = false) => {
      ctx.save();
      ctx.translate(x, y);
      if (opposite) ctx.rotate(Math.PI);
      const w = width;
      const h = height;
      ctx.shadowColor = ego ? "#55baff" : "#00000066";
      ctx.shadowBlur = ego ? 15 : 4;
      // Tires sit outside the body.
      ctx.fillStyle = "#101820";
      for (const side of [-1, 1]) {
        ctx.beginPath();
        ctx.roundRect(side * w * 0.43 - w * 0.075, -h * 0.31, w * 0.15, h * 0.24, 2);
        ctx.roundRect(side * w * 0.43 - w * 0.075, h * 0.12, w * 0.15, h * 0.24, 2);
        ctx.fill();
      }
      // Sculpted body with a narrower hood and rounded rear.
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(-w * 0.31, h * 0.43);
      ctx.quadraticCurveTo(-w * 0.43, h * 0.39, -w * 0.43, h * 0.23);
      ctx.lineTo(-w * 0.39, -h * 0.20);
      ctx.quadraticCurveTo(-w * 0.37, -h * 0.38, -w * 0.23, -h * 0.46);
      ctx.quadraticCurveTo(0, -h * 0.52, w * 0.23, -h * 0.46);
      ctx.quadraticCurveTo(w * 0.37, -h * 0.38, w * 0.39, -h * 0.20);
      ctx.lineTo(w * 0.43, h * 0.23);
      ctx.quadraticCurveTo(w * 0.43, h * 0.39, w * 0.31, h * 0.43);
      ctx.closePath();
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = ego ? "#a9ddff" : "#ffffff55";
      ctx.lineWidth = 1;
      ctx.stroke();
      // Windshield and rear window, separated by the roof.
      ctx.fillStyle = "#182d3d";
      ctx.beginPath();
      ctx.moveTo(-w * 0.29, -h * 0.24);
      ctx.quadraticCurveTo(0, -h * 0.34, w * 0.29, -h * 0.24);
      ctx.lineTo(w * 0.25, -h * 0.04);
      ctx.lineTo(-w * 0.25, -h * 0.04);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#263f50";
      ctx.beginPath();
      ctx.moveTo(-w * 0.25, h * 0.12);
      ctx.lineTo(w * 0.25, h * 0.12);
      ctx.lineTo(w * 0.29, h * 0.31);
      ctx.quadraticCurveTo(0, h * 0.38, -w * 0.29, h * 0.31);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#3c5668";
      ctx.fillRect(-w * 0.23, -h * 0.015, w * 0.46, h * 0.12);
      // Side mirrors and front/rear lighting.
      ctx.fillStyle = color;
      ctx.fillRect(-w * 0.49, -h * 0.22, w * 0.12, h * 0.09);
      ctx.fillRect(w * 0.37, -h * 0.22, w * 0.12, h * 0.09);
      ctx.fillStyle = "#fff0b5";
      ctx.fillRect(-w * 0.29, -h * 0.46, w * 0.17, h * 0.035);
      ctx.fillRect(w * 0.12, -h * 0.46, w * 0.17, h * 0.035);
      ctx.fillStyle = "#ff625f";
      ctx.fillRect(-w * 0.31, h * 0.39, w * 0.19, h * 0.045);
      ctx.fillRect(w * 0.12, h * 0.39, w * 0.19, h * 0.045);
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
      // Roadside speed-limit boards, repeated along the route for a clear visual cue.
      for (let board = 0; board < 5; board++) {
        const routeS = Math.floor(current.distance / 500) * 500 + board * 500 + 120;
        const relative = routeS - current.distance;
        const boardY = egoY - relative * pxPerMeter;
        if (boardY < -45 || boardY > height + 45) continue;
        const boardX = left + roadWidth + 27;
        ctx.fillStyle = "#f7f7f2";
        ctx.beginPath(); ctx.arc(boardX, boardY, 17, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "#d84d4d"; ctx.lineWidth = 4; ctx.stroke();
        ctx.fillStyle = "#202b36"; ctx.font = "bold 10px sans-serif"; ctx.textAlign = "center";
        ctx.fillText(String(SPEED_LIMIT_KMH), boardX, boardY + 4);
      }
      ctx.fillStyle = "#f1d477"; ctx.font = "bold 11px monospace"; ctx.textAlign = "right";
      ctx.fillText("SPEED LIMIT " + SPEED_LIMIT_KMH + " km/h", width - 14, 42);
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
        // The signal gantry and stop lines serve only our-direction lanes 2
        // and 3. No signal hardware is drawn over the oncoming carriageway.
        ctx.fillStyle = "#1c252d"; ctx.fillRect(left + lanePx * 2, y - 32, lanePx * 2, 6);
        for (const signalLane of [2, 3]) {
          const signalX = left + lanePx * (signalLane + 0.5);
          ctx.fillStyle = "#252e37"; ctx.fillRect(signalX - 5, y - 28, 10, 40);
          const colors = ["#df5754", "#e5b34e", "#51c77d"];
          const active = signal.phase === "red" ? 0 : signal.phase === "yellow" ? 1 : 2;
          colors.forEach((color, i) => {
            ctx.fillStyle = i === active ? color : "#4b555d";
            ctx.beginPath(); ctx.arc(signalX, y - 20 + i * 10, 4, 0, Math.PI * 2); ctx.fill();
          });
          ctx.strokeStyle = "#f1d477"; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(signalX - lanePx * 0.42, y + 14); ctx.lineTo(signalX + lanePx * 0.42, y + 14); ctx.stroke();
          if (relative > 0 && relative < 34 && signal.phase !== "green") {
            ctx.fillStyle = "#f4d16f"; ctx.font = "600 10px sans-serif"; ctx.textAlign = "center";
            ctx.fillText("STOP", signalX, y + 29);
          }
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
      } else if (!runningRef.current) {
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
        const egoLane = Math.round(current.lane);
        const aheadHazard = hazards
          .filter(h => h.lane === egoLane && h.s >= current.distance)
          .sort((a, b) => a.s - b.s)[0];
        // Treat a vehicle as occupying our path while it is in our lane
        // OR actively merging into it. This catches cut-ins before the lane
        // animation reaches its midpoint.
        const sameLaneTraffic = current.traffic
          .filter(c => c.s > current.distance &&
            (Math.abs(c.lane - current.lane) < 0.72 ||
             (c.laneTarget !== undefined && Math.round(c.laneTarget) === egoLane)))
          .sort((a, b) => a.s - b.s)[0];
        const upcomingSignal = signals.find(signal => signal.s >= current.distance && signal.s - current.distance < 110);
        let brake = false;
        let desiredLane = current.laneTarget;
        let targetSpeed = Math.min(SPEED_LIMIT_MS, controller === "safety" ? 16 : controller === "baseline" ? 20 : 19);

        // Stop at the painted line. Red always means stop; yellow means stop if
        // braking safely is still possible. Green releases the car normally.
        if (upcomingSignal) {
          const cycle = (current.elapsed + upcomingSignal.s * 0.013) % 24;
          const phase = cycle < 10 ? "green" : cycle < 14 ? "yellow" : "red";
          const stopDistance = upcomingSignal.s - current.distance - 2.8;
          const shouldStop = phase === "red" || (phase === "yellow" && current.speed * current.speed / 8.4 + 2 > stopDistance);
          if (shouldStop && stopDistance > 0) {
            targetSpeed = Math.min(targetSpeed, Math.sqrt(Math.max(0, 2 * 4.2 * Math.max(0, stopDistance - 1))));
            brake = true;
          }
        }

        // Only merge into lanes travelling in our direction. Check both lanes,
        // the space ahead and behind, rear-car closing speed, and hazards.
        const laneIsSafe = (lane: number, requiredFrontGap: number) => {
          if (lane < 2 || lane > 3 || lane === egoLane) return false;
          const vehicles = current.traffic.filter(c => c.lane === lane);
          const front = vehicles.filter(c => c.s >= current.distance).sort((a, b) => a.s - b.s)[0];
          const rear = vehicles.filter(c => c.s < current.distance).sort((a, b) => b.s - a.s)[0];
          const frontGap = front ? front.s - current.distance : Infinity;
          const rearGap = rear ? current.distance - rear.s : Infinity;
          const rearClosingSpeed = rear ? Math.max(0, rear.speed - current.speed) : 0;
          const rearSafeGap = Math.max(16, 12 + rearClosingSpeed * 1.4);
          const laneHasHazard = hazards.some(h => h.lane === lane &&
            h.s > current.distance - 10 && h.s - current.distance < Math.max(95, current.speed * 3.2));
          return !laneHasHazard && frontGap > requiredFrontGap && rearGap > rearSafeGap;
        };

        const obstacleGap = aheadHazard ? aheadHazard.s - current.distance : Infinity;
        const carGap = sameLaneTraffic ? sameLaneTraffic.s - current.distance : Infinity;
        const obstacleManeuverDistance = Math.max(72, current.speed * 3.8);
        const needsObstacleAvoidance = obstacleGap < obstacleManeuverDistance;
        const closingSpeedToLead = sameLaneTraffic ? Math.max(0, current.speed - sameLaneTraffic.speed) : 0;
        const leadBrakingDistance = current.speed * 1.25 + (current.speed * current.speed) / (2 * 6.2);
        const needsTrafficAvoidance = carGap < Math.max(42, leadBrakingDistance + 12, current.speed * 2.6);
        const signalIsRed = upcomingSignal !== undefined &&
          ((current.elapsed + upcomingSignal.s * 0.013) % 24) >= 14;
        // A vehicle queued/stopped for a red light is not an overtaking target.
        // Hold the current lane and wait in the queue instead of repeatedly
        // trying to merge around it as traffic gaps fluctuate.
        const waitingBehindRedLight = signalIsRed &&
          upcomingSignal!.s - current.distance < 95;
        const stoppedVehicleAhead = sameLaneTraffic !== undefined &&
          sameLaneTraffic.speed < 1.8 && carGap < 75;
        const shouldQueueInLane = waitingBehindRedLight || stoppedVehicleAhead;
        // Complete an initiated lane change before evaluating another one.
        const laneChangeInProgress = Math.abs(current.lane - current.laneTarget) > 0.12;

        // Avoid weaving when adjacent lanes offer nearly identical progress.
        // Overtake only when a safe lane has a clearly larger front gap.
        if ((needsObstacleAvoidance || needsTrafficAvoidance) && !shouldQueueInLane && !laneChangeInProgress) {
          const requiredGap = needsObstacleAvoidance ? Math.max(32, current.speed * 1.8) : Math.max(24, current.speed * 1.35);
          const candidates = [2, 3]
            .filter(lane => lane !== egoLane)
            .map(lane => {
              const front = current.traffic
                .filter(c => c.lane === lane && c.s >= current.distance)
                .sort((a, b) => a.s - b.s)[0];
              return { lane, frontGap: front ? front.s - current.distance : Infinity };
            })
            .sort((a, b) => b.frontGap - a.frontGap);
          const bestLane = candidates.find(candidate =>
            laneIsSafe(candidate.lane, requiredGap) &&
            (needsObstacleAvoidance || candidate.frontGap > carGap + 24));
          if (bestLane !== undefined) {
            desiredLane = bestLane.lane;
          } else if (needsObstacleAvoidance) {
            brake = true;
            const usableStoppingDistance = Math.max(0, obstacleGap - 9);
            targetSpeed = Math.min(targetSpeed, Math.sqrt(2 * 4.6 * usableStoppingDistance));
          } else if (sameLaneTraffic) {
            brake = true;
            targetSpeed = Math.min(targetSpeed, Math.max(0, sameLaneTraffic.speed - 1));
          }
        }

        // Independently maintain a safe following gap. Brake smoothly based on
        // distance and relative speed instead of waiting until the last moment.
        if (sameLaneTraffic && carGap < Math.max(58, leadBrakingDistance + 18)) {
          // React early to a slowing or merging lead vehicle. Include closing
          // speed and a reaction-time buffer so braking starts before a cut-in
          // becomes an emergency.
          brake = true;
          const usableGap = Math.max(0, carGap - 10 - closingSpeedToLead * 0.8);
          const safeFollowingSpeed = Math.sqrt(2 * 6.2 * usableGap);
          const speedMatchedTarget = sameLaneTraffic.speed + Math.max(0, carGap - 20) * 0.16;
          targetSpeed = Math.min(targetSpeed, safeFollowingSpeed, speedMatchedTarget);
        }
        if (brake && targetSpeed > current.speed) targetSpeed = current.speed;
        current.laneTarget = desiredLane;
        current.lane += (current.laneTarget - current.lane) * Math.min(1, dt * 1.25);
        // Faster, responsive launch after green while preserving smooth braking.
        const acceleration = targetSpeed < current.speed ? 8.2 : 8.0;
        current.speed += clamp(targetSpeed - current.speed, -acceleration * dt, acceleration * dt);
        current.distance += current.speed * dt;
        current.traffic.forEach(car => {
          const direction = car.lane < 2 ? -1 : 1;
          // Traffic vehicles can route around either a stopped vehicle or a
          // fixed obstacle. A car must not wait forever behind a blocked leader
          // when the neighboring lane has a safe opening.
          const laneChanging = car.laneTarget !== undefined && Math.abs(car.lane - car.laneTarget) > 0.08;
          let slowForBlockedPath = false;
          let blockedPathDistance = Infinity;
          if (!laneChanging) {
            const laneAhead = current.traffic
              .filter(other => other.id !== car.id && Math.round(other.lane) === Math.round(car.lane) &&
                (direction > 0 ? other.s > car.s : other.s < car.s))
              .sort((a, b) => direction > 0 ? a.s - b.s : b.s - a.s)[0];
            const gapAhead = laneAhead ? Math.abs(laneAhead.s - car.s) : Infinity;
            const obstacleAhead = hazards
              .filter(h => Math.round(h.lane) === Math.round(car.lane) &&
                (direction > 0 ? h.s > car.s : h.s < car.s))
              .sort((a, b) => direction > 0 ? a.s - b.s : b.s - a.s)[0];
            const obstacleGap = obstacleAhead ? Math.abs(obstacleAhead.s - car.s) : Infinity;
            const blockedByVehicle = laneAhead !== undefined && gapAhead < 82 &&
              (laneAhead.speed < car.speed - 1.2 || gapAhead < 38);
            const blockedByObstacle = obstacleAhead !== undefined && obstacleGap < Math.max(105, car.speed * 4.5);
            if (blockedByVehicle || blockedByObstacle) {
              blockedPathDistance = Math.min(gapAhead, obstacleGap);
              const sameDirectionLanes = direction > 0 ? [2, 3] : [0, 1];
              const alternatives = sameDirectionLanes
                .filter(candidate => candidate !== Math.round(car.lane))
                .map(candidate => {
                  // A vehicle reserves BOTH its current lane and intended lane
                  // throughout a merge. This prevents another vehicle from
                  // choosing the same opening while the first car is crossing.
                  const vehicles = current.traffic.filter(other =>
                    other.id !== car.id &&
                    (Math.round(other.lane) === candidate ||
                     (other.laneTarget !== undefined && Math.round(other.laneTarget) === candidate)));
                  const front = vehicles
                    .filter(other => direction > 0 ? other.s > car.s : other.s < car.s)
                    .sort((a, b) => direction > 0 ? a.s - b.s : b.s - a.s)[0];
                  const rear = vehicles
                    .filter(other => direction > 0 ? other.s < car.s : other.s > car.s)
                    .sort((a, b) => direction > 0 ? b.s - a.s : a.s - b.s)[0];
                  let frontGap = front ? Math.abs(front.s - car.s) : Infinity;
                  let rearGap = rear ? Math.abs(car.s - rear.s) : Infinity;
                  let rearClosingSpeed = rear ? Math.max(0, rear.speed - car.speed) : 0;

                  // Include the ego vehicle and its intended lane in the same
                  // clearance calculation, so traffic cannot merge across it.
                  const egoLaneReserved = Math.round(current.lane) === candidate ||
                    Math.round(current.laneTarget) === candidate;
                  if (egoLaneReserved) {
                    const egoIsAhead = direction > 0
                      ? current.distance > car.s
                      : current.distance < car.s;
                    const egoGap = Math.abs(car.s - current.distance);
                    if (egoIsAhead && egoGap < frontGap) {
                      frontGap = egoGap;
                    } else if (!egoIsAhead && egoGap < rearGap) {
                      rearGap = egoGap;
                      rearClosingSpeed = Math.max(0, current.speed - car.speed);
                    }
                  }
                  const rearSafeGap = Math.max(58, 34 + rearClosingSpeed * 2.4);
                  const blockedLane = hazards.some(h => Math.round(h.lane) === candidate &&
                    (direction > 0 ? h.s > car.s && h.s - car.s < 145 : h.s < car.s && car.s - h.s < 145));
                  const frontIsTooClose = frontGap < 76;
                  const anotherCarMergingIntoLane = vehicles.some(other =>
                    other.laneTarget !== undefined &&
                    Math.round(other.laneTarget) === candidate &&
                    Math.abs(other.lane - other.laneTarget) > 0.08);
                  return {
                    lane: candidate,
                    frontGap,
                    safe: !blockedLane && !frontIsTooClose &&
                      rearGap > rearSafeGap && !anotherCarMergingIntoLane,
                  };
                })
                .filter(candidate => candidate.safe)
                .sort((a, b) => b.frontGap - a.frontGap);
              // Avoid lane weaving: after a merge, hold that lane for a while.
              // If no safe opening exists (or the cooldown is active), stay put
              // and reduce speed rather than repeatedly hunting for another lane.
              if (alternatives.length > 0 && (car.laneChangeCooldown ?? 0) <= 0) {
                car.laneTarget = alternatives[0].lane;
                car.laneChangeCooldown = 9;
              } else {
                slowForBlockedPath = true;
              }
            }
            if (car.laneChangeCooldown !== undefined && car.laneChangeCooldown > 0) {
              car.laneChangeCooldown = Math.max(0, car.laneChangeCooldown - dt);
            }
          }
          if (car.laneTarget !== undefined) {
            car.lane += (car.laneTarget - car.lane) * Math.min(1, dt * 1.1);
          }
          // Signals belong only to the two lanes travelling with the ego
          // vehicle. Oncoming lanes have their own opposing signal system and
          // must not react to this carriageway's red lights.
          const nextSignal = direction > 0
            ? signals.filter(signal => signal.s > car.s).sort((a, b) => a.s - b.s)[0]
            : undefined;
          const nominalSpeed = Math.min(SPEED_LIMIT_MS, car.lane < 2 ? 15 + (car.id % 5) : 10 + (car.id % 7));
          let trafficTarget = nominalSpeed;
          if (slowForBlockedPath) {
            const safeGap = Math.max(0, blockedPathDistance - 24);
            trafficTarget = Math.min(trafficTarget, Math.sqrt(2 * 3.4 * safeGap));
          }
          // Merging vehicles ease off the throttle while crossing the lane line.
          // This gives nearby traffic time to recognize the reserved space and
          // prevents two fast lane changes from converging at the same point.
          if (laneChanging) {
            trafficTarget = Math.min(trafficTarget, Math.max(6.5, car.speed - 2.4));
          }
          // Traffic reacts to stationary hazards in its lane: brake to a safe
          // standstill before the object instead of clipping through it.
          const trafficHazard = hazards
            .filter(h => (Math.round(h.lane) === Math.round(car.lane) ||
              (laneChanging && Math.round(h.lane) === Math.round(car.laneTarget ?? car.lane))) &&
              (direction > 0 ? h.s > car.s : h.s < car.s))
            .sort((a, b) => direction > 0 ? a.s - b.s : b.s - a.s)[0];
          if (trafficHazard) {
            const hazardGap = Math.abs(trafficHazard.s - car.s) - 10;
            if (hazardGap < Math.max(45, car.speed * 3.2)) {
              trafficTarget = Math.min(trafficTarget, Math.sqrt(Math.max(0, 2 * 5.2 * Math.max(0, hazardGap))));
              if (hazardGap <= 1.5) trafficTarget = 0;
            }
          }
          if (nextSignal) {
            const phase = (current.elapsed + nextSignal.s * 0.013) % 24;
            const redOrYellow = phase >= 10;
            const distanceToLine = Math.abs(nextSignal.s - car.s) - 2.8;
            if (redOrYellow && distanceToLine > 0) {
              trafficTarget = Math.min(trafficTarget, Math.sqrt(Math.max(0, 2 * 5.2 * Math.max(0, distanceToLine - 1))));
            }
            if (redOrYellow && distanceToLine <= 1.2) trafficTarget = 0;
          }
          // Queue naturally: never drive into the vehicle ahead or allow cars
          // to occupy the same longitudinal space in a lane.
          const sameLaneAhead = current.traffic
            .filter(other => other.id !== car.id && Math.round(other.lane) === Math.round(car.lane) &&
              (direction > 0 ? other.s > car.s : other.s < car.s))
            .sort((a, b) => direction > 0 ? a.s - b.s : b.s - a.s)[0];
          if (sameLaneAhead) {
            const gap = Math.abs(sameLaneAhead.s - car.s) - 22;
            const followSpeed = Math.sqrt(Math.max(0, 2 * 4.5 * Math.max(0, gap)));
            trafficTarget = Math.min(trafficTarget, followSpeed, sameLaneAhead.speed + Math.max(0, gap - 10) * 0.08);
          }
          // Treat the ego vehicle as a real lead vehicle for traffic behind it.
          // This is critical when the ego stops at a red light: following cars
          // must brake and queue instead of driving into the rear bumper.
          if (direction > 0 && car.lane >= 2 && Math.abs(car.lane - current.lane) < 0.42 && car.s < current.distance) {
            const egoGap = current.distance - car.s - 24;
            const egoFollowSpeed = Math.sqrt(Math.max(0, 2 * 5.2 * Math.max(0, egoGap)));
            trafficTarget = Math.min(
              trafficTarget,
              egoFollowSpeed,
              current.speed + Math.max(0, egoGap - 8) * 0.08,
            );
          }
          car.speed += clamp(trafficTarget - car.speed, -8 * dt, 4.5 * dt);
          car.s += direction * car.speed * dt;
        });
        // Keep a longer look-ahead buffer. The old +260m cutoff deleted the
        // initial oncoming vehicles before they could enter the visible area.
        current.traffic = current.traffic.filter(car => car.s > current.distance - 180 && car.s < current.distance + 560);
        if (current.distance >= nextTrafficSpawnDistance && current.traffic.length < 40) {
          // Denser, staggered traffic makes the lane-selection/overtake behavior
          // visible without placing a new car directly on top of existing traffic.
          const id = spawnId++;
          const lane = id % 4;
          const spawnS = current.distance + (lane < 2 ? 230 + (id % 5) * 38 : 145 + (id % 5) * 34);
          const spawnLaneClear = current.traffic.every(other =>
            Math.round(other.lane) !== lane || Math.abs(other.s - spawnS) > 55);
          if (spawnLaneClear) {
            current.traffic.push({ id, lane, laneTarget: lane, s: spawnS, speed: Math.min(SPEED_LIMIT_MS, lane < 2 ? 15 + (id % 5) : 10 + (id % 7)), color: COLORS[id % COLORS.length] });
          }
          nextTrafficSpawnDistance = current.distance + 38 + (id % 3) * 16;
        }

        // At 50% route completion, add a staggered group of slower
        // same-direction vehicles to create following and overtaking interactions.
        if (!midRouteTrafficAdded && current.distance >= ROUTE_LENGTH * 0.5) {
          midRouteTrafficAdded = true;
          const surgeCars = [
            { lane: 2, offset: 155, speed: 10 },
            { lane: 2, offset: 265, speed: 13 },
            { lane: 2, offset: 385, speed: 11 },
            { lane: 2, offset: 505, speed: 14 },
            { lane: 3, offset: 195, speed: 12 },
            { lane: 3, offset: 315, speed: 10 },
            { lane: 3, offset: 435, speed: 14 },
            { lane: 3, offset: 555, speed: 12 },
          ];
          for (const surge of surgeCars) {
            const spawnS = current.distance + surge.offset;
            const laneClear = current.traffic.every(other =>
              Math.round(other.lane) !== surge.lane || Math.abs(other.s - spawnS) > 58);
            if (laneClear) {
              const id = spawnId++;
              current.traffic.push({
                id,
                lane: surge.lane,
                laneTarget: surge.lane,
                s: spawnS,
                speed: surge.speed,
                color: COLORS[id % COLORS.length],
              });
            }
          }
        }
        for (const hazard of hazards) {
          if (Math.abs(hazard.s - current.distance) < 3.2 && Math.abs(current.lane - hazard.lane) < 0.42) {
            current.crashed = true; current.collisions += 1; current.speed = 0;
          }
        }
        for (const car of current.traffic) {
          const longitudinalGap = Math.abs(car.s - current.distance);
          if (longitudinalGap < 4.8 && Math.abs(current.lane - car.lane) < 0.42) {
            current.crashed = true;
            current.collisions += 1;
            current.speed = 0;
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
