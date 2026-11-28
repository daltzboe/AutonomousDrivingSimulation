"""Tests for temporal obstacle tracking and motion prediction."""
import unittest

from autodrive_sim.perception import DetectedObstacle
from autodrive_sim.tracking import ObstacleTracker


def detection(x, y=0.0, confidence=0.9):
    return DetectedObstacle(
        x=x, y=y, radius=0.5, range_m=(x * x + y * y) ** 0.5,
        bearing_rad=0.0, confidence=confidence,
    )


class ObstacleTrackerTests(unittest.TestCase):
    def test_creates_track_and_predicts_constant_velocity(self):
        tracker = ObstacleTracker(velocity_smoothing=1.0)
        first = tracker.update((detection(10.0),), dt=0.1)[0]
        self.assertEqual(first.track_id, 1)
        tracker.update((detection(11.0),), dt=0.1)
        track = tracker.tracks[0]
        self.assertAlmostEqual(track.vx_mps, 10.0)
        self.assertAlmostEqual(track.predict(2.0)[0], 31.0)

    def test_associates_same_obstacle_across_frames(self):
        tracker = ObstacleTracker()
        first = tracker.update((detection(10.0),), dt=0.1)[0]
        second = tracker.update((detection(10.2),), dt=0.1)[0]
        self.assertEqual(first.track_id, second.track_id)
        self.assertEqual(second.age_frames, 2)

    def test_bridges_short_missed_detection(self):
        tracker = ObstacleTracker(max_missed_frames=2)
        tracker.update((detection(10.0),), dt=0.1)
        retained = tracker.update((), dt=0.1)
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].missed_frames, 1)
        tracker.update((), dt=0.1)
        self.assertEqual(len(tracker.tracks), 1)
        tracker.update((), dt=0.1)
        self.assertEqual(len(tracker.tracks), 0)

    def test_separates_objects_outside_association_gate(self):
        tracker = ObstacleTracker(association_distance_m=1.0)
        tracker.update((detection(5.0),), dt=0.1)
        tracks = tracker.update((detection(15.0),), dt=0.1)
        self.assertEqual(len(tracks), 2)
        self.assertNotEqual(tracks[0].track_id, tracks[1].track_id)

    def test_rejects_invalid_prediction_horizon_and_timestep(self):
        tracker = ObstacleTracker()
        track = tracker.update((detection(5.0),), dt=0.1)[0]
        with self.assertRaises(ValueError):
            track.predict(-1)
        with self.assertRaises(ValueError):
            tracker.update((), dt=0)


if __name__ == "__main__":
    unittest.main()
