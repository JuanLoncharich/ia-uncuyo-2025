#!/usr/bin/env python3
import os, json
import pandas as pd

RESULTS_ROOT = os.path.abspath("results")
JSON_DIR     = os.path.join(RESULTS_ROOT, "json")
SUMMARY_CSV  = os.path.join(RESULTS_ROOT, "results_summary.csv")

def load_rows(json_dir: str):
    rows = []
    if not os.path.isdir(json_dir):
        return rows
    for algo in os.listdir(json_dir):
        ap = os.path.join(json_dir, algo)
        if not os.path.isdir(ap): 
            continue
        for size in os.listdir(ap):
            sp = os.path.join(ap, size)
            if not os.path.isdir(sp):
                continue
            for fname in os.listdir(sp):
                if not fname.endswith(".json"):
                    continue
                with open(os.path.join(sp, fname), "r", encoding="utf-8") as f:
                    rows.append(json.load(f))
    return rows

def main():
    rows = load_rows(JSON_DIR)
    if not rows:
        print("No se encontraron JSONs. ¿Ya corriste main_experiments.py?")
        return

    df = pd.DataFrame(rows)
    # Tipos robustos
    df["env_n"]  = df["env_n"].astype(int)
    df["size"]   = df["size"].astype(int)
    df["H"]      = df["H"].astype(int)
    df["states"] = df["states"].astype(int)
    df["time"]   = df["time"].astype(float)

    # Agregados por (algoritmo, tamaño)
    def agg(g):
        total = len(g)
        success = (g["H"] == 0)
        n_ok = int(success.sum())
        pct_ok = 100.0 * n_ok / total if total else 0.0

        out = {
            "runs": total,
            "optimal_runs": n_ok,
            "optimality_pct": pct_ok,
            "H_mean_all": g["H"].mean(),
            "H_std_all": g["H"].std(ddof=1) if total > 1 else 0.0,
            "time_mean_all": g["time"].mean(),
            "time_std_all": g["time"].std(ddof=1) if total > 1 else 0.0,
            "states_mean_all": g["states"].mean(),
            "states_std_all": g["states"].std(ddof=1) if total > 1 else 0.0,
        }

        # Métricas SOLO en corridas exitosas (para “tiempo para llegar a solución”)
        g_ok = g[success]
        if len(g_ok) > 0:
            out.update({
                "time_mean_success": g_ok["time"].mean(),
                "time_std_success": g_ok["time"].std(ddof=1) if len(g_ok) > 1 else 0.0,
                "states_mean_success": g_ok["states"].mean(),
                "states_std_success": g_ok["states"].std(ddof=1) if len(g_ok) > 1 else 0.0,
            })
        else:
            out.update({
                "time_mean_success": float("nan"),
                "time_std_success": float("nan"),
                "states_mean_success": float("nan"),
                "states_std_success": float("nan"),
            })
        return pd.Series(out)

    summary = (
        df.groupby(["algorithm_name", "size"])
        .apply(agg, include_groups=False)
        .reset_index()
    )
    summary = summary.sort_values(["size", "algorithm_name"]).reset_index(drop=True)

    os.makedirs(RESULTS_ROOT, exist_ok=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    print("Resumen guardado en:", SUMMARY_CSV)
    print(summary.to_string(index=False))

if __name__ == "__main__":
    main()
