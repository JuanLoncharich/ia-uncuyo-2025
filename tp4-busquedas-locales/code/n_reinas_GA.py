"""
Algoritmo genético para N-reinas con operadores crossover/mutación clásicos.
"""

import random
from typing import List, Optional, Tuple, Union


class Board:
    """Tablero de N-reinas con individuos representados como permutaciones."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.queens = self.random_start()
        self.best_ever: Optional[List[int]] = None
        self.best_ever_fitness = float("inf")

    def random_start(self) -> List[int]:
        """Genera una permutación aleatoria sin conflictos de columna."""
        perm = list(range(self.dimension))
        random.shuffle(perm)
        return perm

    def fitness(self, queens: List[int]) -> int:
        """Calcula H(e) como número de conflictos diagonales."""
        return self.get_threat(queens)

    def get_threat(self, queens: List[int]) -> int:
        """Sólo hay que contemplar diagonales: no existen conflictos de columna."""
        threats = 0
        for col_a in range(self.dimension):
            for col_b in range(col_a + 1, self.dimension):
                if abs(queens[col_a] - queens[col_b]) == abs(col_a - col_b):
                    threats += 1
        return threats

    def mutate(self, actual_board: List[int]) -> List[int]:
        """Mutación por swap simple; mantiene la permutación válida."""
        mutant = actual_board[:]
        i, j = random.sample(range(self.dimension), 2)
        mutant[i], mutant[j] = mutant[j], mutant[i]
        return mutant

    def crossover_pmx(
        self, parent1: List[int], parent2: List[int]
    ) -> Tuple[List[int], List[int]]:
        """Partially Mapped Crossover (PMX), preserva la estructura de permutación."""
        n = self.dimension
        child1 = [-1] * n
        child2 = [-1] * n

        cx_point1, cx_point2 = sorted(random.sample(range(n), 2))

        child1[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]
        child2[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]

        for i in range(n):
            if i < cx_point1 or i >= cx_point2:
                val = parent2[i]
                while val in child1[cx_point1:cx_point2]:
                    idx = parent2[cx_point1:cx_point2].index(val)
                    val = parent1[cx_point1 + idx]
                child1[i] = val

        for i in range(n):
            if i < cx_point1 or i >= cx_point2:
                val = parent1[i]
                while val in child2[cx_point1:cx_point2]:
                    idx = parent1[cx_point1:cx_point2].index(val)
                    val = parent2[cx_point1 + idx]
                child2[i] = val

        return child1, child2

    def crossover_order(
        self, parent1: List[int], parent2: List[int]
    ) -> Tuple[List[int], List[int]]:
        """Order Crossover (OX), alternativa más simple y rápida que PMX."""
        n = self.dimension

        cx_point1, cx_point2 = sorted(random.sample(range(n), 2))

        child1 = [-1] * n
        child1[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]

        ptr = cx_point2
        for i in range(n):
            idx = (cx_point2 + i) % n
            if parent2[idx] not in child1:
                child1[ptr % n] = parent2[idx]
                ptr += 1

        child2 = [-1] * n
        child2[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]

        ptr = cx_point2
        for i in range(n):
            idx = (cx_point2 + i) % n
            if parent1[idx] not in child2:
                child2[ptr % n] = parent1[idx]
                ptr += 1

        return child1, child2

    def genetic_algorithm(
        self,
        population_size: int = 100,
        generations: int = 1000,
        return_history: bool = False,
    ) -> Union[List[int], Tuple[List[int], List[int]]]:
        """Ejecuta el GA con selección por truncamiento/elitismo.

        Selección:
            Se ordena la población por fitness y se toman los mejores (`top-k`)
            para cruzamiento (top-20) y mutación (top-50). Este esquema de
            truncamiento puede reemplazarse fácilmente por ruleta, torneo u otra
            estrategia en futuras iteraciones.

        Reemplazo:
            Elitismo explícito: los 2 mejores se copian sin modificaciones.
            El resto se genera por crossover (80 %) o mutación (20 %).
        """
        population = [self.random_start() for _ in range(population_size)]

        pop_with_fitness = [(ind, self.fitness(ind)) for ind in population]

        pop_with_fitness.sort(key=lambda x: x[1])
        self.best_ever = pop_with_fitness[0][0][:]
        self.best_ever_fitness = pop_with_fitness[0][1]

        history: List[int] = [self.best_ever_fitness]

        for _ in range(generations):
            if pop_with_fitness[0][1] < self.best_ever_fitness:
                self.best_ever = pop_with_fitness[0][0][:]
                self.best_ever_fitness = pop_with_fitness[0][1]

            if self.best_ever_fitness == 0:
                history.append(0)
                break

            population = [ind for ind, _ in pop_with_fitness]

            next_generation = [population[0][:], population[1][:]]

            while len(next_generation) < population_size:
                if random.random() < 0.2:
                    parent = random.choice(population[: min(50, len(population))])
                    mutant = self.mutate(parent)
                    next_generation.append(mutant)
                else:
                    sample_pool = population[: min(20, len(population))]
                    parent1, parent2 = random.sample(sample_pool, 2)
                    child1, child2 = self.crossover_order(parent1, parent2)
                    next_generation.append(child1)
                    if len(next_generation) < population_size:
                        next_generation.append(child2)

            next_generation = next_generation[:population_size]

            pop_with_fitness = [
                (next_generation[0], pop_with_fitness[0][1]),
                (next_generation[1], pop_with_fitness[1][1]),
            ]

            for i in range(2, len(next_generation)):
                fit = self.fitness(next_generation[i])
                pop_with_fitness.append((next_generation[i], fit))

            pop_with_fitness.sort(key=lambda x: x[1])
            history.append(pop_with_fitness[0][1])

            if pop_with_fitness[0][1] == 0:
                break

        best_solution = self.best_ever[:] if self.best_ever else population[0][:]
        if return_history:
            return best_solution, history
        return best_solution

    def print_board(self, queens: Optional[List[int]] = None) -> None:
        """Imprime la configuración en consola."""
        queens = queens if queens is not None else self.queens
        for row in range(self.dimension):
            line = ["Q" if queens[col] == row else "." for col in range(self.dimension)]
            print(" ".join(line))
        print()


def main():
    """Pequeña demo del GA."""
    dim = 10
    board = Board(dimension=dim)

    print("Initial board (permutation):")
    board.print_board()
    print("Initial fitness:", board.fitness(board.queens))

    solution, history = board.genetic_algorithm(
        population_size=200,
        generations=500,
        return_history=True,
    )

    board.queens = solution

    print("Final board:")
    board.print_board()
    print("Final fitness:", board.fitness(board.queens))
    print("History length:", len(history))


if __name__ == "__main__":
    main()
