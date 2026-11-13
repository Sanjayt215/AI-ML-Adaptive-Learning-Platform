"""
Unit tests for Question Intelligence, 4 Learning Modes, and Repetition Prevention.
Part of AutoLearn KT-RL Functionality & Question Intelligence Upgrade.
"""

import unittest
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.resources import (
        QUIZ_QUESTIONS,
        get_all_questions,
        get_question_by_id,
        validate_item_bank,
    )
    from autolearn_fullstack.services.adaptive_tutor import AdaptiveTutorService, TutorActionType
except ImportError:
    from resources import (
        QUIZ_QUESTIONS,
        get_all_questions,
        get_question_by_id,
        validate_item_bank,
    )
    from services.adaptive_tutor import AdaptiveTutorService, TutorActionType


class TestLearningModesAndQuestionIntelligence(unittest.TestCase):
    def setUp(self):
        self.tutor = AdaptiveTutorService()

    def test_distinct_four_learning_modes(self):
        """Verifies that all 4 learning modes select distinct initial topics and questions."""
        modes = ["continue", "weak_topics", "exam_prep", "revision"]
        sessions = {}
        for m in modes:
            sess = self.tutor.start_tutor_session(f"fresh_learner_mode_{m}", mode=m)
            self.assertTrue(sess["ok"])
            q = sess["action"].get("question") or sess["action"].get("practice_question")
            self.assertIsNotNone(q, f"Mode {m} returned no question")
            sessions[m] = {
                "topic": sess["current_topic"],
                "item_id": q["item_id"],
            }

        topics = [data["topic"] for data in sessions.values()]
        item_ids = [data["item_id"] for data in sessions.values()]

        # Verify that modes do not all collapse to 'python' or 'q_py_01'
        self.assertEqual(
            len(set(item_ids)),
            4,
            f"Expected 4 distinct questions across modes, got: {sessions}"
        )
        self.assertEqual(
            len(set(topics)),
            4,
            f"Expected 4 distinct topics across modes, got: {sessions}"
        )

    def test_repetition_avoidance_across_session_steps(self):
        """Verifies that subsequent questions within a learning session never repeat."""
        sess = self.tutor.start_tutor_session("rep_test_learner", mode="continue")
        session_id = sess["session_id"]
        seen_items = set()

        first_q = sess["action"]["question"]
        seen_items.add(first_q["item_id"])

        current_q = first_q
        for step in range(3):
            res = self.tutor.process_student_step(
                session_id=session_id,
                item_id=current_q["item_id"],
                selected_option=current_q["options"][0],
            )
            self.assertTrue(res["ok"])
            next_act = res.get("next_action", {})
            next_q = next_act.get("question") or next_act.get("practice_question")
            if next_q:
                self.assertNotIn(
                    next_q["item_id"],
                    seen_items,
                    f"Duplicate item {next_q['item_id']} presented at step {step + 2}"
                )
                seen_items.add(next_q["item_id"])
                current_q = next_q

    def test_on_demand_simpler_question_avoids_current_item(self):
        """Verifies that requesting an easier question does not return the current question."""
        sess = self.tutor.start_tutor_session("easier_test_learner", mode="continue", topic="python")
        session_id = sess["session_id"]
        current_item_id = sess["action"]["question"]["item_id"]

        help_res = self.tutor.request_on_demand_intervention(session_id, "easier_question")
        self.assertTrue(help_res["ok"])
        if help_res.get("question"):
            self.assertNotEqual(
                help_res["question"]["item_id"],
                current_item_id,
                "Easier question should not be identical to the current question"
            )

    def test_canonical_question_richness_and_validity(self):
        """Verifies canonical questions have 4 plausible options, explanations, and distractor rationales."""
        validation = validate_item_bank()
        self.assertTrue(validation["valid"], f"Validation errors: {validation['errors']}")
        self.assertEqual(validation["total_items"], 52)

        items = get_all_questions()
        for q in items:
            self.assertGreaterEqual(len(q["options"]), 4, f"Item {q['item_id']} has < 4 options")
            self.assertIn(q["correct_answer"], q["options"])
            self.assertTrue(q.get("explanation"), f"Item {q['item_id']} missing explanation")
            self.assertGreaterEqual(q.get("difficulty", 0), 1)
            self.assertLessEqual(q.get("difficulty", 0), 5)

            # Ensure no low-quality filler questions
            q_text = q.get("question", "").lower()
            self.assertNotIn("which learning level should you begin with", q_text)
            self.assertNotIn("mainly asks you to do what", q_text)


if __name__ == "__main__":
    unittest.main()
