"""Typed configuration shared by simulation and evaluation components."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Settings for a CARLA simulation session.

    CARLA-specific values are kept here so the rest of the project can be
    developed and tested before the simulator is installed.
    """

    host: str = "127.0.0.1"
    port: int = 2000
    timeout_seconds: float = 10.0
    town: str = "Town03"
    synchronous_mode: bool = True
    fixed_delta_seconds: float = 0.05
    image_width: int = 320
    image_height: int = 160
    camera_fov: float = 100.0

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.fixed_delta_seconds <= 0:
            raise ValueError("fixed_delta_seconds must be positive")
        if self.image_width <= 0 or self.image_height <= 0:
            raise ValueError("image dimensions must be positive")
        if not 0 < self.camera_fov < 180:
            raise ValueError("camera_fov must be between 0 and 180 degrees")


@dataclass(frozen=True)
class ExperimentConfig:
    """Settings that identify a repeatable controller evaluation."""

    experiment_name: str = "baseline-vs-imitation"
    route_id: str = "route-001"
    target_speed_kmh: float = 30.0
    max_episode_seconds: float = 300.0
    random_seed: int = 42

    def __post_init__(self) -> None:
        if not self.experiment_name.strip():
            raise ValueError("experiment_name must not be empty")
        if not self.route_id.strip():
            raise ValueError("route_id must not be empty")
        if self.target_speed_kmh <= 0:
            raise ValueError("target_speed_kmh must be positive")
        if self.max_episode_seconds <= 0:
            raise ValueError("max_episode_seconds must be positive")
