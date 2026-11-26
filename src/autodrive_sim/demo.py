"""Interactive Pygame demo for the lightweight autonomous-driving simulator.

Run with: python -m autodrive_sim.demo
"""

from __future__ import annotations

import math


def main() -> None:
    """Launch the interactive top-down driving demo."""
    try:
        import pygame
    except ImportError as exc:
        raise SystemExit(
            "Pygame is required for the visual demo. Install it with "
            'python -m pip install -e ".[demo]" and try again.'
        ) from exc

    from autodrive_sim.controllers import ControlCommand
    from autodrive_sim.simulator.road import Road
    from autodrive_sim.simulator.simulation import Obstacle, Simulation

    pygame.init()
    width, height = 1100, 680
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Autonomous Driving Simulation | UTSA CS")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)
    small_font = pygame.font.SysFont("consolas", 14)
    title_font = pygame.font.SysFont("consolas", 22, bold=True)

    road = Road()
    obstacles = (
        Obstacle(130.0, road.center_y(130.0) + 1.4, 0.28),
        Obstacle(290.0, road.center_y(290.0) - 1.4, 0.28),
    )
    simulation = Simulation(road=road, obstacles=obstacles)
    autopilot = True
    paused = False
    running = True
    accumulator = 0.0
    pixels_per_meter = 17.0
    car_screen_x = width * 0.34
    car_screen_y = height * 0.55

    def world_to_screen(world_x: float, world_y: float) -> tuple[int, int]:
        sx = car_screen_x + (world_x - simulation.vehicle.x) * pixels_per_meter
        sy = car_screen_y - (world_y - simulation.vehicle.y) * pixels_per_meter
        return int(sx), int(sy)

    def draw_text(text: str, x: int, y: int, color=(235, 240, 245), target=screen, face=font):
        target.blit(face.render(text, True, color), (x, y))

    while running:
        frame_seconds = min(clock.tick(60) / 1000.0, 0.1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_a:
                    autopilot = not autopilot
                elif event.key == pygame.K_r:
                    simulation.reset()
                    accumulator = 0.0

        keys = pygame.key.get_pressed()
        if not paused and not simulation.completed:
            accumulator += frame_seconds
            while accumulator >= simulation.dt:
                if autopilot:
                    simulation.step()
                else:
                    steering = float(bool(keys[pygame.K_RIGHT])) - float(
                        bool(keys[pygame.K_LEFT])
                    )
                    command = ControlCommand(
                        throttle=0.75 if keys[pygame.K_UP] else 0.0,
                        brake=0.85 if keys[pygame.K_DOWN] else 0.0,
                        steering=steering,
                    )
                    simulation.step(command)
                accumulator -= simulation.dt

        screen.fill((17, 24, 32))
        # Draw a moving top-down view of the road and its lane markings.
        x_start = simulation.vehicle.x - 8.0
        x_end = simulation.vehicle.x + 48.0
        sample_count = 70
        left_edge = []
        right_edge = []
        center_points = []
        for index in range(sample_count + 1):
            world_x = x_start + (x_end - x_start) * index / sample_count
            center_y = road.center_y(world_x)
            left_edge.append(
                world_to_screen(world_x, center_y + road.lane_width / 2.0)
            )
            right_edge.append(
                world_to_screen(world_x, center_y - road.lane_width / 2.0)
            )
            center_points.append(world_to_screen(world_x, center_y))

        pygame.draw.polygon(screen, (65, 72, 82), left_edge + right_edge[::-1])
        pygame.draw.lines(screen, (235, 190, 65), False, left_edge, 3)
        pygame.draw.lines(screen, (235, 190, 65), False, right_edge, 3)
        # Dashed center line.
        for index in range(0, sample_count, 4):
            pygame.draw.line(
                screen, (220, 224, 226),
                center_points[index], center_points[min(index + 2, sample_count)], 2
            )

        for obstacle in obstacles:
            point = world_to_screen(obstacle.x, obstacle.y)
            radius = max(4, int(obstacle.radius * pixels_per_meter))
            pygame.draw.circle(screen, (225, 92, 70), point, radius)
            pygame.draw.circle(screen, (255, 220, 200), point, radius, 2)

        # Vehicle body, rotated to match its world heading.
        car_surface = pygame.Surface((46, 25), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, (45, 165, 225), (0, 0, 46, 25), border_radius=6)
        pygame.draw.rect(car_surface, (220, 242, 252), (28, 4, 12, 17), border_radius=3)
        rotated_car = pygame.transform.rotate(
            car_surface, -math.degrees(simulation.vehicle.yaw)
        )
        car_rect = rotated_car.get_rect(center=(int(car_screen_x), int(car_screen_y)))
        screen.blit(rotated_car, car_rect)

        # HUD panel.
        panel = pygame.Surface((390, 188), pygame.SRCALPHA)
        panel.fill((8, 14, 22, 220))
        screen.blit(panel, (18, 18))
        draw_text("UTSA | AUTONOMOUS DRIVING", 32, 30, (90, 195, 245), screen, title_font)
        mode = "AUTOPILOT" if autopilot else "MANUAL"
        draw_text(f"MODE       {mode}", 32, 68, (120, 225, 160))
        draw_text(f"SPEED      {simulation.vehicle.speed * 3.6:5.1f} km/h", 32, 94)
        lane_error = road.lane_deviation(simulation.vehicle.x, simulation.vehicle.y)
        draw_text(f"LANE ERROR {lane_error:5.2f} m", 32, 120)
        draw_text(f"PROGRESS   {simulation.route_completion_pct:5.1f} %", 32, 146)
        draw_text(f"COLLISIONS {simulation.metrics.collision_events}", 32, 172)

        status = "PAUSED" if paused else (
            "ROUTE COMPLETE" if simulation.completed else "SIMULATION RUNNING"
        )
        status_color = (120, 225, 160) if not simulation.collision else (255, 130, 110)
        draw_text(status, 18, height - 62, status_color)
        draw_text(
            "A: Autopilot  |  Arrows: Manual drive  |  SPACE: Pause  |  R: Reset  |  ESC: Quit",
            18, height - 34, (190, 200, 210), screen, small_font
        )
        if simulation.collision:
            draw_text("OBSTACLE CONTACT DETECTED", width - 340, 28, (255, 125, 105))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
