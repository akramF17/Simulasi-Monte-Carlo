import pygame
import random
import sys

# ================================
# Konfigurasi dasar
# ================================
GRID_ROWS = 10
GRID_COLS = 10
CELL_SIZE = 50
MARGIN = 25

GRID_ORIGIN_X = MARGIN
GRID_ORIGIN_Y = MARGIN
GRID_WIDTH  = GRID_COLS * CELL_SIZE
GRID_HEIGHT = GRID_ROWS * CELL_SIZE

SIDEBAR_WIDTH = 320  # panel kanan untuk UI

# Tinggi panel (sidebar) dibuat lebih besar dari grid supaya UI muat
PANEL_HEIGHT = GRID_HEIGHT + 260

# Window height = cukup untuk muat grid & panel (ambil yang lebih tinggi)
WINDOW_WIDTH  = GRID_WIDTH + 2 * MARGIN + SIDEBAR_WIDTH
WINDOW_HEIGHT = max(GRID_HEIGHT, PANEL_HEIGHT) + 2 * MARGIN

FPS = 30
DEFAULT_STEPS_PER_FRAME = 1
MAX_STEPS_DEFAULT = 200
MAX_SIMULATIONS_DEFAULT = 1000

INITIAL_AGENT_COUNT = 3
MAX_AGENT_COUNT = 20

# Warna (R, G, B)
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GRAY    = (200, 200, 200)
GREEN   = (0, 200,   0)
RED     = (220, 0,   0)
BLUE    = (0,   0, 255)
YELLOW  = (255, 215, 0)
BG      = (30,  30,  30)
PANEL_BG = (40, 40, 60)
PANEL_BORDER = (100, 100, 130)

# ================================
# Grid & rintangan
# ================================
grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

obstacles = [
    (1, 1), (1, 2), (1, 3),
    (2, 3),
    (3, 3), (3, 4), (3, 5),
    (5, 7), (6, 7), (7, 7),
    (4, 1), (5, 1), (6, 1)
]
for r, c in obstacles:
    grid[r][c] = 1

start = (0, 0)
goal  = (GRID_ROWS - 1, GRID_COLS - 1)

moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# ================================
# Inisialisasi Pygame
# ================================
pygame.init()
LOGICAL_WIDTH = WINDOW_WIDTH
LOGICAL_HEIGHT = WINDOW_HEIGHT

windowed_size = (LOGICAL_WIDTH, LOGICAL_HEIGHT)
screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
pygame.display.set_caption("Monte Carlo Pathfinding - Pygame (Multi-agent)")

# surface tempat kita menggambar semuanya (logis)
canvas = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
font_title = pygame.font.SysFont(None, 24, bold=True)

# ================================
# Variabel simulasi & statistik
# ================================
agent_count = INITIAL_AGENT_COUNT
steps_per_frame = DEFAULT_STEPS_PER_FRAME

max_steps_per_walk = MAX_STEPS_DEFAULT
max_simulations    = MAX_SIMULATIONS_DEFAULT

agents = []  # list of dict: {pos, path, visited, active, steps}
best_path = None
best_path_cost = None

sim_count = 0              # episode random walk yang sudah DIMULAI
success_count = 0          # yang sukses sampai goal
total_success_length = 0
min_success_length = None
max_success_length = None

total_success_cost = 0.0
min_success_cost = None
max_success_cost = None

simulation_done = False
paused = True
first_step_after_reset = True

# Heatmap & cost
visit_counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
cell_costs   = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]  # jumlah titik (0-9)

# Cursor mode & cost value
cursor_mode = "obstacle"  # "obstacle" atau "cost"
current_cost_value = 1

# Tombol +/- cost (diisi posisinya di draw_sidebar)
cost_minus_rect = pygame.Rect(0, 0, 0, 0)
cost_plus_rect  = pygame.Rect(0, 0, 0, 0)


# ================================
# Fungsi bantu simulasi & cost
# ================================
def increment_visit(pos):
    r, c = pos
    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
        visit_counts[r][c] += 1


def create_agent():
    return {
        "pos": start,
        "path": [start],
        "visited": {start},
        "active": True,
        "steps": 0,
    }


def reset_agents():
    global agents
    agents = []
    for _ in range(agent_count):
        a = create_agent()
        agents.append(a)
        increment_visit(start)


def reset_heatmap():
    global visit_counts
    visit_counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def reset_stats():
    global best_path, best_path_cost
    global success_count, total_success_length
    global min_success_length, max_success_length
    global total_success_cost, min_success_cost, max_success_cost
    global sim_count

    best_path = None
    best_path_cost = None
    success_count = 0
    total_success_length = 0
    min_success_length = None
    max_success_length = None

    total_success_cost = 0.0
    min_success_cost = None
    max_success_cost = None

    sim_count = 0


