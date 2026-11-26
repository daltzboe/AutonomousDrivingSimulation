"""Baseline autonomous controllers for the lightweight simulation."""

from dataclasses import dataclass
import math

from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.vehicle import Vehicle


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class ControlCommand:
    """Normalized vehicle controls."""

    throttle: float = 0.0
    brake: float = 0.0
    steering: float = 0.0


@dataclass
class LaneFollowingController:
    """Pure-pursuit lane follower used as the rule-based baseline.

    The controller aims at a point ahead on the lane center line, converts
    the target-point geometry into a bicycle-model steering angle, and uses
    proportional speed control. It is an educational baseline, not a
    production driving system.
    """

    target_speed_mps: float = 10.0
    lookahead_m: float = 9.0
    steering_gain: float = 1.0
    speed_gain: float = 0.35

    def __post_init__(self) -> None:
        values = (
            self.target_speed_mps,
            self.lookahead_m,
            self.steering_gain,
            self.speed_gain,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Controller settings must be finite.")
        if min(values) <= 0:
            raise ValueError("Controller settings must be positive.")

    def control(self, vehicle: Vehicle, road: Road) -> ControlCommand:
        """Compute a steering and speed command from the current vehicle state."""
        preview_x = vehicle.x + self.lookahead_m
        target_y = road.center_y(preview_x)
        alpha = _wrap_angle(
            math.atan2(target_y - vehicle.y, self.lookahead_m) - vehicle.yaw
        )
        curvature = 2.0 * math.sin(alpha) / self.lookahead_m
        steering_angle = math.atan(vehicle.wheelbase * curvature)
        steering = _clamp(
            self.steering_gain * steering_angle / vehicle.max_steering_angle,
            -1.0,
            1.0,
        )

        speed_error = self.target_speed_mps - vehicle.speed
        throttle = _clamp(speed_error * self.speed_gain, 0.0, 1.0)
        brake = _clamp(-speed_error * self.speed_gain, 0.0, 1.0)
        return ControlCommand(
            throttle=throttle,
            brake=brake,
            steering=steering,
        )
