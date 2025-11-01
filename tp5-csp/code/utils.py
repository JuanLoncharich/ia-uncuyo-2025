"""
Utilidades para el TP5: generación de gráficos y estadísticas.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas agrupadas por algoritmo y tamaño de problema.

    Retorna un DataFrame con porcentaje de éxito, promedios y desviaciones
    estándar de tiempo y nodos explorados.
    """
    grouped = df.groupby(["algorithm_name", "n"], as_index=False)
    stats = grouped.agg(
        runs=("found_solution", "size"),
        success_rate=("found_solution", lambda s: float(s.mean()) * 100.0),
        mean_time=("time", "mean"),
        std_time=("time", "std"),
        mean_nodes=("explored_nodes", "mean"),
        std_nodes=("explored_nodes", "std"),
    )
    stats = stats.fillna(0.0)
    stats["success_rate"] = stats["success_rate"].round(2)
    stats["mean_time"] = stats["mean_time"].round(6)
    stats["std_time"] = stats["std_time"].round(6)
    stats["mean_nodes"] = stats["mean_nodes"].round(2)
    stats["std_nodes"] = stats["std_nodes"].round(2)
    return stats.sort_values(["n", "algorithm_name"]).reset_index(drop=True)


def make_boxplots(df: pd.DataFrame, metric: str, outpath: Path) -> None:
    """
    Genera boxplots por algoritmo para cada valor de N y guarda la figura.

    :param df: DataFrame con columnas algorithm_name, n y la métrica.
    :param metric: Nombre de la métrica a graficar (e.g. 'time').
    :param outpath: Ruta de salida de la figura.
    """
    if metric not in df.columns:
        raise ValueError(f"La métrica '{metric}' no existe en el DataFrame.")

    metric_labels = {
        "time": "Tiempo (s)",
        "explored_nodes": "Nodos explorados",
    }
    metric_label = metric_labels.get(metric, metric)

    n_values = sorted(df["n"].unique())
    if not n_values:
        raise ValueError("El DataFrame no contiene datos para graficar.")

    fig_width = max(5 * len(n_values), 6)
    fig, axes = plt.subplots(
        1, len(n_values), figsize=(fig_width, 5), sharey=len(n_values) > 1
    )
    if len(n_values) == 1:
        axes = [axes]  # type: ignore[assignment]

    for ax, n in zip(axes, n_values):
        subset = df[df["n"] == n]
        algorithms = sorted(subset["algorithm_name"].unique())
        data = [subset[subset["algorithm_name"] == algo][metric].to_numpy() for algo in algorithms]
        ax.boxplot(data, labels=algorithms)
        ax.set_title(f"N = {n}")
        ax.set_xlabel("Algoritmo")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    axes[0].set_ylabel(metric_label)

    fig.suptitle(f"Distribución de {metric_label.lower()} por algoritmo", fontsize=14)
    fig.tight_layout()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outpath)
    plt.close(fig)
