# Research Experiment Plan

This document defines a reproducible path from the current 2D prototype to the planned CARLA controller comparison. It is a plan, not a report of completed CARLA experiments.

## Research question

How does a camera-based imitation-learning controller compare with a rule-based autonomous-driving baseline on the same simulated routes and scenarios?

## Controller stages

1. **Current development baselines:** pure-pursuit lane following and an optional range-sensor emergency-braking layer in the lightweight 2D simulator. These validate vehicle control, geometric sensing, basic safety intervention, episode orchestration, telemetry, and metric code.
2. **Planned CARLA baseline:** CARLA BasicAgent/PID controller with documented route and scenario settings.
3. **Planned learned controller:** CNN trained to predict steering from front-camera observations and expert control labels.

The lightweight pure-pursuit controller and CARLA BasicAgent are different systems. Do not treat their results as interchangeable.

## Data collection schema

For each simulation time step, preserve at least:

- Episode ID, route ID, scenario ID, and simulation timestamp.
- Camera frame identifier and image dimensions.
- Vehicle position, heading, and speed.
- Expert steering, throttle, and brake labels.
- Weather, map/town, traffic configuration, and simulation time step.

The current CSV recorder stores vehicle telemetry and controls only. The planar range sensor is a deterministic geometric approximation; it is not physical LiDAR and does not model noise or occlusion. Camera-frame capture and metadata fields must be added during the CARLA integration stage.

## Train / validation / test split

- Split by complete route or episode, not by randomly shuffling adjacent camera frames.
- Keep held-out routes and scenarios out of training and hyperparameter selection.
- Fit image normalization and other learned preprocessing only on the training split.
- Use the validation split for model selection and early stopping.
- Evaluate the final model once on the held-out test scenarios.

This avoids placing near-identical consecutive frames from one drive in both training and test sets.

## Fair controller comparison

For the planned CARLA comparison:

1. Use the same map, route definitions, weather, traffic density, spawn conditions, and simulation time step for both controllers.
2. Keep evaluation routes separate from imitation-learning training routes.
3. Use repeatable scenario seeds and report how many runs were completed.
4. Apply the same termination rules and collision definitions to both controllers.
5. Record configuration and software versions alongside each result.
6. Do not tune one controller using the held-out test results.

## Metrics and reporting

Report, at minimum:

| Metric | Definition | Unit |
| --- | --- | --- |
| Steering MAE | Mean absolute difference between predicted and expert steering | normalized steering units |
| Mean lane deviation | Mean absolute distance from lane center | meters |
| Collision rate | Collision events divided by distance traveled | events/km |
| Route completion | Completed route distance divided by total route distance | percent |

For each controller and scenario, report the number of episodes, mean, and standard deviation. Include failed or incomplete runs rather than silently dropping them. Explain any unavailable metric and the reason it could not be calculated.

## Reproducibility checklist

- [ ] Version-control route and scenario definitions.
- [ ] Record random seeds and simulator settings.
- [ ] Preserve raw telemetry and camera data separately from processed datasets.
- [ ] Store train/validation/test episode IDs.
- [ ] Record model architecture, training configuration, and checkpoint identifier.
- [ ] Evaluate both controllers on the same held-out scenarios.
- [ ] Export machine-readable metrics and document any exclusions.

## Current limitations and next steps

The present prototype is a 2D development environment. It has no camera sensor, dynamic traffic, CARLA map, trained CNN, or real-world driving interface. Its range sensor and emergency-braking controller are simplified development baselines, not production perception or planning. The next research milestone is a CARLA integration on a compatible computer or remote machine, followed by synchronized camera/control data collection. All driving experiments remain simulation-only.
