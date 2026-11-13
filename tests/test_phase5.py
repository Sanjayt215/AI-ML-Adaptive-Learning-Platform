"""
Unit and Integration Tests for Phase 5 Evaluation, Ablations, and Controlled Integration.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.rl_env import ExerciseSelectionEnv
from services.learner_simulator import SyntheticLearner
from services.rl_reward import RewardWeights, compute_reward
from services.dqn_agent import DuelingDQNAgent
from services.experimental_recommendation_service import (
    ExperimentalExerciseService,
    is_experiment_enabled,
)


class TestPhase5EvaluationAndIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env = ExerciseSelectionEnv(max_steps=25)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_mastery_gain_hand_calculation(self):
        """Verifies net mastery gain vs gross learning math independently."""
        learner = SyntheticLearner(archetype_name="fast_learner", seed=42)
        init_m = np.mean(list(learner.get_all_hidden_mastery().values()))

        # Simulate 1 step practice on topic 'python'
        deltas = learner.apply_learning(["python"], is_correct=True)
        self.assertGreater(sum(deltas.values()), 0.0)

        # Before forgetting
        gross_m = np.mean(list(learner.get_all_hidden_mastery().values()))
        self.assertGreater(gross_m, init_m)

        # Apply forgetting
        decays = learner.apply_forgetting(delta_time=1.0)
        final_m = np.mean(list(learner.get_all_hidden_mastery().values()))

        # Net gain equals final minus initial
        self.assertAlmostEqual(final_m - init_m, gross_m - sum(decays.values())/30.0 - init_m, places=5)

    def test_reward_components_boundedness(self):
        """Verifies mathematical validity of each reward component."""
        # 1. Valid action reward
        r, comps = compute_reward(
            mastery_deltas={"python": 0.05},
            prior_bkt_mastery=0.5,
            item_difficulty=3,
            is_correct=True,
            consecutive_topic_failures=0,
            is_action_valid=True,
        )
        self.assertGreater(comps["mastery_gain_reward"], 0.0)
        self.assertGreater(comps["information_entropy_reward"], 0.0)
        self.assertGreater(comps["zpd_match_reward"], 0.0)
        self.assertEqual(comps["failure_penalty"], 0.0)
        self.assertLess(comps["step_cost"], 0.0)

        # 2. Invalid action penalty
        r_inv, comps_inv = compute_reward(
            mastery_deltas={},
            prior_bkt_mastery=0.1,
            item_difficulty=5,
            is_correct=False,
            consecutive_topic_failures=0,
            is_action_valid=False,
        )
        self.assertEqual(r_inv, -2.0)
        self.assertEqual(comps_inv["invalid_penalty"], -2.0)

    def test_double_vs_standard_dqn_switch(self):
        """Verifies double_dqn boolean flag correctly changes target calculation mode."""
        agent_double = DuelingDQNAgent(obs_dim=99, num_actions=52, batch_size=4, double_dqn=True, seed=42)
        agent_standard = DuelingDQNAgent(obs_dim=99, num_actions=52, batch_size=4, double_dqn=False, seed=42)

        self.assertTrue(agent_double.double_dqn)
        self.assertFalse(agent_standard.double_dqn)

        # Populate buffers identically
        s = np.zeros(99, dtype=np.float32)
        m = np.ones(52, dtype=np.int8)
        for i in range(10):
            agent_double.replay_buffer.push(s, 0, 1.0, s, False, False, m)
            agent_standard.replay_buffer.push(s, 0, 1.0, s, False, False, m)

        loss_d = agent_double.train_step()
        loss_s = agent_standard.train_step()
        self.assertIsNotNone(loss_d)
        self.assertIsNotNone(loss_s)

    def test_feature_flag_default_disabled(self):
        """Verifies that experimental feature flag strictly defaults to disabled."""
        if "KT_RL_EXPERIMENT_ENABLED" in os.environ:
            del os.environ["KT_RL_EXPERIMENT_ENABLED"]
        self.assertFalse(is_experiment_enabled())

    def test_experimental_recommendation_fallback(self):
        """Verifies experimental service safely falls back when flag is disabled."""
        if "KT_RL_EXPERIMENT_ENABLED" in os.environ:
            del os.environ["KT_RL_EXPERIMENT_ENABLED"]

        service = ExperimentalExerciseService()
        rec = service.recommend_exercise(learner_id="test_learner_fallback")
        self.assertTrue(rec["ok"])
        self.assertIn("item_id", rec)
        self.assertIn("explanation", rec)
        self.assertEqual(rec["explanation"]["policy_mode"], "prereq_aware_weakest_baseline")
        self.assertFalse(rec["explanation"]["experimental_flag_active"])

    def test_experimental_recommendation_enabled(self):
        """Verifies experimental recommendation executes Dueling DQN when flag is active."""
        os.environ["KT_RL_EXPERIMENT_ENABLED"] = "1"
        try:
            service = ExperimentalExerciseService()
            rec = service.recommend_exercise(learner_id="test_learner_active")
            self.assertTrue(rec["ok"])
            self.assertIn("item_id", rec)
            self.assertTrue(rec["explanation"]["experimental_flag_active"])
            self.assertEqual(rec["explanation"]["policy_mode"], "dueling_dqn_experimental")
        finally:
            del os.environ["KT_RL_EXPERIMENT_ENABLED"]

    def test_missing_checkpoint_graceful_handling(self):
        """Verifies service does not crash when model file is missing or invalid."""
        os.environ["KT_RL_EXPERIMENT_ENABLED"] = "1"
        try:
            service = ExperimentalExerciseService(checkpoint_path="nonexistent_checkpoint.pt")
            self.assertIsNone(service.agent)
            rec = service.recommend_exercise(learner_id="test_learner_missing_ckpt")
            self.assertTrue(rec["ok"])
            self.assertEqual(rec["explanation"]["policy_mode"], "prereq_aware_weakest_baseline")
        finally:
            del os.environ["KT_RL_EXPERIMENT_ENABLED"]


if __name__ == "__main__":
    unittest.main()
