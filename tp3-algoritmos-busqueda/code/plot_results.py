import csv
import math
import os
from collections import defaultdict
import matplotlib.pyplot as plt


def _boxplot_with_labels(series, labels):
    """Compatibility wrapper: matplotlib>=3.9 uses tick_labels; older uses labels."""
    try:
        # New API (Matplotlib 3.9+)
        return plt.boxplot(series, tick_labels=labels, showmeans=True)
    except TypeError:
        # Fallback for older Matplotlib
        return plt.boxplot(series, labels=labels, showmeans=True)


def load_results(path=None):
    """
    Lee results.csv soportando dos formatos:
    - Formato antiguo: algorithm, episode, reward, done, truncated, steps
    - Formato TP3: algorithm_name, env_n, states_n, actions_count, actions_cost, time, solution_found
    Devuelve una lista de dicts normalizados con claves:
    algorithm_name, env_n, states_n, actions_count, actions_cost, time, solution_found
    """
    if path is None:
        # Preferir el CSV en la carpeta padre (conforme a la consigna)
        here = os.path.dirname(__file__)
        parent_csv = os.path.join(here, os.pardir, "results.csv")
        local_csv = os.path.join(here, "results.csv")
        path = parent_csv if os.path.exists(parent_csv) else local_csv

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    data = []
    if not rows:
        return data

    cols = set(rows[0].keys())

    if {"algorithm_name", "env_n", "states_n", "actions_count", "actions_cost", "time", "solution_found"} <= cols:
        # Formato TP3
        for r in rows:
            seed = r.get("seed")
            manhattan = r.get("manhattan")
            monotone_rd = r.get("monotone_rd")
            data.append(
                {
                    "algorithm_name": r["algorithm_name"],
                    "env_n": int(r["env_n"]),
                    "states_n": int(r["states_n"]),
                    "actions_count": int(r["actions_count"]),
                    "actions_cost": int(r["actions_cost"]),
                    "time": float(r["time"]),
                    "solution_found": (str(r["solution_found"]).strip().lower() == "true"),
                    "seed": int(seed) if (seed is not None and seed.strip() != "") else None,
                    "manhattan": int(manhattan) if (manhattan is not None and manhattan.strip() != "") else None,
                    "monotone_rd": (str(monotone_rd).strip().lower() == "true") if monotone_rd is not None else None,
                }
            )
    elif {"algorithm", "episode", "reward", "done", "truncated", "steps"} <= cols:
        # Formato antiguo: mapear a las claves nuevas
        for r in rows:
            data.append(
                {
                    "algorithm_name": r["algorithm"],
                    "env_n": int(r["episode"]),
                    "states_n": -1,
                    "actions_count": int(r["steps"]),
                    # Asumir costo esc.2 ~= steps si no hay acciones; mejor -1 para no mezclar
                    "actions_cost": -1,
                    "time": math.nan,
                    "solution_found": (str(r["done"]).strip().lower() == "true"),
                }
            )
    else:
        raise ValueError(f"CSV con columnas no reconocidas: {sorted(cols)}")

    return data


