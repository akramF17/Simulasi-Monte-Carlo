# config.py

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

# Gerakan (atas, bawah, kiri, kanan)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]
