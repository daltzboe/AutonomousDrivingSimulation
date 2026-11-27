# Autonomous Driving Research Dashboard

A browser-based research interface for the Python autonomous-driving simulator.

## Run locally

Use two terminals from the repository root.

**Terminal 1 — Python benchmark API**

Activate the project's virtual environment if needed, then run:

```powershell
$env:PYTHONPATH = "src"
python -m autodrive_sim.api
```

The API listens on `http://127.0.0.1:8000`. Check it at
`http://127.0.0.1:8000/api/health`.

**Terminal 2 — Web dashboard**

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:3000.

## Matched controller comparison\n\nChoose a scenario and use **Compare all 3 controllers** to run baseline, safety, and steering against the same deterministic setup. The comparison endpoint accepts 1–25 episodes per controller and returns each controller's aggregate metrics. Because the current simulator is deterministic, repeated episodes are consistency checks rather than independent randomized samples.\n\n## Running a benchmark

Select a controller and scenario in the dashboard, then choose **Run Python benchmark**.
The dashboard sends a request to the local Python API and displays the returned
aggregate lane-deviation, collision, route-completion, and safe-stop metrics.

The API accepts `baseline`, `safety`, and `steering` controllers; scenarios
`clear`, `center`, `edge`, `outside`, and `multiple`; and 1–100 episodes.

## Current scope and limitations

- Python benchmark results are actual outputs from the deterministic lightweight 2D simulator.
- The animated road and preview telemetry remain front-end illustration only; they are not streamed from the Python vehicle state.
- The API is local-development only and binds to loopback. A deployed Vercel frontend cannot access a visitor's local Python service. A remotely hosted backend and deployment configuration are a separate step.
- This project is not CARLA, a trained neural network, or real-world vehicle control. Steering MAE requires expert steering labels.
