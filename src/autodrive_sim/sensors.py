"""Deterministic 2D range sensing for the lightweight simulator.

This is a geometric sensor model for development and testing. It is not a
physical LiDAR implementation and does not model noise, occlusion by vehicle
geometry, or sensor calibration.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Protocol

from autodrive_sim.simulator.vehicle import Vehicle


class CircularObstacle(Protocol):
    """Minimal obstacle shape required by the range sensor."""

    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class RangeScan:
    """One planar range scan in vehicle-relative ray order."""

    angles_rad: tuple[float, ...]
    distances_m: tuple[float, ...]

    @property
    def nearest_distance_m(self) -> float:
        """Return the nearest measured surface distance, or infinity."""
        return min(self.distances_m, default=math.inf)


@dataclass(frozen=True)
class RangeSensor:
    """A deterministic planar ray sensor mounted at the vehicle origin."""

    field_of_view_deg: float = 120.0
    max_range_m: float = 35.0
    ray_count: int = 61

    def __post_init__(self) -> None:
        if not math.isfinite(self.field_of_view_deg) or not 0 < self.field_of_view_deg <= 360:
            raise ValueError("field_of_view_deg must be in (0, 360]")
        if not math.isfinite(self.max_range_m) or self.max_range_m <= 0:
            raise ValueError("max_range_m must be positive and finite")
        if isinstance(self.ray_count, bool) or not isinstance(self.ray_count, int) or self.ray_count < 2:
            raise ValueError("ray_count must be an integer of at least 2")

    def scan(
        self, vehicle: Vehicle, obstacles: Iterable[CircularObstacle]
    ) -> RangeScan:
        """Cast evenly spaced rays and return nearest circle intersections."""
        half_fov = math.radians(self.field_of_view_deg) / 2.0
        angles = tuple(
            -half_fov + (2.0 * half_fov * index / (self.ray_count - 1))
            for index in range(self.ray_count)
        )
        obstacle_list = tuple(obstacles)
        distances: list[float] = []

        for relative_angle in angles:
            ray_angle = vehicle.yaw + relative_angle
            direction_x = math.cos(ray_angle)
            direction_y = math.sin(ray_angle)
            nearest = self.max_range_m

            for obstacle in obstacle_list:
                offset_x = obstacle.x - vehicle.x
                offset_y = obstacle.y - vehicle.y
                projection = offset_x * direction_x + offset_y * direction_y
                if projection < 0:
                    continue

                perpendicular_sq = (
                    offset_x * offset_x + offset_y * offset_y
                    - projection * projection
                )
                radius_sq = obstacle.radius * obstacle.radius
                if perpendicular_sq > radius_sq:
                    continue

                entry_distance = projection - math.sqrt(
                    max(0.0, radius_sq - perpendicular_sq)
                )
                if 0.0 <= entry_distance < nearest:
                    nearest = entry_distance

            distances.append(nearest)

        return RangeScan(angles_rad=angles, distances_m=tuple(distances))
