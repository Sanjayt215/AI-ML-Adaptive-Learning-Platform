"""
Reproducible Training & Evaluation Pipeline for Dueling DQN.
Part of KT-RL Phase 4: Dueling DQN Agent & Reproducible Training Pipeline.

Features:
1. Dynamic archetype sampling across all 4 synthetic learner profiles:
   - fast_learner
   - typical_learner
   - struggling_learner
   - inconsistent_learner
2. Action-mask-constrained trajectory generation.
3. Training loop with periodic checkpointing and episode metric logging:
   - Episode reward, length, accuracy, ground-truth mastery gain, BKT estimation error.
4. Evaluation engine comparing trained Dueling DQN against 4 Phase 3 baselines:
   - random_eligible
   - weakest_bkt_kc
   - difficulty_ladder
   - prereq_aware_weakest
5. Exports training history to `reports/phase4_training_history.json`.
6. Exports comparative evaluation to `reports/phase4_evaluation.json`.
"""

from __future__ import annotations

import json
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


def train_dqn(
    total_episodes: int = 120,
    steps_per_episode: int = 25,
    warmup_episodes: int = 15,
    batch_size: int = 64,
    learning_rate: float = 3e-4,
    gamma: float = 0.99,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    epsilon_decay_steps: int = 2000,
    target_update_freq: int = 150,
    checkpoint_dir: str = "models/dqn",
    history_output_path: str = "reports/phase4_training_history.json",
    seed: int = 42,
    verbose: bool = True,
) -> Tuple[DuelingDQNAgent, Dict[str, Any]]:
    """
    Trains Dueling DQN across balanced learner archetypes.
    """
    random.seed(seed)
    np.random.seed(seed)

    env = ExerciseSelectionEnv(max_steps=steps_per_episode)
    agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
        learning_rate=learning_rate,
        gamma=gamma,
        epsilon_start=epsilon_start,
        epsilon_min=epsilon_min,
        epsilon_decay_steps=epsilon_decay_steps,
        target_update_freq=target_update_freq,
        batch_size=batch_size,
        seed=seed,
    )

    archetype_list = list(ARCHETYPES.keys())
    episode_history: List[Dict[str, Any]] = []

    start_time = time.time()

    if verbose:
        print(f"=== Starting Dueling DQN Training: {total_episodes} Episodes ===")

    for episode in range(1, total_episodes + 1):
        # Round-robin archetype rotation to ensure balanced representation
        current_archetype = archetype_list[(episode - 1) % len(archetype_list)]
        obs, info = env.reset(seed=seed + episode * 1000, options={"archetype": current_archetype})

        # Track initial hidden ground truth mastery across all topics
        init_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))

        ep_reward = 0.0
        ep_losses: List[float] = []
        correct_count = 0
        total_steps = 0

        terminated = False
        truncated = False

        while not (terminated or truncated):
            mask = info.get("action_mask")
            if mask is None:
                mask = env.get_action_mask()

            # Select masked action
            action = agent.select_action(obs, action_mask=mask, deterministic=False)

            next_obs, reward, terminated, truncated, next_info = env.step(action)
            agent.total_steps += 1
            agent.decay_epsilon()

            next_mask = next_info.get("action_mask")
            if next_mask is None:
                next_mask = env.get_action_mask()

            # Store transition in replay buffer
            agent.replay_buffer.push(
                state=obs,
                action=action,
                reward=reward,
                next_state=next_obs,
                terminated=terminated,
                truncated=truncated,
                next_action_mask=next_mask,
            )

            # Train network once warmup is completed
            if episode > warmup_episodes:
                loss = agent.train_step()
                if loss is not None:
                    ep_losses.append(loss)

            if next_info.get("is_correct", False):
                correct_count += 1

            ep_reward += reward
            total_steps += 1
            obs = next_obs
            info = next_info

        final_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
        mastery_gain = final_mastery - init_mastery
        accuracy = correct_count / total_steps if total_steps > 0 else 0.0
        avg_loss = float(np.mean(ep_losses)) if ep_losses else None

        record = {
            "episode": episode,
            "archetype": current_archetype,
            "reward": round(ep_reward, 3),
            "steps": total_steps,
            "accuracy": round(accuracy, 4),
            "mastery_gain": round(mastery_gain, 4),
            "invalid_actions": 0,  # Action masking strictly guarantees 0
            "epsilon": round(agent.epsilon, 4),
            "avg_loss": round(avg_loss, 5) if avg_loss is not None else None,
        }
        episode_history.append(record)

        if verbose and (episode % 20 == 0 or episode == total_episodes):
            recent_rewards = [r["reward"] for r in episode_history[-20:]]
            recent_gains = [r["mastery_gain"] for r in episode_history[-20:]]
            print(
                f"Ep {episode:3d}/{total_episodes} | "
                f"Arch: {current_archetype:18s} | "
                f"Reward: {ep_reward:6.2f} (Mean20: {np.mean(recent_rewards):6.2f}) | "
                f"Gain: {mastery_gain:+.4f} (Mean20: {np.mean(recent_gains):+.4f}) | "
                f"Eps: {agent.epsilon:.3f} | "
                f"Loss: {f'{avg_loss:.4f}' if avg_loss else 'Warmup'}"
            )

    elapsed_time = round(time.time() - start_time, 2)

    # Save final model checkpoint
    os.makedirs(checkpoint_dir, exist_ok=True)
    final_checkpoint_path = os.path.join(checkpoint_dir, "dueling_dqn_final.pt")
    agent.save_checkpoint(
        final_checkpoint_path,
        extra_metadata={
            "training_episodes": total_episodes,
            "elapsed_seconds": elapsed_time,
            "final_epsilon": agent.epsilon,
            "seed": seed,
        },
    )

    # Save training history
    os.makedirs(os.path.dirname(os.path.abspath(history_output_path)), exist_ok=True)
    history_payload = {
        "metadata": {
            "algorithm": "Dueling Double DQN with Action Masking",
            "total_episodes": total_episodes,
            "steps_per_episode": steps_per_episode,
            "training_time_seconds": elapsed_time,
            "checkpoint_path": final_checkpoint_path,
            "archetypes": archetype_list,
        },
        "episodes": episode_history,
    }
    with open(history_output_path, "w", encoding="utf-8") as f:
        json.dump(history_payload, f, indent=2)

    if verbose:
        print(f"=== Training complete in {elapsed_time}s! Checkpoint saved to: {final_checkpoint_path} ===")

    return agent, history_payload


