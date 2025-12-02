# ui.py

import pygame

from config import (
    GRID_ORIGIN_X, GRID_ORIGIN_Y,
    SIDEBAR_WIDTH,
    WHITE, BLACK, GRAY, GREEN, RED, BLUE,
    BG, PANEL_BG, PANEL_BORDER,
)

from simulation import SimulationState


# =========================================================
# Sumber tunggal semua teks sidebar (NO DUPLICATION)
# =========================================================
def build_sidebar_sections(sim: SimulationState):
    """Sumber tunggal semua teks sidebar."""
    line_h = 16

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
        f"Map size: {sim.rows} x {sim.cols}",
    ]
    if sim.success_count > 0:
        stats_lines += [
            f"Avg len : {avg_len:.1f}",
            f"Min/Max len: {sim.min_success_length}/{sim.max_success_length}",
            f"Avg cost: {avg_cost:.2f}",
            f"Min/Max cost: {sim.min_success_cost:.2f}/{sim.max_success_cost:.2f}",
        ]
    else:
        stats_lines.append("Belum ada jalur sukses.")

    # ===== Status =====
    if sim.simulation_done:
        status_text = "DONE"
    elif not sim.paused:
        status_text = "RUNNING"
    elif sim.paused and sim.sim_count > 0:
        status_text = "PAUSED"
    else:
        status_text = "READY"

    cursor_label = (
        "Obstacle (edit rintangan)"
        if sim.cursor_mode == "obstacle"
        else f"Cost (nilai {sim.current_cost_value})"
    )

    status_lines = [
        f"Status: {status_text}",
        f"Cursor: {cursor_label}",
    ]
    if sim.paused and not sim.simulation_done:
        status_lines.append("SPACE: Start / Pause")
    if sim.simulation_done:
        status_lines.append("Simulasi selesai. Tekan R untuk reset.")

    # ===== Kontrol =====
    controls_lines = [
        "[Kontrol]",
        "SPACE : Start / Pause",
        "R     : Reset simulasi",
        "Z / X : Agen - / +",
        "C / V : Steps/frame - / +",
        "[ / ] : Max simulations - / +",
        ", / . : Max steps/episode - / +",
        "N / M : Baris - / + (5..15)",
        "K / L : Kolom - / + (5..23)",
        "1     : Cursor mode Obstacle",
        "2     : Cursor mode Cost",
        "F     : Toggle window size",
        "ESC   : Keluar",
    ]

    # ===== Legend =====
    legend_lines = [
        "[Mouse & Legend]",
        "Left  : Edit (sesuai mode cursor)",
        "Middle: Set START | Right: Set GOAL",
        "Putih : Jalan | Hitam : Rintangan",
        "Hijau : START | Merah : GOAL",
        "Hijau  : Best path | Biru: Jalur agen",
        "Merah pekat: sering dilalui",
        "Titik hitam: cost 1-9 (dipakai di best cost)",
    ]

    return {
        "line_h": line_h,
        "stats": stats_lines,
        "status": status_lines,
        "controls": controls_lines,
        "legend": legend_lines,
    }


def get_sidebar_height(sim: SimulationState, font, font_title):
    """Hitung tinggi sidebar sesuai konten teks yang digambar."""
    sec = build_sidebar_sections(sim)
    line_h = sec["line_h"]
    y = GRID_ORIGIN_Y + 10

    # Judul + garis
    y += line_h + 6
    y += 6

    # Cost control area (fix)
    y += line_h
    y += 22 + 6
    y += 6

    # Statistik
    y += len(sec["stats"]) * line_h
    y += 4 + 6

    # Status
    y += len(sec["status"]) * line_h
    y += 4 + 6

    # Kontrol
    y += len(sec["controls"]) * line_h
    y += 4 + 6

    # Legend
    y += len(sec["legend"]) * line_h

    # padding bawah
    y += 10
    return y - GRID_ORIGIN_Y


# =========================================================
# Render GRID + PATH
# =========================================================
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


def draw_grid(surface, sim: SimulationState, cell_size: int, font, font_title):
    surface.fill(BG)

    grid_w = sim.cols * cell_size
    grid_h = sim.rows * cell_size
    panel_h = get_sidebar_height(sim, font, font_title)

    # panel sidebar
    panel_x = GRID_ORIGIN_X + grid_w + GRID_ORIGIN_X
    pygame.draw.rect(
        surface,
        PANEL_BG,
        pygame.Rect(panel_x, GRID_ORIGIN_Y, SIDEBAR_WIDTH - GRID_ORIGIN_X, panel_h)
    )
    pygame.draw.rect(
        surface,
        PANEL_BORDER,
        pygame.Rect(panel_x, GRID_ORIGIN_Y, SIDEBAR_WIDTH - GRID_ORIGIN_X, panel_h),
        2
    )

    # separator vertical
    pygame.draw.line(
        surface,
        PANEL_BORDER,
        (GRID_ORIGIN_X + grid_w + GRID_ORIGIN_X // 2, GRID_ORIGIN_Y),
        (GRID_ORIGIN_X + grid_w + GRID_ORIGIN_X // 2, GRID_ORIGIN_Y + panel_h),
        2
    )

    # cari max untuk heatmap
    max_count = 0
    for row in sim.visit_counts:
        row_max = max(row) if row else 0
        if row_max > max_count:
            max_count = row_max

    # grid cells
    for r in range(sim.rows):
        for c in range(sim.cols):
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


# =========================================================
# Render SIDEBAR
# =========================================================
def draw_sidebar(surface, sim: SimulationState, font, font_title, cell_size):
    """Gambar sidebar dan kembalikan rect tombol cost_minus, cost_plus."""

    grid_w = sim.cols * cell_size
    panel_x = GRID_ORIGIN_X + grid_w + GRID_ORIGIN_X + 10
    y = GRID_ORIGIN_Y + 10

    sec = build_sidebar_sections(sim)
    line_h = sec["line_h"]

    # Judul
    title = font_title.render("Monte Carlo Pathfinding", True, (255, 255, 255))
    surface.blit(title, (panel_x, y))
    y += line_h + 6

    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Cost control (tombol +/-) =====
    label = font.render("Cost value (0-9) untuk mode Cost:", True, (230, 230, 230))
    surface.blit(label, (panel_x, y))
    y += line_h

    minus_w = 24
    plus_w = 24
    box_h = 22

    cost_minus_rect = pygame.Rect(panel_x, y, minus_w, box_h)
    value_rect      = pygame.Rect(panel_x + minus_w + 4, y, 40, box_h)
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
    for text in sec["stats"]:
        surf = font.render(text, True, (230, 230, 230))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Status =====
    for text in sec["status"]:
        surf = font.render(text, True, (255, 255, 0) if text.startswith("Status:") else (180, 220, 255))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Kontrol =====
    for text in sec["controls"]:
        surf = font.render(text, True, (220, 220, 220))
        surface.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(surface, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Legend =====
    for text in sec["legend"]:
        surf = font.render(text, True, (210, 210, 210))
        surface.blit(surf, (panel_x, y))
        y += line_h

    return cost_minus_rect, cost_plus_rect
