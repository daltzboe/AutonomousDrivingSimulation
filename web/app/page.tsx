"use client";

import { useEffect, useState } from "react";
import RoadSimulation from "./components/RoadSimulation";

type Controller = "baseline" | "safety" | "steering" | "intelligent";
type Scenario = "clear" | "center" | "edge" | "outside" | "multiple";
type ComparisonReport = { scenario: Scenario; episode_count_per_controller: number; reports: BenchmarkReport[]; interpretation: string };
type BenchmarkReport = {
  controller: Controller;
  scenario: Scenario;
  episode_count: number;
  aggregate: {
    mean_lane_deviation_m: number | null;
    std_lane_deviation_m: number | null;
    mean_collision_events: number;
    std_collision_events: number | null;
    mean_route_completion_pct: number;
    std_route_completion_pct: number | null;
    safe_stop_rate: number;
  };
  episodes: { collision_events: number; completed: number; stopped_before_route: number }[];
};
const simulatorApi = process.env.NEXT_PUBLIC_SIMULATOR_API_URL || "http://127.0.0.1:8000";
const scenarios: Record<Scenario, { label: string; obstacles: { x: number; y: number }[] }> = {
  clear: { label: "Clear road", obstacles: [] },
  center: { label: "Center obstacle", obstacles: [{ x: 50, y: 35 }] },
  edge: { label: "Lane-edge obstacle", obstacles: [{ x: 50, y: 22 }] },
  outside: { label: "Outside-lane obstacle", obstacles: [{ x: 50, y: 8 }] },
  multiple: { label: "Multiple obstacles", obstacles: [{ x: 43, y: 35 }, { x: 66, y: 24 }] },
};

