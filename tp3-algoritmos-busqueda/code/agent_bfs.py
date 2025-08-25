# agent_bfs.py
from typing import Optional, List
from base_agent import BasePlannerAgent
from grid_planner import GridPlanner

class BFSAgent(BasePlannerAgent):
    def _build_plan(self, planner: GridPlanner) -> Optional[List[int]]:
        return planner.bfs()
