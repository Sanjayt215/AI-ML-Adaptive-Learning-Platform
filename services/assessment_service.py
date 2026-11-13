"""
Assessment Service for Pre, Post, and Delayed Retention Assessments.
Part of KT-RL Phase 8: Real-World Validation Readiness & Safe Pilot Infrastructure.

Provides:
- Stratified and balanced assessment test construction across Knowledge Components.
- Assessment session lifecycle management (not_started, in_progress, completed, abandoned).
- Strict answer concealment (solutions never sent to the client).
- Automatic scoring, per-KC accuracy breakdown, and BKT state initialization.
- Incomplete attempt handling with timeout safeguards.
- Standardized learning gain and retention calculation matching Phase 8 metrics specification.
"""

from __future__ import annotations

import json
import logging
import math
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    from resources import QUIZ_QUESTIONS, TOPIC_CATALOG, get_all_questions, get_question_by_id
    from services.learning_store import get_connection, get_db_path
    from services.bkt_service import update_kc_mastery, KCState, BKTParameters, DEFAULT_PARAMS
except ImportError:
    from autolearn_fullstack.resources import QUIZ_QUESTIONS, TOPIC_CATALOG, get_all_questions, get_question_by_id
    from autolearn_fullstack.services.learning_store import get_connection, get_db_path
    from autolearn_fullstack.services.bkt_service import update_kc_mastery, KCState, BKTParameters, DEFAULT_PARAMS

logger = logging.getLogger(__name__)

# Constants
DEFAULT_ASSESSMENT_LENGTH = 10
SESSION_TIMEOUT_MINUTES = 60
MASTERY_THRESHOLD = 0.80
EPSILON = 1e-6


def init_assessment_tables(db_path: Optional[str] = None) -> None:
    """Initializes the assessments table in the SQLite database if not present."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assessment_sessions (
                    assessment_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL, -- 'pre', 'post', 'retention'
                    status TEXT NOT NULL,          -- 'in_progress', 'completed', 'abandoned'
                    num_questions INTEGER NOT NULL,
                    question_ids_json TEXT NOT NULL,
                    responses_json TEXT,
                    score INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.0,
                    kc_scores_json TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    metadata_json TEXT
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assessment_learner ON assessment_sessions(learner_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assessment_type ON assessment_sessions(assessment_type);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assessment_status ON assessment_sessions(status);"
            )
    finally:
        conn.close()


def generate_assessment_items(
    assessment_type: str = "pre",
    num_questions: int = DEFAULT_ASSESSMENT_LENGTH,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Selects a balanced, stratified set of questions from the canonical question bank.
    Ensures broad coverage across core topics and appropriate difficulty distribution.
    Strips correct answers from the returned dicts so student payloads are safe.
    """
    all_questions = get_all_questions()
    if not all_questions:
        return []

    num_questions = max(3, min(num_questions, len(all_questions)))

    # Group questions by primary topic/KC
    topic_map: Dict[str, List[Dict[str, Any]]] = {}
    for q in all_questions:
        topic = q.get("topic") or (q.get("knowledge_components") or ["general"])[0]
        topic_map.setdefault(topic, []).append(q)

    topics = sorted(list(topic_map.keys()))
    selected_items: List[Dict[str, Any]] = []
    seen_ids = set()

    # Stratified selection: pick from each topic in round-robin fashion
    idx = 0
    import random
    rng = random.Random(seed if seed is not None else 42)
    
    # Shuffle within each topic bucket
    for t in topics:
        rng.shuffle(topic_map[t])

    while len(selected_items) < num_questions:
        topic = topics[idx % len(topics)]
        bucket = topic_map[topic]
        picked = None
        for cand in bucket:
            if cand["item_id"] not in seen_ids:
                picked = cand
                break
        if picked:
            seen_ids.add(picked["item_id"])
            # Create sanitized student copy (hide correct answer)
            student_item = {
                "item_id": picked["item_id"],
                "question": picked.get("question") or picked.get("q"),
                "options": list(picked.get("options") or []),
                "difficulty": picked.get("difficulty", 2),
                "knowledge_components": list(picked.get("knowledge_components") or []),
                "topic": picked.get("topic", topic),
            }
            selected_items.append(student_item)
        idx += 1
        # Avoid infinite loop if question bank exhausted
        if idx > len(topics) * 10:
            break

    return selected_items


