# agent_astar.py
from typing import Optional, List, Callable, Tuple
from base_agent import BasePlannerAgent
from grid_planner import GridPlanner

class AStarAgent(BasePlannerAgent):
    def __init__(self, heuristic: Callable | None = None, step_cost: Callable | None = None, heuristic_weights: Tuple[int, int] | None = None):
        super().__init__()
        self.heuristic = heuristic
        self.step_cost = step_cost
        self.heuristic_weights = heuristic_weights

    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        if self.heuristic is not None:
            h = self.heuristic
        elif self.heuristic_weights is not None:
            wr, wc = self.heuristic_weights
            h = lambda rc: planner.weighted_manhattan(rc, planner.goal, wr, wc)
        else:
            h = lambda rc: planner.manhattan(rc, planner.goal)
        return planner.astar(h, step_cost=self.step_cost)
