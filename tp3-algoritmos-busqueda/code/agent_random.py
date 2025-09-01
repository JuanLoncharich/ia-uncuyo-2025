from __future__ import annotations
import random
from typing import Optional


class RandomAgent:
    """
    Agente que selecciona acciones aleatorias reproducibles vía semilla.
    Implementa la misma interfaz (reset, act) usada por EpisodeRunner.
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self._rng = random.Random(seed)
        self._env = None

    def reset(self, env) -> None:
        self._env = env
        # Sembrar espacio de acciones para reproducibilidad adicional
        try:
            env.action_space.seed(self.seed)
        except Exception:
            pass

    def act(self, obs) -> int:
        # Si el espacio de acción provee sample(), úsalo
        if hasattr(self._env.action_space, "sample"):
            return self._env.action_space.sample()
        # Fallback por si acaso
        n = getattr(getattr(self, "_env", None), "action_space", None)
        return self._rng.randrange(n.n if n is not None else 4)

