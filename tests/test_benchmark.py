"""Integration tests for reproducible autonomous-driving scenarios."""

from pathlib import Path
import tempfile
import unittest

from autodrive_sim.benchmark import SCENARIOS, create_scenario, run_episode
from autodrive_sim.simulator.road import Road


class BenchmarkTests(unittest.TestCase):
    def test_baseline_clear_episode_completes_with_stable_lane_tracking(self):
        result = run_episode()
        self.assertAlmostEqual(result["route_completion_pct"], 100.0)
        self.assertLess(result["lane_deviation_mean_m"], 0.25)
        self.assertEqual(result["collision_events"], 0)
        self.assertEqual(result["completed"], 1)
        self.assertGreater(result["distance_travelled_m"], 0.0)

    def test_safety_controller_completes_clear_route(self):
        result = run_episode(controller_name="safety")
        self.assertAlmostEqual(result["route_completion_pct"], 100.0)
        self.assertEqual(result["collision_events"], 0)

    def test_all_scenarios_are_available(self):
        self.assertEqual(
            SCENARIOS,
            ("clear", "center", "edge", "outside", "multiple"),
        )

    def test_clear_scenario_has_no_obstacles(self):
        self.assertEqual(create_scenario("clear", Road()), ())

    def test_center_scenario_places_obstacle_on_lane_center(self):
        road = Road()
        obstacles = create_scenario("center", road)
        self.assertEqual(len(obstacles), 1)
        self.assertAlmostEqual(
            obstacles[0].y, road.center_y(obstacles[0].x)
        )

    def test_edge_scenario_places_obstacle_near_lane_boundary(self):
        road = Road()
        obstacles = create_scenario("edge", road)
        self.assertEqual(len(obstacles), 1)
        self.assertAlmostEqual(
            obstacles[0].y - road.center_y(obstacles[0].x), 1.0
        )

    def test_outside_scenario_is_beyond_lane_relevance_corridor(self):
        road = Road()
        obstacles = create_scenario("outside", road)
        self.assertEqual(len(obstacles), 1)
        self.assertGreater(
            abs(obstacles[0].y - road.center_y(obstacles[0].x)), 2.0
        )

    def test_multiple_scenario_contains_two_obstacles(self):
        obstacles = create_scenario("multiple", Road())
        self.assertEqual(len(obstacles), 2)
        self.assertLess(obstacles[0].x, obstacles[1].x)

    def test_unknown_scenario_is_rejected(self):
        with self.assertRaises(ValueError):
            create_scenario("unknown", Road())

    def test_unknown_controller_is_rejected(self):
        with self.assertRaises(ValueError):
            run_episode(controller_name="unknown")

    def test_baseline_collides_with_center_obstacle(self):
        result = run_episode(
            controller_name="baseline", scenario_name="center"
        )
        self.assertEqual(result["collision_events"], 1)
        self.assertEqual(result["scenario_collision"], 1)
        self.assertEqual(result["completed"], 1)

    def test_safety_controller_stops_before_center_obstacle(self):
        result = run_episode(
            controller_name="safety", scenario_name="center"
        )
        self.assertEqual(result["collision_events"], 0)
        self.assertEqual(result["scenario_collision"], 0)
        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["stopped_before_route"], 1)
        self.assertLess(result["route_completion_pct"], 100.0)
        self.assertAlmostEqual(result["final_speed_mps"], 0.0)

    def test_safety_controller_does_not_brake_for_outside_obstacle(self):
        result = run_episode(
            controller_name="safety", scenario_name="outside"
        )
        self.assertEqual(result["collision_events"], 0)
        self.assertEqual(result["completed"], 1)
        self.assertEqual(result["stopped_before_route"], 0)
        self.assertAlmostEqual(result["route_completion_pct"], 100.0)

    def test_safety_controller_stops_for_edge_obstacle(self):
        result = run_episode(
            controller_name="safety", scenario_name="edge"
        )
        self.assertEqual(result["collision_events"], 0)
        self.assertEqual(result["stopped_before_route"], 1)

    def test_baseline_can_hit_multiple_obstacles(self):
        result = run_episode(
            controller_name="baseline", scenario_name="multiple"
        )
        self.assertEqual(result["collision_events"], 2)

    def test_safety_controller_stops_before_first_of_multiple_obstacles(self):
        result = run_episode(
            controller_name="safety", scenario_name="multiple"
        )
        self.assertEqual(result["collision_events"], 0)
        self.assertEqual(result["stopped_before_route"], 1)

    def test_benchmark_can_export_episode_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "episode.csv"
            result = run_episode(telemetry_path=output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 100)
            self.assertAlmostEqual(result["route_completion_pct"], 100.0)

    def test_scenario_episode_reports_completion_state(self):
        result = run_episode(scenario_name="outside")
        self.assertEqual(result["completed"], 1)
        self.assertEqual(result["scenario_collision"], 0)


if __name__ == "__main__":
    unittest.main()
