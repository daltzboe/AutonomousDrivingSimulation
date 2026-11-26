"""Unit tests for the controller evaluation metrics."""

import unittest

from autodrive_sim.metrics import EvaluationMetrics


class EvaluationMetricsTests(unittest.TestCase):
    def test_steering_mae(self) -> None:
        metrics = EvaluationMetrics()
        metrics.add_steering_prediction(0.5, 0.3)
        metrics.add_steering_prediction(-0.2, 0.0)
        self.assertAlmostEqual(metrics.summary()["steering_mae"], 0.2)

    def test_lane_deviation_mean(self) -> None:
        metrics = EvaluationMetrics()
        metrics.add_lane_deviation(0.2)
        metrics.add_lane_deviation(0.4)
        self.assertAlmostEqual(metrics.summary()["lane_deviation_mean_m"], 0.3)

    def test_collision_rate_per_kilometer(self) -> None:
        metrics = EvaluationMetrics()
        metrics.add_collision()
        metrics.add_distance(500)
        self.assertAlmostEqual(metrics.summary()["collision_rate_per_km"], 2.0)

    def test_route_completion_percentage(self) -> None:
        metrics = EvaluationMetrics()
        metrics.set_route_progress(completed_m=750, total_m=1000)
        self.assertAlmostEqual(metrics.summary()["route_completion_pct"], 75.0)

    def test_missing_measurements_are_none(self) -> None:
        summary = EvaluationMetrics().summary()
        self.assertIsNone(summary["steering_mae"])
        self.assertIsNone(summary["lane_deviation_mean_m"])
        self.assertIsNone(summary["collision_rate_per_km"])
        self.assertIsNone(summary["route_completion_pct"])

    def test_negative_lane_deviation_is_rejected(self) -> None:
        metrics = EvaluationMetrics()
        with self.assertRaises(ValueError):
            metrics.add_lane_deviation(-0.1)

    def test_completed_distance_cannot_exceed_route(self) -> None:
        metrics = EvaluationMetrics()
        with self.assertRaises(ValueError):
            metrics.set_route_progress(completed_m=101, total_m=100)


if __name__ == "__main__":
    unittest.main()
