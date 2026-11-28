"""Core package for the autonomous driving simulation research project."""

from autodrive_sim.config import ExperimentConfig, SimulationConfig
from autodrive_sim.controllers import (
    ControlCommand,
    LaneFollowingController,
    ObstacleAvoidanceController,
)
from autodrive_sim.metrics import EvaluationMetrics
from autodrive_sim.perception import DetectedObstacle, ObstaclePerception
from autodrive_sim.tracking import ObstacleTrack, ObstacleTracker
from autodrive_sim.sensors import RangeScan, RangeSensor
from autodrive_sim.simulator.road import Road
from autodrive_sim.simulator.simulation import Obstacle, Simulation
from autodrive_sim.simulator.vehicle import Vehicle
from autodrive_sim.telemetry import TelemetryRecorder, TelemetrySample

__all__ = [
    "ControlCommand",
    "EvaluationMetrics",
    "DetectedObstacle",
    "ObstaclePerception",
    "ObstacleTrack",
    "ObstacleTracker",
    "ExperimentConfig",
    "LaneFollowingController",
    "Obstacle",
    "ObstacleAvoidanceController",
    "Road",
    "RangeScan",
    "RangeSensor",
    "Simulation",
    "SimulationConfig",
    "TelemetryRecorder",
    "TelemetrySample",
    "Vehicle",
]
