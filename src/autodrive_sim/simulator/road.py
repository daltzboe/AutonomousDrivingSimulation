"""Deterministic road geometry for the lightweight simulator."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Road:
    """A single-lane test route with a smooth, repeatable center line.

    The route is defined in world coordinates: x is forward distance (m),
    y is lateral position (m). This keeps the first simulator independent
    of any graphics or external game engine.
    """

    lane_width: float = 3.6
    curve_amplitude_m: float = 2.8
    curve_frequency_per_m: float = 0.012
    route_length_m: float = 500.0

    def __post_init__(self) -> None:
        values = (
            self.lane_width,
            self.curve_amplitude_m,
            self.curve_frequency_per_m,
            self.route_length_m,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Road parameters must be finite.")
        if self.lane_width <= 0 or self.route_length_m <= 0:
            raise ValueError("Lane width and route length must be positive.")
        if self.curve_amplitude_m < 0 or self.curve_frequency_per_m < 0:
            raise ValueError("Curve parameters cannot be negative.")

    def center_y(self, x: float) -> float:
        """Return the road center's lateral coordinate at forward position x."""
        if not math.isfinite(x):
            raise ValueError("Road position must be finite.")
        return self.curve_amplitude_m * math.sin(
            self.curve_frequency_per_m * x
        )

    def center_heading(self, x: float) -> float:
        """Return the tangent heading of the road center line in radians."""
        if not math.isfinite(x):
            raise ValueError("Road position must be finite.")
        slope = (
            self.curve_amplitude_m
            * self.curve_frequency_per_m
            * math.cos(self.curve_frequency_per_m * x)
        )
        return math.atan(slope)

    def lane_deviation(self, x: float, y: float) -> float:
        """Return absolute lateral distance from the lane center in meters."""
        if not math.isfinite(y):
            raise ValueError("Vehicle position must be finite.")
        return abs(y - self.center_y(x))

    def is_on_road(self, x: float, y: float) -> bool:
        """Return whether a point is within the lane boundaries."""
        return self.lane_deviation(x, y) <= self.lane_width / 2.0
