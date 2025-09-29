#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "results")
SUMMARY_CSV = os.path.join(RESULTS_ROOT, "results_summary.csv")
IMAGES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))
os.makedirs(IMAGES_DIR, exist_ok=True)

# Colores más distintivos
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

def main():
    if not os.path.isfile(SUMMARY_CSV):
        print("No se encontró results_summary.csv. Corré analyze_results.py primero.")
        return
    
    df = pd.read_csv(SUMMARY_CSV)
    algorithms = df["algorithm_name"].unique()
    
    # ---- Gráfico 1: porcentaje de soluciones óptimas (sin cambios) ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df[df["algorithm_name"] == algo]
        plt.plot(subset["size"], subset["optimality_pct"], 
                marker="o", linewidth=2.5, markersize=8, 
                label=algo, color=COLORS[i % len(COLORS)])
    
    plt.xlabel("Tamaño del tablero (N)", fontsize=12, fontweight='bold')
    plt.ylabel("% de soluciones óptimas", fontsize=12, fontweight='bold')
    plt.title("Porcentaje de soluciones óptimas por algoritmo", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.3)
    out1 = os.path.join(IMAGES_DIR, "optimality_pct.png")
    plt.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out1)
    
    # ---- Gráfico 2: H promedio - OPCIÓN 1: Barras de error verticales gruesas ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df[df["algorithm_name"] == algo]
        color = COLORS[i % len(COLORS)]
        
        plt.errorbar(subset["size"], subset["H_mean_all"], 
                    yerr=subset["H_std_all"],
                    marker="o", linewidth=2.5, markersize=8,
                    capsize=8, capthick=2.5, elinewidth=2.5,
                    label=algo, color=color, alpha=0.9)
    
    plt.xlabel("Tamaño del tablero (N)", fontsize=12, fontweight='bold')
    plt.ylabel("H promedio", fontsize=12, fontweight='bold')
    plt.title("H promedio por algoritmo (barras = ±1 desviación estándar)", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.3)
    out2 = os.path.join(IMAGES_DIR, "H_mean.png")
    plt.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out2)
    
    # ---- OPCIÓN 2: Gráfico con subplots separados por algoritmo ----
    fig, axes = plt.subplots(len(algorithms), 1, figsize=(10, 3*len(algorithms)), sharex=True)
    if len(algorithms) == 1:
        axes = [axes]
    
    for i, algo in enumerate(algorithms):
        subset = df[df["algorithm_name"] == algo]
        color = COLORS[i % len(COLORS)]
        
        axes[i].plot(subset["size"], subset["H_mean_all"], 
                    marker="o", linewidth=2.5, markersize=8, color=color)
        axes[i].fill_between(subset["size"], 
                            subset["H_mean_all"] - subset["H_std_all"],
                            subset["H_mean_all"] + subset["H_std_all"],
                            alpha=0.3, color=color)
        axes[i].set_ylabel("H promedio", fontsize=11, fontweight='bold')
        axes[i].set_title(f"{algo}", fontsize=12, fontweight='bold')
        axes[i].grid(True, linestyle="--", alpha=0.3)
    
    axes[-1].set_xlabel("Tamaño del tablero (N)", fontsize=12, fontweight='bold')
    fig.suptitle("H promedio por algoritmo (con bandas de desviación estándar)", 
                fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    out2_alt = os.path.join(IMAGES_DIR, "H_mean_subplots.png")
    plt.savefig(out2_alt, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out2_alt)
    
    # ---- OPCIÓN 3: Box plots para cada tamaño ----
    # (Requeriría datos raw, no solo summary, así que comentado)
    # Si querés esta opción, necesitarías cargar los CSVs individuales
    
    # ---- Gráfico 3: tiempo promedio con BARRAS DE ERROR MÁS GRUESAS ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df[df["algorithm_name"] == algo]
        color = COLORS[i % len(COLORS)]
        
        plt.errorbar(subset["size"], subset["time_mean_all"], 
                    yerr=subset["time_std_all"],
                    marker="o", linewidth=2.5, markersize=8,
                    capsize=6, capthick=2, elinewidth=2,
                    label=algo, color=color)
    
    plt.xlabel("Tamaño del tablero (N)", fontsize=12, fontweight='bold')
    plt.ylabel("Tiempo promedio (s)", fontsize=12, fontweight='bold')
    plt.title("Tiempo de ejecución promedio por algoritmo", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.3)
    out3 = os.path.join(IMAGES_DIR, "time_mean.png")
    plt.savefig(out3, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out3)
    
    # ---- Gráfico 4: estados promedio con BANDA SOMBREADA ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df[df["algorithm_name"] == algo]
        color = COLORS[i % len(COLORS)]
        
        # Línea principal
        plt.plot(subset["size"], subset["states_mean_all"], 
                marker="o", linewidth=2.5, markersize=8,
                label=algo, color=color)
        
        # Banda sombreada
        plt.fill_between(subset["size"], 
                        subset["states_mean_all"] - subset["states_std_all"],
                        subset["states_mean_all"] + subset["states_std_all"],
                        alpha=0.25, color=color)
    
    plt.xlabel("Tamaño del tablero (N)", fontsize=12, fontweight='bold')
    plt.ylabel("Estados explorados promedio", fontsize=12, fontweight='bold')
    plt.title("Estados promedio por algoritmo (banda = ±1 desviación estándar)", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.3)
    out4 = os.path.join(IMAGES_DIR, "states_mean.png")
    plt.savefig(out4, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out4)

if __name__ == "__main__":
    main()