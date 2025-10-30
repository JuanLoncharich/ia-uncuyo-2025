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
from agent_random import RandomAgent

# Tu función ya existente:
def generate_random_map_custom(size=8, p_frozen=0.9, seed=None):
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
    # Elegir posiciones aleatorias para S y G, asegurando que sean distintas
    start_pos = tuple(np.random.choice(size, 2, replace=False))
    goal_pos = tuple(np.random.choice(size, 2, replace=False))
    while goal_pos == start_pos:
        goal_pos = tuple(np.random.choice(size, 2, replace=False))
    grid[start_pos] = 'S'
    grid[goal_pos] = 'G'

    # Convertir a lista de strings
    desc = [''.join(row) for row in grid]
    return desc

if __name__ == "__main__":
    EPISODES = 30
    SIZE = 100
    P_FROZEN = 0.92
    MAX_STEPS = 1000  # Vida del agente

    # Función de costo del escenario 2 (para evaluar costo de acciones)
    def step_cost_s1_from_action(a: int) -> int:
        return 1

    def step_cost_s2_from_action(a: int) -> int:
        # LEFT/RIGHT => 1, UP/DOWN => 10
        return 10 if a in (1, 3) else 1

    def step_cost_s2_from_delta(delta: tuple[int, int]) -> int:
        dr, dc = delta
        if dr != 0 and dc == 0:
            return 10
        return 1

    SEEDS = [i for i in range(1, EPISODES + 1)]

    results = []

    import time

    for ep_idx, seed in enumerate(SEEDS, start=1):
        # Generar mapa determinista para esta semilla
        desc = generate_random_map_custom(size=SIZE, p_frozen=P_FROZEN, seed=seed)

        # Imprimir entorno generado una vez (env 1)
        if ep_idx == 1:
            print("Entorno generado (S=Start, G=Goal, F=Frozen, H=Hole):")
            for row in desc:
                print(row)

        # Entorno determinista con límite de pasos
        env = gym.make("FrozenLake-v1", desc=desc, is_slippery=False).env
        env = gym.wrappers.TimeLimit(env, max_episode_steps=MAX_STEPS)
        runner = EpisodeRunner(env)
        # Planificador auxiliar para métricas por-entorno (Manhattan)
        from grid_planner import GridPlanner
        planner_env = GridPlanner(desc)
        manhattan_dist = planner_env.manhattan(planner_env.start, planner_env.goal)

        agents = [
            ("Random", RandomAgent(seed=seed)),
            ("BFS", BFSAgent()),
            ("DFS", DFSAgent()),
            ("DLS50", DLSAgent(limit=50)),
            ("DLS75", DLSAgent(limit=75)),
            ("DLS100", DLSAgent(limit=100)),
            ("UCS_E1", UCSAgent()),
            ("UCS_E2", UCSAgent(step_cost=step_cost_s2_from_delta)),
            ("AStar_E1", AStarAgent()),
            ("AStar_E2", AStarAgent(step_cost=step_cost_s2_from_delta, heuristic_weights=(10, 1))),
        ]

        for name, agent in agents:
            t0 = time.perf_counter()
            reward, done, truncated, steps, actions_taken = runner.run(agent, verbose=False, seed=seed, name=name)
            t1 = time.perf_counter()

            # Métricas
            solution_found = bool(done and reward == 1.0)
            if solution_found:
                actions_count = sum(step_cost_s1_from_action(a) for a in actions_taken)
                actions_cost = sum(step_cost_s2_from_action(a) for a in actions_taken)
            else:
                actions_count = -1
                actions_cost = -1
            states_n = getattr(agent, "last_expanded", None)
            states_n = int(states_n) if (states_n is not None and solution_found) else -1

            # Monotone path check (only RIGHT or DOWN moves)
            try:
                plan_actions = list(getattr(agent, "plan", []) or [])
            except Exception:
                plan_actions = []
            monotone_rd = (solution_found and len(plan_actions) == steps and all(a in (1, 2) for a in plan_actions))

            # Para el primer entorno, imprimir la secuencia de estados completa (BFS si hay solución)
            if ep_idx == 1 and name == "BFS" and solution_found:
                # Reconstruir trayectoria de estados desde acciones
                # Usamos GridPlanner para conocer coordenadas de inicio
                from grid_planner import GridPlanner

                planner = GridPlanner(desc)
                state_seq = planner.states_from_actions(agent.plan or [])
                print("\nSecuencia de estados (fila, columna) para BFS en env 1:")
                for s in state_seq:
                    print(s)

            results.append(
                {
                    "algorithm_name": name,
                    "env_n": ep_idx,
                    "seed": seed,
                    "manhattan": int(manhattan_dist),
                    "monotone_rd": bool(monotone_rd),
                    "states_n": states_n,
                    "actions_count": actions_count,
                    "actions_cost": actions_cost,
                    "time": t1 - t0,
                    "solution_found": solution_found,
                }
            )

    # Volcar resultados con el formato requerido en la carpeta del TP
    import os
    here = os.path.dirname(__file__)
    out_csv = os.path.abspath(os.path.join(here, os.pardir, "results.csv"))
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "algorithm_name",
                "env_n",
                "seed",
                "manhattan",
                "monotone_rd",
                "states_n",
                "actions_count",
                "actions_cost",
                "time",
                "solution_found",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    # Resumen simple en consola
    print("\nResumen (soluciones encontradas por algoritmo):")
    algos = sorted({r["algorithm_name"] for r in results})
    for alg in algos:
        rows = [r for r in results if r["algorithm_name"] == alg]
        solved = sum(1 for r in rows if r["solution_found"])
        print(f"{alg}: {solved}/{EPISODES} soluciones")
