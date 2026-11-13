"""
Reward Alignment & Counterfactual Diagnostics Engine.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Analyzes the mathematical alignment between RL rewards and pedagogical outcomes:
1. Component Contribution Breakdown: Percentage of total reward from each objective.
2. Correlation Analysis: Pearson correlation r(cumulative_reward, net_mastery_gain).
3. Counterfactual Aligned Reward: Evaluates reward under true information gain
   (entropy reduction delta_H = max(0, H_prior - H_post)) vs static prior entropy.
"""

from __future__ import annotations

import json
import math
import os
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


def compute_aligned_reward(
    mastery_deltas: Dict[str, float],
    prior_bkt: float,
    post_bkt: float,
    item_diff: int,
    is_correct: bool,
    consec_failures: int,
    is_valid: bool = True,
) -> Tuple[float, Dict[str, float]]:
    """
    Principled Counterfactual Aligned Reward:
    - Replaces static prior entropy with TRUE entropy reduction: delta_H = max(0, H(prior) - H(post)).
    - Replaces static challenge match with learning-contingent ZPD bonus.
    - Heavily weights true knowledge improvement.
    """
    if not is_valid:
        return -2.0, {"invalid_penalty": -2.0}

    # 1. True knowledge gain
    gross_delta = sum(max(0.0, d) for d in mastery_deltas.values()) if mastery_deltas else 0.0
    r_mastery = 15.0 * gross_delta

    # 2. True information gain (Entropy reduction)
    p1 = max(0.001, min(0.999, prior_bkt))
    p2 = max(0.001, min(0.999, post_bkt))
    h1 = - (p1 * math.log2(p1) + (1.0 - p1) * math.log2(1.0 - p1))
    h2 = - (p2 * math.log2(p2) + (1.0 - p2) * math.log2(1.0 - p2))
    delta_h = max(0.0, h1 - h2)
    r_info = 1.0 * delta_h

    # 3. Learning-contingent ZPD match (only awarded if learner succeeded or made progress)
    norm_diff = max(0.2, min(1.0, float(item_diff) / 5.0))
    zpd_gap = prior_bkt - norm_diff
    match_bonus = math.exp(-(zpd_gap ** 2) / 0.15)
    r_match = (0.3 * match_bonus) if (is_correct or gross_delta > 0) else 0.0

    # 4. Frustration penalty
    r_penalty = 0.0
    if consec_failures >= 2 and not is_correct:
        r_penalty = -0.5 * (consec_failures - 1)

    # 5. Step cost
    r_step = -0.05

    aligned_total = r_mastery + r_info + r_match + r_penalty + r_step

    return aligned_total, {
        "aligned_mastery": round(r_mastery, 4),
        "aligned_info_reduction": round(r_info, 4),
        "aligned_zpd_match": round(r_match, 4),
        "aligned_penalty": round(r_penalty, 4),
        "aligned_step_cost": round(r_step, 4),
        "aligned_total": round(aligned_total, 4),
    }


