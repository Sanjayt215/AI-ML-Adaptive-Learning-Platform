"""
Unit and Integration Tests for Phase 8 Real-World Validation Readiness.
Part of KT-RL Phase 8: Safe Pilot Infrastructure & Personalized Learning Evaluation.

Tests:
1. Learning metrics mathematical formulations and edge-case division safeguards.
2. Assessment service test construction, answer concealment, scoring, and lifecycle.
3. Privacy service cryptographic pseudonymization, PII removal, and research export.
4. Shadow evaluation default off status, exception shielding, and agreement metrics.
5. Live REST API endpoints for assessments, research export, and learner progress.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


from services.assessment_service import (
    compute_learning_metrics,
    generate_assessment_items,
    start_assessment_session,
    submit_assessment_session,
    compare_pre_post_assessments,
    get_learner_assessments,
    init_assessment_tables,
    cleanup_expired_sessions,
)
from services.privacy_service import (
    pseudonymize_learner_id,
    strip_personal_identifiers,
    export_anonymized_research_dataset,
)
from services.shadow_evaluation import (
    is_shadow_mode_enabled,
    set_shadow_mode,
    record_shadow_evaluation,
    get_shadow_metrics,
    clear_shadow_buffer,
    execute_shadow_comparison,
)
from app import app


class TestPhase8LearningMetrics(unittest.TestCase):
    """Verifies mathematical correctness of learning metrics against specification."""

    def test_standard_improvement(self):
        m = compute_learning_metrics(
            p_pre=0.25,
            p_post=0.75,
            p_delayed=0.65,
            num_exercises=10,
            time_min=15.0,
            pre_mastered=0,
            post_mastered=1,
            delayed_mastered=0,
        )
        self.assertAlmostEqual(m["gross_learning_gain"], 0.50, places=4)
        self.assertAlmostEqual(m["normalized_learning_gain"], 0.666667, places=4)
        self.assertEqual(m["net_mastery_delta"], 1)
        self.assertAlmostEqual(m["retention_rate"], 0.866667, places=4)
        self.assertAlmostEqual(m["retained_mastery_gain"], 0.40, places=4)
        self.assertAlmostEqual(m["exercise_efficiency"], 0.05, places=4)
        self.assertAlmostEqual(m["time_efficiency_per_min"], 0.033333, places=4)

    def test_ceiling_effect_zero_headroom(self):
        m = compute_learning_metrics(
            p_pre=1.0,
            p_post=1.0,
            p_delayed=1.0,
            num_exercises=5,
            time_min=10.0,
        )
        self.assertEqual(m["gross_learning_gain"], 0.0)
        self.assertEqual(m["normalized_learning_gain"], 0.0)
        self.assertEqual(m["retention_rate"], 1.0)
        self.assertEqual(m["exercise_efficiency"], 0.0)

    def test_zero_initial_state(self):
        m = compute_learning_metrics(
            p_pre=0.0,
            p_post=0.85,
            p_delayed=0.80,
            num_exercises=20,
            time_min=25.0,
        )
        self.assertAlmostEqual(m["gross_learning_gain"], 0.85, places=4)
        self.assertAlmostEqual(m["normalized_learning_gain"], 0.85, places=4)
        self.assertAlmostEqual(m["retention_rate"], 0.941176, places=4)

    def test_negative_learning_and_forgetting(self):
        m = compute_learning_metrics(
            p_pre=0.60,
            p_post=0.40,
            p_delayed=0.35,
            num_exercises=12,
            time_min=18.0,
        )
        self.assertAlmostEqual(m["gross_learning_gain"], -0.20, places=4)
        self.assertAlmostEqual(m["normalized_learning_gain"], -0.333333, places=4)
        self.assertAlmostEqual(m["retention_rate"], 0.875, places=4)

    def test_zero_exercise_safeguard(self):
        m = compute_learning_metrics(p_pre=0.20, p_post=0.50, num_exercises=0, time_min=0.0)
        self.assertEqual(m["exercise_efficiency"], 0.0)
        self.assertEqual(m["time_efficiency_per_min"], 0.0)


class TestPhase8AssessmentService(unittest.TestCase):
    """Verifies item generation, lifecycle management, and pre/post scoring."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_assessment_tables(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_generate_items_conceals_answers(self):
        items = generate_assessment_items(assessment_type="pre", num_questions=5)
        self.assertEqual(len(items), 5)
        for it in items:
            self.assertIn("item_id", it)
            self.assertIn("question", it)
            self.assertIn("options", it)
            self.assertNotIn("correct_answer", it)
            self.assertNotIn("answer", it)

    def test_assessment_session_flow(self):
        # 1. Start assessment
        session = start_assessment_session(
            learner_id="test_learner_p8",
            assessment_type="pre",
            num_questions=5,
            db_path=self.db_path,
        )
        asm_id = session["assessment_id"]
        self.assertEqual(session["status"], "in_progress")
        self.assertEqual(len(session["questions"]), 5)

        # 2. Submit answers
        from resources import get_question_by_id
        q_id = session["questions"][0]["item_id"]
        q_meta = get_question_by_id(q_id)
        correct_ans = q_meta.get("correct_answer")

        responses = [
            {"item_id": q_id, "selected_option": correct_ans, "time_spent_ms": 3000}
        ]
        res = submit_assessment_session(asm_id, responses, db_path=self.db_path)
        self.assertEqual(res["status"], "completed")
        self.assertGreaterEqual(res["score"], 1)
        self.assertIn("accuracy", res)

        # 3. Retrieve history
        history = get_learner_assessments("test_learner_p8", db_path=self.db_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["assessment_id"], asm_id)

    def test_pre_post_comparison(self):
        # Pre-assessment
        pre_sess = start_assessment_session("learner_comp", "pre", 4, db_path=self.db_path)
        submit_assessment_session(
            pre_sess["assessment_id"],
            [{"item_id": pre_sess["questions"][0]["item_id"], "selected_option": "wrong_choice"}],
            db_path=self.db_path,
        )

        # Post-assessment
        post_sess = start_assessment_session("learner_comp", "post", 4, db_path=self.db_path)
        from resources import get_question_by_id
        q0 = post_sess["questions"][0]["item_id"]
        c_ans = get_question_by_id(q0).get("correct_answer")
        submit_assessment_session(
            post_sess["assessment_id"],
            [{"item_id": q0, "selected_option": c_ans}],
            db_path=self.db_path,
        )

        # Compare
        comp = compare_pre_post_assessments("learner_comp", db_path=self.db_path)
        self.assertTrue(comp["has_comparison"])
        self.assertIn("gross_learning_gain", comp["metrics"])
        self.assertIn("explanation", comp)


