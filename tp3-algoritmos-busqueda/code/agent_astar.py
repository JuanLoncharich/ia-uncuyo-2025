# agent_astar.py
from typing import Optional, List, Callable
from base_agent import BasePlannerAgent
from grid_planner import GridPlanner

class AStarAgent(BasePlannerAgent):
    def __init__(self, heuristic: Callable = None):
        super().__init__()
        self.heuristic = heuristic

    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        h = (lambda rc: planner.manhattan(rc, planner.goal)) if self.heuristic is None else self.heuristic
        return planner.astar(h)
