# agent_ucs.py
from typing import Optional, List, Callable
from base_agent import BasePlannerAgent
from grid_planner import GridPlanner

class UCSAgent(BasePlannerAgent):
    def __init__(self, step_cost: Callable | None = None):
        super().__init__()
        self.step_cost = step_cost

    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        return planner.ucs(step_cost=self.step_cost)
