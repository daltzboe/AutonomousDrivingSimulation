# Controller Comparison — Experiment Report Template

> Fill this in from an actual dashboard JSON export or CLI output. Do not invent results. This template is a report structure, not measured data.

## Experiment metadata

- Team: Dalton Opudo, Dexter, William
- Date:
- Git commit / branch:
- Simulator: lightweight deterministic 2D
- Scenario:
- Episodes per controller:
- Route / lane configuration:
- Fixed time step:
- Benchmark JSON file:

## Research question

Under the same simulated obstacle scenario, how do pure-pursuit lane following, emergency braking, and steering-based obstacle avoidance differ in collision events and route completion?

## Method

1. Select one scenario and use identical simulator settings for all three controllers.
2. Run the same episode count for baseline, safety, and steering.
3. Save the machine-readable comparison report.
4. Record means and sample standard deviations where at least two runs exist.
5. Inspect incomplete routes and safe stops rather than counting them as successful completion.
6. Explain that deterministic repeats check reproducibility; they are not independent randomized trials.

## Results

| Controller | Mean collision events | Collision SD | Mean route completion (%) | Completion SD (percentage points) | Mean lane deviation (m) | Lane deviation SD (m) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pure pursuit / baseline | — | — | — | — | — | — |
| Emergency braking / safety | — | — | — | — | — | — |
| Steering avoidance | — | — | — | — | — | — |

Use **N/A** when a standard deviation is unavailable because fewer than two episodes were run. Keep the units and number of episodes visible.

## Interpretation

- Which controller avoided modeled contacts?
- Which controller completed the route?
- Did a safe stop prevent collision but reduce route completion?
- Did steering avoid the obstacle and return to the lane?
- What unexpected behavior or failure occurred?
- What does this scenario not prove?

## Limitations

- The environment is a lightweight 2D simulator, not CARLA.
- Obstacles are stationary and the range sensor is a geometric approximation.
- Controller rules are simplified and are not a production autonomous-driving stack.
- No camera-based CNN has been trained.
- Results do not establish real-world vehicle safety.
- Repeated deterministic runs do not provide statistical independence.

## Team review

- **Dalton — simulation / integration notes:**
- **Dexter — experiment / validation notes:**
- **William — dashboard / visualization notes:**
- **All members reviewed the interpretation and limitations:** Yes / No

## Evidence checklist

- [ ] Exported JSON comparison report attached to project materials
- [ ] Screenshot of the comparison dashboard
- [ ] Test suite and production build status recorded
- [ ] Controller and scenario settings visible in presentation
- [ ] No unsupported claims or fabricated results
