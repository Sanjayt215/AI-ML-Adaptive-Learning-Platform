"""
Tests for Question Metadata and Stable Identifiers (KT-RL Phase 1).
Validates:
1. Stable item_id presence and uniqueness across all questions.
2. Canonical Knowledge Component (KC) mappings.
3. Valid difficulty ratings on the 1-5 ordinal scale.
4. Correct answers exist within the question options.
5. get_all_questions() and get_question_by_id() helpers.
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
        TOPIC_CATALOG,
        get_all_questions,
        get_question_by_id,
        validate_item_bank,
    )
except ImportError:
    from resources import (
        QUIZ_QUESTIONS,
        TOPIC_CATALOG,
        get_all_questions,
        get_question_by_id,
        validate_item_bank,
    )


class TestQuestionMetadata(unittest.TestCase):
    def test_item_bank_validation(self):
        result = validate_item_bank()
        self.assertTrue(
            result["valid"],
            f"Question bank validation failed with errors: {result['errors']}"
        )
        self.assertGreaterEqual(result["total_items"], 50)
        self.assertEqual(result["total_items"], result["unique_ids"])

    def test_unique_stable_item_ids(self):
        items = get_all_questions()
        seen = set()
        for q in items:
            item_id = q.get("item_id")
            self.assertIsNotNone(item_id, f"Missing item_id in question: {q}")
            self.assertTrue(item_id.startswith("q_"), f"Item ID should start with 'q_': {item_id}")
            self.assertNotIn(item_id, seen, f"Duplicate item_id: {item_id}")
            seen.add(item_id)

    def test_knowledge_components_and_prerequisites(self):
        items = get_all_questions()
        for q in items:
            kcs = q.get("knowledge_components")
            self.assertIsInstance(kcs, list, f"Item {q['item_id']} has non-list KCs: {kcs}")
            self.assertGreater(len(kcs), 0, f"Item {q['item_id']} has empty KCs")
            
            prereqs = q.get("prerequisite_components")
            if prereqs is not None:
                self.assertIsInstance(prereqs, list, f"Item {q['item_id']} has non-list prereqs: {prereqs}")

    def test_difficulty_ratings(self):
        items = get_all_questions()
        for q in items:
            diff = q.get("difficulty")
            self.assertIsNotNone(diff, f"Item {q['item_id']} missing difficulty")
            self.assertIsInstance(diff, (int, float), f"Item {q['item_id']} difficulty is not numeric")
            self.assertGreaterEqual(diff, 1, f"Item {q['item_id']} difficulty < 1")
            self.assertLessEqual(diff, 5, f"Item {q['item_id']} difficulty > 5")

    def test_options_and_correct_answer(self):
        items = get_all_questions()
        for q in items:
            opts = q.get("options")
            ans = q.get("correct_answer") or q.get("answer")
            self.assertIsInstance(opts, list)
            self.assertGreaterEqual(len(opts), 2)
            self.assertIn(ans, opts, f"Correct answer '{ans}' not in options for item {q['item_id']}")

    def test_get_question_by_id(self):
        # Known existing questions
        q_py = get_question_by_id("q_py_01")
        self.assertIsNotNone(q_py)
        self.assertEqual(q_py["item_id"], "q_py_01")
        self.assertIn("python", q_py["knowledge_components"])

        q_linreg = get_question_by_id("q_linreg_01")
        self.assertIsNotNone(q_linreg)
        self.assertEqual(q_linreg["item_id"], "q_linreg_01")

        # Non-existent ID
        self.assertIsNone(get_question_by_id("non_existent_id_9999"))


if __name__ == "__main__":
    unittest.main()
