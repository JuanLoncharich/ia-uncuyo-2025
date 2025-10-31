import random
from typing import List, Optional, Tuple


class Board:
    """Tablero de N-reinas con representación columna→fila.

    Cada índice de `queens` refiere a una columna y su valor indica la fila
    donde se ubica la reina. De este modo no hay conflictos de columna y el
    cálculo de amenazas se limita a filas y diagonales.
    """

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.queens = self.random_start()

    def random_start(self) -> List[int]:
        """Genera una configuración aleatoria columna→fila."""
        return [random.randint(0, self.dimension - 1) for _ in range(self.dimension)]

    def fitness(self, queens: List[int]) -> int:
        """Evalúa la cantidad de pares de reinas amenazadas."""
        return self.get_threat(queens)

    def get_threat(self, queens: List[int]) -> int:
        """Cuenta amenazas por fila o diagonal."""
        threats = 0
        for col_a in range(self.dimension):
            for col_b in range(col_a + 1, self.dimension):
                same_row = queens[col_a] == queens[col_b]
                same_diag = abs(queens[col_a] - queens[col_b]) == abs(col_a - col_b)
                if same_row or same_diag:
                    threats += 1
        return threats

    def get_best_neighbour(self, actual_board: List[int]) -> Tuple[List[int], int]:
        """Busca el vecino con menor H moviendo una reina de columna."""
        current_fitness = self.fitness(actual_board)
        best_board = actual_board[:]
        best_fitness = current_fitness

        for column in range(self.dimension):
            original_row = actual_board[column]
            for candidate_row in range(self.dimension):
                if candidate_row == original_row:
                    continue
                candidate = actual_board[:]
                candidate[column] = candidate_row
                cand_fit = self.fitness(candidate)
                if cand_fit < best_fitness:
                    best_fitness = cand_fit
                    best_board = candidate
        return best_board, best_fitness

    def print_board(self, queens: Optional[List[int]] = None) -> None:
        """Imprime el tablero usando la convención columna→fila."""
        queens = queens if queens is not None else self.queens
        for row in range(self.dimension):
            line = ["Q" if queens[col] == row else "." for col in range(self.dimension)]
            print(" ".join(line))
        print()


def hill_climbing(
    board: Board,
    max_steps: Optional[int] = None,
    return_history: bool = False,
) -> Tuple[List[int], List[int]]:
    """Ejecuta Hill Climbing canónico sobre un tablero.

    Parameters
    ----------
    board:
        Instancia ya inicializada de `Board`.
    max_steps:
        Límite duro de iteraciones de escalada (None = sin límite).
    return_history:
        Si es True, devuelve además la serie H(t) por iteración.

    Returns
    -------
    tuple
        (mejor_solución, historia_de_H) cuando `return_history=True`,
        o (mejor_solución, []) en caso contrario.
    """
    history: List[int] = []
    steps = 0

    while True:
        current_fit = board.fitness(board.queens)
        if return_history:
            history.append(current_fit)

        next_board, next_fit = board.get_best_neighbour(board.queens)
        if next_fit >= current_fit:
            break

        board.queens = next_board
        steps += 1

        if return_history:
            history.append(next_fit)

        if next_fit == 0:
            break
        if max_steps is not None and steps >= max_steps:
            break

    return board.queens[:], history


def main():
    """Pequeña demo con N=10."""
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board()

    solution, history = hill_climbing(board, return_history=True)

    print("Final board:")
    board.print_board(solution)
    print("Fitness achieved:", board.fitness(solution))
    print("History:", history)


if __name__ == "__main__":
    main()
