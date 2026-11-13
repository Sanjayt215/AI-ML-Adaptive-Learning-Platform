"""
Linear Upper Confidence Bound (LinUCB) Contextual Bandit Policy.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Provides a competitive, sample-efficient reinforcement learning baseline:
- Operates on observable continuous student state features x in R^d.
- Enforces prerequisite action masking (ineligible actions masked out).
- Updates ridge regression parameters online after each observed reward.
- Balances exploitation (predicted reward) with exploration (uncertainty bonus).
"""

from __future__ import annotations

import math
import numpy as np
from typing import Any, Dict, List, Optional, Tuple


class LinUCBBanditPolicy:
    """
    LinUCB Contextual Bandit with Disjoint Linear Models per Action.
    Paper: Li et al. (2010), 'A Contextual-Bandit Approach to Personalized News Recommendation'.
    """

    def __init__(
        self,
        num_actions: int = 52,
        context_dim: int = 32,
        alpha: float = 0.5,
        ridge_lambda: float = 1.0,
    ):
        self.num_actions = num_actions
        self.context_dim = context_dim
        self.alpha = alpha
        self.ridge_lambda = ridge_lambda

        # Maintain A_a = D_a^T D_a + I_d and b_a = D_a^T c_a for each action
        self.A = [np.eye(self.context_dim, dtype=np.float32) * self.ridge_lambda for _ in range(num_actions)]
        self.b = [np.zeros((self.context_dim, 1), dtype=np.float32) for _ in range(num_actions)]
        self.A_inv = [np.eye(self.context_dim, dtype=np.float32) / self.ridge_lambda for _ in range(num_actions)]

    def _extract_context(self, obs: np.ndarray) -> np.ndarray:
        """Extracts and normalizes context feature vector from observation."""
        if len(obs) >= self.context_dim:
            ctx = obs[:self.context_dim].copy()
        else:
            ctx = np.pad(obs, (0, self.context_dim - len(obs)))

        ctx = ctx.reshape(-1, 1).astype(np.float32)
        # Add bias / intercept term
        norm = np.linalg.norm(ctx)
        if norm > 1e-4:
            ctx = ctx / norm
        return ctx

    def select_action(
        self,
        obs: np.ndarray,
        action_mask: np.ndarray,
        deterministic: bool = False,
    ) -> int:
        """Selects action using UCB index over prerequisite-valid actions."""
        ctx = self._extract_context(obs)
        valid_indices = [i for i in range(self.num_actions) if action_mask[i]]

        if not valid_indices:
            return 0

        best_action = valid_indices[0]
        max_ucb = -1e9

        for a in valid_indices:
            # theta_a = A_a^{-1} b_a
            theta_a = np.dot(self.A_inv[a], self.b[a])
            mean_pred = float(np.dot(theta_a.T, ctx)[0, 0])

            if deterministic:
                score = mean_pred
            else:
                var = float(np.dot(np.dot(ctx.T, self.A_inv[a]), ctx)[0, 0])
                ucb_bonus = self.alpha * math.sqrt(max(0.0, var))
                score = mean_pred + ucb_bonus

            if score > max_ucb:
                max_ucb = score
                best_action = a

        return best_action

    def update(self, obs: np.ndarray, action: int, reward: float) -> None:
        """Performs Sherman-Morrison rank-1 update of ridge regression matrices."""
        if not (0 <= action < self.num_actions):
            return

        ctx = self._extract_context(obs)
        self.A[action] += np.dot(ctx, ctx.T)
        self.b[action] += reward * ctx

        # Sherman-Morrison update for inverse matrix A^{-1}
        A_inv = self.A_inv[action]
        numerator = np.dot(np.dot(A_inv, ctx), np.dot(ctx.T, A_inv))
        denominator = 1.0 + float(np.dot(np.dot(ctx.T, A_inv), ctx)[0, 0])
        self.A_inv[action] = A_inv - (numerator / max(1e-6, denominator))