def main():
    data = load_results()
    if not data:
        print("results.csv vacío o no encontrado")
        return

    here = os.path.dirname(__file__)
    images_dir = os.path.abspath(os.path.join(here, os.pardir, "images"))
    os.makedirs(images_dir, exist_ok=True)

    algorithms = sorted({d["algorithm_name"] for d in data})

    # Resumen de soluciones por algoritmo
    print("Resumen: soluciones encontradas por algoritmo")
    for alg in algorithms:
        runs = [d for d in data if d["algorithm_name"] == alg]
        solved = sum(1 for r in runs if r["solution_found"])
        print(f"- {alg}: {solved}/{len(runs)}")

    # Preparar métricas para boxplots (solo valores válidos > -1)
    metrics = {
        "states_n": "Estados expandidos",
        "actions_count": "Cantidad de acciones (esc.1)",
        "actions_cost": "Costo total (esc.2)",
        "time": "Tiempo (s)",
    }

    for key, ylabel in metrics.items():
        series = []
        labels = []
        for alg in algorithms:
            values = [r[key] for r in data if r["algorithm_name"] == alg]
            # Filtrar -1 y NaN
            clean = [v for v in values if isinstance(v, (int, float)) and v == v and v >= 0]
            if clean:
                series.append(clean)
                labels.append(alg)

        if not series:
            continue

        plt.figure(figsize=(8, 5))
        _boxplot_with_labels(series, labels)
        plt.ylabel(ylabel)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        out_path = os.path.join(images_dir, f"box_{key}.png")
        plt.savefig(out_path)
        plt.close()

    # Medias y desviaciones estándar (impresión)
    print("\nMedias y desviaciones (solo valores válidos):")
    import statistics as stats

    for key, label in metrics.items():
        print(f"\n{label}:")
        for alg in algorithms:
            values = [r[key] for r in data if r["algorithm_name"] == alg]
            clean = [v for v in values if isinstance(v, (int, float)) and v == v and v >= 0]
            if clean:
                mu = stats.mean(clean)
                sd = stats.pstdev(clean) if len(clean) > 1 else 0.0
                print(f"- {alg}: media={mu:.2f}, desvío={sd:.2f}")
            else:
                print(f"- {alg}: sin datos válidos")

    # Boxplot: diferencia contra Manhattan por algoritmo (si hay columna)
    if any(d.get("manhattan") is not None for d in data):
        delta_vs_manh_series = []
        delta_vs_manh_labels = []
        for alg in algorithms:
            vals = []
            for r in data:
                if r["algorithm_name"] != alg:
                    continue
                manh = r.get("manhattan")
                steps = r.get("actions_count")
                if manh is not None and isinstance(steps, int) and steps >= 0:
                    vals.append(steps - manh)
            if vals:
                delta_vs_manh_series.append(vals)
                delta_vs_manh_labels.append(alg)

        if delta_vs_manh_series:
            plt.figure(figsize=(8, 5))
            _boxplot_with_labels(delta_vs_manh_series, delta_vs_manh_labels)
            plt.ylabel("Pasos - Manhattan")
            plt.axhline(0, color="gray", linestyle="--", linewidth=1)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            out_path = os.path.join(images_dir, "box_delta_steps_vs_manhattan.png")
            plt.savefig(out_path)
            plt.close()

    # Gráfico adicional: tasa de éxito por algoritmo (incluye los que no resuelven)
    success_counts = []
    for alg in algorithms:
        runs = [d for d in data if d["algorithm_name"] == alg]
        solved = sum(1 for r in runs if r["solution_found"])
        success_counts.append(solved)

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, success_counts)
    plt.ylabel("Soluciones en 30 entornos")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out_path = os.path.join(images_dir, "bar_success_counts.png")
    plt.savefig(out_path)
    plt.close()

    # Boxplot: diferencia de pasos vs BFS por algoritmo
    # Para cada entorno, tomamos los pasos de BFS como baseline y graficamos
    # (steps_alg - steps_bfs) para los algoritmos que resolvieron.
    bfs_steps_by_env = {}
    for r in data:
        if r["algorithm_name"] == "BFS" and r["actions_count"] >= 0:
            bfs_steps_by_env[r["env_n"]] = r["actions_count"]

    delta_series = []
    delta_labels = []
    for alg in sorted({a for a in algorithms if a != "BFS"}):
        deltas = []
        for r in data:
            if r["algorithm_name"] != alg:
                continue
            env = r["env_n"]
            steps = r["actions_count"]
            if steps >= 0 and env in bfs_steps_by_env:
                deltas.append(steps - bfs_steps_by_env[env])
        if deltas:
            delta_series.append(deltas)
            delta_labels.append(alg)

    if delta_series:
        plt.figure(figsize=(8, 5))
        _boxplot_with_labels(delta_series, delta_labels)
        plt.ylabel("Diferencia de pasos vs BFS")
        plt.axhline(0, color="gray", linestyle="--", linewidth=1)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        out_path = os.path.join(images_dir, "box_delta_steps_vs_bfs.png")
        plt.savefig(out_path)
        plt.close()

    # Boxplot: diferencia de estados expandidos vs BFS por algoritmo
    bfs_states_by_env = {}
    for r in data:
        if r["algorithm_name"] == "BFS" and r["states_n"] >= 0:
            bfs_states_by_env[r["env_n"]] = r["states_n"]

    delta_states_series = []
    delta_states_labels = []
    for alg in sorted({a for a in algorithms if a != "BFS"}):
        deltas = []
        for r in data:
            if r["algorithm_name"] != alg:
                continue
            env = r["env_n"]
            st = r["states_n"]
            if st >= 0 and env in bfs_states_by_env:
                deltas.append(st - bfs_states_by_env[env])
        if deltas:
            delta_states_series.append(deltas)
            delta_states_labels.append(alg)

    if delta_states_series:
        plt.figure(figsize=(8, 5))
        _boxplot_with_labels(delta_states_series, delta_states_labels)
        plt.ylabel("Diferencia de estados expandidos vs BFS")
        plt.axhline(0, color="gray", linestyle="--", linewidth=1)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        out_path = os.path.join(images_dir, "box_delta_states_vs_bfs.png")
        plt.savefig(out_path)
        plt.close()

    # Gráfico adicional: pasos promedio condicionados a éxito (0 si nunca resolvió, para mostrar todas)
    avg_steps = []
    for alg in algorithms:
        vals = [r["actions_count"] for r in data if r["algorithm_name"] == alg and r["actions_count"] >= 0]
        avg_steps.append(sum(vals) / len(vals) if vals else 0)

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, avg_steps)
    plt.ylabel("Pasos promedio (solo éxitos; 0 si ninguno)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out_path = os.path.join(images_dir, "bar_avg_steps_success.png")
    plt.savefig(out_path)
    plt.close()


if __name__ == "__main__":
    main()
