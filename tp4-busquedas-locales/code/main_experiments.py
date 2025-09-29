import n_reinas_GA as ga
import n_reinas_HC as hc
import n_reinas_SA as sa
import n_reinas_random as rnd
import random, time, os, json, csv
from dataclasses import dataclass, asdict
from typing import List

# =================== Utilidades de impresión ===================
def print_board(queens):
    for i in range(len(queens)):
        row = ["." for _ in range(len(queens))]
        row[queens[i]] = "Q"
        print(" ".join(row))
    print()

# =================== Medición de estados ===================
class FitnessCounter:
    """
    Cuenta cuántas veces se llama a board.fitness(sol).
    Se hace monkey-patch sobre la instancia de Board.
    """
    def __init__(self, board, max_evals=None):
        self.board = board
        self.counter = 0
        self.max_evals = max_evals
        self._orig = board.fitness

    def __enter__(self):
        def counted_fitness(sol):
            self.counter += 1
            # Lanzar excepción si se excede el presupuesto
            if self.max_evals and self.counter > self.max_evals:
                raise BudgetExceeded()
            return self._orig(sol)
        self.board.fitness = counted_fitness  # type: ignore[attr-defined]
        return self

    def __exit__(self, exc_type, exc, tb):
        self.board.fitness = self._orig  # restaurar método original
        # Suprimir excepción de presupuesto
        if exc_type is BudgetExceeded:
            return True

class BudgetExceeded(Exception):
    """Excepción para detener cuando se agota el presupuesto"""
    pass

# =================== Registro por corrida ===================
@dataclass
class RunRecord:
    algorithm_name: str      # "random" | "HC" | "SA" | "GA"
    env_n: int               # id de la corrida [0..29]
    size: int                # N
    best_solution: List[int] # lista con la mejor solución (posiciones de reinas)
    H: int                   # valor de H() de esa solución
    states: int              # cantidad de estados explorados (llamadas a fitness)
    time: float              # tiempo (segundos)

# =================== Configuración de experimentos ===================
SIZES = [4, 8, 10, 12, 15]
RUNS_PER_SIZE = 30  # 30 ejecuciones por tamaño y algoritmo (env_n = 0..29)

# PRESUPUESTO JUSTO: Mismo límite de evaluaciones para todos los algoritmos
MAX_EVALUATIONS = {
    4: 10_000,
    8: 50_000,
    10: 100_000,
    12: 150_000,
    15: 200_000
}

# Parámetros de algoritmos (sin max_iters, se controla por presupuesto)
SA_PARAMS = lambda n: dict(T_init=n, T_min=1e-3, alpha=0.98, iters_per_T=n*n)
GA_PARAMS = lambda n: dict(population_size=100, generations=10000)  # Generaciones altas, se detendrá por presupuesto

# Salidas
RESULTS_ROOT = os.path.abspath("results")
JSON_DIR     = os.path.join(RESULTS_ROOT, "json")
CSV_PATH     = os.path.join(RESULTS_ROOT, "all_runs.csv")

def ensure_dirs():
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(RESULTS_ROOT, exist_ok=True)

def save_run_json(rec: RunRecord):
    algo_dir = os.path.join(JSON_DIR, rec.algorithm_name, str(rec.size))
    os.makedirs(algo_dir, exist_ok=True)
    path = os.path.join(algo_dir, f"run_{rec.env_n}.json")
    with open(path, "w", encoding="utf-8") as f:
        data = asdict(rec)
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def append_csv_row(rec: RunRecord):
    exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "algorithm_name", "env_n", "size", "best_solution", "H", "states", "time"
        ])
        if not exists:
            writer.writeheader()
        row = asdict(rec)
        row["best_solution"] = json.dumps(row["best_solution"], ensure_ascii=False)
        writer.writerow(row)

# =================== Wrappers por algoritmo ===================
def run_random(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-RANDOM")
    board = rnd.Board(dimension=dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        best = list(board.queens)
        best_H = board.fitness(best)
        try:
            while True:
                candidate = rnd.Board(dimension=dim).queens
                cH = board.fitness(candidate)
                if cH < best_H:
                    best, best_H = candidate, cH
                    if best_H == 0:
                        break
        except BudgetExceeded:
            pass
        elapsed = time.perf_counter() - t0
    
    return RunRecord("random", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_hc(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-HC")
    board = hc.Board(dimension=dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            while True:
                next_board, next_fit = board.get_best_neighbour(board.queens)
                curr_fit = board.fitness(board.queens)
                if next_fit >= curr_fit:
                    break
                board.queens = next_board
                if next_fit == 0:
                    break
        except BudgetExceeded:
            pass
        elapsed = time.perf_counter() - t0
        best = list(board.queens)
        best_H = board.fitness(best)
    
    return RunRecord("HC", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_sa(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-SA")
    board = sa.Board(dimension=dim)
    params = SA_PARAMS(dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            solution, fit = sa.simulated_annealing(
                board,
                T_init=params["T_init"],
                T_min=params["T_min"],
                alpha=params["alpha"],
                iters_per_T=params["iters_per_T"],
                max_iters=999999999  # Sin límite de iteraciones, solo por presupuesto
            )
        except BudgetExceeded:
            solution = board.queens
            fit = board.fitness(solution)
        elapsed = time.perf_counter() - t0
        best = list(solution)
        best_H = fit if fit is not None else board.fitness(best)
    
    return RunRecord("SA", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_ga(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-GA")
    board = ga.Board(dimension=dim)
    params = GA_PARAMS(dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            solution = board.genetic_algorithm(
                population_size=params["population_size"],
                generations=params["generations"],
            )
        except BudgetExceeded:
            # Devolver la mejor solución encontrada hasta ahora
            solution = board.queens
        elapsed = time.perf_counter() - t0
        best = list(solution)
        best_H = board.fitness(best)
    
    return RunRecord("GA", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

ALGORITHMS = [
    ("random", run_random),
    ("HC",     run_hc),
    ("SA",     run_sa),
    ("GA",     run_ga),
]

# =================== main() ===================
def main():
    ensure_dirs()

    # Ejemplo simple en consola (dim=10) — no afecta archivos de resultados
    dim = 10
    print("=== Ejemplo simple (dim=10) por consola ===")
    board = rnd.Board(dimension=dim)
    print("Initial board:")
    print_board(board.queens)
    print("Initial fitness:", board.fitness(board.queens))
    for _ in range(10_000):
        candidate = rnd.Board(dimension=dim).queens
        if board.fitness(candidate) < board.fitness(board.queens):
            board.queens = candidate
    print("Final board:")
    print_board(board.queens)
    print("Final fitness:", board.fitness(board.queens))
    print("\n=== Fin del ejemplo; comienzan los experimentos ===\n")

    # Experimentos completos: 30 corridas x algoritmo x tamaño
    for size in SIZES:
        print(f"\n{'='*60}")
        print(f"Tamaño N={size} | Presupuesto: {MAX_EVALUATIONS[size]:,} evaluaciones")
        print(f"{'='*60}")
        for env_n in range(RUNS_PER_SIZE):
            for name, fn in ALGORITHMS:
                print(f"[size={size:>2}] [env={env_n:>2}] [algo={name:>6}] ...", end=" ", flush=True)
                rec = fn(size, env_n)
                save_path = save_run_json(rec)
                append_csv_row(rec)
                print(f"H={rec.H:>2} | states={rec.states:>7} | time={rec.time:.4f}s", flush=True)

if __name__ == "__main__":
    main()