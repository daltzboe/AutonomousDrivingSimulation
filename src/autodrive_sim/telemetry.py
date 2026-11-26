"""Structured telemetry recording for repeatable simulation episodes."""

from dataclasses import asdict, dataclass
import csv
from pathlib import Path

from autodrive_sim.controllers import ControlCommand
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.vehicle import Vehicle


@dataclass(frozen=True)
class TelemetrySample:
    """One timestamped vehicle state and control observation."""

    time_s: float
    x_m: float
    y_m: float
    yaw_rad: float
    speed_mps: float
    throttle: float
    brake: float
    steering: float
    lane_deviation_m: float
    road_center_y_m: float


@dataclass
class TelemetryRecorder:
    """Collect episode samples and export them as a portable CSV file."""

    samples: list[TelemetrySample]

    def __init__(self) -> None:
        self.samples = []

    def record(
        self,
        time_s: float,
        vehicle: Vehicle,
        command: ControlCommand,
        road: Road,
    ) -> None:
        """Capture the current state after a simulation step."""
        self.samples.append(
            TelemetrySample(
                time_s=time_s,
                x_m=vehicle.x,
                y_m=vehicle.y,
                yaw_rad=vehicle.yaw,
                speed_mps=vehicle.speed,
                throttle=command.throttle,
                brake=command.brake,
                steering=command.steering,
                lane_deviation_m=road.lane_deviation(vehicle.x, vehicle.y),
                road_center_y_m=road.center_y(vehicle.x),
            )
        )

    def clear(self) -> None:
        """Discard samples before starting a fresh episode."""
        self.samples.clear()

    def write_csv(self, path: str | Path) -> Path:
        """Write samples to CSV and return the resulting path."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(TelemetrySample.__dataclass_fields__)
        with destination.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(asdict(sample) for sample in self.samples)
        return destination
