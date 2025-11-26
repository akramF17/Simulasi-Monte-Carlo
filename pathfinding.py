import pygame
import random
import sys

# ================================
# Konfigurasi dasar
# ================================
GRID_ROWS = 10
GRID_COLS = 10
CELL_SIZE = 50
MARGIN = 20

GRID_ORIGIN_X = MARGIN
GRID_ORIGIN_Y = MARGIN
GRID_WIDTH  = GRID_COLS * CELL_SIZE
GRID_HEIGHT = GRID_ROWS * CELL_SIZE

SIDEBAR_WIDTH = 320  # panel kanan untuk UI

WINDOW_WIDTH  = GRID_WIDTH + 2 * MARGIN + SIDEBAR_WIDTH
WINDOW_HEIGHT = GRID_HEIGHT + 2 * MARGIN

FPS = 30
DEFAULT_STEPS_PER_FRAME = 1
MAX_STEPS = 200            # batas langkah satu random walk
MAX_SIMULATIONS = 1000     # total random walk yang dijalankan

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
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Monte Carlo Pathfinding - Pygame (Multi-agent)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
font_title = pygame.font.SysFont(None, 24, bold=True)

# fullscreen toggle
windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
is_fullscreen = False

# ================================
# Variabel simulasi & statistik
# ================================
agent_count = INITIAL_AGENT_COUNT
steps_per_frame = DEFAULT_STEPS_PER_FRAME

agents = []  # list of dict: {pos, path, visited, active, steps}
best_path = None

sim_count = 0              # berapa episode random walk yang sudah DIMULAI
success_count = 0          # berapa yang sukses sampai goal
total_success_length = 0
min_success_length = None
max_success_length = None

simulation_done = False
paused = True              # mulai dalam keadaan berhenti
first_step_after_reset = True  # flag supaya sim_count baru naik saat mulai jalan

# Heatmap
visit_counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


# ================================
# Fungsi bantu simulasi
# ================================
def increment_visit(pos):
    r, c = pos
    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
        visit_counts[r][c] += 1


def create_agent():
    """Buat agen baru mulai dari start (tanpa mengubah sim_count)."""
    agent = {
        "pos": start,
        "path": [start],
        "visited": {start},
        "active": True,
        "steps": 0,
    }
    return agent


def reset_agents():
    """Reset semua agen berdasarkan agent_count (tanpa menyentuh sim_count)."""
    global agents
    agents = []
    for _ in range(agent_count):
        a = create_agent()
        agents.append(a)
        # kalau mau start cell langsung masuk heatmap:
        increment_visit(start)


def reset_heatmap():
    global visit_counts
    visit_counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def reset_stats():
    global best_path, success_count, total_success_length
    global min_success_length, max_success_length, sim_count
    best_path = None
    success_count = 0
    total_success_length = 0
    min_success_length = None
    max_success_length = None
    sim_count = 0


def reset_simulation():
    """Reset semua: heatmap, stats, agen, status simulasi (tetap pause)."""
    global simulation_done, paused, first_step_after_reset
    reset_heatmap()
    reset_stats()
    simulation_done = False
    paused = True           # tidak langsung jalan
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


def handle_success(agent):
    """Update statistik saat agen berhasil mencapai goal."""
    global best_path, success_count, total_success_length
    global min_success_length, max_success_length

    path_len = len(agent["path"])
    success_count += 1
    total_success_length += path_len

    if best_path is None or path_len < len(best_path):
        best_path = agent["path"].copy()
        print(f"Jalur baru terbaik! Panjang = {len(best_path)}")

    if min_success_length is None or path_len < min_success_length:
        min_success_length = path_len
    if max_success_length is None or path_len > max_success_length:
        max_success_length = path_len


