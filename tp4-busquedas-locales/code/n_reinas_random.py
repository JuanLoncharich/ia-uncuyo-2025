"""
Búsqueda aleatoria para N-reinas (baseline).
"""

import random
from typing import List, Optional, Tuple


class Board:
    """Tablero con representación columna→fila, consistente con el TP."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.queens = self.random_start()

    def random_start(self) -> List[int]:
        """Estado aleatorio columna→fila."""
        return [random.randint(0, self.dimension - 1) for _ in range(self.dimension)]

    def fitness(self, queens: List[int]) -> int:
        """Cantidad de pares de reinas amenazadas (H)."""
        return self.get_threat(queens)

    def get_threat(self, queens: List[int]) -> int:
        """Evalúa conflictos por fila y diagonal."""
        threats = 0
        for col_a in range(self.dimension):
            for col_b in range(col_a + 1, self.dimension):
                same_row = queens[col_a] == queens[col_b]
                same_diag = abs(queens[col_a] - queens[col_b]) == abs(col_a - col_b)
                if same_row or same_diag:
                    threats += 1
        return threats


def random_search(
    board: Board,
    max_evals: Optional[int] = None,
    return_history: bool = False,
) -> Tuple[List[int], int, List[int]]:
    """Explora estados al azar conservando el mejor encontrado.

    Parameters
    ----------
    board
        Instancia de `Board` con estado inicial.
    max_evals
        Límite de evaluaciones permitidas.
    return_history
        Si es True, devuelve la evolución del mejor H observado.
    """
    best = board.queens[:]
    best_H = board.fitness(best)
    history: List[int] = [best_H] if return_history else []

    evaluations = 1
    while best_H != 0 and (max_evals is None or evaluations < max_evals):
        candidate = board.random_start()
        cand_H = board.fitness(candidate)
        evaluations += 1
        if cand_H < best_H:
            best = candidate[:]
            best_H = cand_H
        if return_history:
            history.append(best_H)

    return best, best_H, history
