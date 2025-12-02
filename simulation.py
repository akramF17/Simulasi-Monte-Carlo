# simulation.py

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

from config import (
    GRID_ROWS, GRID_COLS, GRID_ORIGIN_X, GRID_ORIGIN_Y, GRID_WIDTH, GRID_HEIGHT,
    DEFAULT_STEPS_PER_FRAME, MAX_STEPS_DEFAULT, MAX_SIMULATIONS_DEFAULT,
    INITIAL_AGENT_COUNT, MAX_AGENT_COUNT,
    MOVES
)


Pos = Tuple[int, int]
Path = List[Pos]


@dataclass
class Agent:
    pos: Pos
    path: Path
    visited: set
    active: bool
    steps: int


@dataclass
class SimulationState:
    # grid & costs
    grid: List[List[int]] = field(default_factory=lambda: [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)])
    visit_counts: List[List[int]] = field(default_factory=lambda: [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)])
    cell_costs: List[List[int]] = field(default_factory=lambda: [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)])

    start: Pos = (0, 0)
    goal: Pos = (GRID_ROWS - 1, GRID_COLS - 1)

    # sim settings
    agent_count: int = INITIAL_AGENT_COUNT
    steps_per_frame: int = DEFAULT_STEPS_PER_FRAME
    max_steps_per_walk: int = MAX_STEPS_DEFAULT
    max_simulations: int = MAX_SIMULATIONS_DEFAULT

    # sim state
    agents: List[Agent] = field(default_factory=list)
    best_path: Optional[Path] = None
    best_path_cost: Optional[float] = None

    sim_count: int = 0
    success_count: int = 0
    total_success_length: int = 0
    min_success_length: Optional[int] = None
    max_success_length: Optional[int] = None

    total_success_cost: float = 0.0
    min_success_cost: Optional[float] = None
    max_success_cost: Optional[float] = None

    simulation_done: bool = False
    paused: bool = True
    first_step_after_reset: bool = True

    # cursor & cost editing
    cursor_mode: str = "obstacle"  # "obstacle" atau "cost"
    current_cost_value: int = 1

    def __post_init__(self):
        # inisialisasi rintangan default
        obstacles = [
            (1, 1), (1, 2), (1, 3),
            (2, 3),
            (3, 3), (3, 4), (3, 5),
            (5, 7), (6, 7), (7, 7),
            (4, 1), (5, 1), (6, 1)
        ]
        for r, c in obstacles:
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                self.grid[r][c] = 1

        self.reset_simulation()

    # ---------- basic utils ----------

    def increment_visit(self, pos: Pos):
        r, c = pos
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            self.visit_counts[r][c] += 1

    def create_agent(self) -> Agent:
        return Agent(
            pos=self.start,
            path=[self.start],
            visited={self.start},
            active=True,
            steps=0,
        )

    def reset_agents(self):
        self.agents = []
        for _ in range(self.agent_count):
            a = self.create_agent()
            self.agents.append(a)
            self.increment_visit(self.start)

    def reset_heatmap(self):
        self.visit_counts = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    def reset_stats(self):
        self.best_path = None
        self.best_path_cost = None

        self.success_count = 0
        self.total_success_length = 0
        self.min_success_length = None
        self.max_success_length = None

        self.total_success_cost = 0.0
        self.min_success_cost = None
        self.max_success_cost = None

        self.sim_count = 0

    def reset_simulation(self):
        self.reset_heatmap()
        self.reset_stats()
        self.simulation_done = False
        self.paused = True
        self.first_step_after_reset = True
        self.reset_agents()

    # ---------- Monte Carlo logic ----------

    def get_valid_neighbors(self, agent: Agent) -> List[Pos]:
        r, c = agent.pos
        neighbors = []
        for dr, dc in MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                if self.grid[nr][nc] == 0 and (nr, nc) not in agent.visited:
                    neighbors.append((nr, nc))
        return neighbors

    def get_cell_cost_value(self, r: int, c: int) -> float:
        """
        Mapping cost:
        - 0 titik  -> 1.0
        - 1 titik  -> 1.2
        - 2 titik  -> 1.4
        ...
        - n titik  -> 1.0 + 0.2 * n
        """
        dots = self.cell_costs[r][c]
        return 1.0 + 0.2 * dots

    def compute_path_cost(self, path: Path) -> float:
        total = 0.0
        for (r, c) in path:
            total += self.get_cell_cost_value(r, c)
        return total

    def handle_success(self, agent: Agent):
        path_len = len(agent.path)
        path_cost = self.compute_path_cost(agent.path)

        self.success_count += 1
        self.total_success_length += path_len
        self.total_success_cost += path_cost

        # best path by minimal cost (tie => shorter length)
        if self.best_path is None:
            self.best_path = agent.path.copy()
            self.best_path_cost = path_cost
            print(f"Jalur baru terbaik! Cost = {path_cost:.2f}, Panjang = {len(self.best_path)}")
        else:
            if (path_cost < self.best_path_cost - 1e-9) or \
               (abs(path_cost - self.best_path_cost) < 1e-9 and path_len < len(self.best_path)):
                self.best_path = agent.path.copy()
                self.best_path_cost = path_cost
                print(f"Jalur baru terbaik! Cost = {path_cost:.2f}, Panjang = {len(self.best_path)}")

        # min/max length
        if self.min_success_length is None or path_len < self.min_success_length:
            self.min_success_length = path_len
        if self.max_success_length is None or path_len > self.max_success_length:
            self.max_success_length = path_len

        # min/max cost
        if self.min_success_cost is None or path_cost < self.min_success_cost:
            self.min_success_cost = path_cost
        if self.max_success_cost is None or path_cost > self.max_success_cost:
            self.max_success_cost = path_cost

    def step_agent(self, agent: Agent):
        if not agent.active:
            return

        if agent.steps >= self.max_steps_per_walk:
            agent.active = False
            return

        if agent.pos == self.goal:
            self.handle_success(agent)
            agent.active = False
            return

        neighbors = self.get_valid_neighbors(agent)
        if not neighbors:
            agent.active = False
            return

        # Monte Carlo: pure random neighbor
        next_pos = random.choice(neighbors)
        agent.pos = next_pos
        agent.path.append(next_pos)
        agent.visited.add(next_pos)
        agent.steps += 1
        self.increment_visit(next_pos)

        if agent.pos == self.goal:
            self.handle_success(agent)
            agent.active = False

    def restart_agent_if_possible(self, agent: Agent) -> bool:
        if self.sim_count >= self.max_simulations:
            return False

        agent.pos = self.start
        agent.path = [self.start]
        agent.visited = {self.start}
        agent.active = True
        agent.steps = 0
        self.sim_count += 1
        self.increment_visit(self.start)
        return True

    def step_frame(self):
        """Jalankan satu frame simulasi (beberapa langkah tergantung steps_per_frame)."""
        if self.paused or self.simulation_done:
            return

        if self.first_step_after_reset:
            active_agents = sum(1 for a in self.agents if a.active)
            self.sim_count = min(active_agents, self.max_simulations)
            self.first_step_after_reset = False

        for _ in range(self.steps_per_frame):
            for agent in self.agents:
                self.step_agent(agent)

            if self.sim_count < self.max_simulations:
                remaining = self.max_simulations - self.sim_count
                for agent in self.agents:
                    if not agent.active and remaining > 0:
                        if self.restart_agent_if_possible(agent):
                            remaining -= 1
                        else:
                            break

            if self.sim_count >= self.max_simulations and all(not a.active for a in self.agents):
                self.simulation_done = True
                print("Simulasi selesai. Mencapai max_simulations.")
                break

    # ---------- Interaksi grid (mouse) ----------

    def handle_grid_click(self, r: int, c: int, button: int):
        """Dipanggil dari main saat klik di cell (r, c)."""
        # left click
        if button == 1:
            if self.cursor_mode == "obstacle":
                if (r, c) != self.start and (r, c) != self.goal:
                    if self.grid[r][c] == 0:
                        self.grid[r][c] = 1
                        self.cell_costs[r][c] = 0
                        self.visit_counts[r][c] = 0
                    else:
                        self.grid[r][c] = 0
            elif self.cursor_mode == "cost":
                if self.grid[r][c] == 0:
                    self.cell_costs[r][c] = max(0, min(9, self.current_cost_value))

        # middle: set start
        elif button == 2:
            if (r, c) != self.goal:
                self.start = (r, c)
                self.reset_simulation()

        # right: set goal
        elif button == 3:
            if (r, c) != self.start:
                self.goal = (r, c)
                self.reset_simulation()
