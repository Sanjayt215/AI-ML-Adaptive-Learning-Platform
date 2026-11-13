"""
Phase 8 Standardized Multi-Policy Research Benchmark.
Part of KT-RL Phase 8: Advanced Policy Audit & RL Improvement Plan.

Evaluates 10 policies under common seeds, archetypes, and standardized metrics:
1. random_eligible
2. difficulty_ladder
3. weakest_bkt_kc
4. prereq_aware_weakest
5. forgetting_aware
6. confidence_aware
7. frustration_remedial
8. composite_adaptive
9. dueling_dqn
10. linucb_bandit

Metrics Reported:
- Mean cumulative reward +/- 95% CI
- Net mastery gain (M_post - M_pre) +/- 95% CI
- Gross positive learning gain
- 7-day delayed retained mastery & retention rate
- Mean response accuracy (%)
- Questions per mastery target / completion
- Invalid action count (prerequisite violations)
- Unique items selected & action entropy
- Mean decision latency (ms)
"""

from __future__ import annotations

import json
import math
import os
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
from services.contextual_bandit import LinUCBBanditPolicy
from services.rl_diagnostics import BASELINE_POLICIES
from services.evaluate_all_9_policies import (
    policy_forgetting_aware,
    policy_confidence_aware,
    policy_frustration_remedial,
    policy_composite_adaptive,
)


