#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(BASE_DIR, "results")
SUMMARY_CSV = os.path.join(RESULTS_ROOT, "results_summary.csv")
ALL_RUNS_CSV = os.path.join(RESULTS_ROOT, "all_runs.csv")
IMAGES_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))
os.makedirs(IMAGES_DIR, exist_ok=True)

# Colores más distintivos
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

def main():
    if not os.path.isfile(SUMMARY_CSV):
        print("No se encontró results_summary.csv. Corré analyze_results.py primero.")
        return
    
    df_summary = pd.read_csv(SUMMARY_CSV)
    algorithms = df_summary["algorithm_name"].unique()
    
    # Cargar datos completos para boxplots
    if os.path.isfile(ALL_RUNS_CSV):
        df_all = pd.read_csv(ALL_RUNS_CSV)
        has_all_data = True
    else:
        print("Advertencia: No se encontró all_runs.csv. Se omitirán boxplots.")
        has_all_data = False
    
    # ========== GRÁFICOS EXISTENTES ==========
    
    # ---- Gráfico 1: porcentaje de soluciones óptimas ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df_summary[df_summary["algorithm_name"] == algo]
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
    
    # ---- Gráfico 2: H promedio con barras de error ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df_summary[df_summary["algorithm_name"] == algo]
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
    
    # ---- Gráfico 3: tiempo promedio con barras de error ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df_summary[df_summary["algorithm_name"] == algo]
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
    
    # ---- Gráfico 4: estados promedio con bandas sombreadas ----
    plt.figure(figsize=(10, 6))
    for i, algo in enumerate(algorithms):
        subset = df_summary[df_summary["algorithm_name"] == algo]
        color = COLORS[i % len(COLORS)]
        
        plt.plot(subset["size"], subset["states_mean_all"], 
                marker="o", linewidth=2.5, markersize=8,
                label=algo, color=color)
        
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
    
    # ========== NUEVOS BOXPLOTS ==========
    
    if not has_all_data:
        return
    
    sizes = sorted(df_all["size"].unique())
    
    # ---- Boxplot 1: Distribución de H por tamaño ----
    fig, axes = plt.subplots(1, len(sizes), figsize=(4*len(sizes), 6), sharey=True)
    if len(sizes) == 1:
        axes = [axes]
    
    for idx, size in enumerate(sizes):
        data_by_algo = []
        labels = []
        colors_list = []
        
        for i, algo in enumerate(algorithms):
            subset = df_all[(df_all["algorithm_name"] == algo) & (df_all["size"] == size)]
            data_by_algo.append(subset["H"].values)
            labels.append(algo)
            colors_list.append(COLORS[i % len(COLORS)])
        
        bp = axes[idx].boxplot(data_by_algo, labels=labels, patch_artist=True,
                              medianprops=dict(color='black', linewidth=2),
                              boxprops=dict(linewidth=1.5),
                              whiskerprops=dict(linewidth=1.5),
                              capprops=dict(linewidth=1.5))
        
        # Colorear boxes
        for patch, color in zip(bp['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        axes[idx].set_title(f"N={size}", fontsize=12, fontweight='bold')
        axes[idx].set_ylabel("H (conflictos diagonales)" if idx == 0 else "", fontsize=11, fontweight='bold')
        axes[idx].grid(True, axis='y', linestyle="--", alpha=0.3)
        axes[idx].tick_params(axis='x', rotation=45)
    
    fig.suptitle("Distribución de H por algoritmo y tamaño (30 corridas cada uno)", 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    out5 = os.path.join(IMAGES_DIR, "boxplot_H.png")
    plt.savefig(out5, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out5)
    
    # ---- Boxplot 2: Distribución de tiempo por tamaño ----
    fig, axes = plt.subplots(1, len(sizes), figsize=(4*len(sizes), 6), sharey=True)
    if len(sizes) == 1:
        axes = [axes]
    
    for idx, size in enumerate(sizes):
        data_by_algo = []
        labels = []
        colors_list = []
        
        for i, algo in enumerate(algorithms):
            subset = df_all[(df_all["algorithm_name"] == algo) & (df_all["size"] == size)]
            data_by_algo.append(subset["time"].values)
            labels.append(algo)
            colors_list.append(COLORS[i % len(COLORS)])
        
        bp = axes[idx].boxplot(data_by_algo, labels=labels, patch_artist=True,
                              medianprops=dict(color='black', linewidth=2),
                              boxprops=dict(linewidth=1.5),
                              whiskerprops=dict(linewidth=1.5),
                              capprops=dict(linewidth=1.5))
        
        for patch, color in zip(bp['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        axes[idx].set_title(f"N={size}", fontsize=12, fontweight='bold')
        axes[idx].set_ylabel("Tiempo (segundos)" if idx == 0 else "", fontsize=11, fontweight='bold')
        axes[idx].grid(True, axis='y', linestyle="--", alpha=0.3)
        axes[idx].tick_params(axis='x', rotation=45)
    
    fig.suptitle("Distribución de tiempo de ejecución por algoritmo y tamaño", 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    out6 = os.path.join(IMAGES_DIR, "boxplot_time.png")
    plt.savefig(out6, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out6)
    
    # ---- Boxplot 3: Distribución de estados explorados por tamaño ----
    fig, axes = plt.subplots(1, len(sizes), figsize=(4*len(sizes), 6), sharey=True)
    if len(sizes) == 1:
        axes = [axes]
    
    for idx, size in enumerate(sizes):
        data_by_algo = []
        labels = []
        colors_list = []
        
        for i, algo in enumerate(algorithms):
            subset = df_all[(df_all["algorithm_name"] == algo) & (df_all["size"] == size)]
            data_by_algo.append(subset["states"].values)
            labels.append(algo)
            colors_list.append(COLORS[i % len(COLORS)])
        
        bp = axes[idx].boxplot(data_by_algo, labels=labels, patch_artist=True,
                              medianprops=dict(color='black', linewidth=2),
                              boxprops=dict(linewidth=1.5),
                              whiskerprops=dict(linewidth=1.5),
                              capprops=dict(linewidth=1.5))
        
        for patch, color in zip(bp['boxes'], colors_list):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        axes[idx].set_title(f"N={size}", fontsize=12, fontweight='bold')
        axes[idx].set_ylabel("Estados explorados" if idx == 0 else "", fontsize=11, fontweight='bold')
        axes[idx].grid(True, axis='y', linestyle="--", alpha=0.3)
        axes[idx].tick_params(axis='x', rotation=45)
    
    fig.suptitle("Distribución de estados explorados por algoritmo y tamaño", 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    out7 = os.path.join(IMAGES_DIR, "boxplot_states.png")
    plt.savefig(out7, dpi=300, bbox_inches="tight")
    plt.close()
    print("Guardado:", out7)

if __name__ == "__main__":
    main()