class TestPhase8PrivacyService(unittest.TestCase):
    """Verifies cryptographic pseudonymization, PII exclusion, and research dataset generation."""

    def test_pseudonymization_properties(self):
        # Deterministic
        h1 = pseudonymize_learner_id("student_alice")
        h2 = pseudonymize_learner_id("student_alice")
        self.assertEqual(h1, h2)
        self.assertTrue(h1.startswith("subj_"))
        self.assertEqual(len(h1), 21)  # 'subj_' + 16 chars

        # Unique for different inputs
        h3 = pseudonymize_learner_id("student_bob")
        self.assertNotEqual(h1, h3)

    def test_strip_personal_identifiers(self):
        raw = {
            "learner_id": "alice_123",
            "name": "Alice Smith",
            "email": "alice@university.edu",
            "ip_address": "192.168.1.10",
            "score": 0.85,
            "profile": {
                "user_name": "asmith",
                "grade": "undergraduate",
            },
        }
        sanitized = strip_personal_identifiers(raw)
        self.assertNotIn("name", sanitized)
        self.assertNotIn("email", sanitized)
        self.assertNotIn("ip_address", sanitized)
        self.assertNotIn("user_name", sanitized.get("profile", {}))
        self.assertEqual(sanitized["score"], 0.85)
        self.assertEqual(sanitized["profile"]["grade"], "undergraduate")

    def test_export_anonymized_research_dataset(self):
        export_data = export_anonymized_research_dataset()
        self.assertIn("compliance", export_data)
        self.assertTrue(export_data["compliance"]["ferpa_compliant"])
        self.assertFalse(export_data["compliance"]["pii_fields_retained"])
        self.assertIn("participants", export_data)


