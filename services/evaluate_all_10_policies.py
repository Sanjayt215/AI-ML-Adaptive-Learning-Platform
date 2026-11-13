"""
Phase 7 10-Policy Comprehensive Comparison Benchmark.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Compares:
1. random_eligible
2. weakest_bkt_kc
3. prereq_aware_weakest
4. difficulty_ladder
5. forgetting_aware
6. confidence_aware
7. frustration_remedial
8. composite_adaptive
9. dueling_dqn
10. linucb_bandit (Contextual Bandit)

Outputs structured comparison to reports/phase7_policy_comparison.json.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.rl_env import ExerciseSelectionEnv
from services.learner_simulator import ARCHETYPES
from services.dqn_agent import DuelingDQNAgent
from services.rl_diagnostics import BASELINE_POLICIES
from services.evaluate_all_9_policies import (
    policy_forgetting_aware,
    policy_confidence_aware,
    policy_frustration_remedial,
    policy_composite_adaptive,
)
from services.evaluate_dqn import evaluate_policy_on_episodes
from services.contextual_bandit import LinUCBBanditPolicy


def run_10_policy_comparison(
    output_path: str = "reports/phase7_policy_comparison.json",
    seeds: Optional[List[int]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    if seeds is None:
        seeds = [101, 202, 303, 404, 505]

    archetypes = list(ARCHETYPES.keys())
    env = ExerciseSelectionEnv(max_steps=25)

    # Setup DQN
    agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
    )
    ckpt = os.path.join(ROOT_DIR, "models/dqn/dueling_dqn_final.pt")
    if os.path.exists(ckpt):
        agent.load_checkpoint(ckpt)

    def dqn_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return agent.select_action(o, action_mask=m, deterministic=True)

    # Setup Contextual Bandit
    bandit = LinUCBBanditPolicy(num_actions=env.num_actions, context_dim=32, alpha=0.5)

    def bandit_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return bandit.select_action(o, action_mask=m, deterministic=True)

    policies = {
        "random_eligible": BASELINE_POLICIES["random_eligible"],
        "weakest_bkt_kc": BASELINE_POLICIES["weakest_bkt_kc"],
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "difficulty_ladder": BASELINE_POLICIES["difficulty_ladder"],
        "forgetting_aware": policy_forgetting_aware,
        "confidence_aware": policy_confidence_aware,
        "frustration_remedial": policy_frustration_remedial,
        "composite_adaptive": policy_composite_adaptive,
        "dueling_dqn": dqn_fn,
        "linucb_bandit": bandit_fn,
    }

    results = {}
    if verbose:
        print("=" * 80)
        print("KT-RL Phase 7: 10-Policy Comprehensive Comparison Benchmark")
        print("=" * 80)

    for p_name, p_fn in policies.items():
        res = evaluate_policy_on_episodes(
            policy_name=p_name,
            policy_fn=p_fn,
            env=env,
            seeds=seeds,
            archetypes=archetypes,
        )
        results[p_name] = res
        ov = res["overall"]
        if verbose:
            print(
                f"{p_name:22s} | "
                f"Reward: {ov['mean_cumulative_reward']:5.2f} +/- {ov['reward_ci95']:.2f} | "
                f"NetGain: {ov['mean_net_mastery_gain']:+.4f} | "
                f"Gross: {ov['mean_gross_learning']:+.2f} | "
                f"Acc: {ov['mean_accuracy']*100:4.1f}% | "
                f"Items: {ov['unique_items_selected']:2d}/52"
            )

    payload = {
        "benchmark_metadata": {
            "title": "KT-RL Phase 7 10-Policy Benchmark",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seeds": seeds,
            "archetypes": archetypes,
            "episodes_per_policy": len(seeds) * len(archetypes),
            "total_episodes": len(policies) * len(seeds) * len(archetypes),
        },
        "policy_metrics": {p: r["overall"] for p, r in results.items()},
        "per_archetype_metrics": {p: r["per_archetype"] for p, r in results.items()},
    }

    full_path = os.path.join(ROOT_DIR, output_path)
    os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if verbose:
        print("=" * 80)
        print(f"Policy comparison successfully saved to {full_path}")

    return payload


if __name__ == "__main__":
    run_10_policy_comparison()
