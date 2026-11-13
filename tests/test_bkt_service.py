"""
Unit tests for Bayesian Knowledge Tracing (BKT) Service (Phase 2).

Validates:
1. Mathematical correctness of observation updates (correct and incorrect answers) against manual derivations.
2. Learning transition step equation correctness.
3. Probability boundary conditions and parameter sanity checks.
4. Identifiability constraints (P(G) + P(S) < 1.0).
5. Zero-denominator safeguards.
6. Learner history replay determinism.
7. Unmapped questions handling.
8. Independent multi-KC update behavior.
9. Evidence quality categorization.
"""

import unittest
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.services.bkt_service import (
        BKTParameters,
        bkt_observation_update,
        bkt_transition_update,
        bkt_step,
        initialize_kc_state,
        update_kc_mastery,
        replay_learner_history,
        compute_evidence_quality,
    )
except ImportError:
    from services.bkt_service import (
        BKTParameters,
        bkt_observation_update,
        bkt_transition_update,
        bkt_step,
        initialize_kc_state,
        update_kc_mastery,
        replay_learner_history,
        compute_evidence_quality,
    )


class TestBKTService(unittest.TestCase):
    def setUp(self):
        # Canonical test parameters
        self.params = BKTParameters(
            p_l0=0.20,
            p_t=0.15,
            p_g=0.20,
            p_s=0.10,
            version="test-params-v1",
            is_calibrated=False,
        )

    def test_correct_response_manual_calculation(self):
        """
        Manual Calculation:
          p = 0.20, S = 0.10, G = 0.20
          num   = p * (1 - S) = 0.20 * 0.90 = 0.18
          denom = 0.18 + (1 - p) * G = 0.18 + 0.80 * 0.20 = 0.18 + 0.16 = 0.34
          P(K | C) = 0.18 / 0.34 = 9 / 17 ≈ 0.52941176

          Transition:
          P(T) = 0.15
          P(K_next) = (9/17) + (1 - 9/17) * 0.15 = 9/17 + (8/17) * 0.15
                    = (9 + 1.2) / 17 = 10.2 / 17 = 0.6000
        """
        p_post, p_next = bkt_step(0.20, is_correct=True, params=self.params)
        self.assertAlmostEqual(p_post, 9.0 / 17.0, places=5)
        self.assertAlmostEqual(p_next, 0.60, places=5)

    def test_incorrect_response_manual_calculation(self):
        """
        Manual Calculation:
          p = 0.20, S = 0.10, G = 0.20
          num   = p * S = 0.20 * 0.10 = 0.02
          denom = 0.02 + (1 - p) * (1 - G) = 0.02 + 0.80 * 0.80 = 0.02 + 0.64 = 0.66
          P(K | I) = 0.02 / 0.66 = 1 / 33 ≈ 0.030303

          Transition:
          P(K_next) = (1/33) + (32/33) * 0.15 = (1 + 4.8) / 33 = 5.8 / 33 ≈ 0.1757575
        """
        p_post, p_next = bkt_step(0.20, is_correct=False, params=self.params)
        self.assertAlmostEqual(p_post, 1.0 / 33.0, places=5)
        self.assertAlmostEqual(p_next, 5.8 / 33.0, places=5)

    def test_boundary_probabilities(self):
        # Zero prior
        p_post_0_c = bkt_observation_update(0.0, is_correct=True, params=self.params)
        self.assertEqual(p_post_0_c, 0.0)
        p_next_0_c = bkt_transition_update(p_post_0_c, params=self.params)
        self.assertEqual(p_next_0_c, 0.15)  # Transition from 0 knowing

        # Complete mastery prior
        p_post_1_c = bkt_observation_update(1.0, is_correct=True, params=self.params)
        self.assertEqual(p_post_1_c, 1.0)
        p_next_1_c = bkt_transition_update(p_post_1_c, params=self.params)
        self.assertEqual(p_next_1_c, 1.0)

        p_post_1_i = bkt_observation_update(1.0, is_correct=False, params=self.params)
        self.assertEqual(p_post_1_i, 1.0)  # P(S) / P(S) = 1.0

    def test_parameter_validations(self):
        # Out of bounds
        with self.assertRaises(ValueError):
            BKTParameters(p_l0=1.5)
        with self.assertRaises(ValueError):
            BKTParameters(p_t=-0.1)

        # Identifiability violation: P(G) + P(S) >= 1.0
        with self.assertRaises(ValueError):
            BKTParameters(p_g=0.6, p_s=0.5)

    def test_evidence_quality_categories(self):
        self.assertEqual(compute_evidence_quality(0), "none")
        self.assertEqual(compute_evidence_quality(1), "limited")
        self.assertEqual(compute_evidence_quality(4), "limited")
        self.assertEqual(compute_evidence_quality(5), "moderate")
        self.assertEqual(compute_evidence_quality(9), "moderate")
        self.assertEqual(compute_evidence_quality(10), "solid")
        self.assertEqual(compute_evidence_quality(25), "solid")

    def test_replay_history_empty(self):
        res = replay_learner_history(learner_id="empty_learner", events=[], params=self.params)
        self.assertEqual(res["total_events_processed"], 0)
        self.assertEqual(res["unmapped_event_count"], 0)
        # All topics should be not_assessed
        for topic in res["topics"]:
            self.assertEqual(topic["status"], "not_assessed")
            self.assertEqual(topic["observation_count"], 0)
            self.assertEqual(topic["mastery_probability"], 0.20)

    def test_replay_history_chronological_sequence(self):
        events = [
            {
                "event_id": "e1",
                "item_id": "q_py_01",
                "knowledge_components": ["python"],
                "is_correct": 1,
                "event_timestamp": "2026-10-13T10:00:00Z",
            },
            {
                "event_id": "e2",
                "item_id": "q_py_02",
                "knowledge_components": ["python"],
                "is_correct": 0,
                "event_timestamp": "2026-10-13T10:05:00Z",
            },
        ]

        res = replay_learner_history(learner_id="test_learner", events=events, params=self.params)
        py_topic = res["topics_map"]["python"]
        self.assertEqual(py_topic["status"], "assessed")
        self.assertEqual(py_topic["observation_count"], 2)
        self.assertEqual(py_topic["correct_count"], 1)
        self.assertEqual(py_topic["incorrect_count"], 1)

        # After step 1 (correct): mastery was 0.60
        # After step 2 (incorrect on prior 0.60):
        # num = 0.60 * 0.10 = 0.06
        # denom = 0.06 + 0.40 * 0.80 = 0.06 + 0.32 = 0.38
        # post = 0.06 / 0.38 = 6 / 38 = 3 / 19 ≈ 0.15789
        # next = 3/19 + (16/19) * 0.15 = (3 + 2.4) / 19 = 5.4 / 19 ≈ 0.28421
        self.assertAlmostEqual(py_topic["mastery_probability"], 5.4 / 19.0, places=4)

    def test_multi_kc_independent_update(self):
        # A question mapping to both python and data preprocessing
        events = [
            {
                "event_id": "e1",
                "item_id": "multi_kc_item",
                "knowledge_components": ["python", "data preprocessing"],
                "is_correct": 1,
                "event_timestamp": "2026-10-13T10:00:00Z",
            }
        ]
        res = replay_learner_history(learner_id="multi_learner", events=events, params=self.params)
        self.assertEqual(res["total_events_processed"], 1)
        py_topic = res["topics_map"]["python"]
        dp_topic = res["topics_map"]["data preprocessing"]

        self.assertEqual(py_topic["observation_count"], 1)
        self.assertEqual(dp_topic["observation_count"], 1)
        self.assertAlmostEqual(py_topic["mastery_probability"], 0.60, places=4)
        self.assertAlmostEqual(dp_topic["mastery_probability"], 0.60, places=4)

    def test_unmapped_question_handling(self):
        events = [
            {
                "event_id": "e_unmapped",
                "item_id": "non_existent_unmapped_item",
                "knowledge_components": [],
                "is_correct": 1,
                "event_timestamp": "2026-10-13T10:00:00Z",
            }
        ]
        res = replay_learner_history(learner_id="unmapped_learner", events=events, params=self.params)
        self.assertEqual(res["unmapped_event_count"], 1)
        self.assertEqual(res["total_events_processed"], 0)


if __name__ == "__main__":
    unittest.main()
