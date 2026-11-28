"""Tests for the geometric obstacle-perception stage."""

import math
import unittest

from autodrive_sim.perception import ObstaclePerception
from autodrive_sim.simulator.simulation import Obstacle
from autodrive_sim.simulator.vehicle import Vehicle


class ObstaclePerceptionTests(unittest.TestCase):
    def test_detects_ahead_obstacle_and_reports_sensor_metadata(self) -> None:
        detector = ObstaclePerception(max_range_m=40, field_of_view_deg=90)
        result = detector.detect(
            Vehicle(), (Obstacle(x=20, y=0, radius=0.5),)
        )
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0].range_m, 20)
        self.assertAlmostEqual(result[0].bearing_rad, 0)
        self.assertGreaterEqual(result[0].confidence, 0.6)

    def test_filters_obstacles_outside_range_or_behind_vehicle(self) -> None:
        detector = ObstaclePerception(max_range_m=15)
        result = detector.detect(
            Vehicle(),
            (Obstacle(x=20, y=0), Obstacle(x=-3, y=0)),
        )
        self.assertEqual(result, ())

    def test_filters_obstacles_outside_field_of_view(self) -> None:
        detector = ObstaclePerception(field_of_view_deg=60)
        result = detector.detect(
            Vehicle(), (Obstacle(x=10, y=8),)
        )
        self.assertEqual(result, ())

    def test_nearest_detection_is_first_and_confidence_decreases_with_range(self) -> None:
        detector = ObstaclePerception(max_range_m=50)
        result = detector.detect(
            Vehicle(),
            (Obstacle(x=40, y=0), Obstacle(x=10, y=0)),
        )
        self.assertEqual(result[0].range_m, 10)
        self.assertGreater(result[0].confidence, result[1].confidence)


if __name__ == "__main__":
    unittest.main()