export default function Dashboard() {
  const [controller, setController] = useState<Controller>("intelligent");
  const [scenario, setScenario] = useState<Scenario>("center");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(0);
  const [ticks, setTicks] = useState(0);
  const [previewResetToken, setPreviewResetToken] = useState(0);
  const [previewLane, setPreviewLane] = useState(3);
  const [previewSignal, setPreviewSignal] = useState("GREEN");
  const [previewCollisions, setPreviewCollisions] = useState(0);
  const [previewMode, setPreviewMode] = useState("CRUISE");
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [comparison, setComparison] = useState<ComparisonReport | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [episodeCount, setEpisodeCount] = useState(10);
  const [benchmarkError, setBenchmarkError] = useState("");

  useEffect(() => {
    let active = true;
    fetch(`${simulatorApi}/api/health`)
      .then((response) => { if (!response.ok) throw new Error("API unavailable"); return response.json(); })
      .then((health) => { if (active && health.status === "ok") setApiStatus("online"); })
      .catch(() => { if (active) setApiStatus("offline"); });
    return () => { active = false; };
  }, []);

  const obstacleCount = scenarios[scenario].obstacles.length;

  const status = previewCollisions > 0 ? "Contact · reset" : progress >= 100 ? "Route complete" : running ? "Driving" : progress > 0 ? "Paused" : "Ready at start";
  const completion = Math.round(progress);
  const elapsed = (ticks * 0.1).toFixed(1);

  function reset() { setRunning(false); setProgress(0); setSpeed(0); setTicks(0); setPreviewLane(3); setPreviewSignal("GREEN"); setPreviewCollisions(0); setPreviewMode("CRUISE"); setPreviewResetToken((value) => value + 1); }
  function run() { if (progress >= 100 || previewCollisions > 0) reset(); setRunning(true); }
  function updatePreview(value: { speed: number; progress: number; elapsed: number; lane: number; signal: string; collisions: number; mode: string }) { setSpeed(value.speed); setProgress(value.progress); setTicks(Math.round(value.elapsed * 10)); setPreviewLane(value.lane); setPreviewSignal(value.signal); setPreviewCollisions(value.collisions); setPreviewMode(value.mode); if (value.collisions > 0 || value.progress >= 100) setRunning(false); }

  async function runBenchmark() {
    setBenchmarkLoading(true);
    setBenchmarkError("");
    try {
      const response = await fetch(`${simulatorApi}/api/benchmark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ controller, scenario, episodes: episodeCount }),
      });
      const payload = await response.json().catch(() => ({ error: "The simulator returned an unreadable response. Check the Python API logs." }));
      if (!response.ok) throw new Error(payload.error || `Benchmark failed (${response.status}).`);
      setBenchmark(payload.report as BenchmarkReport);
    } catch (error) {
      setBenchmarkError(error instanceof Error ? error.message : "Could not connect to the Python simulator.");
    } finally {
      setBenchmarkLoading(false);
    }
  }

  async function runComparison() {
  setComparisonLoading(true);
  setBenchmarkError("");
  try {
    const response = await fetch(`${simulatorApi}/api/compare`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, episodes: Math.min(episodeCount, 25) }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `Comparison failed (${response.status}).`);
    setComparison(payload.report as ComparisonReport);
  } catch (error) {
    setBenchmarkError(error instanceof Error ? error.message : "Could not connect to the Python simulator.");
  } finally { setComparisonLoading(false); }
  }


  function exportComparison() {
    if (!comparison) return;
    const blob = new Blob([JSON.stringify(comparison, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `autonomy-controller-comparison-${comparison.scenario}-${comparison.episode_count_per_controller}episodes.json`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">A<span>V</span></div><div><strong>Autonomy Lab</strong><small>RESEARCH PLATFORM</small></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>
          <a className="nav-item active" href="#overview"><span aria-hidden="true">◫</span> Overview</a>
          <a className="nav-item" href="#simulation"><span aria-hidden="true">⌁</span> Simulation</a>
          <a className="nav-item" href="#benchmarks"><span aria-hidden="true">▥</span> Benchmarks</a>
          <a className="nav-item" href="#sensor-data"><span aria-hidden="true">◉</span> Telemetry</a>
          <a className="nav-item" href="#experiments"><span aria-hidden="true">⌘</span> Experiments</a>
        </nav>
        <div className="sidebar-bottom"><div className="project-chip"><span className="pulse-dot" /> PROJECT STATUS <b>IN DEVELOPMENT</b></div><div className="profile"><div className="avatar">DO</div><div><strong>Dalton Opudo</strong><small>Researcher · UTSA</small></div><span className="more">···</span></div></div>
      </aside>

      <section className="main">
        <header className="topbar"><div className="crumb">Projects <span>/</span> <b>Autonomous Driving Simulation</b></div><div className="top-actions"><span className={`env-pill api-status ${apiStatus}`} aria-live="polite">● {apiStatus === "checking" ? "CHECKING PYTHON API" : apiStatus === "online" ? "PYTHON API CONNECTED" : "PYTHON API OFFLINE · START BACKEND"}</span><div className="top-avatar">DO</div></div></header>
        <div className="content" id="overview">
          <div className="page-heading"><div><div className="eyebrow">RESEARCH OVERVIEW <span>•</span> EXPERIMENT 001</div><h1>Autonomous Driving <em>Research</em></h1><p>Team research project · Dalton Opudo, Dexter & William. Evaluate controllers with reproducible Python experiments.</p></div><button className="export-btn" onClick={() => window.print()}>↥ <span>Export view</span></button></div>

          <div className="stats-grid">
            <Stat label="SIMULATION STATUS" value={previewCollisions > 0 ? "Contact" : running ? "Running" : progress >= 100 ? "Complete" : "At start"} detail={previewCollisions > 0 ? "Reset after simulated contact" : running ? "Browser road simulation active" : progress === 0 ? "Ready at route start" : "Preview paused"} icon="◉" accent={running ? "green" : "blue"} />
            <Stat label="PREVIEW SPEED" value={(speed * 2.236936).toFixed(1)} unit="mph" detail="Live browser vehicle speed" icon="↗" accent="blue" />
            <Stat label="PREVIEW PROGRESS" value={completion.toString()} unit="%" detail="1.74 mi route progress" icon="⌁" accent="orange" />
            <Stat label="SCENARIO HAZARDS" value={String(obstacleCount)} detail="Configured road obstacles" icon="◎" accent="purple" />
          </div>

          <div className="section-row" id="simulation"><div><h2>Browser preview</h2><p>1.74 mi browser-driving preview · live traffic, traffic signals, and controller behavior</p></div><div className="live-status"><span className={running ? "pulse-dot" : "muted-dot"} />{status}</div></div>
          <div className="simulation-grid">
            <div className="panel sim-panel driving-focus">
              <div className="panel-head"><div><strong>Four-lane road · forward journey</strong><small>2 LANES EACH DIRECTION · 2.8 KM ROUTE</small></div><div className="view-tag">LIVE 2D</div></div>
              <RoadSimulation running={running} controller={controller} scenario={scenario} resetToken={previewResetToken} onTelemetry={updatePreview} />
              <div className="sim-controls"><button className="primary-btn" disabled={benchmarkLoading || comparisonLoading} onClick={() => void runBenchmark()}>{benchmarkLoading ? "Running Python benchmark…" : "▶  Run Python benchmark"}</button><button className="secondary-btn" aria-pressed={running} onClick={() => running ? setRunning(false) : run()}>{running ? "Ⅱ  Pause driving" : previewCollisions > 0 ? "↺  Reset & restart" : progress === 0 ? "▷  Start driving" : progress >= 100 ? "▷  Run again" : "▷  Resume driving"}</button><button className="secondary-btn" aria-label="Reset browser preview" onClick={reset}>↺ Reset</button><div className="control-divider" /><label>CONTROLLER<select value={controller} onChange={(e) => {setController(e.target.value as Controller); setBenchmark(null); reset();}}><option value="baseline">Baseline · lane following</option><option value="safety">Safety · emergency brake</option><option value="steering">Steering · obstacle avoidance</option><option value="intelligent">Intelligent · decision controller</option></select></label><label>EPISODES<select value={episodeCount} onChange={(e) => {setEpisodeCount(Number(e.target.value)); setBenchmark(null);}}><option value={1}>1 · Quick check</option><option value={10}>10 · Standard</option><option value={25}>25 · Extended</option><option value={50}>50 · Deep run</option></select></label><label>SCENARIO<select value={scenario} onChange={(e) => {setScenario(e.target.value as Scenario); setBenchmark(null); setComparison(null); reset();}}><option value="clear">Clear road</option><option value="center">Center obstacle</option><option value="edge">Lane-edge obstacle</option><option value="outside">Outside-lane obstacle</option><option value="multiple">Multiple obstacles</option></select></label></div>
            </div>
            <div className="right-stack">
              <div className="panel telemetry-panel" id="sensor-data"><div className="panel-head"><div><strong>Preview readout</strong><small>ANIMATION VALUES · NOT PYTHON TELEMETRY</small></div><span className="telemetry-icon">⌁</span></div><Telemetry label="Longitudinal speed" value={(speed * 2.236936).toFixed(1)} unit="mph" pct={speed / 31.3 * 100}/><Telemetry label="Current lane" value={(Math.round(previewLane) + 1).toString()} unit="/ 4" pct={(previewLane + 1) * 25}/><Telemetry label="Route progress" value={completion.toString()} unit="%" pct={completion}/><Telemetry label="Driving decision" value={controller === "intelligent" ? previewMode : "—"} unit="" pct={controller === "intelligent" ? (previewMode === "CRUISE" ? 25 : previewMode === "APPROACH" ? 50 : previewMode === "AVOID" ? 80 : 100) : 0}/><Telemetry label="Traffic signal" value={previewSignal} unit="" pct={previewSignal === "GREEN" ? 100 : previewSignal === "YELLOW" ? 60 : 20}/><div className="telemetry-foot"><span>SIM TIME</span><b>{elapsed}s</b><span>CONTACTS</span><b>{previewCollisions}</b></div></div>
              <div className="panel controller-panel"><div className="panel-head"><div><strong>Active controller</strong><small>CONTROL STRATEGY</small></div><span className="controller-badge">● ACTIVE</span></div><div className="controller-name">{controller === "baseline" ? "Pure pursuit" : controller === "safety" ? "Emergency braking" : controller === "intelligent" ? "Intelligent decision controller" : "Steering avoidance"}</div><p>{controller === "baseline" ? "Maintains the lane with basic following behavior and signal braking." : controller === "safety" ? "Maintains its lane and applies conservative emergency braking for hazards." : controller === "intelligent" ? "Displays CRUISE, APPROACH, AVOID, and BRAKE decisions in the browser preview. Python benchmarks use the separate rule-based controller." : "Changes lanes around a clear hazard or slower vehicle, while stopping at red lights."}</p><div className="controller-meta"><span>DECISION</span><b>{controller === "intelligent" ? previewMode : "STANDARD"}</b><span>LEARNING</span><b>NOT TRAINED</b></div></div>
            </div>
          </div>

          <div className="section-row benchmark-heading" id="benchmarks"><div><h2>Experiment insights</h2><p>Metrics returned by the Python benchmark</p></div><span className="dataset-label">{benchmark ? "PYTHON BENCHMARK · REAL RESULT" : "WAITING FOR PYTHON RUN"}</span></div>
          <div className="bottom-grid">
            <div className="panel insight-panel"><div className="panel-head"><div><strong>Scenario configuration</strong><small>DETERMINISTIC TEST SETUP</small></div></div><div className="scenario-row"><div className="scenario-icon">⌖</div><div><b>{scenarios[scenario].label}</b><small>{obstacleCount} scenario hazard setting · Four-lane two-way traffic</small></div><span className="scenario-state">SELECTED</span></div><div className="scenario-details"><span>ROAD WIDTH <b>47.2 ft · 4 lanes</b></span><span>ROUTE LENGTH <b>1.74 mi</b></span><span>TRAFFIC <b>2 directions</b></span></div></div>
            <div className="panel insight-panel"><div className="panel-head"><div><strong>Research metrics</strong><small>{benchmark ? `PYTHON · ${benchmark.episode_count} EPISODE` : "REAL RESULTS APPEAR AFTER A PYTHON RUN"}</small></div></div>{benchmarkError && <p role="alert" className="api-error">{benchmarkError}</p>}<div className="metric-list"><div><span>Mean lane deviation</span><b>{benchmark?.aggregate.mean_lane_deviation_m == null ? "—" : (benchmark.aggregate.mean_lane_deviation_m * 3.28084).toFixed(2)}<small> ft</small></b></div><div><span>Mean collision events</span><b>{benchmark ? benchmark.aggregate.mean_collision_events.toFixed(2) : "—"}</b></div><div><span>Route completion</span><b>{benchmark ? benchmark.aggregate.mean_route_completion_pct.toFixed(1) : "—"}<small>%</small></b></div><div><span>Safe-stop rate</span><b>{benchmark ? (benchmark.aggregate.safe_stop_rate * 100).toFixed(0) : "—"}<small>%</small></b></div><div><span>Steering MAE</span><b>Not measured</b></div></div>{benchmark && <p className="benchmark-note">Completed {benchmark.episodes.filter((episode) => episode.completed).length} of {benchmark.episode_count} episodes. Simulator: lightweight 2D.</p>}</div>
          </div>

          <div className="section-row benchmark-heading" id="experiments"><div><h2>Controller comparison</h2><p>Matched scenario · Python benchmark output</p></div><button className="secondary-btn" disabled={comparisonLoading || benchmarkLoading} onClick={() => void runComparison()}>{comparisonLoading ? "Comparing…" : `Compare all 4 · ${Math.min(episodeCount, 25)} each`}</button></div>
          {comparison && <div className="panel comparison-panel"><div className="panel-head"><div><strong>Matched controller benchmark</strong><small>{comparison.scenario.toUpperCase()} · {comparison.episode_count_per_controller} EPISODES EACH</small></div><span className="dataset-label">PYTHON OUTPUT</span></div><div className="comparison-export"><button className="secondary-btn" onClick={exportComparison}>↓ Download JSON data</button><span>Machine-readable report for your team's analysis</span></div><div className="comparison-table"><div className="comparison-header"><span>CONTROLLER</span><span>COLLISIONS ↓</span><span>COMPLETION ↑</span><span>LANE ERROR ↓</span></div>{comparison.reports.map((item) => <div className="comparison-row" key={item.controller}><b>{item.controller === "baseline" ? "Pure pursuit" : item.controller === "safety" ? "Emergency brake" : item.controller === "intelligent" ? "Intelligent decisions" : "Steering avoidance"}</b><span>{item.aggregate.mean_collision_events.toFixed(2)}</span><span className="completion-cell"><div className="comparison-meter"><i style={{width: `${Math.max(0,Math.min(100,item.aggregate.mean_route_completion_pct))}%`}} /></div><strong>{item.aggregate.mean_route_completion_pct.toFixed(1)}%</strong><small>± {item.aggregate.std_route_completion_pct == null ? "—" : item.aggregate.std_route_completion_pct.toFixed(2)}</small></span><span>{item.aggregate.mean_lane_deviation_m == null ? "N/A" : `${(item.aggregate.mean_lane_deviation_m * 3.28084).toFixed(2)} ft`}</span></div>)}</div><p className="comparison-note">{comparison.interpretation} Deterministic repeats are consistency checks, not independent randomized trials.</p></div>}
          <footer><span>Autonomy Lab <b>·</b> UTSA Computer Science Research Project</span><span>SIMULATION BUILD 0.1.0 <b>·</b> NOT FOR REAL-WORLD VEHICLE CONTROL</span></footer>
        </div>
      </section>
    </main>
  );
}

function Stat({label,value,unit,detail,icon,accent}:{label:string;value:string;unit?:string;detail:string;icon:string;accent:string}) {
  return <div className="panel stat-card"><div className="stat-top"><span>{label}</span><i className={"stat-icon "+accent}>{icon}</i></div><div className="stat-value">{value}<small>{unit}</small></div><div className="stat-detail"><span className="detail-dot" />{detail}</div></div>;
}
function Telemetry({label,value,unit,pct}:{label:string;value:string;unit:string;pct:number}) {
  return <div className="telemetry-item"><div><span>{label}</span><b>{value}<small> {unit}</small></b></div><div className="meter"><i style={{width:Math.max(2,Math.min(100,pct))+"%"}} /></div></div>;
}
