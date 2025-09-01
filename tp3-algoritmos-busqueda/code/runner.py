# runner.py
from __future__ import annotations
import gymnasium as gym

class EpisodeRunner:
    def __init__(self, env: gym.Env):
        self.env = env

    def run(self, agent, seed: int | None = None, action_costs=None, verbose: bool = True):
        (state, info) = self.env.reset(seed=seed)
        agent.reset(self.env, action_costs=action_costs)

        if verbose:
            print("Numero de estados:", self.env.observation_space.n)
            print("Numero de acciones:", self.env.action_space.n)
            print("Posicion inicial del agente:", state)

        done = truncated = False
        step = 0
        reward = 0.0
        while not (done or truncated):
            action = agent.act(state)
            next_state, reward, done, truncated, _ = self.env.step(action)
            step += 1

            if verbose:
                print(
                    f"Paso {step} | Accion: {action} | Nuevo estado: {next_state} | Recompensa: {reward}"
                )
                if reward == 1.0:
                    print(f"¿Gano? (encontro el objetivo): {done}")
                else:
                    print(f"¿Gano? (encontro el objetivo): False")
                    print(f"¿Perdio? (se cayo): {done}")
                    print(
                        f"¿Freno? (alcanzo el maximo de pasos posible): {truncated}\n"
                    )

            state = next_state

        # Devolvemos también el número de pasos para facilitar el registro de
        # estadísticas en experimentos repetidos.
        return reward, done, truncated, step
