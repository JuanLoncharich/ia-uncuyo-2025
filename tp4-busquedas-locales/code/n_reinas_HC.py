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

    def get_best_neighbour(self, actual_board):
        current_fitness = self.fitness(actual_board)
        best_board = actual_board[:]
        best_fitness = current_fitness

        for row in range(self.dimension):
            original_col = actual_board[row]
            for col in range(self.dimension):
                if col == original_col:
                    continue
                candidate = actual_board[:]
                candidate[row] = col
                cand_fit = self.fitness(candidate)
                if cand_fit < best_fitness:
                    best_fitness = cand_fit
                    best_board = candidate
        return best_board, best_fitness

    def print_board(self, queens):
        for r in range(self.dimension):
            row = ['.'] * self.dimension
            row[queens[r]] = 'Q'
            print(' '.join(row))
        print()

def main():
    dim = 10
    board = Board(dimension=dim)

    print("Initial board:")
    board.print_board(board.queens)

    while True:
        next_board, next_fit = board.get_best_neighbour(board.queens)
        curr_fit = board.fitness(board.queens)

        if next_fit >= curr_fit:
            break

        board.queens = next_board 

    print("Final board:")
    print("Fitness achieved:", board.fitness(board.queens))
    board.print_board(board.queens)

if __name__ == "__main__":
    main()
