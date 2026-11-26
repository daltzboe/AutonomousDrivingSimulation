"""Tests for simulation episode orchestration."""

import unittest

from autodrive_sim.controllers import ControlCommand
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.simulation import Obstacle, Simulation


class SimulationTests(unittest.TestCase):
    def test_autopilot_completes_route_and_tracks_lane(self) -> None:
        road = Road(route_length_m=100.0)
        simulation = Simulation(road=road)
        for _ in range(3000):
            simulation.step()
            if simulation.completed:
                break

        self.assertTrue(simulation.completed)
        self.assertGreaterEqual(simulation.route_completion_pct, 99.9)
        self.assertLess(simulation.summary()["lane_deviation_mean_m"], 0.25)
        self.assertEqual(simulation.summary()["collision_events"], 0)

    def test_obstacle_contact_is_counted_once(self) -> None:
        simulation = Simulation(
            road=Road(route_length_m=50.0),
            obstacles=(Obstacle(x=0.0, y=0.0),),
        )
        for _ in range(20):
            simulation.step()
        self.assertTrue(simulation.collision)
        self.assertEqual(simulation.summary()["collision_events"], 1)

    def test_manual_command_is_used(self) -> None:
        simulation = Simulation()
        simulation.step(
            ControlCommand(throttle=1.0, brake=0.0, steering=0.0)
        )
        self.assertEqual(simulation.last_command.throttle, 1.0)
        self.assertGreater(simulation.vehicle.speed, 0.0)

    def test_completed_episode_does_not_advance(self) -> None:
        simulation = Simulation(road=Road(route_length_m=0.1))
        for _ in range(100):
            simulation.step()
            if simulation.completed:
                break
        position = simulation.vehicle.x
        simulation.step()
        self.assertEqual(simulation.vehicle.x, position)

    def test_reset_clears_episode_state(self) -> None:
        simulation = Simulation(
            road=Road(route_length_m=20.0),
            obstacles=(Obstacle(x=0.0, y=0.0),),
        )
        simulation.step()
        simulation.reset()
        self.assertEqual(simulation.vehicle.x, 0.0)
        self.assertEqual(simulation.vehicle.speed, 0.0)
        self.assertFalse(simulation.collision)
        self.assertEqual(simulation.summary()["collision_events"], 0)

    def test_invalid_obstacle_and_timestep_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Obstacle(x=0.0, y=0.0, radius=0.0)
        with self.assertRaises(ValueError):
            Simulation(dt=0.0)


if __name__ == "__main__":
    unittest.main()
