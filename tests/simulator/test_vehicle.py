"""Unit tests for the kinematic bicycle vehicle model."""

import math
import unittest

from autodrive_sim.simulator.vehicle import Vehicle


class VehicleTests(unittest.TestCase):
    def test_default_vehicle_starts_at_rest(self) -> None:
        vehicle = Vehicle()
        self.assertEqual((vehicle.x, vehicle.y, vehicle.yaw, vehicle.speed), (0, 0, 0, 0))

    def test_throttle_accelerates_vehicle(self) -> None:
        vehicle = Vehicle()
        vehicle.step(throttle=1.0, brake=0.0, steering=0.0, dt=1.0)
        self.assertAlmostEqual(vehicle.speed, 3.0)
        self.assertAlmostEqual(vehicle.x, 3.0)
        self.assertAlmostEqual(vehicle.y, 0.0)

    def test_braking_reduces_speed(self) -> None:
        vehicle = Vehicle(speed=10.0)
        vehicle.step(throttle=0.0, brake=0.5, steering=0.0, dt=1.0)
        self.assertAlmostEqual(vehicle.speed, 6.0)

    def test_braking_does_not_make_speed_negative(self) -> None:
        vehicle = Vehicle(speed=1.0)
        vehicle.step(throttle=0.0, brake=1.0, steering=0.0, dt=1.0)
        self.assertEqual(vehicle.speed, 0.0)

    def test_steering_changes_heading_and_position(self) -> None:
        vehicle = Vehicle(speed=5.0)
        vehicle.step(throttle=0.0, brake=0.0, steering=1.0, dt=0.5)
        self.assertGreater(vehicle.yaw, 0.0)
        self.assertGreater(vehicle.y, 0.0)

    def test_negative_steering_changes_heading_right(self) -> None:
        vehicle = Vehicle(speed=5.0)
        vehicle.step(throttle=0.0, brake=0.0, steering=-1.0, dt=0.5)
        self.assertLess(vehicle.yaw, 0.0)
        self.assertLess(vehicle.y, 0.0)

    def test_invalid_controls_are_rejected(self) -> None:
        vehicle = Vehicle()
        invalid_inputs = (
            (1.1, 0.0, 0.0, 0.1),
            (0.0, -0.1, 0.0, 0.1),
            (0.0, 0.0, 1.1, 0.1),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, -0.1),
        )
        for controls in invalid_inputs:
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    vehicle.step(*controls)

    def test_non_finite_control_is_rejected(self) -> None:
        vehicle = Vehicle()
        with self.assertRaises(ValueError):
            vehicle.step(throttle=math.nan, brake=0.0, steering=0.0, dt=0.1)

    def test_invalid_vehicle_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Vehicle(speed=-1.0)
        with self.assertRaises(ValueError):
            Vehicle(wheelbase=0.0)
        with self.assertRaises(ValueError):
            Vehicle(x=math.inf)


if __name__ == "__main__":
    unittest.main()
