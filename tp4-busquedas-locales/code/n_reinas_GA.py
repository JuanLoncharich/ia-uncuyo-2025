import random

class Board:
    def __init__(self, dimension):
        self.dimension = dimension
        self.queens = self.random_start()
        self.best_ever = None  # Guardar la mejor solución encontrada
        self.best_ever_fitness = float('inf')

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
        for i in range(self.dimension):
            if random.random() < 0.5:
                child1.append(board1[i])
                child2.append(board2[i])
            else:
                child1.append(board2[i])
                child2.append(board1[i])
        return child1, child2

    def genetic_algorithm(self, population_size=100, generations=1000):
        # Inicializar población y evaluar
        population = [self.random_start() for _ in range(population_size)]
        fitness_cache = {tuple(ind): self.fitness(ind) for ind in population}
        
        # Guardar el mejor inicial
        best_ind = min(population, key=lambda x: fitness_cache[tuple(x)])
        self.best_ever = best_ind[:]
        self.best_ever_fitness = fitness_cache[tuple(best_ind)]
        
        for gen in range(generations):
            # Ordenar usando el cache (sin llamar a fitness extra)
            population = sorted(population, key=lambda x: fitness_cache[tuple(x)])
            
            # Actualizar mejor global si hay mejora
            if fitness_cache[tuple(population[0])] < self.best_ever_fitness:
                self.best_ever = population[0][:]
                self.best_ever_fitness = fitness_cache[tuple(population[0])]
            
            # Si encontramos solución óptima, terminar
            if self.best_ever_fitness == 0:
                break
            
            # Elitismo: mantener los 2 mejores
            next_generation = population[:2]
            
            # Generar nueva población
            while len(next_generation) < population_size:
                if random.random() < 0.3:
                    # Mutación
                    mutant, mutant_fit = self.mutate(random.choice(population))
                    next_generation.append(mutant)
                    fitness_cache[tuple(mutant)] = mutant_fit
                else:
                    # Crossover
                    parent1, parent2 = random.choices(population[:20], k=2)
                    child1, child2 = self.crossover(parent1, parent2)
                    next_generation.extend([child1, child2])
                    # Evaluar hijos
                    fitness_cache[tuple(child1)] = self.fitness(child1)
                    fitness_cache[tuple(child2)] = self.fitness(child2)
            
            # Truncar si nos pasamos
            population = next_generation[:population_size]
        
        # Retornar la mejor solución encontrada en TODAS las generaciones
        return self.best_ever
    
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