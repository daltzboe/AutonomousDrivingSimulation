"""Smoke tests for the local dashboard-to-Python benchmark API."""

import unittest

from autodrive_sim.api import run_benchmark, run_controller_comparison


class BenchmarkAPITests(unittest.TestCase):
    def test_api_report_contains_real_benchmark_aggregate_and_episode(self):
        report = run_benchmark("steering", "center", 1)

        self.assertEqual(report["controller"], "steering")
        self.assertEqual(report["scenario"], "center")
        self.assertEqual(report["simulator"], "lightweight_2d")
        self.assertEqual(report["episode_count"], 1)
        self.assertIn("mean_lane_deviation_m", report["aggregate"])
        self.assertIn("mean_collision_events", report["aggregate"])
        self.assertIn("mean_route_completion_pct", report["aggregate"])
        self.assertEqual(len(report["episodes"]), 1)
        self.assertEqual(report["episodes"][0]["collision_events"], 0)

    def test_comparison_runs_all_controllers_on_same_scenario(self):
        report = run_controller_comparison("outside", 1)

        self.assertEqual(report["scenario"], "outside")
        self.assertEqual(report["episode_count_per_controller"], 1)
        self.assertEqual([item["controller"] for item in report["reports"]], ["baseline", "safety", "steering"])
        self.assertTrue(all(item["episode_count"] == 1 for item in report["reports"]))

    def test_api_aggregates_repeatable_episodes(self):
        report = run_benchmark("baseline", "clear", 2)

        self.assertEqual(report["episode_count"], 2)
        self.assertEqual(len(report["episodes"]), 2)
        self.assertAlmostEqual(
            report["aggregate"]["mean_route_completion_pct"], 100.0
        )
        self.assertEqual(report["aggregate"]["std_route_completion_pct"], 0.0)
        single = run_benchmark("baseline", "clear", 1)
        self.assertIsNone(single["aggregate"]["std_route_completion_pct"])


if __name__ == "__main__":
    unittest.main()