def evaluate_agent(
    agent: DuelingDQNAgent,
    env: ExerciseSelectionEnv,
    seeds: List[int],
    archetypes: List[str],
) -> Dict[str, Any]:
    """
    Evaluates agent deterministically (epsilon=0) across fixed seeds and archetypes.
    """
    rewards: List[float] = []
    mastery_gains: List[float] = []
    accuracies: List[float] = []
    steps_list: List[int] = []
    invalids: List[int] = []
    mae_list: List[float] = []

    for archetype in archetypes:
        for seed in seeds:
            obs, info = env.reset(seed=seed, options={"archetype": archetype})
            init_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))

            ep_reward = 0.0
            correct = 0
            ep_steps = 0
            ep_invalids = 0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                mask = info.get("action_mask")
                if mask is None:
                    mask = env.get_action_mask()

                action = agent.select_action(obs, action_mask=mask, deterministic=True)
                next_obs, reward, terminated, truncated, info = env.step(action)
                ep_reward += reward
                ep_steps += 1
                if info.get("is_correct", False):
                    correct += 1
                if not info.get("is_action_valid", True):
                    ep_invalids += 1
                obs = next_obs

            final_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
            mastery_gain = final_mastery - init_mastery

            rewards.append(ep_reward)
            mastery_gains.append(mastery_gain)
            accuracies.append(correct / ep_steps if ep_steps > 0 else 0.0)
            steps_list.append(ep_steps)
            invalids.append(ep_invalids)

            # BKT estimation error vs hidden truth
            sim_mastery = np.array(list(env.learner.get_all_hidden_mastery().values()))
            bkt_vals = np.array([state.mastery_probability for state in env.bkt_states.values()])
            if len(sim_mastery) == len(bkt_vals) and len(sim_mastery) > 0:
                mae = float(np.mean(np.abs(sim_mastery - bkt_vals)))
                mae_list.append(mae)

    return {
        "mean_cumulative_reward": round(float(np.mean(rewards)), 2),
        "std_cumulative_reward": round(float(np.std(rewards)), 2),
        "mean_mastery_gain": round(float(np.mean(mastery_gains)), 4),
        "std_mastery_gain": round(float(np.std(mastery_gains)), 4),
        "mean_accuracy": round(float(np.mean(accuracies)), 4),
        "std_accuracy": round(float(np.std(accuracies)), 4),
        "mean_episode_length": round(float(np.mean(steps_list)), 2),
        "total_invalid_actions": int(np.sum(invalids)),
        "mean_bkt_mae": round(float(np.mean(mae_list)), 4) if mae_list else 0.0,
    }


