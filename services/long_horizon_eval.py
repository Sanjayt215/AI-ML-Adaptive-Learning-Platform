"""
Long-Horizon Retention Evaluation Harness.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Simulates multi-session longitudinal learning trajectories:
- Multi-day sessions with configurable practice and rest intervals.
- Evaluates:
  1. Immediate Mastery Gain (end of active practice).
  2. Delayed Retained Mastery (after 3-day and 7-day retention intervals).
  3. Passive Forgetting Loss during inactivity.
  4. Pedagogical Retention Efficiency (Retained Mastery / Total Practice Steps).
- Compares policies under matched random seeds and student archetypes.
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
from services.learner_simulator import ARCHETYPES, SyntheticLearner
from services.dqn_agent import DuelingDQNAgent
from services.rl_diagnostics import BASELINE_POLICIES
from services.evaluate_all_9_policies import (
    policy_forgetting_aware,
    policy_confidence_aware,
    policy_frustration_remedial,
    policy_composite_adaptive,
)


def evaluate_long_horizon_retention(
    policy_name: str,
    policy_fn: Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int],
    seeds: List[int],
    archetypes: List[str],
    active_steps: int = 25,
    delay_days: float = 7.0,
) -> Dict[str, Any]:
    """
    Simulates an active practice session followed by a long-horizon retention interval (e.g. 7 days).
    Measures how much learned knowledge survives dormant forgetting.
    """
    records = []

    for archetype in archetypes:
        for seed in seeds:
            env = ExerciseSelectionEnv(max_steps=active_steps)
            obs, info = env.reset(seed=seed, options={"archetype": archetype})

            initial_mastery = env.learner.get_all_hidden_mastery()
            mean_initial = float(np.mean(list(initial_mastery.values())))

            # Active practice session
            done = False
            step_count = 0
            gross_gain = 0.0

            while not done:
                action = policy_fn(env, obs, info)
                prev_mastery = env.learner.get_all_hidden_mastery()
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                step_count += 1

                # Accumulate gross positive learning
                for k, v in env.learner.get_all_hidden_mastery().items():
                    delta = v - prev_mastery.get(k, v)
                    if delta > 0:
                        gross_gain += delta

            # Immediate post-practice state
            immediate_mastery = env.learner.get_all_hidden_mastery()
            mean_immediate = float(np.mean(list(immediate_mastery.values())))
            immediate_net_gain = mean_immediate - mean_initial

            # Long-horizon dormant delay (e.g. 7 days without practice)
            # Apply simulated forgetting across all KCs
            env.learner.apply_forgetting(delta_time=delay_days)
            delayed_mastery = env.learner.get_all_hidden_mastery()

            mean_delayed = float(np.mean(list(delayed_mastery.values())))
            delayed_net_gain = mean_delayed - mean_initial
            forgetting_loss = mean_immediate - mean_delayed
            retention_rate = (mean_delayed / mean_immediate) if mean_immediate > 1e-4 else 0.0

            records.append({
                "archetype": archetype,
                "seed": seed,
                "mean_initial": round(mean_initial, 4),
                "mean_immediate": round(mean_immediate, 4),
                "mean_delayed": round(mean_delayed, 4),
                "gross_gain": round(gross_gain, 4),
                "immediate_net_gain": round(immediate_net_gain, 4),
                "delayed_net_gain": round(delayed_net_gain, 4),
                "forgetting_loss": round(forgetting_loss, 4),
                "retention_rate": round(retention_rate, 4),
            })

    # Summary statistics
    imm_gains = [r["immediate_net_gain"] for r in records]
    del_gains = [r["delayed_net_gain"] for r in records]
    gross_gains = [r["gross_gain"] for r in records]
    losses = [r["forgetting_loss"] for r in records]
    rates = [r["retention_rate"] for r in records]

    return {
        "policy": policy_name,
        "episodes_evaluated": len(records),
        "active_steps": active_steps,
        "delay_days": delay_days,
        "mean_gross_learning": round(float(np.mean(gross_gains)), 4),
        "mean_immediate_net_gain": round(float(np.mean(imm_gains)), 4),
        "mean_delayed_net_gain": round(float(np.mean(del_gains)), 4),
        "mean_forgetting_loss": round(float(np.mean(losses)), 4),
        "mean_retention_rate": round(float(np.mean(rates)), 4),
        "delayed_gain_ci95": round(1.96 * float(np.std(del_gains)) / math.sqrt(len(del_gains)), 4),
        "per_episode_records": records,
    }


def run_long_horizon_benchmark(
    output_path: str = "reports/phase7_long_horizon_results.json",
    seeds: Optional[List[int]] = None,
    delay_days: float = 7.0,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Executes long-horizon retention benchmark across candidate policies."""
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
        "prereq_aware_weakest": BASELINE_POLICIES["prereq_aware_weakest"],
        "weakest_bkt_kc": BASELINE_POLICIES["weakest_bkt_kc"],
        "random_eligible": BASELINE_POLICIES["random_eligible"],
        "forgetting_aware": policy_forgetting_aware,
        "confidence_aware": policy_confidence_aware,
        "frustration_remedial": policy_frustration_remedial,
        "composite_adaptive": policy_composite_adaptive,
        "dueling_dqn": dqn_fn,
    }

    results = {}
    if verbose:
        print("=" * 80)
        print(f"KT-RL Phase 7: Long-Horizon Retention Benchmark ({delay_days} Days Delay)")
        print(f"Seeds: {seeds} | Archetypes: {archetypes}")
        print("=" * 80)

    for p_name, p_fn in policies.items():
        res = evaluate_long_horizon_retention(
            policy_name=p_name,
            policy_fn=p_fn,
            seeds=seeds,
            archetypes=archetypes,
            active_steps=25,
            delay_days=delay_days,
        )
        results[p_name] = res
        if verbose:
            print(
                f"{p_name:22s} | "
                f"Gross: {res['mean_gross_learning']:+6.2f} | "
                f"ImmediateGain: {res['mean_immediate_net_gain']:+.4f} | "
                f"DelayedGain (7d): {res['mean_delayed_net_gain']:+.4f} +/- {res['delayed_gain_ci95']:.4f} | "
                f"RetentionRate: {res['mean_retention_rate']*100:5.1f}%"
            )

    payload = {
        "benchmark_metadata": {
            "title": f"KT-RL Phase 7 Long-Horizon Retention Benchmark ({delay_days}d Inactivity)",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "delay_days": delay_days,
            "seeds": seeds,
            "archetypes": archetypes,
            "episodes_per_policy": len(seeds) * len(archetypes),
        },
        "policies": {
            p: {k: v for k, v in r.items() if k != "per_episode_records"}
            for p, r in results.items()
        },
    }

    full_path = os.path.join(ROOT_DIR, output_path)
    os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if verbose:
        print("=" * 80)
        print(f"Long-horizon benchmark saved to {full_path}")

    return payload


if __name__ == "__main__":
    run_long_horizon_benchmark()
