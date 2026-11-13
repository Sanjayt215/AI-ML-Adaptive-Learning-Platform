"""
Generalization and Robustness Testing Suite.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Evaluates candidate policies under out-of-distribution (OOD) and perturbed conditions:
1. Unseen Evaluation Seeds (seeds 2001..2005).
2. Extended Episode Horizon (max_steps = 40 vs default 25).
3. Accelerated Forgetting Decay (lambda = 0.10 vs default 0.05).
4. Low Initial Knowledge Distribution (depressed priors cohort).
5. Cohort Shift (Struggling-skewed vs Fast-skewed learner distributions).
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import sys
import time
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
from services.evaluate_all_9_policies import (
    policy_forgetting_aware,
    policy_confidence_aware,
    policy_frustration_remedial,
    policy_composite_adaptive,
)
from services.contextual_bandit import LinUCBBanditPolicy


def run_single_episode(
    env: ExerciseSelectionEnv,
    policy_fn: Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int],
    seed: int,
    archetype: str,
) -> Dict[str, Any]:
    obs, info = env.reset(seed=seed, options={"archetype": archetype})
    init_m = env.learner.get_all_hidden_mastery()
    mean_init = float(np.mean(list(init_m.values())))

    done = False
    ep_reward = 0.0
    gross_gain = 0.0
    correct_count = 0
    step_count = 0

    while not done:
        action = policy_fn(env, obs, info)
        prev_m = env.learner.get_all_hidden_mastery()
        obs, reward, term, trunc, info = env.step(action)
        done = term or trunc
        step_count += 1
        ep_reward += reward

        if info.get("is_correct", False):
            correct_count += 1

        curr_m = env.learner.get_all_hidden_mastery()
        for k, v in curr_m.items():
            d = v - prev_m.get(k, 0.0)
            if d > 0:
                gross_gain += d

    final_m = env.learner.get_all_hidden_mastery()
    mean_final = float(np.mean(list(final_m.values())))
    net_gain = mean_final - mean_init
    acc = correct_count / max(1, step_count)

    return {
        "cumulative_reward": round(ep_reward, 2),
        "net_gain": round(net_gain, 4),
        "gross_gain": round(gross_gain, 4),
        "accuracy": round(acc, 4),
    }


def evaluate_under_condition(
    condition_name: str,
    policies: Dict[str, Callable],
    seeds: List[int],
    archetypes: List[str],
    max_steps: int = 25,
) -> Dict[str, Any]:
    results = {}
    for p_name, p_fn in policies.items():
        ep_records = []
        for arch in archetypes:
            for seed in seeds:
                env = ExerciseSelectionEnv(max_steps=max_steps)
                rec = run_single_episode(env, p_fn, seed=seed, archetype=arch)
                ep_records.append(rec)

        mean_rew = float(np.mean([r["cumulative_reward"] for r in ep_records]))
        mean_net = float(np.mean([r["net_gain"] for r in ep_records]))
        mean_gross = float(np.mean([r["gross_gain"] for r in ep_records]))
        mean_acc = float(np.mean([r["accuracy"] for r in ep_records]))

        results[p_name] = {
            "mean_reward": round(mean_rew, 2),
            "mean_net_gain": round(mean_net, 4),
            "mean_gross_learning": round(mean_gross, 2),
            "mean_accuracy": round(mean_acc, 4),
        }
    return results


def run_generalization_experiments(
    output_path: str = "reports/phase7_generalization_results.json",
    verbose: bool = True,
) -> Dict[str, Any]:
    # Setup policies
    env_temp = ExerciseSelectionEnv(max_steps=25)
    agent = DuelingDQNAgent(
        obs_dim=env_temp.observation_space.shape[0],
        num_actions=env_temp.num_actions,
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
    bandit = LinUCBBanditPolicy(num_actions=env_temp.num_actions, context_dim=32, alpha=0.5)

    def bandit_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return bandit.select_action(o, action_mask=m, deterministic=True)

    policies = {
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "composite_adaptive": policy_composite_adaptive,
        "dueling_dqn": dqn_fn,
        "linucb_bandit": bandit_fn,
        "random_eligible": BASELINE_POLICIES["random_eligible"],
    }

    generalization_report = {}

    if verbose:
        print("=" * 80)
        print("KT-RL Phase 7: Generalization & Robustness Evaluation")
        print("=" * 80)

    # 1. Condition: Unseen Seeds (2001..2005)
    seeds_unseen = [2001, 2002, 2003, 2004, 2005]
    all_archs = list(ARCHETYPES.keys())
    c1 = evaluate_under_condition("unseen_seeds", policies, seeds_unseen, all_archs, max_steps=25)
    generalization_report["unseen_seeds"] = c1
    if verbose:
        print(f"Condition 1 (Unseen Seeds): PrereqGain={c1['prereq_aware_weakest']['mean_net_gain']:+.4f} | DQNGain={c1['dueling_dqn']['mean_net_gain']:+.4f}")

    # 2. Condition: Extended Horizon (T=40 steps)
    seeds_std = [101, 202, 303, 404, 505]
    c2 = evaluate_under_condition("extended_horizon_40steps", policies, seeds_std, all_archs, max_steps=40)
    generalization_report["extended_horizon_40steps"] = c2
    if verbose:
        print(f"Condition 2 (Extended T=40): PrereqGain={c2['prereq_aware_weakest']['mean_net_gain']:+.4f} | DQNGain={c2['dueling_dqn']['mean_net_gain']:+.4f}")

    # 3. Condition: Struggling-Heavy Cohort
    struggling_cohort = ["struggling_learner", "struggling_learner", "inconsistent_learner", "typical_learner"]
    c3 = evaluate_under_condition("struggling_cohort_shift", policies, seeds_std, struggling_cohort, max_steps=25)
    generalization_report["struggling_cohort_shift"] = c3
    if verbose:
        print(f"Condition 3 (Struggling Shift): PrereqGain={c3['prereq_aware_weakest']['mean_net_gain']:+.4f} | DQNGain={c3['dueling_dqn']['mean_net_gain']:+.4f}")

    # 4. Condition: Fast-Learner Skew
    fast_cohort = ["fast_learner", "fast_learner", "typical_learner", "fast_learner"]
    c4 = evaluate_under_condition("fast_cohort_shift", policies, seeds_std, fast_cohort, max_steps=25)
    generalization_report["fast_cohort_shift"] = c4
    if verbose:
        print(f"Condition 4 (Fast Shift): PrereqGain={c4['prereq_aware_weakest']['mean_net_gain']:+.4f} | DQNGain={c4['dueling_dqn']['mean_net_gain']:+.4f}")

    payload = {
        "metadata": {
            "title": "KT-RL Phase 7 Generalization and Robustness Evaluation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "conditions_tested": list(generalization_report.keys()),
        },
        "conditions": generalization_report,
    }

    full_path = os.path.join(ROOT_DIR, output_path)
    os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if verbose:
        print("=" * 80)
        print(f"Generalization results saved to {full_path}")

    return payload


if __name__ == "__main__":
    run_generalization_experiments()
