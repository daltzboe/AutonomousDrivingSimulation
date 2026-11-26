# Class Presentation Guide

## Suggested project title

**Autonomous Driving Simulation: Comparing Lane Following and Sensor-Based Emergency Braking**

## One-sentence project summary

This project builds a repeatable 2D autonomous-driving simulator and compares a pure-pursuit baseline controller with a range-sensor safety layer under controlled obstacle scenarios.

## Research question

Can a simple range-sensor emergency-braking layer reduce collisions compared with a pure-pursuit lane-following baseline, and what trade-off does it create in route completion?

## System architecture

```mermaid
flowchart TD
    Road[Curved road model] --> Sim[2D vehicle simulator]
    Vehicle[Vehicle state] --> Controller[Controller]
    Sim --> Vehicle
    Vehicle --> Controller
    Obstacles[Static obstacle layout] --> Sensor[Geometric range sensor]
    Controller --> Commands[Throttle / brake / steering]
    Sensor --> Safety[Emergency-braking layer]
    Controller --> Safety
    Safety --> Commands
    Commands --> Sim
    Sim --> Metrics[Metrics and CSV telemetry]
    Metrics --> Report[JSON experiment report]
```

The baseline controller computes lane-following steering and speed commands. The safety controller uses the same baseline command but can override throttle with full braking when a relevant obstacle is within the estimated stopping distance plus a safety margin.

## Suggested 8-slide structure

1. **Motivation:** Why autonomous-driving controllers need consistent testing before more advanced models are introduced.
2. **Research question:** Compare a lane-following baseline with a sensor-based safety layer.
3. **Simulator design:** Curved road, kinematic bicycle vehicle, fixed time step, obstacles, and telemetry.
4. **Controller design:** Explain pure pursuit, range sensing, stopping distance, and emergency braking.
5. **Experiment design:** Show the clear, center, edge, outside, and multiple-obstacle scenarios.
6. **Preliminary result:** Present the one-episode center-obstacle comparison below.
7. **Limitations:** Explain why stopping safely is not the same as completing the route or planning an alternate path.
8. **Next steps:** Local path planning, moving traffic, camera perception, learning, and eventual CARLA evaluation.

## Preliminary center-obstacle result

The following values are from the first one-episode center-obstacle experiment run during development. They are a preliminary demonstration, not a statistical evaluation.

| Metric | Pure-pursuit baseline | Range-sensor safety |
| --- | ---: | ---: |
| Collision events | 1 | 0 |
| Route completion | 100% | 19.35% |
| Distance traveled | 500.16 m | 96.76 m |
| Mean lane deviation | 0.00475 m | 0.00172 m |

### Interpretation

In this run, the baseline vehicle continued through the obstacle and recorded one collision. The safety controller detected the obstacle and stopped before contact, producing zero collisions. However, it stopped at about 19.35% route completion.

The correct conclusion is that emergency braking prevented a collision in this modeled scenario, but it did not solve obstacle navigation. A more capable controller must find a safe path around the obstacle and return to the lane.

Do not describe this single run as proof of general safety or real-world performance. Repeat the experiments and report the scenario, episode count, simulator, and limitations.

## Live demonstration commands

Run these from the repository root with the virtual environment active.

```powershell
# Launch the interactive driving demo
autodrive-demo

# Run the baseline into a center obstacle
python -m autodrive_sim.benchmark --controller baseline --scenario center --episodes 1

# Run the emergency-braking controller against the same obstacle
python -m autodrive_sim.benchmark --controller safety --scenario center --episodes 1

# Show that an obstacle outside the path does not trigger a safety stop
python -m autodrive_sim.benchmark --controller safety --scenario outside --episodes 1

# Run the full automated test suite
python -m pytest -v
```

The current GitHub Actions pipeline validates compilation, the unittest suite, the pytest suite, and a benchmark CLI smoke test. The obstacle-scenario branch currently passes 63 pytest tests.

## Current limitations to state clearly

- This is a lightweight deterministic 2D simulator, not CARLA.
- The range sensor uses geometric ray-circle intersections; it is not a physical LiDAR sensor.
- Obstacles in the current benchmark are stationary.
- The safety controller brakes but does not steer around obstacles.
- No camera-based neural network has been trained yet.
- No real vehicle is controlled or tested by this project.

## Development roadmap

1. Complete deterministic obstacle scenarios and paired controller benchmarks.
2. Implement a local path planner for steering around stationary obstacles.
3. Add moving vehicles and traffic-following scenarios.
4. Add a camera observation pipeline and labeled data collection.
5. Train and evaluate an imitation-learning model.
6. Integrate CARLA on a compatible machine or remote environment.
7. Compare controllers on matched routes and publish reproducible results.

## Presentation tip

Lead with the live center-obstacle experiment. It makes the engineering trade-off easy to understand: the baseline reaches the destination but collides; the safety layer avoids contact but stops early. Then explain how the next milestone is to achieve both collision avoidance and route completion.
