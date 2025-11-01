"""
Resolución de N-Reinas con verificación anticipada (Forward Checking).

El algoritmo aplica propagación de restricciones al fijar el valor de una
columna, eliminando filas conflictivas en las columnas restantes. Se mantiene
estadística de nodos explorados y tiempo de ejecución para comparar con la
versión de backtracking puro.
"""

from __future__ import annotations

import random
from time import perf_counter
from typing import List, Optional, Sequence, Set

try:
    from .n_reinas_backtracking import NQueensResult
except ImportError:  # Permite ejecución como script local
    from n_reinas_backtracking import NQueensResult  # type: ignore[attr-defined]


def solve_n_queens_forward(n: int, rng: Optional[random.Random] = None) -> NQueensResult:
    """
    Resuelve N-Reinas con forward checking.

    :param n: tamaño del tablero
    :param rng: generador pseudoaleatorio para explorar diversos órdenes
    """
    if n <= 0:
        raise ValueError("n debe ser un entero positivo.")

    rng = rng or random.Random()
    start = perf_counter()
    explored_nodes = 0
    assignment: List[Optional[int]] = [None] * n
    rows_used: Set[int] = set()
    diag1_used: Set[int] = set()
    diag2_used: Set[int] = set()
    solution: Optional[List[int]] = None

    initial_domains: List[Set[int]] = [set(range(n)) for _ in range(n)]

    def propagate(col: int, row: int, domains: List[Set[int]]) -> bool:
        """Actualiza dominios restantes eliminando filas incompatibles."""
        for future_col in range(col + 1, n):
            if assignment[future_col] is not None:
                continue

            remaining = set(domains[future_col])
            distance = future_col - col
            to_remove = {row, row + distance, row - distance}
            remaining -= {value for value in to_remove if 0 <= value < n}

            if remaining != domains[future_col]:
                domains[future_col] = remaining

            if not remaining:
                return False
        return True

    def forward(col: int, domains: List[Set[int]]) -> bool:
        nonlocal explored_nodes, solution
        explored_nodes += 1
        if col == n:
            solution = [row for row in assignment if row is not None]
            return True

        values: Sequence[int] = list(domains[col])
        if not values:
            return False
        values = rng.sample(values, k=len(values))

        for row in values:
            if row in rows_used:
                continue
            if (row - col) in diag1_used or (row + col) in diag2_used:
                continue

            assignment[col] = row
            rows_used.add(row)
            diag1_used.add(row - col)
            diag2_used.add(row + col)

            new_domains = [set(domain) for domain in domains]
            new_domains[col] = {row}

            if propagate(col, row, new_domains) and forward(col + 1, new_domains):
                return True

            assignment[col] = None
            rows_used.remove(row)
            diag1_used.remove(row - col)
            diag2_used.remove(row + col)

        return False

    found = forward(0, initial_domains)
    elapsed = perf_counter() - start
    return NQueensResult(
        found_solution=found,
        solution=solution,
        explored_nodes=explored_nodes,
        time=elapsed,
    )


if __name__ == "__main__":
    rng = random.Random(123)
    result = solve_n_queens_forward(8, rng=rng)
    print(f"Solución encontrada: {result.found_solution}")
    print(f"Nodos explorados: {result.explored_nodes}")
    print(f"Tiempo: {result.time:.6f}s")
    if result.solution:
        print("Columna -> fila:")
        print(result.solution)
