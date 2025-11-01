"""
Resolución del problema de N-Reinas mediante backtracking clásico.

Cada columna representa una variable cuyo dominio es {0, ..., N-1} (filas).
Se emplean estructuras auxiliares para verificar rápidamente filas y diagonales
ocupadas. El orden de evaluación de las filas se randomiza para obtener
diversidad en los experimentos.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from time import perf_counter
from typing import List, Optional


@dataclass
class NQueensResult:
    found_solution: bool
    solution: Optional[List[int]]
    explored_nodes: int
    time: float


def solve_n_queens_backtracking(n: int, rng: Optional[random.Random] = None) -> NQueensResult:
    """
    Resuelve N-Reinas con backtracking.

    :param n: cantidad de reinas
    :param rng: generador para randomizar el orden de los dominios
    """
    if n <= 0:
        raise ValueError("n debe ser un entero positivo.")

    rng = rng or random.Random()
    start = perf_counter()
    explored_nodes = 0
    solution: Optional[List[int]] = None

    assignment: List[Optional[int]] = [None] * n
    rows_used = set()
    diag1_used = set()  # r - c
    diag2_used = set()  # r + c

    def backtrack(col: int) -> bool:
        nonlocal explored_nodes, solution
        explored_nodes += 1
        if col == n:
            solution = [row for row in assignment if row is not None]
            return True

        candidates = list(range(n))
        rng.shuffle(candidates)
        for row in candidates:
            if row in rows_used:
                continue
            if (row - col) in diag1_used or (row + col) in diag2_used:
                continue

            assignment[col] = row
            rows_used.add(row)
            diag1_used.add(row - col)
            diag2_used.add(row + col)

            if backtrack(col + 1):
                return True

            assignment[col] = None
            rows_used.remove(row)
            diag1_used.remove(row - col)
            diag2_used.remove(row + col)

        return False

    found = backtrack(0)
    elapsed = perf_counter() - start
    return NQueensResult(
        found_solution=found,
        solution=solution,
        explored_nodes=explored_nodes,
        time=elapsed,
    )


if __name__ == "__main__":
    rng = random.Random(42)
    result = solve_n_queens_backtracking(8, rng=rng)
    print(f"Solución encontrada: {result.found_solution}")
    print(f"Nodos explorados: {result.explored_nodes}")
    print(f"Tiempo: {result.time:.6f}s")
    if result.solution:
        print("Representación columna -> fila:")
        print(result.solution)