def reset_simulation():
    global simulation_done, paused, first_step_after_reset
    reset_heatmap()
    reset_stats()
    simulation_done = False
    paused = True
    first_step_after_reset = True
    reset_agents()


def get_valid_neighbors_for_agent(agent):
    r, c = agent["pos"]
    neighbors = []
    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
            if grid[nr][nc] == 0 and (nr, nc) not in agent["visited"]:
                neighbors.append((nr, nc))
    return neighbors


def get_cell_cost_value(r, c):
    """
    Mapping cost:
    - 0 titik  -> 1.0
    - 1 titik  -> 1.2
    - 2 titik  -> 1.4
    ...
    - n titik  -> 1.0 + 0.2 * n
    """
    dots = cell_costs[r][c]
    return 1.0 + 0.2 * dots


def compute_path_cost(path):
    total = 0.0
    for (r, c) in path:
        total += get_cell_cost_value(r, c)
    return total


def handle_success(agent):
    """Update statistik saat agen berhasil mencapai goal (pakai cost)."""
    global best_path, best_path_cost
    global success_count, total_success_length
    global min_success_length, max_success_length
    global total_success_cost, min_success_cost, max_success_cost

    path_len = len(agent["path"])
    path_cost = compute_path_cost(agent["path"])

    success_count += 1
    total_success_length += path_len
    total_success_cost += path_cost

    # update best_path by minimal cost (tie-breaker = lebih pendek)
    if best_path is None:
        best_path = agent["path"].copy()
        best_path_cost = path_cost
        print(f"Jalur baru terbaik! Cost = {best_path_cost:.2f}, Panjang = {len(best_path)}")
    else:
        if (path_cost < best_path_cost - 1e-9) or \
           (abs(path_cost - best_path_cost) < 1e-9 and path_len < len(best_path)):
            best_path = agent["path"].copy()
            best_path_cost = path_cost
            print(f"Jalur baru terbaik! Cost = {best_path_cost:.2f}, Panjang = {len(best_path)}")

    # update min/max length
    if min_success_length is None or path_len < min_success_length:
        min_success_length = path_len
    if max_success_length is None or path_len > max_success_length:
        max_success_length = path_len

    # update min/max cost
    if min_success_cost is None or path_cost < min_success_cost:
        min_success_cost = path_cost
    if max_success_cost is None or path_cost > max_success_cost:
        max_success_cost = path_cost


def step_agent(agent):
    if not agent["active"]:
        return

    if agent["steps"] >= max_steps_per_walk:
        agent["active"] = False
        return

    if agent["pos"] == goal:
        handle_success(agent)
        agent["active"] = False
        return

    neighbors = get_valid_neighbors_for_agent(agent)
    if not neighbors:
        agent["active"] = False
        return

    # Monte Carlo: pilih tetangga secara acak (belum pakai cost untuk bias)
    next_pos = random.choice(neighbors)
    agent["pos"] = next_pos
    agent["path"].append(next_pos)
    agent["visited"].add(next_pos)
    agent["steps"] += 1
    increment_visit(next_pos)

    if agent["pos"] == goal:
        handle_success(agent)
        agent["active"] = False


def restart_agent_if_possible(agent):
    global sim_count
    if sim_count >= max_simulations:
        return False

    agent["pos"] = start
    agent["path"] = [start]
    agent["visited"] = {start}
    agent["active"] = True
    agent["steps"] = 0
    sim_count += 1
    increment_visit(start)
    return True


