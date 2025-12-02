# ui.py

import pygame

from config import (
    GRID_ROWS, GRID_COLS, GRID_ORIGIN_X, GRID_ORIGIN_Y, GRID_WIDTH, GRID_HEIGHT,
    SIDEBAR_WIDTH, PANEL_HEIGHT,
    WHITE, BLACK, GRAY, GREEN, RED, BLUE,
    BG, PANEL_BG, PANEL_BORDER,
)

from simulation import SimulationState


def draw_cost_dots(surface, r, c, cost, cell_size):
    if cost <= 0:
        return
    cost = min(cost, 9)

    cx = GRID_ORIGIN_X + c * cell_size + cell_size // 2
    cy = GRID_ORIGIN_Y + r * cell_size + cell_size // 2

    offsets = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0), (0,  0), (1,  0),
        (-1,  1), (0,  1), (1,  1),
    ]

    step = cell_size // 4
    radius = max(2, cell_size // 10)

    for i in range(cost):
        ox, oy = offsets[i]
        x = cx + ox * step
        y = cy + oy * step
        pygame.draw.circle(surface, BLACK, (x, y), radius)


def draw_grid(surface, sim: SimulationState, cell_size: int):
    surface.fill(BG)

    # panel sidebar
    panel_x = GRID_ORIGIN_X + GRID_WIDTH + GRID_ORIGIN_X
    pygame.draw.rect(
        surface,
        PANEL_BG,
        pygame.Rect(panel_x, GRID_ORIGIN_Y, SIDEBAR_WIDTH - GRID_ORIGIN_X, PANEL_HEIGHT)
    )
    pygame.draw.rect(
        surface,
        PANEL_BORDER,
        pygame.Rect(panel_x, GRID_ORIGIN_Y, SIDEBAR_WIDTH - GRID_ORIGIN_X, PANEL_HEIGHT),
        2
    )

    # separator vertical
    pygame.draw.line(
        surface,
        PANEL_BORDER,
        (GRID_ORIGIN_X + GRID_WIDTH + GRID_ORIGIN_X // 2, GRID_ORIGIN_Y),
        (GRID_ORIGIN_X + GRID_WIDTH + GRID_ORIGIN_X // 2, GRID_ORIGIN_Y + PANEL_HEIGHT),
        2
    )

    # cari max untuk heatmap
    max_count = 0
    for row in sim.visit_counts:
        row_max = max(row)
        if row_max > max_count:
            max_count = row_max

    # grid cells
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = GRID_ORIGIN_X + c * cell_size
            y = GRID_ORIGIN_Y + r * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)

            if sim.grid[r][c] == 1:
                pygame.draw.rect(surface, BLACK, rect)
            else:
                if max_count > 0 and sim.visit_counts[r][c] > 0:
                    ratio = sim.visit_counts[r][c] / max_count
                    red = 255
                    gb = int(255 * (1 - ratio))
                    color = (red, gb, gb)
                else:
                    color = WHITE

                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, GRAY, rect, 1)

                if sim.cell_costs[r][c] > 0:
                    draw_cost_dots(surface, r, c, sim.cell_costs[r][c], cell_size)

    # start
    sx = GRID_ORIGIN_X + sim.start[1] * cell_size
    sy = GRID_ORIGIN_Y + sim.start[0] * cell_size
    pygame.draw.rect(surface, GREEN, (sx, sy, cell_size, cell_size))

    # goal
    gx = GRID_ORIGIN_X + sim.goal[1] * cell_size
    gy = GRID_ORIGIN_Y + sim.goal[0] * cell_size
    pygame.draw.rect(surface, RED, (gx, gy, cell_size, cell_size))


def draw_paths(surface, sim: SimulationState, cell_size: int):
    if sim.best_path is not None and len(sim.best_path) >= 2:
        draw_path(surface, sim.best_path, GREEN, cell_size, width=4)

    for agent in sim.agents:
        if agent.active and len(agent.path) >= 2:
            draw_path(surface, agent.path, BLUE, cell_size, width=2)


def draw_path(surface, path, color, cell_size, width=3):
    pts = []
    for (r, c) in path:
        x = GRID_ORIGIN_X + c * cell_size + cell_size // 2
        y = GRID_ORIGIN_Y + r * cell_size + cell_size // 2
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(surface, color, False, pts, width)


def draw_sidebar(surface, sim: SimulationState, font, font_title):
    """Gambar sidebar dan kembalikan rect tombol cost_minus, cost_plus."""
    panel_x = GRID_ORIGIN_X + GRID_WIDTH + GRID_ORIGIN_X + 10
    y = GRID_ORIGIN_Y + 10
    line_h = 16

    # Judul
    title = font_title.render("Monte Carlo Pathfinding", True, (255, 255, 255))
    surface.blit(title, (panel_x, y))
    y += line_h + 6

    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Cost control (pakai tombol +/-) =====
    label = font.render("Cost value (0-9) untuk mode Cost:", True, (230, 230, 230))
    surface.blit(label, (panel_x, y))
    y += line_h

    minus_w = 24
    plus_w = 24
    box_h = 22

    cost_minus_rect = pygame.Rect(panel_x, y, minus_w, box_h)
    value_rect       = pygame.Rect(panel_x + minus_w + 4, y, 40, box_h)
    cost_plus_rect  = pygame.Rect(panel_x + minus_w + 4 + 40 + 4, y, plus_w, box_h)

    # minus
    pygame.draw.rect(surface, (100, 80, 80), cost_minus_rect, border_radius=3)
    pygame.draw.rect(surface, (220, 210, 210), cost_minus_rect, 1, border_radius=3)
    minus_text = font.render("-", True, (255, 255, 255))
    surface.blit(minus_text, minus_text.get_rect(center=cost_minus_rect.center))

    # value
    pygame.draw.rect(surface, (80, 80, 110), value_rect, border_radius=3)
    pygame.draw.rect(surface, (200, 200, 230), value_rect, 1, border_radius=3)
    val_text = font.render(str(sim.current_cost_value), True, (255, 255, 255))
    surface.blit(val_text, val_text.get_rect(center=value_rect.center))

    # plus
    pygame.draw.rect(surface, (80, 120, 80), cost_plus_rect, border_radius=3)
    pygame.draw.rect(surface, (210, 230, 210), cost_plus_rect, 1, border_radius=3)
    plus_text = font.render("+", True, (255, 255, 255))
    surface.blit(plus_text, plus_text.get_rect(center=cost_plus_rect.center))

    y += box_h + 6

    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Statistik =====
    best_len = len(sim.best_path) if sim.best_path is not None else "-"
    best_cost_str = f"{sim.best_path_cost:.2f}" if sim.best_path_cost is not None else "-"
    success_rate = (sim.success_count / sim.sim_count * 100) if sim.sim_count > 0 else 0.0
    avg_len = (sim.total_success_length / sim.success_count) if sim.success_count > 0 else 0
    avg_cost = (sim.total_success_cost / sim.success_count) if sim.success_count > 0 else 0.0

    stats_lines = [
        "[Statistik]",
        f"Simulasi: {sim.sim_count}/{sim.max_simulations}",
        f"Agen      : {sim.agent_count}",
        f"Steps/frame: {sim.steps_per_frame}",
        f"Max steps/episode: {sim.max_steps_per_walk}",
        f"Best length: {best_len}",
        f"Best cost  : {best_cost_str}",
        f"Sukses: {sim.success_count} ({success_rate:.1f}%)",
    ]

    if sim.success_count > 0:
        stats_lines.append(f"Avg len : {avg_len:.1f}")
        stats_lines.append(f"Min/Max len: {sim.min_success_length}/{sim.max_success_length}")
        stats_lines.append(f"Avg cost: {avg_cost:.2f}")
        stats_lines.append(f"Min/Max cost: {sim.min_success_cost:.2f}/{sim.max_success_cost:.2f}")
    else:
        stats_lines.append("Belum ada jalur sukses.")

    for text in stats_lines:
        surf = font.render(text, True, (230, 230, 230))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Status =====
    if sim.simulation_done:
        status_text = "DONE"
    elif not sim.paused and not sim.simulation_done:
        status_text = "RUNNING"
    elif sim.paused and sim.sim_count > 0:
        status_text = "PAUSED"
    else:
        status_text = "READY"

    surf = font.render(f"Status: {status_text}", True, (255, 255, 0))
    surface.blit(surf, (panel_x, y))
    y += line_h

    if sim.cursor_mode == "obstacle":
        cursor_label = "Obstacle (edit rintangan)"
    else:
        cursor_label = f"Cost (nilai {sim.current_cost_value})"
    surf = font.render(f"Cursor: {cursor_label}", True, (180, 220, 255))
    surface.blit(surf, (panel_x, y))
    y += line_h

    if sim.paused and not sim.simulation_done:
        hint = "SPACE: Start / Pause"
        surf = font.render(hint, True, (180, 255, 180))
        surface.blit(surf, (panel_x, y))
        y += line_h

    if sim.simulation_done:
        done_msg = "Simulasi selesai. Tekan R untuk reset."
        surf = font.render(done_msg, True, (255, 200, 0))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Kontrol =====
    controls = [
        "[Kontrol]",
        "SPACE : Start / Pause",
        "R     : Reset simulasi",
        "Z / X : Agen - / +",
        "C / V : Steps/frame - / +",
        "[ / ] : Max simulations - / +",
        ", / . : Max steps/episode - / +",
        "1     : Cursor mode Obstacle",
        "2     : Cursor mode Cost",
        "F     : Toggle window size",
        "ESC   : Keluar",
    ]
    for text in controls:
        surf = font.render(text, True, (220, 220, 220))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Legend =====
    legend = [
        "[Mouse & Legend]",
        "Left  : Edit (sesuai mode cursor)",
        "Middle: Set START | Right: Set GOAL",
        "Putih : Jalan | Hitam : Rintangan",
        "Hijau : START | Merah : GOAL",
        "Hijau  : Best path | Biru: Jalur agen",
        "Merah pekat: sering dilalui",
        "Titik hitam: cost 1-9 (dipakai di best cost)",
    ]
    for text in legend:
        surf = font.render(text, True, (210, 210, 210))
        surface.blit(surf, (panel_x, y))
        y += line_h

    return cost_minus_rect, cost_plus_rect
