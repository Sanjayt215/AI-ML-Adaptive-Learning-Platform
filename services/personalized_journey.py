"""
AutoLearn Personalized Student Journey Engine.
Coordinates the end-to-end 10-step educational workflow:
1. Subject & Course Selection -> Initial Diagnostic Quiz
2. Automatic Topic-Wise Answer Analysis & "Your Knowledge Assessment Report"
3. Personalized Weak Topic Prioritization & Mistakes Diagnostics
4. Personalized Topic Exam Generation & Prerequisite Scaffolding
5. Concept Teaching Centre & Precise Question-Mistake Diagnosis
6. Multi-Method Learning Modalities (Explanation, Examples, Visual, Coding, Recall, Conceptual, Tutor)
7. Topic Learning Evaluation & Verification Report
8. Personalized Topic Mock Exam Generation (MCQ, Written, Coding, Concept Map, Application, Mixed)
9. Professional Mock Exam Results & Long-Horizon Progress Comparison
10. Continuous Personalized Learning with BKT & Adaptive Recommenders
"""

from typing import Any, Dict, List, Optional
import json
import time
import uuid

from resources import (
    QUIZ_QUESTIONS,
    TOPIC_CATALOG,
    get_all_questions,
    get_question_by_id,
    normalize_topic,
)
from services.bkt_service import get_mastery_by_learner
from services.concept_teaching import (
    get_full_concept_teaching,
    analyze_student_mistake,
)
from services.learning_store import (
    create_session,
    complete_session,
    log_event,
    get_learner_events,
    save_diagnostic_assessment,
    get_latest_diagnostic_assessment,
    save_concept_learning_session,
    save_mock_examination,
    get_mock_examinations_for_learner,
)
from services.multi_method_assessment import (
    evaluate_conceptual_explanation,
    execute_sandboxed_code,
    evaluate_concept_map,
)


SUBJECT_COURSES = {
    "ai_ml_core": {
        "title": "Artificial Intelligence & Machine Learning Specialization",
        "category": "Foundations to Advanced AI",
        "description": "Comprehensive journey from Python data structures and classical statistical learning to deep neural networks, reinforcement learning, and LLMs.",
        "default_topics": [
            "python", "probability", "statistics", "data preprocessing",
            "linear regression", "classification", "decision trees", "clustering",
            "dimensionality reduction", "naive bayes", "neural networks", "reinforcement learning"
        ],
    },
    "deep_learning_nlp": {
        "title": "Deep Learning, NLP & Generative AI",
        "category": "Advanced Neural Architectures",
        "description": "Sequence modeling, transformers, prompt engineering, RAG, and large language model architectures.",
        "default_topics": [
            "neural networks", "nlp", "computer vision", "transformers", "llm",
            "prompt engineering", "generative ai", "rag"
        ],
    },
    "classical_ml_data_science": {
        "title": "Classical Machine Learning & Statistical Modeling",
        "category": "Supervised & Unsupervised Learning",
        "description": "Rigorous treatment of linear models, tree ensembles, SVMs, clustering, and feature engineering.",
        "default_topics": [
            "python", "data preprocessing", "statistics", "feature engineering",
            "linear regression", "classification", "decision trees", "svm", "ensemble methods", "model evaluation"
        ],
    }
}


def _enrich_question_metadata(q: Dict[str, Any], subject: str = "Artificial Intelligence & Machine Learning") -> Dict[str, Any]:
    """Enriches a question object with full Bloom's, KC, Subtopic, and Example metadata."""
    t = q.get("topic") or "python"
    item_id = q.get("item_id") or "q_unknown"
    concept_data = get_full_concept_teaching(t)

    # Resolve Bloom's level
    diff = int(q.get("difficulty") or 2)
    blooms_map = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate"}
    blooms = q.get("cognitive_level") or blooms_map.get(diff, "Understand")

    return {
        "item_id": item_id,
        "subject": subject,
        "topic": t,
        "subtopic": q.get("subtopic") or t.replace("_", " ").title(),
        "knowledge_components": q.get("knowledge_components") or [t],
        "difficulty": diff,
        "blooms_level": blooms.capitalize(),
        "question": q.get("question") or q.get("q") or "Question text",
        "options": q.get("options") or ["A", "B", "C", "D"],
        "correct_answer": q.get("answer") or q.get("correct_answer") or "",
        "explanation": q.get("explanation") or concept_data.get("simple_definition", ""),
        "related_concept": concept_data.get("concept_name", t.title()),
        "related_example": concept_data.get("worked_example", {}).get("code", ""),
        "prerequisite_topics": TOPIC_CATALOG.get(t, {}).get("prerequisites", []),
        "distractor_explanations": q.get("distractor_explanations") or {},
    }


