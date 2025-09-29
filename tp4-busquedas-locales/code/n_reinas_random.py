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