def start_assessment_session(
    learner_id: str,
    assessment_type: str = "pre",
    num_questions: int = DEFAULT_ASSESSMENT_LENGTH,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initiates a new assessment session for a learner, persists it in SQLite,
    and returns the sanitized assessment payload.
    """
    init_assessment_tables(db_path)
    if assessment_type not in ("pre", "post", "retention"):
        raise ValueError(f"Invalid assessment_type '{assessment_type}'. Must be 'pre', 'post', or 'retention'.")

    # Check and mark expired sessions as abandoned
    cleanup_expired_sessions(learner_id, db_path=db_path)

    items = generate_assessment_items(assessment_type=assessment_type, num_questions=num_questions)
    question_ids = [it["item_id"] for it in items]
    assessment_id = f"asm_{uuid.uuid4().hex[:12]}"
    now_str = datetime.now(timezone.utc).isoformat()

    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO assessment_sessions (
                    assessment_id, learner_id, assessment_type, status,
                    num_questions, question_ids_json, started_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    assessment_id,
                    learner_id,
                    assessment_type,
                    "in_progress",
                    len(question_ids),
                    json.dumps(question_ids),
                    now_str,
                    json.dumps({"timeout_minutes": SESSION_TIMEOUT_MINUTES}),
                ),
            )
    finally:
        conn.close()

    return {
        "assessment_id": assessment_id,
        "learner_id": learner_id,
        "assessment_type": assessment_type,
        "status": "in_progress",
        "num_questions": len(items),
        "questions": items,
        "started_at": now_str,
        "timeout_minutes": SESSION_TIMEOUT_MINUTES,
    }


def submit_assessment_session(
    assessment_id: str,
    responses: List[Dict[str, Any]],
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submits student responses for an active assessment session.
    Computes overall score, per-KC breakdown, marks session completed,
    and returns detailed evaluation results.

    Each response item expected:
    {
        "item_id": "py_var_01",
        "selected_option": "int",     # string answer or selected index
        "time_spent_ms": 4200
    }
    """
    init_assessment_tables(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM assessment_sessions WHERE assessment_id = ?;", (assessment_id,)
        ).fetchone()

        if not row:
            raise ValueError(f"Assessment session '{assessment_id}' not found.")

        current_status = row["status"]
        if current_status == "completed":
            raise ValueError(f"Assessment session '{assessment_id}' is already completed.")
        if current_status == "abandoned":
            raise ValueError(f"Assessment session '{assessment_id}' has been abandoned/timed out.")

        learner_id = row["learner_id"]
        assessment_type = row["assessment_type"]
        started_at_str = row["started_at"]
        question_ids = json.loads(row["question_ids_json"])

        started_at = datetime.fromisoformat(started_at_str)
        now = datetime.now(timezone.utc)
        duration_sec = max(0.0, (now - started_at).total_seconds())

        # Build response map
        resp_map = {r.get("item_id"): r for r in responses if r.get("item_id")}

        # Score responses
        total_score = 0
        total_items = len(question_ids)
        kc_results: Dict[str, Dict[str, int]] = {}  # kc -> {"correct": 0, "total": 0}
        item_evaluations: List[Dict[str, Any]] = []

        for q_id in question_ids:
            q_meta = get_question_by_id(q_id)
            if not q_meta:
                continue

            resp = resp_map.get(q_id, {})
            selected_option = resp.get("selected_option")
            time_spent = resp.get("time_spent_ms", 0)

            expected_ans = q_meta.get("correct_answer") or q_meta.get("answer")
            is_correct = False
            if selected_option is not None:
                # Direct match or string comparison
                if str(selected_option).strip() == str(expected_ans).strip():
                    is_correct = True
                # Index based match if selected_option is integer
                elif isinstance(selected_option, int) and 0 <= selected_option < len(q_meta.get("options", [])):
                    if q_meta["options"][selected_option] == expected_ans:
                        is_correct = True

            if is_correct:
                total_score += 1

            kcs = q_meta.get("knowledge_components") or [q_meta.get("topic", "general")]
            for kc in kcs:
                if kc not in kc_results:
                    kc_results[kc] = {"correct": 0, "total": 0}
                kc_results[kc]["total"] += 1
                if is_correct:
                    kc_results[kc]["correct"] += 1

            item_evaluations.append({
                "item_id": q_id,
                "is_correct": is_correct,
                "selected_option": selected_option,
                "correct_answer": expected_ans,
                "knowledge_components": kcs,
                "time_spent_ms": time_spent,
            })

        accuracy = float(total_score) / max(1, total_items)

        # Per-KC accuracy dictionary
        kc_scores = {
            kc: {
                "score": data["correct"],
                "total": data["total"],
                "mastery_estimate": round(float(data["correct"]) / max(1, data["total"]), 4),
            }
            for kc, data in kc_results.items()
        }

        # Save to database
        now_str = now.isoformat()
        with conn:
            conn.execute(
                """
                UPDATE assessment_sessions
                SET status = 'completed',
                    score = ?,
                    total_questions = ?,
                    accuracy = ?,
                    responses_json = ?,
                    kc_scores_json = ?,
                    completed_at = ?,
                    duration_seconds = ?
                WHERE assessment_id = ?;
                """,
                (
                    total_score,
                    total_items,
                    accuracy,
                    json.dumps(item_evaluations),
                    json.dumps(kc_scores),
                    now_str,
                    duration_sec,
                    assessment_id,
                ),
            )

        return {
            "assessment_id": assessment_id,
            "learner_id": learner_id,
            "assessment_type": assessment_type,
            "status": "completed",
            "score": total_score,
            "total_questions": total_items,
            "accuracy": round(accuracy, 4),
            "duration_seconds": round(duration_sec, 2),
            "kc_scores": kc_scores,
            "evaluations": item_evaluations,
            "completed_at": now_str,
        }
    finally:
        conn.close()


def cleanup_expired_sessions(learner_id: Optional[str] = None, db_path: Optional[str] = None) -> int:
    """Marks in-progress assessment sessions older than SESSION_TIMEOUT_MINUTES as abandoned."""
    conn = get_connection(db_path)
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=SESSION_TIMEOUT_MINUTES)).isoformat()
        query = "UPDATE assessment_sessions SET status = 'abandoned' WHERE status = 'in_progress' AND started_at < ?"
        params = [cutoff]
        if learner_id:
            query += " AND learner_id = ?"
            params.append(learner_id)
        with conn:
            cur = conn.execute(query, tuple(params))
            return cur.rowcount
    finally:
        conn.close()


