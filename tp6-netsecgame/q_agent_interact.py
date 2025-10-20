"""
q_agent_interact.py
===================

This module defines a high‑level Q‑learning agent for the NetSecGame
environment.  The agent is based on the provided QAgent template but has
been adapted to operate on an abstracted state representation: instead of
using full game states keyed by IP addresses and services, it compresses
the state into a tuple of counts describing the number of networks,
hosts, services and data items in various categories.  The agent learns
Q‑values over these abstract states for the five high‑level action types
defined by the environment: ``ScanNetwork``, ``FindServices``, ``ExploitService``,
``FindData`` and ``ExfiltrateData``.

During action selection the agent uses an epsilon‑greedy policy: with
probability ``epsilon`` it explores by choosing a random action type,
otherwise it exploits by selecting the action type with the highest
estimated Q‑value.  A simple heuristic then chooses a concrete action
from the set of valid actions matching the selected high‑level action type.

The Q‑learning update rule is applied after each step, using a
discount factor ``gamma`` and learning rate ``alpha``.  The Q‑table is
stored as a dictionary keyed by ``(state_id, action_name)``.  The
state identifier is computed from the abstract state tuple via a
mapping stored in ``self.state_mapping``.

Because the environment code is not available in this repository,
some assumptions have been made about the structure of ``GameState``
and ``Action`` objects.  The helper functions attempt to extract
information from both attribute and dictionary interfaces.  When used
inside the actual NetSecGame environment these functions should work
without further modification, but they can be extended if needed.
"""

from __future__ import annotations

import argparse
import json
import random
import pickle
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, List, Any, Callable
import logging
import os
from collections import defaultdict, Counter

logger = logging.getLogger("q_agent_interact")


try:
    # NetSecGame imports.  These will work when running inside the game
    # environment.  If running outside, these imports will fail and the
    # agent cannot interact with the environment.
    from AIDojoCoordinator.game_components import Action, Observation, GameState, AgentStatus
    from NetSecGameAgents.agents.base_agent import BaseAgent
    from NetSecGameAgents.agents.agent_utils import generate_valid_actions
except ImportError:
    # Provide minimal stubs so that type hints remain valid.  These stubs
    # do not implement any functionality and should not be used outside
    # the game environment.
    Action = Any  # type: ignore
    Observation = Any  # type: ignore
    GameState = Any  # type: ignore
    AgentStatus = Any  # type: ignore
    BaseAgent = object  # type: ignore
    def generate_valid_actions(state: GameState) -> List[Any]:
        return []


@dataclass
class StateCounts:
    """Container for abstracted state counts used as a key in the Q‑table."""

    num_known_nets: int
    num_known_hosts: int
    num_scanned_hosts: int
    num_known_services: int
    num_exploited_services: int
    num_known_data: int
    num_taken_data: int
    num_ready_data: int
    num_exfiltrated_data: int

    def as_tuple(self) -> Tuple[int, ...]:
        return (
            self.num_known_nets,
            self.num_known_hosts,
            self.num_scanned_hosts,
            self.num_known_services,
            self.num_exploited_services,
            self.num_known_data,
            self.num_taken_data,
            self.num_ready_data,
            self.num_exfiltrated_data,
        )


def _extract_from_state(state: GameState, attr_names: Tuple[str, ...], default: Any) -> Any:
    """Attempt to read sequence/dict attributes from the environment state safely."""
    for name in attr_names:
        value = getattr(state, name, None)
        if value is not None:
            return value
    if isinstance(state, dict):
        for name in attr_names:
            if name in state:
                return state[name]
    if hasattr(state, "__getitem__"):
        for name in attr_names:
            try:
                value = state[name]  # type: ignore[index]
            except Exception:
                continue
            if value is not None:
                return value
    return default


def _state_to_dict(state: GameState) -> Any:
    if hasattr(state, "to_dict"):
        try:
            return state.to_dict()
        except Exception:
            pass
    if isinstance(state, dict):
        return state
    if hasattr(state, "__dict__"):
        return {key: value for key, value in state.__dict__.items() if not key.startswith("_")}
    return state


def _summarise_state(state: GameState) -> Dict[str, Any]:
    data = _state_to_dict(state)
    if not isinstance(data, dict):
        return {"state_repr": data}
    summary: Dict[str, Any] = {}
    for key, value in data.items():
        summary[key] = _summarise_value(value)
    return summary


def _summarise_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _summarise_value(v) for k, v in value.items()}
    if isinstance(value, (list, set, tuple)):
        return len(value)
    return value


def _describe_action(action: Any) -> str:
    name = getattr(action, "name", None) or getattr(action, "action_type", None) or type(action).__name__
    details: Dict[str, Any] = {}
    for attr in ("target_network", "target_host", "target_service", "target_port", "parameters"):
        val = getattr(action, attr, None)
        if val:
            details[attr] = val
    if not details and hasattr(action, "__dict__"):
        details = {k: v for k, v in action.__dict__.items() if not k.startswith("_")}
    return f"{name} {details}" if details else str(name)


def _get_action_parameter(action: Any, name: str) -> Any:
    """Extract an action parameter regardless of attribute vs dict access."""
    value = getattr(action, name, None)
    if value is not None:
        return value
    params = getattr(action, "parameters", None)
    if isinstance(params, dict):
        return params.get(name)
    return None


def _matches_agent_status(value: Any, status: AgentStatus) -> bool:
    """Return True when *value* represents the given AgentStatus."""
    if value is None:
        return False
    try:
        if isinstance(value, AgentStatus):
            return value == status
    except Exception:
        pass
    if isinstance(value, str):
        stripped = value.replace("AgentStatus.", "")
        try:
            target = status.value  # type: ignore[attr-defined]
        except Exception:
            target = str(status)
        return stripped == target
    try:
        return str(value) == str(status.value)  # type: ignore[attr-defined]
    except Exception:
        return str(value) == str(status)


