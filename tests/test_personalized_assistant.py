"""
Unit and Integration Tests for Personalized Learning Assistant & Smart Exam Preparation.
Tests:
1. Smart Exam Plan creation, topological prerequisite ordering, and days calculation.
2. Dynamic rebalancing of remaining study days based on BKT performance & availability.
3. Adaptive Tutor Session lifecycle across 4 entry points (continue, weak_topics, exam_prep, revision).
4. Prerequisite Repair: detecting weak upstream DAG prerequisites and triggering remediation.
5. Learning Difficulty Rescue Mode: delivering step-by-step worked examples on repeated errors.
6. On-demand pedagogical interventions (concept explanation, worked example, easier question, prereq help).
7. REST API endpoints (/api/assistant/* and /api/exam/*).
"""

import json
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
from services.exam_planner import (
    create_smart_exam_plan,
    get_smart_exam_plan,
    rebalance_exam_plan,
    complete_exam_activity,
)
from services.adaptive_tutor import AdaptiveTutorService, TutorActionType
from services.tutor_content import get_concept_explanation, get_worked_example


class TestPersonalizedAssistant(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.learner_id = "test_student_assistant_01"

    def test_concept_explanation_and_worked_example(self):
        """Verifies authentic educational content is provided for canonical topics."""
        exp = get_concept_explanation("linear_regression")
        self.assertIn("title", exp)
        self.assertIn("concept_summary", exp)
        self.assertGreater(len(exp["key_points"]), 0)

        example = get_worked_example("linear_regression")
        self.assertIn("title", example)
        self.assertIn("steps", example)
        self.assertGreaterEqual(len(example["steps"]), 3)
        self.assertIn("check_question", example)

    def test_smart_exam_plan_lifecycle(self):
        """Verifies exam schedule creation, topological ordering, and progress tracking."""
        exam_date = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        plan = create_smart_exam_plan(
            learner_id=self.learner_id,
            exam_name="Machine Learning Midterm",
            exam_date=exam_date,
            daily_minutes=45,
            syllabus_topics=["classification", "python", "linear_regression", "decision_trees"],
        )

        self.assertTrue(plan["ok"])
        self.assertEqual(plan["days_remaining"], 10)
        self.assertEqual(plan["daily_minutes"], 45)
        # Topological check: python should be scheduled before linear_regression and classification
        topics = plan["syllabus_topics"]
        self.assertIn("python", topics)
        self.assertLess(topics.index("python"), topics.index("classification"))

        # Retrieve active plan
        fetched = get_smart_exam_plan(self.learner_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["plan_id"], plan["plan_id"])
        self.assertEqual(fetched["progress_pct"], 0.0)
        self.assertIsNotNone(fetched["today_activity"])

        # Mark an activity complete
        first_act = fetched["schedule"][0]
        comp = complete_exam_activity(
            learner_id=self.learner_id,
            plan_id=plan["plan_id"],
            activity_id=first_act["activity_id"],
            score=0.90,
        )
        self.assertTrue(comp["ok"])

        # Re-check progress
        updated = get_smart_exam_plan(self.learner_id)
        self.assertEqual(updated["completed_activities"], 1)

        # Dynamic rebalancing
        rebalanced = rebalance_exam_plan(
            learner_id=self.learner_id,
            plan_id=plan["plan_id"],
            new_daily_minutes=60,
        )
        self.assertTrue(rebalanced["ok"])
        self.assertEqual(rebalanced["plan"]["daily_minutes"], 60)

    def test_adaptive_tutor_start_and_step(self):
        """Verifies tutor session start, question delivery, answer submission, and BKT update."""
        tutor = AdaptiveTutorService()
        sess = tutor.start_tutor_session(
            learner_id=self.learner_id,
            mode="continue",
            topic="python",
        )
        self.assertTrue(sess["ok"])
        session_id = sess["session_id"]
        action = sess["action"]
        self.assertIn("question", action)

        q_item = action["question"]
        item_id = q_item["item_id"]
        opts = q_item["options"]

        # Submit an answer
        res = tutor.process_student_step(
            session_id=session_id,
            item_id=item_id,
            selected_option=opts[0],
            response_time_ms=1500,
        )
        self.assertTrue(res["ok"])
        self.assertIn("feedback", res)
        self.assertIn("is_correct", res["feedback"])
        self.assertIn("next_action", res)

    def test_prerequisite_repair_or_rescue_mode(self):
        """Verifies system triggers Prerequisite Repair or Rescue Mode on consecutive failures."""
        tutor = AdaptiveTutorService()
        sess = tutor.start_tutor_session(
            learner_id="struggling_learner",
            mode="weak_topics",
            topic="decision_trees",
        )
        session_id = sess["session_id"]
        q_item = sess["action"]["question"]

        # Intentionally submit incorrect answer 1
        res1 = tutor.process_student_step(
            session_id=session_id,
            item_id=q_item["item_id"],
            selected_option="Definitely_Wrong_Option_123",
            response_time_ms=2000,
        )
        self.assertFalse(res1["feedback"]["is_correct"])

        # Intentionally submit incorrect answer 2 to trigger rescue or prerequisite repair
        next_q = res1["next_action"].get("question") or q_item
        res2 = tutor.process_student_step(
            session_id=session_id,
            item_id=next_q["item_id"],
            selected_option="Definitely_Wrong_Option_456",
            response_time_ms=2000,
        )
        self.assertFalse(res2["feedback"]["is_correct"])

        # Next action should be an educational intervention: WORKED_EXAMPLE or PREREQUISITE_REPAIR
        next_act = res2["next_action"]
        self.assertIn(next_act["action_type"], [
            TutorActionType.WORKED_EXAMPLE.value,
            TutorActionType.PREREQUISITE_REPAIR.value,
        ])
        self.assertIn("rationale", next_act)
        self.assertIn("worked_example", next_act)

    def test_on_demand_student_interventions(self):
        """Verifies students can ask for explanations, worked examples, and prerequisite help."""
        tutor = AdaptiveTutorService()
        sess = tutor.start_tutor_session(
            learner_id=self.learner_id,
            mode="continue",
            topic="classification",
        )
        session_id = sess["session_id"]

        # Request concept explanation
        exp_res = tutor.request_on_demand_intervention(session_id, "explain")
        self.assertTrue(exp_res["ok"])
        self.assertEqual(exp_res["action_type"], "concept_explanation")
        self.assertIn("content", exp_res)

        # Request worked example
        ex_res = tutor.request_on_demand_intervention(session_id, "worked_example")
        self.assertTrue(ex_res["ok"])
        self.assertEqual(ex_res["action_type"], "worked_example")
        self.assertIn("steps", ex_res["content"])

        # Request prerequisite help
        p_res = tutor.request_on_demand_intervention(session_id, "prereq_help")
        self.assertTrue(p_res["ok"])
        self.assertIn("prerequisites", p_res)

    def test_rest_api_endpoints(self):
        """Verifies all new Flask API endpoints return valid JSON responses."""
        # Start assistant session
        r_start = self.client.post('/api/assistant/start', json={
            "learner_id": self.learner_id,
            "mode": "continue",
            "topic": "python",
        })
        self.assertEqual(r_start.status_code, 200)
        d_start = r_start.get_json()
        self.assertTrue(d_start["ok"])
        session_id = d_start["session_id"]
        q_item = d_start["action"]["question"]

        # Step submission
        r_step = self.client.post('/api/assistant/step', json={
            "session_id": session_id,
            "item_id": q_item["item_id"],
            "selected_option": q_item["options"][0],
            "response_time_ms": 1200,
        })
        self.assertEqual(r_step.status_code, 200)
        d_step = r_step.get_json()
        self.assertTrue(d_step["ok"])

        # On-demand intervention
        r_int = self.client.post('/api/assistant/intervention', json={
            "session_id": session_id,
            "intervention_type": "explain",
        })
        self.assertEqual(r_int.status_code, 200)
        self.assertTrue(r_int.get_json()["ok"])

        # Create exam plan
        exam_dt = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
        r_exam = self.client.post('/api/exam/create', json={
            "learner_id": self.learner_id,
            "exam_name": "Final Semester Exam",
            "exam_date": exam_dt,
            "daily_minutes": 30,
            "syllabus_topics": ["python", "linear_regression"],
        })
        self.assertEqual(r_exam.status_code, 200)
        self.assertTrue(r_exam.get_json()["ok"])

        # Get exam plan
        r_get_exam = self.client.get(f'/api/exam/plan/{self.learner_id}')
        self.assertEqual(r_get_exam.status_code, 200)
        self.assertTrue(r_get_exam.get_json()["ok"])


if __name__ == '__main__':
    unittest.main()
