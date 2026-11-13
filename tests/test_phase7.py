"""
Unit and Integration Tests for Phase 7 RL Improvements & Diagnostics.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.
"""

import math
import os
import unittest
import numpy as np
from datetime import datetime, timezone, timedelta

from services.adaptive_recommender import UnifiedAdaptiveRecommender
from services.recovery_controller import DifficultyRecoveryController, ControllerState
from services.contextual_bandit import LinUCBBanditPolicy
from services.adaptive_exploration import AdaptiveExplorationController, ExplorationConfig
from services.reward_diagnostics import compute_aligned_reward


class TestPhase7AdvancedRL(unittest.TestCase):
    """Rigorous tests covering Phase 7 components, hysteresis, and edge cases."""

    def setUp(self):
        self.recommender = UnifiedAdaptiveRecommender()
        self.controller = DifficultyRecoveryController(base_difficulty=2)
        self.explorer = AdaptiveExplorationController()
        self.bandit = LinUCBBanditPolicy(num_actions=52, context_dim=32, alpha=0.5)

    def test_forgetting_selection_with_staggered_recency(self):
        """Verifies that non-uniform elapsed practice times differentiate candidate rankings."""
        now = datetime.now(timezone.utc)
        one_day_ago = (now - timedelta(days=1)).isoformat()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        bkt_map = {
            "python": {"mastery_probability": 0.60, "observation_count": 5},
            "data preprocessing": {"mastery_probability": 0.60, "observation_count": 5},
        }
        ts_map = {
            "python": one_day_ago,
            "data preprocessing": thirty_days_ago,
        }

        retention = self.recommender.estimate_retention(bkt_map, ts_map, reference_time=now)
        ret_recent = retention["python"]
        ret_stale = retention["data preprocessing"]

        self.assertGreater(ret_recent["predicted_retention"], ret_stale["predicted_retention"])
        self.assertGreater(ret_stale["decay_amount"], ret_recent["decay_amount"])

    def test_equivalent_candidates_produce_same_selection(self):
        """Verifies that equivalent candidates legitimately produce identical retention estimates."""
        now = datetime.now(timezone.utc)
        bkt_map = {
            "python": {"mastery_probability": 0.20, "observation_count": 0},
            "data preprocessing": {"mastery_probability": 0.20, "observation_count": 0},
        }
        ts_map = {}
        retention = self.recommender.estimate_retention(bkt_map, ts_map, reference_time=now)
        self.assertEqual(retention["python"]["predicted_retention"], retention["data preprocessing"]["predicted_retention"])

    def test_reward_components_boundedness_and_signs(self):
        """Verifies that aligned reward terms operate within finite, expected bounds."""
        r_val, comp = compute_aligned_reward(
            mastery_deltas={"python": 0.15},
            prior_bkt=0.40,
            post_bkt=0.55,
            item_diff=2,
            is_correct=True,
            consec_failures=0,
            is_valid=True,
        )
        self.assertTrue(math.isfinite(r_val))
        self.assertGreater(comp["aligned_mastery"], 0.0)
        self.assertGreaterEqual(comp["aligned_info_reduction"], 0.0)
        self.assertLessEqual(comp["aligned_step_cost"], 0.0)

    def test_entropy_proxy_reward_vs_true_gain(self):
        """Verifies that aligned reward awards zero information gain when entropy does not reduce."""
        # Case where posterior entropy increases (p prior 0.20 -> p post 0.50)
        _, comp = compute_aligned_reward(
            mastery_deltas={"python": 0.0},
            prior_bkt=0.20,
            post_bkt=0.50,
            item_diff=2,
            is_correct=False,
            consec_failures=0,
            is_valid=True,
        )
        # delta_h = max(0, H_prior - H_post) must be zero
        self.assertEqual(comp["aligned_info_reduction"], 0.0)

    def test_delayed_retention_calculation(self):
        """Verifies exponential forgetting decay over a 7-day dormant interval."""
        initial_val = 0.80
        m_floor = self.recommender.mastery_floor
        delay_days = 7.0
        expected = m_floor + (initial_val - m_floor) * math.exp(-self.recommender.forgetting_rate * delay_days)

        now = datetime.now(timezone.utc)
        past_iso = (now - timedelta(days=delay_days)).isoformat()
        bkt_map = {"python": {"mastery_probability": initial_val, "observation_count": 5}}
        ts_map = {"python": past_iso}

        ret = self.recommender.estimate_retention(bkt_map, ts_map, reference_time=now)
        pred = ret["python"]["predicted_retention"]
        self.assertAlmostEqual(pred, round(expected, 4), places=3)
        self.assertGreaterEqual(pred, m_floor)

    def test_adaptive_exploration_prerequisite_safety(self):
        """Verifies that exploration controller NEVER selects an action with action_mask=0."""
        mask = np.zeros(52, dtype=np.int8)
        mask[10] = 1  # Only action 10 is prerequisite-eligible
        mock_items = [{"item_id": f"q_{i}", "difficulty": 1, "knowledge_components": ["python"]} for i in range(52)]

        bkt_map = {"python": {"mastery_probability": 0.50, "attempt_count": 0}}
        chosen_action, meta = self.explorer.select_action(bkt_map, mask, mock_items)
        self.assertEqual(chosen_action, 10)
        self.assertEqual(mask[chosen_action], 1)

    def test_adaptive_exploration_probe_cap(self):
        """Verifies that consecutive probes on the same KC are strictly capped."""
        kc = "loops_iteration"
        self.assertTrue(self.explorer.should_explore(kc, bkt_mastery=0.50, attempt_count=0))

        # Simulate 2 consecutive probes
        self.explorer.consecutive_probes_by_kc[kc] = 2
        # Now probe cap must block further probes
        self.assertFalse(self.explorer.should_explore(kc, bkt_mastery=0.50, attempt_count=0))

    def test_linucb_bandit_masked_action_selection(self):
        """Verifies that LinUCB contextual bandit strictly obeys the action mask."""
        obs = np.random.rand(32).astype(np.float32)
        mask = np.zeros(52, dtype=np.int8)
        mask[5] = 1
        mask[22] = 1

        action = self.bandit.select_action(obs, mask, deterministic=True)
        self.assertIn(action, [5, 22])
        self.assertEqual(mask[action], 1)

    def test_difficulty_controller_hysteresis_step_down(self):
        """Verifies hysteresis: single error does not downgrade difficulty; 2 errors do."""
        self.assertEqual(self.controller.current_difficulty, 2)

        # Single error
        self.controller.record_response(is_correct=False)
        self.assertEqual(self.controller.current_difficulty, 2, "Single error must NOT drop difficulty")

        # Second consecutive error triggers step down
        self.controller.record_response(is_correct=False)
        self.assertEqual(self.controller.current_difficulty, 1, "Two consecutive errors must drop difficulty to 1")

    def test_difficulty_controller_hysteresis_step_up(self):
        """Verifies hysteresis: 2 consecutive correct responses required to step up."""
        self.assertEqual(self.controller.current_difficulty, 2)

        # One correct response
        self.controller.record_response(is_correct=True)
        self.assertEqual(self.controller.current_difficulty, 2)

        # Second consecutive correct response steps up
        self.controller.record_response(is_correct=True)
        self.assertEqual(self.controller.current_difficulty, 3, "Two consecutive correct must increase difficulty to 3")


if __name__ == "__main__":
    unittest.main()
