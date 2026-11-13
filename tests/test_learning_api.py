"""
API Integration tests for Phase 1 Learning Infrastructure.
Tests:
1. POST /api/learning/sessions
2. GET /api/learning/sessions/<id>
3. POST /api/learning/sessions/<id>/complete
4. POST /api/learning/events
5. GET /api/learning/events/<learner_id>
6. GET /api/learning/state/<learner_id>
7. GET /api/learning/items
8. POST /api/quiz event persistence verification
"""

import json
import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Point DB to temporary test location before importing app
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.close(temp_db_fd)
os.environ["LEARNING_DB_PATH"] = temp_db_path

from app import app
from services.learning_store import init_db, get_learner_events


class TestLearningAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(temp_db_path)
        app.testing = True

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

    def setUp(self):
        self.client = app.test_client()

    def test_learning_items_endpoint(self):
        res = self.client.get("/api/learning/items")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(data["count"], 50)
        self.assertTrue(data["item_bank_validation"]["valid"])

    def test_learning_sessions_crud(self):
        # Create session
        res = self.client.post("/api/learning/sessions", json={
            "learner_id": "api_test_learner_01",
            "session_type": "quiz",
            "target_topics": ["python", "deep learning"],
        })
        self.assertEqual(res.status_code, 201)
        sess = res.get_json()["session"]
        session_id = sess["session_id"]
        self.assertEqual(sess["learner_id"], "api_test_learner_01")

        # Get session
        res_get = self.client.get(f"/api/learning/sessions/{session_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()["session"]["session_id"], session_id)

        # Complete session
        res_comp = self.client.post(f"/api/learning/sessions/{session_id}/complete")
        self.assertEqual(res_comp.status_code, 200)
        self.assertEqual(res_comp.get_json()["session"]["status"], "completed")

    def test_learning_events_logging_and_state(self):
        # Create a session first
        res = self.client.post("/api/learning/sessions", json={"learner_id": "api_test_learner_02"})
        session_id = res.get_json()["session"]["session_id"]

        # Log event
        res_evt = self.client.post("/api/learning/events", json={
            "session_id": session_id,
            "learner_id": "api_test_learner_02",
            "item_id": "q_py_01",
            "knowledge_components": ["python"],
            "submitted_answer": "NumPy",
            "correctness": 1,
            "response_time_ms": 3200,
            "attempt_number": 1,
        })
        self.assertEqual(res_evt.status_code, 201)
        evt_data = res_evt.get_json()
        self.assertTrue(evt_data["ok"])

        # Fetch learner events
        res_list = self.client.get("/api/learning/events/api_test_learner_02")
        self.assertEqual(res_list.status_code, 200)
        events = res_list.get_json()["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item_id"], "q_py_01")

        # Fetch learner state
        res_state = self.client.get("/api/learning/state/api_test_learner_02")
        self.assertEqual(res_state.status_code, 200)
        state = res_state.get_json()["state"]
        self.assertEqual(state["total_interactions"], 1)
        self.assertEqual(state["total_correct"], 1)
        self.assertIn("python", state["kc_mastery"])

    def test_quiz_submission_persists_events(self):
        # 1. Start a plan to set up session profile
        with self.client.session_transaction() as sess:
            sess["profile"] = {
                "topics": ["python"],
                "quiz_seed": 42,
                "activity": {"quiz_attempts": 0, "completed_actions": 0},
            }
            sess["quiz_items"] = [{
                "topic": "python",
                "index": "0_0_1234",
                "item_id": "q_py_01",
                "q": "Which library is mainly used for numerical arrays in Python?",
                "options": ["NumPy", "Flask", "OpenCV", "NLTK"],
                "answer": "NumPy",
                "correct_answer": "NumPy",
                "knowledge_components": ["python"],
                "difficulty": 1,
            }]

        # 2. Submit quiz with answer and response time
        res = self.client.post("/api/quiz", json={
            "answers": {"python_0_0_1234": "NumPy"},
            "response_times": {"python_0_0_1234": 2800},
            "learner_id": "integrated_learner_99",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["learner_id"], "integrated_learner_99")

        # 3. Verify event was persisted into SQLite database
        events = get_learner_events("integrated_learner_99", db_path=temp_db_path)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item_id"], "q_py_01")
        self.assertEqual(events[0]["correctness"], 1)
        self.assertEqual(events[0]["response_time_ms"], 2800)

    def test_bkt_mastery_endpoints(self):
        # 1. Fetch mastery for learner with no history (all unassessed)
        res = self.client.get("/api/learning/mastery/brand_new_learner")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["model"], "BKT")
        self.assertEqual(data["total_events_processed"], 0)
        # Verify python topic is unassessed with default prior
        py_topic = data["topics_map"]["python"]
        self.assertEqual(py_topic["status"], "not_assessed")
        self.assertEqual(py_topic["mastery_probability"], 0.20)

        # 2. Query specific KC endpoint
        res_kc = self.client.get("/api/learning/mastery/brand_new_learner/python")
        self.assertEqual(res_kc.status_code, 200)
        self.assertEqual(res_kc.get_json()["topic"]["kc_id"], "python")

        # 3. Non-existent KC returns 404
        res_non_kc = self.client.get("/api/learning/mastery/brand_new_learner/totally_fake_kc_123")
        self.assertEqual(res_non_kc.status_code, 404)

    def test_bkt_mastery_replay_endpoint(self):
        # Replay with experimental parameters
        res = self.client.post("/api/learning/mastery/brand_new_learner/replay", json={
            "parameters": {
                "p_l0": 0.30,
                "p_t": 0.20,
                "p_g": 0.25,
                "p_s": 0.05,
                "version": "bkt-experiment-v2",
            }
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["parameter_version"], "bkt-experiment-v2")
        self.assertEqual(data["parameters"]["p_l0"], 0.30)


    def test_fresh_session_auto_provisioning(self):
        # 1. Fresh client session without prior profile setup
        fresh_client = app.test_client()

        # 2. GET /api/quiz should auto-create default profile and return 200 with quiz items
        res_quiz = fresh_client.get("/api/quiz")
        self.assertEqual(res_quiz.status_code, 200)
        data_quiz = res_quiz.get_json()
        self.assertTrue(data_quiz["ok"])
        self.assertGreater(len(data_quiz["quizItems"]), 0)
        self.assertIn("topics", data_quiz)

        # 3. GET /api/path/resources?topic=search%20algorithms should succeed with 200
        res_res = fresh_client.get("/api/path/resources?topic=search%20algorithms")
        self.assertEqual(res_res.status_code, 200)
        data_res = res_res.get_json()
        self.assertTrue(data_res["ok"])
        self.assertEqual(data_res["topic"], "search algorithms")
        self.assertIn("resources", data_res)
        self.assertIn("videos", data_res["resources"])

        # 4. GET /api/path/progress should succeed with 200
        res_prog = fresh_client.get("/api/path/progress")
        self.assertEqual(res_prog.status_code, 200)
        data_prog = res_prog.get_json()
        self.assertTrue(data_prog["ok"])


if __name__ == "__main__":
    unittest.main()
