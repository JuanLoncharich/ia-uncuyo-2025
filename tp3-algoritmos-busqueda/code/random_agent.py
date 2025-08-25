import gymnasium as gym
import generate_random_map as random_map

desc_large = random_map.generate_large_custom_map(size=100, p_frozen=0.92, seed=123)

# Crear entorno determinista
env = gym.make('FrozenLake-v1', desc=desc_large, is_slippery=False, render_mode='human').env

# Modificar el límite de pasos a 1000
env = gym.wrappers.TimeLimit(env, max_episode_steps=1000)


print("Numero de estados:", env.observation_space.n)
print("Numero de acciones:", env.action_space.n)

state = env.reset()
print("Posicion inicial del agente:", state[0])
done = truncated = False
i=0
while not (done or truncated):
    action = env.action_space.sample()
    i+=1
    # Accion aleatoria
    next_state, reward, done, truncated, _ = env.step(action)
    print(f"Accion: {action}, Nuevo estado: {next_state}, Recompensa: {reward}")
    if not reward == 1.0:
        print(f"¿Gano? (encontro el objetivo): False")
        print(f"¿Perdio? (se cayo): {done}")
        print(f"¿Freno? (alcanzo el maximo de pasos posible): {truncated}\n")
    else:
        print(f"¿Gano? (encontro el objetivo): {done}")
    state = next_state