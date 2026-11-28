"""Simple geometric obstacle perception for the lightweight simulator.

This module models a limited field-of-view/range detection stage. It consumes
simulator obstacle geometry, but exposes only detections to the controller;
it is not camera vision, LiDAR hardware, or a trained perception model.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Protocol

from autodrive_sim.simulator.vehicle import Vehicle


class ObstacleGeometry(Protocol):
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class DetectedObstacle:
    """An obstacle detection in world coordinates with sensor metadata."""

    x: float
    y: float
    radius: float
    range_m: float
    bearing_rad: float
    confidence: float


@dataclass(frozen=True)
class ObstaclePerception:
    """Range/FOV filter that turns world obstacles into sensor detections."""

    max_range_m: float = 60.0
    field_of_view_deg: float = 120.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_range_m) or self.max_range_m <= 0:
            raise ValueError("max_range_m must be positive and finite")
        if (
            not math.isfinite(self.field_of_view_deg)
            or not 0 < self.field_of_view_deg <= 360
        ):
            raise ValueError("field_of_view_deg must be in (0, 360]")

    def detect(
        self, vehicle: Vehicle, obstacles: Iterable[ObstacleGeometry]
    ) -> tuple[DetectedObstacle, ...]:
        """Return visible obstacles ordered nearest-first.

        Confidence gently decreases with range to make sensor metadata useful
        for future noisy/learned perception experiments.
        """
        half_fov = math.radians(self.field_of_view_deg) / 2.0
        detections = []
        for obstacle in obstacles:
            dx = obstacle.x - vehicle.x
            dy = obstacle.y - vehicle.y
            distance = math.hypot(dx, dy)
            bearing = (math.atan2(dy, dx) - vehicle.yaw + math.pi) % (
                2.0 * math.pi
            ) - math.pi
            if dx < 0 or distance > self.max_range_m or abs(bearing) > half_fov:
                continue
            confidence = max(0.6, 1.0 - 0.4 * distance / self.max_range_m)
            detections.append(
                DetectedObstacle(
                    x=obstacle.x,
                    y=obstacle.y,
                    radius=obstacle.radius,
                    range_m=distance,
                    bearing_rad=bearing,
                    confidence=confidence,
                )
            )
        return tuple(sorted(detections, key=lambda item: item.range_m))
