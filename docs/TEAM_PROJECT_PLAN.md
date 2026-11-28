# Three-Person Project Plan

## Project

**Autonomous Driving Simulation: Controller Evaluation and Research Dashboard**

Team: **Dalton Opudo · Dexter · William**

This is a collaborative computer-science simulation project. The team will develop, test, evaluate, and present a reproducible autonomous-driving prototype. The current implementation is a deterministic lightweight 2D simulator; CARLA and machine-learning integration are future milestones, not completed features.

## Shared objective

Build a clear demonstration of the engineering trade-off between:
- A lane-following baseline that prioritizes route progress.
- A range-sensor safety controller that can stop before an obstacle.
- A steering-based controller that attempts a lateral bypass and lane return.

Evaluate all controllers using the same scenario settings and report collision events, route completion, and lane deviation. The team will keep claims limited to what the simulator and experiments actually measure.

## Proposed workstream ownership

These are planned responsibilities for coordination. Each member should record the work they personally complete; this document does not claim that every item has already been done.

### Dalton — Simulation and system integration
- Own the vehicle/road simulation architecture and controller integration.
- Review API-to-simulator behavior and keep the system runnable from the documented setup.
- Coordinate branch integration, release readiness, and the final technical walkthrough.
- Deliverable: architecture diagram, runnable integrated build, and explanation of controller behavior.

### Dexter — Experiments, scenarios, and validation
- Own benchmark scenario design and the fair comparison protocol.
- Review collision, completion, and lane-deviation metric definitions.
- Add or maintain experiment tests, inspect edge cases, and document limitations.
- Deliverable: experiment matrix, repeatable commands, test evidence, and results interpretation.

### William — Dashboard, visualization, and presentation assets
- Own the research dashboard experience and data presentation.
- Connect dashboard controls to the Python API and make comparison results readable.
- Prepare figures, workflow visuals, and clear demo/presentation materials.
- Deliverable: responsive dashboard, comparison visualization, and presentation-ready graphics.

## Team-wide responsibilities

Every member should:
1. Review the pull request for their workstream.
2. Run the documented tests or verify the relevant CI result.
3. Explain their own implementation during the presentation.
4. Add a short contribution note with files/features and evidence.
5. Flag bugs or unsupported claims rather than hiding them.

## Milestones and acceptance checks

| Milestone | Acceptance check |
| --- | --- |
| Stable simulator | Deterministic episode, documented controller choices, automated tests |
| Scenario suite | Clear, center, edge, outside-path, and multiple-obstacle cases |
| Matched comparison | All three controllers run on the same scenario and episode count |
| Research dashboard | Shows actual Python benchmark output and clearly labels illustrative preview |
| Presentation package | Architecture, experiment method, measured results, limitations, and future work |
| Final review | Clean setup instructions, tests passing, no unresolved critical defects |

## Results and research integrity

- Record the scenario, controller, episode count, and simulator version with results.
- Repeated deterministic episodes are reproducibility checks, not independent randomized samples.
- Do not invent or backfill individual contributions, measurements, or citations.
- Do not call this CARLA, a trained neural network, or a real-vehicle system until those stages are actually implemented and validated.
- Do not interpret simulation metrics as proof of real-world driving safety.

## Contribution log template

Each team member should complete their own entry before submission:

- **Member:**
- **Implemented / analyzed:**
- **Files or features:**
- **Tests or evidence:**
- **What I learned / remaining limitation:**
