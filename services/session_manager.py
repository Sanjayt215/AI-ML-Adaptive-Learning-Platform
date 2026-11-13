"""
Unified Session Management and Assistance Service.
Part of AutoLearn KT-RL Architecture & Assistance Upgrades.

Handles:
1. Persistent SQLite-backed session lifecycle (create, retrieve, restore, expire, complete).
2. Session recovery across page refreshes and server restarts.
3. Controlled responses for expired, completed, or invalid sessions without disabling validation.
4. Unified assistance dispatch:
   - Explain Concept (multi-tier learner mastery adaptation + distractor diagnosis)
   - Show Worked Example (10-point structured pedagogical walkthrough)
   - Need an Easier Step (calibrated foundational exercise)
   - Inspect Prerequisites (DAG dependency status & gap detection)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import TOPIC_CATALOG, get_all_questions, get_question_by_id
from services.learning_store import (
    get_connection,
    get_db_path,
    init_db,
    create_session as create_db_session,
    get_session as get_db_session,
    complete_session as complete_db_session,
    get_learner_events,
)
from services.bkt_service import get_mastery_by_learner
from services.tutor_content import (
    get_concept_explanation,
    get_worked_example,
)

logger = logging.getLogger(__name__)

# Session expiration threshold (24 hours)
SESSION_EXPIRATION_HOURS = 24


def serialize_session_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures sets and non-serializable objects within session state are JSON-safe without mutating the source."""
    if not isinstance(state, dict):
        return state
    res = {}
    for k, v in state.items():
        if isinstance(v, set):
            res[k] = list(v)
        elif isinstance(v, dict):
            res[k] = serialize_session_state(v)
        elif isinstance(v, list):
            res[k] = [list(item) if isinstance(item, set) else item for item in v]
        else:
            res[k] = v
    return res

# Active session cache (in-memory for speed, backed by SQLite)
_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}


def create_unified_session(
    learner_id: str,
    workflow_type: str,
    target_topic: str,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new persistent session in SQLite and registers it in the unified session cache.
    """
    init_db(db_path)
    learner_id = str(learner_id).strip() or "learner_default"
    target_topic = str(target_topic).strip().lower()
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()

    session_id = f"sess_{workflow_type[:4]}_{uuid.uuid4().hex[:10]}"

    meta = dict(metadata or {})
    meta["workflow_type"] = workflow_type
    meta["current_topic"] = target_topic
    meta["presented_item_ids"] = list(meta.get("presented_item_ids", []))

    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO learning_sessions
                (session_id, learner_id, started_at, session_type, status, questions_presented, questions_answered, metadata_json)
                VALUES (?, ?, ?, ?, 'in_progress', 0, 0, ?);
                """,
                (session_id, learner_id, now_iso, f"workflow_{workflow_type}", json.dumps(meta)),
            )
    finally:
        conn.close()

    session_state = {
        "session_id": session_id,
        "learner_id": learner_id,
        "workflow_type": workflow_type,
        "current_topic": target_topic,
        "status": "in_progress",
        "started_at": now_iso,
        "last_active_at": now_iso,
        "presented_item_ids": set(meta["presented_item_ids"]),
        "consecutive_successes": 0,
        "consecutive_errors": 0,
        "questions_answered": 0,
        "questions_correct": 0,
        "metadata": meta,
    }

    _SESSION_CACHE[session_id] = session_state
    return session_state


