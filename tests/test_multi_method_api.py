"""
Integration Tests for Multi-Method Knowledge Assessment REST APIs.
Part of AutoLearn KT-RL Multi-Method Knowledge Analysis & RL Integration.
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


class TestMultiMethodAPIs(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_diagnostic_endpoint(self):
        res = self.client.get('/api/assessment/diagnostic/python?learner_id=test_diag_api_1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("questions", data)

    def test_conceptual_evaluate_endpoint(self):
        res = self.client.post('/api/assessment/conceptual/evaluate', json={
            "topic": "python",
            "prompt": "Explain NumPy",
            "response": "NumPy provides contiguous C-level memory arrays with fast vectorized operations.",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("score_pct", data)
        self.assertIn("recognized_concepts", data)

    def test_coding_execute_endpoint(self):
        res = self.client.post('/api/assessment/coding/execute', json={
            "code": "def double_val(x): return x * 2\n",
            "test_cases": [{"input": "double_val(5)", "expected": "10"}],
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["tests_passed"], 1)

    def test_concept_map_endpoint(self):
        res = self.client.post('/api/assessment/concept-map/evaluate', json={
            "edges": [
                {"source": "python", "target": "data preprocessing", "relation": "prerequisite"}
            ]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("alignment_pct", data)

    def test_confidence_calibration_endpoint(self):
        res = self.client.post('/api/assessment/confidence/calibrate', json={
            "history": [
                {"confidence_level": 3, "is_correct": True},
                {"confidence_level": 1, "is_correct": False},
            ]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("calibration", data)

    def test_project_evaluate_endpoint(self):
        res = self.client.post('/api/assessment/project/evaluate', json={
            "project_id": "proj_numpy_eda",
            "submission": "def normalize_scores(X): return (X - X.min()) / (X.max() - X.min())",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("final_score_pct", data)


if __name__ == "__main__":
    unittest.main()
