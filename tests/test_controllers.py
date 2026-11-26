"""Tests for baseline and obstacle-avoidance controllers."""

import unittest

from autodrive_sim.controllers import (
    LaneFollowingController,
    ObstacleAvoidanceController,
    SteeringObstacleAvoidanceController,
)
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


class EmergencyBrakingControllerTests(unittest.TestCase):
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


class SteeringObstacleAvoidanceControllerTests(unittest.TestCase):
    def test_steering_controller_selects_a_bypass_path(self) -> None:
        road = Road(lane_width=4.8)
        vehicle = Vehicle(x=70.0, y=road.center_y(70.0), speed=10.0)
        obstacle = Obstacle(x=100.0, y=road.center_y(100.0), radius=0.35)

        command = SteeringObstacleAvoidanceController().control(
            vehicle, road, (obstacle,)
        )

        self.assertNotEqual(command.steering, 0.0)
        self.assertEqual(command.brake, 0.0)
        self.assertGreaterEqual(command.steering, -1.0)
        self.assertLessEqual(command.steering, 1.0)

    def test_steering_controller_passes_on_opposite_side_of_edge_obstacle(self) -> None:
        road = Road(lane_width=4.8)
        vehicle = Vehicle(x=80.0, y=road.center_y(80.0), speed=10.0)
        obstacle = Obstacle(
            x=100.0, y=road.center_y(100.0) + 1.0, radius=0.35
        )

        command = SteeringObstacleAvoidanceController().control(
            vehicle, road, (obstacle,)
        )

        self.assertLess(command.steering, 0.0)
        self.assertEqual(command.brake, 0.0)

    def test_steering_controller_brakes_when_lane_is_too_narrow_to_pass(self) -> None:
        road = Road(lane_width=3.6)
        vehicle = Vehicle(x=92.0, y=road.center_y(92.0), speed=10.0)
        obstacle = Obstacle(x=100.0, y=road.center_y(100.0), radius=0.35)

        command = SteeringObstacleAvoidanceController().control(
            vehicle, road, (obstacle,)
        )

        self.assertEqual(command.throttle, 0.0)
        self.assertEqual(command.brake, 1.0)

    def test_steering_controller_ignores_obstacles_outside_detection_range(self) -> None:
        road = Road(lane_width=4.8)
        vehicle = Vehicle(x=0.0, y=road.center_y(0.0), speed=5.0)
        obstacle = Obstacle(x=100.0, y=road.center_y(100.0), radius=0.35)

        command = SteeringObstacleAvoidanceController().control(
            vehicle, road, (obstacle,)
        )

        baseline = LaneFollowingController().control(vehicle, road)
        self.assertEqual(command, baseline)

    def test_invalid_avoidance_settings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SteeringObstacleAvoidanceController(vehicle_radius_m=0.0)


if __name__ == "__main__":
    unittest.main()
