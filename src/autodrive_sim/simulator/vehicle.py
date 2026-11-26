"""Vehicle dynamics using a kinematic bicycle model."""

from dataclasses import dataclass
import math


@dataclass
class Vehicle:
    """A lightweight 2D vehicle with normalized control inputs.

    Coordinates are measured in meters, yaw in radians, and speed in m/s.
    Steering input is normalized to [-1, 1].
    """

    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0
    speed: float = 0.0

    wheelbase: float = 2.7
    max_steering_angle: float = 0.55
    max_acceleration: float = 3.0
    max_braking: float = 8.0

    def __post_init__(self) -> None:
        values = (
            self.x,
            self.y,
            self.yaw,
            self.speed,
            self.wheelbase,
            self.max_steering_angle,
            self.max_acceleration,
            self.max_braking,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Vehicle parameters must be finite.")
        if self.speed < 0:
            raise ValueError("Speed cannot be negative.")
        if min(
            self.wheelbase,
            self.max_steering_angle,
            self.max_acceleration,
            self.max_braking,
        ) <= 0:
            raise ValueError("Vehicle limits must be positive.")

    def step(
        self,
        throttle: float,
        brake: float,
        steering: float,
        dt: float,
    ) -> None:
        """Advance the vehicle state by one time step.

        Args:
            throttle: Normalized acceleration command in [0, 1].
            brake: Normalized braking command in [0, 1].
            steering: Normalized steering command in [-1, 1].
            dt: Elapsed simulation time in seconds.
        """
        controls = (throttle, brake, steering, dt)
        if not all(math.isfinite(value) for value in controls):
            raise ValueError("Controls and time step must be finite.")
        if not 0.0 <= throttle <= 1.0:
            raise ValueError("Throttle must be between 0 and 1.")
        if not 0.0 <= brake <= 1.0:
            raise ValueError("Brake must be between 0 and 1.")
        if not -1.0 <= steering <= 1.0:
            raise ValueError("Steering must be between -1 and 1.")
        if dt <= 0.0:
            raise ValueError("Time step must be positive.")

        acceleration = (
            throttle * self.max_acceleration
            - brake * self.max_braking
        )
        self.speed = max(0.0, self.speed + acceleration * dt)

        steering_angle = steering * self.max_steering_angle
        self.yaw += (
            self.speed
            / self.wheelbase
            * math.tan(steering_angle)
            * dt
        )

        self.x += self.speed * math.cos(self.yaw) * dt
        self.y += self.speed * math.sin(self.yaw) * dt
