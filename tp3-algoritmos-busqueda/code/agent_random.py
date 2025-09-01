from typing import Optional


class RandomAgent:
    """Agent that selects actions uniformly at random."""

    def __init__(self):
        self.env = None

    def reset(self, env, action_costs: Optional[dict] = None) -> None:
        self.env = env

    def act(self, obs) -> int:
        return self.env.action_space.sample()
