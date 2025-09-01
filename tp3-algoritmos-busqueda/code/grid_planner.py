# grid_planner.py
from __future__ import annotations
from collections import deque
from heapq import heappush, heappop
from typing import Dict, Iterable, List, Optional, Tuple

# Acciones: 0=LEFT, 1=DOWN, 2=RIGHT, 3=UP
ACTION_FROM_DELTA = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}
DELTAS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DEFAULT_ACTION_COSTS = {delta: 1 for delta in DELTAS}

Coord = Tuple[int, int]


class GridPlanner:
    """
    Utilidad sobre 'desc' de FrozenLake (determinista).
    Expone: parseo, vecinos, y búsquedas clásicas (BFS, DFS, DLS, UCS, A*).
    """

    def __init__(self, desc, action_costs: Optional[Dict[Tuple[int, int], int]] = None):
        self.grid, self.n, self.start, self.goal = self._parse_desc(desc)
        self.action_costs = action_costs or DEFAULT_ACTION_COSTS

    @staticmethod
    def _parse_desc(desc) -> Tuple[List[str], int, Coord, Coord]:
        grid = [row.decode("utf-8") if not isinstance(row, str) else row for row in desc]
        n = len(grid)
        start = goal = None
        for r in range(n):
            for c in range(n):
                ch = grid[r][c]
                if ch == "S":
                    start = (r, c)
                elif ch == "G":
                    goal = (r, c)
        if start is None or goal is None:
            raise ValueError("El mapa debe contener 'S' (inicio) y 'G' (objetivo).")
        return grid, n, start, goal

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n

    def neighbors(self, rc: Coord) -> Iterable[Tuple[Coord, Tuple[int, int]]]:
        """Vecinos válidos evitando agujeros 'H'."""
        r, c = rc
        for dr, dc in DELTAS:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc) and self.grid[nr][nc] != "H":
                yield (nr, nc), (dr, dc)

    @staticmethod
    def reconstruct_actions(parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]],
                            start: Coord, goal: Coord) -> List[int]:
        actions: List[int] = []
        cur = goal
        while cur != start:
            prev, delta = parents[cur]
            actions.append(ACTION_FROM_DELTA[delta])
            cur = prev
        actions.reverse()
        return actions

    def step_cost(self, delta: Tuple[int, int]) -> int:
        return self.action_costs.get(delta, 1)

    # --------------------- Búsquedas no informadas ---------------------

    def bfs(self) -> Optional[List[int]]:
        q = deque([self.start])
        visited = {self.start}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        while q:
            u = q.popleft()
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                if v not in visited:
                    visited.add(v)
                    parents[v] = (u, delta)
                    q.append(v)
        return None

    def dfs(self) -> Optional[List[int]]:
        stack = [self.start]
        visited = {self.start}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        while stack:
            u = stack.pop()
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                if v not in visited:
                    visited.add(v)
                    parents[v] = (u, delta)
                    stack.append(v)
        return None

    def dls(self, limit: int) -> Optional[List[int]]:
        """Búsqueda por profundidad limitada."""
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        visited_depth: Dict[Coord, int] = {self.start: 0}
        stack: List[Tuple[Coord, int]] = [(self.start, 0)]

        while stack:
            u, depth = stack.pop()
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            if depth == limit:
                continue
            for v, delta in self.neighbors(u):
                nd = depth + 1
                if v not in visited_depth or nd < visited_depth[v]:
                    visited_depth[v] = nd
                    parents[v] = (u, delta)
                    stack.append((v, nd))
        return None

    # --------------------- Búsquedas con costo ---------------------

    def ucs(self) -> Optional[List[int]]:
        """Costo uniforme con costos unitarios por paso."""
        g: Dict[Coord, int] = {self.start: 0}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        pq: List[Tuple[int, Coord]] = []
        heappush(pq, (0, self.start))
        closed = set()

        while pq:
            cost, u = heappop(pq)
            if u in closed:
                continue
            closed.add(u)
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                step_c = self.step_cost(delta)
                new_cost = cost + step_c
                if v not in g or new_cost < g[v]:
                    g[v] = new_cost
                    parents[v] = (u, delta)
                    heappush(pq, (new_cost, v))
        return None

    # --------------------- A* ---------------------

    def manhattan(self, a: Coord, b: Coord) -> int:
        """Heurística admisible para costos diferenciados por eje."""
        vert = min(self.action_costs.get((1, 0), 1), self.action_costs.get((-1, 0), 1))
        hor = min(self.action_costs.get((0, 1), 1), self.action_costs.get((0, -1), 1))
        return abs(a[0] - b[0]) * vert + abs(a[1] - b[1]) * hor

    def astar(self, heuristic=None) -> Optional[List[int]]:
        if heuristic is None:
            heuristic = lambda rc: self.manhattan(rc, self.goal)

        g: Dict[Coord, int] = {self.start: 0}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        pq: List[Tuple[int, int, Coord]] = []
        heappush(pq, (heuristic(self.start), 0, self.start))
        tiebreak = 1
        closed = set()

        while pq:
            f, _, u = heappop(pq)
            if u in closed:
                continue
            closed.add(u)
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                step_c = self.step_cost(delta)
                tentative_g = g[u] + step_c
                if v not in g or tentative_g < g[v]:
                    g[v] = tentative_g
                    parents[v] = (u, delta)
                    heappush(pq, (tentative_g + heuristic(v), tiebreak, v))
                    tiebreak += 1
        return None
