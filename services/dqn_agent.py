from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


MODEL_SCHEMA_VERSION = "kt_rl_dueling_dqn_v1"


class DuelingQNetwork(nn.Module):
    """
    Dueling Deep Q-Network module separating State-Value V(s) and Advantage A(s, a).
    """

    def __init__(
        self,
        obs_dim: int = 99,
        num_actions: int = 52,
        hidden_dim: int = 128,
        use_layer_norm: bool = True,
    ):
        super().__init__()
        self.obs_dim = obs_dim
        self.num_actions = num_actions
        self.hidden_dim = hidden_dim

        # Shared feature extractor
        if use_layer_norm:
            self.shared = nn.Sequential(
                nn.Linear(obs_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
            )
        else:
            self.shared = nn.Sequential(
                nn.Linear(obs_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )

        # Value stream V(s) -> scalar
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

        # Advantage stream A(s, a) -> num_actions
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_actions),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass computing Q(s, a) = V(s) + (A(s, a) - mean(A(s, a'))).
        """
        features = self.shared(state)
        value = self.value_stream(features)  # (batch_size, 1)
        advantage = self.advantage_stream(features)  # (batch_size, num_actions)

        # Dueling aggregation formula
        q_values = value + (advantage - advantage.mean(dim=-1, keepdim=True))
        return q_values


class ReplayBuffer:
    """
    Uniform Transition Experience Replay Buffer storing action masks.
    """

    def __init__(self, capacity: int = 20000, seed: Optional[int] = None):
        self.capacity = capacity
        self.buffer: List[Dict[str, Any]] = []
        self.position = 0
        self.rng = random.Random(seed)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        terminated: bool,
        truncated: bool,
        next_action_mask: np.ndarray,
    ) -> None:
        """Stores a transition in the buffer."""
        transition = {
            "state": np.asarray(state, dtype=np.float32),
            "action": int(action),
            "reward": float(reward),
            "next_state": np.asarray(next_state, dtype=np.float32),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "next_action_mask": np.asarray(next_action_mask, dtype=np.int8),
        }
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.position] = transition
        self.position = (self.position + 1) % self.capacity

    def sample(
        self, batch_size: int
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Samples a batch and converts components into PyTorch tensors.
        Returns:
            states: (batch_size, obs_dim) float32
            actions: (batch_size, 1) int64
            rewards: (batch_size, 1) float32
            next_states: (batch_size, obs_dim) float32
            dones: (batch_size, 1) float32 (terminated only for Bellman backup)
            next_masks: (batch_size, num_actions) int8
        """
        batch = self.rng.sample(self.buffer, batch_size)

        states = torch.tensor(np.array([t["state"] for t in batch]), dtype=torch.float32)
        actions = torch.tensor([t["action"] for t in batch], dtype=torch.int64).unsqueeze(1)
        rewards = torch.tensor([t["reward"] for t in batch], dtype=torch.float32).unsqueeze(1)
        next_states = torch.tensor(np.array([t["next_state"] for t in batch]), dtype=torch.float32)
        # Note: Under standard RL, bootstrapping continues on truncation but stops on true termination
        dones = torch.tensor([1.0 if t["terminated"] else 0.0 for t in batch], dtype=torch.float32).unsqueeze(1)
        next_masks = torch.tensor(np.array([t["next_action_mask"] for t in batch]), dtype=torch.int8)

        return states, actions, rewards, next_states, dones, next_masks

    def __len__(self) -> int:
        return len(self.buffer)


class DuelingDQNAgent:
    """
    Action-Masked Dueling DQN Agent with Double DQN updates.
    """

    def __init__(
        self,
        obs_dim: int = 99,
        num_actions: int = 52,
        hidden_dim: int = 128,
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay_steps: int = 2500,
        target_update_freq: int = 250,
        buffer_capacity: int = 20000,
        batch_size: int = 64,
        max_grad_norm: float = 1.0,
        double_dqn: bool = True,
        device: str = "cpu",
        seed: Optional[int] = None,
    ):
        self.obs_dim = obs_dim
        self.num_actions = num_actions
        self.hidden_dim = hidden_dim
        self.gamma = gamma
        self.double_dqn = double_dqn
        self.epsilon = epsilon_start
        self.epsilon_start = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay_steps = max(1, epsilon_decay_steps)
        self.target_update_freq = target_update_freq
        self.batch_size = batch_size
        self.max_grad_norm = max_grad_norm
        self.device = torch.device(device)

        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)
            random.seed(seed)

        self.rng = random.Random(seed)

        # Networks
        self.q_online = DuelingQNetwork(obs_dim, num_actions, hidden_dim).to(self.device)
        self.q_target = DuelingQNetwork(obs_dim, num_actions, hidden_dim).to(self.device)
        self.q_target.load_state_dict(self.q_online.state_dict())
        self.q_target.eval()

        self.optimizer = optim.Adam(self.q_online.parameters(), lr=learning_rate)
        self.criterion = nn.SmoothL1Loss()  # Huber loss for gradient stability

        self.replay_buffer = ReplayBuffer(capacity=buffer_capacity, seed=seed)

        self.total_steps = 0
        self.train_updates = 0

    def select_action(
        self,
        state: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        deterministic: bool = False,
    ) -> int:
        """
        Selects an action respecting the prerequisite mask.
        - If deterministic or (random >= epsilon): picks valid argmax Q(s, a).
        - Otherwise (exploration): picks uniformly at random among VALID actions only.
        """
        if action_mask is None:
            valid_actions = list(range(self.num_actions))
        else:
            valid_actions = [i for i, valid in enumerate(action_mask) if valid]
            if not valid_actions:
                valid_actions = list(range(self.num_actions))

        # Exploration branch
        if not deterministic and (self.rng.random() < self.epsilon):
            return self.rng.choice(valid_actions)

        # Exploitation branch
        self.q_online.eval()
        with torch.no_grad():
            s_t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            q_values = self.q_online(s_t).squeeze(0)  # (num_actions,)

            if action_mask is not None:
                mask_t = torch.tensor(action_mask, dtype=torch.bool, device=self.device)
                # Apply large negative bias to invalid actions
                q_values = torch.where(mask_t, q_values, torch.tensor(-1e9, device=self.device))

            best_action = int(torch.argmax(q_values).item())

        return best_action

    def decay_epsilon(self) -> None:
        """Decays epsilon linearly from epsilon_start down to epsilon_min."""
        fraction = min(1.0, self.total_steps / self.epsilon_decay_steps)
        self.epsilon = self.epsilon_start - fraction * (self.epsilon_start - self.epsilon_min)

    def train_step(self) -> Optional[float]:
        """
        Performs one Double DQN gradient update from replay memory.
        Returns loss value as float, or None if buffer size < batch_size.
        """
        if len(self.replay_buffer) < self.batch_size:
            return None

        self.q_online.train()
        states, actions, rewards, next_states, dones, next_masks = self.replay_buffer.sample(self.batch_size)
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        next_masks = next_masks.to(self.device)

        # Current Q estimates for chosen actions
        current_q = self.q_online(states).gather(1, actions)

        # Double DQN vs Standard DQN target calculation:
        with torch.no_grad():
            invalid_mask = (next_masks == 0)
            if self.double_dqn:
                # Double DQN: a* = argmax_{a in valid(s')} Q_online(s', a)
                # Target = r + gamma * (1 - done) * Q_target(s', a*)
                next_q_online = self.q_online(next_states)
                next_q_online_masked = next_q_online.masked_fill(invalid_mask, -1e9)
                best_next_actions = torch.argmax(next_q_online_masked, dim=1, keepdim=True)
                next_q_target = self.q_target(next_states).gather(1, best_next_actions)
            else:
                # Standard DQN: max_{a in valid(s')} Q_target(s', a)
                next_q_target_all = self.q_target(next_states)
                next_q_target_masked = next_q_target_all.masked_fill(invalid_mask, -1e9)
                next_q_target, _ = torch.max(next_q_target_masked, dim=1, keepdim=True)

            expected_q = rewards + (1.0 - dones) * self.gamma * next_q_target

        loss = self.criterion(current_q, expected_q)

        self.optimizer.zero_grad()
        loss.backward()
        if self.max_grad_norm > 0:
            nn.utils.clip_grad_norm_(self.q_online.parameters(), self.max_grad_norm)
        self.optimizer.step()

        self.train_updates += 1

        # Periodic target network sync
        if self.train_updates % self.target_update_freq == 0:
            self.q_target.load_state_dict(self.q_online.state_dict())

        return float(loss.item())

    def save_checkpoint(
        self,
        filepath: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Saves model weights, optimizer, and training metadata to disk.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        checkpoint = {
            "schema_version": MODEL_SCHEMA_VERSION,
            "obs_dim": self.obs_dim,
            "num_actions": self.num_actions,
            "hidden_dim": self.hidden_dim,
            "q_online_state_dict": self.q_online.state_dict(),
            "q_target_state_dict": self.q_target.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon": float(self.epsilon),
            "total_steps": int(self.total_steps),
            "train_updates": int(self.train_updates),
            "extra_metadata": extra_metadata or {},
        }
        torch.save(checkpoint, filepath)
        return checkpoint

    def load_checkpoint(self, filepath: str) -> Dict[str, Any]:
        """
        Loads and validates model checkpoint.
        Raises ValueError if checkpoint metadata is incompatible.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Checkpoint file not found: {filepath}")

        checkpoint = torch.load(filepath, map_location=self.device, weights_only=False)

        schema = checkpoint.get("schema_version")
        if schema != MODEL_SCHEMA_VERSION:
            raise ValueError(f"Incompatible schema version: expected {MODEL_SCHEMA_VERSION}, found {schema}")

        c_obs_dim = checkpoint.get("obs_dim")
        c_num_actions = checkpoint.get("num_actions")
        c_hidden_dim = checkpoint.get("hidden_dim")

        if c_obs_dim != self.obs_dim:
            raise ValueError(f"Observation dim mismatch: expected {self.obs_dim}, found {c_obs_dim}")
        if c_num_actions != self.num_actions:
            raise ValueError(f"Action space size mismatch: expected {self.num_actions}, found {c_num_actions}")
        if c_hidden_dim != self.hidden_dim:
            raise ValueError(f"Hidden dim mismatch: expected {self.hidden_dim}, found {c_hidden_dim}")

        self.q_online.load_state_dict(checkpoint["q_online_state_dict"])
        self.q_target.load_state_dict(checkpoint["q_target_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = float(checkpoint.get("epsilon", self.epsilon_min))
        self.total_steps = int(checkpoint.get("total_steps", 0))
        self.train_updates = int(checkpoint.get("train_updates", 0))

        return checkpoint
