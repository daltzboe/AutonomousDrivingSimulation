"""Headless rendering smoke test for the interactive demo."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError:
    pygame = None

from autodrive_sim.demo import main


@unittest.skipIf(pygame is None, "Pygame demo extra is not installed")
class DemoSmokeTests(unittest.TestCase):
    def test_demo_renders_a_frame_and_closes_cleanly(self) -> None:
        quit_event = pygame.event.Event(pygame.QUIT)
        with patch("pygame.event.get", return_value=[quit_event]):
            main()


if __name__ == "__main__":
    unittest.main()
