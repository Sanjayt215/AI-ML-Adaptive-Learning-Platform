"""
Reward Function for Adaptive Exercise Selection.
Part of KT-RL Phase 3: Learner Simulator & Reinforcement Learning Environment.

Computes multi-objective reinforcement learning rewards balancing:
1. Learning Gain: Ground-truth mastery improvement (measured in simulation).
2. Diagnostic Information Value: Selecting items with uncertain mastery P(K) ≈ 0.5.
3. Challenge Calibration: Penalizing excessively easy questions (m >> d) or harsh difficulty spikes.
4. Repeated Failure Penalty: Penalizing trapping struggling learners on frustration loops.
5. Exercise Cost: Small step penalty encouraging efficient mastery trajectories.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class RewardWeights:
    """Configurable weights for the multi-objective reward formulation."""
    w_mastery_gain: float = 10.0   # Weight for simulated ground-truth mastery increase
    w_info_gain: float = 0.5       # Weight for diagnostic entropy/uncertainty reduction
    w_challenge_match: float = 0.4  # Bonus for selecting items near the Zone of Proximal Development
    w_failure_penalty: float = 0.8  # Penalty for triggering repeated consecutive failures
    w_invalid_penalty: float = 2.0  # Penalty for attempting an ineligible action (masked out)
    w_step_cost: float = 0.05       # Base step penalty encouraging pedagogical efficiency


DEFAULT_REWARD_WEIGHTS = RewardWeights()


def compute_reward(
    mastery_deltas: Dict[str, float],
    prior_bkt_mastery: float,
    item_difficulty: int,
    is_correct: bool,
    consecutive_topic_failures: int,
    is_action_valid: bool = True,
    weights: RewardWeights = DEFAULT_REWARD_WEIGHTS,
    post_bkt_mastery: Optional[float] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    Computes scalar reward R_t and diagnostic breakdown components.

    Formulation:
      1. R_mastery = w_m * sum(max(0, delta_m)) (True knowledge acquisition)
      2. R_info    = w_i * max(0, H(prior) - H(post)) (True information gain / entropy reduction)
                     Falls back to w_i * H(prior) if post_bkt_mastery is omitted for compatibility.
      3. R_match   = w_c * exp(-((prior_m - norm_d)^2) / 0.15) (ZPD alignment bonus)
      4. R_penalty = -w_f * (consecutive_failures - 1) if (consecutive_failures >= 2 and not is_correct) else 0.0
      5. R_invalid = -w_inv if not is_action_valid else 0.0
      6. R_step    = -w_step (Pedagogical pacing cost)

    Total Reward:
      R_t = R_mastery + R_info + R_match + R_penalty + R_invalid + R_step
    """
    if not is_action_valid:
        penalty = -weights.w_invalid_penalty
        return penalty, {"invalid_penalty": penalty, "total_reward": penalty}

    # 1. Ground truth mastery gain component (meaningful learning improvement)
    total_delta = sum(max(0.0, d) for d in mastery_deltas.values()) if mastery_deltas else 0.0
    r_mastery = weights.w_mastery_gain * total_delta

    # 2. Information gain component (Entropy reduction delta_H vs static prior entropy)
    p1 = max(0.001, min(0.999, prior_bkt_mastery))
    h1 = - (p1 * math.log2(p1) + (1.0 - p1) * math.log2(1.0 - p1))

    if post_bkt_mastery is not None:
        p2 = max(0.001, min(0.999, post_bkt_mastery))
        h2 = - (p2 * math.log2(p2) + (1.0 - p2) * math.log2(1.0 - p2))
        delta_h = max(0.0, h1 - h2)
        r_info = weights.w_info_gain * delta_h
    else:
        # Fallback to prior entropy for backward compatibility
        r_info = weights.w_info_gain * h1

    # 3. Zone of Proximal Development (ZPD) alignment
    # Ideal difficulty is calibrated near student's current mastery
    norm_diff = max(0.2, min(1.0, float(item_difficulty) / 5.0))
    zpd_gap = prior_bkt_mastery - norm_diff
    # Gaussian bell curve centered at zero gap
    r_match = weights.w_challenge_match * math.exp(-(zpd_gap ** 2) / 0.15)

    # 4. Frustration / Repeated failure penalty
    r_penalty = 0.0
    if consecutive_topic_failures >= 2 and not is_correct:
        r_penalty = -weights.w_failure_penalty * (consecutive_topic_failures - 1)

    # 5. Base step cost
    r_step = -weights.w_step_cost

    total_reward = r_mastery + r_info + r_match + r_penalty + r_step

    components = {
        "mastery_gain_reward": round(r_mastery, 4),
        "information_entropy_reward": round(r_info, 4),
        "zpd_match_reward": round(r_match, 4),
        "failure_penalty": round(r_penalty, 4),
        "step_cost": round(r_step, 4),
        "total_reward": round(total_reward, 4),
    }

    return total_reward, components
