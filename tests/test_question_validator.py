"""
Tests for Question Quality Validation Pipeline.
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
    from autolearn_fullstack.services.question_validator import audit_question_bank
except ImportError:
    from services.question_validator import audit_question_bank


class TestQuestionValidator(unittest.TestCase):
    def test_audit_question_bank(self):
        report = audit_question_bank()
        self.assertTrue(report["ok"])
        self.assertTrue(report["is_valid"], f"Validation failed with errors: {report['errors']}")
        self.assertGreaterEqual(report["total_items"], 50)
        self.assertEqual(report["total_items"], report["valid_items"])
        self.assertEqual(report["quality_score_pct"], 100.0)

        # Check distribution maps
        self.assertIn("type_distribution", report)
        self.assertIn("cognitive_level_distribution", report)
        self.assertIn("difficulty_distribution", report)
        self.assertIn("provenance_distribution", report)


if __name__ == "__main__":
    unittest.main()
