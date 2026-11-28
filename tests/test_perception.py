"""Tests for obstacle perception and sensor uncertainty."""
import unittest

from autodrive_sim.perception import ObstaclePerception
from autodrive_sim.simulator.simulation import Obstacle
from autodrive_sim.simulator.vehicle import Vehicle


class ObstaclePerceptionTests(unittest.TestCase):
    def test_detects_obstacle_and_reports_metadata(self):
        detector = ObstaclePerception(range_noise_std_m=0, bearing_noise_std_deg=0)
        result = detector.detect(Vehicle(), (Obstacle(x=20, y=0, radius=0.5),))
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0].range_m, 20)
        self.assertAlmostEqual(result[0].bearing_rad, 0)

    def test_filters_out_of_range_and_behind_obstacles(self):
        detector = ObstaclePerception(max_range_m=15)
        self.assertEqual(detector.detect(Vehicle(), (Obstacle(x=20, y=0), Obstacle(x=-3, y=0))), ())

    def test_filters_outside_field_of_view(self):
        detector = ObstaclePerception(field_of_view_deg=60)
        self.assertEqual(detector.detect(Vehicle(), (Obstacle(x=10, y=8),)), ())

    def test_seed_reproduces_noisy_sensor_sequence(self):
        obstacles = (Obstacle(x=22, y=2), Obstacle(x=35, y=-1))
        first = ObstaclePerception(seed=123, miss_probability=0).detect(Vehicle(), obstacles)
        second = ObstaclePerception(seed=123, miss_probability=0).detect(Vehicle(), obstacles)
        self.assertEqual(first, second)
        self.assertNotAlmostEqual(first[0].range_m, 22, places=4)

    def test_miss_probability_one_is_rejected(self):
        with self.assertRaises(ValueError):
            ObstaclePerception(miss_probability=1.0)

    def test_zero_noise_is_exact_and_misses_can_be_disabled(self):
        detector = ObstaclePerception(range_noise_std_m=0, bearing_noise_std_deg=0, miss_probability=0)
        detection = detector.detect(Vehicle(), (Obstacle(x=10, y=0),))[0]
        self.assertEqual(detection.x, 10)
        self.assertEqual(detection.y, 0)


if __name__ == "__main__":
    unittest.main()
