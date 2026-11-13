"""
Rigorous Evaluation Engine & Comprehensive Baseline Benchmark.
Part of KT-RL Phase 5: Adaptive Policy Evaluation & Ablation Studies.

Evaluates policies on held-out evaluation seeds across all 4 learner archetypes:
- Deterministic policy execution (frozen weights, epsilon=0)
- Net true mastery gain & Gross learning improvement
- Cumulative reward and full reward component breakdown
- Question selection diversity (unique questions, frequency entropy)
- Accuracy, episode length, prerequisite violations (invalids)
- BKT estimation error (MAE)
- Granular per-archetype metrics & aggregated metrics with confidence intervals
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


def evaluate_policy_on_episodes(
    policy_name: str,
    policy_fn: Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int],
    env: ExerciseSelectionEnv,
    seeds: List[int],
    archetypes: List[str],
) -> Dict[str, Any]:
    """
    Evaluates a policy across specified seeds and archetypes.
    Records comprehensive metrics per episode and computes aggregate statistics.
    """
    episode_records: List[Dict[str, Any]] = []
    per_archetype_records: Dict[str, List[Dict[str, Any]]] = {arch: [] for arch in archetypes}
    all_selected_actions: List[int] = []

    for archetype in archetypes:
        for seed in seeds:
            obs, info = env.reset(seed=seed, options={"archetype": archetype})
            init_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))

            ep_reward = 0.0
            gross_gain = 0.0
            correct_count = 0
            ep_steps = 0
            ep_invalids = 0
            rc_accum = {
                "mastery_gain_reward": 0.0,
                "information_entropy_reward": 0.0,
                "zpd_match_reward": 0.0,
                "failure_penalty": 0.0,
                "step_cost": 0.0,
            }

            terminated = False
            truncated = False

            while not (terminated or truncated):
                action = policy_fn(env, obs, info)
                all_selected_actions.append(action)

                next_obs, reward, terminated, truncated, step_info = env.step(action)
                ep_reward += reward
                ep_steps += 1

                if step_info.get("is_correct", False):
                    correct_count += 1
                if not step_info.get("is_action_valid", True):
                    ep_invalids += 1

                # Accumulate gross learning deltas
                deltas = step_info.get("_diag_mastery_deltas", {})
                gross_gain += sum(deltas.values())

                # Accumulate reward components
                rc = step_info.get("reward_components", {})
                for k in rc_accum:
                    rc_accum[k] += rc.get(k, 0.0)

                obs = next_obs
                info = step_info

            final_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
            net_gain = final_mastery - init_mastery
            accuracy = correct_count / ep_steps if ep_steps > 0 else 0.0

            # BKT estimation error against hidden ground truth
            sim_mastery = np.array(list(env.learner.get_all_hidden_mastery().values()))
            bkt_vals = np.array([state.mastery_probability for state in env.bkt_states.values()])
            bkt_mae = float(np.mean(np.abs(sim_mastery - bkt_vals))) if len(sim_mastery) == len(bkt_vals) else 0.0

            rec = {
                "seed": seed,
                "archetype": archetype,
                "steps": ep_steps,
                "reward": round(ep_reward, 3),
                "accuracy": round(accuracy, 4),
                "init_mastery": round(init_mastery, 4),
                "final_mastery": round(final_mastery, 4),
                "net_mastery_gain": round(net_gain, 4),
                "gross_learning": round(gross_gain, 4),
                "invalid_actions": ep_invalids,
                "bkt_mae": round(bkt_mae, 4),
                "reward_components": {k: round(v, 3) for k, v in rc_accum.items()},
            }
            episode_records.append(rec)
            per_archetype_records[archetype].append(rec)

    # Diversity metrics over all selections made by the policy
    total_actions = len(all_selected_actions)
    action_counts = Counter(all_selected_actions)
    unique_actions = len(action_counts)
    # Shannon entropy of action selection distribution
    probs = [c / total_actions for c in action_counts.values()]
    action_entropy = -sum(p * math.log2(p) for p in probs) if probs else 0.0

    def summarize_records(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        rewards = [r["reward"] for r in recs]
        net_gains = [r["net_mastery_gain"] for r in recs]
        gross_gains = [r["gross_learning"] for r in recs]
        accuracies = [r["accuracy"] for r in recs]
        invalids = [r["invalid_actions"] for r in recs]
        maes = [r["bkt_mae"] for r in recs]
        steps = [r["steps"] for r in recs]

        n = len(recs)
        r_mean = float(np.mean(rewards))
        r_std = float(np.std(rewards))
        # 95% Confidence Interval for mean reward
        r_ci95 = 1.96 * (r_std / math.sqrt(n)) if n > 1 else 0.0

        g_mean = float(np.mean(net_gains))
        g_std = float(np.std(net_gains))
        g_ci95 = 1.96 * (g_std / math.sqrt(n)) if n > 1 else 0.0

        # Mean reward components
        rc_keys = ["mastery_gain_reward", "information_entropy_reward", "zpd_match_reward", "failure_penalty", "step_cost"]
        mean_rc = {k: round(float(np.mean([r["reward_components"][k] for r in recs])), 2) for k in rc_keys}

        return {
            "n_episodes": n,
            "mean_cumulative_reward": round(r_mean, 2),
            "std_cumulative_reward": round(r_std, 2),
            "reward_ci95": round(r_ci95, 2),
            "mean_net_mastery_gain": round(g_mean, 4),
            "std_net_mastery_gain": round(g_std, 4),
            "net_mastery_gain_ci95": round(g_ci95, 4),
            "mean_gross_learning": round(float(np.mean(gross_gains)), 4),
            "mean_accuracy": round(float(np.mean(accuracies)), 4),
            "mean_episode_length": round(float(np.mean(steps)), 2),
            "total_invalid_actions": int(np.sum(invalids)),
            "mean_bkt_mae": round(float(np.mean(maes)), 4),
            "mean_reward_components": mean_rc,
        }

    overall_summary = summarize_records(episode_records)
    overall_summary["unique_items_selected"] = unique_actions
    overall_summary["action_distribution_entropy"] = round(action_entropy, 3)

    per_arch_summary = {arch: summarize_records(recs) for arch, recs in per_archetype_records.items()}

    return {
        "policy_name": policy_name,
        "overall": overall_summary,
        "per_archetype": per_arch_summary,
        "episodes": episode_records,
    }


def run_comprehensive_evaluation(
    checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
    output_path: str = "reports/phase5_evaluation.json",
    seeds: Optional[List[int]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Executes fair, held-out evaluation across 100 episodes (25 seeds x 4 archetypes)
    for Dueling DQN and all 4 baselines.
    """
    if seeds is None:
        # 25 independent held-out seeds (seeds 1001 to 1025)
        seeds = [1000 + i for i in range(1, 26)]

    archetypes = list(ARCHETYPES.keys())
    env = ExerciseSelectionEnv(max_steps=25)

    # 1. Setup Dueling DQN agent
    agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
    )
    agent.load_checkpoint(checkpoint_path)

    def dqn_policy_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return agent.select_action(o, action_mask=m, deterministic=True)

    policies: Dict[str, Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int]] = {
        "dueling_dqn": dqn_policy_fn,
        "random_eligible": BASELINE_POLICIES["random_eligible"],
        "weakest_bkt_kc": BASELINE_POLICIES["weakest_bkt_kc"],
        "difficulty_ladder": BASELINE_POLICIES["difficulty_ladder"],
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
    }

    results: Dict[str, Any] = {}

    if verbose:
        print(f"=== Running Phase 5 Rigorous Evaluation: {len(seeds)*len(archetypes)} Episodes Per Policy ===")
        print(f"Seeds: {len(seeds)} | Archetypes: {len(archetypes)} | Total per policy: {len(seeds)*len(archetypes)}")

    for p_name, p_fn in policies.items():
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
                f"{p_name:20s} | "
                f"Reward: {ov['mean_cumulative_reward']:6.2f} ± {ov['reward_ci95']:.2f} | "
                f"NetGain: {ov['mean_net_mastery_gain']:+.4f} ± {ov['net_mastery_gain_ci95']:.4f} | "
                f"Gross: {ov['mean_gross_learning']:+.2f} | "
                f"Acc: {ov['mean_accuracy']*100:4.1f}% | "
                f"Items: {ov['unique_items_selected']:2d}/52 | "
                f"Time: {elapsed:4.1f}s"
            )

    payload = {
        "evaluation_config": {
            "eval_seeds": seeds,
            "archetypes": archetypes,
            "episodes_per_policy": len(seeds) * len(archetypes),
            "checkpoint_evaluated": checkpoint_path,
            "steps_per_episode": 25,
        },
        "policies": {p: {"overall": r["overall"], "per_archetype": r["per_archetype"]} for p, r in results.items()},
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


if __name__ == "__main__":
    run_comprehensive_evaluation()
