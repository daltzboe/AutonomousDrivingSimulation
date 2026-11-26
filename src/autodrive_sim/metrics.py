"""Evaluation metrics for comparing autonomous driving controllers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math


def _require_finite_non_negative(name: str, value: float) -> float:
    numeric_value = float(value)
    if not math.isfinite(numeric_value) or numeric_value < 0:
        raise ValueError(f"{name} must be a finite, non-negative number")
    return numeric_value


@dataclass
class EvaluationMetrics:
    """Accumulate episode measurements and produce a comparable summary.

    Collision rate is reported as collision events per kilometer driven.
    Lane deviation is the mean absolute distance from the lane center in
    meters. Steering MAE compares predicted steering with expert steering.
    Route completion is completed route distance divided by total route
    distance, expressed as a percentage.
    """

    steering_absolute_error_sum: float = 0.0
    steering_samples: int = 0
    lane_deviation_sum_m: float = 0.0
    lane_deviation_samples: int = 0
    collision_events: int = 0
    distance_travelled_m: float = 0.0
    route_distance_m: float = 0.0
    route_completed_m: float = 0.0

    def add_steering_prediction(self, predicted: float, expert: float) -> None:
        predicted_value = float(predicted)
        expert_value = float(expert)
        if not math.isfinite(predicted_value) or not math.isfinite(expert_value):
            raise ValueError("steering values must be finite")
        self.steering_absolute_error_sum += abs(predicted_value - expert_value)
        self.steering_samples += 1

    def add_lane_deviation(self, deviation_m: float) -> None:
        self.lane_deviation_sum_m += _require_finite_non_negative(
            "deviation_m", deviation_m
        )
        self.lane_deviation_samples += 1

    def add_collision(self, count: int = 1) -> None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("collision count must be a non-negative integer")
        self.collision_events += count

    def add_distance(self, distance_m: float) -> None:
        self.distance_travelled_m += _require_finite_non_negative(
            "distance_m", distance_m
        )

    def set_route_progress(self, completed_m: float, total_m: float) -> None:
        total = _require_finite_non_negative("total_m", total_m)
        completed = _require_finite_non_negative("completed_m", completed_m)
        if total == 0:
            raise ValueError("total route distance must be greater than zero")
        if completed > total:
            raise ValueError("completed route distance cannot exceed total distance")
        self.route_completed_m = completed
        self.route_distance_m = total

    def summary(self) -> dict[str, float | int | None]:
        """Return metrics in stable, JSON-friendly units."""

        distance_km = self.distance_travelled_m / 1000.0
        return {
            "steering_mae": (
                self.steering_absolute_error_sum / self.steering_samples
                if self.steering_samples
                else None
            ),
            "lane_deviation_mean_m": (
                self.lane_deviation_sum_m / self.lane_deviation_samples
                if self.lane_deviation_samples
                else None
            ),
            "collision_events": self.collision_events,
            "collision_rate_per_km": (
                self.collision_events / distance_km if distance_km > 0 else None
            ),
            "distance_travelled_m": self.distance_travelled_m,
            "route_completion_pct": (
                100.0 * self.route_completed_m / self.route_distance_m
                if self.route_distance_m > 0
                else None
            ),
        }

    def to_dict(self) -> dict[str, float | int | None]:
        """Alias for callers that prefer serialization-oriented naming."""

        return self.summary()