# ================================
# Fungsi gambar / UI
# ================================
def draw_cost_dots(surface, r, c, cost):
    if cost <= 0:
        return
    cost = min(cost, 9)

    cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE // 2
    cy = GRID_ORIGIN_Y + r * CELL_SIZE + CELL_SIZE // 2

    offsets = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0), (0,  0), (1,  0),
        (-1,  1), (0,  1), (1,  1),
    ]

    step = CELL_SIZE // 4
    radius = max(2, CELL_SIZE // 10)

    for i in range(cost):
        ox, oy = offsets[i]
        x = cx + ox * step
        y = cy + oy * step
        pygame.draw.circle(surface, BLACK, (x, y), radius)


def draw_grid(surface):
    surface.fill(BG)

    # panel sidebar
    panel_x = GRID_ORIGIN_X + GRID_WIDTH + MARGIN
    pygame.draw.rect(
        surface,
        PANEL_BG,
        pygame.Rect(panel_x, MARGIN, SIDEBAR_WIDTH - MARGIN, PANEL_HEIGHT)
    )
    pygame.draw.rect(
        surface,
        PANEL_BORDER,
        pygame.Rect(panel_x, MARGIN, SIDEBAR_WIDTH - MARGIN, PANEL_HEIGHT),
        2
    )

    # separator vertical
    pygame.draw.line(
        surface,
        PANEL_BORDER,
        (GRID_ORIGIN_X + GRID_WIDTH + MARGIN // 2, MARGIN),
        (GRID_ORIGIN_X + GRID_WIDTH + MARGIN // 2, MARGIN + PANEL_HEIGHT),
        2
    )

    # cari max untuk heatmap
    max_count = 0
    for row in visit_counts:
        row_max = max(row)
        if row_max > max_count:
            max_count = row_max

    # grid cells
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = GRID_ORIGIN_X + c * CELL_SIZE
            y = GRID_ORIGIN_Y + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            if grid[r][c] == 1:
                pygame.draw.rect(surface, BLACK, rect)
            else:
                if max_count > 0 and visit_counts[r][c] > 0:
                    ratio = visit_counts[r][c] / max_count
                    red = 255
                    gb = int(255 * (1 - ratio))
                    color = (red, gb, gb)
                else:
                    color = WHITE

                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, GRAY, rect, 1)

                if cell_costs[r][c] > 0:
                    draw_cost_dots(surface, r, c, cell_costs[r][c])

    # start
    sx = GRID_ORIGIN_X + start[1] * CELL_SIZE
    sy = GRID_ORIGIN_Y + start[0] * CELL_SIZE
    pygame.draw.rect(surface, GREEN, (sx, sy, CELL_SIZE, CELL_SIZE))

    # goal
    gx = GRID_ORIGIN_X + goal[1] * CELL_SIZE
    gy = GRID_ORIGIN_Y + goal[0] * CELL_SIZE
    pygame.draw.rect(surface, RED, (gx, gy, CELL_SIZE, CELL_SIZE))


def draw_paths(surface):
    if best_path is not None and len(best_path) >= 2:
        draw_path(surface, best_path, GREEN, width=4)

    for agent in agents:
        if agent["active"] and len(agent["path"]) >= 2:
            draw_path(surface, agent["path"], BLUE, width=2)


def draw_path(surface, path, color, width=3):
    pts = []
    for (r, c) in path:
        x = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE // 2
        y = GRID_ORIGIN_Y + r * CELL_SIZE + CELL_SIZE // 2
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(surface, color, False, pts, width)


def draw_sidebar(surface):
    global cost_minus_rect, cost_plus_rect

    panel_x = GRID_ORIGIN_X + GRID_WIDTH + MARGIN + 10
    y = MARGIN + 10
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

    # Tombol - [nilai] +
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
    val_text = font.render(str(current_cost_value), True, (255, 255, 255))
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
    best_len = len(best_path) if best_path is not None else "-"
    best_cost_str = f"{best_path_cost:.2f}" if best_path_cost is not None else "-"
    success_rate = (success_count / sim_count * 100) if sim_count > 0 else 0.0
    avg_len = (total_success_length / success_count) if success_count > 0 else 0
    avg_cost = (total_success_cost / success_count) if success_count > 0 else 0.0

    stats_lines = [
        "[Statistik]",
        f"Simulasi: {sim_count}/{max_simulations}",
        f"Agen      : {agent_count}",
        f"Steps/frame: {steps_per_frame}",
        f"Max steps/episode: {max_steps_per_walk}",
        f"Best length: {best_len}",
        f"Best cost  : {best_cost_str}",
        f"Sukses: {success_count} ({success_rate:.1f}%)",
    ]

    if success_count > 0:
        stats_lines.append(f"Avg len : {avg_len:.1f}")
        stats_lines.append(f"Min/Max len: {min_success_length}/{max_success_length}")
        stats_lines.append(f"Avg cost: {avg_cost:.2f}")
        stats_lines.append(f"Min/Max cost: {min_success_cost:.2f}/{max_success_cost:.2f}")
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
    if simulation_done:
        status_text = "DONE"
    elif not paused and not simulation_done:
        status_text = "RUNNING"
    elif paused and sim_count > 0:
        status_text = "PAUSED"
    else:
        status_text = "READY"

    surf = font.render(f"Status: {status_text}", True, (255, 255, 0))
    surface.blit(surf, (panel_x, y))
    y += line_h

    # status cursor mode
    if cursor_mode == "obstacle":
        cursor_label = "Obstacle (edit rintangan)"
    else:
        cursor_label = f"Cost (nilai {current_cost_value})"
    surf = font.render(f"Cursor: {cursor_label}", True, (180, 220, 255))
    surface.blit(surf, (panel_x, y))
    y += line_h

    if paused and not simulation_done:
        hint = "SPACE: Start / Pause"
        surf = font.render(hint, True, (180, 255, 180))
        surface.blit(surf, (panel_x, y))
        y += line_h

    if simulation_done:
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


# ================================
# Inisialisasi awal
# ================================
reset_simulation()

# ================================
# Main loop
# ================================
running = True
while running:
    clock.tick(FPS)

    # pastikan current_cost_value tetap di range 0–9
    current_cost_value = max(0, min(current_cost_value, 9))

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                if not simulation_done:
                    paused = not paused

            elif event.key == pygame.K_r:
                reset_simulation()

            elif event.key == pygame.K_z:
                if agent_count > 1:
                    agent_count -= 1
                    reset_simulation()
            elif event.key == pygame.K_x:
                if agent_count < MAX_AGENT_COUNT:
                    agent_count += 1
                    reset_simulation()

            elif event.key == pygame.K_c:
                if steps_per_frame > 1:
                    steps_per_frame -= 1
            elif event.key == pygame.K_v:
                if steps_per_frame < 20:
                    steps_per_frame += 1

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
                if max_simulations > agent_count:
                    max_simulations = max(max_simulations - 50, agent_count)

            elif event.key == pygame.K_RIGHTBRACKET:
                max_simulations += 50

            elif event.key == pygame.K_COMMA:
                if max_steps_per_walk > 10:
                    max_steps_per_walk -= 10

            elif event.key == pygame.K_PERIOD:
                max_steps_per_walk += 10

            elif event.key == pygame.K_1:
                cursor_mode = "obstacle"
            elif event.key == pygame.K_2:
                cursor_mode = "cost"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            display_w, display_h = screen.get_size()

            scale_x = LOGICAL_WIDTH / display_w
            scale_y = LOGICAL_HEIGHT / display_h

            mx_log = int(mx * scale_x)
            my_log = int(my * scale_y)

            # cek klik tombol cost +/- (di sidebar)
            if cost_minus_rect.collidepoint(mx_log, my_log):
                current_cost_value = max(0, current_cost_value - 1)
            elif cost_plus_rect.collidepoint(mx_log, my_log):
                current_cost_value = min(9, current_cost_value + 1)

                        # area grid
            if (GRID_ORIGIN_X <= mx_log < GRID_ORIGIN_X + GRID_WIDTH and
                GRID_ORIGIN_Y <= my_log < GRID_ORIGIN_Y + GRID_HEIGHT):
                c = (mx_log - GRID_ORIGIN_X) // CELL_SIZE
                r = (my_log - GRID_ORIGIN_Y) // CELL_SIZE

                if event.button == 1:
                    if cursor_mode == "obstacle":
                        if (r, c) != start and (r, c) != goal:
                            if grid[r][c] == 0:
                                grid[r][c] = 1
                                cell_costs[r][c] = 0
                                visit_counts[r][c] = 0
                            else:
                                grid[r][c] = 0
                    elif cursor_mode == "cost":
                        if grid[r][c] == 0:
                            cell_costs[r][c] = current_cost_value

                elif event.button == 2:
                    if (r, c) != goal:
                        start = (r, c)
                        reset_simulation()
                elif event.button == 3:
                    if (r, c) != start:
                        goal = (r, c)
                        reset_simulation()
    # --- Update simulasi Monte Carlo ---
    if not paused and not simulation_done:
        if first_step_after_reset:
            active_agents = sum(1 for a in agents if a["active"])
            sim_count = min(active_agents, max_simulations)
            first_step_after_reset = False

        for _ in range(steps_per_frame):
            for agent in agents:
                step_agent(agent)

            if sim_count < max_simulations:
                remaining = max_simulations - sim_count
                for agent in agents:
                    if not agent["active"] and remaining > 0:
                        if restart_agent_if_possible(agent):
                            remaining -= 1
                        else:
                            break

            if sim_count >= max_simulations and all(not a["active"] for a in agents):
                simulation_done = True
                print("Simulasi selesai. Mencapai max_simulations.")
                break

    # --- Gambar ---
    draw_grid(canvas)
    draw_paths(canvas)
    draw_sidebar(canvas)

    display_size = screen.get_size()
    scaled = pygame.transform.scale(canvas, display_size)
    screen.blit(scaled, (0, 0))
    pygame.display.flip()

# keluar
pygame.quit()
sys.exit()

