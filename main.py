# main.py

import sys
import pygame

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    GRID_ORIGIN_X, GRID_ORIGIN_Y, GRID_WIDTH, GRID_HEIGHT,
    FPS, MAX_AGENT_COUNT,
)
from config import (
    DEFAULT_STEPS_PER_FRAME, MAX_STEPS_DEFAULT, MAX_SIMULATIONS_DEFAULT
)
from config import GRID_ROWS, GRID_COLS, CELL_SIZE

from simulation import SimulationState
import ui


def main():
    pygame.init()

    LOGICAL_WIDTH = WINDOW_WIDTH
    LOGICAL_HEIGHT = WINDOW_HEIGHT

    windowed_size = (LOGICAL_WIDTH, LOGICAL_HEIGHT)
    screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
    pygame.display.set_caption("Monte Carlo Pathfinding - Pygame (Multi-agent)")

    canvas = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 20)
    font_title = pygame.font.SysFont(None, 24, bold=True)

    sim = SimulationState()

    running = True
    cost_minus_rect = pygame.Rect(0, 0, 0, 0)
    cost_plus_rect = pygame.Rect(0, 0, 0, 0)

    while running:
        clock.tick(FPS)

        # update simulasi
        sim.step_frame()

        # gambar
        ui.draw_grid(canvas, sim, CELL_SIZE)
        ui.draw_paths(canvas, sim, CELL_SIZE)
        cost_minus_rect, cost_plus_rect = ui.draw_sidebar(canvas, sim, font, font_title)

        # scale canvas ke window
        display_size = screen.get_size()
        scaled = pygame.transform.scale(canvas, display_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    if not sim.simulation_done:
                        sim.paused = not sim.paused

                elif event.key == pygame.K_r:
                    sim.reset_simulation()

                elif event.key == pygame.K_z:
                    if sim.agent_count > 1:
                        sim.agent_count -= 1
                        sim.reset_simulation()
                elif event.key == pygame.K_x:
                    if sim.agent_count < MAX_AGENT_COUNT:
                        sim.agent_count += 1
                        sim.reset_simulation()

                elif event.key == pygame.K_c:
                    if sim.steps_per_frame > 1:
                        sim.steps_per_frame -= 1
                elif event.key == pygame.K_v:
                    if sim.steps_per_frame < 20:
                        sim.steps_per_frame += 1

                elif event.key == pygame.K_f:
                    current_size = screen.get_size()
                    if hasattr(pygame.display, "get_desktop_sizes"):
                        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
                    else:
                        info = pygame.display.Info()
                        desktop_w, desktop_h = info.current_w, info.current_h
                    desktop_size = (desktop_w, desktop_h)

                    if (abs(current_size[0] - windowed_size[0]) < 10 and
                        abs(current_size[1] - windowed_size[1]) < 10):
                        screen = pygame.display.set_mode(desktop_size, pygame.RESIZABLE)
                    else:
                        screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)

                elif event.key == pygame.K_LEFTBRACKET:
                    if sim.max_simulations > sim.agent_count:
                        sim.max_simulations = max(sim.max_simulations - 50, sim.agent_count)

                elif event.key == pygame.K_RIGHTBRACKET:
                    sim.max_simulations += 50

                elif event.key == pygame.K_COMMA:
                    if sim.max_steps_per_walk > 10:
                        sim.max_steps_per_walk -= 10

                elif event.key == pygame.K_PERIOD:
                    sim.max_steps_per_walk += 10

                elif event.key == pygame.K_1:
                    sim.cursor_mode = "obstacle"
                elif event.key == pygame.K_2:
                    sim.cursor_mode = "cost"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                display_w, display_h = screen.get_size()

                scale_x = LOGICAL_WIDTH / display_w
                scale_y = LOGICAL_HEIGHT / display_h

                mx_log = int(mx * scale_x)
                my_log = int(my * scale_y)

                # klik tombol cost +/- di sidebar
                if cost_minus_rect.collidepoint(mx_log, my_log):
                    sim.current_cost_value = max(0, sim.current_cost_value - 1)
                    continue
                if cost_plus_rect.collidepoint(mx_log, my_log):
                    sim.current_cost_value = min(9, sim.current_cost_value + 1)
                    continue

                # klik di grid
                if (GRID_ORIGIN_X <= mx_log < GRID_ORIGIN_X + GRID_WIDTH and
                    GRID_ORIGIN_Y <= my_log < GRID_ORIGIN_Y + GRID_HEIGHT):
                    c = (mx_log - GRID_ORIGIN_X) // CELL_SIZE
                    r = (my_log - GRID_ORIGIN_Y) // CELL_SIZE
                    sim.handle_grid_click(r, c, event.button)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
