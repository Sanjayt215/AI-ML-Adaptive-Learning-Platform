"""
Automated unit tests for Unified Adaptive Recommendation Service (Phase D).
Tests:
1. Forgetting-aware retention modeling over elapsed days.
2. Confidence- and uncertainty-aware posterior entropy calculation.
3. Frustration-risk detection from consecutive errors and remedial action.
4. Prerequisite-constrained action masking across all recommendation strategies.
5. Composite adaptive strategy scoring and pedagogical rationale generation.
6. Safe handling of disabled experimental DQN mode with transparent baseline fallback.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.adaptive_recommender import UnifiedAdaptiveRecommender, is_experimental_dqn_enabled
from services.bkt_service import initialize_kc_state
from resources import TOPIC_CATALOG


class TestAdaptiveRecommender(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recommender = UnifiedAdaptiveRecommender()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_prerequisite_action_masking(self):
        """Validates prerequisite locking when prerequisite topic mastery is low."""
        bkt_map = {t: initialize_kc_state(t).to_dict() for t in TOPIC_CATALOG}
        # Set 'python' mastery to 0.10 (below 0.50 threshold)
        bkt_map["python"]["mastery_probability"] = 0.10

        mask = self.recommender.compute_prerequisite_mask(bkt_map, threshold=0.50)
        # Topics that require python as prerequisite must be locked (mask == 0)
        for idx, item in enumerate(self.recommender.item_bank):
            topic = item.get("topic")
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            if "python" in prereqs:
                self.assertEqual(mask[idx], 0, f"Item {item['item_id']} requiring unmastered prerequisite 'python' must be locked.")

    def test_retention_decay_calculation(self):
        """Validates longitudinal forgetting decay formula."""
        now = datetime.now(timezone.utc)
        ten_days_ago = (now - timedelta(days=10)).isoformat()

        bkt_map = {"python": {"mastery_probability": 0.80, "observation_count": 5}}
        ts_map = {"python": ten_days_ago}

        retention = self.recommender.estimate_retention(bkt_map, ts_map, reference_time=now)
        py_ret = retention["python"]

        self.assertLess(py_ret["predicted_retention"], 0.80, "Predicted retention must decay below initial mastery.")
        self.assertGreater(py_ret["decay_amount"], 0.05, "Decay amount over 10 days must be non-zero.")
        self.assertIn(py_ret["retention_status"], ["decaying", "needs_revision"])

    def test_uncertainty_and_confidence(self):
        """Validates Shannon entropy and evidence classification."""
        bkt_map = {
            "python": {"mastery_probability": 0.50, "observation_count": 1},  # Maximum uncertainty
            "clustering": {"mastery_probability": 0.95, "observation_count": 10},  # Low uncertainty, solid evidence
        }
        unc = self.recommender.estimate_uncertainty_and_confidence(bkt_map)

        self.assertTrue(unc["python"]["is_uncertain"])
        self.assertAlmostEqual(unc["python"]["posterior_entropy"], 1.0, places=1)
        self.assertEqual(unc["python"]["evidence_quality"], "limited")

        self.assertFalse(unc["clustering"]["is_uncertain"])
        self.assertEqual(unc["clustering"]["evidence_quality"], "solid")

    def test_frustration_risk_detection(self):
        """Validates disengagement risk detection and remedial response."""
        # 3 consecutive failures on python
        events = [
            {"topic": "python", "is_correct": False},
            {"topic": "python", "is_correct": False},
            {"topic": "python", "is_correct": False},
        ]
        frust = self.recommender.estimate_frustration_risk(events)
        self.assertTrue(frust["is_frustrated"])
        self.assertEqual(frust["consecutive_failures"], 3)
        self.assertIn("python", frust["troubled_topics"])
        self.assertIn(frust["recommended_action"], ["remedial_support", "lower_difficulty"])

    def test_composite_recommendation_structure(self):
        """Verifies structured recommendation output and pedagogical explanation."""
        rec = self.recommender.recommend(learner_id="test_learner_comp", strategy="composite_adaptive")
        self.assertTrue(rec["ok"])
        self.assertIn("item_id", rec)
        self.assertIn("explanation", rec)
        self.assertIn("diagnostics", rec)
        self.assertTrue(rec["prerequisites_valid"])
        self.assertGreater(len(rec["explanation"]["pedagogical_rationale"]), 10)

    def test_experimental_dqn_flag_safety(self):
        """Verifies experimental flag defaults to disabled and falls back gracefully."""
        if "KT_RL_EXPERIMENT_ENABLED" in os.environ:
            del os.environ["KT_RL_EXPERIMENT_ENABLED"]

        self.assertFalse(is_experimental_dqn_enabled())
        rec = self.recommender.recommend(learner_id="test_learner_dqn", strategy="experimental_dqn")
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["strategy"], "prereq_aware_weakest_baseline")
        self.assertFalse(rec["explanation"]["experimental_mode"])


if __name__ == "__main__":
    unittest.main()
