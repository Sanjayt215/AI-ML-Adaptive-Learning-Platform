"""
Smart Exam Preparation Planning Service.
Part of KT-RL Personalized Learning Assistant.

Generates and dynamically manages customized day-by-day study schedules:
1. Inputs: Target syllabus topics, exam date, and daily study availability (minutes/day).
2. Topological Prerequisite Ordering: Schedules foundational topics before advanced concepts.
3. Multi-Phase Structure:
   - Phase 1 (Core Concepts): Diagnostic exploration & targeted practice.
   - Phase 2 (Reinforcement): Interleaved review & weak prerequisite repair.
   - Phase 3 (Mock Readiness): Timed mock tests & comprehensive revision.
4. Dynamic Rebalancing: Adjusts remaining study days based on observed performance & availability changes.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.learning_store import get_connection, get_db_path
from services.curriculum_planner import CurriculumPlanner
from services.bkt_service import get_mastery_by_learner

logger = logging.getLogger(__name__)


def init_exam_tables(db_path: Optional[str] = None) -> None:
    """Initializes SQLite tables for personalized exam preparation plans."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS exam_plans (
                    plan_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    exam_name TEXT NOT NULL,
                    exam_date TEXT NOT NULL,
                    daily_minutes INTEGER NOT NULL,
                    syllabus_topics_json TEXT NOT NULL,
                    plan_data_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_exam_learner ON exam_plans(learner_id);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_exam_status ON exam_plans(status);"
            )
    finally:
        conn.close()


