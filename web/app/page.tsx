"use client";

import { useEffect, useMemo, useState } from "react";

type Controller = "baseline" | "safety" | "steering";
type Scenario = "clear" | "center" | "edge" | "outside" | "multiple";
type ComparisonReport = { scenario: Scenario; episode_count_per_controller: number; reports: BenchmarkReport[]; interpretation: string };
type BenchmarkReport = {
  controller: Controller;
  scenario: Scenario;
  episode_count: number;
  aggregate: {
    mean_lane_deviation_m: number | null;
    mean_collision_events: number;
    mean_route_completion_pct: number;
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
  const [controller, setController] = useState<Controller>("steering");
  const [scenario, setScenario] = useState<Scenario>("center");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(18);
  const [speed, setSpeed] = useState(42);
  const [ticks, setTicks] = useState(0);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [comparison, setComparison] = useState<ComparisonReport | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [episodeCount, setEpisodeCount] = useState(10);
  const [benchmarkError, setBenchmarkError] = useState("");

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => {
      setProgress((p) => {
        if (p >= 94) { setRunning(false); return 94; }
        return p + 0.55;
      });
      setTicks((t) => t + 1);
      setSpeed((s) => Math.max(28, Math.min(62, s + (Math.random() - 0.48) * 2)));
    }, 100);
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

  return () => window.clearInterval(timer);
  }, [running]);

  const obstacleCount = scenarios[scenario].obstacles.length;
  const laneOffset = controller === "steering" && scenario !== "clear" && progress > 35 && progress < 72 ? 7 : 0;
  const status = !running && progress >= 94 ? "Episode complete" : running ? "Simulation running" : "Ready to run";
  const completion = Math.min(100, Math.round((progress - 18) / 76 * 100));
  const elapsed = useMemo(() => (ticks * 0.1).toFixed(1), [ticks]);

  function reset() { setRunning(false); setProgress(18); setSpeed(42); setTicks(0); }
  function run() { if (progress >= 94) reset(); setRunning(true); }

  async function runBenchmark() {
    setBenchmarkLoading(true);
    setBenchmarkError("");
    try {
      const response = await fetch(`${simulatorApi}/api/benchmark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ controller, scenario, episodes: episodeCount }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `Benchmark failed (${response.status}).`);
      setBenchmark(payload.report as BenchmarkReport);
    } catch (error) {
      setBenchmarkError(error instanceof Error ? error.message : "Could not connect to the Python simulator.");
    } finally {
      setBenchmarkLoading(false);
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">A<span>V</span></div><div><strong>Autonomy Lab</strong><small>RESEARCH PLATFORM</small></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>
          <a className="nav-item active"><span>◫</span> Overview</a>
          <a className="nav-item"><span>⌁</span> Simulation</a>
          <a className="nav-item"><span>▥</span> Benchmarks</a>
          <a className="nav-item"><span>◉</span> Sensor data</a>
          <a className="nav-item"><span>⌘</span> Experiments</a>
        </nav>
        <div className="sidebar-bottom"><div className="project-chip"><span className="pulse-dot" /> PROJECT STATUS <b>IN DEVELOPMENT</b></div><div className="profile"><div className="avatar">DO</div><div><strong>Dalton Opudo</strong><small>Researcher · UTSA</small></div><span className="more">···</span></div></div>
      </aside>

      <section className="main">
        <header className="topbar"><div className="crumb">Projects <span>/</span> <b>Autonomous Driving Simulation</b></div><div className="top-actions"><span className="env-pill">● SIMULATION ENVIRONMENT</span><div className="top-avatar">DO</div></div></header>
        <div className="content">
          <div className="page-heading"><div><div className="eyebrow">RESEARCH OVERVIEW <span>•</span> EXPERIMENT 001</div><h1>Autonomous Driving <em>Research</em></h1><p>Team research project · Dalton Opudo, Dexter & William. Evaluate controllers with reproducible Python experiments.</p></div><button className="export-btn" onClick={() => window.print()}>↥ <span>Export view</span></button></div>

          <div className="stats-grid">
            <Stat label="SIMULATION STATUS" value={running ? "Running" : progress >= 94 ? "Complete" : "Standby"} detail={running ? "Live episode in progress" : "Awaiting execution"} icon="◉" accent={running ? "green" : "blue"} />
            <Stat label="PREVIEW SPEED" value={speed.toFixed(1)} unit="m/s" detail="Illustrative browser animation" icon="↗" accent="blue" />
            <Stat label="PREVIEW PROGRESS" value={completion.toString()} unit="%" detail="Animation only · not benchmark output" icon="⌁" accent="orange" />
            <Stat label="OBSTACLES DETECTED" value={String(obstacleCount)} detail="Static scenario objects" icon="◎" accent="purple" />
          </div>

          <div className="section-row"><div><h2>Browser preview</h2><p>Illustrative animation · separate from Python benchmark execution</p></div><div className="live-status"><span className={running ? "pulse-dot" : "muted-dot"} />{status}</div></div>
          <div className="simulation-grid">
            <div className="panel sim-panel">
              <div className="panel-head"><div><strong>Road environment</strong><small>TOP-DOWN VIEW · NOT TO SCALE</small></div><div className="view-tag">2D VIEW</div></div>
              <div className="road-stage">
                <div className="road">
                  <div className="road-edge left" /><div className="road-edge right" />
                  <div className="lane-line" />
                  {scenarios[scenario].obstacles.map((o, i) => <div key={i} className="obstacle" style={{ left: o.x + "%", top: o.y + "%" }}><span /></div>)}
                  <div className="car" style={{ left: (50 + laneOffset) + "%", bottom: (100 - progress) + "%" }}><div className="car-glass" /><div className="car-light front" /><div className="car-light rear" /></div>
                  <div className="road-label start">START</div><div className="road-label finish">FINISH</div>
                </div>
                <div className="road-overlay"><span>● EGO VEHICLE</span><span>○ STATIC OBSTACLE</span></div>
              </div>
              <div className="sim-controls"><button className="primary-btn" disabled={benchmarkLoading} onClick={() => void runBenchmark()}>{benchmarkLoading ? "Running Python benchmark…" : "▶  Run Python benchmark"}</button><button className="secondary-btn" onClick={() => running ? setRunning(false) : run()}>{running ? "Ⅱ  Pause preview" : "▷  Play preview"}</button><button className="secondary-btn" onClick={reset}>↺ Reset</button><div className="control-divider" /><label>CONTROLLER<select value={controller} onChange={(e) => {setController(e.target.value as Controller); setBenchmark(null); reset();}}><option value="baseline">Baseline · lane following</option><option value="safety">Safety · emergency brake</option><option value="steering">Steering · obstacle avoidance</option></select></label><label>EPISODES<select value={episodeCount} onChange={(e) => {setEpisodeCount(Number(e.target.value)); setBenchmark(null);}}><option value={1}>1 · Quick check</option><option value={10}>10 · Standard</option><option value={25}>25 · Extended</option><option value={50}>50 · Deep run</option></select></label><label>SCENARIO<select value={scenario} onChange={(e) => {setScenario(e.target.value as Scenario); setBenchmark(null); reset();}}><option value="clear">Clear road</option><option value="center">Center obstacle</option><option value="edge">Lane-edge obstacle</option><option value="outside">Outside-lane obstacle</option><option value="multiple">Multiple obstacles</option></select></label></div>
            </div>
            <div className="right-stack">
              <div className="panel telemetry-panel"><div className="panel-head"><div><strong>Preview readout</strong><small>ANIMATION VALUES · NOT PYTHON TELEMETRY</small></div><span className="telemetry-icon">⌁</span></div><Telemetry label="Longitudinal speed" value={speed.toFixed(1)} unit="m/s" pct={speed / 70 * 100}/><Telemetry label="Lateral offset" value={(laneOffset * 0.1).toFixed(2)} unit="m" pct={laneOffset * 1.2}/><Telemetry label="Route progress" value={completion.toString()} unit="%" pct={completion}/><div className="telemetry-foot"><span>SIM TIME</span><b>{elapsed}s</b><span>FIXED STEP</span><b>0.10s</b></div></div>
              <div className="panel controller-panel"><div className="panel-head"><div><strong>Active controller</strong><small>CONTROL STRATEGY</small></div><span className="controller-badge">● ACTIVE</span></div><div className="controller-name">{controller === "baseline" ? "Pure pursuit" : controller === "safety" ? "Emergency braking" : "Steering avoidance"}</div><p>{controller === "baseline" ? "Tracks the lane center using a pure-pursuit steering baseline." : controller === "safety" ? "Uses range-sensor proximity to brake when an obstacle is too close." : "Selects a clear lateral path around an obstacle, then returns toward lane center."}</p><div className="controller-meta"><span>MODE</span><b>RULE-BASED</b><span>LEARNING</span><b>NOT TRAINED</b></div></div>
            </div>
          </div>

          <div className="section-row benchmark-heading"><div><h2>Experiment insights</h2><p>Metrics returned by the Python benchmark</p></div><span className="dataset-label">{benchmark ? "PYTHON BENCHMARK · REAL RESULT" : "WAITING FOR PYTHON RUN"}</span></div>
          <div className="bottom-grid">
            <div className="panel insight-panel"><div className="panel-head"><div><strong>Scenario configuration</strong><small>DETERMINISTIC TEST SETUP</small></div></div><div className="scenario-row"><div className="scenario-icon">⌖</div><div><b>{scenarios[scenario].label}</b><small>{obstacleCount} obstacle{obstacleCount === 1 ? "" : "s"} · Single-lane road</small></div><span className="scenario-state">SELECTED</span></div><div className="scenario-details"><span>ROAD WIDTH <b>4.8 m</b></span><span>ROUTE LENGTH <b>1,200 m</b></span><span>TIME STEP <b>0.10 s</b></span></div></div>
            <div className="panel insight-panel"><div className="panel-head"><div><strong>Research metrics</strong><small>{benchmark ? `PYTHON · ${benchmark.episode_count} EPISODE` : "REAL RESULTS APPEAR AFTER A PYTHON RUN"}</small></div></div>{benchmarkError && <p role="alert" className="api-error">{benchmarkError}</p>}<div className="metric-list"><div><span>Mean lane deviation</span><b>{benchmark?.aggregate.mean_lane_deviation_m == null ? "—" : benchmark.aggregate.mean_lane_deviation_m.toFixed(3)}<small> m</small></b></div><div><span>Mean collision events</span><b>{benchmark ? benchmark.aggregate.mean_collision_events.toFixed(2) : "—"}</b></div><div><span>Route completion</span><b>{benchmark ? benchmark.aggregate.mean_route_completion_pct.toFixed(1) : "—"}<small>%</small></b></div><div><span>Safe-stop rate</span><b>{benchmark ? (benchmark.aggregate.safe_stop_rate * 100).toFixed(0) : "—"}<small>%</small></b></div><div><span>Steering MAE</span><b>Not measured</b></div></div>{benchmark && <p className="benchmark-note">Completed {benchmark.episodes.filter((episode) => episode.completed).length} of {benchmark.episode_count} episodes. Simulator: lightweight 2D.</p>}</div>
          </div>

          <div className="section-row benchmark-heading"><div><h2>Controller comparison</h2><p>Matched scenario · Python benchmark output</p></div><button className="secondary-btn" disabled={comparisonLoading} onClick={() => void runComparison()}>{comparisonLoading ? "Comparing…" : "Compare all 3 controllers"}</button></div>
          {comparison && <div className="panel comparison-panel"><div className="panel-head"><div><strong>Matched controller benchmark</strong><small>{comparison.scenario.toUpperCase()} · {comparison.episode_count_per_controller} EPISODES EACH</small></div><span className="dataset-label">PYTHON OUTPUT</span></div><div className="comparison-table"><div className="comparison-header"><span>CONTROLLER</span><span>COLLISIONS ↓</span><span>COMPLETION ↑</span><span>LANE ERROR ↓</span></div>{comparison.reports.map((item) => <div className="comparison-row" key={item.controller}><b>{item.controller === "baseline" ? "Pure pursuit" : item.controller === "safety" ? "Emergency brake" : "Steering avoidance"}</b><span>{item.aggregate.mean_collision_events.toFixed(2)}</span><span className="completion-cell"><div className="comparison-meter"><i style={{width: `${Math.max(0,Math.min(100,item.aggregate.mean_route_completion_pct))}%`}} /></div><strong>{item.aggregate.mean_route_completion_pct.toFixed(1)}%</strong></span><span>{item.aggregate.mean_lane_deviation_m == null ? "N/A" : `${item.aggregate.mean_lane_deviation_m.toFixed(3)} m`}</span></div>)}</div><p className="comparison-note">{comparison.interpretation} Deterministic repeats are consistency checks, not independent randomized trials.</p></div>}
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
