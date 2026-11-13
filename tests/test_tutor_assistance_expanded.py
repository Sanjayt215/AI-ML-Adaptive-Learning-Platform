"""
Unit tests for Expanded AI Tutor Assistance Actions.
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
    from autolearn_fullstack.services.session_manager import (
        create_unified_session,
        handle_assistance_request,
    )
except ImportError:
    from services.session_manager import (
        create_unified_session,
        handle_assistance_request,
    )


class TestExpandedTutorAssistance(unittest.TestCase):
    def setUp(self):
        self.learner_id = "test_assistant_learner_404"
        self.sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic="python",
        )
        self.session_id = self.sess["session_id"]

    def test_explain_wrong_action(self):
        res = handle_assistance_request(
            session_id=self.session_id,
            action="explain_wrong",
            item_id="q_py_01",
            topic="python",
            selected_option="Flask",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "explain_wrong")
        self.assertIn("misconception_analysis", res)
        self.assertIn("Flask", res["misconception_analysis"])

    def test_give_hint_action(self):
        res = handle_assistance_request(
            session_id=self.session_id,
            action="give_hint",
            item_id="q_py_01",
            topic="python",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "give_hint")
        self.assertIn("hints", res)
        self.assertEqual(len(res["hints"]), 3)

    def test_test_understanding_action(self):
        res = handle_assistance_request(
            session_id=self.session_id,
            action="test_understanding",
            item_id="q_py_01",
            topic="python",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "test_understanding")
        self.assertIn("question", res)
        self.assertIn("item_id", res["question"])


if __name__ == "__main__":
    unittest.main()
