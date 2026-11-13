"""
Adaptive Personal Tutor Service.
Part of KT-RL Student-Facing Personalized Learning Assistant.

Integrates:
1. Complete Adaptive Learning Loop: Select topic -> Question -> Answer -> BKT Update -> Policy Action.
2. Prerequisite Repair: Detects when student failure stems from weak upstream DAG prerequisites (P(K) < 0.60),
   delivers targeted prerequisite remediation, and reassesses the original concept.
3. Learning Difficulty Rescue Mode: Activates on repeated failure (2 consecutive errors) with simpler
   worked examples, guided problem-solving, and stepped-down difficulty.
4. Smart Exam Prep & Revision Bridges: Seamlessly connects with ExamPlanner and SpacedRepetitionScheduler.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import TOPIC_CATALOG, get_all_questions, get_question_by_id
from services.bkt_service import get_mastery_by_learner, get_kc_mastery
from services.learning_store import create_session, log_event, get_learner_events
from services.adaptive_recommender import UnifiedAdaptiveRecommender
from services.curriculum_planner import CurriculumPlanner
from services.spaced_repetition import SpacedRepetitionScheduler
from services.tutor_content import get_concept_explanation, get_worked_example

logger = logging.getLogger(__name__)

# Active In-Memory Tutor Sessions cache
_ACTIVE_TUTOR_SESSIONS: Dict[str, Dict[str, Any]] = {}


class TutorActionType(str, Enum):
    PRACTICE_QUESTION = "practice_question"
    WORKED_EXAMPLE = "worked_example"
    CONCEPT_EXPLANATION = "concept_explanation"
    PREREQUISITE_REPAIR = "prerequisite_repair"
    EASIER_QUESTION = "easier_question"
    CHALLENGE_QUESTION = "challenge_question"


class AdaptiveTutorService:
    """Coordinates personalized student learning, prerequisite repair, and rescue mode."""

    def __init__(self):
        self.recommender = UnifiedAdaptiveRecommender()
        self.curriculum = CurriculumPlanner()
        self.all_questions = get_all_questions()

    def start_tutor_session(
        self,
        learner_id: str,
        mode: str = "continue",  # "continue" | "weak_topics" | "exam_prep" | "revision"
        topic: Optional[str] = None,
        exam_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initializes an adaptive tutor session based on one of the 4 student entry points.
        """
        learner_id = str(learner_id).strip() or "learner_default"
        session_id = f"tut_sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # 1. Fetch learner BKT mastery and past learning events
        mastery_info = get_mastery_by_learner(learner_id)
        bkt_map = mastery_info.get("topics_map", {})
        learner_events = get_learner_events(learner_id, limit=200, reverse=False)

        # 2. Select initial target topic according to entry point mode
        selected_topic = "python"
        target_activity_meta = {}

        if mode == "weak_topics":
            if topic:
                selected_topic = str(topic).strip().lower()
                target_activity_meta["reason"] = f"Focused on strengthening selected concept ({selected_topic.replace('_', ' ').title()})."
            else:
                # 1) Check assessed topics with lowest BKT mastery
                assessed_topics = [
                    (t, data.get("mastery_probability", 0.20))
                    for t, data in bkt_map.items()
                    if data.get("status") == "assessed"
                ]
                if assessed_topics:
                    assessed_topics.sort(key=lambda x: x[1])
                    selected_topic = assessed_topics[0][0]
                    target_activity_meta["reason"] = f"Focused on strengthening your weakest assessed concept ({selected_topic.replace('_', ' ').title()})."
                elif learner_events:
                    # 2) Check error rates from past interactions
                    err_counts = {}
                    tot_counts = {}
                    for ev in learner_events:
                        t = ev.get("topic")
                        if t:
                            tot_counts[t] = tot_counts.get(t, 0) + 1
                            if not ev.get("is_correct"):
                                err_counts[t] = err_counts.get(t, 0) + 1
                    err_rates = [
                        (t, err_counts.get(t, 0) / tot_counts[t])
                        for t in tot_counts if tot_counts[t] >= 2
                    ]
                    if err_rates:
                        err_rates.sort(key=lambda x: x[1], reverse=True)
                        selected_topic = err_rates[0][0]
                        target_activity_meta["reason"] = f"Targeted review for '{selected_topic.replace('_', ' ').title()}' where your recent error rate was {Math_round_pct(err_rates[0][1])}%."
                    else:
                        selected_topic = "data preprocessing"
                        target_activity_meta["diagnostic"] = True
                        target_activity_meta["reason"] = "Diagnostic Baseline: Evaluating core data preprocessing foundations to identify baseline knowledge gaps."
                else:
                    # 3) Brand-new learner without assessments: deliver diagnostic baseline on Data Preprocessing
                    selected_topic = "data preprocessing"
                    target_activity_meta["diagnostic"] = True
                    target_activity_meta["reason"] = "Diagnostic Baseline: Evaluating core data preprocessing foundations to identify baseline knowledge gaps."

        elif mode == "revision":
            if topic:
                selected_topic = str(topic).strip().lower()
                target_activity_meta["reason"] = f"Revision scheduled to reinforce long-term memory for {selected_topic.replace('_', ' ').title()}."
            else:
                # Hydrate spaced repetition scheduler with actual practice history
                scheduler = SpacedRepetitionScheduler()
                for idx, ev in enumerate(learner_events):
                    scheduler.record_practice(
                        kc_id=ev.get("topic", ""),
                        current_step=idx + 1,
                        is_correct=bool(ev.get("is_correct", False)),
                    )
                due = scheduler.get_due_topics(current_step=max(len(learner_events) + 5, 10))
                if due:
                    selected_topic = due[0][0]
                    retrieval_pct = Math_round_pct(due[0][1])
                    target_activity_meta["retrievability_pct"] = retrieval_pct
                    target_activity_meta["reason"] = f"Spaced Repetition: Reinforcing '{selected_topic.replace('_', ' ').title()}' where estimated retention has decayed to {retrieval_pct}%."
                elif learner_events:
                    all_practiced = list(dict.fromkeys(ev.get("topic") for ev in learner_events if ev.get("topic")))
                    selected_topic = all_practiced[0] if all_practiced else "statistics"
                    target_activity_meta["reason"] = f"Retention check for previously practiced topic ({selected_topic.replace('_', ' ').title()})."
                else:
                    # Brand-new learner: foundational retention review
                    selected_topic = "statistics"
                    target_activity_meta["reason"] = "Retention Baseline: Reinforcing foundational statistical reasoning for machine learning."

        elif mode == "exam_prep":
            # Query active exam plan if available
            from services.exam_planner import get_smart_exam_plan
            plan = get_smart_exam_plan(learner_id)
            if plan and plan.get("today_activity"):
                act = plan["today_activity"]
                act_topic = act.get("topic")
                if act_topic and act_topic != "all_syllabus" and act_topic != "weak_review":
                    selected_topic = act_topic
                else:
                    selected_topic = plan["syllabus_topics"][0]
                target_activity_meta["exam_activity"] = act
                target_activity_meta["exam_name"] = plan.get("exam_name")
                target_activity_meta["days_remaining"] = plan.get("days_remaining")
                target_activity_meta["reason"] = f"Aligned with your exam study schedule for {selected_topic.replace('_', ' ').title()} ({plan.get('exam_name')})."
            else:
                if topic:
                    selected_topic = str(topic).strip().lower()
                else:
                    # High-weight analytical exam topic
                    selected_topic = "linear regression"
                target_activity_meta["reason"] = f"Exam Readiness Practice: Core problem solving on {selected_topic.replace('_', ' ').title()}."
                target_activity_meta["prompt_setup"] = True

        else:  # "continue" (Default)
            if topic:
                selected_topic = str(topic).strip().lower()
                target_activity_meta["reason"] = f"Continuing targeted practice on {selected_topic.replace('_', ' ').title()}."
            else:
                valid_past_events = [e for e in learner_events if e.get("topic")]
                if valid_past_events:
                    last_topic = valid_past_events[-1].get("topic")
                    last_mastery = bkt_map.get(last_topic, {}).get("mastery_probability", 0.20)
                    if last_mastery >= 0.75:
                        cur_idx = self.curriculum.topological_order.index(last_topic) if last_topic in self.curriculum.topological_order else -1
                        if 0 <= cur_idx < len(self.curriculum.topological_order) - 1:
                            selected_topic = self.curriculum.topological_order[cur_idx + 1]
                        else:
                            selected_topic = last_topic or self.curriculum.topological_order[0]
                        target_activity_meta["reason"] = f"Advancing along your prerequisite path to {selected_topic.replace('_', ' ').title()} (previous concept mastered at {Math_round_pct(last_mastery)}%)."
                    else:
                        selected_topic = last_topic or self.curriculum.topological_order[0]
                        target_activity_meta["reason"] = f"Continuing targeted practice on {selected_topic.replace('_', ' ').title()} (current mastery {Math_round_pct(last_mastery)}%)."
                else:
                    plan = self.curriculum.generate_curriculum_plan(learner_id=learner_id)
                    stages = plan.get("stages", [])
                    found_topic = None
                    for st in stages:
                        for t in st.get("topics", []):
                            if t.get("status") in ("ready", "in_progress"):
                                found_topic = t.get("topic")
                                break
                        if found_topic:
                            break
                    selected_topic = found_topic or self.curriculum.topological_order[0]
                    target_activity_meta["reason"] = f"Starting your prerequisite learning path with foundational {selected_topic.replace('_', ' ').title()}."

        # 3. Create persistent learning session in SQLite
        db_sess = create_session(
            learner_id=learner_id,
            session_type=f"tutor_{mode}",
            metadata={"initial_topic": selected_topic, "mode": mode}
        )

        # 4. Initialize session state
        session_state = {
            "session_id": session_id,
            "db_session_id": db_sess["session_id"],
            "learner_id": learner_id,
            "mode": mode,
            "current_topic": selected_topic,
            "consecutive_errors": 0,
            "consecutive_successes": 0,
            "in_prerequisite_repair": False,
            "repair_target_topic": None,
            "repair_prereq_topic": None,
            "in_rescue_mode": False,
            "questions_answered": 0,
            "questions_correct": 0,
            "presented_item_ids": set(),
            "history": [],
            "started_at": now.isoformat(),
        }
        _ACTIVE_TUTOR_SESSIONS[session_id] = session_state
        try:
            from services.session_manager import _SESSION_CACHE, register_db_session
            _SESSION_CACHE[session_id] = session_state
            register_db_session(session_id, learner_id, mode, {"current_topic": selected_topic})
        except Exception:
            pass

        # 5. Fetch first educational action
        action_data = self._select_next_action(session_state)
        # Track initial question if present
        first_q = action_data.get("question") or action_data.get("practice_question")
        if first_q and first_q.get("item_id"):
            session_state["presented_item_ids"].add(first_q["item_id"])
        return {
            "ok": True,
            "session_id": session_id,
            "mode": mode,
            "current_topic": selected_topic,
            "meta": target_activity_meta,
            "action": action_data,
        }

    def process_student_step(
        self,
        session_id: str,
        item_id: str,
        selected_option: str,
        response_time_ms: int = 2000,
    ) -> Dict[str, Any]:
        """
        Processes student's answer submission:
        1. Evaluates correctness against canonical question bank.
        2. Logs learning event to SQLite interaction store.
        3. Updates Bayesian Knowledge Tracing posterior state.
        4. Triggers Prerequisite Repair if upstream prerequisite is weak.
        5. Triggers Rescue Mode (simpler worked example) on repeated errors.
        6. Selects the next policy action.
        """
        session_state = _ACTIVE_TUTOR_SESSIONS.get(session_id)
        if not session_state:
            return {"ok": False, "error": f"Session '{session_id}' not found. Please restart session."}

        learner_id = session_state["learner_id"]
        q = get_question_by_id(item_id)
        if not q:
            return {"ok": False, "error": f"Question '{item_id}' not found"}

        correct_answer = q.get("answer") or q.get("correct_answer") or ""
        is_correct = (selected_option.strip().lower() == correct_answer.strip().lower())
        topic = q.get("topic") or session_state["current_topic"]
        difficulty = q.get("difficulty", 2)

        # 1. Update session counters
        session_state["questions_answered"] += 1
        presented = session_state.setdefault("presented_item_ids", set())
        presented.add(item_id)
        if is_correct:
            session_state["questions_correct"] += 1
            session_state["consecutive_successes"] += 1
            session_state["consecutive_errors"] = 0
        else:
            session_state["consecutive_errors"] += 1
            session_state["consecutive_successes"] = 0

        # 2. Log learning event in SQLite
        try:
            log_event(
                session_id=session_state["db_session_id"],
                learner_id=learner_id,
                item_id=item_id,
                knowledge_components=q.get("knowledge_components", [topic]),
                submitted_answer=selected_option,
                correctness=1 if is_correct else 0,
                response_time_ms=response_time_ms,
                attempt_number=1,
                interaction_type="adaptive_tutor",
                metadata={"topic": topic, "difficulty": difficulty, "session_mode": session_state["mode"]},
            )
        except Exception as log_err:
            logger.warning(f"Error logging tutor step event: {log_err}")

        # 3. Read updated BKT mastery
        updated_bkt = get_kc_mastery(learner_id, topic)

        # 4. Immediate feedback payload
        feedback = {
            "is_correct": is_correct,
            "submitted_answer": selected_option,
            "correct_answer": correct_answer,
            "explanation": q.get("explanation") or f"The correct answer is '{correct_answer}'.",
            "topic": topic,
            "updated_mastery_pct": Math_round_pct(updated_bkt.get("mastery_probability", 0.20)),
        }

        # 5. Check if we just completed a Prerequisite Repair
        if session_state.get("in_prerequisite_repair") and is_correct:
            # Successfully passed prerequisite practice! Return to original topic
            orig_topic = session_state.get("repair_target_topic")
            prereq_topic = session_state.get("repair_prereq_topic")
            session_state["in_prerequisite_repair"] = False
            session_state["current_topic"] = orig_topic
            session_state["consecutive_errors"] = 0
            feedback["transition_message"] = (
                f"Excellent! You've strengthened prerequisite concept '{prereq_topic.replace('_', ' ')}'. "
                f"Now returning to your original concept '{orig_topic.replace('_', ' ')}' for reassessment."
            )

        # 6. Evaluate next action via policy
        next_action = self._select_next_action(session_state)
        next_q = next_action.get("question") or next_action.get("practice_question")
        if next_q and next_q.get("item_id"):
            session_state.setdefault("presented_item_ids", set()).add(next_q["item_id"])

        return {
            "ok": True,
            "feedback": feedback,
            "next_action": next_action,
            "session_summary": {
                "questions_answered": session_state["questions_answered"],
                "questions_correct": session_state["questions_correct"],
                "current_topic": session_state["current_topic"],
            }
        }

    def request_on_demand_intervention(
        self,
        session_id: str,
        intervention_type: str,  # "explain" | "worked_example" | "easier_question" | "prereq_help"
    ) -> Dict[str, Any]:
        """Provides on-demand pedagogical support when a student clicks an intervention button."""
        session_state = _ACTIVE_TUTOR_SESSIONS.get(session_id)
        if not session_state:
            return {"ok": False, "error": "Active session not found"}

        topic = session_state["current_topic"]

        if intervention_type == "explain":
            explanation = get_concept_explanation(topic)
            return {
                "ok": True,
                "action_type": TutorActionType.CONCEPT_EXPLANATION.value,
                "content": explanation,
                "topic": topic,
                "title": f"Concept Breakdown: {topic.replace('_', ' ').title()}",
            }

        elif intervention_type == "worked_example":
            example = get_worked_example(topic)
            return {
                "ok": True,
                "action_type": TutorActionType.WORKED_EXAMPLE.value,
                "content": example,
                "topic": topic,
                "title": f"Step-by-Step Worked Example: {topic.replace('_', ' ').title()}",
            }

        elif intervention_type == "easier_question":
            # Find an eligible item with difficulty 1 or 2, avoiding current question
            easier_item = self._find_question(
                topic=topic,
                max_difficulty=2,
                exclude_item_ids=session_state.get("presented_item_ids")
            )
            if easier_item:
                session_state.setdefault("presented_item_ids", set()).add(easier_item["item_id"])
                return {
                    "ok": True,
                    "action_type": TutorActionType.EASIER_QUESTION.value,
                    "question": easier_item,
                    "topic": topic,
                    "title": f"Guided Simpler Exercise: {topic.replace('_', ' ').title()}",
                }
            else:
                return {
                    "ok": True,
                    "action_type": TutorActionType.WORKED_EXAMPLE.value,
                    "content": get_worked_example(topic),
                    "topic": topic,
                    "title": f"Worked Example: {topic.replace('_', ' ').title()}",
                }

        elif intervention_type == "prereq_help":
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            mastery_info = get_mastery_by_learner(session_state["learner_id"])
            bkt_map = mastery_info.get("topics_map", {})
            prereq_status = [
                {
                    "topic": p,
                    "mastery_pct": Math_round_pct(bkt_map.get(p, {}).get("mastery_probability", 0.20)),
                    "is_ready": bkt_map.get(p, {}).get("mastery_probability", 0.20) >= 0.60
                }
                for p in prereqs
            ]
            return {
                "ok": True,
                "action_type": TutorActionType.PREREQUISITE_REPAIR.value,
                "topic": topic,
                "prerequisites": prereq_status,
                "title": f"Prerequisite Breakdown for {topic.replace('_', ' ').title()}",
            }

        return {"ok": False, "error": f"Unknown intervention '{intervention_type}'"}

    def _select_next_action(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically selects the next pedagogical action:
        - If student has 2 consecutive errors:
          * Check upstream prerequisites. If any prerequisite has P(K) < 0.60 -> PREREQUISITE REPAIR.
          * Otherwise -> RESCUE MODE (simpler worked example or difficulty D-1).
        - If student has 2 consecutive successes:
          * CHALLENGE QUESTION (difficulty D+1).
        - Otherwise -> Standard adaptive practice question selected by policy.
        """
        learner_id = session_state["learner_id"]
        topic = session_state["current_topic"]
        consec_errors = session_state["consecutive_errors"]
        consec_successes = session_state["consecutive_successes"]

        # Fetch learner's current BKT knowledge state
        mastery_info = get_mastery_by_learner(learner_id)
        bkt_map = mastery_info.get("topics_map", {})

        # -------------------------------------------------------------
        # 1. PREREQUISITE REPAIR CHECK (Triggered on struggle)
        # -------------------------------------------------------------
        if consec_errors >= 2 and not session_state.get("in_prerequisite_repair"):
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            weak_prereqs = [
                p for p in prereqs
                if bkt_map.get(p, {}).get("mastery_probability", 0.20) < 0.60
            ]

            if weak_prereqs:
                target_prereq = weak_prereqs[0]
                session_state["in_prerequisite_repair"] = True
                session_state["repair_target_topic"] = topic
                session_state["repair_prereq_topic"] = target_prereq
                session_state["current_topic"] = target_prereq

                p_mastery = bkt_map.get(target_prereq, {}).get("mastery_probability", 0.20)
                prereq_q = self._find_question(
                    topic=target_prereq,
                    max_difficulty=2,
                    exclude_item_ids=session_state.get("presented_item_ids")
                )
                worked_ex = get_worked_example(target_prereq)

                return {
                    "action_type": TutorActionType.PREREQUISITE_REPAIR.value,
                    "target_topic": target_prereq,
                    "original_topic": topic,
                    "rationale": (
                        f"You're experiencing repeated difficulty on '{topic.replace('_', ' ')}'. "
                        f"Our prerequisite graph identifies that '{topic.replace('_', ' ')}' relies on '{target_prereq.replace('_', ' ')}', "
                        f"where your estimated mastery is currently only {Math_round_pct(p_mastery)}%. "
                        f"Let's strengthen this prerequisite foundation first."
                    ),
                    "worked_example": worked_ex,
                    "practice_question": prereq_q,
                }

        # -------------------------------------------------------------
        # 2. LEARNING DIFFICULTY RESCUE MODE (Prerequisites ok, but struggling on concept)
        # -------------------------------------------------------------
        if consec_errors >= 2:
            session_state["in_rescue_mode"] = True
            worked_ex = get_worked_example(topic)
            easier_q = self._find_question(
                topic=topic,
                max_difficulty=2,
                exclude_item_ids=session_state.get("presented_item_ids")
            )

            return {
                "action_type": TutorActionType.WORKED_EXAMPLE.value,
                "target_topic": topic,
                "rationale": (
                    f"You've encountered difficulty on '{topic.replace('_', ' ')}'. "
                    f"Rescue mode active: here is a step-by-step worked example demonstrating the solution technique, "
                    f"followed by a guided simpler exercise."
                ),
                "worked_example": worked_ex,
                "practice_question": easier_q,
            }

        # -------------------------------------------------------------
        # 3. CHALLENGE ADVANCEMENT (2 consecutive successes)
        # -------------------------------------------------------------
        if consec_successes >= 2:
            challenge_q = self._find_question(
                topic=topic,
                min_difficulty=3,
                exclude_item_ids=session_state.get("presented_item_ids")
            )
            if challenge_q:
                return {
                    "action_type": TutorActionType.CHALLENGE_QUESTION.value,
                    "target_topic": topic,
                    "rationale": (
                        f"Great consecutive accuracy on '{topic.replace('_', ' ')}'! "
                        f"Advancing you to a higher-difficulty challenge exercise to deepen your mastery."
                    ),
                    "question": challenge_q,
                }

        # -------------------------------------------------------------
        # 4. NORMAL ADAPTIVE PRACTICE (Selected by Policy)
        # -------------------------------------------------------------
        mode = session_state.get("mode", "continue")
        strat = "composite_adaptive"
        if mode == "weak_topics":
            strat = "prereq_aware_weakest"
        elif mode == "revision":
            strat = "forgetting_revision"

        # Query recommendation engine
        rec = self.recommender.recommend(learner_id=learner_id, strategy=strat)
        rec_item_id = rec.get("item_id")
        rec_q = get_question_by_id(rec_item_id) if rec_item_id else None

        # Fallback to topic search if recommendation topic differs from session topic in targeted modes or already presented
        presented = session_state.get("presented_item_ids", set())
        if not rec_q or (mode in ("weak_topics", "exam_prep", "revision") and rec.get("topic") != topic) or (rec_item_id in presented):
            min_d = 2 if mode == "exam_prep" else None
            rec_q = self._find_question(topic=topic, min_difficulty=min_d, exclude_item_ids=presented)

        if not rec_q:
            # If all items in this topic were presented in this session, select an unseen question from another concept
            unseen_cands = [q for q in self.all_questions if q.get("item_id") not in presented]
            if unseen_cands:
                rec_q = unseen_cands[0]
            else:
                rec_q = self.all_questions[0]

        return {
            "action_type": TutorActionType.PRACTICE_QUESTION.value,
            "target_topic": rec_q.get("topic", topic),
            "rationale": rec.get("explanation", {}).get("pedagogical_rationale") or f"Targeted practice for {rec_q.get('topic', topic).replace('_', ' ')}.",
            "question": {
                "item_id": rec_q["item_id"],
                "question": rec_q["question"],
                "options": rec_q["options"],
                "difficulty": rec_q.get("difficulty", 2),
                "topic": rec_q.get("topic", topic),
                "explanation": rec_q.get("explanation"),
                "cognitive_level": rec_q.get("cognitive_level"),
                "question_type": rec_q.get("question_type"),
            }
        }

    def _find_question(
        self,
        topic: str,
        max_difficulty: Optional[int] = None,
        min_difficulty: Optional[int] = None,
        exclude_item_ids: Optional[set[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Finds a matching question in the canonical question bank with repetition prevention."""
        clean_t = str(topic).strip().lower()
        candidates = [
            q for q in self.all_questions
            if q.get("topic") == clean_t or clean_t in q.get("knowledge_components", [])
        ]
        if not candidates:
            # Fallback to any question
            candidates = self.all_questions

        if max_difficulty is not None:
            filtered = [q for q in candidates if q.get("difficulty", 2) <= max_difficulty]
            if filtered:
                candidates = filtered

        if min_difficulty is not None:
            filtered = [q for q in candidates if q.get("difficulty", 2) >= min_difficulty]
            if filtered:
                candidates = filtered

        # Repetition filtering: avoid presented items when fresh items exist
        if exclude_item_ids:
            unseen = [q for q in candidates if q.get("item_id") not in exclude_item_ids]
            if unseen:
                candidates = unseen
            else:
                # If all candidates for this specific topic were presented, look across entire item bank
                bank_unseen = [q for q in self.all_questions if q.get("item_id") not in exclude_item_ids]
                if bank_unseen:
                    candidates = bank_unseen

        if candidates:
            # Deterministically cycle or pick first available candidate
            chosen = candidates[0]
            return {
                "item_id": chosen["item_id"],
                "question": chosen["question"],
                "options": chosen["options"],
                "difficulty": chosen.get("difficulty", 2),
                "topic": chosen.get("topic", clean_t),
                "explanation": chosen.get("explanation"),
                "cognitive_level": chosen.get("cognitive_level"),
                "question_type": chosen.get("question_type"),
            }
        return None


def Math_round_pct(val: float) -> int:
    return int(round(val * 100))
