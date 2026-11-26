"""Tests for the baseline lane-following controller."""

import unittest

from autodrive_sim.controllers import LaneFollowingController
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


if __name__ == "__main__":
    unittest.main()
