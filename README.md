# Autonomous Driving Simulation

A UTSA computer science research project for developing and evaluating autonomous-driving controllers in a reproducible simulation. The repository includes a lightweight interactive 2D driving environment, deterministic obstacle scenarios, range-sensor emergency braking, automated tests, and experiment telemetry. CARLA integration and camera-based learning remain planned research stages.

## Project team

Three-person team: **Dalton Opudo, Dexter, and William**. See the [team work plan and contribution checklist](docs/TEAM_PROJECT_PLAN.md) for proposed workstreams, milestones, and each member's contribution log.

## Research question

How do different autonomous-driving control approaches compare when evaluated on the same simulated routes and scenarios?

## Current implementation

### Lightweight 2D simulator

- Kinematic bicycle vehicle model with throttle, braking, and steering inputs.
- Deterministic curved single-lane road with configurable width and route length.
- Pure-pursuit lane-following controller with proportional speed control.
- Stationary obstacle contacts and collision-event counting.
- Deterministic planar range sensor with configurable field of view, ray count, and range.
- Obstacle-aware emergency-braking controller that stops when a hazard is too close.
- Steering-based obstacle-avoidance controller that selects a clear lateral bypass, follows a smooth offset path, and returns to lane center; it falls back to braking when the road is too narrow.
- Five deterministic benchmark scenarios: clear road, center-lane obstacle, lane-edge obstacle, outside-path obstacle, and multiple obstacles.
- Fixed simulation time step and repeatable episode reset.
- Interactive Pygame top-down view with live speed, lane deviation, route progress, and collision count.
- Keyboard controls for manual driving and autopilot.
- Reusable evaluation metrics for steering MAE, mean lane deviation, collision events per kilometer, distance, and route completion.

### Planned research comparison

1. **Rule-based baseline:** first validate the local pure-pursuit controller, then integrate CARLA's BasicAgent/PID baseline when CARLA is available.
2. **Imitation-learning CNN:** collect simulated camera frames and expert control labels, train a camera-to-steering model, and evaluate it on matching routes.

The current Pygame controller is an initial baseline for software development and demonstration. It is not CARLA's BasicAgent and does not represent a trained neural network.

## Quick start (Windows / PowerShell)

From the repository root, activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project and demo/test extras:

```powershell
python -m pip install -e ".[dev,demo]"
```

Launch the visual simulation:

```powershell
python -m autodrive_sim.demo
```

You can also use the installed command:

```powershell
autodrive-demo
```

Run repeatable headless baseline episodes and export metrics plus telemetry:

```powershell
python -m autodrive_sim.benchmark --controller baseline --episodes 3 --output results/baseline_summary.json --telemetry-dir results/telemetry
python -m autodrive_sim.benchmark --controller safety --episodes 3 --output results/safety_summary.json

# Compare both controllers against a center-lane obstacle
python -m autodrive_sim.benchmark --controller baseline --scenario center --episodes 3 --output results/center_baseline.json
python -m autodrive_sim.benchmark --controller safety --scenario center --episodes 3 --output results/center_safety.json
python -m autodrive_sim.benchmark --controller steering --scenario center --episodes 3 --output results/center_steering.json

# Compare both obstacle-avoidance strategies on multiple hazards
python -m autodrive_sim.benchmark --controller steering --scenario multiple --episodes 3

# Test an obstacle outside the vehicle's path
python -m autodrive_sim.benchmark --controller safety --scenario outside --episodes 3
```

Choose `--controller baseline` for pure-pursuit lane following, `--controller safety` for emergency braking, or `--controller steering` for lateral obstacle avoidance. The benchmark uses a 4.8 m road lane to provide enough modeled clearance for the configured vehicle to pass the stationary obstacles; the controller still checks road boundaries and falls back to braking when no safe side is available. Choose a scenario with `--scenario clear|center|edge|outside|multiple`. The `center` and `edge` scenarios challenge the safety controller; `outside` checks that an irrelevant obstacle does not trigger braking. A safe stop before the destination is reported as incomplete route completion, not as a completed trip. Use `--output` for a JSON summary and `--telemetry-dir` to save one CSV per episode. The CSV contains timestamp, position, heading, speed, control inputs, and lane deviation. It is useful for inspecting baseline behavior and building later data pipelines; it does not contain camera images and is not yet an imitation-learning dataset.

