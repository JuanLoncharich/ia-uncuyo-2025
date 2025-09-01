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
                    "scenario": row["scenario"],
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
    scenarios = sorted({d["scenario"] for d in data})
    for scenario in scenarios:
        scen_runs = [d for d in data if d["scenario"] == scenario]
        algorithms = sorted({d["algorithm"] for d in scen_runs})

        wins = []
        avg_steps = []
        for alg in algorithms:
            alg_runs = [d for d in scen_runs if d["algorithm"] == alg]
            win_runs = [d for d in alg_runs if d["done"]]
            wins.append(len(win_runs))
            avg_steps.append(
                sum(r["steps"] for r in win_runs) / len(win_runs) if win_runs else math.nan
            )

        safe = scenario.replace(" ", "_").lower()

        plt.figure()
        plt.bar(algorithms, wins)
        plt.ylabel("Victorias en 30 episodios")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"wins_{safe}.png")

        plt.figure()
        plt.bar(algorithms, avg_steps)
        plt.ylabel("Pasos promedio (solo victorias)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"avg_steps_{safe}.png")


if __name__ == "__main__":
    main()
