from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "autolearn_learning.db")


def get_db_path(custom_path: Optional[str] = None) -> str:
    if custom_path:
        return custom_path
    env_path = os.environ.get("LEARNING_DB_PATH")
    if env_path:
        return env_path
    os.makedirs(DEFAULT_DB_DIR, exist_ok=True)
    return DEFAULT_DB_PATH


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Safe, repeatable initialization of the learning event database schema."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    session_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    questions_presented INTEGER DEFAULT 0,
                    questions_answered INTEGER DEFAULT 0,
                    metadata_json TEXT
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_learner ON learning_sessions(learner_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_started ON learning_sessions(started_at);"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    knowledge_components TEXT NOT NULL,
                    submitted_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    attempt_number INTEGER DEFAULT 1,
                    difficulty INTEGER DEFAULT 2,
                    event_timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (session_id) REFERENCES learning_sessions(session_id)
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_learner ON learning_events(learner_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_session ON learning_events(session_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_item ON learning_events(item_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON learning_events(event_timestamp);"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS diagnostic_assessments (
                    diagnostic_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    total_questions INTEGER DEFAULT 0,
                    attempted_questions INTEGER DEFAULT 0,
                    correct_answers INTEGER DEFAULT 0,
                    unanswered_questions INTEGER DEFAULT 0,
                    score_pct REAL DEFAULT 0.0,
                    time_spent_seconds INTEGER DEFAULT 0,
                    topic_breakdown_json TEXT,
                    knowledge_gaps_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_diag_learner ON diagnostic_assessments(learner_id);"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS concept_learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    subtopic TEXT,
                    learning_method TEXT NOT NULL,
                    time_spent_seconds INTEGER DEFAULT 0,
                    interactive_input TEXT,
                    evaluation_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cls_learner ON concept_learning_sessions(learner_id);"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mock_examinations (
                    exam_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    method TEXT NOT NULL,
                    topics_json TEXT NOT NULL,
                    difficulty INTEGER DEFAULT 2,
                    duration_minutes INTEGER DEFAULT 15,
                    score_pct REAL DEFAULT 0.0,
                    passed INTEGER DEFAULT 0,
                    topic_scores_json TEXT,
                    method_scores_json TEXT,
                    initial_diagnostic_score REAL,
                    learning_score REAL,
                    improvement_pct REAL,
                    review_items_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mock_learner ON mock_examinations(learner_id);"
            )
    finally:
        conn.close()


def validate_response_time(duration_ms: Any) -> Optional[int]:
    """Sanitizes and validates response duration in milliseconds.
    Rejects negative, non-numeric, or implausible values (> 1 hour or < 50ms).
    Returns the integer milliseconds if valid, otherwise None.
    """
    if duration_ms is None:
        return None
    try:
        val = int(duration_ms)
        if 50 <= val <= 3600000:
            return val
        return None
    except (ValueError, TypeError):
        return None


def create_session(
    learner_id: Optional[str] = None,
    session_type: str = "quiz",
    target_topics: Optional[List[str]] = None,
    questions_presented: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    resolved_learner_id = learner_id.strip() if (learner_id and learner_id.strip()) else f"learner_{uuid.uuid4().hex[:12]}"
    
    meta_dict = dict(metadata or {})
    if target_topics:
        meta_dict["target_topics"] = target_topics
    meta_str = json.dumps(meta_dict)

    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO learning_sessions
                (session_id, learner_id, started_at, session_type, status, questions_presented, questions_answered, metadata_json)
                VALUES (?, ?, ?, ?, 'in_progress', ?, 0, ?);
                """,
                (session_id, resolved_learner_id, now_iso, session_type, questions_presented, meta_str),
            )
        return {
            "session_id": session_id,
            "learner_id": resolved_learner_id,
            "started_at": now_iso,
            "session_type": session_type,
            "status": "in_progress",
            "questions_presented": questions_presented,
            "questions_answered": 0,
            "target_topics": target_topics or [],
            "metadata": meta_dict,
        }
    finally:
        conn.close()


def get_session(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM learning_sessions WHERE session_id = ?;", (session_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            meta = json.loads(data.get("metadata_json") or "{}")
            data["metadata"] = meta
            data["target_topics"] = meta.get("target_topics", [])
        except Exception:
            data["metadata"] = {}
            data["target_topics"] = []
        data["end_time"] = data.get("ended_at")
        return data
    finally:
        conn.close()


def complete_session(
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM learning_sessions WHERE session_id = ?;", (session_id,))
            sess_row = cur.fetchone()
            if not sess_row:
                return None

            cur.execute("SELECT COUNT(*) FROM learning_events WHERE session_id = ?;", (session_id,))
            answered_count = cur.fetchone()[0]

            existing_meta = {}
            try:
                existing_meta = json.loads(sess_row["metadata_json"] or "{}")
            except Exception:
                pass
            if metadata:
                existing_meta.update(metadata)
            meta_update = json.dumps(existing_meta)

            cur.execute(
                """
                UPDATE learning_sessions
                SET ended_at = ?, status = 'completed', questions_answered = ?, metadata_json = ?
                WHERE session_id = ?;
                """,
                (now_iso, answered_count, meta_update, session_id),
            )
            conn.commit()
        return get_session(session_id, db_path=db_path)
    finally:
        conn.close()


def log_event(
    event_dict: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    learner_id: Optional[str] = None,
    item_id: Optional[str] = None,
    knowledge_components: Optional[List[str]] = None,
    submitted_answer: Optional[str] = None,
    correctness: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    attempt_number: int = 1,
    interaction_type: str = "quiz_answer",
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Records a single validated question-answer interaction with server-side correctness.
    Accepts either a single dictionary or direct keyword arguments.
    Handles duplicate prevention for retries.
    """
    if event_dict is not None and isinstance(event_dict, dict):
        d = dict(event_dict)
    else:
        d = {
            "session_id": session_id,
            "learner_id": learner_id,
            "item_id": item_id,
            "knowledge_components": knowledge_components,
            "submitted_answer": submitted_answer,
            "correctness": correctness,
            "is_correct": correctness,
            "response_time_ms": response_time_ms,
            "attempt_number": attempt_number,
            "interaction_type": interaction_type,
            "metadata": metadata,
        }
    d.update(kwargs)
    event_dict = d
    init_db(db_path)
    session_id = str(event_dict.get("session_id") or "").strip()
    learner_id = str(event_dict.get("learner_id") or "").strip()
    item_id = str(event_dict.get("item_id") or "").strip()

    if not item_id:
        raise ValueError("item_id is required for logging a learning event.")

    # Lazy-import to prevent circular import
    try:
        from resources import get_question_by_id
    except ImportError:
        from autolearn_fullstack.resources import get_question_by_id

    question_meta = get_question_by_id(item_id)
    raw_answer = str(event_dict.get("submitted_answer") or "").strip()

    # Determine canonical correctness on the server
    if question_meta and "answer" in question_meta:
        canonical_answer = str(question_meta["answer"]).strip()
        is_correct = 1 if raw_answer.lower() == canonical_answer.lower() else 0
    elif "is_correct" in event_dict:
        # Fallback if procedural item without static metadata
        is_correct = 1 if bool(event_dict["is_correct"]) else 0
    else:
        is_correct = 0

    # Ensure valid session exists
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            if session_id:
                cur.execute("SELECT session_id, learner_id FROM learning_sessions WHERE session_id = ?;", (session_id,))
                sess = cur.fetchone()
                if sess:
                    if not learner_id:
                        learner_id = sess["learner_id"]
                else:
                    # Session ID specified but not in DB -> create it
                    now_iso = datetime.now(timezone.utc).isoformat()
                    if not learner_id:
                        learner_id = f"learner_{uuid.uuid4().hex[:12]}"
                    cur.execute(
                        """
                        INSERT INTO learning_sessions
                        (session_id, learner_id, started_at, session_type, status, questions_presented, questions_answered)
                        VALUES (?, ?, ?, 'auto_created', 'in_progress', 1, 0);
                        """,
                        (session_id, learner_id, now_iso),
                    )
            else:
                now_iso = datetime.now(timezone.utc).isoformat()
                session_id = f"sess_{uuid.uuid4().hex[:12]}"
                if not learner_id:
                    learner_id = f"learner_{uuid.uuid4().hex[:12]}"
                cur.execute(
                    """
                    INSERT INTO learning_sessions
                    (session_id, learner_id, started_at, session_type, status, questions_presented, questions_answered)
                    VALUES (?, ?, ?, 'auto_created', 'in_progress', 1, 0);
                    """,
                    (session_id, learner_id, now_iso),
                )

            # Knowledge components resolution
            kc_list = event_dict.get("knowledge_components")
            if not kc_list and question_meta:
                kc_list = question_meta.get("knowledge_components", [])
            if not kc_list and event_dict.get("topic"):
                kc_list = [str(event_dict["topic"]).strip().lower()]
            if not isinstance(kc_list, list):
                kc_list = [str(kc_list)] if kc_list else ["general"]
            kc_json = json.dumps(kc_list)

            # Difficulty resolution (1-5 scale)
            diff_val = event_dict.get("difficulty")
            if diff_val is None and question_meta:
                diff_val = question_meta.get("difficulty", 2)
            try:
                difficulty = int(diff_val) if diff_val is not None else 2
                difficulty = max(1, min(5, difficulty))
            except (ValueError, TypeError):
                difficulty = 2

            # Attempt number
            attempt_number = int(event_dict.get("attempt_number") or 1)

            # Duplicate / Retry Check (Idempotency)
            cur.execute(
                """
                SELECT event_id, is_correct, event_timestamp
                FROM learning_events
                WHERE session_id = ? AND item_id = ? AND attempt_number = ?;
                """,
                (session_id, item_id, attempt_number),
            )
            existing = cur.fetchone()
            if existing:
                return {
                    "event_id": existing["event_id"],
                    "session_id": session_id,
                    "learner_id": learner_id,
                    "item_id": item_id,
                    "is_correct": bool(existing["is_correct"]),
                    "duplicate": True,
                    "event_timestamp": existing["event_timestamp"],
                }

            # Response time validation
            raw_rt = event_dict.get("response_time_ms")
            sanitized_rt = validate_response_time(raw_rt)

            now_iso = datetime.now(timezone.utc).isoformat()
            event_id = str(event_dict.get("event_id") or f"evt_{uuid.uuid4().hex[:14]}")
            source = str(event_dict.get("source") or "classic_quiz")

            meta = event_dict.get("metadata") or {}
            if raw_rt is not None and sanitized_rt is None:
                meta["raw_rejected_response_time_ms"] = raw_rt

            meta_json = json.dumps(meta)

            cur.execute(
                """
                INSERT INTO learning_events
                (event_id, session_id, learner_id, item_id, knowledge_components,
                 submitted_answer, is_correct, response_time_ms, attempt_number,
                 difficulty, event_timestamp, source, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event_id,
                    session_id,
                    learner_id,
                    item_id,
                    kc_json,
                    raw_answer,
                    is_correct,
                    sanitized_rt,
                    attempt_number,
                    difficulty,
                    now_iso,
                    source,
                    meta_json,
                ),
            )

            # Update session question answered count
            cur.execute(
                """
                UPDATE learning_sessions
                SET questions_answered = questions_answered + 1
                WHERE session_id = ?;
                """,
                (session_id,),
            )

        return {
            "event_id": event_id,
            "session_id": session_id,
            "learner_id": learner_id,
            "item_id": item_id,
            "knowledge_components": kc_list,
            "is_correct": bool(is_correct),
            "correctness": int(is_correct),
            "response_time_ms": sanitized_rt,
            "difficulty": difficulty,
            "attempt_number": attempt_number,
            "event_timestamp": now_iso,
            "duplicate": False,
        }
    finally:
        conn.close()


def get_learner_events(
    learner_id: str,
    limit: int = 100,
    reverse: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        order = "DESC" if reverse else "ASC"
        cur.execute(
            f"""
            SELECT * FROM learning_events
            WHERE learner_id = ?
            ORDER BY event_timestamp {order}
            LIMIT ?;
            """,
            (learner_id, max(1, min(limit, 1000))),
        )
        events = []
        for row in cur.fetchall():
            item = dict(row)
            item["is_correct"] = bool(item["is_correct"])
            item["correctness"] = 1 if item["is_correct"] else 0
            try:
                item["knowledge_components"] = json.loads(item.get("knowledge_components") or "[]")
            except Exception:
                item["knowledge_components"] = []
            try:
                item["metadata"] = json.loads(item.get("metadata_json") or "{}")
            except Exception:
                item["metadata"] = {}
            events.append(item)
        return events
    finally:
        conn.close()


def get_learner_state(learner_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes observed interaction summary statistics for a learner.
    These are observed counts and percentages, not BKT posterior predictions.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT item_id, knowledge_components, is_correct, difficulty, event_timestamp
            FROM learning_events
            WHERE learner_id = ?
            ORDER BY event_timestamp ASC;
            """,
            (learner_id,),
        )
        rows = cur.fetchall()

        total_answered = len(rows)
        total_correct = sum(1 for r in rows if r["is_correct"] == 1)
        accuracy = round((total_correct / total_answered) * 100, 1) if total_answered > 0 else 0.0

        topic_stats: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            try:
                kcs = json.loads(r["knowledge_components"] or "[]")
            except Exception:
                kcs = ["general"]
            for kc in kcs:
                if kc not in topic_stats:
                    topic_stats[kc] = {
                        "attempts": 0,
                        "correct": 0,
                        "accuracy": 0.0,
                        "last_difficulty": r["difficulty"],
                        "last_timestamp": r["event_timestamp"],
                    }
                topic_stats[kc]["attempts"] += 1
                if r["is_correct"] == 1:
                    topic_stats[kc]["correct"] += 1
                topic_stats[kc]["accuracy"] = round(
                    (topic_stats[kc]["correct"] / topic_stats[kc]["attempts"]) * 100, 1
                )
                topic_stats[kc]["empirical_accuracy"] = topic_stats[kc]["accuracy"]
                topic_stats[kc]["last_difficulty"] = r["difficulty"]
                topic_stats[kc]["last_timestamp"] = r["event_timestamp"]

        recent_events = get_learner_events(learner_id, limit=10, reverse=True, db_path=db_path)

        last_active = rows[-1]["event_timestamp"] if rows else None

        return {
            "learner_id": learner_id,
            "total_answered": total_answered,
            "total_interactions": total_answered,
            "total_correct": total_correct,
            "accuracy": accuracy,
            "overall_accuracy": accuracy,
            "topic_breakdown": topic_stats,
            "kc_mastery": topic_stats,
            "recent_events": recent_events,
            "last_active": last_active,
        }
    finally:
        conn.close()


def save_diagnostic_assessment(
    learner_id: str,
    subject: str,
    difficulty: str,
    total_questions: int,
    attempted_questions: int,
    correct_answers: int,
    unanswered_questions: int,
    score_pct: float,
    time_spent_seconds: int,
    topic_breakdown: Dict[str, Any],
    knowledge_gaps: List[Dict[str, Any]],
    diagnostic_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Persists a complete diagnostic assessment record."""
    init_db(db_path)
    d_id = diagnostic_id or f"diag_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO diagnostic_assessments
                (diagnostic_id, learner_id, subject, difficulty, total_questions,
                 attempted_questions, correct_answers, unanswered_questions, score_pct,
                 time_spent_seconds, topic_breakdown_json, knowledge_gaps_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    d_id,
                    learner_id,
                    subject,
                    difficulty,
                    total_questions,
                    attempted_questions,
                    correct_answers,
                    unanswered_questions,
                    score_pct,
                    time_spent_seconds,
                    json.dumps(topic_breakdown),
                    json.dumps(knowledge_gaps),
                    now_iso,
                ),
            )
        return {
            "diagnostic_id": d_id,
            "learner_id": learner_id,
            "score_pct": score_pct,
            "created_at": now_iso,
        }
    finally:
        conn.close()


def get_latest_diagnostic_assessment(
    learner_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent diagnostic assessment for a learner."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM diagnostic_assessments
            WHERE learner_id = ?
            ORDER BY created_at DESC LIMIT 1;
            """,
            (learner_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        data["topic_breakdown"] = json.loads(data.get("topic_breakdown_json") or "{}")
        data["knowledge_gaps"] = json.loads(data.get("knowledge_gaps_json") or "[]")
        return data
    finally:
        conn.close()


def save_concept_learning_session(
    learner_id: str,
    topic: str,
    learning_method: str,
    subtopic: Optional[str] = None,
    time_spent_seconds: int = 0,
    interactive_input: Optional[str] = None,
    evaluation_score: float = 0.0,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Records student engagement in a specific concept learning method."""
    init_db(db_path)
    sess_id = f"cls_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO concept_learning_sessions
                (session_id, learner_id, topic, subtopic, learning_method,
                 time_spent_seconds, interactive_input, evaluation_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    sess_id,
                    learner_id,
                    topic,
                    subtopic or topic.title(),
                    learning_method,
                    time_spent_seconds,
                    interactive_input or "",
                    evaluation_score,
                    now_iso,
                ),
            )
        return {"session_id": sess_id, "ok": True}
    finally:
        conn.close()


def save_mock_examination(
    learner_id: str,
    title: str,
    method: str,
    topics: List[str],
    score_pct: float,
    passed: bool,
    topic_scores: Dict[str, Any],
    method_scores: Dict[str, Any],
    initial_diagnostic_score: Optional[float] = None,
    learning_score: Optional[float] = None,
    improvement_pct: Optional[float] = None,
    review_items: Optional[List[Dict[str, Any]]] = None,
    difficulty: int = 2,
    duration_minutes: int = 15,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Saves a completed multi-method mock examination record."""
    init_db(db_path)
    exam_id = f"mock_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO mock_examinations
                (exam_id, learner_id, title, method, topics_json, difficulty,
                 duration_minutes, score_pct, passed, topic_scores_json, method_scores_json,
                 initial_diagnostic_score, learning_score, improvement_pct, review_items_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    exam_id,
                    learner_id,
                    title,
                    method,
                    json.dumps(topics),
                    difficulty,
                    duration_minutes,
                    score_pct,
                    1 if passed else 0,
                    json.dumps(topic_scores),
                    json.dumps(method_scores),
                    initial_diagnostic_score,
                    learning_score,
                    improvement_pct,
                    json.dumps(review_items or []),
                    now_iso,
                ),
            )
        return {"exam_id": exam_id, "ok": True}
    finally:
        conn.close()


def get_mock_examinations_for_learner(
    learner_id: str,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves all past mock examinations for a learner."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM mock_examinations
            WHERE learner_id = ?
            ORDER BY created_at DESC;
            """,
            (learner_id,),
        )
        rows = cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["topics"] = json.loads(d.get("topics_json") or "[]")
            d["topic_scores"] = json.loads(d.get("topic_scores_json") or "{}")
            d["method_scores"] = json.loads(d.get("method_scores_json") or "{}")
            d["review_items"] = json.loads(d.get("review_items_json") or "[]")
            d["passed"] = bool(d.get("passed"))
            results.append(d)
        return results
    finally:
        conn.close()

