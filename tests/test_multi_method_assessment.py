"""
Unit Tests for Multi-Method Student Knowledge Assessment & Evaluation.
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
    from autolearn_fullstack.services.multi_method_assessment import (
        generate_diagnostic_assessment,
        evaluate_diagnostic_assessment,
        evaluate_conceptual_explanation,
        execute_sandboxed_code,
        evaluate_concept_map,
        calculate_confidence_calibration,
        evaluate_project_submission,
        CODING_CHALLENGES,
        PROJECT_SPECIFICATIONS,
    )
except ImportError:
    from services.multi_method_assessment import (
        generate_diagnostic_assessment,
        evaluate_diagnostic_assessment,
        evaluate_conceptual_explanation,
        execute_sandboxed_code,
        evaluate_concept_map,
        calculate_confidence_calibration,
        evaluate_project_submission,
        CODING_CHALLENGES,
        PROJECT_SPECIFICATIONS,
    )


class TestMultiMethodAssessment(unittest.TestCase):
    def test_diagnostic_assessment_generation_and_evaluation(self):
        diag = generate_diagnostic_assessment("linear_regression", learner_id="test_diag_learner_1", num_questions=3)
        self.assertTrue(diag["ok"])
        self.assertEqual(diag["topic"], "linear_regression")
        self.assertGreaterEqual(len(diag["questions"]), 1)

        # Evaluate diagnostic
        sample_q = diag["questions"][0]
        answers = {sample_q["item_id"]: sample_q.get("correct_answer", sample_q.get("options")[0])}
        eval_res = evaluate_diagnostic_assessment("test_diag_learner_1", "linear_regression", answers)
        self.assertTrue(eval_res["ok"])
        self.assertIn("calibrated_prior_mastery", eval_res)
        self.assertIn("recommended_starting_level", eval_res)

    def test_conceptual_understanding_evaluation(self):
        # Good explanation
        resp_good = "NumPy provides contiguous C-level memory buffers with vectorized SIMD array operations that eliminate Python loop overhead."
        res = evaluate_conceptual_explanation("python", "Explain NumPy memory structure", resp_good)
        self.assertTrue(res["ok"])
        self.assertGreaterEqual(res["score_pct"], 60.0)
        self.assertIn("vectorization", res["recognized_concepts"])

        # Brief response
        res_brief = "NumPy is fast."
        brief_eval = evaluate_conceptual_explanation("python", "Explain NumPy", res_brief)
        self.assertTrue(brief_eval["ok"])
        self.assertEqual(brief_eval["status"], "incomplete_response")

    def test_sandboxed_code_execution_security(self):
        # 1. Valid code passing test cases
        valid_code = "def compute_mse(y_true, y_pred):\n    return sum((yt - yp)**2 for yt, yp in zip(y_true, y_pred)) / len(y_true)\n"
        tc = [
            {"input": "compute_mse([1, 2, 3], [1, 2, 3])", "expected": "0.0"},
            {"input": "compute_mse([1, 2, 3], [2, 3, 4])", "expected": "1.0"},
        ]
        res = execute_sandboxed_code(valid_code, tc)
        self.assertTrue(res["ok"])
        self.assertTrue(res["syntax_valid"])
        self.assertEqual(res["tests_passed"], 2)
        self.assertEqual(res["score_pct"], 100.0)

        # 2. Dangerous code blocked
        evil_code = "import os\nos.system('dir')"
        res_evil = execute_sandboxed_code(evil_code, tc)
        self.assertFalse(res_evil["ok"])
        self.assertIn("Security violation", res_evil["error"])

    def test_concept_mapping_assessment(self):
        # Connect python -> data preprocessing -> linear regression
        edges = [
            {"source": "python", "target": "data preprocessing", "relation": "prerequisite"},
            {"source": "data preprocessing", "target": "linear regression", "relation": "prerequisite"},
        ]
        eval_res = evaluate_concept_map(edges)
        self.assertTrue(eval_res["ok"])
        self.assertGreater(eval_res["alignment_pct"], 0)
        self.assertGreaterEqual(eval_res["valid_edges_count"], 1)

    def test_confidence_calibration(self):
        history = [
            {"confidence_level": 3, "is_correct": True},
            {"confidence_level": 3, "is_correct": True},
            {"confidence_level": 2, "is_correct": False},
            {"confidence_level": 1, "is_correct": False},
        ]
        cal = calculate_confidence_calibration(history)
        self.assertIn("brier_score", cal)
        self.assertIn("calibration_status", cal)
        self.assertLessEqual(cal["brier_score"], 0.50)

    def test_project_based_assessment(self):
        sub = "def normalize_scores(X):\n    return (X - X.min()) / (X.max() - X.min())\ndef zscore_outliers(X):\n    return X > 2.0\n"
        res = evaluate_project_submission("proj_numpy_eda", sub)
        self.assertTrue(res["ok"])
        self.assertIn("final_score_pct", res)
        self.assertIn("criteria_results", res)
        self.assertEqual(len(res["criteria_results"]), 4)


if __name__ == "__main__":
    unittest.main()