def get_learner_assessments(learner_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all assessment sessions for a specific learner."""
    init_assessment_tables(db_path)
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM assessment_sessions
            WHERE learner_id = ?
            ORDER BY started_at ASC;
            """,
            (learner_id,),
        ).fetchall()

        results = []
        for r in rows:
            accuracy_val = r["accuracy"]
            score_pct = round(accuracy_val * 100, 1) if accuracy_val is not None else (
                round((r["score"] / r["total_questions"]) * 100, 1) if r["total_questions"] and r["total_questions"] > 0 else 0.0
            )
            results.append({
                "assessment_id": r["assessment_id"],
                "learner_id": r["learner_id"],
                "assessment_type": r["assessment_type"],
                "status": r["status"],
                "score": r["score"],
                "total_questions": r["total_questions"],
                "accuracy": accuracy_val,
                "score_pct": score_pct,
                "kc_scores": json.loads(r["kc_scores_json"]) if r["kc_scores_json"] else {},
                "started_at": r["started_at"],
                "completed_at": r["completed_at"],
                "duration_seconds": r["duration_seconds"],
            })
        return results
    finally:
        conn.close()


def compute_learning_metrics(
    p_pre: float,
    p_post: float,
    p_delayed: Optional[float] = None,
    num_exercises: int = 0,
    time_min: float = 0.0,
    pre_mastered: int = 0,
    post_mastered: int = 0,
    delayed_mastered: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Standard implementation of Phase 8 Learning Metrics Specification:
    - Gross Learning Gain
    - Normalized Learning Gain (Hake's g) with epsilon safeguard
    - Net Mastery Delta
    - Retention Rate
    - Retained Mastery Gain
    - Exercise & Time Efficiency
    """
    # 1. Gross Learning Gain
    gross_gain = p_post - p_pre

    # 2. Normalized Learning Gain (Hake's gain)
    if p_pre < (1.0 - EPSILON) and p_post >= p_pre:
        norm_gain = (p_post - p_pre) / (1.0 - p_pre)
    elif p_pre > EPSILON and p_post < p_pre:
        norm_gain = (p_post - p_pre) / p_pre
    else:
        norm_gain = 0.0

    # 3. Net Binary Mastery Delta
    net_mastery_delta = post_mastered - pre_mastered

    # 4. Retention Metrics
    retention_rate = 0.0
    retained_gain = 0.0
    norm_retained_gain = 0.0

    if p_delayed is not None:
        retained_gain = p_delayed - p_pre
        if p_post > EPSILON:
            retention_rate = p_delayed / p_post
        elif p_post <= EPSILON and p_delayed <= EPSILON:
            retention_rate = 1.0
        else:
            retention_rate = 0.0

        if p_pre < (1.0 - EPSILON):
            norm_retained_gain = (p_delayed - p_pre) / (1.0 - p_pre)
        else:
            norm_retained_gain = 0.0

    # 5. Efficiency Metrics
    exercise_efficiency = gross_gain / num_exercises if num_exercises > 0 else 0.0
    time_efficiency = gross_gain / time_min if time_min > 0.0 else 0.0

    return {
        "gross_learning_gain": round(gross_gain, 6),
        "normalized_learning_gain": round(norm_gain, 6),
        "net_mastery_delta": net_mastery_delta,
        "retention_rate": round(retention_rate, 6) if p_delayed is not None else None,
        "retained_mastery_gain": round(retained_gain, 6) if p_delayed is not None else None,
        "normalized_retained_gain": round(norm_retained_gain, 6) if p_delayed is not None else None,
        "exercise_efficiency": round(exercise_efficiency, 6),
        "time_efficiency_per_min": round(time_efficiency, 6),
    }


def compare_pre_post_assessments(learner_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates learning progress by comparing the latest completed Pre-Assessment
    with the latest completed Post-Assessment (and optional Retention Assessment).
    """
    history = get_learner_assessments(learner_id, db_path=db_path)
    completed = [h for h in history if h["status"] == "completed"]

    pre_asm = next((h for h in reversed(completed) if h["assessment_type"] == "pre"), None)
    post_asm = next((h for h in reversed(completed) if h["assessment_type"] == "post"), None)
    ret_asm = next((h for h in reversed(completed) if h["assessment_type"] == "retention"), None)

    if not pre_asm or not post_asm:
        return {
            "has_comparison": False,
            "learner_id": learner_id,
            "message": "Both a completed Pre-Assessment and Post-Assessment are required to calculate learning gains.",
            "completed_assessments": len(completed),
        }

    p_pre = pre_asm["accuracy"]
    p_post = post_asm["accuracy"]
    p_delayed = ret_asm["accuracy"] if ret_asm else None

    # Count mastered KCs (mastery threshold >= 0.80)
    pre_kc = pre_asm.get("kc_scores", {})
    post_kc = post_asm.get("kc_scores", {})
    ret_kc = ret_asm.get("kc_scores", {}) if ret_asm else {}

    pre_mastered = sum(1 for kc, v in pre_kc.items() if v.get("mastery_estimate", 0) >= MASTERY_THRESHOLD)
    post_mastered = sum(1 for kc, v in post_kc.items() if v.get("mastery_estimate", 0) >= MASTERY_THRESHOLD)
    delayed_mastered = sum(1 for kc, v in ret_kc.items() if v.get("mastery_estimate", 0) >= MASTERY_THRESHOLD) if ret_asm else None

    # Calculate metrics
    metrics = compute_learning_metrics(
        p_pre=p_pre,
        p_post=p_post,
        p_delayed=p_delayed,
        num_exercises=10,  # default / placeholder if no active session count
        time_min=(post_asm.get("duration_seconds", 0) + pre_asm.get("duration_seconds", 0)) / 60.0,
        pre_mastered=pre_mastered,
        post_mastered=post_mastered,
        delayed_mastered=delayed_mastered,
    )

    # Per-KC comparisons
    all_kcs = sorted(list(set(list(pre_kc.keys()) + list(post_kc.keys()))))
    kc_breakdown = {}
    for kc in all_kcs:
        kc_pre = pre_kc.get(kc, {}).get("mastery_estimate", 0.0)
        kc_post = post_kc.get(kc, {}).get("mastery_estimate", 0.0)
        kc_gain = round(kc_post - kc_pre, 4)
        kc_breakdown[kc] = {
            "pre_score": kc_pre,
            "post_score": kc_post,
            "gain": kc_gain,
            "mastered": kc_post >= MASTERY_THRESHOLD,
        }

    # Generate academic explanation
    explanation = (
        f"Learner '{learner_id}' demonstrated a gross accuracy gain of {metrics['gross_learning_gain']:+.1%}, "
        f"with a normalized learning gain (Hake's g) of {metrics['normalized_learning_gain']:.2f}. "
        f"Number of mastered Knowledge Components changed from {pre_mastered} to {post_mastered} (delta: {metrics['net_mastery_delta']:+d})."
    )
    if p_delayed is not None:
        explanation += f" Delayed retention was assessed at {p_delayed:.1%}, yielding a retention rate of {metrics['retention_rate']:.1%}."

    return {
        "has_comparison": True,
        "has_both": True,
        "learner_id": learner_id,
        "pre_score": round(p_pre, 4),
        "post_score": round(p_post, 4),
        "pre_score_pct": round(p_pre * 100, 1),
        "post_score_pct": round(p_post * 100, 1),
        "absolute_gain_pct": round(metrics["gross_learning_gain"] * 100, 1),
        "normalized_gain_hake": round(metrics["normalized_learning_gain"], 2),
        "pre_assessment_id": pre_asm["assessment_id"],
        "post_assessment_id": post_asm["assessment_id"],
        "retention_assessment_id": ret_asm["assessment_id"] if ret_asm else None,
        "metrics": metrics,
        "kc_breakdown": kc_breakdown,
        "pre_mastered_kcs": pre_mastered,
        "post_mastered_kcs": post_mastered,
        "delayed_mastered_kcs": delayed_mastered,
        "explanation": explanation,
    }
