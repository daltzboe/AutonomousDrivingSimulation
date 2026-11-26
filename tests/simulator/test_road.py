"""Tests for deterministic road geometry."""

import math
import unittest

from autodrive_sim.simulator.road import Road


class RoadTests(unittest.TestCase):
    def test_straight_road_center_is_zero(self) -> None:
        road = Road(curve_amplitude_m=0.0)
        self.assertEqual(road.center_y(125.0), 0.0)
        self.assertEqual(road.center_heading(125.0), 0.0)

    def test_curved_road_center_is_deterministic(self) -> None:
        road = Road()
        self.assertAlmostEqual(road.center_y(25.0), road.center_y(25.0))
        self.assertGreater(road.center_y(25.0), 0.0)

    def test_lane_deviation_is_absolute(self) -> None:
        road = Road(curve_amplitude_m=0.0)
        self.assertAlmostEqual(road.lane_deviation(0.0, -0.4), 0.4)
        self.assertAlmostEqual(road.lane_deviation(0.0, 0.4), 0.4)

    def test_lane_boundary_is_inclusive(self) -> None:
        road = Road(curve_amplitude_m=0.0, lane_width=4.0)
        self.assertTrue(road.is_on_road(10.0, 2.0))
        self.assertFalse(road.is_on_road(10.0, 2.01))

    def test_non_finite_position_is_rejected(self) -> None:
        road = Road()
        with self.assertRaises(ValueError):
            road.center_y(math.nan)
        with self.assertRaises(ValueError):
            road.lane_deviation(0.0, math.inf)

    def test_invalid_road_dimensions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Road(lane_width=0.0)
        with self.assertRaises(ValueError):
            Road(route_length_m=-1.0)


if __name__ == "__main__":
    unittest.main()
