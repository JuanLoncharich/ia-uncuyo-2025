"""
Modelado y resolución de Sudoku como un problema de satisfacción de restricciones.

Se representa cada celda como una variable con dominio {1, ..., 9} salvo que el
tablero inicial especifique un valor fijo. Las restricciones corresponden a las
filas, columnas y subcuadros 3x3. Se ofrece un solucionador por backtracking
con heurísticas clásicas (MRV + LCV) y soporte opcional de AC-3 como inferencia
en cada paso de la búsqueda.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

Grid = List[List[int]]
Variable = Tuple[int, int]
Assignment = Dict[Variable, int]
Domains = Dict[Variable, Set[int]]


def _default_domain() -> Set[int]:
    """Crea un dominio estándar para una celda vacía."""
    return set(range(1, 10))


@dataclass(frozen=True)
class SudokuCSP:
    """CSP para Sudoku 9x9 con dominios discretos y restricciones binarias."""

    initial_grid: Grid

    def __post_init__(self) -> None:
        self._validate_grid()
        object.__setattr__(self, "variables", [(r, c) for r in range(9) for c in range(9)])
        object.__setattr__(self, "neighbors", self._build_neighbors())
        object.__setattr__(self, "domains", self._build_initial_domains())

    def _validate_grid(self) -> None:
        if len(self.initial_grid) != 9 or any(len(row) != 9 for row in self.initial_grid):
            raise ValueError("El tablero debe ser una matriz 9x9.")
        for row in self.initial_grid:
            for value in row:
                if not (0 <= value <= 9):
                    raise ValueError("Los valores deben estar en el rango 0..9 (0 = vacío).")

    def _build_neighbors(self) -> Dict[Variable, Set[Variable]]:
        neighbors: Dict[Variable, Set[Variable]] = {}
        for r in range(9):
            for c in range(9):
                var = (r, c)
                related: Set[Variable] = set()
                # Misma fila
                related.update((r, cc) for cc in range(9) if cc != c)
                # Misma columna
                related.update((rr, c) for rr in range(9) if rr != r)
                # Mismo subcuadro
                box_r = (r // 3) * 3
                box_c = (c // 3) * 3
                related.update(
                    (rr, cc)
                    for rr in range(box_r, box_r + 3)
                    for cc in range(box_c, box_c + 3)
                    if (rr, cc) != (r, c)
                )
                neighbors[var] = related
        return neighbors

    def _build_initial_domains(self) -> Domains:
        domains: Domains = {}
        for r in range(9):
            for c in range(9):
                value = self.initial_grid[r][c]
                if value == 0:
                    domains[(r, c)] = _default_domain()
                else:
                    domains[(r, c)] = {value}
        return domains

    # ------------------------------------------------------------------ #
    # Consistencia y búsqueda

    def is_consistent(self, var: Variable, value: int, assignment: Assignment) -> bool:
        """Verifica si asignar `value` a `var` viola alguna restricción."""
        for neighbor in self.neighbors[var]:
            if neighbor in assignment and assignment[neighbor] == value:
                return False
        return True

    def select_unassigned_variable(self, assignment: Assignment, domains: Domains) -> Variable:
        """Selecciona la próxima variable sin asignar usando heurística MRV."""
        unassigned = [var for var in self.variables if var not in assignment]
        return min(unassigned, key=lambda var: (len(domains[var]), var[0], var[1]))

    def order_domain_values(
        self, var: Variable, assignment: Assignment, domains: Domains
    ) -> Sequence[int]:
        """Ordena los valores por heurística LCV (menor restricción a vecinos)."""
        def conflicts(value: int) -> int:
            count = 0
            for neighbor in self.neighbors[var]:
                if neighbor in assignment:
                    continue
                count += sum(1 for v in domains[neighbor] if v == value)
            return count

        return sorted(domains[var], key=conflicts)

    # ------------------------------------------------------------------ #
    # AC-3

    def ac3(self, domains: Domains) -> bool:
        """
        Ejecuta AC-3 sobre los dominios.

        Devuelve False si algún dominio queda vacío (inconsistencia).
        """
        queue = deque([(xi, xj) for xi in self.variables for xj in self.neighbors[xi]])
        while queue:
            xi, xj = queue.popleft()
            if self._revise(domains, xi, xj):
                if not domains[xi]:
                    return False
                for xk in self.neighbors[xi] - {xj}:
                    queue.append((xk, xi))
        return True

    def _revise(self, domains: Domains, xi: Variable, xj: Variable) -> bool:
        """Elimina valores inconsistentes del dominio de xi respecto a xj."""
        revised = False
        to_remove: Set[int] = set()
        for x in domains[xi]:
            if not any(x != y for y in domains[xj]):
                to_remove.add(x)
        if to_remove:
            domains[xi] -= to_remove
            revised = True
        return revised

    # ------------------------------------------------------------------ #
    # Búsqueda con backtracking

    def solve(self, use_ac3: bool = True) -> Optional[Grid]:
        """
        Intenta resolver el Sudoku devolviendo una nueva grilla si tiene solución.

        Si `use_ac3` es True, aplica AC-3 como inferencia en cada paso de la
        búsqueda para reducir dominios.
        """
        assignment: Assignment = {
            var: next(iter(domain)) for var, domain in self.domains.items() if len(domain) == 1
        }
        domains = deepcopy(self.domains)
        if use_ac3 and not self.ac3(domains):
            return None
        solution_assignment = self._backtrack(assignment, domains, use_ac3)
        if solution_assignment is None:
            return None
        return self._assignment_to_grid(solution_assignment)

    def _backtrack(
        self,
        assignment: Assignment,
        domains: Domains,
        use_ac3: bool,
    ) -> Optional[Assignment]:
        if len(assignment) == len(self.variables):
            return assignment

        var = self.select_unassigned_variable(assignment, domains)
        for value in self.order_domain_values(var, assignment, domains):
            if not self.is_consistent(var, value, assignment):
                continue
            assignment[var] = value
            saved_domains = deepcopy(domains)
            domains[var] = {value}
            inference_ok = True
            if use_ac3:
                inference_ok = self.ac3(domains)
            if inference_ok:
                result = self._backtrack(assignment, domains, use_ac3)
                if result is not None:
                    return result
            assignment.pop(var, None)
            domains.clear()
            domains.update(saved_domains)
        return None

    def _assignment_to_grid(self, assignment: Assignment) -> Grid:
        grid = [[0] * 9 for _ in range(9)]
        for (r, c), value in assignment.items():
            grid[r][c] = value
        return grid


def _format_grid(grid: Grid) -> str:
    """Devuelve una representación amigable del tablero."""
    lines = []
    for r, row in enumerate(grid):
        if r % 3 == 0 and r != 0:
            lines.append("-" * 21)
        line_parts = []
        for c, value in enumerate(row):
            if c % 3 == 0 and c != 0:
                line_parts.append("|")
            line_parts.append(str(value))
        lines.append(" ".join(line_parts))
    return "\n".join(lines)


def load_grid_from_string(data: str) -> Grid:
    """
    Carga un Sudoku a partir de una cadena de 9 líneas separadas por saltos.

    Se aceptan espacios y ceros como celdas vacías.
    """
    rows = [row.strip().replace(" ", "") for row in data.strip().splitlines() if row.strip()]
    if len(rows) != 9 or any(len(row) != 9 for row in rows):
        raise ValueError("La entrada debe contener 9 filas de 9 caracteres.")
    grid: Grid = []
    for row in rows:
        grid.append([int(ch) for ch in row])
    return grid


if __name__ == "__main__":
    EXAMPLE = """
    530070000
    600195000
    098000060
    800060003
    400803001
    700020006
    060000280
    000419005
    000080079
    """
    puzzle = load_grid_from_string(EXAMPLE)
    csp = SudokuCSP(puzzle)
    solution = csp.solve()
    if solution:
        print("Sudoku resuelto con AC-3 + backtracking:")
        print(_format_grid(solution))
    else:
        print("El Sudoku dado no tiene solución.")