def step_agent(agent):
    """Satu langkah random walk untuk satu agen."""
    if not agent["active"]:
        return

    if agent["steps"] >= MAX_STEPS:
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

    # Monte Carlo: pilih tetangga secara acak
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
    """Restart agen jika masih boleh menambah simulasi baru."""
    global sim_count
    if sim_count >= MAX_SIMULATIONS:
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
def draw_grid():
    """Gambar grid, heatmap, rintangan, start, dan goal + panel frame."""
    screen.fill(BG)

    # panel sidebar
    panel_x = GRID_ORIGIN_X + GRID_WIDTH + MARGIN
    pygame.draw.rect(
        screen,
        PANEL_BG,
        pygame.Rect(panel_x, MARGIN, SIDEBAR_WIDTH - MARGIN, WINDOW_HEIGHT - 2 * MARGIN)
    )
    pygame.draw.rect(
        screen,
        PANEL_BORDER,
        pygame.Rect(panel_x, MARGIN, SIDEBAR_WIDTH - MARGIN, WINDOW_HEIGHT - 2 * MARGIN),
        2
    )

    # separator vertical antara grid dan panel
    pygame.draw.line(
        screen,
        PANEL_BORDER,
        (GRID_ORIGIN_X + GRID_WIDTH + MARGIN // 2, MARGIN),
        (GRID_ORIGIN_X + GRID_WIDTH + MARGIN // 2, WINDOW_HEIGHT - MARGIN),
        2
    )

    # hitung max heat
    max_count = 0
    for row in visit_counts:
        row_max = max(row)
        if row_max > max_count:
            max_count = row_max

    # sel-sel grid
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = GRID_ORIGIN_X + c * CELL_SIZE
            y = GRID_ORIGIN_Y + r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            if grid[r][c] == 1:
                pygame.draw.rect(screen, BLACK, rect)
            else:
                if max_count > 0 and visit_counts[r][c] > 0:
                    ratio = visit_counts[r][c] / max_count
                    red = 255
                    gb = int(255 * (1 - ratio))
                    color = (red, gb, gb)
                else:
                    color = WHITE

                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, GRAY, rect, 1)

    # start (hijau)
    sx = GRID_ORIGIN_X + start[1] * CELL_SIZE
    sy = GRID_ORIGIN_Y + start[0] * CELL_SIZE
    pygame.draw.rect(screen, GREEN, (sx, sy, CELL_SIZE, CELL_SIZE))

    # goal (merah)
    gx = GRID_ORIGIN_X + goal[1] * CELL_SIZE
    gy = GRID_ORIGIN_Y + goal[0] * CELL_SIZE
    pygame.draw.rect(screen, RED, (gx, gy, CELL_SIZE, CELL_SIZE))


def draw_paths():
    """Gambar jalur terbaik & jalur agen."""
    if best_path is not None and len(best_path) >= 2:
        draw_path(best_path, BLUE, width=4)

    for agent in agents:
        if agent["active"] and len(agent["path"]) >= 2:
            draw_path(agent["path"], YELLOW, width=2)


def draw_path(path, color, width=3):
    pts = []
    for (r, c) in path:
        x = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE // 2
        y = GRID_ORIGIN_Y + r * CELL_SIZE + CELL_SIZE // 2
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(screen, color, False, pts, width)


def draw_sidebar():
    """Gambar teks/statistik/kontrol di panel kanan."""
    panel_x = GRID_ORIGIN_X + GRID_WIDTH + MARGIN + 10
    y = MARGIN + 10
    line_h = 16  # sedikit lebih rapat supaya tidak kepotong

    # Judul
    title = font_title.render("Monte Carlo Pathfinding", True, (255, 255, 255))
    screen.blit(title, (panel_x, y))
    y += line_h + 6

    pygame.draw.line(screen, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Statistik =====
    best_len = len(best_path) if best_path is not None else "-"
    success_rate = (success_count / sim_count * 100) if sim_count > 0 else 0.0
    avg_len = (total_success_length / success_count) if success_count > 0 else 0

    stats_lines = [
        "[Statistik]",
        f"Simulasi: {sim_count}/{MAX_SIMULATIONS}",
        f"Agen      : {agent_count}",
        f"Steps/frame: {steps_per_frame}",
        f"Best length: {best_len}",
        f"Sukses: {success_count} ({success_rate:.1f}%)",
    ]

    if success_count > 0:
        stats_lines.append(f"Avg len: {avg_len:.1f}")
        stats_lines.append(f"Min/Max: {min_success_length}/{max_success_length}")
    else:
        stats_lines.append("Belum ada jalur sukses.")

    for text in stats_lines:
        surf = font.render(text, True, (230, 230, 230))
        screen.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(screen, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
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
    screen.blit(surf, (panel_x, y))
    y += line_h

    if paused and not simulation_done:
        hint = "SPACE: Start / Pause"
        surf = font.render(hint, True, (180, 255, 180))
        screen.blit(surf, (panel_x, y))
        y += line_h

    if simulation_done:
        done_msg = "Simulasi selesai. Tekan R untuk reset."
        surf = font.render(done_msg, True, (255, 200, 0))
        screen.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(screen, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Kontrol =====
    controls = [
        "[Kontrol]",
        "SPACE : Start / Pause",
        "R     : Reset simulasi",
        "Z / X : Agen - / +",
        "C / V : Steps/frame - / +",
        "F     : Fullscreen ON/OFF",
        "ESC   : Keluar",
    ]
    for text in controls:
        surf = font.render(text, True, (220, 220, 220))
        screen.blit(surf, (panel_x, y))
        y += line_h

    y += 4
    pygame.draw.line(screen, PANEL_BORDER, (panel_x, y), (panel_x + SIDEBAR_WIDTH - 40, y), 1)
    y += 6

    # ===== Legend =====
    legend = [
        "[Mouse & Legend]",
        "Left  : Toggle wall",
        "Middle: Set START",
        "Right : Set GOAL",
        "Putih : Jalan",
        "Hitam : Rintangan",
        "Hijau : START",
        "Merah : GOAL",
        "Biru  : Best path",
        "Kuning: Jalur agen",
        "Merah pekat: sering dilalui",
    ]
    for text in legend:
        surf = font.render(text, True, (210, 210, 210))
        screen.blit(surf, (panel_x, y))
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

            # ubah jumlah agen (reset simulasi)
            elif event.key == pygame.K_z:
                if agent_count > 1:
                    agent_count -= 1
                    reset_simulation()
            elif event.key == pygame.K_x:
                if agent_count < MAX_AGENT_COUNT:
                    agent_count += 1
                    reset_simulation()

            # ubah steps per frame
            elif event.key == pygame.K_c:
                if steps_per_frame > 1:
                    steps_per_frame -= 1
            elif event.key == pygame.K_v:
                if steps_per_frame < 20:
                    steps_per_frame += 1

            # toggle fullscreen
            elif event.key == pygame.K_f:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode(windowed_size)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # cek klik di area grid saja
            if (GRID_ORIGIN_X <= mx < GRID_ORIGIN_X + GRID_WIDTH and
                GRID_ORIGIN_Y <= my < GRID_ORIGIN_Y + GRID_HEIGHT):
                c = (mx - GRID_ORIGIN_X) // CELL_SIZE
                r = (my - GRID_ORIGIN_Y) // CELL_SIZE

                if event.button == 1:
                    # toggle obstacle kecuali di start/goal
                    if (r, c) != start and (r, c) != goal:
                        grid[r][c] = 1 - grid[r][c]
                        visit_counts[r][c] = 0
                elif event.button == 2:
                    # set START
                    if (r, c) != goal:
                        start = (r, c)
                        reset_simulation()
                elif event.button == 3:
                    # set GOAL
                    if (r, c) != start:
                        goal = (r, c)
                        reset_simulation()

    # --- Update simulasi Monte Carlo ---
    if not paused and not simulation_done:
        # saat baru pertama kali jalan setelah reset, hitung agen awal sebagai simulasi
        if first_step_after_reset:
            # setiap agen aktif = satu episode yang dimulai
            active_agents = sum(1 for a in agents if a["active"])
            sim_count = min(active_agents, MAX_SIMULATIONS)
            first_step_after_reset = False

        for _ in range(steps_per_frame):
            # langkah tiap agen
            for agent in agents:
                step_agent(agent)

            # restart agen jika bisa
            if sim_count < MAX_SIMULATIONS:
                remaining = MAX_SIMULATIONS - sim_count
                for agent in agents:
                    if not agent["active"] and remaining > 0:
                        if restart_agent_if_possible(agent):
                            remaining -= 1
                        else:
                            break

            # cek selesai total
            if sim_count >= MAX_SIMULATIONS and all(not a["active"] for a in agents):
                simulation_done = True
                print("Simulasi selesai. Mencapai MAX_SIMULATIONS.")
                break

    # --- Gambar ---
    draw_grid()
    draw_paths()
    draw_sidebar()

    pygame.display.flip()

# keluar
pygame.quit()
sys.exit()
