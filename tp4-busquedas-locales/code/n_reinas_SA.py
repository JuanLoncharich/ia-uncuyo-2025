import random
import math

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
        n = self.dimension
        for i in range(n):
            for j in range(i + 1, n):
                same_col = (queens[i] == queens[j])
                same_diag = abs(queens[i] - queens[j]) == abs(i - j)
                if same_col or same_diag:
                    threats += 1
        return threats

    def random_neighbour(self, actual_board):
        n = self.dimension
        neighbour = actual_board[:]
        row = random.randrange(n)
        new_col = random.randrange(n)
        while new_col == neighbour[row]:
            new_col = random.randrange(n)
        neighbour[row] = new_col
        return neighbour, self.fitness(neighbour)

    def print_board(self, queens):
        for i in range(self.dimension):
            row = ['.'] * self.dimension
            row[queens[i]] = 'Q'
            print(' '.join(row))
        print()

def simulated_annealing(board, T_init=100, T_min=0.01, alpha=0.95, max_iters=100000):
    current = board.queens[:]
    current_fit = board.fitness(current)
    
    best = current[:]
    best_fit = current_fit
    
    T = T_init
    
    for _ in range(max_iters):
        if best_fit == 0:
            break
            
        candidate, cand_fit = board.random_neighbour(current)
        delta = cand_fit - current_fit
        
        if delta <= 0 or random.random() < math.exp(-delta / T):
            current = candidate
            current_fit = cand_fit
            
            if cand_fit < best_fit:
                best = candidate[:]
                best_fit = cand_fit
        
        T *= alpha
        
        if T < T_min:
            break
    
    return best, best_fit

def main():
    random.seed()
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board(board.queens)
    print("Initial fitness:", board.fitness(board.queens))

    solution, fit = simulated_annealing(board)

    board.queens = solution

    print("Final board:")
    print("Fitness achieved:", fit)
    board.print_board(board.queens)

if __name__ == "__main__":
    main()