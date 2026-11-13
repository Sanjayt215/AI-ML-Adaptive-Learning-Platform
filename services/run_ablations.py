"""
Ablation Studies Suite for Dueling DQN Architecture and Environment Components.
Part of KT-RL Phase 5: Adaptive Policy Evaluation & Ablation Studies.

Evaluates:
1. Double DQN vs Standard DQN Target Bootstrapping.
2. Multi-Objective Reward Ablation:
   - Full Reward
   - No Information Entropy Reward (w_info_gain = 0.0)
   - No ZPD Challenge Matching Reward (w_challenge_match = 0.0)
   - No Anti-Frustration Penalty (w_failure_penalty = 0.0)
3. Action Masking Ablation:
   - Prerequisite-Constrained Selection (Standard)
   - Unconstrained Action Selection (Mask Ignored, Violations Tracked)
4. Training-Seed Sensitivity:
   - Models trained with seeds 42, 123, 777 evaluated on identical held-out seeds.

Exports complete machine-readable report to: `reports/phase5_ablation_results.json`
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.rl_env import ExerciseSelectionEnv
from services.learner_simulator import ARCHETYPES
from services.rl_reward import RewardWeights, compute_reward
from services.dqn_agent import DuelingDQNAgent
from services.evaluate_dqn import evaluate_policy_on_episodes


def run_double_vs_standard_dqn_ablation(
    train_episodes: int = 40,
    eval_seeds: Optional[List[int]] = None,
    checkpoint_dir: str = "models/dqn/ablations",
) -> Dict[str, Any]:
    """
    Compares Double DQN vs Standard DQN training and evaluation under identical settings.
    """
    if eval_seeds is None:
        eval_seeds = [1001, 1002, 1003, 1004, 1005]  # 5 seeds x 4 archetypes = 20 episodes

    os.makedirs(checkpoint_dir, exist_ok=True)
    archetypes = list(ARCHETYPES.keys())
    results = {}

    for is_double in [True, False]:
        tag = "double_dqn" if is_double else "standard_dqn"
        env = ExerciseSelectionEnv(max_steps=25)
        agent = DuelingDQNAgent(
            obs_dim=env.observation_space.shape[0],
            num_actions=env.num_actions,
            hidden_dim=128,
            double_dqn=is_double,
            seed=42,
        )

        # Train for train_episodes
        for ep in range(1, train_episodes + 1):
            arch = archetypes[(ep - 1) % len(archetypes)]
            obs, info = env.reset(seed=42 + ep * 100, options={"archetype": arch})
            done = False
            while not done:
                mask = info.get("action_mask")
                if mask is None: mask = env.get_action_mask()
                action = agent.select_action(obs, action_mask=mask, deterministic=False)
                next_obs, r, term, trunc, next_info = env.step(action)
                agent.total_steps += 1
                agent.decay_epsilon()
                next_mask = next_info.get("action_mask")
                if next_mask is None: next_mask = env.get_action_mask()
                agent.replay_buffer.push(obs, action, r, next_obs, term, trunc, next_mask)
                if ep > 5:
                    agent.train_step()
                obs = next_obs
                info = next_info
                done = term or trunc

        # Evaluate deterministically
        def policy_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
            m = inf.get("action_mask")
            if m is None: m = e.get_action_mask()
            return agent.select_action(o, action_mask=m, deterministic=True)

        res = evaluate_policy_on_episodes(tag, policy_fn, env, seeds=eval_seeds, archetypes=archetypes)
        results[tag] = res["overall"]

    return results


def run_reward_component_ablation(
    eval_seeds: Optional[List[int]] = None,
    checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
) -> Dict[str, Any]:
    """
    Evaluates policy under isolated reward weight variants.
    """
    if eval_seeds is None:
        eval_seeds = [1001, 1002, 1003, 1004, 1005]

    archetypes = list(ARCHETYPES.keys())
    agent = DuelingDQNAgent(obs_dim=99, num_actions=52)
    agent.load_checkpoint(checkpoint_path)

    def policy_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None: m = e.get_action_mask()
        return agent.select_action(o, action_mask=m, deterministic=True)

    reward_configs = {
        "full_reward": RewardWeights(),
        "no_info_gain": RewardWeights(w_info_gain=0.0),
        "no_zpd_match": RewardWeights(w_challenge_match=0.0),
        "no_failure_penalty": RewardWeights(w_failure_penalty=0.0),
    }

    results = {}
    for r_name, r_weights in reward_configs.items():
        env = ExerciseSelectionEnv(max_steps=25, reward_weights=r_weights)
        res = evaluate_policy_on_episodes(r_name, policy_fn, env, seeds=eval_seeds, archetypes=archetypes)
        results[r_name] = res["overall"]

    return results


def run_masking_ablation(
    eval_seeds: Optional[List[int]] = None,
    checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
) -> Dict[str, Any]:
    """
    Compares standard prerequisite-masked execution against an unconstrained variant.
    """
    if eval_seeds is None:
        eval_seeds = [1001, 1002, 1003, 1004, 1005]

    archetypes = list(ARCHETYPES.keys())
    agent = DuelingDQNAgent(obs_dim=99, num_actions=52)
    agent.load_checkpoint(checkpoint_path)
    env = ExerciseSelectionEnv(max_steps=25)

    # 1. Masked policy
    def masked_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        m = inf.get("action_mask")
        if m is None: m = e.get_action_mask()
        return agent.select_action(o, action_mask=m, deterministic=True)

    # 2. Unmasked / Unconstrained policy
    def unmasked_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
        # Pass None so agent selects purely based on maximum argmax Q(s, a) without prerequisite gating
        return agent.select_action(o, action_mask=None, deterministic=True)

    res_masked = evaluate_policy_on_episodes("prereq_masked", masked_fn, env, seeds=eval_seeds, archetypes=archetypes)
    res_unmasked = evaluate_policy_on_episodes("unconstrained", unmasked_fn, env, seeds=eval_seeds, archetypes=archetypes)

    return {
        "prereq_masked": res_masked["overall"],
        "unconstrained": res_unmasked["overall"],
    }


def run_training_seed_sensitivity(
    seeds_to_train: List[int],
    train_episodes: int = 40,
    eval_seeds: Optional[List[int]] = None,
    checkpoint_dir: str = "models/dqn/seeds",
) -> Dict[str, Any]:
    """
    Trains multiple models with different random seeds and evaluates on held-out seeds.
    """
    if eval_seeds is None:
        eval_seeds = [1001, 1002, 1003, 1004, 1005]

    os.makedirs(checkpoint_dir, exist_ok=True)
    archetypes = list(ARCHETYPES.keys())
    results = {}

    for s in seeds_to_train:
        env = ExerciseSelectionEnv(max_steps=25)
        agent = DuelingDQNAgent(
            obs_dim=env.observation_space.shape[0],
            num_actions=env.num_actions,
            hidden_dim=128,
            seed=s,
        )

        for ep in range(1, train_episodes + 1):
            arch = archetypes[(ep - 1) % len(archetypes)]
            obs, info = env.reset(seed=s + ep * 100, options={"archetype": arch})
            done = False
            while not done:
                mask = info.get("action_mask")
                if mask is None: mask = env.get_action_mask()
                action = agent.select_action(obs, action_mask=mask, deterministic=False)
                next_obs, r, term, trunc, next_info = env.step(action)
                agent.total_steps += 1
                agent.decay_epsilon()
                next_mask = next_info.get("action_mask")
                if next_mask is None: next_mask = env.get_action_mask()
                agent.replay_buffer.push(obs, action, r, next_obs, term, trunc, next_mask)
                if ep > 5:
                    agent.train_step()
                obs = next_obs
                info = next_info
                done = term or trunc

        def policy_fn(e: ExerciseSelectionEnv, o: np.ndarray, inf: Dict[str, Any]) -> int:
            m = inf.get("action_mask")
            if m is None: m = e.get_action_mask()
            return agent.select_action(o, action_mask=m, deterministic=True)

        res = evaluate_policy_on_episodes(f"seed_{s}", policy_fn, env, seeds=eval_seeds, archetypes=archetypes)
        results[f"train_seed_{s}"] = res["overall"]

    return results


def run_all_ablations(
    output_path: str = "reports/phase5_ablation_results.json",
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Executes the complete ablation suite and writes results to JSON.
    """
    start_time = time.time()
    if verbose:
        print("=== Running Phase 5 Ablation Studies ===")

    # 1. Double DQN vs Standard DQN
    if verbose:
        print("\n1. Running Double DQN vs Standard DQN Ablation...")
    double_vs_std = run_double_vs_standard_dqn_ablation(train_episodes=40)

    # 2. Reward Component Ablation
    if verbose:
        print("\n2. Running Reward Component Ablation...")
    reward_abl = run_reward_component_ablation()

    # 3. Action Masking Ablation
    if verbose:
        print("\n3. Running Action Masking Ablation...")
    masking_abl = run_masking_ablation()

    # 4. Training Seed Sensitivity
    if verbose:
        print("\n4. Running Training Seed Sensitivity (seeds: [42, 123, 777])...")
    seed_sens = run_training_seed_sensitivity(seeds_to_train=[42, 123, 777], train_episodes=40)

    elapsed = round(time.time() - start_time, 2)

    ablation_payload = {
        "metadata": {
            "title": "Phase 5 Dueling DQN Ablation Studies",
            "elapsed_seconds": elapsed,
            "eval_episodes_per_ablation": 20,
        },
        "ablations": {
            "target_bootstrapping": double_vs_std,
            "reward_components": reward_abl,
            "action_masking": masking_abl,
            "training_seed_sensitivity": seed_sens,
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ablation_payload, f, indent=2)

    if verbose:
        print(f"\n=== Ablations completed in {elapsed}s! Saved to: {output_path} ===")

    return ablation_payload


if __name__ == "__main__":
    run_all_ablations()
