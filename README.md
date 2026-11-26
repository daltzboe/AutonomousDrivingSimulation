# Autonomous Driving Simulation

UTSA computer science project based on the **Autonomous Driving Simulation** research proposal.

## Research question

Can we effectively train and evaluate autonomous driving AI in a simulated environment without exposing real vehicles or people to safety risks?

## Project scope

The project will implement and compare two driving approaches in the CARLA simulator:

1. **CARLA BasicAgent** — a rule-based baseline using route navigation, PID vehicle control, and obstacle-response behavior.
2. **Imitation-learning CNN** — a model trained to predict steering commands from simulated camera images, following the approach described by Bojarski et al. (2016).

The experiment will evaluate both approaches using the metrics in the proposal:

- Steering error (MAE)
- Collision rate
- Lane deviation
- Route completion

## Planned workflow

1. Set up and verify the CARLA simulator and Python client.
2. Run BasicAgent as the baseline and collect expert camera/control samples.
3. Prepare a reproducible training and validation dataset.
4. Train the camera-to-steering CNN.
5. Evaluate both controllers on comparable routes and scenarios.
6. Record results and limitations without inventing performance claims.

## Data

Camera images will provide visual input (road, lane markings, vehicles, and obstacles). Vehicle telemetry and control labels will include steering, throttle, brake, speed, position, and yaw. Data will come from public CARLA datasets and/or newly generated simulation runs, as described in the proposal.

## Safety and boundaries

All driving experiments are performed in simulation. Advanced ideas such as generative world models, reasoning-based trajectory planning, and sensor fusion are future-work directions—not part of the initial implementation.

## Environment

The development environment is Windows with IntelliJ IDEA and a dedicated Python virtual environment. The exact CARLA release and compatible Python version will be documented after environment verification.

## Current status

This repository is at its initial setup stage. No training or evaluation results are claimed yet.
