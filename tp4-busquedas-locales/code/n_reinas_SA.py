"""
Simulated Annealing para N-reinas con registro opcional de la evolución de H().
"""

import math
import random
from typing import List, Optional, Tuple, Union


class Board:
    """Tablero con representación columna→fila, alineado al resto del TP."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.queens = self.random_start()

    def random_start(self) -> List[int]:
        """Genera un estado inicial aleatorio columna→fila."""
        return [random.randint(0, self.dimension - 1) for _ in range(self.dimension)]

    def fitness(self, queens: List[int]) -> int:
        """Devuelve H(e): cantidad de pares de reinas en conflicto."""
        return self.get_threat(queens)

    def get_threat(self, queens: List[int]) -> int:
        """Cuenta amenazas por filas y diagonales."""
        threats = 0
        n = self.dimension
        for col_a in range(n):
            for col_b in range(col_a + 1, n):
                same_row = queens[col_a] == queens[col_b]
                same_diag = abs(queens[col_a] - queens[col_b]) == abs(col_a - col_b)
                if same_row or same_diag:
                    threats += 1
        return threats

    def random_neighbour(self, actual_board: List[int]) -> Tuple[List[int], int]:
        """Desplaza una reina a otra fila en la misma columna."""
        n = self.dimension
        neighbour = actual_board[:]
        column = random.randrange(n)
        new_row = random.randrange(n)
        while new_row == neighbour[column]:
            new_row = random.randrange(n)
        neighbour[column] = new_row
        return neighbour, self.fitness(neighbour)

    def print_board(self, queens: Optional[List[int]] = None) -> None:
        """Imprime el tablero respetando la representación columna→fila."""
        queens = queens if queens is not None else self.queens
        for row in range(self.dimension):
            line = ["Q" if queens[col] == row else "." for col in range(self.dimension)]
            print(" ".join(line))
        print()


def schedule(iteration: int, T0: float, alpha: float) -> float:
    """Esquema de enfriamiento geométrico T_i = T0 * alpha^i."""
    return T0 * (alpha ** iteration)


def simulated_annealing(
    board: Board,
    T_init: float = 100.0,
    T_min: float = 0.01,
    alpha: float = 0.95,
    max_iters: int = 100_000,
    return_history: bool = False,
) -> Union[Tuple[List[int], int], Tuple[List[int], int, List[int]]]:
    """Optimiza N-reinas mediante Simulated Annealing.

    Parameters
    ----------
    board
        Instancia de `Board` con configuración inicial.
    T_init
        Temperatura inicial del esquema de enfriamiento geométrico.
    T_min
        Temperatura mínima para detener el algoritmo.
    alpha
        Factor de enfriamiento geométrico (0 < alpha < 1).
    max_iters
        Límite de iteraciones independientemente del enfriamiento.
    return_history
        Si es True, devuelve también la serie H(t) del estado actual.

    Returns
    -------
    tuple
        (mejor_solución, mejor_fitness) y opcionalmente history si se solicita.

    Notas
    -----
    Criterios de terminación:
    - Se alcanza solución óptima (H == 0).
    - La temperatura llega a `T_min`.
    - Se ejecutan `max_iters` iteraciones.
    """
    current = board.queens[:]
    current_fit = board.fitness(current)

    best = current[:]
    best_fit = current_fit

    temperature = T_init
    history: List[int] = []

    for iteration in range(max_iters):
        if return_history:
            history.append(current_fit)

        if best_fit == 0:
            break

        if temperature < T_min:
            break

        candidate, cand_fit = board.random_neighbour(current)
        delta = cand_fit - current_fit

        if delta <= 0 or random.random() < math.exp(-delta / temperature):
            current = candidate
            current_fit = cand_fit

            if cand_fit < best_fit:
                best = candidate[:]
                best_fit = cand_fit

        temperature = schedule(iteration + 1, T0=T_init, alpha=alpha)

    if return_history:
        return best, best_fit, history
    return best, best_fit


def main():
    """Ejemplo rápido en consola."""
    random.seed()
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board()
    print("Initial fitness:", board.fitness(board.queens))

    solution, fit, history = simulated_annealing(
        board, return_history=True, max_iters=10_000
    )

    board.queens = solution

    print("Final board:")
    board.print_board()
    print("Fitness achieved:", fit)
    print("History length:", len(history))


if __name__ == "__main__":
    main()
