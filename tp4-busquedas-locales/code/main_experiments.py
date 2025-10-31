import argparse
import csv
import json
import os
import random
import shutil
import time
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import n_reinas_GA as ga
import n_reinas_HC as hc
import n_reinas_SA as sa
import n_reinas_random as rnd

# =================== Utilidades de impresión ===================
def print_board(queens: Sequence[int]) -> None:
    """Imprime un tablero usando la convención columna→fila."""
    n = len(queens)
    for row in range(n):
        line = ["Q" if queens[col] == row else "." for col in range(n)]
        print(" ".join(line))
    print()

# =================== Medición de estados ===================
class FitnessCounter:
    """Context manager para medir llamadas a `board.fitness`."""

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
SA_PARAMS = lambda n: dict(T_init=float(n), T_min=1e-3, alpha=0.98)
GA_PARAMS = lambda n: dict(population_size=100, generations=10_000)

# Salidas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "results")
JSON_DIR = os.path.join(RESULTS_ROOT, "json")
CSV_PATH = os.path.join(RESULTS_ROOT, "all_runs.csv")
SUMMARY_CSV = os.path.join(RESULTS_ROOT, "results_summary.csv")

def ensure_dirs():
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(RESULTS_ROOT, exist_ok=True)

def save_run_json(rec: RunRecord) -> str:
    algo_dir = os.path.join(JSON_DIR, rec.algorithm_name, str(rec.size))
    os.makedirs(algo_dir, exist_ok=True)
    path = os.path.join(algo_dir, f"run_{rec.env_n}.json")
    with open(path, "w", encoding="utf-8") as f:
        data = asdict(rec)
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def rebuild_csv_from_json() -> None:
    """Reconstruye all_runs.csv leyendo todos los JSON existentes."""
    if not os.path.isdir(JSON_DIR):
        if os.path.isfile(CSV_PATH):
            os.remove(CSV_PATH)
        return

    entries = []
    for algo in os.listdir(JSON_DIR):
        algo_dir = os.path.join(JSON_DIR, algo)
        if not os.path.isdir(algo_dir):
            continue
        for size_name in os.listdir(algo_dir):
            size_dir = os.path.join(algo_dir, size_name)
            if not os.path.isdir(size_dir):
                continue
            for fname in os.listdir(size_dir):
                if not fname.endswith(".json"):
                    continue
                with open(os.path.join(size_dir, fname), "r", encoding="utf-8") as f:
                    entries.append(json.load(f))

    if not entries:
        if os.path.isfile(CSV_PATH):
            os.remove(CSV_PATH)
        return

    entries.sort(key=lambda row: (row["size"], row["algorithm_name"], row["env_n"]))
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["algorithm_name", "env_n", "size", "best_solution", "H", "states", "time"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in entries:
            row = row.copy()
            row["best_solution"] = json.dumps(row["best_solution"], ensure_ascii=False)
            writer.writerow(row)


def reset_results(target_sizes: Iterable[int], target_algorithms: Iterable[str]) -> None:
    """Elimina resultados previos para los tamaños/algoritmos seleccionados."""
    ensure_dirs()
    for algo in target_algorithms:
        algo_dir = os.path.join(JSON_DIR, algo)
        if not os.path.isdir(algo_dir):
            continue
        for size in target_sizes:
            size_dir = os.path.join(algo_dir, str(size))
            if os.path.isdir(size_dir):
                shutil.rmtree(size_dir)
        if os.path.isdir(algo_dir) and not os.listdir(algo_dir):
            os.rmdir(algo_dir)

    if os.path.isfile(SUMMARY_CSV):
        os.remove(SUMMARY_CSV)


def run_demo() -> None:
    """Demostración simple del pipeline con búsqueda aleatoria."""
    dim = 10
    print("=== Ejemplo simple (dim=10) por consola ===")
    board = rnd.Board(dimension=dim)
    print("Initial board:")
    print_board(board.queens)
    print("Initial fitness:", board.fitness(board.queens))
    best, best_H, _ = rnd.random_search(board, max_evals=10_000, return_history=True)
    board.queens = best
    print("Final board:")
    print_board(board.queens)
    print("Final fitness:", best_H)
    print("\n=== Fin del ejemplo; comienzan los experimentos ===\n")


def parse_cli() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(
        description="Reproduce los experimentos de N-reinas con metaheurísticas.",
    )
    parser.add_argument(
        "--n",
        dest="sizes",
        action="append",
        type=int,
        metavar="N",
        help="Tamaño del tablero. Puede repetirse varias veces. Por defecto: 4,8,10,12,15.",
    )
    parser.add_argument(
        "--algo",
        dest="algorithms",
        action="append",
        type=algo_choice,
        metavar="ALGO",
        help="Algoritmo a ejecutar (random, HC, SA, GA). Puede repetirse.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=RUNS_PER_SIZE,
        help="Cantidad de corridas por tamaño y algoritmo (default: 30).",
    )
    parser.add_argument(
        "--seed-offset",
        type=int,
        default=0,
        help="Offset inicial para env_n (permite continuar experimentos previos).",
    )
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Omite el ejemplo inicial de búsqueda aleatoria.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina resultados previos de los tamaños/algoritmos seleccionados antes de correr.",
    )
    args = parser.parse_args()
    return parser, args

