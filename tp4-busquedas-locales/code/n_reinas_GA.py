import random

class Board:
    def __init__(self, dimension):
        self.dimension = dimension
        self.queens = self.random_start()
        self.best_ever = None
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
        """
        Mutación por swap de posiciones (mantiene permutación)
        Intercambia las posiciones de dos reinas aleatorias
        """
        n = self.dimension
        mutant = actual_board[:]
        i, j = random.sample(range(n), 2)
        mutant[i], mutant[j] = mutant[j], mutant[i]
        return mutant

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
        # Inicializar población
        population = [self.random_start() for _ in range(population_size)]
        
        # Evaluar población inicial y crear pares (individuo, fitness)
        pop_with_fitness = [(ind, self.fitness(ind)) for ind in population]
        
        # Guardar el mejor inicial
        pop_with_fitness.sort(key=lambda x: x[1])
        self.best_ever = pop_with_fitness[0][0][:]
        self.best_ever_fitness = pop_with_fitness[0][1]
        
        for gen in range(generations):
            # Ya tenemos la población ordenada por fitness
            
            # Actualizar mejor global
            if pop_with_fitness[0][1] < self.best_ever_fitness:
                self.best_ever = pop_with_fitness[0][0][:]
                self.best_ever_fitness = pop_with_fitness[0][1]
            
            # Si encontramos solución óptima, terminar
            if self.best_ever_fitness == 0:
                break
            
            # Extraer solo los individuos (sin fitness) para trabajar
            population = [ind for ind, fit in pop_with_fitness]
            
            # Elitismo: mantener los 2 mejores
            next_generation = [population[0][:], population[1][:]]
            
            # Generar nueva población
            while len(next_generation) < population_size:
                if random.random() < 0.3:
                    # Mutación
                    parent = random.choice(population[:50])  # De los mejores 50
                    mutant = self.mutate(parent)
                    next_generation.append(mutant)
                else:
                    # Crossover
                    parent1, parent2 = random.sample(population[:20], 2)
                    child1, child2 = self.crossover(parent1, parent2)
                    next_generation.append(child1)
                    if len(next_generation) < population_size:
                        next_generation.append(child2)
            
            # Truncar si nos pasamos
            next_generation = next_generation[:population_size]
            
            # Evaluar SOLO los nuevos individuos (todos menos los 2 elites)
            # Los elites ya tienen su fitness conocido
            pop_with_fitness = [
                (next_generation[0], pop_with_fitness[0][1]),  # Elite 1
                (next_generation[1], pop_with_fitness[1][1])   # Elite 2
            ]
            
            # Evaluar el resto
            for i in range(2, len(next_generation)):
                fit = self.fitness(next_generation[i])
                pop_with_fitness.append((next_generation[i], fit))
            
            # Ordenar para la siguiente generación
            pop_with_fitness.sort(key=lambda x: x[1])
        
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