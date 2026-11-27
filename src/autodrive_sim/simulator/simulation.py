"""Episode orchestration for the lightweight autonomous-driving simulator."""

from dataclasses import dataclass, field
import math

from autodrive_sim.controllers import (
    ControlCommand,
    IntelligentDrivingController,
    LaneFollowingController,
    ObstacleAvoidanceController,
    SteeringObstacleAvoidanceController,
)
from autodrive_sim.metrics import EvaluationMetrics
from autodrive_sim.telemetry import TelemetryRecorder
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.vehicle import Vehicle


@dataclass(frozen=True)
class Obstacle:
    """A circular stationary obstacle in world coordinates."""

    x: float
    y: float
    radius: float = 0.35

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.x, self.y, self.radius)):
            raise ValueError("Obstacle values must be finite.")
        if self.radius <= 0:
            raise ValueError("Obstacle radius must be positive.")


@dataclass
class Simulation:
    """Run a repeatable vehicle episode on a deterministic test road."""

    road: Road = field(default_factory=Road)
    vehicle: Vehicle = field(default_factory=Vehicle)
    controller: LaneFollowingController | ObstacleAvoidanceController | SteeringObstacleAvoidanceController | IntelligentDrivingController = field(
        default_factory=LaneFollowingController
    )
    obstacles: tuple[Obstacle, ...] = field(default_factory=tuple)
    vehicle_radius: float = 0.8
    dt: float = 0.05
    metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    recorder: TelemetryRecorder = field(default_factory=TelemetryRecorder)
    elapsed_seconds: float = 0.0
    collision: bool = False
    completed: bool = False
    last_command: ControlCommand = field(default_factory=ControlCommand)
    _hit_obstacles: set[int] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        if not math.isfinite(self.dt) or self.dt <= 0:
            raise ValueError("Simulation time step must be positive and finite.")
        if not math.isfinite(self.vehicle_radius) or self.vehicle_radius <= 0:
            raise ValueError("Vehicle radius must be positive and finite.")

    def reset(self) -> None:
        """Reset the episode to its initial state and clear all measurements."""
        self.vehicle = Vehicle(y=self.road.center_y(0.0))
        self.metrics = EvaluationMetrics()
        self.recorder.clear()
        self.elapsed_seconds = 0.0
        self.collision = False
        self.completed = False
        self.last_command = ControlCommand()
        self._hit_obstacles.clear()

    def step(self, command: ControlCommand | None = None) -> None:
        """Advance one fixed simulation step using AI or supplied manual input."""
        if self.completed:
            return
        selected_command = (
            command if command is not None
            else (
                self.controller.control(self.vehicle, self.road, self.obstacles)
                if isinstance(
                    self.controller,
                    (ObstacleAvoidanceController, SteeringObstacleAvoidanceController, IntelligentDrivingController),
                )
                else self.controller.control(self.vehicle, self.road)
            )
        )
        previous_x = self.vehicle.x
        self.vehicle.step(
            throttle=selected_command.throttle,
            brake=selected_command.brake,
            steering=selected_command.steering,
            dt=self.dt,
        )
        self.last_command = selected_command
        self.elapsed_seconds += self.dt
        self.recorder.record(
            self.elapsed_seconds, self.vehicle, selected_command, self.road
        )

        distance = max(0.0, self.vehicle.x - previous_x)
        self.metrics.add_distance(distance)
        deviation = self.road.lane_deviation(self.vehicle.x, self.vehicle.y)
        self.metrics.add_lane_deviation(deviation)

        for index, obstacle in enumerate(self.obstacles):
            separation = math.hypot(
                self.vehicle.x - obstacle.x, self.vehicle.y - obstacle.y
            )
            if (
                index not in self._hit_obstacles
                and separation <= self.vehicle_radius + obstacle.radius
            ):
                self._hit_obstacles.add(index)
                self.metrics.add_collision()
                self.collision = True

        self.metrics.set_route_progress(
            min(max(self.vehicle.x, 0.0), self.road.route_length_m),
            self.road.route_length_m,
        )
        if self.vehicle.x >= self.road.route_length_m:
            self.completed = True

    @property
    def route_completion_pct(self) -> float:
        """Current route progress as a percentage."""
        return min(
            100.0,
            100.0 * self.vehicle.x / self.road.route_length_m,
        )

    def summary(self) -> dict[str, float | int | None]:
        """Return the accumulated evaluation metrics."""
        return self.metrics.summary()
