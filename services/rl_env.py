"""
Reinforcement Learning Environment for Personalized Exercise Selection.
Part of KT-RL Phase 3: Learner Simulator & Reinforcement Learning Environment.

Provides a Gymnasium-compatible interface:
  reset(seed=..., options=...) -> (obs, info)
  step(action) -> (obs, reward, terminated, truncated, info)

Key Design Features:
- Action space: Discrete(52), indexing the canonical question bank stably sorted by item_id.
- Observation space: Box(low=0.0, high=1.0, shape=(99,), dtype=float32) from StateEncoder.
- Prerequisite action masking: Only items whose required prerequisite topics meet readiness criteria are eligible.
- Encapsulated Simulator: True learner mastery is kept strictly in the simulator and never leaked to the agent.
- BKT Belief Tracking: Observable state is maintained using Phase 2 Bayesian Knowledge Tracing.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from resources import TOPIC_CATALOG, get_all_questions
    from services.bkt_service import (
        BKTParameters,
        DEFAULT_PARAMS as BKT_DEFAULT_PARAMS,
        initialize_kc_state,
        update_kc_mastery,
        KCState,
    )
    from services.learner_simulator import SyntheticLearner, ARCHETYPES
    from services.rl_reward import RewardWeights, DEFAULT_REWARD_WEIGHTS, compute_reward
    from services.rl_state_encoder import StateEncoder
except ImportError:
    from autolearn_fullstack.resources import TOPIC_CATALOG, get_all_questions
    from autolearn_fullstack.services.bkt_service import (
        BKTParameters,
        DEFAULT_PARAMS as BKT_DEFAULT_PARAMS,
        initialize_kc_state,
        update_kc_mastery,
        KCState,
    )
    from autolearn_fullstack.services.learner_simulator import SyntheticLearner, ARCHETYPES
    from autolearn_fullstack.services.rl_reward import RewardWeights, DEFAULT_REWARD_WEIGHTS, compute_reward
    from autolearn_fullstack.services.rl_state_encoder import StateEncoder


class DiscreteSpace:
    """Lightweight discrete space interface matching Gymnasium spaces.Discrete."""
    def __init__(self, n: int, seed: Optional[int] = None):
        self.n = n
        self.rng = random.Random(seed)

    def sample(self, mask: Optional[np.ndarray] = None) -> int:
        if mask is not None:
            valid_indices = [i for i in range(self.n) if mask[i]]
            if valid_indices:
                return self.rng.choice(valid_indices)
        return self.rng.randint(0, self.n - 1)

    def contains(self, x: Any) -> bool:
        return isinstance(x, (int, np.integer)) and 0 <= x < self.n


class BoxSpace:
    """Lightweight continuous box space matching Gymnasium spaces.Box."""
    def __init__(self, low: float, high: float, shape: Tuple[int, ...], dtype: Any = np.float32):
        self.low = low
        self.high = high
        self.shape = shape
        self.dtype = dtype

    def sample(self) -> np.ndarray:
        return np.random.uniform(self.low, self.high, size=self.shape).astype(self.dtype)

    def contains(self, x: Any) -> bool:
        return isinstance(x, np.ndarray) and x.shape == self.shape


class ExerciseSelectionEnv:
    """
    Gymnasium-compatible environment for exercise selection.
    """

    def __init__(
        self,
        max_steps: int = 25,
        target_mastery: float = 0.85,
        prereq_threshold: float = 0.50,
        bkt_params: BKTParameters = BKT_DEFAULT_PARAMS,
        reward_weights: RewardWeights = DEFAULT_REWARD_WEIGHTS,
        default_archetype: str = "typical_learner",
        step_time_delta: float = 0.05,
    ):
        self.max_steps = max_steps
        self.target_mastery = target_mastery
        self.prereq_threshold = prereq_threshold
        self.bkt_params = bkt_params
        self.reward_weights = reward_weights
        self.default_archetype = default_archetype
        self.step_time_delta = step_time_delta

        # 1. Canonical Item Bank stably sorted by item_id
        all_q = get_all_questions()
        self.item_bank = sorted(all_q, key=lambda q: q["item_id"])
        self.num_actions = len(self.item_bank)

        # 2. Canonical Topics
        self.topics = sorted(list(TOPIC_CATALOG.keys()))
        self.num_topics = len(self.topics)

        # 3. Action and Observation Spaces
        self.action_space = DiscreteSpace(self.num_actions)
        self.encoder = StateEncoder(topics=self.topics, max_steps=self.max_steps)
        self.observation_space = BoxSpace(
            low=0.0,
            high=1.0,
            shape=(self.encoder.feature_dim,),
            dtype=np.float32,
        )

        # State Variables
        self.learner: Optional[SyntheticLearner] = None
        self.bkt_states: Dict[str, KCState] = {}
        self.current_step: int = 0
        self.recent_history: List[int] = []
        self.consecutive_failures_by_topic: Dict[str, int] = {}
        self.last_difficulty: int = 2
        self.rng = random.Random()
        self.episode_log: List[Dict[str, Any]] = []

    def get_action_mask(self) -> np.ndarray:
        """
        Computes a binary mask array of length num_actions where:
          mask[i] = 1 if all prerequisite topics of item i have estimated BKT mastery >= prereq_threshold
          mask[i] = 0 otherwise.

        Note: Prerequisite readiness is evaluated using observable BKT mastery, NOT hidden ground truth!
        """
        mask = np.ones(self.num_actions, dtype=np.int8)

        # Evaluate readiness per topic based on observable BKT belief
        for idx, item in enumerate(self.item_bank):
            kcs = item.get("knowledge_components", [])
            for kc in kcs:
                prereqs = TOPIC_CATALOG.get(kc, {}).get("prerequisites", [])
                for prereq in prereqs:
                    prereq_clean = str(prereq).strip().lower()
                    if prereq_clean in self.bkt_states:
                        p_m = self.bkt_states[prereq_clean].mastery_probability
                        obs_cnt = self.bkt_states[prereq_clean].observation_count
                        # A prerequisite is satisfied if mastery >= threshold OR it has not been assessed yet
                        # but student has attempted at least 1 prerequisite exercise with passing mastery.
                        # Strict rule: If prereq is assessed and mastery < threshold, lock it.
                        if obs_cnt > 0 and p_m < self.prereq_threshold:
                            mask[idx] = 0
                            break
                if mask[idx] == 0:
                    break

        # Fallback safeguard: If all actions are masked out, unmask level-1 foundational items
        if np.sum(mask) == 0:
            for idx, item in enumerate(self.item_bank):
                if item.get("difficulty", 2) == 1:
                    mask[idx] = 1

        return mask

    def _get_prereq_readiness_map(self) -> Dict[str, bool]:
        readiness = {}
        for topic in self.topics:
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            if not prereqs:
                readiness[topic] = True
            else:
                is_ready = True
                for p in prereqs:
                    p_clean = str(p).strip().lower()
                    state = self.bkt_states.get(p_clean)
                    if state and state.observation_count > 0 and state.mastery_probability < self.prereq_threshold:
                        is_ready = False
                        break
                readiness[topic] = is_ready
        return readiness

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Resets environment to starting state.
        Returns:
          (observation, info_dict)
        """
        if seed is not None:
            self.rng = random.Random(seed)
            self.action_space.rng = random.Random(seed)

        options = options or {}
        archetype = options.get("archetype", self.default_archetype)

        # 1. Initialize fresh synthetic learner (independent episode)
        learner_seed = self.rng.randint(0, 1_000_000_000)
        self.learner = SyntheticLearner(
            archetype_name=archetype,
            topics=self.topics,
            seed=learner_seed,
        )

        # 2. Reset BKT observable states to prior
        self.bkt_states = {
            topic: initialize_kc_state(topic, self.bkt_params)
            for topic in self.topics
        }

        # 3. Reset episode counters
        self.current_step = 0
        self.recent_history = []
        self.consecutive_failures_by_topic = {t: 0 for t in self.topics}
        self.last_difficulty = 2
        self.episode_log = []

        # 4. Generate initial observation
        obs = self._get_obs()
        mask = self.get_action_mask()

        info = {
            "archetype": archetype,
            "seed": seed,
            "learner_seed": learner_seed,
            "action_mask": mask,
            "step": self.current_step,
            "valid_action_count": int(np.sum(mask)),
        }
        return obs, info

    def _get_obs(self) -> np.ndarray:
        bkt_map = {k: v.to_dict() for k, v in self.bkt_states.items()}
        prereq_map = self._get_prereq_readiness_map()
        recent_failures = max(self.consecutive_failures_by_topic.values()) if self.consecutive_failures_by_topic else 0

        return self.encoder.encode(
            bkt_topics_map=bkt_map,
            prereq_readiness_map=prereq_map,
            recent_history=self.recent_history,
            recent_topic_failures=recent_failures,
            last_difficulty=self.last_difficulty,
            current_step=self.current_step,
        )

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Executes one step in the environment.
        Returns 5-tuple: (observation, reward, terminated, truncated, info)
        """
        if self.learner is None:
            raise RuntimeError("Environment must be reset before calling step().")

        self.current_step += 1
        mask = self.get_action_mask()

        # Validate action
        is_in_bounds = self.action_space.contains(action)
        is_valid = bool(is_in_bounds and mask[action] == 1)

        if not is_in_bounds:
            # Action out of range
            reward, r_components = compute_reward(
                mastery_deltas={},
                prior_bkt_mastery=0.20,
                item_difficulty=2,
                is_correct=False,
                consecutive_topic_failures=0,
                is_action_valid=False,
                weights=self.reward_weights,
            )
            obs = self._get_obs()
            terminated = False
            truncated = bool(self.current_step >= self.max_steps)
            info = {
                "error": "Action index out of bounds",
                "action": action,
                "is_action_valid": False,
                "reward_components": r_components,
            }
            return obs, reward, terminated, truncated, info

        item = self.item_bank[action]
        item_id = item["item_id"]
        kcs = item.get("knowledge_components", [])
        primary_topic = kcs[0] if kcs else item.get("topic", "general")
        difficulty = item.get("difficulty", 2)
        self.last_difficulty = difficulty

        if not is_valid:
            # Action was masked out (prerequisite violation)
            reward, r_components = compute_reward(
                mastery_deltas={},
                prior_bkt_mastery=self.bkt_states.get(primary_topic, initialize_kc_state(primary_topic)).mastery_probability,
                item_difficulty=difficulty,
                is_correct=False,
                consecutive_topic_failures=self.consecutive_failures_by_topic.get(primary_topic, 0),
                is_action_valid=False,
                weights=self.reward_weights,
            )
            obs = self._get_obs()
            terminated = False
            truncated = bool(self.current_step >= self.max_steps)
            info = {
                "error": "Prerequisite condition not satisfied for selected action",
                "item_id": item_id,
                "topic": primary_topic,
                "is_action_valid": False,
                "reward_components": r_components,
                "action_mask": self.get_action_mask(),
            }
            return obs, reward, terminated, truncated, info

        # Prior BKT belief on primary topic
        prior_state = self.bkt_states.get(primary_topic, initialize_kc_state(primary_topic, self.bkt_params))
        prior_bkt_mastery = prior_state.mastery_probability

        # 1. Simulate Learner Response
        is_correct, p_correct, sim_diag = self.learner.simulate_response(
            knowledge_components=kcs,
            difficulty=difficulty,
        )

        # 2. Update Ground Truth Mastery & Apply Calibrated Forgetting
        mastery_deltas = self.learner.apply_learning(
            knowledge_components=kcs,
            is_correct=is_correct,
        )
        # Fractional session time advancement (default 0.05 units per exercise)
        forgetting_deltas = self.learner.apply_forgetting(delta_time=self.step_time_delta)

        # 3. Update Observable BKT State
        for kc in kcs:
            kc_clean = str(kc).strip().lower()
            if kc_clean in self.bkt_states:
                self.bkt_states[kc_clean] = update_kc_mastery(
                    self.bkt_states[kc_clean],
                    is_correct=is_correct,
                    params=self.bkt_params,
                )

        post_bkt_mastery = self.bkt_states[primary_topic].mastery_probability if primary_topic in self.bkt_states else prior_bkt_mastery

        # 4. Update Consecutive Failures Counter
        if is_correct:
            self.consecutive_failures_by_topic[primary_topic] = 0
        else:
            self.consecutive_failures_by_topic[primary_topic] = self.consecutive_failures_by_topic.get(primary_topic, 0) + 1

        self.recent_history.append(1 if is_correct else 0)

        # 5. Compute Aligned Reward (Entropy Reduction & Mastery Improvement)
        reward, r_components = compute_reward(
            mastery_deltas=mastery_deltas,
            prior_bkt_mastery=prior_bkt_mastery,
            item_difficulty=difficulty,
            is_correct=is_correct,
            consecutive_topic_failures=self.consecutive_failures_by_topic[primary_topic],
            is_action_valid=True,
            weights=self.reward_weights,
            post_bkt_mastery=post_bkt_mastery,
        )

        # 6. Check Termination & Truncation
        # Terminate if all syllabus topics reach target BKT mastery
        all_mastered = all(
            s.mastery_probability >= self.target_mastery
            for s in self.bkt_states.values()
        )
        terminated = bool(all_mastered)
        truncated = bool(self.current_step >= self.max_steps)

        obs = self._get_obs()
        next_mask = self.get_action_mask()

        # Step diagnostic payload
        info = {
            "step": self.current_step,
            "action": action,
            "item_id": item_id,
            "topic": primary_topic,
            "difficulty": difficulty,
            "is_correct": is_correct,
            "p_correct_simulated": sim_diag["p_correct"],
            "reward": reward,
            "reward_components": r_components,
            "action_mask": next_mask,
            "bkt_posterior": self.bkt_states[primary_topic].mastery_probability,
            "all_mastered": all_mastered,
            # Diagnostic-only hidden ground truth (FOR BENCHMARK METRICS ONLY, NOT OBSERVATION)
            "_diag_hidden_mastery": self.learner.get_hidden_mastery(primary_topic),
            "_diag_mastery_deltas": mastery_deltas,
        }

        self.episode_log.append(info)
        return obs, reward, terminated, truncated, info

    def close(self) -> None:
        pass