class TestPhase8ShadowEvaluation(unittest.TestCase):
    """Verifies safe parallel shadow evaluation, disabled default, and agreement metrics."""

    def setUp(self):
        clear_shadow_buffer()
        set_shadow_mode(False)

    def tearDown(self):
        set_shadow_mode(False)
        clear_shadow_buffer()

    def test_shadow_mode_disabled_by_default(self):
        self.assertFalse(is_shadow_mode_enabled())
        metrics = get_shadow_metrics()
        self.assertFalse(metrics["shadow_mode_enabled"])

    def test_record_and_get_shadow_metrics(self):
        set_shadow_mode(True)
        self.assertTrue(is_shadow_mode_enabled())

        record_shadow_evaluation(
            learner_id="subj_test_1",
            state_vector=None,
            production_item_id="py_var_01",
            production_strategy="composite_adaptive",
            shadow_decisions={
                "dueling_dqn": {"item_id": "py_var_01", "latency_ms": 12.0},
                "linucb_bandit": {"item_id": "py_loops_02", "latency_ms": 5.0},
            },
        )

        metrics = get_shadow_metrics()
        self.assertEqual(metrics["total_evaluations"], 1)
        self.assertAlmostEqual(metrics["policies"]["dueling_dqn"]["concordance_rate"], 1.0)
        self.assertAlmostEqual(metrics["policies"]["linucb_bandit"]["concordance_rate"], 0.0)

    def test_execute_shadow_comparison_fault_tolerance(self):
        set_shadow_mode(True)

        class MockRecommender:
            def recommend_exercise(self, learner_id, strategy_override, difficulty_preference=None):
                if strategy_override == "faulty_policy":
                    raise RuntimeError("Simulated experimental exception")
                return {"question": {"item_id": "mock_01", "difficulty": 2}}

        rec = execute_shadow_comparison(
            recommender_instance=MockRecommender(),
            learner_id="test_safe_shadow",
            production_recommendation={"question": {"item_id": "mock_01"}, "strategy_used": "composite_adaptive"},
            candidate_shadow_policies=["faulty_policy"],
        )
        self.assertIsNotNone(rec)
        self.assertEqual(rec["shadow_decisions"]["faulty_policy"]["status"], "error")


