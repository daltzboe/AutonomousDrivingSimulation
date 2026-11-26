# Autonomous Driving Simulation

A UTSA computer science research project for developing and comparing autonomous-driving controllers in simulation. The repository now includes a lightweight, interactive 2D driving environment that can be demonstrated on a standard Windows laptop. A CARLA integration and camera-based learning pipeline remain planned research stages.

## Research question

How do different autonomous-driving control approaches compare when evaluated on the same simulated routes and scenarios?

## Current implementation

### Lightweight 2D simulator

- Kinematic bicycle vehicle model with throttle, braking, and steering inputs.
- Deterministic curved single-lane road with configurable width and route length.
- Pure-pursuit lane-following controller with proportional speed control.
- Stationary obstacle contacts and collision-event counting.
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
python -m autodrive_sim.benchmark --episodes 3 --output results/baseline_summary.json --telemetry-dir results/telemetry
```

This creates one CSV telemetry file per episode and a JSON summary. The CSV contains timestamp, position, heading, speed, control inputs, and lane deviation. It is useful for inspecting baseline behavior and building later data pipelines; it does not contain camera images and is not yet an imitation-learning dataset.

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

## Tests

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

Or run it with pytest:

```powershell
python -m pytest
```

The suite contains 37 automated tests covering metric calculations, vehicle dynamics, road geometry, controller outputs, episode progression, obstacle contacts, benchmark execution, telemetry export, and reset behavior.

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
    simulator/
      __init__.py
      road.py
      simulation.py
      vehicle.py
tests/
  test_metrics.py
  test_benchmark.py
  test_controllers.py
  test_telemetry.py
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
- The current lane follower is a transparent pure-pursuit baseline, not a production-grade autonomous-driving stack.
- CARLA has not yet been integrated or run in this repository.
- No imitation-learning model has been trained and no controller-comparison results are claimed.
- All experiments are intended to remain in simulation; this project does not control a real vehicle.

## Planned milestones

1. Validate the lightweight simulator and its automated tests.
2. Add repeatable scenario and telemetry recording.
3. Integrate CARLA on a compatible machine or remote environment.
4. Collect expert camera/control samples from the rule-based CARLA baseline.
5. Train and validate the imitation-learning CNN.
6. Compare controllers on matching routes using the documented metrics.
7. Analyze results, limitations, and future work.

## Development environment

The initial development environment is Windows, IntelliJ IDEA, and Python 3.12.10. The lightweight simulator uses Pygame and the existing Python package structure. CARLA setup is intentionally deferred until its version and Python API compatibility can be validated.
