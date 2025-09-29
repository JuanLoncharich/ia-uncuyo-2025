#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # donde está este script
RESULTS_ROOT = os.path.join(BASE_DIR, "results")               # carpeta con CSV
SUMMARY_CSV = os.path.join(RESULTS_ROOT, "results_summary.csv")

# carpeta ../images
IMAGES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))
os.makedirs(IMAGES_DIR, exist_ok=True)

def main():
    if not os.path.isfile(SUMMARY_CSV):
        print("No se encontró results_summary.csv. Corré analyze_results.py primero.")
        return

    df = pd.read_csv(SUMMARY_CSV)

    # ---- Gráfico 1: porcentaje de soluciones óptimas ----
    plt.figure(figsize=(8, 6))
    for algo in df["algorithm_name"].unique():
        subset = df[df["algorithm_name"] == algo]
        plt.plot(subset["size"], subset["optimality_pct"], marker="o", label=algo)
    plt.xlabel("Tamaño del tablero (N)")
    plt.ylabel("% de soluciones óptimas")
    plt.title("Porcentaje de soluciones óptimas por algoritmo")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    out1 = os.path.join(IMAGES_DIR, "optimality_pct.png")
    plt.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out1)

    # ---- Gráfico 2: H promedio ----
    plt.figure(figsize=(8, 6))
    for algo in df["algorithm_name"].unique():
        subset = df[df["algorithm_name"] == algo]
        plt.errorbar(subset["size"], subset["H_mean_all"], yerr=subset["H_std_all"],
                     marker="o", capsize=4, label=algo)
    plt.xlabel("Tamaño del tablero (N)")
    plt.ylabel("H promedio (con desviación)")
    plt.title("H promedio por algoritmo")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    out2 = os.path.join(IMAGES_DIR, "H_mean.png")
    plt.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out2)

    # ---- Gráfico 3: tiempo promedio ----
    plt.figure(figsize=(8, 6))
    for algo in df["algorithm_name"].unique():
        subset = df[df["algorithm_name"] == algo]
        plt.errorbar(subset["size"], subset["time_mean_all"], yerr=subset["time_std_all"],
                     marker="o", capsize=4, label=algo)
    plt.xlabel("Tamaño del tablero (N)")
    plt.ylabel("Tiempo promedio (s)")
    plt.title("Tiempo de ejecución promedio por algoritmo")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    out3 = os.path.join(IMAGES_DIR, "time_mean.png")
    plt.savefig(out3, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out3)

    # ---- Gráfico 4: estados promedio ----
    plt.figure(figsize=(8, 6))
    for algo in df["algorithm_name"].unique():
        subset = df[df["algorithm_name"] == algo]
        plt.errorbar(subset["size"], subset["states_mean_all"], yerr=subset["states_std_all"],
                     marker="o", capsize=4, label=algo)
    plt.xlabel("Tamaño del tablero (N)")
    plt.ylabel("Estados explorados promedio")
    plt.title("Estados promedio por algoritmo")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    out4 = os.path.join(IMAGES_DIR, "states_mean.png")
    plt.savefig(out4, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out4)


if __name__ == "__main__":
    main()
