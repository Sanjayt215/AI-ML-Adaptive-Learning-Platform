"""
Comprehensive unit and integration test suite for AutoLearn 10-Step Personalized Student Journey.
Tests:
- Subject & Course Selection + Initial Diagnostic Generation
- Accurate Topic-Wise Answer Analysis & "Your Knowledge Assessment Report"
- Unattempted questions handled correctly without penalizing as wrong
- Personalized Weak Topic Prioritization & Mistakes Diagnostics
- Topic Exam Generation & Prerequisite Scaffolding
- Full Concept Teaching Centre & Mistake Diagnosis Engine
- Multi-Method Learning Execution (Explanations, Coding Sandbox, Conceptual Evaluation)
- Topic Learning Evaluation Report
- Multi-Method Mock Exam Generation (MCQ, Written, Coding, Mixed)
- Progress Comparison with Initial Diagnostic Baseline
"""

import os
import sys
import tempfile
import unittest
import uuid

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
from services.concept_teaching import get_full_concept_teaching, analyze_student_mistake
from services.personalized_journey import (
    start_initial_diagnostic,
    submit_initial_diagnostic,
    get_weak_topics_priority,
    generate_topic_targeted_exam,
    submit_topic_targeted_exam,
    record_learning_method_activity,
    evaluate_topic_understanding_activity,
    generate_personalized_mock_exam,
    submit_personalized_mock_exam,
)


