import random

class Board:
    def __init__(self, dimension):
        self.dimension = dimension
        self.queens = self.random_start()

    def random_start(self):
        return [random.randint(0, self.dimension - 1) for _ in range(self.dimension)]

    def fitness(self, queens):
        return self.get_threat(queens)

    def get_threat(self, queens):
        threats = 0
        for i in range(self.dimension):
            for j in range(i + 1, self.dimension):
                same_col = (queens[i] == queens[j])
                same_diag = abs(queens[i] - queens[j]) == abs(i - j)
                if same_col or same_diag:
                    threats += 1
        return threats
    
    def mutate(self, actual_board):
        n = self.dimension
        mutant = actual_board[:]

        i, j = random.sample(range(n), 2)

        mutant[i], mutant[j] = mutant[j], mutant[i]

        return mutant, self.fitness(mutant)


    def crossover(self, board1, board2):
        child1 = []
        child2 = []
        n = self.dimension
        point = random.randint(1, n - 1)
        for i in range(self.dimension):
            if random.random() < 0.5:
                child1.append(board1[i])
                child2.append(board2[i])
            else:
                child1.append(board2[i])
                child2.append(board1[i])

        return child1, child2

    def genetic_algorithm(self, population_size=100, generations=1000):
        population = [self.random_start() for _ in range(population_size)]
        for _ in range(generations):
            population = sorted(population, key=self.fitness)
            next_generation = population[:2]
            while len(next_generation) < population_size:
                if random.random() < 0.3:
                    mutant, _ = self.mutate(random.choice(population))
                    next_generation.append(mutant)
                parent1, parent2 = random.choices(population[:20], k=2)
                child1, child2 = self.crossover(parent1, parent2)
                next_generation.extend([child1, child2])
            population = next_generation
        return min(population, key=self.fitness)
    
    def print_board(self, queens):
        for i in range(self.dimension):
            row = ['Q' if col == queens[i] else '.' for col in range(self.dimension)]
            print(' '.join(row))
        print()

def main():
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board(board.queens)
    print("Initial fitness:", board.fitness(board.queens))

    solution = board.genetic_algorithm(
        population_size=200,
        generations=500
    )

    board.queens = solution

    print("Final board:")
    board.print_board(board.queens)
    print("Final fitness:", board.fitness(board.queens))

if __name__ == "__main__":
    main()
