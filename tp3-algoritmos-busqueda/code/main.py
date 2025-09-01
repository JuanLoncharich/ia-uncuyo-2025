# main.py
import csv
import gymnasium as gym
import numpy as np

from runner import EpisodeRunner
from agent_bfs import BFSAgent
from agent_dfs import DFSAgent
from agent_dls import DLSAgent
from agent_ucs import UCSAgent
from agent_astar import AStarAgent

# Tu función ya existente:
def generate_large_custom_map(size=8, p_frozen=0.9, seed=None):
    """
    Genera un mapa personalizado de FrozenLake con:
    - Tamaño: size x size
    - Probabilidad p_frozen de que una celda sea F (hielo)
    - S y G colocados en las esquinas opuestas
    - El resto aleatorio según probabilidad
    """
    if seed is not None:
        np.random.seed(seed)

    # Crear una matriz de agujeros (H)
    grid = np.full((size, size), 'H')

    # Rellenar con hielo (F) según la probabilidad
    mask_frozen = np.random.random((size, size)) < p_frozen
    grid[mask_frozen] = 'F'

    # Colocar Start (S) y Goal (G) en esquinas opuestas
    grid[0, 0] = 'S'
    grid[size-1, size-1] = 'G'

    # Convertir a lista de strings
    desc = [''.join(row) for row in grid]
    return desc

if __name__ == "__main__":
    # Mapa determinista grande
    desc = generate_large_custom_map(size=100, p_frozen=0.92, seed=123)

    env = gym.make("FrozenLake-v1", desc=desc, is_slippery=False).env
    env = gym.wrappers.TimeLimit(env, max_episode_steps=2000)

    runner = EpisodeRunner(env)
    agents = [
        ("BFS (Anchura)", BFSAgent()),
        ("DFS (Profundidad)", DFSAgent()),
        ("DLS 50", DLSAgent(limit=50)),
        ("DLS 75", DLSAgent(limit=75)),
        ("DLS 100", DLSAgent(limit=100)),
        ("UCS (Costo Uniforme)", UCSAgent()),
        ("A* (Manhattan)", AStarAgent()),
    ]

    EPISODES = 30
    results = []

    for name, agent in agents:
        for episode in range(1, EPISODES + 1):
            reward, done, truncated, steps = runner.run(agent, verbose=False)
            results.append(
                {
                    "algorithm": name,
                    "episode": episode,
                    "reward": reward,
                    "done": done,
                    "truncated": truncated,
                    "steps": steps,
                }
            )

    with open("results.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["algorithm", "episode", "reward", "done", "truncated", "steps"]
        )
        writer.writeheader()
        writer.writerows(results)

    # Mostrar un resumen simple en consola
    for name, _ in agents:
        alg_results = [r for r in results if r["algorithm"] == name]
        wins = [r for r in alg_results if r["done"]]
        win_rate = len(wins) / EPISODES
        avg_steps = sum(r["steps"] for r in wins) / len(wins) if wins else float("nan")
        print(f"{name}: tasa de victoria {win_rate:.2%}, pasos promedio {avg_steps:.1f}")
