"""
Unit tests for RL Intelligence API & Learner Intelligence Endpoints.
Part of AutoLearn KT-RL Full Website Transformation.
"""

import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.app import app
except ImportError:
    from app import app


class TestRLIntelligenceAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_learner_intelligence_endpoint(self):
        res = self.client.get('/api/learner/intelligence/test_api_learner_99')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("knowledge_state", data)
        self.assertIn("kc_mastery_map", data)
        self.assertIn("difficulty_history", data)

    def test_questions_quality_report_endpoint(self):
        res = self.client.get('/api/questions/quality-report')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["is_valid"])
        self.assertGreaterEqual(data["total_items"], 50)
        self.assertEqual(data["quality_score_pct"], 100.0)

    def test_rl_intelligence_endpoint(self):
        res = self.client.get('/api/rl/intelligence/test_api_learner_99')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("live_learner_state", data)
        self.assertIn("policy_laboratory", data)
        self.assertIn("reward_analytics", data)
        self.assertIn("safety_and_invariants", data)
        self.assertEqual(data["safety_and_invariants"]["action_masking_enforced"], True)


if __name__ == "__main__":
    unittest.main()