def analyze_policy_rewards(
    policy_name: str,
    policy_fn: Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int],
    seeds: List[int],
    archetypes: List[str],
    steps_per_episode: int = 25,
) -> Dict[str, Any]:
    """Runs episodes and collects per-step reward breakdown and correlations."""
    raw_rewards = []
    aligned_rewards = []
    net_gains = []
    gross_gains = []

    comp_totals = {
        "mastery_gain_reward": 0.0,
        "information_entropy_reward": 0.0,
        "zpd_match_reward": 0.0,
        "failure_penalty": 0.0,
        "step_cost": 0.0,
    }

    for arch in archetypes:
        for seed in seeds:
            env = ExerciseSelectionEnv(max_steps=steps_per_episode)
            obs, info = env.reset(seed=seed, options={"archetype": arch})

            init_mastery = env.learner.get_all_hidden_mastery()
            mean_init = float(np.mean(list(init_mastery.values())))

            ep_raw_reward = 0.0
            ep_aligned_reward = 0.0
            ep_gross = 0.0

            done = False
            while not done:
                action = policy_fn(env, obs, info)
                prev_mastery = env.learner.get_all_hidden_mastery()
                primary_kc = env.item_bank[action].get("knowledge_components", ["python"])[0]
                prior_bkt = env.bkt_states.get(primary_kc).mastery_probability if primary_kc in env.bkt_states else 0.20

                obs, reward, term, trunc, info = env.step(action)
                done = term or trunc

                ep_raw_reward += reward

                # Sum components
                rc = info.get("reward_components", {})
                for k in comp_totals:
                    comp_totals[k] += rc.get(k, 0.0)

                # Aligned reward
                post_bkt = env.bkt_states.get(primary_kc).mastery_probability if primary_kc in env.bkt_states else 0.20
                curr_mastery = env.learner.get_all_hidden_mastery()
                deltas = {k: curr_mastery[k] - prev_mastery.get(k, 0.0) for k in curr_mastery}
                for d in deltas.values():
                    if d > 0:
                        ep_gross += d

                diff = env.item_bank[action].get("difficulty", 2)
                is_corr = bool(info.get("is_correct", False))
                consec = max(env.consecutive_failures_by_topic.values()) if env.consecutive_failures_by_topic else 0

                ar, _ = compute_aligned_reward(
                    mastery_deltas=deltas,
                    prior_bkt=prior_bkt,
                    post_bkt=post_bkt,
                    item_diff=diff,
                    is_correct=is_corr,
                    consec_failures=consec,
                    is_valid=True,
                )
                ep_aligned_reward += ar

            final_mastery = env.learner.get_all_hidden_mastery()
            mean_final = float(np.mean(list(final_mastery.values())))
            net_gain = mean_final - mean_init

            raw_rewards.append(ep_raw_reward)
            aligned_rewards.append(ep_aligned_reward)
            net_gains.append(net_gain)
            gross_gains.append(ep_gross)

    # Compute correlation r(raw_reward, net_gain) and r(aligned_reward, net_gain)
    r_matrix_raw = np.corrcoef(raw_rewards, net_gains)[0, 1] if len(raw_rewards) > 1 else 0.0
    r_matrix_aligned = np.corrcoef(aligned_rewards, net_gains)[0, 1] if len(aligned_rewards) > 1 else 0.0

    total_comp_sum = sum(comp_totals.values()) if sum(comp_totals.values()) > 0 else 1.0
    percentages = {k: round(100.0 * v / total_comp_sum, 1) for k, v in comp_totals.items()}

    return {
        "policy": policy_name,
        "mean_raw_reward": round(float(np.mean(raw_rewards)), 2),
        "mean_aligned_reward": round(float(np.mean(aligned_rewards)), 2),
        "mean_net_gain": round(float(np.mean(net_gains)), 4),
        "mean_gross_gain": round(float(np.mean(gross_gains)), 2),
        "pearson_r_raw_vs_net_gain": round(float(r_matrix_raw), 4) if not np.isnan(r_matrix_raw) else 0.0,
        "pearson_r_aligned_vs_net_gain": round(float(r_matrix_aligned), 4) if not np.isnan(r_matrix_aligned) else 0.0,
        "component_contributions_pct": percentages,
    }


def run_reward_alignment_audit(
    seeds: Optional[List[int]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    if seeds is None:
        seeds = [101, 202, 303, 404, 505]

    archetypes = list(ARCHETYPES.keys())
    env_temp = ExerciseSelectionEnv(max_steps=25)

    # Setup DQN
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

    policies = {
        "dueling_dqn": dqn_fn,
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "composite_adaptive": policy_composite_adaptive,
        "confidence_aware": policy_confidence_aware,
        "random_eligible": BASELINE_POLICIES["random_eligible"],
    }

    results = {}
    if verbose:
        print("=" * 80)
        print("KT-RL Phase 7: Reward Alignment & Counterfactual Correlation Audit")
        print("=" * 80)

    for p_name, p_fn in policies.items():
        res = analyze_policy_rewards(
            policy_name=p_name,
            policy_fn=p_fn,
            seeds=seeds,
            archetypes=archetypes,
        )
        results[p_name] = res
        if verbose:
            print(
                f"{p_name:22s} | "
                f"RawReward: {res['mean_raw_reward']:5.1f} (r={res['pearson_r_raw_vs_net_gain']:+.2f}) | "
                f"AlignedReward: {res['mean_aligned_reward']:5.1f} (r={res['pearson_r_aligned_vs_net_gain']:+.2f}) | "
                f"NetGain: {res['mean_net_gain']:+.4f} | "
                f"InfoEntropy%: {res['component_contributions_pct']['information_entropy_reward']}%"
            )

    return results


if __name__ == "__main__":
    run_reward_alignment_audit()