class HighLevelQAgent(BaseAgent):
    """
    A Q‑learning agent that operates on a compressed state representation and
    learns values for high‑level action types.  Concrete action parameters
    are chosen with simple heuristics from the set of valid actions.
    """

    # The high‑level actions recognised by the environment.  These names must
    # match the names of Action objects provided by generate_valid_actions().
    ACTION_TYPES = [
        "ScanNetwork",
        "FindServices",
        "ExploitService",
        "FindData",
        "ExfiltrateData",
    ]
    ACTION_LOG_LIMIT = 5

    def __init__(
        self,
        host: str,
        port: int,
        role: str = "Attacker",
        alpha: float = 0.1,
        gamma: float = 0.9,
        epsilon_start: float = 0.9,
        epsilon_end: float = 0.1,
        epsilon_max_episodes: int = 5000,
        apm_limit: int | None = None,
    ) -> None:
        try:
            super().__init__(host, port, role)
        except TypeError:
            if BaseAgent is object:
                pass
            else:
                raise
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_max_episodes = epsilon_max_episodes
        self.current_epsilon = epsilon_start
        self.apm_limit = apm_limit
        self.inter_action_interval = 60 / apm_limit if apm_limit else 0.0
        # Q‑table and state mapping
        self.q_values: Dict[Tuple[int, str], float] = {}
        self.state_mapping: Dict[Tuple[int, ...], int] = {}
        # Track exploited services to avoid repeated exploitation
        self.exploited_services: set[Tuple[str, str]] = set()
        # Optional progress callback supplied by the driver code
        self.progress_callback: Callable[[str], None] | None = None
        self._logged_state_summaries: set[int] = set()
        self._logged_action_states: set[int] = set()
        # [QL] minimal params & storage
        self.q_enabled = True
        self.q_gamma = 0.95
        self.q_eps0 = 0.7
        self.q_eps_min = 0.05
        self.q_alpha_beta = 0.5
        self.q_scale = 1000.0
        self.q_clip = 1.0
        self.q_episode_idx = 0
        self.q_table: Dict[int, Dict[str, float]] = defaultdict(dict)
        self.q_visits: Counter[Tuple[int, str]] = Counter()
        self.q_rng = __import__("random").Random(1337)
        self._ql_initial_state_id: int | None = None
        self._ql_initial_actions: List[Action] = []
        env_toggle = os.environ.get("QLEARN")
        if env_toggle is not None:
            self.q_enabled = env_toggle not in {"0", "false", "False"}
        self.q_enabled_learn = True
        self.q_eps_start = self.q_eps0
        self.q_eps_end = self.q_eps_min
        self.q_eps_max = 1
        self.q_model_path = "q_table.pkl"
        try:
            blob = pickle.load(open(self.q_model_path, "rb"))
            self.q_table = blob.get("Q", self.q_table)
            self.q_visits = blob.get("visits", self.q_visits)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # State abstraction
    # ------------------------------------------------------------------
    def compute_state_counts(self, state: GameState) -> StateCounts:
        """Compute the abstracted state counts from a GameState.

        The NetSecGame environment uses a state representation that includes
        sets of networks, known hosts, controlled hosts, known services and
        known data【495200347051879†L462-L469】.  This method extracts those sets
        using a combination of attribute and dictionary access, then derives
        additional counts representing scanned hosts, exploited services and
        data status.

        Notes
        -----
        - ``num_scanned_hosts`` is approximated as the number of entries in
          the known services dictionary, since a host must be scanned to know
          its services.
        - ``num_exploited_services`` is maintained by the agent based on
          exploitation actions previously taken; it is not directly available
          from the state.
        - Data status (taken/ready/exfiltrated) is not provided by the
          environment state.  We set these counts to zero and encourage
          users to extend this logic if their environment exposes this
          information.
        """
        # Extract sets/dicts from the state.  Try attribute access first,
        # fall back to item access if the state acts like a dictionary.
        nets = _extract_from_state(state, ("nets", "networks"), [])
        known_hosts = _extract_from_state(state, ("known_hosts",), [])
        known_services = _extract_from_state(state, ("known_services",), {})
        known_data = _extract_from_state(state, ("known_data",), {})

        # Counts
        num_known_nets = len(nets)
        num_known_hosts = len(known_hosts)
        # Use the keys of known_services as scanned hosts if possible
        if isinstance(known_services, dict):
            num_scanned_hosts = len(known_services)
            num_known_services = sum(len(svcs) for svcs in known_services.values())
        else:
            num_scanned_hosts = 0
            num_known_services = 0
        num_known_data = 0
        if isinstance(known_data, dict):
            num_known_data = sum(len(items) for items in known_data.values())

        num_exploited_services = len(self.exploited_services)
        # Data status counts: these are placeholders.  Extend if the
        # environment exposes data with status (found/taken/exfiltrated).
        num_taken_data = 0
        num_ready_data = 0
        num_exfiltrated_data = 0

        return StateCounts(
            num_known_nets=num_known_nets,
            num_known_hosts=num_known_hosts,
            num_scanned_hosts=num_scanned_hosts,
            num_known_services=num_known_services,
            num_exploited_services=num_exploited_services,
            num_known_data=num_known_data,
            num_taken_data=num_taken_data,
            num_ready_data=num_ready_data,
            num_exfiltrated_data=num_exfiltrated_data,
        )

    def get_state_id(self, state: GameState) -> int:
        """Map the abstract state counts to a unique integer identifier.

        Unknown count tuples are added to the mapping automatically.
        """
        counts = self.compute_state_counts(state)
        key = counts.as_tuple()
        if key not in self.state_mapping:
            self.state_mapping[key] = len(self.state_mapping)
        return self.state_mapping[key]

    # ------------------------------------------------------------------
    # Diagnostic helpers
    # ------------------------------------------------------------------
    def _notify_progress(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    def _emit_state_summary(self, state_id: int, state: GameState, context: str) -> None:
        if state_id in self._logged_state_summaries:
            return
        summary = _summarise_state(state)
        logger.info("%s state summary (state_id=%s): %s", context, state_id, summary)
        self._notify_progress(f"{context} state summary (state_id={state_id}): {summary}")
        self._logged_state_summaries.add(state_id)

    def _emit_action_choices(self, state_id: int, actions: List[Action], context: str) -> None:
        if not actions:
            self._notify_progress(f"{context} state_id={state_id}: no valid actions")
            logger.warning("%s state_id=%s has no valid actions", context, state_id)
            return
        if state_id in self._logged_action_states:
            return
        descriptions = [_describe_action(action) for action in actions[: self.ACTION_LOG_LIMIT]]
        if len(actions) > self.ACTION_LOG_LIMIT:
            descriptions.append(f"... (+{len(actions) - self.ACTION_LOG_LIMIT} more)")
        logger.info("%s valid actions (state_id=%s, total=%s): %s", context, state_id, len(actions), descriptions)
        self._notify_progress(
            f"{context} valid actions (state_id={state_id}, total={len(actions)}): {descriptions}"
        )
        self._logged_action_states.add(state_id)

    def _emit_environment_info(self, observation: Observation, episode_number: int, context: str) -> None:
        state = observation.state
        state_id = self.get_state_id(state)
        self._emit_state_summary(state_id, state, f"[Episode {episode_number}] {context}")
        info_payload = getattr(observation, "info", None)
        if info_payload:
            logger.info("[Episode %s] %s info: %s", episode_number, context, info_payload)
            self._notify_progress(f"[Episode {episode_number}] {context} info: {info_payload}")
        actions = list(generate_valid_actions(state))
        self._emit_action_choices(state_id, actions, f"[Episode {episode_number}] {context}")

    # ------------------------------------------------------------------
    # Q-learning augmentation helpers
    # ------------------------------------------------------------------
    def _ql_action_key(self, act: Action) -> str:
        if hasattr(act, "to_compact_string"):
            try:
                return act.to_compact_string()
            except Exception:
                pass
        if hasattr(act, "name") and act.name:
            return str(act.name)
        return repr(act)

    def _ql_epsilon(self) -> float:
        es = getattr(self, "q_eps_start", self.q_eps0)
        ee = getattr(self, "q_eps_end", self.q_eps_min)
        em = max(1.0, float(getattr(self, "q_eps_max", 1)))
        idx = float(self.q_episode_idx)
        if idx >= em:
            return ee
        frac = 1.0 - (idx / em)
        frac = max(0.0, frac)
        return ee + (es - ee) * frac

    def _ql_alpha(self, state_id: int, action_key: str) -> float:
        visits = self.q_visits[(state_id, action_key)]
        n = 1.0 + visits
        return 1.0 / (1.0 + self.q_alpha_beta * n)

    def _ql_proc_reward(self, reward: float) -> float:
        if self.q_scale and self.q_scale != 1.0:
            reward = reward / self.q_scale
        if self.q_clip and self.q_clip > 0.0:
            reward = max(-self.q_clip, min(self.q_clip, reward))
        return reward

    def _ql_log_progress(self, train_reward: float, steps: int) -> None:
        if self._ql_initial_state_id is None:
            return
        actions = self._ql_initial_actions or []
        qvals = [
            self.q_table[self._ql_initial_state_id].get(self._ql_action_key(act), 0.0)
            for act in actions
        ]
        qvals = [v for v in qvals if v is not None]
        qvals.sort(reverse=True)
        q0_max = qvals[0] if qvals else 0.0
        q0_gap = (qvals[0] - qvals[1]) if len(qvals) > 1 else 0.0
        print(
            json.dumps(
                {
                    "ep": self.q_episode_idx,
                    "eps": round(self._ql_epsilon(), 4),
                    "reward": round(train_reward, 4),
                    "steps": steps,
                    "q0_max": round(q0_max, 4),
                    "q0_gap": round(q0_gap, 4),
                }
            )
        )

    def _ql_checkpoint(self, force: bool = False) -> None:
        if not self.q_enabled or not self.q_enabled_learn:
            return
        if not force and (self.q_episode_idx % 500 != 0):
            return
        try:
            path = Path(self.q_model_path or "q_table.pkl")
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump({"Q": self.q_table, "visits": self.q_visits}, f)
        except Exception as exc:
            logger.warning("[ql] save failed: %s", exc)

    def _ql_read_value(self, state_id: int, act: Action) -> float:
        a_key = self._ql_action_key(act)
        table = self.q_table.get(state_id, {})
        if a_key in table:
            return table[a_key]
        act_name = getattr(act, "name", None) or getattr(act, "action_type", None) or ""
        return self.q_values.get((state_id, str(act_name)), 0.0)

    def _ql_seed_from_legacy(self, state_id: int, actions: List[Action]) -> None:
        if not actions:
            return
        table = self.q_table.setdefault(state_id, {})
        for act in actions:
            a_key = self._ql_action_key(act)
            if a_key in table:
                continue
            act_name = getattr(act, "name", None) or getattr(act, "action_type", None) or ""
            legacy_val = self.q_values.get((state_id, str(act_name)))
            if legacy_val is not None:
                table[a_key] = legacy_val

    # ------------------------------------------------------------------
    # Q‑learning helper methods
    # ------------------------------------------------------------------
    def max_action_q(self, observation: Observation) -> float:
        """Return the maximum Q‑value over all high‑level actions for the
        current abstract state.

        This method computes the abstract state ID and then iterates over
        the predefined high‑level action types, returning the highest Q
        estimate found.  Missing entries in the Q‑table default to 0.
        """
        state_id = self.get_state_id(observation.state)
        max_q = 0.0
        for action_name in self.ACTION_TYPES:
            q_val = self.q_values.get((state_id, action_name), 0.0)
            if q_val > max_q:
                max_q = q_val
        return max_q

    def select_action(self, observation: Observation, testing: bool = False) -> Tuple[Action, int, str]:
        """Select a concrete action from the valid actions using epsilon‑greedy.

        Parameters
        ----------
        observation: Observation
            Current observation containing the game state.
        testing: bool
            If True, always exploit (no exploration).

        Returns
        -------
        (Action, state_id, selected_action_name)
            The chosen Action object, the abstract state identifier and
            the high‑level action type that was selected.
        """
        state = observation.state
        state_id = self.get_state_id(state)
        # Extract valid actions from the environment
        valid_actions = list(generate_valid_actions(state))
        if not valid_actions:
            # If no actions are available, return None
            logger.warning("No valid actions available for state_id=%s", state_id)
            return None, state_id, ""

        # Determine whether to explore or exploit
        effective_epsilon = 0.0 if testing else self.current_epsilon
        explore = (effective_epsilon > 0.0) and (random.uniform(0, 1) < effective_epsilon)
        if self.q_enabled:
            explore = False
        logger.debug(
            "Selecting action for state_id=%s testing=%s epsilon=%.4f explore=%s valid_actions=%s",
            state_id,
            testing,
            effective_epsilon,
            explore,
            len(valid_actions),
        )

        # Choose an action type
        if explore:
            # Exploration: random high‑level action
            chosen_action_type = random.choice(self.ACTION_TYPES)
        else:
            # Exploitation: pick the action type with the highest Q‑value
            best_val = -float("inf")
            chosen_action_type = self.ACTION_TYPES[0]
            for act_name in self.ACTION_TYPES:
                q_val = self.q_values.get((state_id, act_name), 0.0)
                if q_val > best_val:
                    best_val = q_val
                    chosen_action_type = act_name

        # Filter valid actions to those matching the chosen high‑level type
        matching_actions = []
        for act in valid_actions:
            # Try to compare by name or type
            name = getattr(act, "name", None)
            if name is None:
                name = getattr(act, "action_type", None)
            if name is None:
                # Fallback: string representation may include the action type
                name = str(act)
            if chosen_action_type in str(name):
                matching_actions.append(act)

        # If no concrete action matches the selected type, fall back to random
        if matching_actions:
            concrete_action = random.choice(matching_actions)
        else:
            concrete_action = random.choice(valid_actions)
            # Determine action type for unknown fallback
            fallback_type = getattr(concrete_action, "name", chosen_action_type)
            logger.debug(
                "No matching actions for %s; falling back to %s",
                chosen_action_type,
                fallback_type,
            )
            chosen_action_type = fallback_type

        if self.q_enabled and valid_actions:
            eps = 0.0 if testing else self._ql_epsilon()
            if self.q_rng.random() < eps:
                concrete_action = self.q_rng.choice(valid_actions)
            else:
                best_q = -float("inf")
                best_act = None
                for act in valid_actions:
                    q_val = self._ql_read_value(state_id, act)
                    if q_val > best_q:
                        best_q = q_val
                        best_act = act
                if best_act is None:
                    best_act = valid_actions[0]
                concrete_action = best_act
            chosen_action_type = getattr(concrete_action, "name", chosen_action_type)

        # Initialise Q‑value entry if necessary
        if (state_id, chosen_action_type) not in self.q_values:
            self.q_values[(state_id, chosen_action_type)] = 0.0

        logger.debug(
            "Selected action=%s state_id=%s q_value=%.4f",
            chosen_action_type,
            state_id,
            self.q_values.get((state_id, chosen_action_type), 0.0),
        )
        return concrete_action, state_id, chosen_action_type

    def update_q_value(
        self,
        state_id: int,
        action_name: str,
        reward: float,
        next_observation: Observation,
    ) -> None:
        """Apply the Q‑learning update rule to the Q‑table entry.

        Q(s,a) ← Q(s,a) + α [r + γ max_a′ Q(s′,a′) − Q(s,a)]
        """
        # Current Q
        current_q = self.q_values.get((state_id, action_name), 0.0)
        # Target: reward plus discounted value of next state
        max_next_q = self.max_action_q(next_observation)
        target = reward + self.gamma * max_next_q
        # Update
        new_q = current_q + self.alpha * (target - current_q)
        self.q_values[(state_id, action_name)] = new_q
        logger.debug(
            "Q-update state_id=%s action=%s reward=%.2f current=%.4f target=%.4f new=%.4f",
            state_id,
            action_name,
            reward,
            current_q,
            target,
            new_q,
        )

    # ------------------------------------------------------------------
    # Reward handling
    # ------------------------------------------------------------------
    def recompute_reward(self, observation: Observation) -> Observation:
        """Override reward computation to include detection penalties and
        success bonuses.

        The NetSecGame environment provides sparse rewards: the agent receives
        a small penalty for each step and larger rewards or penalties when
        succeeding, failing or timing out【495200347051879†L526-L531】.  This method
        translates the ``info['end_reason']`` into a numerical reward.
        """
        state = observation.state
        reward = observation.reward
        end = observation.end
        info = observation.info
        end_reason = info.get("end_reason") if info else None
        if _matches_agent_status(end_reason, AgentStatus.Fail):
            reward = -1000
        elif _matches_agent_status(end_reason, AgentStatus.Success):
            reward = 1000
        elif _matches_agent_status(end_reason, AgentStatus.TimeoutReached):
            reward = -100
        else:
            # Small negative reward to encourage shorter trajectories
            reward = -1
        return Observation(state, reward, end, info)

    # ------------------------------------------------------------------
    # Epsilon scheduling
    # ------------------------------------------------------------------
    def update_epsilon(self, episode_number: int) -> None:
        """Decay epsilon linearly over ``epsilon_max_episodes`` episodes."""
        decay_rate = max((self.epsilon_max_episodes - episode_number) / self.epsilon_max_episodes, 0)
        self.current_epsilon = (self.epsilon_start - self.epsilon_end) * decay_rate + self.epsilon_end
        logger.debug("Epsilon updated after episode %s to %.4f", episode_number, self.current_epsilon)

    # ------------------------------------------------------------------
    # Main gameplay loop
    # ------------------------------------------------------------------
    def play_episode_from_observation(
        self,
        initial_observation: Observation,
        episode_number: int,
        testing: bool = False,
    ) -> Tuple[Observation, int, float]:
        """Run a single episode of the game.

        Returns the final observation (after the episode ends) and the number of
        steps taken.  During training the Q‑table is updated after each
        transition; during testing the policy is fixed.  The cumulative reward
        for the episode is also returned for logging.
        """
        # Reset per-episode bookkeeping
        self.exploited_services.clear()
        self._logged_state_summaries.clear()
        self._logged_action_states.clear()
        observation = initial_observation
        if observation is None:
            raise RuntimeError("Episode cannot start without an initial observation.")
        self._ql_initial_state_id = None
        self._ql_initial_actions = []
        self._emit_environment_info(observation, episode_number, "initial")
        ql_total_reward = 0.0
        if self.q_enabled:
            initial_state = observation.state
            self._ql_initial_state_id = self.get_state_id(initial_state)
            self._ql_initial_actions = list(generate_valid_actions(initial_state))
            self._ql_seed_from_legacy(self._ql_initial_state_id, self._ql_initial_actions)
        episode_epsilon = 0.0 if testing else self.current_epsilon
        logger.debug(
            "Episode %s start (testing=%s, epsilon=%.4f, q_entries=%s, states=%s)",
            episode_number,
            testing,
            episode_epsilon,
            len(self.q_values),
            len(self.state_mapping),
        )
        num_steps = 0
        episode_reward = 0.0
        # Loop until the environment signals that the episode ended
        last_observation = observation
        while observation and not observation.end:
            num_steps += 1
            # Choose action
            action, state_id, action_name = self.select_action(observation, testing=testing)
            if action is None:
                # No valid actions; terminate
                break
            q_prev_state_id = state_id if self.q_enabled else None
            q_prev_action_key = self._ql_action_key(action) if self.q_enabled else ""
            logger.debug(
                "Episode %s step %s executing action=%s state_id=%s",
                episode_number,
                num_steps,
                action_name,
                state_id,
            )
            # Execute the action and obtain new observation
            try:
                new_observation = self.make_step(action)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to decode environment response: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"Environment communication failed: {exc}") from exc
            # Update exploited services if necessary
            if not testing and action_name == "ExploitService":
                # Record exploited service by target host/service if possible
                target_host = _get_action_parameter(action, "target_host")
                target_service = _get_action_parameter(action, "target_service")
                if target_host and target_service:
                    self.exploited_services.add((str(target_host), str(target_service)))
                    logger.debug(
                        "Episode %s step %s marked exploited host=%s service=%s",
                        episode_number,
                        num_steps,
                        target_host,
                        target_service,
                    )
            # Recompute reward
            new_observation = self.recompute_reward(new_observation)
            if not testing:
                # Q‑learning update
                self.update_q_value(state_id, action_name, new_observation.reward, new_observation)
            if self.q_enabled and self.q_enabled_learn and q_prev_state_id is not None:
                next_state_id = self.get_state_id(new_observation.state)
                next_valid_actions = list(generate_valid_actions(new_observation.state))
                scaled_reward = self._ql_proc_reward(float(new_observation.reward))
                alpha = self._ql_alpha(q_prev_state_id, q_prev_action_key)
                visits_key = (q_prev_state_id, q_prev_action_key)
                visits_before = self.q_visits[visits_key]
                if new_observation.end:
                    target = scaled_reward
                else:
                    if next_valid_actions:
                        max_next = max(
                            self.q_table[next_state_id].get(self._ql_action_key(a2), 0.0)
                            for a2 in next_valid_actions
                        )
                    else:
                        max_next = 0.0
                    target = scaled_reward + self.q_gamma * max_next
                current_q = self.q_table[q_prev_state_id].get(q_prev_action_key, 0.0)
                self.q_table[q_prev_state_id][q_prev_action_key] = current_q + alpha * (target - current_q)
                self.q_visits[visits_key] = visits_before + 1
                ql_total_reward += scaled_reward
            episode_reward += float(new_observation.reward)
            logger.debug(
                "Episode %s step %s reward=%.2f cumulative=%.2f end=%s",
                episode_number,
                num_steps,
                new_observation.reward,
                episode_reward,
                new_observation.end,
            )
            # Set current observation to next
            observation = new_observation
            if observation is None:
                logger.warning(
                    "Episode %s step %s returned no observation; terminating episode early.",
                    episode_number,
                    num_steps,
                )
                break
            self._emit_environment_info(observation, episode_number, f"post-step {num_steps}")
            # Handle actions‑per‑minute limit
            if self.apm_limit:
                # Sleep to respect APM.  In practice this should use time.time()
                pass  # Omitted for brevity
        # Epsilon decay after training episodes
        if not testing:
            self.update_epsilon(episode_number)

        if self.q_enabled and self.q_enabled_learn and not testing:
            self.q_episode_idx += 1
            if self.q_episode_idx % 100 == 0:
                self._ql_log_progress(train_reward=ql_total_reward, steps=num_steps)
            self._ql_checkpoint(force=False)

        end_epsilon = 0.0 if testing else self.current_epsilon
        logger.debug(
            "Episode %s finished (testing=%s, steps=%s, total_reward=%.2f, epsilon=%.4f)",
            episode_number,
            testing,
            num_steps,
            episode_reward,
            end_epsilon,
        )
        return observation, num_steps, episode_reward

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_q_table(self, filename: str) -> None:
        """Save the Q‑table and state mapping to a pickle file."""
        with open(filename, "wb") as f:
            pickle.dump({"q_table": self.q_values, "state_mapping": self.state_mapping}, f)

    def load_q_table(self, filename: str) -> None:
        """Load the Q‑table and state mapping from a pickle file."""
        with open(filename, "rb") as f:
            data = pickle.load(f)
            self.q_values = data.get("q_table", {})
            self.state_mapping = data.get("state_mapping", {})


