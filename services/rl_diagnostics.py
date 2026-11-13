"""
Diagnostics & Baseline Policy Evaluation Suite.
Part of KT-RL Phase 3: Learner Simulator & Reinforcement Learning Environment.

Evaluates 4 heuristic baseline policies across 4 learner archetypes over multiple random seeds:
1. Random eligible action (baseline stochastic exploration).
2. Weakest estimated BKT KC first (diagnostic focus on low mastery).
3. Difficulty-only heuristic (stepping through easy to hard).
4. Prerequisite-aware weakest-KC selection (pedagogically sound rule-based baseline).

Produces reproducible diagnostic metrics:
- Mean and standard deviation of simulated ground-truth mastery gain.
- Mean episode length and completion rates.
- Accuracy / Correct response rate.
- Invalid action count / Prerequisite violation rate (strictly 0.0 with masking).
- BKT estimation error against hidden simulator truth (MAE/RMSE).
- Output serialized to `autolearn_fullstack/reports/phase3_environment_diagnostics.json`.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Dict, List, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.rl_env import ExerciseSelectionEnv
from services.learner_simulator import ARCHETYPES


# Baseline policy implementations: (env, obs, info) -> action_int

def policy_random_eligible(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    return env.action_space.sample(mask=mask)


def policy_weakest_bkt_kc(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Pick valid action whose primary topic has the lowest observable BKT mastery
    best_action = valid_indices[0]
    lowest_mastery = 1.0

    for idx in valid_indices:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p_val = m.mastery_probability if m else 0.20
        if p_val < lowest_mastery:
            lowest_mastery = p_val
            best_action = idx

    return best_action


def policy_difficulty_ladder(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Sort valid actions by ascending difficulty
    return min(valid_indices, key=lambda i: env.item_bank[i].get("difficulty", 2))


def policy_prereq_aware_weakest(env: ExerciseSelectionEnv, obs: np.ndarray, info: Dict[str, Any]) -> int:
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Balance: Prioritize lowest BKT mastery, tie-broken by lowest difficulty
    def score_item(idx: int) -> Tuple[float, int]:
        item = env.item_bank[idx]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "general")
        m = env.bkt_states.get(primary, None)
        p_val = m.mastery_probability if m else 0.20
        diff = item.get("difficulty", 2)
        return (p_val, diff)

    return min(valid_indices, key=score_item)


BASELINE_POLICIES: Dict[str, Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int]] = {
    "random_eligible": policy_random_eligible,
    "weakest_bkt_kc": policy_weakest_bkt_kc,
    "difficulty_ladder": policy_difficulty_ladder,
    "prereq_aware_weakest": policy_prereq_aware_weakest,
}


def run_episode(
    env: ExerciseSelectionEnv,
    policy_fn: Callable[[ExerciseSelectionEnv, np.ndarray, Dict[str, Any]], int],
    seed: int,
    archetype: str,
) -> Dict[str, Any]:
    """Runs a single evaluation episode under a fixed seed and policy."""
    obs, info = env.reset(seed=seed, options={"archetype": archetype})

    # Track initial hidden ground-truth mastery
    init_hidden_mastery = np.mean(list(env.learner.get_all_hidden_mastery().values()))

    total_reward = 0.0
    correct_count = 0
    step_count = 0
    invalid_actions = 0
    bkt_errors = []

    while True:
        action = policy_fn(env, obs, info)
        next_obs, reward, terminated, truncated, step_info = env.step(action)

        total_reward += reward
        step_count += 1
        if step_info.get("is_correct"):
            correct_count += 1
        if not step_info.get("is_action_valid", True):
            invalid_actions += 1

        # Track BKT estimation error against hidden truth for primary topic
        topic = step_info.get("topic")
        if topic:
            hidden_m = step_info.get("_diag_hidden_mastery", 0.0)
            bkt_m = step_info.get("bkt_posterior", 0.20)
            bkt_errors.append(abs(bkt_m - hidden_m))

        obs = next_obs
        info = step_info

        if terminated or truncated:
            break

    # Final hidden ground-truth mastery
    final_hidden_mastery = np.mean(list(env.learner.get_all_hidden_mastery().values()))
    mastery_gain = final_hidden_mastery - init_hidden_mastery

    return {
        "seed": seed,
        "archetype": archetype,
        "steps": step_count,
        "total_reward": round(total_reward, 4),
        "accuracy": round(correct_count / max(1, step_count), 4),
        "invalid_actions": invalid_actions,
        "init_hidden_mastery": round(init_hidden_mastery, 4),
        "final_hidden_mastery": round(final_hidden_mastery, 4),
        "ground_truth_mastery_gain": round(mastery_gain, 4),
        "mean_bkt_mae": round(float(np.mean(bkt_errors)), 4) if bkt_errors else 0.0,
    }


def evaluate_all_baselines(
    seeds: List[int] = [101, 202, 303, 404, 505],
    archetypes: Optional[List[str]] = None,
    max_steps: int = 25,
) -> Dict[str, Any]:
    """Runs cross-archetype, multi-seed evaluation across all 4 baseline policies."""
    if archetypes is None:
        archetypes = list(ARCHETYPES.keys())

    env = ExerciseSelectionEnv(max_steps=max_steps)
    results: Dict[str, Any] = {
        "evaluation_config": {
            "seeds": seeds,
            "archetypes": archetypes,
            "max_steps_per_episode": max_steps,
            "total_episodes_per_policy": len(seeds) * len(archetypes),
            "num_canonical_items": env.num_actions,
            "num_topics": env.num_topics,
        },
        "policies": {},
    }

    for policy_name, policy_fn in BASELINE_POLICIES.items():
        policy_records = []
        for arch in archetypes:
            for seed in seeds:
                ep_res = run_episode(env, policy_fn, seed=seed, archetype=arch)
                policy_records.append(ep_res)

        gains = [r["ground_truth_mastery_gain"] for r in policy_records]
        rewards = [r["total_reward"] for r in policy_records]
        accuracies = [r["accuracy"] for r in policy_records]
        invalids = sum(r["invalid_actions"] for r in policy_records)
        bkt_maes = [r["mean_bkt_mae"] for r in policy_records]

        # Archetype breakdown
        by_arch: Dict[str, Any] = {}
        for arch in archetypes:
            arch_records = [r for r in policy_records if r["archetype"] == arch]
            arch_gains = [r["ground_truth_mastery_gain"] for r in arch_records]
            by_arch[arch] = {
                "mean_mastery_gain": round(float(np.mean(arch_gains)), 4),
                "std_mastery_gain": round(float(np.std(arch_gains)), 4),
                "mean_reward": round(float(np.mean([r["total_reward"] for r in arch_records])), 4),
                "mean_accuracy": round(float(np.mean([r["accuracy"] for r in arch_records])), 4),
            }

        results["policies"][policy_name] = {
            "summary": {
                "mean_ground_truth_mastery_gain": round(float(np.mean(gains)), 4),
                "std_ground_truth_mastery_gain": round(float(np.std(gains)), 4),
                "mean_cumulative_reward": round(float(np.mean(rewards)), 4),
                "std_cumulative_reward": round(float(np.std(rewards)), 4),
                "mean_accuracy": round(float(np.mean(accuracies)), 4),
                "total_invalid_actions": invalids,
                "mean_bkt_mae_vs_truth": round(float(np.mean(bkt_maes)), 4),
            },
            "by_archetype": by_arch,
            "episodes": policy_records,
        }

    return results


def save_diagnostic_report(output_path: Optional[str] = None) -> str:
    """Executes evaluation and writes structured JSON output."""
    if output_path is None:
        reports_dir = os.path.join(ROOT_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output_path = os.path.join(reports_dir, "phase3_environment_diagnostics.json")

    diagnostics = evaluate_all_baselines()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    return output_path


if __name__ == "__main__":
    out = save_diagnostic_report()
    print(f"Phase 3 Environment Diagnostics generated at: {out}")
