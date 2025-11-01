"""
Script de experimentación para N-Reinas con backtracking y forward checking.

Genera estadísticas, gráficos y un CSV con los resultados de múltiples corridas
para distintos tamaños de tablero.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence

import pandas as pd

try:
    from .n_reinas_backtracking import NQueensResult, solve_n_queens_backtracking
    from .n_reinas_forward import solve_n_queens_forward
    from .utils import compute_stats, make_boxplots
except ImportError:  # Permite correr como script sin paquete
    from n_reinas_backtracking import NQueensResult, solve_n_queens_backtracking  # type: ignore[attr-defined]
    from n_reinas_forward import solve_n_queens_forward  # type: ignore[attr-defined]
    from utils import compute_stats, make_boxplots  # type: ignore[attr-defined]

Solver = Callable[[int, random.Random], NQueensResult]

ALGORITHMS: Dict[str, Solver] = {
    "BT": solve_n_queens_backtracking,
    "FC": solve_n_queens_forward,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Experimentos con N-Reinas.")
    parser.add_argument(
        "--n",
        dest="n_values",
        nargs="+",
        type=int,
        default=[4, 8, 10],
        help="Valores de N a evaluar (default: 4 8 10).",
    )
    parser.add_argument(
        "--algo",
        dest="algorithm",
        choices=["BT", "FC", "both"],
        default="both",
        help="Algoritmo a ejecutar (BT, FC o both).",
    )
    parser.add_argument(
        "--runs",
        dest="runs",
        type=int,
        default=30,
        help="Cantidad de corridas por combinación (default: 30).",
    )
    parser.add_argument(
        "--output",
        dest="output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tp5-Nreinas.csv",
        help="Ruta de salida para el CSV.",
    )
    return parser.parse_args(argv)


def run_experiments(n_values: Iterable[int], algos: Iterable[str], runs: int) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for n in n_values:
        for algo_key in algos:
            solver = ALGORITHMS[algo_key]
            print(f"Ejecutando {algo_key} para N={n} ({runs} corridas)...")
            for seed in range(1, runs + 1):
                rng = random.Random(seed)
                result = solver(n, rng=rng)
                records.append(
                    {
                        "algorithm_name": algo_key,
                        "n": n,
                        "found_solution": result.found_solution,
                        "time": result.time,
                        "explored_nodes": result.explored_nodes,
                    }
                )
    return records


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    algos = ALGORITHMS.keys() if args.algorithm == "both" else [args.algorithm]
    output_path: Path = args.output
    images_dir = Path(__file__).resolve().parents[1] / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    records = run_experiments(args.n_values, algos, args.runs)
    df = pd.DataFrame.from_records(records)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Resultados guardados en {output_path}")

    stats_df = compute_stats(df)
    print("\nResumen estadístico:")
    print(stats_df.to_string(index=False))

    make_boxplots(df, metric="time", outpath=images_dir / "boxplot_tiempos.png")
    make_boxplots(df, metric="explored_nodes", outpath=images_dir / "boxplot_nodos.png")
    print(f"Gráficos guardados en {images_dir}")


if __name__ == "__main__":
    main()
