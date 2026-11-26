"""Tests for the baseline lane-following controller."""

import unittest

from autodrive_sim.controllers import LaneFollowingController, ObstacleAvoidanceController
from autodrive_sim.simulator.simulation import Obstacle
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.vehicle import Vehicle


class LaneFollowingControllerTests(unittest.TestCase):
    def test_commands_stay_within_normalized_limits(self) -> None:
        controller = LaneFollowingController()
        command = controller.control(Vehicle(y=20.0, speed=2.0), Road())
        self.assertGreaterEqual(command.throttle, 0.0)
        self.assertLessEqual(command.throttle, 1.0)
        self.assertGreaterEqual(command.brake, 0.0)
        self.assertLessEqual(command.brake, 1.0)
        self.assertGreaterEqual(command.steering, -1.0)
        self.assertLessEqual(command.steering, 1.0)

    def test_controller_accelerates_below_target_speed(self) -> None:
        command = LaneFollowingController(target_speed_mps=10.0).control(
            Vehicle(speed=2.0), Road()
        )
        self.assertGreater(command.throttle, 0.0)
        self.assertEqual(command.brake, 0.0)

    def test_controller_brakes_above_target_speed(self) -> None:
        command = LaneFollowingController(target_speed_mps=10.0).control(
            Vehicle(speed=15.0), Road()
        )
        self.assertEqual(command.throttle, 0.0)
        self.assertGreater(command.brake, 0.0)

    def test_invalid_controller_settings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LaneFollowingController(lookahead_m=0.0)

    def test_safety_controller_brakes_for_close_path_obstacle(self) -> None:
        controller = ObstacleAvoidanceController()
        vehicle = Vehicle(speed=10.0)
        command = controller.control(
            vehicle, Road(), (Obstacle(x=6.0, y=0.0, radius=0.5),)
        )
        self.assertEqual(command.throttle, 0.0)
        self.assertEqual(command.brake, 1.0)

    def test_safety_controller_ignores_obstacle_outside_vehicle_path(self) -> None:
        controller = ObstacleAvoidanceController()
        vehicle = Vehicle(speed=10.0)
        command = controller.control(
            vehicle, Road(), (Obstacle(x=6.0, y=2.0, radius=0.3),)
        )
        self.assertEqual(command.brake, 0.0)

    def test_safety_controller_does_not_brake_for_distant_obstacle(self) -> None:
        controller = ObstacleAvoidanceController()
        vehicle = Vehicle(speed=10.0)
        command = controller.control(
            vehicle, Road(), (Obstacle(x=60.0, y=0.0, radius=0.5),)
        )
        self.assertEqual(command.brake, 0.0)


if __name__ == "__main__":
    unittest.main()
