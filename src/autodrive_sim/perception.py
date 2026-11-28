"""Geometric obstacle perception with reproducible sensor uncertainty.

This is a lightweight range/bearing sensor model, not real LiDAR or learned
computer vision. It approximates noisy measurements and occasional misses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Iterable, Protocol

from autodrive_sim.simulator.vehicle import Vehicle


class ObstacleGeometry(Protocol):
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class DetectedObstacle:
    """Estimated obstacle position plus sensor metadata."""

    x: float
    y: float
    radius: float
    range_m: float
    bearing_rad: float
    confidence: float


@dataclass
class ObstaclePerception:
    """Range/FOV filter with configurable Gaussian noise and missed returns."""

    max_range_m: float = 60.0
    field_of_view_deg: float = 120.0
    range_noise_std_m: float = 0.35
    bearing_noise_std_deg: float = 1.2
    miss_probability: float = 0.04
    seed: int = 7
    _rng: random.Random = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_range_m) or self.max_range_m <= 0:
            raise ValueError("max_range_m must be positive and finite")
        if not math.isfinite(self.field_of_view_deg) or not 0 < self.field_of_view_deg <= 360:
            raise ValueError("field_of_view_deg must be in (0, 360]")
        if not math.isfinite(self.range_noise_std_m) or self.range_noise_std_m < 0:
            raise ValueError("range_noise_std_m must be finite and non-negative")
        if not math.isfinite(self.bearing_noise_std_deg) or self.bearing_noise_std_deg < 0:
            raise ValueError("bearing_noise_std_deg must be finite and non-negative")
        if not math.isfinite(self.miss_probability) or not 0 <= self.miss_probability < 1:
            raise ValueError("miss_probability must be in [0, 1)")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        self._rng = random.Random(self.seed)

    def detect(self, vehicle: Vehicle, obstacles: Iterable[ObstacleGeometry]) -> tuple[DetectedObstacle, ...]:
        """Return noisy estimated detections nearest-first.

        A fixed seed reproduces the same sequence of sensor readings. Noise is
        sampled per detection; missed returns are modeled probabilistically.
        """
        half_fov = math.radians(self.field_of_view_deg) / 2.0
        detections = []
        for obstacle in obstacles:
            dx = obstacle.x - vehicle.x
            dy = obstacle.y - vehicle.y
            true_range = math.hypot(dx, dy)
            true_bearing = (math.atan2(dy, dx) - vehicle.yaw + math.pi) % (2.0 * math.pi) - math.pi
            if dx < 0 or true_range > self.max_range_m or abs(true_bearing) > half_fov:
                continue
            confidence = max(0.6, 1.0 - 0.4 * true_range / self.max_range_m)
            if self._rng.random() < self.miss_probability * (1.0 + (1.0 - confidence)):
                continue
            measured_range = max(0.0, true_range + self._rng.gauss(0.0, self.range_noise_std_m))
            measured_bearing = true_bearing + self._rng.gauss(
                0.0, math.radians(self.bearing_noise_std_deg)
            )
            estimated_x = vehicle.x + measured_range * math.cos(vehicle.yaw + measured_bearing)
            estimated_y = vehicle.y + measured_range * math.sin(vehicle.yaw + measured_bearing)
            detections.append(
                DetectedObstacle(
                    x=estimated_x,
                    y=estimated_y,
                    radius=obstacle.radius,
                    range_m=measured_range,
                    bearing_rad=measured_bearing,
                    confidence=confidence,
                )
            )
        return tuple(sorted(detections, key=lambda item: item.range_m))
