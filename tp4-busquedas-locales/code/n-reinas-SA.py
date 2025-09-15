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

def simulated_annealing(board,T_init=None,T_min=1e-3,alpha=0.98,iters_per_T=None,max_iters=100000):
    n = board.dimension
    if T_init is None:
        T_init = float(n)
    if iters_per_T is None:
        iters_per_T = n * n

    current = board.queens[:]
    current_fit = board.fitness(current)

    best = current[:]
    best_fit = current_fit

    T = float(T_init)
    iterations = 0

    while T > T_min and iterations < max_iters and best_fit > 0:
        for _ in range(iters_per_T):
            iterations += 1
            candidate, cand_fit = board.random_neighbour(current)

            delta = cand_fit - current_fit

            if delta <= 0:
                current, current_fit = candidate, cand_fit
                if cand_fit < best_fit:
                    best, best_fit = candidate[:], cand_fit
            else:
                if random.random() < math.exp(-delta / T):
                    current, current_fit = candidate, cand_fit

            if iterations >= max_iters or best_fit == 0:
                break

        T *= alpha

    return best, best_fit

def main():
    random.seed()
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board(board.queens)
    print("Initial fitness:", board.fitness(board.queens))

    solution, fit = simulated_annealing(
        board,
        T_init=dim,
        T_min=1e-3,
        alpha=0.98,
        iters_per_T=dim*dim,
        max_iters=200000
    )

    board.queens = solution

    print("Final board:")
    print("Fitness achieved:", fit)
    board.print_board(board.queens)

if __name__ == "__main__":
    main()