def create_smart_exam_plan(
    learner_id: str,
    exam_name: str,
    exam_date: str,
    daily_minutes: int = 45,
    syllabus_topics: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a personalized, prerequisite-ordered day-by-day exam preparation schedule.
    """
    init_exam_tables(db_path)
    learner_id = str(learner_id).strip()
    exam_name = str(exam_name).strip() or "Upcoming AI/ML Examination"
    daily_minutes = max(15, min(int(daily_minutes or 45), 240))

    # Parse target exam date
    try:
        exam_dt = datetime.strptime(str(exam_date).strip()[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        # Default to 14 days from now if invalid
        exam_dt = datetime.now(timezone.utc) + timedelta(days=14)

    now = datetime.now(timezone.utc)
    days_remaining = max(1, (exam_dt.date() - now.date()).days)

    # Topological sorting of syllabus topics
    planner = CurriculumPlanner()
    all_ordered = planner.topological_order

    if not syllabus_topics:
        # Default to first 10 foundational and core topics
        selected_topics = all_ordered[:10]
    else:
        clean_input = {str(t).strip().lower() for t in syllabus_topics}
        selected_topics = [t for t in all_ordered if t in clean_input]
        if not selected_topics:
            selected_topics = all_ordered[:8]

    # Generate Day-by-Day schedule
    schedule: List[Dict[str, Any]] = []

    # Distribute topics across available days
    # Days 1 to N-2: Core study & practice
    # Day N-1: Targeted weak-point consolidation
    # Day N: Final mock exam & readiness review
    core_days = max(1, days_remaining - 2) if days_remaining > 2 else days_remaining
    topics_per_day = max(1, len(selected_topics) / core_days)

    topic_idx = 0
    for day_num in range(1, days_remaining + 1):
        target_date = (now + timedelta(days=day_num - 1)).strftime("%Y-%m-%d")

        if day_num == days_remaining and days_remaining >= 3:
            # Final Day: Full Mock Examination
            schedule.append({
                "activity_id": f"act_mock_{day_num}_{uuid.uuid4().hex[:6]}",
                "day_number": day_num,
                "date": target_date,
                "topic": "all_syllabus",
                "activity_type": "mock_exam",
                "title": "Comprehensive Mock Exam & Readiness Check",
                "description": f"Timed diagnostic assessment covering all {len(selected_topics)} syllabus topics under exam conditions.",
                "target_duration_mins": daily_minutes,
                "status": "pending",
                "score": None,
                "completed_at": None,
            })
        elif day_num == days_remaining - 1 and days_remaining >= 4:
            # Penultimate Day: High-Priority Review
            schedule.append({
                "activity_id": f"act_rev_{day_num}_{uuid.uuid4().hex[:6]}",
                "day_number": day_num,
                "date": target_date,
                "topic": "weak_review",
                "activity_type": "spaced_revision",
                "title": "Weak Topic Consolidation & Formula Review",
                "description": "Reinforce struggling topics and review key formulas and worked examples.",
                "target_duration_mins": daily_minutes,
                "status": "pending",
                "score": None,
                "completed_at": None,
            })
        else:
            # Core Learning & Practice Day
            curr_topic = selected_topics[min(int(topic_idx), len(selected_topics) - 1)]
            topic_idx += topics_per_day

            schedule.append({
                "activity_id": f"act_core_{day_num}_{uuid.uuid4().hex[:6]}",
                "day_number": day_num,
                "date": target_date,
                "topic": curr_topic,
                "activity_type": "core_practice",
                "title": f"Mastery & Practice: {curr_topic.replace('_', ' ').title()}",
                "description": f"Adaptive practice questions, concept review, and step-by-step problem solving for {curr_topic.replace('_', ' ')}.",
                "target_duration_mins": daily_minutes,
                "status": "pending",
                "score": None,
                "completed_at": None,
            })

    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    created_at = now.isoformat()

    conn = get_connection(db_path)
    try:
        with conn:
            # Mark any previous active plan as archived
            conn.execute(
                "UPDATE exam_plans SET status = 'archived', updated_at = ? WHERE learner_id = ? AND status = 'active'",
                (created_at, learner_id)
            )
            conn.execute(
                """
                INSERT INTO exam_plans (
                    plan_id, learner_id, exam_name, exam_date, daily_minutes,
                    syllabus_topics_json, plan_data_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?);
                """,
                (
                    plan_id,
                    learner_id,
                    exam_name,
                    exam_dt.strftime("%Y-%m-%d"),
                    daily_minutes,
                    json.dumps(selected_topics),
                    json.dumps(schedule),
                    created_at,
                    created_at,
                )
            )
    finally:
        conn.close()

    return {
        "ok": True,
        "plan_id": plan_id,
        "learner_id": learner_id,
        "exam_name": exam_name,
        "exam_date": exam_dt.strftime("%Y-%m-%d"),
        "days_remaining": days_remaining,
        "daily_minutes": daily_minutes,
        "total_syllabus_topics": len(selected_topics),
        "syllabus_topics": selected_topics,
        "schedule": schedule,
        "created_at": created_at,
    }


def get_smart_exam_plan(learner_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves the active exam preparation plan with dynamic progress tracking."""
    init_exam_tables(db_path)
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT plan_id, learner_id, exam_name, exam_date, daily_minutes,
                   syllabus_topics_json, plan_data_json, status, created_at, updated_at
            FROM exam_plans
            WHERE learner_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1;
            """,
            (learner_id,)
        ).fetchone()

        if not row:
            return None

        schedule: List[Dict[str, Any]] = json.loads(row["plan_data_json"])
        syllabus: List[str] = json.loads(row["syllabus_topics_json"])
        exam_dt = datetime.strptime(row["exam_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_remaining = max(0, (exam_dt.date() - now.date()).days)

        completed_count = sum(1 for a in schedule if a.get("status") == "completed")
        total_activities = len(schedule)
        progress_pct = round((completed_count / max(1, total_activities)) * 100, 1)

        # Identify today's active activity
        today_str = now.strftime("%Y-%m-%d")
        today_activity = next(
            (a for a in schedule if a.get("date") == today_str and a.get("status") != "completed"),
            next((a for a in schedule if a.get("status") != "completed"), None)
        )

        return {
            "ok": True,
            "plan_id": row["plan_id"],
            "learner_id": row["learner_id"],
            "exam_name": row["exam_name"],
            "exam_date": row["exam_date"],
            "days_remaining": days_remaining,
            "daily_minutes": row["daily_minutes"],
            "syllabus_topics": syllabus,
            "schedule": schedule,
            "progress_pct": progress_pct,
            "completed_activities": completed_count,
            "total_activities": total_activities,
            "today_activity": today_activity,
            "updated_at": row["updated_at"],
        }
    finally:
        conn.close()


def rebalance_exam_plan(
    learner_id: str,
    plan_id: str,
    new_daily_minutes: Optional[int] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Dynamically rebalances remaining study days based on current BKT mastery
    and any changes in daily availability.
    """
    plan = get_smart_exam_plan(learner_id, db_path=db_path)
    if not plan or plan["plan_id"] != plan_id:
        return {"ok": False, "error": "Active plan not found"}

    schedule: List[Dict[str, Any]] = plan["schedule"]
    now = datetime.now(timezone.utc)

    # 1. Fetch current BKT mastery
    mastery_info = get_mastery_by_learner(learner_id, db_path=db_path)
    bkt_map = mastery_info.get("topics_map", {})

    # 2. Identify remaining uncompleted activities
    pending = [a for a in schedule if a.get("status") != "completed"]
    if not pending:
        return {"ok": True, "message": "All activities already completed", "plan": plan}

    # 3. Find weak syllabus topics (P(K) < 0.60)
    weak_topics = []
    for t in plan["syllabus_topics"]:
        m = bkt_map.get(t, {}).get("mastery_probability", 0.20)
        if m < 0.60:
            weak_topics.append(t)

    # 4. Re-allocate pending activities prioritizing weak topics
    if new_daily_minutes:
        daily_mins = max(15, min(int(new_daily_minutes), 240))
    else:
        daily_mins = plan["daily_minutes"]

    for i, act in enumerate(pending):
        act["target_duration_mins"] = daily_mins
        # If there are weak topics and this is not a mock exam, adjust topic focus
        if weak_topics and act.get("activity_type") != "mock_exam" and i < len(weak_topics):
            weak_t = weak_topics[i % len(weak_topics)]
            act["topic"] = weak_t
            act["title"] = f"Priority Reinforcement: {weak_t.replace('_', ' ').title()}"
            act["description"] = f"Remedial focus: your current understanding is below threshold. Strengthening core concepts."

    updated_at = now.isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                UPDATE exam_plans
                SET daily_minutes = ?, plan_data_json = ?, updated_at = ?
                WHERE plan_id = ?;
                """,
                (daily_mins, json.dumps(schedule), updated_at, plan_id)
            )
    finally:
        conn.close()

    plan["schedule"] = schedule
    plan["daily_minutes"] = daily_mins
    plan["rebalanced"] = True
    plan["weak_topics_prioritized"] = weak_topics
    return {"ok": True, "plan": plan}


def complete_exam_activity(
    learner_id: str,
    plan_id: str,
    activity_id: str,
    score: Optional[float] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Marks a scheduled exam preparation activity as completed."""
    plan = get_smart_exam_plan(learner_id, db_path=db_path)
    if not plan or plan["plan_id"] != plan_id:
        return {"ok": False, "error": "Active plan not found"}

    schedule: List[Dict[str, Any]] = plan["schedule"]
    found = False
    now = datetime.now(timezone.utc)

    for act in schedule:
        if act.get("activity_id") == activity_id:
            act["status"] = "completed"
            act["score"] = score
            act["completed_at"] = now.isoformat()
            found = True
            break

    if not found:
        return {"ok": False, "error": f"Activity '{activity_id}' not found in plan"}

    updated_at = now.isoformat()
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                "UPDATE exam_plans SET plan_data_json = ?, updated_at = ? WHERE plan_id = ?;",
                (json.dumps(schedule), updated_at, plan_id)
            )
    finally:
        conn.close()

    return {"ok": True, "activity_id": activity_id, "status": "completed"}
