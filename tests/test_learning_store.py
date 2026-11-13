"""
Unit tests for Persistent Learner Event Storage (KT-RL Phase 1).
Validates:
1. SQLite schema creation and tables (learning_sessions, learning_events).
2. Session lifecycle: create, retrieve, complete.
3. Event logging: response-time bounds, attempt numbers, idempotency.
4. Learner state aggregation and KC-level accuracy calculations.
"""

import os
import tempfile
import unittest
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from autolearn_fullstack.services.learning_store import (
        init_db,
        create_session,
        get_session,
        complete_session,
        log_event,
        get_learner_events,
        get_learner_state,
        validate_response_time,
    )
except ImportError:
    from services.learning_store import (
        init_db,
        create_session,
        get_session,
        complete_session,
        log_event,
        get_learner_events,
        get_learner_state,
        validate_response_time,
    )


class TestLearningStore(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary SQLite database for each test
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_session_lifecycle(self):
        sess = create_session(
            learner_id="test_learner_01",
            session_type="quiz",
            target_topics=["python", "linear algebra"],
            metadata={"source": "test_suite"},
            db_path=self.db_path,
        )
        self.assertIsNotNone(sess)
        self.assertEqual(sess["learner_id"], "test_learner_01")
        self.assertEqual(sess["status"], "in_progress")
        self.assertEqual(sess["target_topics"], ["python", "linear algebra"])

        fetched = get_session(sess["session_id"], db_path=self.db_path)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["session_id"], sess["session_id"])

        completed = complete_session(sess["session_id"], db_path=self.db_path)
        self.assertEqual(completed["status"], "completed")
        self.assertIsNotNone(completed["end_time"])

    def test_event_logging(self):
        sess = create_session(learner_id="test_learner_02", db_path=self.db_path)
        evt = log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_02",
            item_id="q_py_01",
            knowledge_components=["python"],
            submitted_answer="NumPy",
            correctness=1,
            response_time_ms=4500,
            attempt_number=1,
            interaction_type="quiz_answer",
            metadata={"client": "test"},
            db_path=self.db_path,
        )
        self.assertIsNotNone(evt)
        self.assertEqual(evt["learner_id"], "test_learner_02")
        self.assertEqual(evt["correctness"], 1)
        self.assertEqual(evt["response_time_ms"], 4500)

        events = get_learner_events("test_learner_02", db_path=self.db_path)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item_id"], "q_py_01")

    def test_idempotency_prevents_duplicates(self):
        sess = create_session(learner_id="test_learner_03", db_path=self.db_path)
        evt1 = log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_03",
            item_id="q_py_01",
            knowledge_components=["python"],
            submitted_answer="NumPy",
            correctness=1,
            response_time_ms=3000,
            attempt_number=1,
            db_path=self.db_path,
        )
        # Duplicate submission with same session_id, item_id, attempt_number
        evt2 = log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_03",
            item_id="q_py_01",
            knowledge_components=["python"],
            submitted_answer="NumPy",
            correctness=1,
            response_time_ms=3000,
            attempt_number=1,
            db_path=self.db_path,
        )
        self.assertEqual(evt1["event_id"], evt2["event_id"])
        events = get_learner_events("test_learner_03", db_path=self.db_path)
        self.assertEqual(len(events), 1)

    def test_response_time_validation(self):
        # Normal bounds
        self.assertEqual(validate_response_time(1500), 1500)
        # Unrealistically fast (<50ms)
        self.assertIsNone(validate_response_time(10))
        # Unrealistically long (>3600000ms / 1hr)
        self.assertIsNone(validate_response_time(5000000))
        # None or invalid type
        self.assertIsNone(validate_response_time(None))

    def test_learner_state_aggregation(self):
        sess = create_session(learner_id="test_learner_04", db_path=self.db_path)
        # 1 correct on python
        log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_04",
            item_id="q_py_01",
            knowledge_components=["python"],
            submitted_answer="NumPy",
            correctness=1,
            attempt_number=1,
            db_path=self.db_path,
        )
        # 1 incorrect on python
        log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_04",
            item_id="q_py_02",
            knowledge_components=["python"],
            submitted_answer="wrong",
            correctness=0,
            attempt_number=1,
            db_path=self.db_path,
        )
        # 1 correct on linear regression
        log_event(
            session_id=sess["session_id"],
            learner_id="test_learner_04",
            item_id="q_linreg_01",
            knowledge_components=["linear regression"],
            submitted_answer="Regression",
            correctness=1,
            attempt_number=1,
            db_path=self.db_path,
        )

        state = get_learner_state("test_learner_04", db_path=self.db_path)
        self.assertEqual(state["total_interactions"], 3)
        self.assertEqual(state["total_correct"], 2)
        self.assertEqual(state["overall_accuracy"], 66.7)

        kc_mastery = state["kc_mastery"]
        self.assertIn("python", kc_mastery)
        self.assertEqual(kc_mastery["python"]["attempts"], 2)
        self.assertEqual(kc_mastery["python"]["correct"], 1)
        self.assertIn("linear regression", kc_mastery)
        self.assertEqual(kc_mastery["linear regression"]["empirical_accuracy"], 100.0)


if __name__ == "__main__":
    unittest.main()
