"""Temporal obstacle tracking and short-horizon motion prediction.

Tracks associate noisy detections across simulation frames, estimate velocity,
and retain briefly missed objects using constant-velocity extrapolation.
This is a lightweight simulation component, not a production perception stack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable

from autodrive_sim.perception import DetectedObstacle


@dataclass
class ObstacleTrack:
    """A tracked obstacle with a smoothed world-coordinate velocity estimate."""

    track_id: int
    x: float
    y: float
    radius: float
    vx_mps: float = 0.0
    vy_mps: float = 0.0
    confidence: float = 1.0
    age_frames: int = 1
    missed_frames: int = 0

    def predict(self, horizon_seconds: float) -> tuple[float, float]:
        """Predict the obstacle's world position under constant velocity."""
        if not math.isfinite(horizon_seconds) or horizon_seconds < 0:
            raise ValueError("Prediction horizon must be finite and non-negative.")
        return (
            self.x + self.vx_mps * horizon_seconds,
            self.y + self.vy_mps * horizon_seconds,
        )


@dataclass
class ObstacleTracker:
    """Greedy gated association with velocity smoothing and brief track memory."""

    association_distance_m: float = 4.0
    max_missed_frames: int = 3
    velocity_smoothing: float = 0.25
    max_obstacle_speed_mps: float = 45.0
    _tracks: list[ObstacleTrack] = field(default_factory=list, init=False, repr=False)
    _next_track_id: int = 1

    def __post_init__(self) -> None:
        if not math.isfinite(self.association_distance_m) or self.association_distance_m <= 0:
            raise ValueError("association_distance_m must be positive and finite")
        if isinstance(self.max_missed_frames, bool) or not isinstance(self.max_missed_frames, int) or self.max_missed_frames < 0:
            raise ValueError("max_missed_frames must be a non-negative integer")
        if not math.isfinite(self.velocity_smoothing) or not 0 < self.velocity_smoothing <= 1:
            raise ValueError("velocity_smoothing must be in (0, 1]")
        if not math.isfinite(self.max_obstacle_speed_mps) or self.max_obstacle_speed_mps <= 0:
            raise ValueError("max_obstacle_speed_mps must be positive and finite")

    @property
    def tracks(self) -> tuple[ObstacleTrack, ...]:
        """Return the currently retained tracks, nearest first by x position."""
        return tuple(sorted(self._tracks, key=lambda track: track.x))

    def reset(self) -> None:
        """Clear tracks and restart deterministic track identifiers."""
        self._tracks.clear()
        self._next_track_id = 1

    def update(
        self,
        detections: Iterable[DetectedObstacle],
        dt: float,
    ) -> tuple[ObstacleTrack, ...]:
        """Associate this frame's detections and update motion estimates."""
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be positive and finite")
        observed = tuple(detections)
        candidates = []
        for track_index, track in enumerate(self._tracks):
            for detection_index, detection in enumerate(observed):
                distance = math.hypot(detection.x - track.x, detection.y - track.y)
                if distance <= self.association_distance_m:
                    candidates.append((distance, track_index, detection_index))
        candidates.sort()

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        for _, track_index, detection_index in candidates:
            if track_index in matched_tracks or detection_index in matched_detections:
                continue
            track = self._tracks[track_index]
            detection = observed[detection_index]
            measured_vx = (detection.x - track.x) / dt
            measured_vy = (detection.y - track.y) / dt
            speed = math.hypot(measured_vx, measured_vy)
            if speed > self.max_obstacle_speed_mps:
                scale = self.max_obstacle_speed_mps / speed
                measured_vx *= scale
                measured_vy *= scale
            alpha = self.velocity_smoothing
            track.vx_mps += alpha * (measured_vx - track.vx_mps)
            track.vy_mps += alpha * (measured_vy - track.vy_mps)
            track.x = detection.x
            track.y = detection.y
            track.radius = detection.radius
            track.confidence = detection.confidence
            track.age_frames += 1
            track.missed_frames = 0
            matched_tracks.add(track_index)
            matched_detections.add(detection_index)

        survivors = []
        for index, track in enumerate(self._tracks):
            if index not in matched_tracks:
                track.x += track.vx_mps * dt
                track.y += track.vy_mps * dt
                track.missed_frames += 1
                track.confidence *= 0.75
            if track.missed_frames <= self.max_missed_frames:
                survivors.append(track)
        self._tracks = survivors

        for index, detection in enumerate(observed):
            if index in matched_detections:
                continue
            self._tracks.append(
                ObstacleTrack(
                    track_id=self._next_track_id,
                    x=detection.x,
                    y=detection.y,
                    radius=detection.radius,
                    confidence=detection.confidence,
                )
            )
            self._next_track_id += 1

        return self.tracks
