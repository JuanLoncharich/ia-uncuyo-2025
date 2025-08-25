# agent_dls.py
from typing import Optional, List
from base_agent import BasePlannerAgent
from grid_planner import GridPlanner

class DLSAgent(BasePlannerAgent):
    def __init__(self, limit: int):
        super().__init__()
        self.limit = limit

    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        return planner.dls(self.limit)
