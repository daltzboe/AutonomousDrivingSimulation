"""Run reproducible rule-based episodes and export metrics/telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

from autodrive_sim.controllers import ObstacleAvoidanceController
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.simulation import Obstacle, Simulation


def run_episode(
    telemetry_path: Path | None = None,
    controller_name: str = "baseline",
) -> dict[str, float | int | None]:
    """Run one complete default route and optionally save its telemetry."""
    road = Road()
    obstacles = (
        Obstacle(130.0, road.center_y(130.0) + 1.4, 0.28),
        Obstacle(290.0, road.center_y(290.0) - 1.4, 0.28),
    )
    if controller_name not in {"baseline", "safety"}:
        raise ValueError("controller_name must be 'baseline' or 'safety'")
    controller = ObstacleAvoidanceController() if controller_name == "safety" else None
    simulation = Simulation(
        road=road,
        obstacles=obstacles,
        **({"controller": controller} if controller is not None else {}),
    )
    maximum_steps = int(road.route_length_m / 2.0 / simulation.dt)
    for _ in range(maximum_steps):
        simulation.step()
        if simulation.completed:
            break
    if not simulation.completed:
        raise RuntimeError("Episode did not complete within the step limit.")
    if telemetry_path is not None:
        simulation.recorder.write_csv(telemetry_path)
    return simulation.summary()


def main() -> None:
    """Command-line entry point for repeatable baseline evaluation."""
    parser = argparse.ArgumentParser(
        description="Run repeatable pure-pursuit autonomous-driving episodes."
    )
    parser.add_argument(
        "--episodes", type=int, default=1,
        help="number of identical baseline episodes to run (1-100)",
    )
    parser.add_argument(
        "--controller", choices=("baseline", "safety"), default="baseline",
        help="pure-pursuit baseline or range-sensor emergency-braking controller",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="optional JSON file for the episode metrics summary",
    )
    parser.add_argument(
        "--telemetry-dir", type=Path, default=None,
        help="optional directory in which to save one CSV per episode",
    )
    args = parser.parse_args()
    if not 1 <= args.episodes <= 100:
        parser.error("--episodes must be between 1 and 100")

    episode_results = []
    for episode_number in range(1, args.episodes + 1):
        telemetry_path = (
            args.telemetry_dir / f"episode_{episode_number:03d}.csv"
            if args.telemetry_dir is not None else None
        )
        episode_results.append(run_episode(telemetry_path, args.controller))

    lane_values = [
        result["lane_deviation_mean_m"]
        for result in episode_results
        if result["lane_deviation_mean_m"] is not None
    ]
    collision_values = [int(result["collision_events"]) for result in episode_results]
    completion_values = [
        float(result["route_completion_pct"])
        for result in episode_results
        if result["route_completion_pct"] is not None
    ]
    report = {
        "controller": (
            "pure_pursuit_baseline" if args.controller == "baseline"
            else "pure_pursuit_with_range_sensor_safety"
        ),
        "simulator": "lightweight_2d",
        "episode_count": len(episode_results),
        "aggregate": {
            "mean_lane_deviation_m": (
                statistics.mean(lane_values) if lane_values else None
            ),
            "mean_collision_events": statistics.mean(collision_values),
            "mean_route_completion_pct": (
                statistics.mean(completion_values) if completion_values else None
            ),
        },
        "episodes": episode_results,
        "notes": [
            "These are results from the lightweight 2D simulator only.",
            "They are not CARLA results or a comparison with a trained CNN.",
            "Steering MAE is null until expert steering labels are supplied.",
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