def get_unified_session(
    session_id: str,
    db_path: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Retrieves and validates an active session:
    Returns (session_dict, None) if valid and in_progress.
    Returns (None, error_dict) if invalid, expired, completed, or not found.
    """
    if not session_id or not str(session_id).strip():
        return None, {
            "ok": False,
            "status": "INVALID_SESSION",
            "error": "Session identifier is missing or invalid. Please start a new session.",
            "recovery_action": "start_new",
        }

    session_id = str(session_id).strip()

    # 1. Check in-memory cache
    if session_id in _SESSION_CACHE:
        state = _SESSION_CACHE[session_id]
        # Check expiry
        try:
            started = datetime.fromisoformat(state["started_at"])
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - started) > timedelta(hours=SESSION_EXPIRATION_HOURS):
                state["status"] = "expired"
                return None, {
                    "ok": False,
                    "status": "EXPIRED",
                    "error": f"Session '{session_id}' has expired (exceeded {SESSION_EXPIRATION_HOURS}h). Please start a new session.",
                    "recovery_action": "restart_session",
                }
        except Exception:
            pass

        if state.get("status") == "completed":
            return None, {
                "ok": False,
                "status": "COMPLETED",
                "error": "This learning session has already been completed. Please start a new session.",
                "recovery_action": "start_new",
            }

        return serialize_session_state(state), None

    # 1b. Check AdaptiveTutorService._ACTIVE_TUTOR_SESSIONS fallback
    try:
        from services.adaptive_tutor import _ACTIVE_TUTOR_SESSIONS
        if session_id in _ACTIVE_TUTOR_SESSIONS:
            tutor_state = _ACTIVE_TUTOR_SESSIONS[session_id]
            _SESSION_CACHE[session_id] = tutor_state
            return tutor_state, None
    except Exception:
        pass

    # 2. Reconstitute from SQLite database
    db_sess = get_db_session(session_id, db_path=db_path)
    if not db_sess:
        return None, {
            "ok": False,
            "status": "NOT_FOUND",
            "error": f"Session '{session_id}' not found. Please select a learning module to begin.",
            "recovery_action": "start_new",
        }

    # Check status in DB
    status = db_sess.get("status", "in_progress")
    if status == "completed":
        return None, {
            "ok": False,
            "status": "COMPLETED",
            "error": "This learning session has already been completed. Please start a new session.",
            "recovery_action": "start_new",
        }

    # Check expiration
    started_str = db_sess.get("started_at")
    if started_str:
        try:
            started = datetime.fromisoformat(started_str)
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - started) > timedelta(hours=SESSION_EXPIRATION_HOURS):
                conn = get_connection(db_path)
                try:
                    with conn:
                        conn.execute("UPDATE learning_sessions SET status = 'expired' WHERE session_id = ?;", (session_id,))
                finally:
                    conn.close()
                return None, {
                    "ok": False,
                    "status": "EXPIRED",
                    "error": f"Session '{session_id}' has expired. Please restart your learning activity.",
                    "recovery_action": "restart_session",
                }
        except Exception:
            pass

    # Reconstitute active state from SQLite
    meta = db_sess.get("metadata", {})
    learner_id = db_sess.get("learner_id", "learner_default")
    events = get_learner_events(learner_id, db_path=db_path)
    session_events = [e for e in events if e.get("session_id") == session_id]

    presented = set(meta.get("presented_item_ids", []))
    for e in session_events:
        if e.get("item_id"):
            presented.add(e["item_id"])

    correct_count = sum(1 for e in session_events if e.get("is_correct"))

    reconstituted = {
        "session_id": session_id,
        "learner_id": learner_id,
        "workflow_type": meta.get("workflow_type", "continue_learning"),
        "current_topic": meta.get("current_topic", "python"),
        "status": "in_progress",
        "started_at": db_sess.get("started_at", datetime.now(timezone.utc).isoformat()),
        "last_active_at": datetime.now(timezone.utc).isoformat(),
        "presented_item_ids": presented,
        "consecutive_successes": 0,
        "consecutive_errors": 0,
        "questions_answered": len(session_events),
        "questions_correct": correct_count,
        "metadata": meta,
    }

    _SESSION_CACHE[session_id] = reconstituted
    return serialize_session_state(reconstituted), None


def complete_unified_session(
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Marks a session completed in both SQLite and cache."""
    session_id = str(session_id).strip()
    complete_db_session(session_id, metadata=metadata, db_path=db_path)
    if session_id in _SESSION_CACHE:
        _SESSION_CACHE[session_id]["status"] = "completed"
    return {"ok": True, "session_id": session_id, "status": "completed"}


# =========================================================================
# UNIFIED ASSISTANCE DISPATCHER
# =========================================================================

def handle_assistance_request(
    session_id: str,
    action: str,  # "explain" | "worked_example" | "easier_step" | "inspect_prerequisites"
    item_id: Optional[str] = None,
    topic: Optional[str] = None,
    learner_id: Optional[str] = None,
    selected_option: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fulfills an on-demand assistance request:
    1. Validates the session. If invalid/expired/completed, returns actionable error.
    2. Identifies topic and question context.
    3. Generates high-quality pedagogical assistance:
       - 'explain': 9-point multi-tier concept explanation with distractor rationale
       - 'worked_example': 10-point step-by-step worked example with code/math
       - 'easier_step': calibrated level 1-2 question
       - 'inspect_prerequisites': DAG dependency status and gap detection
    """
    session_state, err = get_unified_session(session_id, db_path=db_path)
    if err:
        # If session_id was invalid but learner_id and topic are available, allow auto-recovery
        if learner_id and topic:
            logger.info(f"Auto-recovering session for learner {learner_id} on topic {topic}")
            session_state = create_unified_session(
                learner_id=learner_id,
                workflow_type="continue_learning",
                target_topic=topic,
                db_path=db_path,
            )
        else:
            return err

    # Resolve context
    resolved_topic = str(topic or session_state.get("current_topic") or "python").strip().lower()
    resolved_learner = str(learner_id or session_state.get("learner_id") or "learner_default").strip()
    session_state["last_active_at"] = datetime.now(timezone.utc).isoformat()

    # Question metadata if item_id provided
    q_meta = get_question_by_id(item_id) if item_id else None
    if q_meta and q_meta.get("topic"):
        resolved_topic = q_meta["topic"]

    # Learner's current BKT mastery
    mastery_info = get_mastery_by_learner(resolved_learner, db_path=db_path)
    bkt_p = mastery_info.get("topics_map", {}).get(resolved_topic, {}).get("mastery_probability", 0.50)

    # ─────────────────────────────────────────────────────────────
    # 1. EXPLAIN CONCEPT (9-Point Structured Multi-Tier Explanation)
    # ─────────────────────────────────────────────────────────────
    if action in ("explain", "concept_explanation"):
        exp = get_concept_explanation(resolved_topic)

        # Determine learner tone tier
        if bkt_p < 0.45:
            level_tier = "Beginner (Intuitive Foundations)"
            tier_note = "Focus on the core concept definition and real-world analogy before delving into formulas."
        elif bkt_p < 0.75:
            level_tier = "Intermediate (Mechanism & Algorithmic Steps)"
            tier_note = "Understand how the algorithm transforms input representations into outputs."
        else:
            level_tier = "Advanced (Mathematical & Optimization Rigor)"
            tier_note = "Analyze mathematical assumptions, trade-offs, regularization, and computational complexity."

        # Distractor specific feedback if student chose a specific wrong option
        distractor_note = None
        if q_meta and selected_option:
            distractors = q_meta.get("distractor_explanations", {})
            distractor_note = distractors.get(selected_option)

        content_payload = {
            "title": f"Concept Mastery: {resolved_topic.replace('_', ' ').title()}",
            "topic": resolved_topic,
            "definition": exp.get("concept_summary", f"Core formulation of {resolved_topic.replace('_', ' ')}."),
            "why_it_matters": (
                f"Mastering {resolved_topic.replace('_', ' ')} is essential for building robust machine learning pipelines "
                f"and avoiding common pitfalls like overfitting, data leakage, and high variance."
            ),
            "step_by_step_reasoning": exp.get("key_points", [
                "1. Identify input feature representations and target objectives.",
                "2. Apply appropriate statistical or algorithmic transformations.",
                "3. Validate model outputs and evaluate performance metrics."
            ]),
            "formula_or_syntax": exp.get("key_formula", "y = f(x; θ)"),
            "common_misconceptions": exp.get("common_pitfalls", "Applying the model without checking feature distributions."),
            "learner_level_adaptation": {
                "tier": level_tier,
                "current_mastery_pct": round(bkt_p * 100, 1),
                "guidance": tier_note,
            },
            "short_summary": f"{resolved_topic.replace('_', ' ').title()} enables systematic learning of patterns from empirical data.",
            "check_question": {
                "question": f"What is the primary objective of {resolved_topic.replace('_', ' ')}?",
                "options": [
                    f"Model patterns and make reliable predictions in {resolved_topic.replace('_', ' ')}",
                    "Randomly shuffle data without evaluating loss",
                    "Hardcode prediction rules manually",
                    "Ignore validation performance"
                ],
                "answer": f"Model patterns and make reliable predictions in {resolved_topic.replace('_', ' ')}",
                "hint": "Focus on pattern generalization to unseen test distributions."
            }
        }

        if q_meta:
            content_payload["question_context"] = {
                "question": q_meta.get("question"),
                "correct_answer": q_meta.get("answer"),
                "explanation": q_meta.get("explanation"),
                "distractor_insight": distractor_note,
            }

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "concept_explanation",
            "topic": resolved_topic,
            "title": content_payload["title"],
            "content": content_payload,
        }

    # ─────────────────────────────────────────────────────────────
    # 2. SHOW WORKED EXAMPLE (10-Point Step-by-Step Walkthrough)
    # ─────────────────────────────────────────────────────────────
    elif action in ("worked_example", "show_worked_example"):
        ex = get_worked_example(resolved_topic)
        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "worked_example",
            "topic": resolved_topic,
            "title": ex.get("title", f"Worked Example: {resolved_topic.replace('_', ' ').title()}"),
            "worked_example": {
                "problem_statement": ex.get("problem", f"Step-by-step guided analysis for {resolved_topic.replace('_', ' ')}."),
                "concept": resolved_topic,
                "steps": ex.get("steps", []),
                "key_takeaway": ex.get("key_takeaway", "Systematic evaluation prevents hidden data leakage."),
                "check_question": ex.get("check_question"),
            },
        }

    # ─────────────────────────────────────────────────────────────
    # 3. NEED AN EASIER STEP (Level 1-2 Foundational Exercise)
    # ─────────────────────────────────────────────────────────────
    elif action in ("easier_step", "easier_question"):
        all_q = get_all_questions()
        presented = session_state.get("presented_item_ids")
        if not isinstance(presented, set):
            presented = set(presented or [])
            session_state["presented_item_ids"] = presented
        if item_id:
            presented.add(item_id)

        # Find questions with difficulty 1 or 2
        candidates = [
            q for q in all_q
            if (q.get("topic") == resolved_topic or resolved_topic in q.get("knowledge_components", []))
            and q.get("difficulty", 2) <= 2
            and q.get("item_id") not in presented
        ]

        if not candidates:
            # Look for foundational prerequisites
            prereqs = TOPIC_CATALOG.get(resolved_topic, {}).get("prerequisites", [])
            for p in prereqs:
                p_cands = [
                    q for q in all_q
                    if (q.get("topic") == p or p in q.get("knowledge_components", []))
                    and q.get("item_id") not in presented
                ]
                if p_cands:
                    candidates = p_cands
                    resolved_topic = p
                    break

        if not candidates:
            # Fallback to any unseen easy question
            candidates = [q for q in all_q if q.get("difficulty", 2) <= 2 and q.get("item_id") not in presented]

        chosen = candidates[0] if candidates else all_q[0]
        presented.add(chosen["item_id"])

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "easier_question",
            "topic": chosen.get("topic", resolved_topic),
            "rationale": (
                f"Switched to a guided Level {chosen.get('difficulty', 1)} exercise on '{chosen.get('topic', resolved_topic).replace('_', ' ')}' "
                f"to strengthen fundamental concepts before advancing to higher complexity."
            ),
            "question": {
                "item_id": chosen["item_id"],
                "question": chosen["question"],
                "options": chosen["options"],
                "difficulty": chosen.get("difficulty", 1),
                "topic": chosen.get("topic", resolved_topic),
            },
        }

    # ─────────────────────────────────────────────────────────────
    # 4. INSPECT PREREQUISITES (DAG Dependency Status & Gap Analysis)
    # ─────────────────────────────────────────────────────────────
    elif action in ("inspect_prerequisites", "prereq_help", "prerequisites"):
        prereqs = TOPIC_CATALOG.get(resolved_topic, {}).get("prerequisites", [])
        prereq_status_list = []
        has_gap = False

        for p in prereqs:
            p_clean = str(p).strip().lower()
            p_mastery = mastery_info.get("topics_map", {}).get(p_clean, {}).get("mastery_probability", 0.20)
            p_pct = round(p_mastery * 100, 1)

            if p_mastery >= 0.75:
                status_label = "Mastered"
                badge_color = "green"
            elif p_mastery >= 0.50:
                status_label = "In Progress"
                badge_color = "amber"
            else:
                status_label = "Gap / Deficient"
                badge_color = "red"
                has_gap = True

            prereq_status_list.append({
                "topic": p_clean,
                "title": p_clean.replace("_", " ").title(),
                "mastery_probability": p_mastery,
                "mastery_pct": p_pct,
                "status": status_label,
                "badge_color": badge_color,
                "description": TOPIC_CATALOG.get(p_clean, {}).get("description", "Foundational machine learning concept."),
            })

        recommendation = (
            f"All prerequisite concepts for '{resolved_topic.replace('_', ' ')}' are satisfied. You are ready for optimal challenge."
            if not has_gap else
            f"Prerequisite gap detected! Reviewing foundational concepts marked in red will resolve repeated difficulties."
        )

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "inspect_prerequisites",
            "target_topic": resolved_topic,
            "target_topic_mastery_pct": round(bkt_p * 100, 1),
            "prerequisites": prereq_status_list,
            "has_prerequisite_gap": has_gap,
            "recommendation": recommendation,
        }

    # ─────────────────────────────────────────────────────────────
    # 5. EXPLAIN WHY MY ANSWER IS WRONG (Distractor Misconception)
    # ─────────────────────────────────────────────────────────────
    elif action in ("explain_wrong", "why_wrong", "misconception"):
        selected = str(selected_option or "").strip()
        explanation_text = None
        if q_meta and selected:
            distractors = q_meta.get("distractor_explanations", {})
            explanation_text = distractors.get(selected)

        if not explanation_text:
            correct_ans = q_meta.get("correct_answer") or q_meta.get("answer") if q_meta else "the correct concept"
            explanation_text = (
                f"Selecting '{selected or 'this option'}' represents a common misconception in {resolved_topic.replace('_', ' ')}. "
                f"The correct foundation is '{correct_ans}'. Review the core definition: "
                f"{q_meta.get('explanation', 'Verify the algorithmic transformation and mathematical assumptions.') if q_meta else 'Verify assumptions.'}"
            )

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "explain_wrong",
            "topic": resolved_topic,
            "selected_option": selected,
            "correct_answer": q_meta.get("correct_answer") if q_meta else None,
            "misconception_analysis": explanation_text,
            "recovery_tip": f"When evaluating {resolved_topic.replace('_', ' ')}, trace the intermediate representations before selecting an answer.",
        }

    # ─────────────────────────────────────────────────────────────
    # 6. GIVE ME A HINT (Graduated Multi-Tier Scaffolding)
    # ─────────────────────────────────────────────────────────────
    elif action in ("give_hint", "hint"):
        q_text = q_meta.get("question", "") if q_meta else resolved_topic
        hint_tier_1 = f"Identify the core learning objective: this exercise tests key mechanics of {resolved_topic.replace('_', ' ').title()}."
        hint_tier_2 = "Eliminate distractors that confuse training optimization with inference evaluation or scale parameters incorrectly."
        hint_tier_3 = (
            q_meta.get("explanation", "").split(".")[0] + "."
            if q_meta and q_meta.get("explanation")
            else f"Remember that {resolved_topic.replace('_', ' ')} optimizes the objective function under specific inductive biases."
        )

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "give_hint",
            "topic": resolved_topic,
            "hints": [
                {"tier": 1, "title": "Conceptual Clue", "hint": hint_tier_1},
                {"tier": 2, "title": "Elimination Clue", "hint": hint_tier_2},
                {"tier": 3, "title": "Algorithmic Rule", "hint": hint_tier_3},
            ],
        }

    # ─────────────────────────────────────────────────────────────
    # 7. TEST MY UNDERSTANDING / ASK A FOLLOW-UP QUESTION
    # ─────────────────────────────────────────────────────────────
    elif action in ("test_understanding", "follow_up_question", "ask_follow_up"):
        all_q = get_all_questions()
        presented = session_state.get("presented_item_ids")
        if not isinstance(presented, set):
            presented = set(presented or [])
            session_state["presented_item_ids"] = presented
        if item_id:
            presented.add(item_id)

        candidates = [
            q for q in all_q
            if (q.get("topic") == resolved_topic or resolved_topic in q.get("knowledge_components", []))
            and q.get("item_id") not in presented
        ]
        if not candidates:
            candidates = [q for q in all_q if q.get("item_id") not in presented]
        chosen = candidates[0] if candidates else (q_meta or all_q[0])
        presented.add(chosen["item_id"])

        return {
            "ok": True,
            "session_id": session_state["session_id"],
            "action_type": "test_understanding",
            "topic": resolved_topic,
            "follow_up_prompt": f"Let's test if you've internalized '{resolved_topic.replace('_', ' ')}'. Solve this related challenge:",
            "question": {
                "item_id": chosen["item_id"],
                "question": chosen["question"],
                "options": chosen["options"],
                "difficulty": chosen.get("difficulty", 2),
                "topic": chosen.get("topic", resolved_topic),
            },
        }

    return {
        "ok": False,
        "error": f"Unknown assistance action '{action}'. Supported actions: explain, worked_example, easier_step, inspect_prerequisites, explain_wrong, give_hint, test_understanding.",
    }
