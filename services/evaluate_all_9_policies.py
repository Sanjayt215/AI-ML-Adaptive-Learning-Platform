"""
Comprehensive 9-Policy Evaluation & Statistical Reproducibility Harness.
Part of KT-RL Phase 6: Final System Acceptance & Research Validation.

Compares:
1. random_eligible
2. weakest_bkt_kc
3. prereq_aware_weakest
4. difficulty_ladder
5. dueling_dqn
6. forgetting_aware
7. confidence_aware
8. frustration_remedial
9. composite_adaptive

Evaluates under matched conditions across all 4 learner archetypes and fixed seeds.
Outputs structured JSON to reports/phase6_reproducibility_results.json.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.rl_env import ExerciseSelectionEnv
from services.learner_simulator import ARCHETYPES
from services.dqn_agent import DuelingDQNAgent
from services.rl_diagnostics import BASELINE_POLICIES
from services.evaluate_dqn import evaluate_policy_on_episodes


# ---------------------------------------------------------------------------
# Policy Implementations for the 4 Adaptive Strategies
# ---------------------------------------------------------------------------

def policy_forgetting_aware(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    """Prioritizes eligible items with lowest predicted retention (highest forgetting decay)."""
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Calculate retention for each eligible item
    # R(t) = floor + (p_bkt - floor) * exp(-lambda * delta_t)
    best_idx = valid_indices[0]
    min_retention = 999.0

    for idx in valid_indices:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p_val = m.mastery_probability if m else 0.20
        elapsed_steps = env.current_step - getattr(m, "last_updated_step", 0) if m else env.current_step
        decay = math.exp(-0.05 * elapsed_steps)
        retention = 0.10 + (p_val - 0.10) * decay
        if retention < min_retention:
            min_retention = retention
            best_idx = idx

    return best_idx


def policy_confidence_aware(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    """Prioritizes eligible items with highest posterior Shannon entropy (maximum uncertainty)."""
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    best_idx = valid_indices[0]
    max_entropy = -1.0

    for idx in valid_indices:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p = m.mastery_probability if m else 0.20
        p = max(1e-5, min(1.0 - 1e-5, p))
        entropy = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
        if entropy > max_entropy:
            max_entropy = entropy
            best_idx = idx

    return best_idx


def policy_frustration_remedial(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    """Checks recent failures. If learner is struggling, selects lower-difficulty eligible items."""
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Determine if learner has consecutive failures
    recent_wrong = max(env.consecutive_failures_by_topic.values()) >= 2 if env.consecutive_failures_by_topic else False

    target_diff = 1 if recent_wrong else 2

    # Filter to matching difficulty if available
    matching = [i for i in valid_indices if env.item_bank[i].get("difficulty", 2) <= target_diff]
    candidates = matching if matching else valid_indices

    # Among candidates, select weakest BKT KC
    best_idx = candidates[0]
    min_mastery = 999.0
    for idx in candidates:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p_val = m.mastery_probability if m else 0.20
        if p_val < min_mastery:
            min_mastery = p_val
            best_idx = idx

    return best_idx


def policy_composite_adaptive(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    """
    Multi-objective pedagogical ranking:
    Balances mastery deficit (1 - R(t)), entropy exploration, and ZPD proximity (around 0.55).
    """
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    best_idx = valid_indices[0]
    max_utility = -999.0

    for idx in valid_indices:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p = m.mastery_probability if m else 0.20

        # Retention decay
        elapsed_steps = env.current_step - getattr(m, "last_updated_step", 0) if m else env.current_step
        decay = math.exp(-0.05 * elapsed_steps)
        retention = 0.10 + (p - 0.10) * decay

        # Entropy
        p_safe = max(1e-5, min(1.0 - 1e-5, p))
        entropy = -p_safe * math.log2(p_safe) - (1.0 - p_safe) * math.log2(1.0 - p_safe)

        # ZPD proximity: Gaussian centered at 0.55
        zpd_score = math.exp(-((p - 0.55) ** 2) / (2.0 * (0.20 ** 2)))

        # Composite score
        utility = 2.0 * (1.0 - retention) + 0.5 * entropy + 0.5 * zpd_score
        if utility > max_utility:
            max_utility = utility
            best_idx = idx

    return best_idx


# ---------------------------------------------------------------------------
# Comprehensive Evaluation Runner
# ---------------------------------------------------------------------------

def run_9_policy_benchmark(
    checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
    output_path: str = "reports/phase6_reproducibility_results.json",
    seeds: Optional[List[int]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    if seeds is None:
        # 5 fixed evaluation seeds: 101, 202, 303, 404, 505
        seeds = [101, 202, 303, 404, 505]

    archetypes = list(ARCHETYPES.keys())
    env = ExerciseSelectionEnv(max_steps=25)

    # Setup DQN Agent
    agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
    )
    candidate_paths = [
        checkpoint_path,
        os.path.join(ROOT_DIR, checkpoint_path),
        os.path.join(ROOT_DIR, "autolearn_fullstack", checkpoint_path),
    ]
    loaded = False
    for p in candidate_paths:
        if os.path.exists(p):
            agent.load_checkpoint(p)
            loaded = True
            break
    if not loaded:
        print(f"[WARN] Checkpoint not found at {candidate_paths}. DQN will use initialized weights.")

    def dqn_policy_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return agent.select_action(o, action_mask=m, deterministic=True)

    all_policies: Dict[str, Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int]] = {
        "random_eligible": BASELINE_POLICIES["random_eligible"],
        "weakest_bkt_kc": BASELINE_POLICIES["weakest_bkt_kc"],
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "difficulty_ladder": BASELINE_POLICIES["difficulty_ladder"],
        "dueling_dqn": dqn_policy_fn,
        "forgetting_aware": policy_forgetting_aware,
        "confidence_aware": policy_confidence_aware,
        "frustration_remedial": policy_frustration_remedial,
        "composite_adaptive": policy_composite_adaptive,
    }

    results: Dict[str, Any] = {}

    if verbose:
        print("=" * 80)
        print(f"KT-RL Phase 6: 9-Policy Evaluation Benchmark ({len(seeds)*len(archetypes)} Episodes / Policy)")
        print(f"Seeds: {seeds} | Archetypes: {archetypes}")
        print("=" * 80)

    for p_name, p_fn in all_policies.items():
        t0 = time.time()
        res = evaluate_policy_on_episodes(
            policy_name=p_name,
            policy_fn=p_fn,
            env=env,
            seeds=seeds,
            archetypes=archetypes,
        )
        elapsed = time.time() - t0
        results[p_name] = res

        ov = res["overall"]
        if verbose:
            print(
                f"{p_name:22s} | "
                f"Reward: {ov['mean_cumulative_reward']:6.2f} +/- {ov['reward_ci95']:.2f} | "
                f"NetGain: {ov['mean_net_mastery_gain']:+.4f} | "
                f"Gross: {ov['mean_gross_learning']:+.2f} | "
                f"Acc: {ov['mean_accuracy']*100:4.1f}% | "
                f"Items: {ov['unique_items_selected']:2d}/52 | "
                f"Time: {elapsed:4.1f}s"
            )

    payload = {
        "benchmark_metadata": {
            "title": "KT-RL Phase 6 9-Policy Benchmark",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluation_seeds": seeds,
            "archetypes": archetypes,
            "episodes_per_policy": len(seeds) * len(archetypes),
            "total_decisions_per_policy": len(seeds) * len(archetypes) * 25,
            "steps_per_episode": 25,
        },
        "policy_metrics": {p: r["overall"] for p, r in results.items()},
        "per_archetype_metrics": {p: r["per_archetype"] for p, r in results.items()},
    }

    full_output_path = os.path.join(ROOT_DIR, output_path)
    os.makedirs(os.path.dirname(os.path.abspath(full_output_path)), exist_ok=True)
    with open(full_output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if verbose:
        print("=" * 80)
        print(f"Results successfully saved to {full_output_path}")

    return payload


if __name__ == "__main__":
    run_9_policy_benchmark()
