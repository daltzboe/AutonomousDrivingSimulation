"""Baseline and obstacle-aware controllers for the lightweight simulation."""

from dataclasses import dataclass, field
from enum import Enum
import math

from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.vehicle import Vehicle
from autodrive_sim.sensors import RangeSensor


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
        return self._track_target(vehicle, target_y, self.lookahead_m)

    def _track_target(
        self, vehicle: Vehicle, target_y: float, lookahead_m: float
    ) -> ControlCommand:
        """Track a target point while retaining the baseline speed controller."""
        alpha = _wrap_angle(
            math.atan2(target_y - vehicle.y, lookahead_m) - vehicle.yaw
        )
        curvature = 2.0 * math.sin(alpha) / lookahead_m
        steering_angle = math.atan(vehicle.wheelbase * curvature)
        steering = _clamp(
            self.steering_gain * steering_angle / vehicle.max_steering_angle,
            -1.0,
            1.0,
        )

        speed_error = self.target_speed_mps - vehicle.speed
        throttle = _clamp(speed_error * self.speed_gain, 0.0, 1.0)
        brake = _clamp(-speed_error * self.speed_gain, 0.0, 1.0)
        return ControlCommand(throttle=throttle, brake=brake, steering=steering)


@dataclass
class ObstacleAvoidanceController:
    """Lane-following controller with a range-sensor emergency-braking layer.

    This intentionally remains the conservative stop-only baseline so its
    results can be compared with the steering-based planner.
    """

    lane_follower: LaneFollowingController = field(default_factory=LaneFollowingController)
    sensor: RangeSensor = field(default_factory=RangeSensor)
    safety_margin_m: float = 3.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.safety_margin_m) or self.safety_margin_m < 0:
            raise ValueError("safety_margin_m must be finite and non-negative")

    def control(self, vehicle: Vehicle, road: Road, obstacles=()) -> ControlCommand:
        """Return the lane-following command, braking for a close obstacle."""
        baseline = self.lane_follower.control(vehicle, road)
        lane_obstacles = tuple(
            obstacle
            for obstacle in obstacles
            if abs(obstacle.y - road.center_y(obstacle.x))
            <= 0.8 + obstacle.radius
        )
        nearest = self.sensor.scan(vehicle, lane_obstacles).nearest_distance_m
        stopping_distance = (
            vehicle.speed * vehicle.speed / (2.0 * vehicle.max_braking)
            + self.safety_margin_m
        )
        if nearest <= stopping_distance:
            return ControlCommand(
                throttle=0.0, brake=1.0, steering=baseline.steering
            )
        return baseline


