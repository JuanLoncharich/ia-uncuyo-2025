# base_agent.py
from __future__ import annotations
from typing import List, Optional
from grid_planner import GridPlanner

class BasePlannerAgent:
    """
    Construye un plan al hacer reset(env) y luego devuelve acciones con act(obs).
    Subclases implementan _build_plan(planner) -> List[int] | None.
    """

    def __init__(self):
        self.plan: Optional[List[int]] = None
        self.ptr: int = 0
        self._env = None  # para fallback

    def reset(self, env, action_costs=None) -> None:
        self._env = env
        planner = GridPlanner(env.unwrapped.desc, action_costs=action_costs)
        self.plan = self._build_plan(planner)
        self.ptr = 0

    def act(self, obs) -> int:
        if not self.plan:
            # Sin plan: fallback (RIGHT si existe, luego DOWN)
            n = getattr(getattr(self, "_env", None), "action_space", None)
            if n is not None and n.n >= 3:
                return 2
            return 1 if (n is not None and n.n > 1) else 0
        if self.ptr >= len(self.plan):
            # Plan agotado: repetir última acción
            return self.plan[-1]
        a = self.plan[self.ptr]
        self.ptr += 1
        return a

    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        raise NotImplementedError