class TestPhase8RESTAPI(unittest.TestCase):
    """Verifies live Flask endpoints for assessment, research export, and shadow metrics."""

    def setUp(self):
        self.client = app.test_client()

    def test_api_assessment_config(self):
        res = self.client.get("/api/assessment/config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("default_length", data)
        self.assertIn("supported_types", data)

    def test_api_assessment_lifecycle(self):
        # 1. Start assessment
        res_start = self.client.post("/api/assessment/start", json={
            "user_id": "api_test_user",
            "assessment_type": "pre",
            "num_questions": 3,
        })
        self.assertEqual(res_start.status_code, 200)
        start_data = res_start.get_json()
        self.assertTrue(start_data["ok"])
        asm = start_data["assessment"]
        asm_id = asm["assessment_id"]
        self.assertEqual(len(asm["questions"]), 3)

        # 2. Submit assessment
        res_submit = self.client.post("/api/assessment/submit", json={
            "assessment_id": asm_id,
            "responses": [
                {"item_id": asm["questions"][0]["item_id"], "selected_option": "any", "time_spent_ms": 2500}
            ],
        })
        self.assertEqual(res_submit.status_code, 200)
        submit_data = res_submit.get_json()
        self.assertTrue(submit_data["ok"])
        self.assertEqual(submit_data["results"]["status"], "completed")

        # 3. Get history
        res_hist = self.client.get(f"/api/assessment/history/api_test_user")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = res_hist.get_json()
        self.assertTrue(hist_data["ok"])
        self.assertGreaterEqual(len(hist_data["assessments"]), 1)

    def test_api_research_export(self):
        res = self.client.get("/api/research/export")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("dataset", data)
        self.assertTrue(data["dataset"]["compliance"]["ferpa_compliant"])

    def test_api_shadow_metrics(self):
        res = self.client.get("/api/research/shadow_metrics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("metrics", data)

    def test_api_learner_progress(self):
        res = self.client.get("/api/research/learner_progress/api_test_user")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("bkt_mastery", data)
        self.assertIn("assessment_comparison", data)

    def test_api_curriculum_plan(self):
        res = self.client.get("/api/curriculum/plan?learner_id=test_curric_api")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("curriculum_summary", data)
        self.assertIn("stages", data)
        self.assertEqual(len(data["stages"]), 4)

    def test_api_diagnostic_calibration(self):
        res = self.client.get("/api/diagnostic/calibration")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("calibration", data)
        self.assertIn("ece", data["calibration"])
        self.assertIn("brier_score", data["calibration"])


class TestPhase8SpacedRepetition(unittest.TestCase):
    """Verifies half-life spaced repetition stability, retrievability, and due item detection."""

    def test_stability_expansion_and_lapse(self):
        from services.spaced_repetition import KCSpacingState
        state = KCSpacingState(kc_id="python")
        self.assertEqual(state.stability, 1.0)
        self.assertEqual(state.compute_retrievability(current_step=0), 1.0)

        # Successful review expands stability
        state.update_after_review(current_step=1, is_correct=True)
        self.assertEqual(state.stability, 2.0)
        self.assertEqual(state.repetition_count, 1)

        # Another correct review doubles stability
        state.update_after_review(current_step=3, is_correct=True)
        self.assertEqual(state.stability, 4.0)

        # Retrievability decays as steps elapse
        r_step7 = state.compute_retrievability(current_step=7)
        self.assertAlmostEqual(r_step7, 0.50, places=3)  # 2^(-4/4) = 0.5

        # Lapse resets stability to 1.0
        state.update_after_review(current_step=8, is_correct=False)
        self.assertEqual(state.stability, 1.0)
        self.assertEqual(state.repetition_count, 0)

    def test_scheduler_due_detection(self):
        from services.spaced_repetition import SpacedRepetitionScheduler
        sched = SpacedRepetitionScheduler(retrieval_threshold=0.85)
        sched.record_practice(kc_id="loops", current_step=1, is_correct=True)

        # Immediately after practice, topic is not due
        due_at_1 = sched.get_due_topics(current_step=1)
        self.assertEqual(len(due_at_1), 0)

        # After several steps, retrievability drops below 0.85 -> marked due
        due_at_5 = sched.get_due_topics(current_step=5)
        self.assertEqual(len(due_at_5), 1)
        self.assertEqual(due_at_5[0][0], "loops")


class TestPhase8CurriculumPlanning(unittest.TestCase):
    """Verifies prerequisite topological sort, dependency depth, and frontier identification."""

    def test_curriculum_dag_properties(self):
        from services.curriculum_planner import CurriculumPlanner
        planner = CurriculumPlanner()
        self.assertEqual(len(planner.topological_order), 30)
        # Python should be foundational (depth 0)
        self.assertEqual(planner.depth_map.get("python", 0), 0)

    def test_curriculum_plan_generation(self):
        from services.curriculum_planner import CurriculumPlanner
        planner = CurriculumPlanner()
        plan = planner.generate_curriculum_plan(learner_id="test_plan_student")
        self.assertTrue(plan["ok"])
        self.assertGreater(plan["curriculum_summary"]["total_topics"], 20)
        self.assertEqual(len(plan["stages"]), 4)


class TestPhase8DiagnosticCalibration(unittest.TestCase):
    """Verifies Expected Information Gain and calibration ECE/Brier scoring."""

    def test_information_gain_positive(self):
        from services.diagnostic_calibration import compute_expected_information_gain
        eig_mid = compute_expected_information_gain(0.50)
        eig_extreme = compute_expected_information_gain(0.99)
        self.assertGreater(eig_mid, 0.0)
        # Uncertainty is higher at 0.50 than 0.99
        self.assertGreater(eig_mid, eig_extreme)

    def test_calibration_metrics_accuracy(self):
        from services.diagnostic_calibration import evaluate_bkt_calibration
        preds = [0.9, 0.9, 0.1, 0.1]
        labels = [1, 1, 0, 0]
        cal = evaluate_bkt_calibration(preds, labels)
        self.assertEqual(cal["total_samples"], 4)
        self.assertLess(cal["brier_score"], 0.05)
        self.assertLess(cal["ece"], 0.15)


class TestPhase8NewEndpoints(unittest.TestCase):
    """Verifies live REST API endpoints for revision plan and research benchmark."""

    def setUp(self):
        self.client = app.test_client()

    def test_revision_plan_endpoint(self):
        res = self.client.get('/api/revision/plan?learner_id=test_learner_srs')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('due_today', data)
        self.assertIn('upcoming', data)
        self.assertIn('summary', data)

    def test_research_benchmark_endpoint(self):
        res = self.client.get('/api/research/benchmark')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('data', data)
        self.assertIn('policy_metrics', data['data'])
        self.assertIn('composite_adaptive', data['data']['policy_metrics'])



if __name__ == "__main__":
    unittest.main()