@dataclass
class SteeringObstacleAvoidanceController:
    """Plan a smooth lateral bypass around obstacles when the lane permits.

    The controller selects a collision-clear side, follows a smooth lateral
    offset around the nearest obstacle, and returns to lane center afterward.
    If neither side has enough room inside the road boundaries, it delegates
    to the conservative emergency-braking controller.
    """

    lane_follower: LaneFollowingController = field(default_factory=LaneFollowingController)
    sensor: RangeSensor = field(default_factory=RangeSensor)
    vehicle_radius_m: float = 0.8
    lateral_clearance_m: float = 0.1
    boundary_margin_m: float = 0.1
    detection_range_m: float = 30.0

    def __post_init__(self) -> None:
        values = (
            self.vehicle_radius_m,
            self.lateral_clearance_m,
            self.boundary_margin_m,
            self.detection_range_m,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Avoidance settings must be finite.")
        if self.vehicle_radius_m <= 0 or self.lateral_clearance_m < 0:
            raise ValueError("Vehicle radius must be positive and clearance non-negative.")
        if self.boundary_margin_m < 0 or self.detection_range_m <= 0:
            raise ValueError("Boundary margin must be non-negative and detection range positive.")

    @staticmethod
    def _smoothstep(value: float) -> float:
        value = _clamp(value, 0.0, 1.0)
        return value * value * (3.0 - 2.0 * value)

    def _path_offset(self, x: float, obstacle_x: float, offset: float) -> float:
        lookahead = self.lane_follower.lookahead_m
        start = obstacle_x - 3.0 * lookahead
        peak_start = obstacle_x - lookahead
        peak_end = obstacle_x + 0.5 * lookahead
        end = obstacle_x + 3.0 * lookahead
        if x < start or x >= end:
            return 0.0
        if x < peak_start:
            return offset * self._smoothstep(
                (x - start) / (peak_start - start)
            )
        if x <= peak_end:
            return offset
        return offset * (
            1.0 - self._smoothstep((x - peak_end) / (end - peak_end))
        )

    def _choose_offset(
        self, obstacle, obstacles, road: Road, vehicle_y: float
    ) -> float | None:
        maximum_offset = (
            road.lane_width / 2.0
            - self.vehicle_radius_m
            - self.boundary_margin_m
        )
        required_clearance = (
            self.vehicle_radius_m + obstacle.radius + self.lateral_clearance_m
        )
        if required_clearance > maximum_offset:
            return None

        candidates = []
        for sign in (-1.0, 1.0):
            offset = sign * required_clearance
            target_y = road.center_y(obstacle.x) + offset
            if abs(target_y - obstacle.y) < required_clearance:
                continue
            blocked = any(
                other is not obstacle
                and abs(other.x - obstacle.x)
                <= self.vehicle_radius_m + other.radius + obstacle.radius
                and abs(other.y - target_y)
                < self.vehicle_radius_m + other.radius + self.lateral_clearance_m
                for other in obstacles
            )
            if not blocked:
                candidates.append(offset)

        if not candidates:
            return None
        # Prefer the side requiring the smaller lateral movement; break ties
        # consistently toward the left side of the vehicle.
        return min(
            candidates,
            key=lambda value: (
                abs(road.center_y(obstacle.x) + value - vehicle_y),
                -value,
            ),
        )

    def control(self, vehicle: Vehicle, road: Road, obstacles=()) -> ControlCommand:
        """Steer around the nearest feasible obstacle, or safely brake."""
        obstacle_list = tuple(obstacles)
        # Use tracked world positions to retain obstacle awareness while the
        # vehicle is steering. A forward-only range ray can miss an obstacle
        # during a lateral bypass and prematurely cancel the avoidance path.
        relevant = tuple(
            obstacle
            for obstacle in obstacle_list
            if -1.0 <= obstacle.x - vehicle.x <= self.detection_range_m
            and abs(obstacle.y - road.center_y(obstacle.x))
            <= road.lane_width / 2.0 + obstacle.radius
        )
        if not relevant:
            return self.lane_follower.control(vehicle, road)

        obstacle = min(relevant, key=lambda item: item.x - vehicle.x)
        offset = self._choose_offset(obstacle, relevant, road, vehicle.y)
        if offset is None:
            return ObstacleAvoidanceController(
                lane_follower=self.lane_follower, sensor=self.sensor
            ).control(vehicle, road, relevant)

        preview_x = vehicle.x + self.lane_follower.lookahead_m
        target_y = road.center_y(preview_x) + self._path_offset(
            preview_x, obstacle.x, offset
        )
        return self.lane_follower._track_target(
            vehicle, target_y, self.lane_follower.lookahead_m
        )



class DrivingMode(str, Enum):
    """High-level autonomous-driving states exposed for telemetry and tests."""

    CRUISE = "CRUISE"
    APPROACH = "APPROACH"
    AVOID = "AVOID"
    BRAKE = "BRAKE"


@dataclass
class IntelligentDrivingController:
    """Coordinate obstacle avoidance with speed decisions.

    The existing steering controller remains responsible for path geometry.
    This layer decides whether to cruise, approach, avoid, or brake, and
    reduces speed as a relevant obstacle gets closer. It is a deterministic
    rule-based controller, not a trained machine-learning policy.
    """

    steering_controller: SteeringObstacleAvoidanceController = field(
        default_factory=SteeringObstacleAvoidanceController
    )
    target_speed_mps: float = 10.0
    crawl_speed_mps: float = 5.0
    approach_distance_m: float = 45.0
    speed_gain: float = 0.35
    mode: DrivingMode = field(default=DrivingMode.CRUISE, init=False)

    def __post_init__(self) -> None:
        values = (
            self.target_speed_mps,
            self.crawl_speed_mps,
            self.approach_distance_m,
            self.speed_gain,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Decision-controller settings must be finite.")
        if self.target_speed_mps <= 0 or self.crawl_speed_mps < 0:
            raise ValueError("Target speed must be positive and crawl speed non-negative.")
        if self.crawl_speed_mps > self.target_speed_mps:
            raise ValueError("Crawl speed cannot exceed target speed.")
        if self.approach_distance_m <= 0 or self.speed_gain <= 0:
            raise ValueError("Approach distance and speed gain must be positive.")

    def control(self, vehicle: Vehicle, road: Road, obstacles=()) -> ControlCommand:
        """Select a driving mode and produce a safe normalized control command."""
        obstacle_list = tuple(
            obstacle for obstacle in obstacles
            if obstacle.x >= vehicle.x - 1.0
            and abs(obstacle.y - road.center_y(obstacle.x))
            <= road.lane_width / 2.0 + obstacle.radius
        )
        nearest = min(
            obstacle_list,
            key=lambda obstacle: obstacle.x - vehicle.x,
            default=None,
        )
        base = self.steering_controller.control(vehicle, road, obstacle_list)

        if nearest is None:
            self.mode = DrivingMode.CRUISE
            return base

        distance = max(0.0, nearest.x - vehicle.x)
        if distance > self.approach_distance_m:
            self.mode = DrivingMode.CRUISE
            return base

        if base.brake >= 0.5:
            self.mode = DrivingMode.BRAKE
            return base

        # Classify avoidance from the planner's selected path, not only the
        # instantaneous steering delta. During the early smooth transition,
        # the planned lateral offset can be meaningful before steering differs
        # substantially from normal lane-following (especially on curved roads).
        preview_x = vehicle.x + self.steering_controller.lane_follower.lookahead_m
        avoidance_offset = self.steering_controller._choose_offset(
            nearest, obstacle_list, road, vehicle.y
        )
        planned_offset = (
            0.0
            if avoidance_offset is None
            else self.steering_controller._path_offset(
                preview_x, nearest.x, avoidance_offset
            )
        )
        if abs(planned_offset) > 1e-6:
            self.mode = DrivingMode.AVOID
        else:
            self.mode = DrivingMode.APPROACH

        # Reduce the target speed progressively as the obstacle gets closer.
        # The path planner still chooses the steering direction; this layer
        # only adjusts longitudinal control.
        progress = _clamp(distance / self.approach_distance_m, 0.0, 1.0)
        desired_speed = self.crawl_speed_mps + (
            self.target_speed_mps - self.crawl_speed_mps
        ) * progress
        speed_error = desired_speed - vehicle.speed
        throttle = _clamp(speed_error * self.speed_gain, 0.0, 1.0)
        brake = _clamp(-speed_error * self.speed_gain, 0.0, 1.0)
        return ControlCommand(
            throttle=throttle,
            brake=brake,
            steering=base.steering,
        )
