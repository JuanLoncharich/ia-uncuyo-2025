import csv
import math
import matplotlib.pyplot as plt


def load_results(path="results.csv"):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            data.append(
                {
                    "algorithm": row["algorithm"],
                    "episode": int(row["episode"]),
                    "reward": float(row["reward"]),
                    "done": row["done"] == "True",
                    "truncated": row["truncated"] == "True",
                    "steps": int(row["steps"]),
                }
            )
        return data


def main():
    data = load_results()
    algorithms = sorted({d["algorithm"] for d in data})

    wins = []
    avg_steps = []
    for alg in algorithms:
        alg_runs = [d for d in data if d["algorithm"] == alg]
        win_runs = [d for d in alg_runs if d["done"]]
        wins.append(len(win_runs))
        avg_steps.append(
            sum(r["steps"] for r in win_runs) / len(win_runs) if win_runs else math.nan
        )

    plt.figure()
    plt.bar(algorithms, wins)
    plt.ylabel("Victorias en 30 episodios")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("wins.png")

    plt.figure()
    plt.bar(algorithms, avg_steps)
    plt.ylabel("Pasos promedio (solo victorias)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("avg_steps.png")


if __name__ == "__main__":
    main()
