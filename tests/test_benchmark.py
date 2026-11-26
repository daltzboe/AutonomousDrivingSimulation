"""Integration tests for the repeatable baseline benchmark."""

from pathlib import Path
import tempfile
import unittest

from autodrive_sim.benchmark import run_episode


class BenchmarkTests(unittest.TestCase):
    def test_baseline_episode_completes_with_stable_lane_tracking(self) -> None:
        result = run_episode()
        self.assertAlmostEqual(result["route_completion_pct"], 100.0)
        self.assertLess(result["lane_deviation_mean_m"], 0.25)
        self.assertEqual(result["collision_events"], 0)
        self.assertGreater(result["distance_travelled_m"], 0.0)

    def test_benchmark_can_export_episode_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "episode.csv"
            result = run_episode(output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 100)
            self.assertAlmostEqual(result["route_completion_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
