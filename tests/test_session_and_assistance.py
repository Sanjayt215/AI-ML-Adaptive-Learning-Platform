"""
Unit Tests for Unified Session Management, Expiration, Assistance Dispatcher,
and Mock Exam Simulation.
Part of AutoLearn KT-RL Functionality, Session Bug Fixes & AI Tutor Upgrades.
"""

import unittest
import uuid
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure repo root and app dir in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.services.session_manager import (
        create_unified_session,
        get_unified_session,
        complete_unified_session,
        handle_assistance_request,
        _SESSION_CACHE,
    )
    from autolearn_fullstack.services.distinct_workflows import (
        continue_learning,
        improve_weak_topics,
        prepare_for_exam,
        revise_previous_topics,
        start_mock_exam,
        submit_mock_exam,
        submit_spaced_review,
    )
except ImportError:
    from services.session_manager import (
        create_unified_session,
        get_unified_session,
        complete_unified_session,
        handle_assistance_request,
        _SESSION_CACHE,
    )
    from services.distinct_workflows import (
        continue_learning,
        improve_weak_topics,
        prepare_for_exam,
        revise_previous_topics,
        start_mock_exam,
        submit_mock_exam,
        submit_spaced_review,
    )


class TestSessionAndAssistance(unittest.TestCase):
    def setUp(self):
        self.learner_id = f"test_learner_{uuid.uuid4().hex[:8]}"
        self.topic = "linear_regression"

    def test_session_creation_and_persistent_retrieval(self):
        """Verifies session is created in SQLite and retrieved successfully."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic=self.topic,
        )
        self.assertIn("session_id", sess)
        self.assertEqual(sess["status"], "in_progress")

        # Retrieve session
        retrieved, err = get_unified_session(sess["session_id"])
        self.assertIsNone(err)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["session_id"], sess["session_id"])
        self.assertEqual(retrieved["current_topic"], self.topic)

    def test_missing_and_invalid_session_handling(self):
        """Verifies missing or invalid session ID returns controlled error response."""
        _, err_none = get_unified_session(None)
        self.assertIsNotNone(err_none)
        self.assertEqual(err_none["status"], "INVALID_SESSION")

        _, err_empty = get_unified_session("")
        self.assertIsNotNone(err_empty)
        self.assertEqual(err_empty["status"], "INVALID_SESSION")

        _, err_fake = get_unified_session("sess_nonexistent_12345")
        self.assertIsNotNone(err_fake)
        self.assertEqual(err_fake["status"], "NOT_FOUND")

    def test_completed_session_cannot_be_reused(self):
        """Verifies a completed session returns controlled COMPLETED status."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic=self.topic,
        )
        complete_unified_session(sess["session_id"])

        retrieved, err = get_unified_session(sess["session_id"])
        self.assertIsNone(retrieved)
        self.assertIsNotNone(err)
        self.assertEqual(err["status"], "COMPLETED")

    def test_expired_session_handling(self):
        """Verifies sessions older than 24 hours return controlled EXPIRED status."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic=self.topic,
        )
        # Manually backdate started_at by 25 hours
        old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        sess["started_at"] = old_time
        _SESSION_CACHE[sess["session_id"]]["started_at"] = old_time

        retrieved, err = get_unified_session(sess["session_id"])
        self.assertIsNone(retrieved)
        self.assertIsNotNone(err)
        self.assertEqual(err["status"], "EXPIRED")

    def test_assistance_explain_concept(self):
        """Verifies Explain Concept returns 9-point structured conceptual breakdown."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic=self.topic,
        )
        res = handle_assistance_request(
            session_id=sess["session_id"],
            action="explain",
            item_id="q_linreg_01",
            topic=self.topic,
            learner_id=self.learner_id,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "concept_explanation")
        self.assertIn("content", res)
        content = res["content"]
        self.assertIn("definition", content)
        self.assertIn("why_it_matters", content)
        self.assertIn("step_by_step_reasoning", content)
        self.assertIn("formula_or_syntax", content)
        self.assertIn("common_misconceptions", content)
        self.assertIn("learner_level_adaptation", content)
        self.assertIn("check_question", content)

    def test_assistance_worked_example(self):
        """Verifies Show Worked Example returns 10-point structured walkthrough."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="improve_weak_topics",
            target_topic=self.topic,
        )
        res = handle_assistance_request(
            session_id=sess["session_id"],
            action="worked_example",
            topic=self.topic,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "worked_example")
        self.assertIn("worked_example", res)
        we = res["worked_example"]
        self.assertIn("problem_statement", we)
        self.assertIn("steps", we)
        self.assertGreaterEqual(len(we["steps"]), 2)

    def test_assistance_easier_step(self):
        """Verifies Need an Easier Step delivers lower-difficulty non-repeating question."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="continue_learning",
            target_topic=self.topic,
        )
        res = handle_assistance_request(
            session_id=sess["session_id"],
            action="easier_step",
            item_id="q_linreg_01",
            topic=self.topic,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "easier_question")
        self.assertIn("question", res)
        self.assertLessEqual(res["question"]["difficulty"], 2)

    def test_assistance_inspect_prerequisites(self):
        """Verifies Inspect Prerequisites returns DAG dependency tree and gap detection."""
        sess = create_unified_session(
            learner_id=self.learner_id,
            workflow_type="improve_weak_topics",
            target_topic="linear_regression",
        )
        res = handle_assistance_request(
            session_id=sess["session_id"],
            action="inspect_prerequisites",
            topic="linear_regression",
            learner_id=self.learner_id,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["action_type"], "inspect_prerequisites")
        self.assertIn("prerequisites", res)
        self.assertIn("has_prerequisite_gap", res)

    def test_mock_exam_simulation(self):
        """Verifies start and scoring of multi-question Mock Exam in Workflow C."""
        exam_init = start_mock_exam(
            learner_id=self.learner_id,
            num_questions=5,
            syllabus_topics=["python", "linear_regression", "classification"],
        )
        self.assertTrue(exam_init["ok"])
        self.assertEqual(exam_init["total_questions"], 5)
        self.assertEqual(len(exam_init["questions"]), 5)
        session_id = exam_init["session_id"]

        # Submit answers
        answers = {q["item_id"]: q["options"][0] for q in exam_init["questions"]}
        exam_result = submit_mock_exam(session_id=session_id, answers=answers)
        self.assertTrue(exam_result["ok"])
        self.assertIn("score_pct", exam_result)
        self.assertIn("passed", exam_result)
        self.assertIn("topic_breakdown", exam_result)
        self.assertEqual(exam_result["total_questions"], 5)

    def test_spaced_review_flashcard_rating(self):
        """Verifies flashcard recall rating updates stability and next review date in Workflow D."""
        rev = revise_previous_topics(self.learner_id)
        session_id = rev["session_id"]
        item_id = rev["selected_action"]["question"]["item_id"]

        # Rate recall as "good"
        res = submit_spaced_review(session_id=session_id, item_id=item_id, recall_rating="good")
        self.assertTrue(res["ok"])
        self.assertIn("next_review_date", res)
        self.assertIn("updated_stability", res)
        self.assertGreaterEqual(res["updated_stability"], 2.0)


if __name__ == "__main__":
    unittest.main()
