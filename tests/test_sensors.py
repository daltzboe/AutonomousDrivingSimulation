"""Tests for the deterministic planar range sensor."""

import math
import unittest

from autodrive_sim.sensors import RangeSensor
from autodrive_sim.simulator.simulation import Obstacle
from autodrive_sim.simulator.vehicle import Vehicle


class RangeSensorTests(unittest.TestCase):
    def test_detects_obstacle_ahead_at_surface_distance(self) -> None:
        ray_count = 5
        sensor = RangeSensor(field_of_view_deg=90, max_range_m=30, ray_count=ray_count)
        scan = sensor.scan(Vehicle(), (Obstacle(x=10.0, y=0.0, radius=1.0),))
        self.assertAlmostEqual(scan.nearest_distance_m, 9.0)
        self.assertEqual(len(scan.distances_m), ray_count)

    def test_returns_maximum_range_when_no_obstacle_is_visible(self) -> None:
        scan = RangeSensor(max_range_m=18.0).scan(Vehicle(), ())
        self.assertTrue(all(distance == 18.0 for distance in scan.distances_m))

    def test_ignores_obstacles_behind_vehicle(self) -> None:
        scan = RangeSensor().scan(
            Vehicle(), (Obstacle(x=-3.0, y=0.0, radius=0.5),)
        )
        self.assertEqual(scan.nearest_distance_m, 35.0)

    def test_rotated_vehicle_changes_sensor_direction(self) -> None:
        vehicle = Vehicle(yaw=math.pi / 2)
        scan = RangeSensor(field_of_view_deg=30).scan(
            vehicle, (Obstacle(x=0.0, y=8.0, radius=1.0),)
        )
        self.assertAlmostEqual(scan.nearest_distance_m, 7.0)

    def test_invalid_sensor_settings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RangeSensor(field_of_view_deg=0)
        with self.assertRaises(ValueError):
            RangeSensor(max_range_m=0)
        with self.assertRaises(ValueError):
            RangeSensor(ray_count=1)


if __name__ == "__main__":
    unittest.main()
