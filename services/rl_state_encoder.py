"""
RL State Encoder for Exercise Selection.
Part of KT-RL Phase 3: Learner Simulator & Reinforcement Learning Environment.

Encodes observable student state and Bayesian Knowledge Tracing estimates into
a fixed-size numerical observation vector suitable for RL agents (DQN/PPO).
Strictly excludes simulator hidden ground truth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


class StateEncoder:
    """
    Transforms observable BKT estimates, response history, and session context into
    a normalized float32 vector.

    Observation vector layout (Total length = 30 + 30 + 30 + 5 + 4 = 99 features):
    - [0:30]   Per-KC BKT estimated mastery probabilities in [0.0, 1.0]
    - [30:60]  Per-KC normalized evidence / attempt counts min(n / 10, 1.0)
    - [60:90]  Per-KC prerequisite readiness flags (1.0 = ready, 0.0 = not ready)
    - [90:95]  Recent window correctness history (5 most recent binary outcomes, 0.5 for empty)
    - [95]     Recent repeated failure flag (1.0 if >=2 recent errors on same topic, else 0.0)
    - [96]     Normalized last selected exercise difficulty (difficulty / 5.0)
    - [97]     Episode progress ratio (current_step / max_steps)
    - [98]     Average overall BKT mastery estimate across syllabus
    """

    def __init__(self, topics: List[str], max_steps: int = 25):
        self.topics = sorted(list(topics))
        self.num_topics = len(self.topics)
        self.max_steps = max_steps
        self.topic_to_idx = {t: i for i, t in enumerate(self.topics)}

        # Total feature dimension calculation
        # 3 * num_topics + 5 (recent history) + 4 (context features)
        self.feature_dim = 3 * self.num_topics + 9

    def encode(
        self,
        bkt_topics_map: Dict[str, Dict[str, Any]],
        prereq_readiness_map: Dict[str, bool],
        recent_history: List[int],
        recent_topic_failures: int,
        last_difficulty: int,
        current_step: int,
    ) -> np.ndarray:
        """
        Encodes the observable environment state into a float32 array.
        """
        obs = np.zeros(self.feature_dim, dtype=np.float32)

        # 1. BKT Mastery probabilities [0:30]
        # 2. Normalized evidence counts [30:60]
        for topic, idx in self.topic_to_idx.items():
            kc_info = bkt_topics_map.get(topic, {})
            mastery = kc_info.get("mastery_probability", 0.20)
            obs[idx] = float(mastery)

            obs_count = kc_info.get("observation_count", 0)
            obs[self.num_topics + idx] = min(1.0, float(obs_count) / 10.0)

            # 3. Prerequisite readiness [60:90]
            is_ready = prereq_readiness_map.get(topic, False)
            obs[2 * self.num_topics + idx] = 1.0 if is_ready else 0.0

        offset = 3 * self.num_topics

        # 4. Recent correctness window (last 5 responses)
        window = recent_history[-5:] if len(recent_history) >= 5 else recent_history
        for i in range(5):
            if i < len(window):
                obs[offset + i] = float(window[i])
            else:
                obs[offset + i] = 0.5  # Neutral default for unfilled slots

        offset += 5

        # 5. Contextual features
        # Repeated failure flag
        obs[offset] = 1.0 if recent_topic_failures >= 2 else 0.0
        # Last difficulty normalized
        obs[offset + 1] = max(0.2, min(1.0, float(last_difficulty) / 5.0))
        # Episode progress ratio
        obs[offset + 2] = min(1.0, float(current_step) / float(max(1, self.max_steps)))
        # Average overall BKT mastery
        mastery_vals = [obs[i] for i in range(self.num_topics)]
        obs[offset + 3] = float(np.mean(mastery_vals))

        return obs
