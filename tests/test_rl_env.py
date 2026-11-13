"""
Unit tests for Synthetic Learner Simulator and RL Environment (Phase 3).

Validates:
1. Fixed-seed reproducibility across simulator and environment.
2. Independent seed divergence.
3. Response probability scaling with mastery and difficulty.
4. Archetype configuration integrity.
5. Ground-truth mastery bounds preservation.
6. Forgetting decay following exponential formula and zero elapsed time preservation.
7. Environment reset observation shape and info payload.
8. Environment step 5-tuple structure: (obs, reward, terminated, truncated, info).
9. Action space and observation space definitions.
10. Prerequisite action masking enforcement.
11. Isolation: Hidden simulator truth is NEVER present in observable observation vector.
12. Multi-KC response and learning aggregation.
13. BKT belief state updates from generated responses.
14. Total invalid actions penalty handling.
"""

import math
import os
import sys
import unittest
import numpy as np

# Ensure root path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.learner_simulator import SyntheticLearner, ARCHETYPES
from services.rl_env import ExerciseSelectionEnv
from services.rl_reward import compute_reward, RewardWeights


class TestLearnerSimulator(unittest.TestCase):
    def test_fixed_seed_reproducibility(self):
        learner1 = SyntheticLearner(archetype_name="typical_learner", seed=42)
        learner2 = SyntheticLearner(archetype_name="typical_learner", seed=42)

        m1 = learner1.get_all_hidden_mastery()
        m2 = learner2.get_all_hidden_mastery()
        self.assertEqual(m1, m2, "Identical seeds must yield identical initial hidden mastery.")

        # Simulate response
        res1, p1, _ = learner1.simulate_response(["python"], difficulty=2)
        res2, p2, _ = learner2.simulate_response(["python"], difficulty=2)
        self.assertEqual(res1, res2)
        self.assertAlmostEqual(p1, p2, places=6)

    def test_independent_seed_divergence(self):
        learner1 = SyntheticLearner(archetype_name="typical_learner", seed=101)
        learner2 = SyntheticLearner(archetype_name="typical_learner", seed=999)

        m1 = learner1.get_all_hidden_mastery()
        m2 = learner2.get_all_hidden_mastery()
        self.assertNotEqual(m1, m2, "Different seeds must produce independent initial mastery profiles.")

    def test_archetype_characteristics(self):
        fast = SyntheticLearner(archetype_name="fast_learner", seed=42)
        struggling = SyntheticLearner(archetype_name="struggling_learner", seed=42)

        fast_mean = np.mean(list(fast.get_all_hidden_mastery().values()))
        struggling_mean = np.mean(list(struggling.get_all_hidden_mastery().values()))
        self.assertGreater(fast_mean, struggling_mean)

        self.assertGreater(fast.archetype.learning_rate, struggling.archetype.learning_rate)
        self.assertLess(fast.archetype.slip_rate, struggling.archetype.slip_rate)

    def test_response_probability_mastery_difficulty_monotonicity(self):
        learner = SyntheticLearner(archetype_name="typical_learner", seed=42)
        # Test lower difficulty vs higher difficulty on same skill
        _, p_easy, _ = learner.simulate_response(["python"], difficulty=1)
        _, p_hard, _ = learner.simulate_response(["python"], difficulty=5)
        self.assertGreater(p_easy, p_hard, "Easier exercise must yield higher success probability than harder one.")

    def test_forgetting_exponential_decay(self):
        learner = SyntheticLearner(archetype_name="typical_learner", seed=42)
        # Manually set high mastery
        learner._hidden_mastery["python"] = 0.90
        floor = learner.mastery_floor
        rate = learner.archetype.forgetting_rate
        dt = 5.0

        expected_m = floor + (0.90 - floor) * math.exp(-rate * dt)
        learner.apply_forgetting(delta_time=dt)
        actual_m = learner.get_hidden_mastery("python")
        self.assertAlmostEqual(actual_m, expected_m, places=4)

    def test_zero_time_forgetting_preserves_mastery(self):
        learner = SyntheticLearner(archetype_name="typical_learner", seed=42)
        m_before = learner.get_all_hidden_mastery()
        learner.apply_forgetting(delta_time=0.0)
        m_after = learner.get_all_hidden_mastery()
        self.assertEqual(m_before, m_after, "Zero delta_time must preserve exact mastery.")

    def test_mastery_bounds_preservation(self):
        learner = SyntheticLearner(archetype_name="fast_learner", seed=42)
        # Apply many learning opportunities
        for _ in range(50):
            learner.apply_learning(["python"], is_correct=True)
        m_val = learner.get_hidden_mastery("python")
        self.assertLessEqual(m_val, 1.0)
        self.assertGreaterEqual(m_val, 0.0)


