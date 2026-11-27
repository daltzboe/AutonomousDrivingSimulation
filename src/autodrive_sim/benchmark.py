"""Run reproducible autonomous-driving scenarios and export metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

from autodrive_sim.controllers import (
    ObstacleAvoidanceController,
    IntelligentDrivingController,
    SteeringObstacleAvoidanceController,
)
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.simulation import Obstacle, Simulation


SCENARIOS = ("clear", "center", "edge", "outside", "multiple")


def create_scenario(name: str, road: Road) -> tuple[Obstacle, ...]:
    """Create a deterministic obstacle layout for a named scenario."""
    if name not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario {name!r}. Choose from: {', '.join(SCENARIOS)}"
        )

    if name == "clear":
        return ()
    if name == "center":
        return (Obstacle(100.0, road.center_y(100.0), 0.35),)
    if name == "edge":
        return (Obstacle(100.0, road.center_y(100.0) + 1.0, 0.35),)
    if name == "outside":
        return (Obstacle(100.0, road.center_y(100.0) + 4.0, 0.35),)

    return (
        Obstacle(100.0, road.center_y(100.0), 0.35),
        Obstacle(220.0, road.center_y(220.0), 0.35),
    )


def run_episode(
    telemetry_path: Path | None = None,
    controller_name: str = "baseline",
    scenario_name: str = "clear",
) -> dict[str, float | int | None]:
    """Run one scenario and optionally save its telemetry as CSV."""
    if controller_name not in {"baseline", "safety", "steering", "intelligent"}:
        raise ValueError(
            "controller_name must be 'baseline', 'safety', 'steering', or 'intelligent'"
        )

    # The benchmark uses a 4.8 m lane so the vehicle can safely pass a
    # stationary obstacle while remaining within the road boundaries.
    road = Road(lane_width=4.8)
    obstacles = create_scenario(scenario_name, road)
    controller = (
        ObstacleAvoidanceController()
        if controller_name == "safety"
        else SteeringObstacleAvoidanceController()
        if controller_name == "steering"
        else IntelligentDrivingController()
        if controller_name == "intelligent"
        else None
    )
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
        # A full-brake safety command that has brought the vehicle to rest is
        # a valid safe-stop outcome, not a failed benchmark execution.
        if simulation.last_command.brake >= 1.0 and simulation.vehicle.speed <= 1e-9:
            break

    if telemetry_path is not None:
        simulation.recorder.write_csv(telemetry_path)

    result = simulation.summary()
    result.update(
        {
            "route_completion_pct": simulation.route_completion_pct,
            "completed": int(simulation.completed),
            "scenario_collision": int(simulation.collision),
            "stopped_before_route": int(
                not simulation.completed
                and not simulation.collision
                and simulation.vehicle.speed <= 1e-9
            ),
            "final_speed_mps": simulation.vehicle.speed,
        }
    )
    return result


def main() -> None:
    """Run benchmark episodes from the command line."""
    parser = argparse.ArgumentParser(
        description="Compare rule-based controllers in repeatable driving scenarios."
    )
    parser.add_argument(
        "--episodes", type=int, default=1,
        help="number of identical episodes to run (1-100)",
    )
    parser.add_argument(
        "--controller", choices=("baseline", "safety", "steering", "intelligent"), default="baseline",
        help="baseline lane follower, emergency braking, steering avoidance, or intelligent decision control",
    )
    parser.add_argument(
        "--scenario", choices=SCENARIOS, default="clear",
        help="deterministic obstacle scenario to evaluate",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="optional JSON file for the experiment summary",
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
        episode_results.append(
            run_episode(
                telemetry_path=telemetry_path,
                controller_name=args.controller,
                scenario_name=args.scenario,
            )
        )

    lane_values = [
        float(result["lane_deviation_mean_m"])
        for result in episode_results
        if result["lane_deviation_mean_m"] is not None
    ]
    report = {
        "controller": args.controller,
        "scenario": args.scenario,
        "simulator": "lightweight_2d",
        "episode_count": len(episode_results),
        "aggregate": {
            "mean_lane_deviation_m": (
                statistics.mean(lane_values) if lane_values else None
            ),
            "mean_collision_events": statistics.mean(
                int(result["collision_events"]) for result in episode_results
            ),
            "mean_route_completion_pct": statistics.mean(
                float(result["route_completion_pct"])
                for result in episode_results
            ),
            "safe_stop_rate": statistics.mean(
                int(result["stopped_before_route"])
                for result in episode_results
            ),
        },
        "episodes": episode_results,
        "notes": [
            "Results are from the deterministic lightweight 2D simulator.",
            "The safety controller performs emergency braking; the steering controller plans a smooth lateral bypass; the intelligent controller adds CRUISE, APPROACH, AVOID, and BRAKE decisions with adaptive speed.",
            "Benchmark road width is 4.8 m to provide a feasible passing corridor for the configured vehicle and obstacle sizes.",
            "A safe stop before the destination is reported as incomplete route completion.",
            "These results are not CARLA results or trained neural-network results.",
            "Steering MAE requires expert steering labels.",
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
