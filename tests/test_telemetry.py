"""Tests for structured simulation telemetry recording."""

import csv
from pathlib import Path
import tempfile
import unittest

from autodrive_sim.simulator.simulation import Simulation


class TelemetryRecorderTests(unittest.TestCase):
    def test_simulation_records_one_sample_per_step(self) -> None:
        simulation = Simulation()
        simulation.step()
        simulation.step()
        self.assertEqual(len(simulation.recorder.samples), 2)
        sample = simulation.recorder.samples[-1]
        self.assertAlmostEqual(sample.time_s, 0.1)
        self.assertGreaterEqual(sample.lane_deviation_m, 0.0)

    def test_samples_can_be_exported_to_csv(self) -> None:
        simulation = Simulation()
        simulation.step()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "episode.csv"
            written = simulation.recorder.write_csv(output)
            self.assertTrue(written.exists())
            with written.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), 1)
            self.assertIn("steering", rows[0])
            self.assertIn("lane_deviation_m", rows[0])

    def test_reset_clears_telemetry(self) -> None:
        simulation = Simulation()
        simulation.step()
        simulation.reset()
        self.assertEqual(simulation.recorder.samples, [])


if __name__ == "__main__":
    unittest.main()