def run_comprehensive_benchmark(
    seeds: Optional[List[int]] = None,
    archetypes: Optional[List[str]] = None,
    max_steps: int = 25,
    delay_days: float = 7.0,
    output_json: str = "reports/phase8_benchmark_results.json",
    verbose: bool = True,
) -> Dict[str, Any]:
    if seeds is None:
        seeds = [101, 202, 303, 404, 505]
    if archetypes is None:
        archetypes = list(ARCHETYPES.keys())

    env = ExerciseSelectionEnv(max_steps=max_steps, step_time_delta=0.05)

    # Setup DQN Agent
    dqn_agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
    )
    ckpt = os.path.join(ROOT_DIR, "models/dqn/dueling_dqn_final.pt")
    if os.path.exists(ckpt):
        dqn_agent.load_checkpoint(ckpt)
    dqn_agent.q_online.eval()

    def dqn_policy(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return dqn_agent.select_action(o, action_mask=m, deterministic=True)

    # Setup LinUCB Bandit
    bandit = LinUCBBanditPolicy(num_actions=env.num_actions, context_dim=32, alpha=0.5)

    def bandit_policy(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None:
            m = e.get_action_mask()
        return bandit.select_action(o, action_mask=m, deterministic=True)

    policies: Dict[str, Callable] = {
        "random_eligible": BASELINE_POLICIES["random_eligible"],
        "difficulty_ladder": BASELINE_POLICIES["difficulty_ladder"],
        "weakest_bkt_kc": BASELINE_POLICIES["weakest_bkt_kc"],
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "forgetting_aware": policy_forgetting_aware,
        "confidence_aware": policy_confidence_aware,
        "frustration_remedial": policy_frustration_remedial,
        "composite_adaptive": policy_composite_adaptive,
        "dueling_dqn": dqn_policy,
        "linucb_bandit": bandit_policy,
    }

    benchmark_results = {}
    if verbose:
        print("=" * 95)
        print("AutoLearn KT-RL Phase 8: Standardized 10-Policy Comprehensive Research Benchmark")
        print("=" * 95)

    for p_name, p_fn in policies.items():
        ep_rewards = []
        ep_net_gains = []
        ep_gross_gains = []
        ep_accuracies = []
        ep_retention_rates = []
        ep_delayed_gains = []
        ep_invalids = []
        action_history = []
        latencies_ms = []

        for arch in archetypes:
            for s in seeds:
                obs, info = env.reset(seed=s, options={"archetype": arch})
                init_m = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))

                tot_r = 0.0
                correct_cnt = 0
                gross_delta = 0.0
                invalids_cnt = 0
                step_cnt = 0
                done = False

                while not done:
                    t_start = time.perf_counter()
                    act = p_fn(env, obs, info)
                    t_dur = (time.perf_counter() - t_start) * 1000.0
                    latencies_ms.append(t_dur)

                    action_history.append(act)
                    prev_mastery = env.learner.get_all_hidden_mastery()
                    obs, r, term, trunc, step_info = env.step(act)
                    done = term or trunc
                    step_cnt += 1

                    tot_r += r
                    if step_info.get("is_correct", False):
                        correct_cnt += 1
                    if not step_info.get("is_action_valid", True):
                        invalids_cnt += 1

                    # Gross positive learning gain
                    for k, v in env.learner.get_all_hidden_mastery().items():
                        delta = v - prev_mastery.get(k, v)
                        if delta > 0:
                            gross_delta += delta

                    info = step_info

                post_m = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
                net_g = post_m - init_m

                # 7-day retention delay
                env.learner.apply_forgetting(delta_time=delay_days)
                del_m = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
                ret_rate = (del_m / post_m) if post_m > 1e-4 else 0.0
                del_g = del_m - init_m

                ep_rewards.append(tot_r)
                ep_net_gains.append(net_g)
                ep_gross_gains.append(gross_delta)
                ep_accuracies.append(correct_cnt / max(1, step_cnt))
                ep_retention_rates.append(ret_rate)
                ep_delayed_gains.append(del_g)
                ep_invalids.append(invalids_cnt)

        n_eps = len(ep_rewards)
        mean_r = float(np.mean(ep_rewards))
        std_r = float(np.std(ep_rewards))
        ci95_r = 1.96 * std_r / math.sqrt(n_eps)

        mean_net = float(np.mean(ep_net_gains))
        std_net = float(np.std(ep_net_gains))
        ci95_net = 1.96 * std_net / math.sqrt(n_eps)

        mean_gross = float(np.mean(ep_gross_gains))
        mean_acc = float(np.mean(ep_accuracies))
        mean_ret = float(np.mean(ep_retention_rates))
        mean_del_g = float(np.mean(ep_delayed_gains))
        tot_invalids = int(sum(ep_invalids))
        mean_lat = float(np.mean(latencies_ms))

        # Diversity entropy
        action_counts = Counter(action_history)
        tot_acts = len(action_history)
        entropy = -sum((c / tot_acts) * math.log2(c / tot_acts) for c in action_counts.values())

        p_summary = {
            "policy_name": p_name,
            "episodes": n_eps,
            "mean_cumulative_reward": round(mean_r, 2),
            "std_cumulative_reward": round(std_r, 2),
            "reward_ci95": round(ci95_r, 2),
            "mean_net_mastery_gain": round(mean_net, 4),
            "std_net_mastery_gain": round(std_net, 4),
            "net_mastery_gain_ci95": round(ci95_net, 4),
            "mean_gross_learning": round(mean_gross, 2),
            "mean_accuracy": round(mean_acc, 4),
            "mean_7day_retention_rate": round(mean_ret, 4),
            "mean_7day_delayed_gain": round(mean_del_g, 4),
            "total_invalid_actions": tot_invalids,
            "unique_items_selected": len(action_counts),
            "action_distribution_entropy": round(entropy, 3),
            "mean_latency_ms": round(mean_lat, 3),
        }
        benchmark_results[p_name] = p_summary

        if verbose:
            print(
                f"{p_name:22s} | "
                f"Reward: {mean_r:5.2f} +/- {ci95_r:4.2f} | "
                f"NetGain: {mean_net:+.4f} | "
                f"Gross: {mean_gross:4.2f} | "
                f"Ret7d: {mean_ret*100:4.1f}% | "
                f"Acc: {mean_acc*100:4.1f}% | "
                f"Items: {len(action_counts):2d}/52 | "
                f"Lat: {mean_lat:4.2f}ms"
            )

    full_output = {
        "benchmark_metadata": {
            "title": "AutoLearn KT-RL Phase 8 Standardized Multi-Policy Benchmark",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seeds": seeds,
            "archetypes": archetypes,
            "max_steps": max_steps,
            "delay_days": delay_days,
            "step_time_delta": 0.05,
            "reward_version": "Phase 8 Entropy-Reduction & Learning-Aligned Reward",
            "total_episodes": len(policies) * len(seeds) * len(archetypes),
        },
        "policy_metrics": benchmark_results,
    }

    full_path = os.path.join(ROOT_DIR, output_json)
    os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    if verbose:
        print("=" * 95)
        print(f"Benchmark results successfully saved to: {full_path}")

    return full_output


if __name__ == "__main__":
    run_comprehensive_benchmark()