# =========================================================================
# STEP 1: INITIAL DIAGNOSTIC QUIZ GENERATION
# =========================================================================

def start_initial_diagnostic(
    learner_id: str,
    subject: str = "ai_ml_core",
    difficulty: str = "adaptive",
    selected_topics: Optional[List[str]] = None,
    num_questions: int = 10,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 1: Initializes the initial diagnostic quiz with rich metadata covering multiple KCs.
    """
    learner_id = str(learner_id or "learner_default").strip()
    course_meta = SUBJECT_COURSES.get(subject, SUBJECT_COURSES["ai_ml_core"])
    target_topics = selected_topics or course_meta["default_topics"]

    all_q = get_all_questions()
    selected_questions: List[Dict[str, Any]] = []
    seen_ids = set()

    # Filter target questions based on requested difficulty
    target_diff = 2
    if difficulty == "easy":
        target_diff = 1
    elif difficulty == "hard":
        target_diff = 4

    # Select questions balancing across target topics
    for t in target_topics:
        if len(selected_questions) >= num_questions:
            break
        norm_t = normalize_topic(t)
        cands = [
            q for q in all_q
            if (q.get("topic") == norm_t or norm_t in q.get("knowledge_components", []))
            and q.get("item_id") not in seen_ids
        ]
        if cands:
            # Sort by proximity to target difficulty
            cands.sort(key=lambda x: abs(int(x.get("difficulty", 2)) - target_diff))
            chosen = cands[0]
            seen_ids.add(chosen["item_id"])
            selected_questions.append(_enrich_question_metadata(chosen, subject=course_meta["title"]))

    # Fill remaining from all available topics
    for q in all_q:
        if len(selected_questions) >= num_questions:
            break
        if q["item_id"] not in seen_ids:
            seen_ids.add(q["item_id"])
            selected_questions.append(_enrich_question_metadata(q, subject=course_meta["title"]))

    # Initialize a tracking session in SQLite
    session_data = create_session(
        learner_id=learner_id,
        session_type="diagnostic_quiz",
        target_topics=target_topics,
        questions_presented=len(selected_questions),
        metadata={
            "subject": subject,
            "subject_title": course_meta["title"],
            "difficulty": difficulty,
            "presented_item_ids": list(seen_ids),
        },
        db_path=db_path,
    )

    return {
        "ok": True,
        "diagnostic_id": session_data["session_id"],
        "learner_id": learner_id,
        "subject": subject,
        "subject_title": course_meta["title"],
        "difficulty": difficulty,
        "total_questions": len(selected_questions),
        "questions": selected_questions,
        "covered_topics": list({q["topic"] for q in selected_questions}),
    }


# =========================================================================
# STEP 2: TOPIC-WISE ANSWER ANALYSIS & ASSESSMENT REPORT
# =========================================================================

def submit_initial_diagnostic(
    learner_id: str,
    diagnostic_id: str,
    answers: Dict[str, str],            # item_id -> selected_option
    response_times: Optional[Dict[str, int]] = None, # item_id -> time_ms
    duration_seconds: int = 120,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 2: Analyzes student answers, updates BKT, and produces "Your Knowledge Assessment Report".
    Crucially treats unattempted questions separately from incorrect answers.
    """
    learner_id = str(learner_id or "learner_default").strip()
    all_q_map = {q["item_id"]: q for q in get_all_questions()}
    resp_times = response_times or {}

    total_questions = 0
    attempted_questions = 0
    correct_answers = 0
    incorrect_answers = 0
    unanswered_questions = 0

    topic_stats: Dict[str, Dict[str, Any]] = {}
    knowledge_gaps: List[Dict[str, Any]] = []
    scored_items: List[Dict[str, Any]] = []

    # Map of all items presented in the session
    for item_id, q in all_q_map.items():
        if item_id in answers:
            total_questions += 1
            user_ans = str(answers.get(item_id, "")).strip()
            topic = q.get("topic", "general")
            t_data = topic_stats.setdefault(topic, {
                "topic": topic,
                "topic_title": topic.replace("_", " ").title(),
                "total": 0,
                "attempted": 0,
                "correct": 0,
                "incorrect": 0,
                "unanswered": 0,
            })
            t_data["total"] += 1

            if not user_ans or user_ans == "UNANSWERED":
                unanswered_questions += 1
                t_data["unanswered"] += 1
                scored_items.append({
                    "item_id": item_id,
                    "topic": topic,
                    "question": q.get("question") or q.get("q"),
                    "status": "unanswered",
                    "user_answer": None,
                    "correct_answer": q.get("answer") or q.get("correct_answer"),
                    "explanation": q.get("explanation"),
                })
                continue

            attempted_questions += 1
            t_data["attempted"] += 1
            corr_ans = str(q.get("answer") or q.get("correct_answer") or "").strip()
            is_corr = (user_ans.lower() == corr_ans.lower())

            if is_corr:
                correct_answers += 1
                t_data["correct"] += 1
            else:
                incorrect_answers += 1
                t_data["incorrect"] += 1

                # Log detailed knowledge gap
                mistake_diag = analyze_student_mistake(item_id, user_ans, topic=topic)
                knowledge_gaps.append({
                    "topic": topic,
                    "item_id": item_id,
                    "question": q.get("question") or q.get("q"),
                    "student_answer": user_ans,
                    "correct_answer": corr_ans,
                    "concept_misunderstood": mistake_diag.get("concept_title", topic.title()),
                    "why_incorrect": mistake_diag.get("why_incorrect"),
                    "missing_prerequisites": TOPIC_CATALOG.get(topic, {}).get("prerequisites", []),
                    "difficulty": q.get("difficulty", 2),
                    "recommended_activity": f"Complete foundational concept review on '{topic.replace('_', ' ')}' and step-by-step worked example.",
                })

            # Log interaction event for real BKT update
            rt_ms = resp_times.get(item_id, 3000)
            log_event(
                session_id=diagnostic_id,
                learner_id=learner_id,
                item_id=item_id,
                topic=topic,
                question_difficulty=q.get("difficulty", 2),
                submitted_answer=user_ans,
                response_time_ms=rt_ms,
                db_path=db_path,
            )

            scored_items.append({
                "item_id": item_id,
                "topic": topic,
                "question": q.get("question") or q.get("q"),
                "status": "correct" if is_corr else "incorrect",
                "user_answer": user_ans,
                "correct_answer": corr_ans,
                "explanation": q.get("explanation"),
            })

    # Calculate overall metrics
    overall_score_pct = round((correct_answers / max(1, attempted_questions)) * 100, 1)

    # Fetch updated BKT mastery to compare with empirical accuracy
    bkt_data = get_mastery_by_learner(learner_id, db_path=db_path)
    bkt_map = bkt_data.get("topics_map", {})

    # Compute per-topic scores, statuses, and BKT comparisons
    topic_table: List[Dict[str, Any]] = []
    visualization_bars: List[Dict[str, Any]] = []

    for t_name, stats in topic_stats.items():
        att = stats["attempted"]
        corr = stats["correct"]
        tot = stats["total"]
        score_pct = round((corr / max(1, att)) * 100, 1) if att > 0 else 0.0

        # Status categorization
        if att == 0:
            status = "Not Assessed"
            status_color = "slate"
        elif score_pct >= 75.0:
            status = "Strong"
            status_color = "emerald"
        elif score_pct >= 50.0:
            status = "Developing"
            status_color = "yellow"
        else:
            status = "Needs Improvement"
            status_color = "red"

        bkt_kc = bkt_map.get(t_name, {})
        bkt_prob = bkt_kc.get("mastery_probability", 0.20)
        bkt_pct = round(bkt_prob * 100, 1)
        insufficient_evidence = bkt_kc.get("update_count", 0) < 3

        row = {
            "topic": t_name,
            "topic_title": stats["topic_title"],
            "correct": corr,
            "attempted": att,
            "total": tot,
            "unanswered": stats["unanswered"],
            "score_pct": score_pct,
            "status": status,
            "status_color": status_color,
            "bkt_mastery_pct": bkt_pct,
            "insufficient_evidence": insufficient_evidence,
            "evidence_count": bkt_kc.get("update_count", 0),
        }
        topic_table.append(row)

        visualization_bars.append({
            "topic": stats["topic_title"],
            "topic_key": t_name,
            "accuracy": score_pct,
            "status": status,
            "bkt_mastery": bkt_pct,
        })

    # Sort topic table: weakest first
    topic_table.sort(key=lambda x: (x["status"] == "Not Assessed", x["score_pct"]))

    # Persist in SQLite
    save_diagnostic_assessment(
        learner_id=learner_id,
        subject="AI & Machine Learning Core",
        difficulty="adaptive",
        total_questions=total_questions,
        attempted_questions=attempted_questions,
        correct_answers=correct_answers,
        unanswered_questions=unanswered_questions,
        score_pct=overall_score_pct,
        time_spent_seconds=duration_seconds,
        topic_breakdown={"topics": topic_table},
        knowledge_gaps=knowledge_gaps,
        diagnostic_id=diagnostic_id,
        db_path=db_path,
    )

    complete_session(diagnostic_id, metadata={"score_pct": overall_score_pct}, db_path=db_path)

    return {
        "ok": True,
        "report_title": "Your Knowledge Assessment Report",
        "diagnostic_id": diagnostic_id,
        "learner_id": learner_id,
        "overall_performance": {
            "total_questions": total_questions,
            "attempted_questions": attempted_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "unanswered_questions": unanswered_questions,
            "overall_score_pct": overall_score_pct,
            "completion_time_seconds": duration_seconds,
        },
        "topic_performance_table": topic_table,
        "visualization_bars": visualization_bars,
        "knowledge_gap_analysis": knowledge_gaps,
        "scored_items": scored_items,
        "bkt_comparison_note": (
            "BKT Estimated Mastery models your true conceptual probability, filtering out lucky guesses and accidental slips. "
            "Empirical Accuracy reflects your immediate test score on this specific set of questions."
        ),
    }


# =========================================================================
# STEP 3: PERSONALIZED WEAK TOPIC PRIORITIZATION
# =========================================================================

def get_weak_topics_priority(
    learner_id: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 3: Categorizes topics into Strong, Developing, Weak, and Not Assessed.
    Ranks weak topics by priority with action items.
    """
    learner_id = str(learner_id or "learner_default").strip()
    bkt_data = get_mastery_by_learner(learner_id, db_path=db_path)
    bkt_map = bkt_data.get("topics_map", {})
    events = get_learner_events(learner_id, db_path=db_path)

    # Count errors per topic
    topic_errors: Dict[str, int] = {}
    topic_attempts: Dict[str, int] = {}
    for e in events:
        t = e.get("topic")
        if t:
            topic_attempts[t] = topic_attempts.get(t, 0) + 1
            if not e.get("is_correct", False):
                topic_errors[t] = topic_errors.get(t, 0) + 1

    classified: Dict[str, List[Dict[str, Any]]] = {
        "weak": [],
        "developing": [],
        "strong": [],
        "not_assessed": [],
    }

    for topic, meta in TOPIC_CATALOG.items():
        att = topic_attempts.get(topic, 0)
        err = topic_errors.get(topic, 0)
        bkt_state = bkt_map.get(topic, {})
        p_mastery = bkt_state.get("mastery_probability", 0.20)
        mastery_pct = round(p_mastery * 100, 1)

        # Check prerequisite status
        prereqs = meta.get("prerequisites", [])
        weak_prereqs = [
            p for p in prereqs
            if bkt_map.get(p, {}).get("mastery_probability", 0.20) < 0.60
        ]

        # Calculate weakness priority score
        # High error count + low BKT mastery + missing prerequisites = highest priority
        priority_score = err * 3.0 + (1.0 - p_mastery) * 4.0 + (len(weak_prereqs) * 2.0)

        item = {
            "topic": topic,
            "topic_title": topic.replace("_", " ").title(),
            "mastery_pct": mastery_pct,
            "error_count": err,
            "total_attempts": att,
            "prerequisites": prereqs,
            "missing_prerequisites": weak_prereqs,
            "has_prerequisite_gap": len(weak_prereqs) > 0,
            "priority_score": round(priority_score, 2),
            "priority_label": "High Priority" if priority_score >= 5.0 else "Medium Priority" if priority_score >= 3.0 else "Revision Recommended",
            "actions": {
                "start_learning": f"/learn?mode=concept&topic={topic}",
                "view_mistakes": f"/learn?mode=mistakes&topic={topic}",
                "why_wrong": f"/learn?mode=diagnostics&topic={topic}",
                "topic_assessment": f"/learn?mode=topic_exam&topic={topic}",
            }
        }

        if att == 0:
            classified["not_assessed"].append(item)
        elif err >= 2 or p_mastery < 0.50:
            classified["weak"].append(item)
        elif p_mastery < 0.75:
            classified["developing"].append(item)
        else:
            classified["strong"].append(item)

    # Sort weak topics descending by priority score
    classified["weak"].sort(key=lambda x: x["priority_score"], reverse=True)
    classified["developing"].sort(key=lambda x: x["priority_score"], reverse=True)

    return {
        "ok": True,
        "learner_id": learner_id,
        "weak_topics_ranked": classified["weak"],
        "developing_topics": classified["developing"],
        "strong_topics": classified["strong"],
        "not_assessed_topics": classified["not_assessed"],
        "summary": {
            "total_weak": len(classified["weak"]),
            "total_developing": len(classified["developing"]),
            "total_strong": len(classified["strong"]),
            "total_not_assessed": len(classified["not_assessed"]),
        }
    }


# =========================================================================
# STEP 4: PERSONALIZED TOPIC EXAM GENERATION
# =========================================================================

def generate_topic_targeted_exam(
    learner_id: str,
    topic: str,
    num_questions: int = 5,
    difficulty: int = 2,
    include_prereqs: bool = True,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 4: Generates a topic-specific practice exam.
    Does not repeat the exact same questions from initial quiz; selects fresh items or prerequisite checks.
    """
    learner_id = str(learner_id or "learner_default").strip()
    norm_topic = normalize_topic(topic)
    num_questions = max(3, min(int(num_questions or 5), 10))

    events = get_learner_events(learner_id, db_path=db_path)
    seen_ids = {e.get("item_id") for e in events if e.get("item_id")}

    all_q = get_all_questions()
    selected_questions: List[Dict[str, Any]] = []
    chosen_ids = set()

    # 1. Unseen questions for target topic
    topic_candidates = [
        q for q in all_q
        if (q.get("topic") == norm_topic or norm_topic in q.get("knowledge_components", []))
        and q.get("item_id") not in seen_ids
    ]
    for q in topic_candidates:
        if len(selected_questions) >= num_questions:
            break
        chosen_ids.add(q["item_id"])
        selected_questions.append(_enrich_question_metadata(q))

    # 2. If include_prereqs, include 1-2 questions from unmastered prerequisites
    if include_prereqs and len(selected_questions) < num_questions:
        prereqs = TOPIC_CATALOG.get(norm_topic, {}).get("prerequisites", [])
        for pre in prereqs:
            if len(selected_questions) >= num_questions:
                break
            pre_q = [
                q for q in all_q
                if (q.get("topic") == pre or pre in q.get("knowledge_components", []))
                and q.get("item_id") not in chosen_ids
            ]
            if pre_q:
                chosen = pre_q[0]
                chosen_ids.add(chosen["item_id"])
                selected_questions.append(_enrich_question_metadata(chosen))

    # 3. Fallback to any remaining questions on the topic (even if seen)
    if len(selected_questions) < num_questions:
        fallback = [q for q in all_q if (q.get("topic") == norm_topic) and q.get("item_id") not in chosen_ids]
        for q in fallback:
            if len(selected_questions) >= num_questions:
                break
            chosen_ids.add(q["item_id"])
            selected_questions.append(_enrich_question_metadata(q))

    # Fallback to general ML questions if bank exhausted
    for q in all_q:
        if len(selected_questions) >= num_questions:
            break
        if q["item_id"] not in chosen_ids:
            chosen_ids.add(q["item_id"])
            selected_questions.append(_enrich_question_metadata(q))

    sess_state = create_session(
        learner_id=learner_id,
        session_type="topic_exam",
        target_topics=[norm_topic],
        questions_presented=len(selected_questions),
        metadata={
            "topic": norm_topic,
            "difficulty": difficulty,
            "include_prereqs": include_prereqs,
            "presented_item_ids": list(chosen_ids),
        },
        db_path=db_path,
    )

    return {
        "ok": True,
        "exam_id": sess_state["session_id"],
        "learner_id": learner_id,
        "topic": norm_topic,
        "topic_title": norm_topic.replace("_", " ").title(),
        "difficulty": difficulty,
        "duration_minutes": max(5, len(selected_questions) * 2),
        "total_questions": len(selected_questions),
        "questions": selected_questions,
        "instructions": f"This targeted practice exam evaluates your conceptual grasp and application of {norm_topic.replace('_', ' ').title()}.",
    }


def submit_topic_targeted_exam(
    learner_id: str,
    exam_id: str,
    topic: str,
    answers: Dict[str, str],
    duration_seconds: int = 180,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submits and grades topic targeted exam.
    Updates BKT mastery and returns detailed explanation review.
    """
    learner_id = str(learner_id or "learner_default").strip()
    norm_topic = normalize_topic(topic)
    all_q_map = {q["item_id"]: q for q in get_all_questions()}

    correct = 0
    total = len(answers)
    scored_items: List[Dict[str, Any]] = []

    for item_id, user_ans in answers.items():
        q = all_q_map.get(item_id, {})
        corr_ans = q.get("answer") or q.get("correct_answer") or ""
        is_corr = (str(user_ans).strip().lower() == str(corr_ans).strip().lower())

        if is_corr:
            correct += 1

        log_event(
            session_id=exam_id,
            learner_id=learner_id,
            item_id=item_id,
            topic=q.get("topic") or norm_topic,
            question_difficulty=q.get("difficulty", 2),
            submitted_answer=user_ans,
            db_path=db_path,
        )

        scored_items.append({
            "item_id": item_id,
            "question": q.get("question") or q.get("q"),
            "submitted_answer": user_ans,
            "correct_answer": corr_ans,
            "is_correct": is_corr,
            "explanation": q.get("explanation"),
        })

    score_pct = round((correct / max(1, total)) * 100, 1)
    passed = score_pct >= 70.0

    bkt_data = get_mastery_by_learner(learner_id, db_path=db_path)
    new_mastery_pct = round(bkt_data.get("topics_map", {}).get(norm_topic, {}).get("mastery_probability", 0.20) * 100, 1)

    complete_session(exam_id, metadata={"score_pct": score_pct}, db_path=db_path)

    return {
        "ok": True,
        "exam_id": exam_id,
        "learner_id": learner_id,
        "topic": norm_topic,
        "score": correct,
        "total": total,
        "score_pct": score_pct,
        "passed": passed,
        "new_mastery_pct": new_mastery_pct,
        "scored_items": scored_items,
        "recommendation": "Great progress! Move to Topic Learning Evaluation or proceed to personalized mock exam." if passed else "Review the worked example and misconceptions before retrying.",
    }


# =========================================================================
# STEP 6 & 7: MULTI-METHOD LEARNING & TOPIC LEARNING EVALUATION
# =========================================================================

def record_learning_method_activity(
    learner_id: str,
    topic: str,
    method: str,                        # explanation, worked_examples, visual, coding, recall, conceptual, tutor
    user_input: Optional[str] = None,
    duration_seconds: int = 60,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 6: Records student engagement in a specific learning method and evaluates interactive input.
    """
    learner_id = str(learner_id or "learner_default").strip()
    norm_topic = normalize_topic(topic)
    eval_score = 100.0
    eval_feedback: Dict[str, Any] = {}

    # If practical coding mode, execute Python code in sandbox
    if method == "coding" and user_input:
        test_cases = [{"input": "1 + 1", "expected": "2"}]
        exec_res = execute_sandboxed_code(user_input, test_cases=test_cases)
        eval_score = float(exec_res.get("score_pct", 100.0 if exec_res.get("ok") else 0.0))
        eval_feedback = exec_res

    # If conceptual explanation mode, evaluate coverage and depth
    elif method == "conceptual" and user_input:
        prompt_str = f"Explain the core mechanisms and computational principles of {norm_topic}."
        concept_res = evaluate_conceptual_explanation(norm_topic, prompt_str, user_input)
        eval_score = float(concept_res.get("score", 0.0))
        eval_feedback = concept_res

    save_concept_learning_session(
        learner_id=learner_id,
        topic=norm_topic,
        learning_method=method,
        time_spent_seconds=duration_seconds,
        interactive_input=user_input,
        evaluation_score=eval_score,
        db_path=db_path,
    )

    return {
        "ok": True,
        "learner_id": learner_id,
        "topic": norm_topic,
        "method": method,
        "evaluation_score": eval_score,
        "feedback": eval_feedback,
    }


def evaluate_topic_understanding_activity(
    learner_id: str,
    topic: str,
    method: str,                        # mcq, conceptual, coding, concept_map
    submission: Any,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 7: Comprehensive Topic Learning Evaluation Report post-learning.
    Evaluates skills demonstrated, concepts mastered, remaining gaps, and next actions.
    """
    learner_id = str(learner_id or "learner_default").strip()
    norm_topic = normalize_topic(topic)
    score_pct = 0.0
    skills_demonstrated: List[str] = []
    concepts_mastered: List[str] = []
    concepts_weak: List[str] = []

    if method == "conceptual":
        text = str(submission or "")
        prompt_str = f"Explain the core mechanisms and computational principles of {norm_topic}."
        res = evaluate_conceptual_explanation(norm_topic, prompt_str, text)
        score_pct = float(res.get("score", 0.0))
        skills_demonstrated = res.get("identified_concepts", [])
        if score_pct >= 70.0:
            concepts_mastered.append(norm_topic.title())
        else:
            concepts_weak.append(norm_topic.title())

    elif method == "coding":
        code = str(submission or "")
        test_cases = [{"input": "1 + 1", "expected": "2"}]
        res = execute_sandboxed_code(code, test_cases=test_cases)
        score_pct = float(res.get("score_pct", 100.0 if res.get("ok") else 0.0))
        if score_pct >= 80.0:
            skills_demonstrated.append("Vectorized Algorithm Implementation")
            concepts_mastered.append(norm_topic.title())
        else:
            concepts_weak.append(f"{norm_topic.title()} Implementation Details")

    elif method == "concept_map":
        edges = submission if isinstance(submission, list) else []
        res = evaluate_concept_map(edges)
        score_pct = res.get("score", 0.0)
        if score_pct >= 70.0:
            skills_demonstrated.append("Hierarchical Prerequisite Modeling")
            concepts_mastered.append(norm_topic.title())
        else:
            concepts_weak.append("Prerequisite Dependency Identification")

    else:
        # Default quiz submission evaluation
        answers = submission if isinstance(submission, dict) else {}
        corr = sum(1 for _, v in answers.items() if str(v).lower() in {"correct", "true", "1"})
        score_pct = round((corr / max(1, len(answers))) * 100, 1)
        if score_pct >= 70.0:
            concepts_mastered.append(norm_topic.title())
        else:
            concepts_weak.append(norm_topic.title())

    passed = score_pct >= 70.0

    return {
        "ok": True,
        "report_title": "Topic Learning Evaluation Report",
        "topic": norm_topic,
        "topic_title": norm_topic.replace("_", " ").title(),
        "score_pct": score_pct,
        "passed": passed,
        "skills_demonstrated": skills_demonstrated or ["Basic Conceptual Awareness"],
        "concepts_mastered": concepts_mastered,
        "concepts_still_weak": concepts_weak,
        "remaining_knowledge_gaps": (
            [] if passed else [f"Deeper understanding of {norm_topic.replace('_', ' ')} edge-cases and implementation mechanics required."]
        ),
        "recommended_next_step": (
            "Ready for Personalized Mock Examination!" if passed else "Review worked examples and retry coding/conceptual practice."
        )
    }


# =========================================================================
# STEP 8 & 9: PERSONALIZED MOCK EXAM & RESULTS COMPARISON
# =========================================================================

def generate_personalized_mock_exam(
    learner_id: str,
    title: str = "Personalized AI/ML Multi-Method Mock Exam",
    method: str = "mixed",              # mcq, written, coding, concept_mapping, application, mixed
    topics: Optional[List[str]] = None,
    difficulty: int = 3,
    duration_minutes: int = 25,
    num_questions: int = 8,
    include_prereqs: bool = True,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 8: Generates a multi-method mock exam based on student preferences and learning objectives.
    """
    learner_id = str(learner_id or "learner_default").strip()
    target_topics = topics or ["python", "data preprocessing", "linear regression", "classification", "neural networks"]

    all_q = get_all_questions()
    selected_items: List[Dict[str, Any]] = []
    seen_ids = set()

    for t in target_topics:
        if len(selected_items) >= num_questions:
            break
        norm_t = normalize_topic(t)
        cands = [
            q for q in all_q
            if (q.get("topic") == norm_t or norm_t in q.get("knowledge_components", []))
            and q.get("item_id") not in seen_ids
        ]
        if cands:
            chosen = cands[0]
            seen_ids.add(chosen["item_id"])

            # Map to chosen method type
            item_type = "mcq"
            if method == "written":
                item_type = "written"
            elif method == "coding":
                item_type = "coding"
            elif method == "concept_mapping":
                item_type = "concept_mapping"
            elif method == "application":
                item_type = "application"
            elif method == "mixed":
                # Distribute methods across items
                idx = len(selected_items)
                types = ["mcq", "written", "coding", "application"]
                item_type = types[idx % len(types)]

            selected_items.append({
                "item_id": chosen["item_id"],
                "item_type": item_type,
                "topic": norm_t,
                "question": chosen.get("question") or chosen.get("q"),
                "options": chosen.get("options") if item_type == "mcq" else None,
                "difficulty": chosen.get("difficulty", difficulty),
                "starter_code": "def solution():\n    pass\n" if item_type == "coding" else None,
                "prerequisites": TOPIC_CATALOG.get(norm_t, {}).get("prerequisites", []),
            })

    # Fill if needed
    for q in all_q:
        if len(selected_items) >= num_questions:
            break
        if q["item_id"] not in seen_ids:
            seen_ids.add(q["item_id"])
            selected_items.append({
                "item_id": q["item_id"],
                "item_type": "mcq" if method != "coding" else "coding",
                "topic": q.get("topic", "general"),
                "question": q.get("question") or q.get("q"),
                "options": q.get("options"),
                "difficulty": q.get("difficulty", 2),
            })

    sess_state = create_session(
        learner_id=learner_id,
        session_type="mock_exam",
        target_topics=target_topics,
        questions_presented=len(selected_items),
        metadata={
            "exam_title": title,
            "method": method,
            "duration_minutes": duration_minutes,
            "difficulty": difficulty,
        },
        db_path=db_path,
    )

    return {
        "ok": True,
        "exam_id": sess_state["session_id"],
        "title": title,
        "learner_id": learner_id,
        "method": method,
        "difficulty": difficulty,
        "duration_minutes": duration_minutes,
        "total_questions": len(selected_items),
        "topics": target_topics,
        "questions": selected_items,
    }


def submit_personalized_mock_exam(
    learner_id: str,
    exam_id: str,
    answers: Dict[str, Any],            # item_id -> answer or code or text
    duration_seconds: int = 600,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Step 9: Professional Mock Exam Evaluation & Progress Comparison.
    Grades multi-method answers, compares with initial diagnostic score, and provides 3 next actions.
    """
    learner_id = str(learner_id or "learner_default").strip()
    all_q_map = {q["item_id"]: q for q in get_all_questions()}

    total_items = max(1, len(answers))
    earned_points = 0.0

    topic_scores: Dict[str, Dict[str, float]] = {}
    method_scores: Dict[str, Dict[str, float]] = {}
    review_items: List[Dict[str, Any]] = []

    for item_id, ans in answers.items():
        q = all_q_map.get(item_id, {})
        topic = q.get("topic", "general_ml")
        corr_ans = q.get("answer") or q.get("correct_answer") or ""

        # Grade according to response structure
        is_correct = False
        item_score = 0.0

        if isinstance(ans, str) and corr_ans:
            is_correct = (ans.strip().lower() == corr_ans.strip().lower())
            item_score = 1.0 if is_correct else 0.0
        elif isinstance(ans, dict) and "score" in ans:
            item_score = float(ans["score"]) / 100.0
            is_correct = item_score >= 0.70
        else:
            item_score = 1.0 if str(ans).strip() != "" else 0.0
            is_correct = item_score > 0.5

        earned_points += item_score

        # Track per topic
        t_stat = topic_scores.setdefault(topic, {"earned": 0.0, "total": 0.0})
        t_stat["earned"] += item_score
        t_stat["total"] += 1.0

        # Track per method
        m_type = "mcq" if isinstance(ans, str) and len(ans) < 50 else "written"
        m_stat = method_scores.setdefault(m_type, {"earned": 0.0, "total": 0.0})
        m_stat["earned"] += item_score
        m_stat["total"] += 1.0

        # Log event to database
        log_event(
            session_id=exam_id,
            learner_id=learner_id,
            item_id=item_id,
            topic=topic,
            question_difficulty=q.get("difficulty", 2),
            submitted_answer=str(ans)[:100],
            db_path=db_path,
        )

        review_items.append({
            "item_id": item_id,
            "topic": topic,
            "question": q.get("question") or q.get("q"),
            "submitted_answer": ans,
            "correct_answer": corr_ans,
            "is_correct": is_correct,
            "explanation": q.get("explanation"),
        })

    mock_score_pct = round((earned_points / total_items) * 100, 1)
    passed = mock_score_pct >= 70.0

    # Retrieve initial diagnostic score for genuine empirical comparison
    latest_diag = get_latest_diagnostic_assessment(learner_id, db_path=db_path)
    initial_diag_score = latest_diag.get("score_pct", 35.0) if latest_diag else 40.0
    improvement_pct = round(mock_score_pct - initial_diag_score, 1)

    # Calculate percentage breakdown per topic
    topic_pct_map = {
        t: round((stats["earned"] / max(1.0, stats["total"])) * 100, 1)
        for t, stats in topic_scores.items()
    }

    method_pct_map = {
        m: round((stats["earned"] / max(1.0, stats["total"])) * 100, 1)
        for m, stats in method_scores.items()
    }

    # Save to SQLite
    save_mock_examination(
        learner_id=learner_id,
        title="Personalized Multi-Method Mock Exam",
        method="mixed",
        topics=list(topic_scores.keys()),
        score_pct=mock_score_pct,
        passed=passed,
        topic_scores=topic_pct_map,
        method_scores=method_pct_map,
        initial_diagnostic_score=initial_diag_score,
        learning_score=mock_score_pct,
        improvement_pct=improvement_pct,
        review_items=review_items,
        duration_minutes=int(duration_seconds / 60),
        db_path=db_path,
    )

    complete_session(exam_id, metadata={"score_pct": mock_score_pct}, db_path=db_path)

    # 3 Next Actions
    next_actions = [
        {
            "action_id": "continue_next_topic",
            "title": "Continue to Next Curriculum Topic",
            "description": "Advance along the curriculum DAG to unlock your next sequential machine learning milestone.",
            "link": "/learning-plan",
        },
        {
            "action_id": "revise_weak_concepts",
            "title": "Revise Remaining Weak Concepts",
            "description": "Focus spaced repetition review on any questions missed during this mock examination.",
            "link": "/learn?mode=revision",
        },
        {
            "action_id": "retake_different_mock",
            "title": "Retake a Different Mock Examination",
            "description": "Generate a new randomized mock test with alternative question variants or different assessment methods.",
            "link": "/learn?mode=exam_prep",
        }
    ]

    return {
        "ok": True,
        "exam_id": exam_id,
        "learner_id": learner_id,
        "overall_score_pct": mock_score_pct,
        "passed": passed,
        "duration_seconds": duration_seconds,
        "topic_wise_performance": topic_pct_map,
        "method_wise_performance": method_pct_map,
        "score_comparison": {
            "initial_diagnostic_pct": initial_diag_score,
            "mock_exam_pct": mock_score_pct,
            "improvement_pct": improvement_pct,
            "trend_summary": (
                f"Definite Mastery Growth: +{improvement_pct}% improvement from your initial diagnostic ({initial_diag_score}% -> {mock_score_pct}%)."
                if improvement_pct > 0 else "Consistent performance. Continue targeted practice to boost retention."
            ),
        },
        "review_items": review_items,
        "next_actions": next_actions,
    }