def _create_agent_from_args(
    args: argparse.Namespace,
    q_values: Dict[Tuple[int, str], float] | None = None,
    state_mapping: Dict[Tuple[int, ...], int] | None = None,
    current_epsilon: float | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> HighLevelQAgent:
    agent = HighLevelQAgent(
        host=args.host,
        port=args.port,
        role=args.role,
        alpha=args.alpha,
        gamma=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_max_episodes=args.epsilon_max_episodes,
        apm_limit=args.apm_limit,
    )
    if q_values is not None:
        agent.q_values = q_values
    if state_mapping is not None:
        agent.state_mapping = state_mapping
    if current_epsilon is not None:
        agent.current_epsilon = current_epsilon
    agent.progress_callback = progress_callback
    agent.q_model_path = str(args.output_model)
    agent.q_eps_start = args.epsilon_start
    agent.q_eps_end = args.epsilon_end
    agent.q_eps_max = max(1, args.epsilon_max_episodes)
    return agent


def _save_model_data(
    q_values: Dict[Tuple[int, str], float],
    state_mapping: Dict[Tuple[int, ...], int],
    model_path: Path,
    q_table: Dict[int, Dict[str, float]] | None = None,
    q_visits: Counter[Tuple[int, str]] | None = None,
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        payload = {"q_table": q_values, "state_mapping": state_mapping}
        if q_table is not None:
            payload["Q"] = q_table
        if q_visits is not None:
            payload["visits"] = q_visits
        pickle.dump(payload, f)


def _moving_average(values: List[float], window: int) -> float:
    if not values or window <= 0:
        return 0.0
    count = min(window, len(values))
    return sum(values[-count:]) / count


def _mean_std(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(statistics.mean(values)), float(statistics.stdev(values))


def _load_model_data(
    model_path: Path,
) -> Tuple[
    Dict[Tuple[int, str], float],
    Dict[Tuple[int, ...], int],
    Dict[int, Dict[str, float]],
    Counter[Tuple[int, str]],
]:
    with open(model_path, "rb") as f:
        data = pickle.load(f)
    q_values = data.get("q_table", {})
    state_mapping = data.get("state_mapping", {})
    q_table = data.get("Q", {})
    visits = data.get("visits", Counter())
    if not isinstance(visits, Counter):
        visits = Counter(visits)
    return q_values, state_mapping, q_table, visits


def _safe_close(agent: HighLevelQAgent) -> None:
    terminate_fn = getattr(agent, "terminate_connection", None)
    if callable(terminate_fn):
        try:
            terminate_fn()
        except Exception:
            logger.debug("Error terminating agent connection", exc_info=True)


def _setup_logging(level: str, log_file: str | None) -> None:
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    handlers: List[logging.Handler] = []
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode="w"))
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    logger.debug("Logging configured at level %s with handlers=%s", level.upper(), handlers)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Interact with the NetSecGame environment using a Q-learning agent.")
    parser.add_argument("--port", required=True, type=int, help="Coordinator port to connect to.")
    parser.add_argument("--host", required=True, help="Coordinator host to connect to.")
    parser.add_argument("--role", default="Attacker", help="Agent role recognised by the environment.")
    parser.add_argument("--episodes", type=int, default=1, help="Number of training episodes to run.")
    parser.add_argument("--test-episodes", type=int, default=0, help="Number of evaluation episodes to run with a greedy policy.")
    parser.add_argument("--alpha", type=float, default=0.1, help="Learning rate for Q-learning updates.")
    parser.add_argument("--gamma", type=float, default=0.9, help="Discount factor for future rewards.")
    parser.add_argument("--epsilon-start", type=float, default=0.9, help="Initial epsilon for exploration.")
    parser.add_argument("--epsilon-end", type=float, default=0.1, help="Final epsilon after decay.")
    parser.add_argument("--epsilon-max-episodes", type=int, default=5000, help="Number of episodes over which epsilon decays.")
    parser.add_argument("--apm-limit", type=int, default=None, help="Optional actions-per-minute cap.")
    parser.add_argument("--previous-model", type=str, help="Path to an existing Q-table pickle to resume training from.")
    parser.add_argument("--output-model", type=str, default="q_table.pkl", help="Path where the updated Q-table will be saved.")
    parser.add_argument("--save-every", type=int, default=0, help="Save the Q-table every N episodes (0 disables periodic saves).")
    parser.add_argument("--log-every", type=int, default=1, help="Log training progress every N episodes.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).")
    parser.add_argument("--log-file", type=str, default="agent.log", help="Path to log file (logs are written only to this file).")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress output on stdout.")
    args = parser.parse_args(argv)

    _setup_logging(args.log_level, args.log_file)

    model_path = Path(args.output_model)
    episode_rewards: List[float] = []
    episodes_completed = 0
    agent: HighLevelQAgent | None = None
    q_values: Dict[Tuple[int, str], float] = {}
    state_mapping: Dict[Tuple[int, ...], int] = {}
    current_epsilon: float | None = None
    if args.previous_model:
        prev_model_path = Path(args.previous_model)
        if not prev_model_path.exists():
            raise FileNotFoundError(f"Q-table file not found: {prev_model_path}")
        q_values, state_mapping, loaded_Q, loaded_visits = _load_model_data(prev_model_path)
        logger.info(
            "Loaded previous model from %s (q_entries=%s, states=%s)",
            prev_model_path,
            len(q_values),
            len(state_mapping),
        )
    else:
        loaded_Q = {}
        loaded_visits = Counter()
    show_progress = not args.no_progress
    progress_callback = (lambda message: print(message, flush=True)) if show_progress else None
    interrupted = False
    aborted_training = 0
    aborted_eval = 0
    train_wins = 0
    train_detected = 0
    train_timeouts = 0
    train_step_counts: List[int] = []
    train_returns: List[float] = []
    train_win_steps: List[int] = []
    train_detected_steps: List[int] = []
    train_timeout_steps: List[int] = []
    train_win_returns: List[float] = []
    train_detected_returns: List[float] = []
    train_timeout_returns: List[float] = []
    try:
        agent = _create_agent_from_args(
            args,
            q_values,
            state_mapping,
            current_epsilon,
            progress_callback=progress_callback,
        )
        agent.q_enabled_learn = (args.episodes or 0) > 0
        if loaded_Q:
            agent.q_table.update(loaded_Q)
        if loaded_visits:
            agent.q_visits.update(loaded_visits)
        current_observation = agent.register()
        if current_observation is None:
            raise RuntimeError("Failed to register agent with the coordinator.")
        if args.episodes > 0:
            logger.info("Starting training for %s episode(s)...", args.episodes)
            if show_progress:
                print(f"Starting training for {args.episodes} episode(s)...", flush=True)
        for episode in range(1, args.episodes + 1):
            try:
                final_observation, steps, total_reward = agent.play_episode_from_observation(
                    current_observation,
                    episode,
                    testing=False,
                )
            except RuntimeError as exc:
                aborted_training += 1
                logger.warning("[Episode %s] aborted: %s. Continuing with next episode...", episode, exc)
                if show_progress:
                    print(f"[Episode {episode}] aborted: {exc}", flush=True)
                interrupted = True
                # Attempt to reset connection for the next attempt
                try:
                    current_observation = agent.request_game_reset()
                except Exception:
                    current_observation = None
                if current_observation is None:
                    logger.warning("Unable to reset game after abort; breaking training loop.")
                    break
                continue
            q_values = agent.q_values
            state_mapping = agent.state_mapping
            current_epsilon = agent.current_epsilon
            episodes_completed += 1
            episode_rewards.append(total_reward)
            info = getattr(final_observation, "info", {}) or {}
            reason = info.get("end_reason")
            train_step_counts.append(steps)
            train_returns.append(total_reward)
            if _matches_agent_status(reason, AgentStatus.Success):
                train_wins += 1
                train_win_steps.append(steps)
                train_win_returns.append(total_reward)
            elif _matches_agent_status(reason, AgentStatus.Fail):
                train_detected += 1
                train_detected_steps.append(steps)
                train_detected_returns.append(total_reward)
            elif _matches_agent_status(reason, AgentStatus.TimeoutReached):
                train_timeouts += 1
                train_timeout_steps.append(steps)
                train_timeout_returns.append(total_reward)
            avg_reward = _moving_average(episode_rewards, 10)
            if args.log_every and (episode % args.log_every == 0 or episode == 1):
                end_reason = ""
                if final_observation and getattr(final_observation, "info", None):
                    end_reason = str(final_observation.info.get("end_reason", ""))
                logger.info(
                    "[Episode %s] steps=%s reward=%.2f avg_reward_10=%.2f end_reason=%s",
                    episode,
                    steps,
                    total_reward,
                    avg_reward,
                    end_reason,
                )
                if show_progress:
                    print(
                        f"[Episode {episode}] steps={steps} reward={total_reward:.2f} "
                        f"avg_reward_10={avg_reward:.2f} end_reason={end_reason}",
                        flush=True,
                    )
            if args.save_every and episode % args.save_every == 0:
                _save_model_data(
                    q_values,
                    state_mapping,
                    model_path,
                    q_table=agent.q_table,
                    q_visits=agent.q_visits,
                )
                logger.info(
                    "Saved checkpoint to %s at episode %s",
                    model_path,
                    episode,
                )
            try:
                current_observation = agent.request_game_reset()
            except Exception as exc:
                logger.warning("Failed to reset game after episode %s: %s", episode, exc)
                if show_progress:
                    print(f"Failed to reset after episode {episode}: {exc}", flush=True)
                current_observation = None
            if current_observation is None:
                logger.warning("Reset did not return a new observation; stopping training loop.")
                break
        if train_step_counts:
            total_train = len(train_step_counts)
            train_win_rate = (train_wins / total_train) * 100
            train_detection_rate = (train_detected / total_train) * 100
            train_timeout_rate = (train_timeouts / total_train) * 100
            train_avg_steps, train_std_steps = _mean_std(train_step_counts)
            train_avg_return, train_std_return = _mean_std(train_returns)
            train_avg_win_steps, train_std_win_steps = _mean_std(train_win_steps)
            train_avg_detected_steps, train_std_detected_steps = _mean_std(train_detected_steps)
            train_avg_timeout_steps, train_std_timeout_steps = _mean_std(train_timeout_steps)
            train_avg_win_returns, train_std_win_returns = _mean_std(train_win_returns)
            train_avg_detected_returns, train_std_detected_returns = _mean_std(train_detected_returns)
            train_avg_timeout_returns, train_std_timeout_returns = _mean_std(train_timeout_returns)
            progress_lines: List[str] = []
            segment_count = min(6, total_train)
            if segment_count > 0:
                segment_size = max(1, total_train // segment_count)
                for idx in range(segment_count):
                    start = idx * segment_size
                    end = total_train if idx == segment_count - 1 else min((idx + 1) * segment_size, total_train)
                    if start >= total_train:
                        break
                    segment_rewards = train_returns[start:end]
                    seg_avg = sum(segment_rewards) / len(segment_rewards)
                    progress_lines.append(
                        f"    Episodes {start + 1}-{end}: avg return={seg_avg:.2f}"
                    )
            train_summary = (
                f"Training summary ({total_train} episodes):\n"
                f"  Wins={train_wins} ({train_win_rate:.2f}%)\n"
                f"  Detections={train_detected} ({train_detection_rate:.2f}%)\n"
                f"  Timeouts={train_timeouts} ({train_timeout_rate:.2f}%)\n"
                f"  Avg steps={train_avg_steps:.2f} ± {train_std_steps:.2f}, avg return={train_avg_return:.2f} ± {train_std_return:.2f}\n"
                f"  Avg win steps={train_avg_win_steps:.2f} ± {train_std_win_steps:.2f}, avg win return={train_avg_win_returns:.2f} ± {train_std_win_returns:.2f}\n"
                f"  Avg detected steps={train_avg_detected_steps:.2f} ± {train_std_detected_steps:.2f}, "
                f"avg detected return={train_avg_detected_returns:.2f} ± {train_std_detected_returns:.2f}\n"
                f"  Avg timeout steps={train_avg_timeout_steps:.2f} ± {train_std_timeout_steps:.2f}, "
                f"avg timeout return={train_avg_timeout_returns:.2f} ± {train_std_timeout_returns:.2f}\n"
                f"  epsilon={agent.current_epsilon:.4f}"
            )
            if progress_lines:
                train_summary += "\n  Reward trajectory:\n" + "\n".join(progress_lines)
            logger.info(train_summary)
            if show_progress:
                print(train_summary, flush=True)
        eval_prev_epsilon: float | None = None
        if args.test_episodes > 0:
            eval_prev_epsilon = agent.current_epsilon
            agent.current_epsilon = 0.0
            logger.info("Running %s evaluation episode(s)...", args.test_episodes)
            if show_progress:
                print(f"Running {args.test_episodes} evaluation episode(s)...", flush=True)
        test_wins = 0
        test_detected = 0
        test_timeouts = 0
        test_step_counts: List[int] = []
        test_returns: List[float] = []
        test_win_steps: List[int] = []
        test_detected_steps: List[int] = []
        test_timeout_steps: List[int] = []
        test_win_returns: List[float] = []
        test_detected_returns: List[float] = []
        test_timeout_returns: List[float] = []
        for offset in range(1, args.test_episodes + 1):
            test_index = episodes_completed + offset
            if current_observation is None:
                current_observation = agent.register()
                if current_observation is None:
                    logger.warning("Unable to register before evaluation; aborting evaluation loop.")
                    break
            try:
                final_observation, steps, total_reward = agent.play_episode_from_observation(
                    current_observation,
                    test_index,
                    testing=True,
                )
            except RuntimeError as exc:
                aborted_eval += 1
                logger.warning("[Eval %s] aborted: %s. Stopping remaining evaluation episodes.", offset, exc)
                if show_progress:
                    print(f"[Eval {offset}] aborted: {exc}", flush=True)
                break
            episode_rewards.append(total_reward)
            end_reason = ""
            if final_observation and getattr(final_observation, "info", None):
                end_reason = str(final_observation.info.get("end_reason", ""))
            logger.info(
                "[Eval %s/%s] steps=%s reward=%.2f end_reason=%s",
                offset,
                args.test_episodes,
                steps,
                total_reward,
                end_reason,
            )
            test_step_counts.append(steps)
            test_returns.append(total_reward)
            info = getattr(final_observation, "info", {}) or {}
            reason = info.get("end_reason")
            if _matches_agent_status(reason, AgentStatus.Success):
                test_wins += 1
                test_win_steps.append(steps)
                test_win_returns.append(total_reward)
            elif _matches_agent_status(reason, AgentStatus.Fail):
                test_detected += 1
                test_detected_steps.append(steps)
                test_detected_returns.append(total_reward)
            elif _matches_agent_status(reason, AgentStatus.TimeoutReached):
                test_timeouts += 1
                test_timeout_steps.append(steps)
                test_timeout_returns.append(total_reward)
            if show_progress:
                print(
                    f"[Eval {offset}/{args.test_episodes}] steps={steps} reward={total_reward:.2f} "
                    f"end_reason={end_reason}",
                    flush=True,
                )
            current_observation = agent.request_game_reset()
        if args.test_episodes > 0 and test_step_counts:
            total = len(test_step_counts)
            win_rate = (test_wins / total) * 100
            detection_rate = (test_detected / total) * 100
            timeout_rate = (test_timeouts / total) * 100
            avg_steps, std_steps = _mean_std(test_step_counts)
            avg_return, std_return = _mean_std(test_returns)
            avg_win_steps, std_win_steps = _mean_std(test_win_steps)
            avg_detected_steps, std_detected_steps = _mean_std(test_detected_steps)
            avg_timeout_steps, std_timeout_steps = _mean_std(test_timeout_steps)
            avg_win_returns, std_win_returns = _mean_std(test_win_returns)
            avg_detected_returns, std_detected_returns = _mean_std(test_detected_returns)
            avg_timeout_returns, std_timeout_returns = _mean_std(test_timeout_returns)
            summary = (
                f"Evaluation summary ({total} episodes):\n"
                f"  Wins={test_wins} ({win_rate:.2f}%)\n"
                f"  Detections={test_detected} ({detection_rate:.2f}%)\n"
                f"  Timeouts={test_timeouts} ({timeout_rate:.2f}%)\n"
                f"  Avg steps={avg_steps:.2f} ± {std_steps:.2f}, avg return={avg_return:.2f} ± {std_return:.2f}\n"
                f"  Avg win steps={avg_win_steps:.2f} ± {std_win_steps:.2f}, avg win return={avg_win_returns:.2f} ± {std_win_returns:.2f}\n"
                f"  Avg detected steps={avg_detected_steps:.2f} ± {std_detected_steps:.2f}, "
                f"avg detected return={avg_detected_returns:.2f} ± {std_detected_returns:.2f}\n"
                f"  Avg timeout steps={avg_timeout_steps:.2f} ± {std_timeout_steps:.2f}, "
                f"avg timeout return={avg_timeout_returns:.2f} ± {std_timeout_returns:.2f}\n"
                f"  epsilon={agent.current_epsilon:.4f}"
            )
            logger.info(summary)
            if show_progress:
                print(summary, flush=True)
        if eval_prev_epsilon is not None:
            agent.current_epsilon = eval_prev_epsilon
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Saving current Q-table...")
        if show_progress:
            print("Interrupted by user. Saving current Q-table...", flush=True)
        interrupted = True
    finally:
        if agent is not None:
            _safe_close(agent)
        if q_values or state_mapping:
            _save_model_data(
                q_values,
                state_mapping,
                model_path,
                q_table=agent.q_table if agent else None,
                q_visits=agent.q_visits if agent else None,
            )
        elif not interrupted:
            # Ensure an output file exists even if no episodes ran.
            _save_model_data({}, {}, model_path, q_table=agent.q_table if agent else None, q_visits=agent.q_visits if agent else None)
        legacy_entries = len(q_values)
        legacy_states = len(state_mapping)
        concrete_states = len(agent.q_table) if agent else 0
        concrete_pairs = (
            sum(len(d) for d in agent.q_table.values()) if agent else 0
        )
        logger.info(
            "Model saved to %s | legacy_entries=%d | legacy_states=%d | concrete_states=%d | concrete_pairs=%d",
            model_path,
            legacy_entries,
            legacy_states,
            concrete_states,
            concrete_pairs,
        )
        if show_progress:
            print(
                flush=True,
            )
        if aborted_training:
            logger.warning("Training episodes aborted due to communication errors: %s", aborted_training)
            if show_progress:
                print(f"Training episodes aborted due to communication errors: {aborted_training}", flush=True)
        if aborted_eval:
            logger.warning("Evaluation episodes aborted due to communication errors: %s", aborted_eval)
            if show_progress:
                print(f"Evaluation episodes aborted due to communication errors: {aborted_eval}", flush=True)


if __name__ == "__main__":
    main()