# =================== Wrappers por algoritmo ===================
def run_random(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-RANDOM")
    board = rnd.Board(dimension=dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    best = list(board.queens)
    best_H = None
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            best_H = board.fitness(best)
            while True:
                candidate = rnd.Board(dimension=dim).queens
                cH = board.fitness(candidate)
                if cH < best_H:
                    best, best_H = candidate, cH
                    if best_H == 0:
                        break
        except BudgetExceeded:
            # Calcular fitness final sin incrementar contador
            board.fitness = fc._orig
            best_H = board.fitness(best)
        elapsed = time.perf_counter() - t0
    
    return RunRecord("random", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_hc(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-HC")
    board = hc.Board(dimension=dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    best = list(board.queens)
    best_H = None
    history: List[int] = []
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            best, history = hc.hill_climbing(board, return_history=True)
        except BudgetExceeded:
            best = list(board.queens)
        elapsed = time.perf_counter() - t0
        # Calcular fitness final sin incrementar contador
        board.fitness = fc._orig
        best_H = board.fitness(best)
    
    return RunRecord("HC", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_sa(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-SA")
    board = sa.Board(dimension=dim)
    params = SA_PARAMS(dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    solution = board.queens
    best_H = None
    history: List[int] = []
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            result = sa.simulated_annealing(
                board,
                T_init=params["T_init"],
                T_min=params["T_min"],
                alpha=params["alpha"],
                max_iters=999_999_999,  # Sin límite de iteraciones, sólo presupuesto
            )
            if isinstance(result, tuple) and len(result) == 3:
                solution, fit, history = result
            else:
                solution, fit = result
            best_H = fit
        except BudgetExceeded:
            solution = board.queens
            # Calcular fitness sin incrementar contador
            board.fitness = fc._orig
            best_H = board.fitness(solution)
        elapsed = time.perf_counter() - t0
        best = list(solution)
    
    return RunRecord("SA", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

def run_ga(dim: int, env_n: int) -> RunRecord:
    random.seed(f"{dim}-{env_n}-GA")
    board = ga.Board(dimension=dim)
    params = GA_PARAMS(dim)
    max_evals = MAX_EVALUATIONS[dim]
    
    # Inicializar variables por si se agota el presupuesto
    solution = board.queens
    best_H = None
    history: List[int] = []
    
    with FitnessCounter(board, max_evals=max_evals) as fc:
        t0 = time.perf_counter()
        try:
            result = board.genetic_algorithm(
                population_size=params["population_size"],
                generations=params["generations"],
            )
            if isinstance(result, tuple):
                solution, history = result
            else:
                solution = result
            best_H = board.fitness(solution)
        except BudgetExceeded:
            # Devolver la mejor solución encontrada hasta ahora
            solution = board.queens
            # Calcular fitness sin incrementar contador (restaurar método original temporalmente)
            board.fitness = fc._orig
            best_H = board.fitness(solution)
        elapsed = time.perf_counter() - t0
        best = list(solution)
    
    return RunRecord("GA", env_n, dim, best, int(best_H), fc.counter, float(elapsed))

ALGORITHMS: Dict[str, Callable[[int, int], RunRecord]] = {
    "random": run_random,
    "HC": run_hc,
    "SA": run_sa,
    "GA": run_ga,
}
ALGO_NAME_MAP = {name.lower(): name for name in ALGORITHMS}


def algo_choice(value: str) -> str:
    """Normaliza el nombre del algoritmo desde CLI."""
    key = ALGO_NAME_MAP.get(value.lower())
    if key is None:
        valid = ", ".join(ALGORITHMS.keys())
        raise argparse.ArgumentTypeError(f"Algoritmo desconocido '{value}'. Opciones: {valid}")
    return key

# =================== main() ===================
def main() -> None:
    parser, args = parse_cli()
    ensure_dirs()

    raw_sizes = args.sizes or SIZES
    sizes = list(dict.fromkeys(raw_sizes))
    invalid_sizes = [n for n in sizes if n not in MAX_EVALUATIONS]
    if invalid_sizes:
        parser.error(
            f"Tamaños no soportados: {invalid_sizes}. Valores válidos: {list(MAX_EVALUATIONS.keys())}"
        )

    raw_algorithms = args.algorithms or list(ALGORITHMS.keys())
    algorithms = list(dict.fromkeys(raw_algorithms))

    runs = args.runs
    if runs <= 0:
        parser.error("--runs debe ser un entero positivo.")

    seed_offset = args.seed_offset
    if seed_offset < 0:
        parser.error("--seed-offset debe ser mayor o igual a 0.")

    if args.reset:
        reset_results(sizes, algorithms)

    if not args.skip_demo:
        run_demo()

    for size in sizes:
        print(f"\n{'=' * 60}")
        print(f"Tamaño N={size} | Presupuesto: {MAX_EVALUATIONS[size]:,} evaluaciones")
        print(f"{'=' * 60}")

        for run_idx in range(runs):
            env_n = seed_offset + run_idx
            for name in algorithms:
                fn = ALGORITHMS[name]
                print(f"[size={size:>2}] [env={env_n:>2}] [algo={name:>6}] ...", end=" ", flush=True)
                rec = fn(size, env_n)
                save_run_json(rec)
                print(f"H={rec.H:>2} | states={rec.states:>7} | time={rec.time:.4f}s", flush=True)

    rebuild_csv_from_json()

    print(f"\nResultados consolidados en: {CSV_PATH}")
    if os.path.isfile(SUMMARY_CSV):
        print(f"Resumen existente en: {SUMMARY_CSV} (recordá regenerarlo si necesitás datos frescos).")


if __name__ == "__main__":
    main()
