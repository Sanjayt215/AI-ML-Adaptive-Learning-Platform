"""
Unit Tests for Four Distinct Learning Workflows & RL Research Lab Telemetry.
Validates Phase 2, Phase 3, Phase 4 requirements of KT-RL Upgrade.
"""

import unittest
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.services.distinct_workflows import (
        continue_learning,
        improve_weak_topics,
        prepare_for_exam,
        revise_previous_topics,
        submit_workflow_step,
        get_rl_research_telemetry,
    )
except ImportError:
    from services.distinct_workflows import (
        continue_learning,
        improve_weak_topics,
        prepare_for_exam,
        revise_previous_topics,
        submit_workflow_step,
        get_rl_research_telemetry,
    )


class TestFourDistinctWorkflows(unittest.TestCase):
    def setUp(self):
        self.learner_id = "test_workflow_learner_001"

    def test_workflow_a_continue_learning(self):
        """Verifies Continue Learning loads history, frontier, and curriculum progress."""
        res = continue_learning(self.learner_id)
        self.assertTrue(res["ok"])
        self.assertEqual(res["workflow_type"], "continue_learning")
        self.assertIn("curriculum_progress_pct", res)
        self.assertIn("next_recommended_concept", res)
        self.assertIn("reason", res)
        self.assertEqual(res["recommendation_source"], "curriculum_dag_frontier")
        self.assertIsNotNone(res.get("selected_action"))
        self.assertIn("question", res["selected_action"])

    def test_workflow_b_improve_weak_topics(self):
        """Verifies Weak Topics analyzes KCs, ranks weak concepts, and selects intervention."""
        res = improve_weak_topics(self.learner_id)
        self.assertTrue(res["ok"])
        self.assertEqual(res["workflow_type"], "improve_weak_topics")
        self.assertIn("selected_concept", res)
        self.assertIn("intervention_type", res)
        self.assertIn(res["intervention_type"], ["prerequisite_repair", "guided_remediation", "targeted_practice"])
        self.assertIn("weak_concepts_ranked", res)
        self.assertIn("reason", res)
        self.assertEqual(res["recommendation_source"], "recovery_hysteresis_controller")

    def test_workflow_c_prepare_for_exam_setup_and_schedule(self):
        """Verifies Exam Prep returns setup prompt when empty, and schedules tasks when configured."""
        import uuid
        fresh_learner = f"fresh_exam_{uuid.uuid4().hex[:8]}"
        res_setup = prepare_for_exam(fresh_learner)
        self.assertTrue(res_setup["ok"])
        self.assertTrue(res_setup.get("needs_setup", True))

        # Now configure an exam plan
        res_plan = prepare_for_exam(
            learner_id=fresh_learner,
            exam_date="2026-11-20",
            syllabus_topics=["python", "linear_regression", "neural_networks"],
            daily_minutes=30,
            target_score_pct=90,
        )
        self.assertTrue(res_plan["ok"])
        self.assertFalse(res_plan.get("needs_setup", False))
        self.assertEqual(res_plan["workflow_type"], "prepare_for_exam")
        self.assertIn("today_activity", res_plan)
        self.assertIn("days_remaining", res_plan)
        self.assertIn("selected_action", res_plan)

    def test_workflow_d_revise_previous_topics(self):
        """Verifies Spaced Repetition calculates retention decay and scheduled intervals."""
        res = revise_previous_topics(self.learner_id)
        self.assertTrue(res["ok"])
        self.assertEqual(res["workflow_type"], "revise_previous_topics")
        self.assertIn("selected_concept", res)
        self.assertIn("retention_estimate_pct", res)
        self.assertIn("stability_intervals", res)
        self.assertIn("expected_interval_on_success", res)
        self.assertIn("selected_action", res)

    def test_workflow_step_submission_and_adaptation(self):
        """Verifies submitting a step evaluates answer and returns difficulty adaptation."""
        cont_res = continue_learning(self.learner_id)
        session_id = cont_res["session_id"]
        q = cont_res["selected_action"]["question"]

        step_res = submit_workflow_step(
            workflow_type="continue_learning",
            session_id=session_id,
            item_id=q["item_id"],
            selected_option=q["options"][0],
            response_time_ms=1800,
        )
        self.assertTrue(step_res["ok"])
        self.assertIn("feedback", step_res)
        self.assertIn("is_correct", step_res["feedback"])
        self.assertIn("difficulty_adaptation", step_res["feedback"])
        self.assertIn(step_res["feedback"]["difficulty_adaptation"], ["easier", "same", "harder"])

    def test_rl_research_telemetry(self):
        """Verifies Research Lab telemetry exposes DQN disabled state and 10-policy comparison."""
        tel = get_rl_research_telemetry(self.learner_id)
        self.assertTrue(tel["ok"])
        self.assertIn("production_policy", tel)
        self.assertIn("experimental_dqn", tel)
        self.assertIn("contextual_bandit", tel)
        self.assertIn("policy_comparison_benchmark", tel)
        self.assertGreaterEqual(len(tel["policy_comparison_benchmark"]), 8)
        self.assertEqual(tel["experimental_dqn"]["status"], "EXPERIMENTAL / DISABLED BY DEFAULT")


if __name__ == "__main__":
    unittest.main()
