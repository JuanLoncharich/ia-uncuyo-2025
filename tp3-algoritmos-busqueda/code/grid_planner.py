# grid_planner.py
from __future__ import annotations
from collections import deque
from heapq import heappush, heappop
from typing import Dict, Iterable, List, Optional, Tuple

# Acciones: 0=LEFT, 1=DOWN, 2=RIGHT, 3=UP
ACTION_FROM_DELTA = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}
DELTAS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
ACTION_TO_DELTA = {
    0: (0, -1),  # LEFT
    1: (1, 0),   # DOWN
    2: (0, 1),   # RIGHT
    3: (-1, 0),  # UP
}

Coord = Tuple[int, int]


class GridPlanner:
    """
    Utilidad sobre 'desc' de FrozenLake (determinista).
    Expone: parseo, vecinos, y búsquedas clásicas (BFS, DFS, DLS, UCS, A*).
    """

    def __init__(self, desc):
        self.grid, self.n, self.start, self.goal = self._parse_desc(desc)
        self.last_expanded: int = 0

    @staticmethod
    def _parse_desc(desc) -> Tuple[List[str], int, Coord, Coord]:
        """
        Soporta:
          - List[str]                             e.g. ["SFFF","FHFH",...]
          - List[bytes]                           e.g. [b"SFFF", b"FHFH", ...]
          - List[List[bytes|str]]                 e.g. [[b"S",b"F",...], ...]
          - np.ndarray shape (n,n) dtype 'S1'/'<U1' u object
        """
        grid: List[str] = []

        for row in desc:
            # Caso 1: la fila ya es una string o bytes de longitud n
            if isinstance(row, (str, bytes, bytearray)):
                s = row.decode("utf-8") if isinstance(row, (bytes, bytearray)) else row
                grid.append(s)
                continue

            # Caso 2: la fila es iterable de caracteres (lista/tupla/ndarray)
            try:
                chars = []
                for ch in row:
                    if isinstance(ch, (bytes, bytearray)):
                        chars.append(ch.decode("utf-8"))
                    else:
                        # ch puede ser np.str_, str, o incluso un escalar numpy
                        chars.append(str(ch))
                grid.append("".join(chars))
            except TypeError:
                # No iterable: formato inesperado
                raise TypeError(f"Fila de 'desc' con tipo no soportado: {type(row)}")

        n = len(grid)
        start = goal = None
        for r in range(n):
            for c in range(len(grid[r])):
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

    # --------------------- Búsquedas no informadas ---------------------

    def bfs(self) -> Optional[List[int]]:
        self.last_expanded = 0
        q = deque([self.start])
        visited = {self.start}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        while q:
            u = q.popleft()
            self.last_expanded += 1
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                if v not in visited:
                    visited.add(v)
                    parents[v] = (u, delta)
                    q.append(v)
        return None

    def dfs(self) -> Optional[List[int]]:
        self.last_expanded = 0
        stack = [self.start]
        visited = {self.start}
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        while stack:
            u = stack.pop()
            self.last_expanded += 1
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
        self.last_expanded = 0
        parents: Dict[Coord, Tuple[Coord, Tuple[int, int]]] = {}
        visited_depth: Dict[Coord, int] = {self.start: 0}
        stack: List[Tuple[Coord, int]] = [(self.start, 0)]

        while stack:
            u, depth = stack.pop()
            self.last_expanded += 1
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

    def ucs(self, step_cost=None) -> Optional[List[int]]:
        """
        Búsqueda de costo uniforme.
        - step_cost(delta) -> costo de un paso (por defecto 1 por movimiento)
        """
        self.last_expanded = 0
        if step_cost is None:
            step_cost = lambda delta: 1

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
            self.last_expanded += 1
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                new_cost = cost + step_cost(delta)
                if v not in g or new_cost < g[v]:
                    g[v] = new_cost
                    parents[v] = (u, delta)
                    heappush(pq, (new_cost, v))
        return None

    # --------------------- A* ---------------------

    @staticmethod
    def manhattan(a: Coord, b: Coord) -> int:
        """Heurística admisible y consistente en grid 4-conexo con costos unitarios."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def astar(self, heuristic=None, step_cost=None) -> Optional[List[int]]:
        self.last_expanded = 0
        if heuristic is None:
            heuristic = lambda rc: self.manhattan(rc, self.goal)
        if step_cost is None:
            step_cost = lambda delta: 1

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
            self.last_expanded += 1
            if u == self.goal:
                return self.reconstruct_actions(parents, self.start, self.goal)
            for v, delta in self.neighbors(u):
                tentative_g = g[u] + step_cost(delta)
                if v not in g or tentative_g < g[v]:
                    g[v] = tentative_g
                    parents[v] = (u, delta)
                    heappush(pq, (tentative_g + heuristic(v), tiebreak, v))
                    tiebreak += 1
        return None

    # --------------------- Heurísticas útiles ---------------------

    @staticmethod
    def weighted_manhattan(a: Coord, b: Coord, w_row: int, w_col: int) -> int:
        """
        Variante de Manhattan con pesos distintos por eje.
        - w_row: costo por moverse verticalmente (arriba/abajo)
        - w_col: costo por moverse horizontalmente (izquierda/derecha)
        """
        return abs(a[0] - b[0]) * w_row + abs(a[1] - b[1]) * w_col

    # --------------------- Utilidades ---------------------

    def states_from_actions(self, actions: List[int]) -> List[Coord]:
        """Reconstruye la secuencia de estados (incluye el inicial) aplicando acciones en la grilla."""
        path = [self.start]
        r, c = self.start
        for a in actions:
            dr, dc = ACTION_TO_DELTA.get(a, (0, 0))
            nr, nc = r + dr, c + dc
            path.append((nr, nc))
            r, c = nr, nc
        return path
