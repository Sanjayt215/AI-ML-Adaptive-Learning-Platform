"""
Tests for Shared Learner Intelligence Layer.
Part of AutoLearn KT-RL Full Website Transformation.
"""

import unittest
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.services.learner_intelligence import get_unified_learner_intelligence
except ImportError:
    from services.learner_intelligence import get_unified_learner_intelligence


class TestLearnerIntelligence(unittest.TestCase):
    def setUp(self):
        self.learner_id = "test_intelligence_learner_001"

    def test_unified_learner_intelligence_dimensions(self):
        intel = get_unified_learner_intelligence(self.learner_id)
        self.assertTrue(intel["ok"])
        self.assertEqual(intel["learner_id"], self.learner_id)

        # 1. Knowledge State
        self.assertIn("knowledge_state", intel)
        ks = intel["knowledge_state"]
        self.assertIn("overall_mastery_pct", ks)
        self.assertIn("mastered_kcs_count", ks)
        self.assertIn("total_kcs", ks)
        self.assertGreaterEqual(ks["total_kcs"], 10)

        # 2. KC-Level BKT Mastery
        self.assertIn("kc_mastery_map", intel)
        self.assertIn("kc_details_list", intel)
        self.assertTrue(len(intel["kc_details_list"]) > 0)

        # 3. Assessment Performance
        self.assertIn("assessment_performance", intel)
        ap = intel["assessment_performance"]
        self.assertIn("overall_accuracy_pct", ap)
        self.assertIn("diagnostic_entropy_bits", ap)

        # 4. Difficulty History
        self.assertIn("difficulty_history", intel)
        dh = intel["difficulty_history"]
        for d in range(1, 6):
            self.assertIn(d, dh)

        # 5. Learning Progress
        self.assertIn("learning_progress", intel)

        # 6. Prerequisite Completion
        self.assertIn("prerequisite_completion", intel)

        # 7. Response History
        self.assertIn("response_history", intel)

        # 8. Retention Estimates
        self.assertIn("retention_estimates", intel)

        # 9. Learning Goals
        self.assertIn("learning_goals", intel)

        # 10. Exam Preparation Status
        self.assertIn("exam_preparation_status", intel)

        # 11. Preferences
        self.assertIn("preferences_and_study_time", intel)

        # 12. Recent Intervention History
        self.assertIn("recent_intervention_history", intel)


if __name__ == "__main__":
    unittest.main()
