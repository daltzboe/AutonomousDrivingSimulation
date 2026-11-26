# Obstacle Scenario Benchmark Protocol

## Purpose

This benchmark compares two controllers under repeatable conditions in the project's lightweight 2D simulator:

- **Baseline:** pure-pursuit lane following with proportional speed control.
- **Safety:** the same lane follower plus a geometric range sensor and emergency-braking layer.

The experiment asks whether the safety layer reduces modeled obstacle contacts, and whether it avoids unnecessary braking when an obstacle is outside the vehicle's path.

This is a controlled software experiment. It is not a real-vehicle safety validation.

## Scenario definitions

All scenarios use the same deterministic 500 m curved road, vehicle model, time step, and controller settings.

| Scenario | Obstacle layout | Expected question |
| --- | --- | --- |
| `clear` | No obstacles | Do both controllers complete the route normally? |
| `center` | One circular obstacle centered in the lane at 100 m | Does emergency braking prevent a direct collision? |
| `edge` | One obstacle offset 1.0 m from lane center at 100 m | Does the sensor treat a lane-edge hazard as relevant? |
| `outside` | One obstacle offset 4.0 m from lane center at 100 m | Does the controller avoid braking for an irrelevant object? |
| `multiple` | Two center-lane obstacles at 100 m and 220 m | How do the controllers behave when more than one hazard is present? |

Obstacles are stationary circles. Their positions are deterministic and are identical between controller runs.

## Run the experiments

Activate the project's virtual environment and install the development dependencies first. From the repository root:

```powershell
# Baseline against a center-lane obstacle
python -m autodrive_sim.benchmark --controller baseline --scenario center --episodes 3 --output results/center_baseline.json --telemetry-dir results/center_baseline

# Safety controller against the same obstacle
python -m autodrive_sim.benchmark --controller safety --scenario center --episodes 3 --output results/center_safety.json --telemetry-dir results/center_safety

# Check lane-edge behavior
python -m autodrive_sim.benchmark --controller baseline --scenario edge --episodes 3
python -m autodrive_sim.benchmark --controller safety --scenario edge --episodes 3

# Check an obstacle outside the path
python -m autodrive_sim.benchmark --controller baseline --scenario outside --episodes 3
python -m autodrive_sim.benchmark --controller safety --scenario outside --episodes 3

# Compare multiple obstacles
python -m autodrive_sim.benchmark --controller baseline --scenario multiple --episodes 3
python -m autodrive_sim.benchmark --controller safety --scenario multiple --episodes 3
```

Each JSON report contains the selected controller and scenario, aggregate metrics, episode-level metrics, and interpretation notes. CSV telemetry can be written with `--telemetry-dir`.

## Metrics

- **Collision events:** number of modeled contacts between the vehicle and obstacles.
- **Collision rate per kilometer:** collision events divided by distance traveled, scaled to one kilometer.
- **Route completion:** forward progress divided by the route length.
- **Mean lane deviation:** mean absolute lateral distance from the road centerline.
- **Safe-stop rate:** fraction of episodes in which the vehicle came to rest before the route ended without a recorded collision.
- **Final speed:** vehicle speed at the end of the episode.

A safety-controller episode that stops before an obstacle is intentionally recorded as **not route-complete**. A zero-collision result alone is not sufficient to claim successful autonomous navigation; route completion and safe-stop rate must be considered alongside collisions.

## Current controller limitations

The safety controller does not plan a path around obstacles. It preserves pure-pursuit steering and applies full braking when the nearest relevant range measurement is within the estimated stopping distance plus a margin. Consequently, a safe stop can prevent a collision but cannot finish a route blocked by an obstacle.

The range sensor is a deterministic geometric ray model. It does not simulate sensor noise, occlusion, reflections, object classification, or physical LiDAR hardware. Obstacles are stationary; moving traffic is not included in this benchmark.

## Fair-comparison procedure

1. Use the same scenario, road, vehicle parameters, and number of episodes for both controllers.
2. Do not change controller parameters between the paired runs unless the experiment explicitly studies parameter sensitivity.
3. Save the JSON report and CSV telemetry for each run.
4. Report collision events and route completion together. Do not describe a stopped vehicle as having completed the route.
5. Include the simulator type and its limitations in any class presentation.
6. Repeat experiments after any code or parameter change.

## Suggested presentation conclusion

The current experiment demonstrates a measurable trade-off: a range-sensor emergency-braking layer can prevent a modeled collision by stopping before a stationary obstacle, but stopping alone does not solve the route-planning problem. The next research milestone is a local obstacle-avoidance planner that can choose a safe lateral path and rejoin the lane, followed by evaluation across varied and moving traffic scenarios.

These findings apply only to the lightweight 2D simulation. They are not CARLA results, real-world driving evidence, or evidence from a trained neural network.
