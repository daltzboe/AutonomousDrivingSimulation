# Autonomous Driving Simulation

UTSA computer science research project comparing a rule-based autonomous driving baseline with a camera-based imitation-learning model in the CARLA simulator.

## Research question

Can we effectively train and evaluate autonomous driving AI in a simulated environment without exposing real vehicles or people to safety risks?

## Research scope

We will implement and compare two approaches:

1. **CARLA BasicAgent** — a rule-based baseline using route navigation, vehicle control, and obstacle-response behavior.
2. **Imitation-learning CNN** — a neural network trained to predict steering commands from simulated camera images, following the end-to-end learning approach described by Bojarski et al. (2016).

Both controllers will be evaluated on comparable routes and scenarios using:

- Steering mean absolute error (MAE)
- Collision events per kilometer
- Mean absolute lane-center deviation (meters)
- Route completion (percentage)

All driving experiments are performed in simulation. Results will be measured and reported; no performance claims will be made before experiments are run.

## Repository structure

```text
src/
  autodrive_sim/
    __init__.py
    config.py       # Shared, validated simulation/experiment settings
    metrics.py      # Controller evaluation metrics
tests/
  test_metrics.py   # Unit tests for metric calculations
pyproject.toml      # Package metadata and test configuration
requirements.txt    # Python dependencies
```

## Development environment

Current development setup:

- Windows + IntelliJ IDEA
- Python 3.12.10
- Project virtual environment: `.venv`
- pip 26.3
- NumPy, Pandas, Matplotlib, Pygame, OpenCV, scikit-learn, and SciPy installed locally

The CARLA simulator and its Python API have **not** been integrated yet. We will select and document a CARLA release only after checking compatibility with the development environment.

## Setup

Activate the project's virtual environment, then run:

```powershell
python -m pip install -e ".[dev]"
```

Run the unit tests:

```powershell
python -m unittest discover -s tests -v
```

## Current progress

### Completed

- [x] Created the Python virtual environment and verified Python 3.12.10.
- [x] Upgraded pip to 26.3.
- [x] Installed the initial scientific-computing, visualization, and computer-vision libraries.
- [x] Created the `autodrive_sim` Python package.
- [x] Added validated simulation and experiment configuration dataclasses.
- [x] Implemented reusable evaluation metrics for steering MAE, lane deviation, collision rate, distance, and route completion.
- [x] Added unit tests for metric calculations and invalid inputs.

### In progress

- [ ] Run the new unit tests in the local IntelliJ environment.
- [ ] Select and install a CARLA release compatible with the chosen Python environment.
- [ ] Connect to CARLA and verify a basic simulation session.

### Not yet claimed

No CARLA runs, trained models, or controller-comparison results have been produced yet.

## Planned workflow

1. Verify the project package and metric tests locally.
2. Install and connect the CARLA simulator.
3. Run BasicAgent and collect expert camera/control samples.
4. Build a reproducible training and validation dataset.
5. Train the camera-to-steering CNN.
6. Evaluate both approaches on matching routes and scenarios.
7. Analyze results, limitations, and future work.

## Safety and boundaries

The project is a research simulation. It does not control a real vehicle. Advanced ideas such as generative world models, reasoning-based trajectory planning, and sensor fusion are future-work directions, not part of the initial implementation.
