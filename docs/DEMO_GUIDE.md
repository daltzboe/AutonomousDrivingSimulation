# Demo Guide

## Before presenting

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,demo]"
python -m autodrive_sim.demo
```

The visual simulator opens in autopilot mode. It is designed as a lightweight 2D demonstration and does not require CARLA.

## Suggested 2-3 minute walkthrough

1. **Show the autonomous baseline.** Start with autopilot enabled. Point out the moving road, lane markings, vehicle, and live speed / lane-error / route-progress / collision readouts.
2. **Explain the controller.** The baseline uses pure-pursuit geometry to steer toward a look-ahead point on the lane centerline. A proportional controller manages target speed.
3. **Demonstrate manual control.** Press `A` to switch to manual mode. Use the arrow keys to accelerate, brake, and steer. Show how lane deviation responds to steering.
4. **Return to autopilot.** Press `R` to reset the episode, then make sure autopilot is enabled with `A` if needed.
5. **Show measurable output.** Close the visual window and run:

   ```powershell
   python -m autodrive_sim.benchmark --episodes 3 --output results/baseline_summary.json --telemetry-dir results/telemetry
   ```

   Explain that the JSON contains episode metrics and each CSV contains timestamped vehicle state and control telemetry.

## What the current demo demonstrates

- A vehicle model with throttle, braking, and steering.
- A deterministic curved lane and a pure-pursuit lane-following baseline.
- Live state visualization and manual/autonomous mode switching.
- Repeatable simulation episodes, modeled obstacle-contact events, and evaluation metrics.
- Structured CSV telemetry and JSON benchmark summaries.

## Be precise about the research status

The current visual simulator is a local 2D prototype. It is not CARLA, CARLA BasicAgent, or a trained neural network. The obstacle model uses stationary circular objects and does not implement a complete obstacle-avoidance planner. The current benchmark provides a baseline software test and telemetry export; it is not yet a scientific comparison between two controllers.

The next research stages are CARLA integration, camera and expert-control data collection, imitation-learning model training, and matched-route evaluation. Do not present unrun CARLA experiments or untrained-model results as completed work.
