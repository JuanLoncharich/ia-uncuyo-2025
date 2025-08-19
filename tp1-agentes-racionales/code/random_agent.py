import sys
import os
from typing import Optional
import random

# Add the parent directory to the path to import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent


class RandomAgent(BaseAgent):
    """
    An agent that performs random actions in the vacuum cleaner world.
    
    This agent randomly chooses to move in one of four directions, clean, or do nothing.
    It serves as a simple example of how to implement an agent that interacts with the environment.
    """
    
    def __init__(self, 
                 server_url: str = "http://localhost:5000", 
                 enable_ui: bool = False,
                 record_game: bool = False, 
                 replay_file: Optional[str] = None,
                 cell_size: int = 60,
                 fps: int = 10,
                 auto_exit_on_finish: bool = True,
                 live_stats: bool = False):
        super().__init__(server_url, "RandomAgent", enable_ui, record_game, 
                         replay_file, cell_size, fps, auto_exit_on_finish, live_stats)
    
    def get_strategy_description(self) -> str:
        return "Randomly moves and cleans"

    def think(self) -> bool:
        """
        Implements the random decision logic of the agent.
        
        Returns:
            bool: True if the action was executed successfully, False if simulation should stop.
        """
        if not self.is_connected():
            return False
        
        perception = self.get_perception()
        if not perception or perception.get('is_finished', False):
            return False

        # List of possible actions as callable methods
        possible_actions = [
            self.up,
            self.down,
            self.left,
            self.right,
            self.suck,
            self.idle
        ]

        # Choose a random action and execute it
        action = random.choice(possible_actions)
        return action()  # Returns True if action was accepted (e.g., didn't hit wall)


def run_random_agent_simulation(size_x: int = 8, size_y: int = 8, 
                               dirt_rate: float = 0.3, 
                               server_url: str = "http://localhost:5000",
                               verbose: bool = True) -> int:
    """
    Function to run a simulation with the RandomAgent.
    """
    agent = RandomAgent(server_url, enable_ui=True, live_stats=verbose, record_game=False)
    
    try:
        if not agent.connect_to_environment(size_x, size_y, dirt_rate):
            print("Failed to connect to environment.")
            return 0
        
        performance = agent.run_simulation(verbose=verbose)
        return performance
    
    finally:
        agent.disconnect()


if __name__ == "__main__":
    print("Random Agent - Random Action Strategy")
    print("Make sure the environment server is running on localhost:5000")
    print("Strategy: Randomly move, clean, or idle at each step")
    print()
    
    performance = run_random_agent_simulation(verbose=True)
    print(f"\nFinal performance: {performance}")
    
    print("\nThis agent uses the same structure as ExampleAgent.")
    print("You can now register it in run_agent.py like:")
    print('    "random": RandomAgent')