### Demo controls

| Key | Action |
| --- | --- |
| A | Toggle autopilot / manual driving |
| Up arrow | Accelerate in manual mode |
| Down arrow | Brake in manual mode |
| Left / Right arrows | Steer in manual mode |
| Space | Pause / resume |
| R | Reset the episode |
| Esc | Quit |

The visual demo starts in autopilot mode. Switch to manual mode to demonstrate steering and throttle inputs, then reset to let the controller drive again.

For a short presentation walkthrough and research-status notes, see [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).
For the obstacle scenario definitions, experiment commands, and interpretation guide, see [docs/SCENARIO_BENCHMARKS.md](docs/SCENARIO_BENCHMARKS.md).
For a slide-by-slide class presentation outline and preliminary center-obstacle results, see [docs/CLASS_PRESENTATION.md](docs/CLASS_PRESENTATION.md).
For the vehicle equations, pure-pursuit steering model, and metric definitions, see [docs/MODEL_AND_METRICS.md](docs/MODEL_AND_METRICS.md).
For the planned CARLA/CNN experiment design and fair evaluation protocol, see [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md).

## Tests

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

Or run it with pytest:

```powershell
python -m pytest
```

The suite covers metric calculations, vehicle dynamics, road geometry, controller outputs, episode progression, obstacle contacts, scenario construction, safe-stop and steering-avoidance behavior, benchmark execution, telemetry export, demo rendering, and reset behavior.

## Evaluation metrics

- **Steering MAE:** mean absolute difference between predicted and expert steering commands. It is available when paired steering samples are collected.
- **Lane deviation:** mean absolute distance from the lane center, in meters.
- **Collision events:** modeled contacts between the vehicle and stationary obstacles.
- **Collision rate:** collision events per kilometer traveled.
- **Route completion:** completed forward distance divided by route length.

An empty or unmeasured metric is reported as `null`, not as a fabricated zero. The current Pygame episode does not produce expert steering labels, so steering MAE remains unavailable until a data-collection workflow is added.

## Project structure

```text
src/
  autodrive_sim/
    __init__.py
    config.py
    controllers.py
    benchmark.py
    demo.py
    metrics.py
    telemetry.py
    sensors.py
    simulator/
      __init__.py
      road.py
      simulation.py
      vehicle.py
tests/
  test_metrics.py
  test_benchmark.py
  test_demo.py
  test_controllers.py
  test_telemetry.py
  test_sensors.py
  simulator/
    test_road.py
    test_simulation.py
    test_vehicle.py
pyproject.toml
requirements.txt
```

## Research integrity and limitations

- The lightweight 2D environment is a development and demonstration tool, not a replacement for CARLA.
- Obstacles in the current environment are stationary and simplified.
- The planar range sensor is a deterministic geometric approximation, not a physical LiDAR sensor; it does not model noise, occlusion, or calibration.
- The current lane follower is a transparent pure-pursuit baseline, not a production-grade autonomous-driving stack.
- CARLA has not yet been integrated or run in this repository.
- No imitation-learning model has been trained and no controller-comparison results are claimed.
- All experiments are intended to remain in simulation; this project does not control a real vehicle.

## Planned milestones

1. Validate the lightweight simulator and its automated tests.
2. Add repeatable scenario and telemetry recording.
3. Extend local planning to dense and moving obstacles.
4. Integrate CARLA on a compatible machine or remote environment.
5. Collect expert camera/control samples from the rule-based CARLA baseline.
6. Train and validate the imitation-learning CNN.
7. Compare controllers on matching routes using the documented metrics.
8. Analyze results, limitations, and future work.

## Development environment

The initial development environment is Windows, IntelliJ IDEA, and Python 3.12.10. The lightweight simulator uses Pygame and the existing Python package structure. CARLA setup is intentionally deferred until its version and Python API compatibility can be validated.