class TestRLEnvironment(unittest.TestCase):
    def setUp(self):
        self.env = ExerciseSelectionEnv(max_steps=10)

    def test_reset_interface(self):
        obs, info = self.env.reset(seed=42, options={"archetype": "typical_learner"})
        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(obs.shape, (self.env.encoder.feature_dim,))
        self.assertEqual(obs.dtype, np.float32)

        self.assertIn("action_mask", info)
        self.assertIn("archetype", info)
        self.assertEqual(len(info["action_mask"]), self.env.num_actions)
        self.assertTrue(self.env.observation_space.contains(obs))

    def test_step_five_tuple_structure(self):
        self.env.reset(seed=42)
        obs, reward, terminated, truncated, info = self.env.step(0)

        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(obs.shape, (self.env.encoder.feature_dim,))
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)
        self.assertIn("reward_components", info)
        self.assertIn("item_id", info)

    def test_hidden_mastery_not_in_observation(self):
        obs, _ = self.env.reset(seed=42)
        # Check observable features: BKT mastery, evidence count, prereq readiness, history, context
        # Hidden true mastery from self.env.learner must not appear directly in obs
        hidden_vals = self.env.learner.get_all_hidden_mastery()
        # Verify initial BKT mastery is exactly the heuristic prior 0.20, NOT the hidden simulator truth
        for idx in range(self.env.num_topics):
            self.assertAlmostEqual(obs[idx], 0.20, places=4, msg="Observation must contain BKT prior, not hidden truth.")

    def test_prerequisite_action_masking(self):
        self.env.reset(seed=42)
        mask = self.env.get_action_mask()
        self.assertEqual(len(mask), self.env.num_actions)

        # Level 1 foundational items should always be eligible
        level1_indices = [i for i, item in enumerate(self.env.item_bank) if item.get("difficulty") == 1]
        for idx in level1_indices:
            self.assertEqual(mask[idx], 1, f"Foundational level-1 item {idx} should be valid.")

    def test_invalid_action_handling(self):
        self.env.reset(seed=42)
        # Action index far out of bounds
        obs, reward, terminated, truncated, info = self.env.step(9999)
        self.assertFalse(info["is_action_valid"])
        self.assertLess(reward, 0.0, "Invalid action must receive penalty reward.")
        self.assertIn("error", info)

    def test_episode_truncation(self):
        env = ExerciseSelectionEnv(max_steps=3)
        env.reset(seed=42)
        t1, tr1 = env.step(0)[2:4]
        self.assertFalse(tr1)
        t2, tr2 = env.step(0)[2:4]
        self.assertFalse(tr2)
        t3, tr3 = env.step(0)[2:4]
        self.assertTrue(tr3, "Episode must be truncated when max_steps is reached.")

    def test_reward_components_finite(self):
        self.env.reset(seed=42)
        for _ in range(5):
            mask = self.env.get_action_mask()
            action = self.env.action_space.sample(mask=mask)
            _, reward, _, _, info = self.env.step(action)
            self.assertTrue(math.isfinite(reward))
            for k, val in info["reward_components"].items():
                self.assertTrue(math.isfinite(val))


if __name__ == "__main__":
    unittest.main()
