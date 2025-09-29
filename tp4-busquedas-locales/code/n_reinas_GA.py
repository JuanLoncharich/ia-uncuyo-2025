import random

class Board:
    def __init__(self, dimension):
        self.dimension = dimension
        self.queens = self.random_start()
        self.best_ever = None
        self.best_ever_fitness = float('inf')

    def random_start(self):
        """Genera una permutación aleatoria - sin conflictos de columna"""
        perm = list(range(self.dimension))
        random.shuffle(perm)
        return perm

    def fitness(self, queens):
        return self.get_threat(queens)

    def get_threat(self, queens):
        """Solo cuenta conflictos diagonales (no hay conflictos de columna por construcción)"""
        threats = 0
        for i in range(self.dimension):
            for j in range(i + 1, self.dimension):
                # Solo verificar diagonales
                if abs(queens[i] - queens[j]) == abs(i - j):
                    threats += 1
        return threats
    
    def mutate(self, actual_board):
        """
        Mutación por swap - mantiene la permutación
        Intercambia las posiciones de dos reinas aleatorias
        """
        mutant = actual_board[:]
        i, j = random.sample(range(self.dimension), 2)
        mutant[i], mutant[j] = mutant[j], mutant[i]
        return mutant

    def crossover_pmx(self, parent1, parent2):
        """
        Partially Mapped Crossover (PMX) - preserva permutaciones
        """
        n = self.dimension
        child1 = [-1] * n
        child2 = [-1] * n
        
        # Elegir dos puntos de corte
        cx_point1, cx_point2 = sorted(random.sample(range(n), 2))
        
        # Copiar segmento del medio
        child1[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]
        child2[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]
        
        # Mapear el resto para child1
        for i in range(n):
            if i < cx_point1 or i >= cx_point2:
                # Intentar copiar de parent2
                val = parent2[i]
                while val in child1[cx_point1:cx_point2]:
                    # Valor ya usado, buscar mapeo
                    idx = parent2[cx_point1:cx_point2].index(val)
                    val = parent1[cx_point1 + idx]
                child1[i] = val
        
        # Mapear el resto para child2
        for i in range(n):
            if i < cx_point1 or i >= cx_point2:
                val = parent1[i]
                while val in child2[cx_point1:cx_point2]:
                    idx = parent1[cx_point1:cx_point2].index(val)
                    val = parent2[cx_point1 + idx]
                child2[i] = val
        
        return child1, child2

    def crossover_order(self, parent1, parent2):
        """
        Order Crossover (OX) - más simple y rápido que PMX
        """
        n = self.dimension
        
        # Elegir dos puntos de corte
        cx_point1, cx_point2 = sorted(random.sample(range(n), 2))
        
        # Child 1
        child1 = [-1] * n
        child1[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]
        
        # Llenar el resto con orden de parent2
        ptr = cx_point2
        for i in range(n):
            idx = (cx_point2 + i) % n
            if parent2[idx] not in child1:
                child1[ptr % n] = parent2[idx]
                ptr += 1
        
        # Child 2
        child2 = [-1] * n
        child2[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]
        
        ptr = cx_point2
        for i in range(n):
            idx = (cx_point2 + i) % n
            if parent1[idx] not in child2:
                child2[ptr % n] = parent1[idx]
                ptr += 1
        
        return child1, child2

    def genetic_algorithm(self, population_size=100, generations=1000):
        # Inicializar población (todas permutaciones válidas)
        population = [self.random_start() for _ in range(population_size)]
        
        # Evaluar población inicial y crear pares (individuo, fitness)
        pop_with_fitness = [(ind, self.fitness(ind)) for ind in population]
        
        # Guardar el mejor inicial
        pop_with_fitness.sort(key=lambda x: x[1])
        self.best_ever = pop_with_fitness[0][0][:]
        self.best_ever_fitness = pop_with_fitness[0][1]
        
        for gen in range(generations):
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
                if random.random() < 0.2:
                    # Mutación (20%)
                    parent = random.choice(population[:50])
                    mutant = self.mutate(parent)
                    next_generation.append(mutant)
                else:
                    # Crossover (80%)
                    parent1, parent2 = random.sample(population[:20], 2)
                    child1, child2 = self.crossover_order(parent1, parent2)
                    next_generation.append(child1)
                    if len(next_generation) < population_size:
                        next_generation.append(child2)
            
            # Truncar si nos pasamos
            next_generation = next_generation[:population_size]
            
            # Evaluar SOLO los nuevos individuos (todos menos los 2 elites)
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

    print("Initial board (permutation):")
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