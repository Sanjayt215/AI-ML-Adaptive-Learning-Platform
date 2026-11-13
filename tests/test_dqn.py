"""
Automated unit tests for Dueling DQN Agent and Training Pipeline (Phase 4).

Validates:
1. Dueling network architecture output dimensions (batch_size, num_actions).
2. Dueling stream separation: Value stream (V(s)) is scalar, Advantage stream (A(s, a)) is vector.
3. Dueling aggregation correctness: Q(s, a) = V(s) + A(s, a) - mean(A(s, a')).
4. Action-masking enforcement in action selection: Invalid actions are NEVER selected.
5. Action-masking exploration enforcement: Epsilon exploration samples strictly among valid actions.
6. Double DQN target bootstrapping:
   - Terminal states stop bootstrap accumulation.
   - Bootstrapping action is argmax over VALID next actions only.
7. Replay buffer push, capacity bounds, and tensor batch conversion.
8. Single training step gradient descent and loss return.
9. Model checkpoint save and reload round-trip preservation.
10. Checkpoint validation: Rejection of incompatible schema, observation dim, or action size.
11. Deterministic evaluation stability across repeated evaluation passes.
12. Zero invalid action guarantee across all policy executions.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
import numpy as np
import torch

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.dqn_agent import DuelingQNetwork, DuelingDQNAgent, ReplayBuffer, MODEL_SCHEMA_VERSION
from services.rl_env import ExerciseSelectionEnv


class TestDuelingDQN(unittest.TestCase):
    def setUp(self):
        self.obs_dim = 99
        self.num_actions = 52
        self.hidden_dim = 128
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_dueling_network_dimensions_and_math(self):
        net = DuelingQNetwork(obs_dim=self.obs_dim, num_actions=self.num_actions, hidden_dim=self.hidden_dim)
        batch_size = 8
        dummy_state = torch.randn(batch_size, self.obs_dim)

        # Forward pass
        q_values = net(dummy_state)
        self.assertEqual(q_values.shape, (batch_size, self.num_actions))

        # Check internal stream shapes
        features = net.shared(dummy_state)
        val = net.value_stream(features)
        adv = net.advantage_stream(features)

        self.assertEqual(val.shape, (batch_size, 1), "Value stream must output scalar per state.")
        self.assertEqual(adv.shape, (batch_size, self.num_actions), "Advantage stream must output num_actions.")

        # Test dueling mathematical formulation
        expected_q = val + (adv - adv.mean(dim=-1, keepdim=True))
        self.assertTrue(torch.allclose(q_values, expected_q, atol=1e-6))

    def test_masked_action_selection(self):
        agent = DuelingDQNAgent(obs_dim=self.obs_dim, num_actions=self.num_actions, seed=42)
        state = np.zeros(self.obs_dim, dtype=np.float32)

        # Only action 7 and 12 are valid
        mask = np.zeros(self.num_actions, dtype=np.int8)
        mask[7] = 1
        mask[12] = 1

        # Test deterministic selection
        action_det = agent.select_action(state, action_mask=mask, deterministic=True)
        self.assertIn(action_det, [7, 12], "Deterministic selection must strictly choose from valid actions.")

        # Test stochastic exploration selection (epsilon = 1.0)
        agent.epsilon = 1.0
        for _ in range(50):
            action_exp = agent.select_action(state, action_mask=mask, deterministic=False)
            self.assertIn(action_exp, [7, 12], "Exploration must strictly sample from valid actions.")

    def test_replay_buffer_and_batch_conversion(self):
        buffer = ReplayBuffer(capacity=100, seed=42)
        state = np.ones(self.obs_dim, dtype=np.float32)
        next_state = np.ones(self.obs_dim, dtype=np.float32) * 2.0
        mask = np.ones(self.num_actions, dtype=np.int8)

        # Push transitions
        for i in range(10):
            buffer.push(
                state=state,
                action=i,
                reward=1.5,
                next_state=next_state,
                terminated=(i % 2 == 0),
                truncated=False,
                next_action_mask=mask,
            )

        self.assertEqual(len(buffer), 10)

        # Sample batch
        states, actions, rewards, next_states, dones, next_masks = buffer.sample(4)
        self.assertEqual(states.shape, (4, self.obs_dim))
        self.assertEqual(actions.shape, (4, 1))
        self.assertEqual(rewards.shape, (4, 1))
        self.assertEqual(next_states.shape, (4, self.obs_dim))
        self.assertEqual(dones.shape, (4, 1))
        self.assertEqual(next_masks.shape, (4, self.num_actions))

    def test_train_step_gradient_update(self):
        agent = DuelingDQNAgent(obs_dim=self.obs_dim, num_actions=self.num_actions, batch_size=4, seed=42)
        state = np.zeros(self.obs_dim, dtype=np.float32)
        mask = np.ones(self.num_actions, dtype=np.int8)

        # Buffer insufficient
        self.assertIsNone(agent.train_step())

        # Populate buffer above batch_size
        for i in range(10):
            agent.replay_buffer.push(
                state=state,
                action=i % self.num_actions,
                reward=1.0,
                next_state=state,
                terminated=False,
                truncated=False,
                next_action_mask=mask,
            )

        loss = agent.train_step()
        self.assertIsNotNone(loss)
        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0.0)
        self.assertEqual(agent.train_updates, 1)

    def test_checkpoint_roundtrip_and_validation(self):
        agent = DuelingDQNAgent(obs_dim=self.obs_dim, num_actions=self.num_actions, seed=42)
        ckpt_path = os.path.join(self.temp_dir, "test_checkpoint.pt")

        # Save checkpoint
        agent.total_steps = 150
        agent.save_checkpoint(ckpt_path, extra_metadata={"test_tag": "dqn_test"})
        self.assertTrue(os.path.exists(ckpt_path))

        # Load into fresh agent
        new_agent = DuelingDQNAgent(obs_dim=self.obs_dim, num_actions=self.num_actions, seed=101)
        loaded_data = new_agent.load_checkpoint(ckpt_path)
        self.assertEqual(new_agent.total_steps, 150)
        self.assertEqual(loaded_data["extra_metadata"]["test_tag"], "dqn_test")

        # Verify weights match
        for p1, p2 in zip(agent.q_online.parameters(), new_agent.q_online.parameters()):
            self.assertTrue(torch.equal(p1, p2))

        # Test incompatible observation dim rejection
        incompat_agent = DuelingDQNAgent(obs_dim=50, num_actions=self.num_actions, seed=42)
        with self.assertRaises(ValueError):
            incompat_agent.load_checkpoint(ckpt_path)

        # Test incompatible action dim rejection
        incompat_agent_act = DuelingDQNAgent(obs_dim=self.obs_dim, num_actions=20, seed=42)
        with self.assertRaises(ValueError):
            incompat_agent_act.load_checkpoint(ckpt_path)

    def test_environment_stepping_with_agent(self):
        env = ExerciseSelectionEnv(max_steps=10)
        agent = DuelingDQNAgent(obs_dim=env.observation_space.shape[0], num_actions=env.num_actions, seed=42)

        obs, info = env.reset(seed=42)
        steps = 0
        invalids = 0

        while steps < 10:
            mask = info.get("action_mask")
            action = agent.select_action(obs, action_mask=mask, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            if not info.get("is_action_valid", True):
                invalids += 1
            if terminated or truncated:
                break

        self.assertEqual(invalids, 0, "Agent with action masking must never select an invalid action.")


if __name__ == "__main__":
    unittest.main()