class TestPersonalizedJourney(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        os.environ["LEARNING_DB_PATH"] = self.db_path
        self.client = app.test_client()
        self.test_learner = f"test_student_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_step1_initial_diagnostic_generation(self):
        """Step 1: Diagnostic questions must have complete educational metadata."""
        diag = start_initial_diagnostic(
            learner_id=self.test_learner,
            subject="ai_ml_core",
            difficulty="adaptive",
            num_questions=6,
            db_path=self.db_path,
        )
        self.assertTrue(diag["ok"])
        self.assertGreaterEqual(diag["total_questions"], 3)
        self.assertIn("diagnostic_id", diag)

        # Inspect first question metadata
        q1 = diag["questions"][0]
        self.assertIn("item_id", q1)
        self.assertIn("topic", q1)
        self.assertIn("subtopic", q1)
        self.assertIn("blooms_level", q1)
        self.assertIn("explanation", q1)
        self.assertIn("related_concept", q1)
        self.assertIn("related_example", q1)
        self.assertIn("prerequisite_topics", q1)

    def test_step2_topic_wise_answer_analysis_and_unattempted_handling(self):
        """Step 2: Unanswered questions must NOT be penalized as wrong answers."""
        diag = start_initial_diagnostic(
            learner_id=self.test_learner,
            subject="ai_ml_core",
            num_questions=5,
            db_path=self.db_path,
        )
        diag_id = diag["diagnostic_id"]
        q_list = diag["questions"]

        # Student answers 1 correctly, 1 incorrectly, and leaves remaining unanswered
        answers = {
            q_list[0]["item_id"]: q_list[0]["correct_answer"],
            q_list[1]["item_id"]: "Totally Incorrect Option 123",
            q_list[2]["item_id"]: "UNANSWERED",
        }

        report = submit_initial_diagnostic(
            learner_id=self.test_learner,
            diagnostic_id=diag_id,
            answers=answers,
            duration_seconds=90,
            db_path=self.db_path,
        )

        self.assertTrue(report["ok"])
        perf = report["overall_performance"]
        self.assertEqual(perf["correct_answers"], 1)
        self.assertEqual(perf["incorrect_answers"], 1)
        self.assertEqual(perf["unanswered_questions"], 1)
        self.assertEqual(perf["attempted_questions"], 2)
        # Score is 1 correct out of 2 attempted = 50.0%
        self.assertEqual(perf["overall_score_pct"], 50.0)

        # Topic breakdown table must be present
        self.assertGreater(len(report["topic_performance_table"]), 0)
        t_row = report["topic_performance_table"][0]
        self.assertIn("status", t_row)
        self.assertIn("bkt_mastery_pct", t_row)

        # Knowledge gaps must capture the incorrect answer
        gaps = report["knowledge_gap_analysis"]
        self.assertGreaterEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["item_id"], q_list[1]["item_id"])
        self.assertIn("concept_misunderstood", gaps[0])

    def test_step3_weak_topics_priority(self):
        """Step 3: Weak topics must be ranked and classified with actionable paths."""
        res = get_weak_topics_priority(self.test_learner, db_path=self.db_path)
        self.assertTrue(res["ok"])
        self.assertIn("weak_topics_ranked", res)
        self.assertIn("developing_topics", res)
        self.assertIn("strong_topics", res)
        self.assertIn("not_assessed_topics", res)

    def test_step4_topic_targeted_exam(self):
        """Step 4: Generates topic exam without repeating previous quiz questions."""
        exam = generate_topic_targeted_exam(
            learner_id=self.test_learner,
            topic="python",
            num_questions=3,
            db_path=self.db_path,
        )
        self.assertTrue(exam["ok"])
        self.assertEqual(exam["topic"], "python")
        self.assertGreaterEqual(len(exam["questions"]), 1)

        # Submit topic exam
        q_item = exam["questions"][0]
        sub = submit_topic_targeted_exam(
            learner_id=self.test_learner,
            exam_id=exam["exam_id"],
            topic="python",
            answers={q_item["item_id"]: q_item["correct_answer"]},
            db_path=self.db_path,
        )
        self.assertTrue(sub["ok"])
        self.assertEqual(sub["score"], 1)
        self.assertEqual(sub["score_pct"], 100.0)

    def test_step5_concept_teaching_and_mistake_diagnosis(self):
        """Step 5: Full concept definitions, formulas, and precise mistake analysis."""
        concept = get_full_concept_teaching("linear regression")
        self.assertIn("concept_name", concept)
        self.assertIn("simple_definition", concept)
        self.assertIn("how_it_works_steps", concept)
        self.assertIn("formula", concept)
        self.assertIn("diagram", concept)
        self.assertIn("worked_example", concept)

        # Mistake analysis for q_py_01
        mistake = analyze_student_mistake("q_py_01", "Flask", topic="python")
        self.assertTrue(mistake["ok"])
        self.assertFalse(mistake["is_correct"])
        self.assertIn("Flask is a lightweight WSGI", mistake["why_incorrect"])
        self.assertEqual(mistake["correct_answer"], "NumPy")
        self.assertIn("follow_up_question", mistake)

    def test_step6_and_7_multi_method_learning_and_evaluation(self):
        """Step 6 & 7: Multiple learning methods and post-learning evaluation report."""
        # Record coding challenge
        code = "import numpy as np\ndef solution():\n    return 42\n"
        rec = record_learning_method_activity(
            learner_id=self.test_learner,
            topic="python",
            method="coding",
            user_input=code,
            db_path=self.db_path,
        )
        self.assertTrue(rec["ok"])

        # Topic learning evaluation report
        eval_rep = evaluate_topic_understanding_activity(
            learner_id=self.test_learner,
            topic="python",
            method="conceptual",
            submission="NumPy provides contiguous C-memory array buffers and vectorized SIMD instructions for linear algebra.",
            db_path=self.db_path,
        )
        self.assertTrue(eval_rep["ok"])
        self.assertIn("report_title", eval_rep)
        self.assertIn("skills_demonstrated", eval_rep)
        self.assertIn("concepts_mastered", eval_rep)

    def test_step8_and_9_personalized_mock_exam_and_comparison(self):
        """Step 8 & 9: Multi-method mock exam and longitudinal progress comparison."""
        mock = generate_personalized_mock_exam(
            learner_id=self.test_learner,
            title="Comprehensive Semester Mock Test",
            method="mixed",
            num_questions=4,
            db_path=self.db_path,
        )
        self.assertTrue(mock["ok"])
        self.assertIn("exam_id", mock)

        # Answer mock questions
        answers = {q["item_id"]: "Option A" for q in mock["questions"]}
        res = submit_personalized_mock_exam(
            learner_id=self.test_learner,
            exam_id=mock["exam_id"],
            answers=answers,
            duration_seconds=300,
            db_path=self.db_path,
        )
        self.assertTrue(res["ok"])
        self.assertIn("score_comparison", res)
        self.assertIn("initial_diagnostic_pct", res["score_comparison"])
        self.assertIn("mock_exam_pct", res["score_comparison"])
        self.assertEqual(len(res["next_actions"]), 3)

    def test_journey_api_endpoints(self):
        """End-to-end HTTP API verification of all journey endpoints."""
        # 1. GET /api/journey/status
        res_status = self.client.get(f"/api/journey/status?learner_id={self.test_learner}")
        self.assertEqual(res_status.status_code, 200)
        self.assertEqual(res_status.get_json()["stage"], "select_and_diagnostic")

        # 2. POST /api/journey/diagnostic/start
        res_diag = self.client.post("/api/journey/diagnostic/start", json={
            "learner_id": self.test_learner,
            "subject": "ai_ml_core",
            "num_questions": 4,
        })
        self.assertEqual(res_diag.status_code, 200)
        diag_id = res_diag.get_json()["diagnostic_id"]

        # 3. POST /api/journey/diagnostic/submit
        res_sub = self.client.post("/api/journey/diagnostic/submit", json={
            "learner_id": self.test_learner,
            "diagnostic_id": diag_id,
            "answers": {"q_py_01": "NumPy"},
            "duration_seconds": 45,
        })
        self.assertEqual(res_sub.status_code, 200)

        # 4. GET /api/journey/concept/python
        res_concept = self.client.get("/api/journey/concept/python")
        self.assertEqual(res_concept.status_code, 200)
        self.assertTrue(res_concept.get_json()["ok"])

        # 5. POST /api/journey/concept/mistake-analysis
        res_mistake = self.client.post("/api/journey/concept/mistake-analysis", json={
            "item_id": "q_py_01",
            "submitted_answer": "Flask",
        })
        self.assertEqual(res_mistake.status_code, 200)
        self.assertIn("Flask", res_mistake.get_json()["why_incorrect"])


if __name__ == "__main__":
    unittest.main()