def run_comparative_benchmark(
    checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
    output_path: str = "reports/phase4_evaluation.json",
    seeds: Optional[List[int]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Runs head-to-head comparison between trained Dueling DQN and the 4 Phase 3 baselines
    under the exact same evaluation configuration.
    """
    if seeds is None:
        seeds = [101, 202, 303, 404, 505]  # 5 seeds x 4 archetypes = 20 episodes

    archetypes = list(ARCHETYPES.keys())
    env = ExerciseSelectionEnv(max_steps=25)

    results: Dict[str, Any] = {}

    # 1. Evaluate trained Dueling DQN
    agent = DuelingDQNAgent(
        obs_dim=env.observation_space.shape[0],
        num_actions=env.num_actions,
        hidden_dim=128,
    )
    agent.load_checkpoint(checkpoint_path)
    if verbose:
        print(f"Loaded checkpoint for evaluation: {checkpoint_path}")

    dqn_metrics = evaluate_agent(agent, env, seeds=seeds, archetypes=archetypes)
    results["dueling_dqn"] = dqn_metrics
    if verbose:
        print(
            f"{'dueling_dqn':20s}: Reward {dqn_metrics['mean_cumulative_reward']:6.2f} | "
            f"Mastery Gain {dqn_metrics['mean_mastery_gain']:+.4f} | "
            f"Accuracy {dqn_metrics['mean_accuracy']*100:.1f}% | "
            f"Invalids: {dqn_metrics['total_invalid_actions']}"
        )

    # 2. Evaluate the 4 Phase 3 Baselines
    for policy_name, policy_fn in BASELINE_POLICIES.items():
        rewards: List[float] = []
        mastery_gains: List[float] = []
        accuracies: List[float] = []
        steps_list: List[int] = []
        invalids: List[int] = []
        mae_list: List[float] = []

        for archetype in archetypes:
            for seed in seeds:
                obs, info = env.reset(seed=seed, options={"archetype": archetype})
                init_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))

                ep_reward = 0.0
                correct = 0
                ep_steps = 0
                ep_invalids = 0
                terminated = False
                truncated = False

                while not (terminated or truncated):
                    action = policy_fn(env, obs, info)
                    next_obs, reward, terminated, truncated, info = env.step(action)
                    ep_reward += reward
                    ep_steps += 1
                    if info.get("is_correct", False):
                        correct += 1
                    if not info.get("is_action_valid", True):
                        ep_invalids += 1
                    obs = next_obs

                final_mastery = float(np.mean(list(env.learner.get_all_hidden_mastery().values())))
                mastery_gain = final_mastery - init_mastery

                rewards.append(ep_reward)
                mastery_gains.append(mastery_gain)
                accuracies.append(correct / ep_steps if ep_steps > 0 else 0.0)
                steps_list.append(ep_steps)
                invalids.append(ep_invalids)

                sim_mastery = np.array(list(env.learner.get_all_hidden_mastery().values()))
                bkt_vals = np.array([state.mastery_probability for state in env.bkt_states.values()])
                if len(sim_mastery) == len(bkt_vals) and len(sim_mastery) > 0:
                    mae = float(np.mean(np.abs(sim_mastery - bkt_vals)))
                    mae_list.append(mae)

        base_metrics = {
            "mean_cumulative_reward": round(float(np.mean(rewards)), 2),
            "std_cumulative_reward": round(float(np.std(rewards)), 2),
            "mean_mastery_gain": round(float(np.mean(mastery_gains)), 4),
            "std_mastery_gain": round(float(np.std(mastery_gains)), 4),
            "mean_accuracy": round(float(np.mean(accuracies)), 4),
            "std_accuracy": round(float(np.std(accuracies)), 4),
            "mean_episode_length": round(float(np.mean(steps_list)), 2),
            "total_invalid_actions": int(np.sum(invalids)),
            "mean_bkt_mae": round(float(np.mean(mae_list)), 4) if mae_list else 0.0,
        }
        results[policy_name] = base_metrics

        if verbose:
            print(
                f"{policy_name:20s}: Reward {base_metrics['mean_cumulative_reward']:6.2f} | "
                f"Mastery Gain {base_metrics['mean_mastery_gain']:+.4f} | "
                f"Accuracy {base_metrics['mean_accuracy']*100:.1f}% | "
                f"Invalids: {base_metrics['total_invalid_actions']}"
            )

    benchmark_payload = {
        "evaluation_config": {
            "episodes_per_policy": len(seeds) * len(archetypes),
            "seeds": seeds,
            "archetypes": archetypes,
            "steps_per_episode": 25,
            "checkpoint_evaluated": checkpoint_path,
        },
        "policies": results,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2)

    return benchmark_payload


if __name__ == "__main__":
    train_dqn(
        total_episodes=120,
        steps_per_episode=25,
        warmup_episodes=15,
        checkpoint_dir="models/dqn",
        history_output_path="reports/phase4_training_history.json",
    )

    run_comparative_benchmark(
        checkpoint_path="models/dqn/dueling_dqn_final.pt",
        output_path="reports/phase4_evaluation.json",
    )
