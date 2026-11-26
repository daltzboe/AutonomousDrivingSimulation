# Autonomous Driving Research Dashboard

A browser-based companion interface for the Python autonomous-driving simulator.

## Run locally

From the repository root:

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:3000.

## Current scope

- Responsive research dashboard layout.
- Interactive front-end road preview with selectable obstacle scenarios and controller descriptions.
- Run, pause, and reset controls for a demonstration animation.
- Telemetry-style readouts and experiment configuration panels.

## Integration status

The current road animation and telemetry values are front-end demonstration behavior. They are not yet streamed from the Python simulator, and the displayed values must not be treated as benchmark results. The next integration stage will expose reproducible Python benchmark outputs to the dashboard.

The Python simulator remains the source of truth for vehicle dynamics, sensor behavior, collision checks, and evaluation metrics. This web app does not control a real vehicle.
