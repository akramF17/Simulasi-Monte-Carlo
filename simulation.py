# simulation.py

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from config import (
    DEFAULT_GRID_ROWS, DEFAULT_GRID_COLS,
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
    # ukuran grid dinamis
    rows: int = DEFAULT_GRID_ROWS
    cols: int = DEFAULT_GRID_COLS

    # grid & costs
    grid: List[List[int]] = field(default_factory=list)
    visit_counts: List[List[int]] = field(default_factory=list)
    cell_costs: List[List[int]] = field(default_factory=list)

    start: Pos = (0, 0)
    goal: Pos = (DEFAULT_GRID_ROWS - 1, DEFAULT_GRID_COLS - 1)

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
    cursor_mode: str = "obstacle"
    current_cost_value: int = 1

    # dipakai main.py untuk rebuild window/canvas
    map_just_resized: bool = False

    def __post_init__(self):
        self._allocate_grids(self.rows, self.cols)

        self.start = (0, 0)
        self.goal = (self.rows - 1, self.cols - 1)

        obstacles = [
            (1, 1), (1, 2), (1, 3),
            (2, 3),
            (3, 3), (3, 4), (3, 5),
            (5, 7), (6, 7), (7, 7),
            (4, 1), (5, 1), (6, 1)
        ]
        for r, c in obstacles:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.grid[r][c] = 1

        self.reset_simulation()

    # ---------- grid allocation / resize ----------

    def _allocate_grids(self, rows: int, cols: int):
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.visit_counts = [[0 for _ in range(cols)] for _ in range(rows)]
        self.cell_costs = [[0 for _ in range(cols)] for _ in range(rows)]

    def resize_grid(self, rows: int, cols: int):
        """Resize map dan reset simulasi."""
        self.rows, self.cols = rows, cols
        self._allocate_grids(rows, cols)

        self.start = (0, 0)
        self.goal = (rows - 1, cols - 1)

        self.reset_simulation()
        self.map_just_resized = True

    # ---------- basic utils ----------

    def increment_visit(self, pos: Pos):
        r, c = pos
        if 0 <= r < self.rows and 0 <= c < self.cols:
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
        self.visit_counts = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

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
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] == 0 and (nr, nc) not in agent.visited:
                    neighbors.append((nr, nc))
        return neighbors

    def get_cell_cost_value(self, r: int, c: int) -> float:
        dots = self.cell_costs[r][c]
        return 1.0 + 0.2 * dots

    def compute_path_cost(self, path: Path) -> float:
        return sum(self.get_cell_cost_value(r, c) for (r, c) in path)

    def handle_success(self, agent: Agent):
        path_len = len(agent.path)
        path_cost = self.compute_path_cost(agent.path)

        self.success_count += 1
        self.total_success_length += path_len
        self.total_success_cost += path_cost

        if self.best_path is None:
            self.best_path = agent.path.copy()
            self.best_path_cost = path_cost
        else:
            if (path_cost < self.best_path_cost - 1e-9) or \
               (abs(path_cost - self.best_path_cost) < 1e-9 and path_len < len(self.best_path)):
                self.best_path = agent.path.copy()
                self.best_path_cost = path_cost

        if self.min_success_length is None or path_len < self.min_success_length:
            self.min_success_length = path_len
        if self.max_success_length is None or path_len > self.max_success_length:
            self.max_success_length = path_len

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
                break

    # ---------- Interaksi grid (mouse) ----------

    def handle_grid_click(self, r: int, c: int, button: int):
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

        elif button == 2:
            if (r, c) != self.goal:
                self.start = (r, c)
                self.reset_simulation()

        elif button == 3:
            if (r, c) != self.start:
                self.goal = (r, c)
                self.reset_simulation()
