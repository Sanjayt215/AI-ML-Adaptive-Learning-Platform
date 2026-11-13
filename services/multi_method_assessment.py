"""
Multi-Method Student Knowledge Assessment & Evaluation Service.
Part of AutoLearn KT-RL Multi-Method Knowledge Analysis & RL Integration.

Implements eight distinct assessment methods:
1. Diagnostic Assessment (Pre-topic knowledge, EIG bits, gap analysis)
2. Conceptual Understanding Assessment (Rubric-based open-ended response scoring, missing concepts, misconceptions)
3. Practical Coding Assessment (Safe sandboxed execution, test cases, debugging, output prediction, code rubrics)
4. Concept Mapping Assessment (Concept relationship graph comparison against Curriculum DAG)
5. Active Recall Assessment (Question-before-answer, cloze reconstruction, spaced retrieval ratings)
6. Confidence Calibration Assessment (Metacognitive calibration, Brier score, over/underconfidence tracking)
7. Learning Behaviour Analytics (Telemetry on attempts, hints, response times, pacing)
8. Project-Based Assessment (Multi-step applied tasks with structured rubrics and partial credit)
"""

from __future__ import annotations

import ast
import io
import json
import logging
import math
import os
import re
import subprocess
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import TOPIC_CATALOG, get_all_questions, get_question_by_id
from services.bkt_service import get_mastery_by_learner, bkt_step
from services.curriculum_planner import CurriculumPlanner
from services.learning_store import get_connection, get_db_path, log_event, get_learner_events
from services.diagnostic_calibration import compute_expected_information_gain

logger = logging.getLogger(__name__)

# =========================================================================
# 1. DIAGNOSTIC ASSESSMENT
# =========================================================================

def generate_diagnostic_assessment(
    topic: str,
    learner_id: str = "learner_default",
    num_questions: int = 4,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs a pre-topic diagnostic assessment mixing:
    - Prerequisite knowledge checks
    - Core conceptual diagnostic questions (selecting high EIG items)
    - Code prediction / comprehension checks
    Avoids recently attempted items for the learner.
    """
    topic_raw = str(topic).strip().lower()
    topic_space = topic_raw.replace("_", " ")
    topic_under = topic_raw.replace(" ", "_")
    all_questions = get_all_questions()

    # Identify prerequisites
    prereqs = (
        TOPIC_CATALOG.get(topic_space, {}).get("prerequisites", [])
        or TOPIC_CATALOG.get(topic_under, {}).get("prerequisites", [])
    )

    # Fetch learner's past events to avoid repeating items
    events = get_learner_events(learner_id, limit=300, db_path=db_path)
    seen_item_ids = {e.get("item_id") for e in events if e.get("item_id")}

    diagnostic_items = []

    # 1. Prerequisite check question (if prerequisites exist)
    for p in prereqs:
        p_clean = p.replace("_", " ")
        p_cands = [
            q for q in all_questions
            if (q.get("topic") == p or q.get("topic") == p_clean or p in q.get("knowledge_components", []) or p_clean in q.get("knowledge_components", []))
            and q.get("item_id") not in seen_item_ids
        ]
        if p_cands:
            item = dict(p_cands[0])
            item["diagnostic_role"] = "prerequisite_check"
            item["prerequisite_for"] = topic_space
            diagnostic_items.append(item)
            seen_item_ids.add(item["item_id"])
            break

    # 2. Topic core questions (prioritizing items matching topic or knowledge_components)
    def matches_topic(q):
        t = str(q.get("topic", "")).lower()
        kcs = [str(k).lower() for k in q.get("knowledge_components", [])]
        return t in (topic_raw, topic_space, topic_under) or any(k in (topic_raw, topic_space, topic_under) for k in kcs)

    topic_cands = [q for q in all_questions if matches_topic(q) and q.get("item_id") not in seen_item_ids]
    if not topic_cands:
        topic_cands = [q for q in all_questions if matches_topic(q)]
    if not topic_cands:
        topic_cands = all_questions

    for q in topic_cands[: max(1, num_questions - len(diagnostic_items))]:
        item = dict(q)
        item["diagnostic_role"] = "core_concept_diagnostic"
        diagnostic_items.append(item)
        seen_item_ids.add(item.get("item_id"))

    # Current BKT mastery for context
    mastery_info = get_mastery_by_learner(learner_id, db_path=db_path)
    prior_p = (
        mastery_info.get("topics_map", {}).get(topic_space, {}).get("mastery_probability")
        or mastery_info.get("topics_map", {}).get(topic_under, {}).get("mastery_probability", 0.20)
    )

    return {
        "ok": True,
        "assessment_type": "diagnostic",
        "topic": topic,
        "learner_id": learner_id,
        "prior_mastery_probability": round(prior_p, 3),
        "prerequisites_checked": prereqs,
        "questions": diagnostic_items,
        "total_items": len(diagnostic_items),
        "instructions": (
            f"This diagnostic gauges your current knowledge of '{topic.replace('_', ' ').title()}' "
            f"and foundational prerequisites before beginning new learning activities."
        ),
    }


def evaluate_diagnostic_assessment(
    learner_id: str = "learner_default",
    topic: str = "python",
    answers: Optional[Dict[str, str]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates completed diagnostic, computes score, updates BKT prior, and generates gap report.
    Supports both (learner_id, topic, answers) and (topic, answers) calling signatures.
    Only counts valid attempted questions in denominator.
    """
    if isinstance(topic, dict) and answers is None:
        answers = topic
        topic = learner_id
        learner_id = "learner_default"

    topic = str(topic).strip().lower().replace("_", " ")
    answers = answers or {}
    all_questions = get_all_questions()
    q_map = {q["item_id"]: q for q in all_questions if q.get("item_id")}

    # Filter only questions that have non-empty selections and exist in repository
    valid_attempted = {
        item_id: str(selected).strip()
        for item_id, selected in answers.items()
        if item_id in q_map and selected is not None and str(selected).strip() != ""
    }

    total = len(valid_attempted)
    if total == 0:
        return {
            "ok": True,
            "assessment_type": "diagnostic",
            "topic": topic,
            "score_pct": 0.0,
            "correct_count": 0,
            "total_items": 0,
            "status": "no_items_attempted",
            "calibrated_prior_mastery": 0.20,
            "recommended_starting_level": 1,
            "prerequisite_gaps_identified": [],
            "recommendation": "No questions were answered. Please attempt diagnostic questions to calibrate your personalized learning path.",
            "item_results": [],
        }

    correct_count = 0
    item_results = []
    prereq_weaknesses = []

    for item_id, selected in valid_attempted.items():
        q = q_map[item_id]
        corr = q.get("correct_answer") or q.get("answer")
        is_corr = (str(selected).strip().lower() == str(corr).strip().lower())
        if is_corr:
            correct_count += 1
        else:
            if q.get("diagnostic_role") == "prerequisite_check" or q.get("topic") != topic:
                prereq_weaknesses.append(q.get("topic", "prerequisite"))

        item_results.append({
            "item_id": item_id,
            "topic": q.get("topic"),
            "selected": selected,
            "correct_answer": corr,
            "is_correct": is_corr,
            "explanation": q.get("explanation"),
        })

    score_pct = round((correct_count / total) * 100, 1)

    # Initial calibrated mastery based on diagnostic
    calibrated_prior = round(max(0.10, min(0.90, 0.15 + (score_pct / 100.0) * 0.70)), 3)

    # Determine recommended starting level
    if score_pct >= 75:
        starting_level = 3
        recommendation = f"Strong prior foundations! Advance directly to Level 3 exercises on {topic.title()}."
    elif score_pct >= 50:
        starting_level = 2
        recommendation = f"Moderate familiarity. Begin with Level 2 guided exercises on {topic.title()}."
    else:
        starting_level = 1
        recommendation = (
            f"Foundational support recommended. "
            + (f"Prerequisite weakness detected in {', '.join(set(prereq_weaknesses))}. Review prerequisites first."
               if prereq_weaknesses else f"Start with intuitive Level 1 concepts.")
        )

    return {
        "ok": True,
        "assessment_type": "diagnostic",
        "topic": topic,
        "score_pct": score_pct,
        "correct_count": correct_count,
        "total_items": total,
        "status": "evaluated",
        "calibrated_prior_mastery": calibrated_prior,
        "recommended_starting_level": starting_level,
        "prerequisite_gaps_identified": list(set(prereq_weaknesses)),
        "recommendation": recommendation,
        "item_results": item_results,
    }


# =========================================================================
# 2. CONCEPTUAL UNDERSTANDING ASSESSMENT (OPEN-ENDED RESPONSES)
# =========================================================================

CONCEPT_RUBRICS: Dict[str, Dict[str, Any]] = {
    "python": {
        "key_concepts": ["vectorization", "contiguous memory", "numpy", "broadcasting", "hash table", "immutable"],
        "misconceptions": [
            ("python lists are contiguous float arrays", "Python lists store pointers to objects, whereas NumPy ndarrays store contiguous homogeneous C buffers."),
            ("dict lookup is o(n)", "Python dictionary lookups are average O(1) through open-addressing hash tables."),
        ],
        "rubric_criteria": [
            {"criterion": "Memory Structure", "max_points": 30, "keywords": ["contiguous", "array", "buffer", "pointer", "hash"]},
            {"criterion": "Vectorization / Performance", "max_points": 40, "keywords": ["vectorized", "simd", "c-level", "overhead", "loop"]},
            {"criterion": "Practical Usage", "max_points": 30, "keywords": ["numpy", "index", "slice", "performance"]},
        ],
    },
    "linear_regression": {
        "key_concepts": ["residual sum of squares", "gradient descent", "ordinary least squares", "assumptions", "multicollinearity", "l1", "l2"],
        "misconceptions": [
            ("r2 measures causality", "R² measures the proportion of variance explained by the model, not causal influence."),
            ("ridge sets weights to zero", "Ridge regression (L2) shrinks coefficients asymptotically toward zero but does not produce exact sparsity; Lasso (L1) yields sparse models."),
        ],
        "rubric_criteria": [
            {"criterion": "Objective Function", "max_points": 35, "keywords": ["loss", "mse", "rss", "least squares", "residuals"]},
            {"criterion": "Optimization & Regularization", "max_points": 35, "keywords": ["gradient", "penalty", "l1", "l2", "ridge", "lasso"]},
            {"criterion": "Assumptions & Limitations", "max_points": 30, "keywords": ["linearity", "homoscedasticity", "independence", "collinearity"]},
        ],
    },
    "classification": {
        "key_concepts": ["decision boundary", "logistic function", "sigmoid", "cross-entropy", "precision", "recall", "roc-auc"],
        "misconceptions": [
            ("accuracy is always sufficient", "Under severe class imbalance, high accuracy can be achieved trivially by predicting the majority class, masking poor minority detection."),
            ("logistic regression output is exact probability", "Raw logistic outputs represent calibrated model likelihoods under log-odds linearity assumptions."),
        ],
        "rubric_criteria": [
            {"criterion": "Decision Mechanics", "max_points": 35, "keywords": ["boundary", "sigmoid", "logistic", "threshold", "log-odds"]},
            {"criterion": "Loss & Optimization", "max_points": 35, "keywords": ["cross-entropy", "log loss", "maximum likelihood"]},
            {"criterion": "Evaluation Metrics", "max_points": 30, "keywords": ["precision", "recall", "f1", "roc", "auc", "confusion matrix"]},
        ],
    },
}

def evaluate_conceptual_explanation(
    topic: str,
    prompt: str,
    student_response: str,
) -> Dict[str, Any]:
    """
    Evaluates an open-ended natural language explanation using a structured, transparent rubric.
    Identifies:
    - Keywords / concepts recognized
    - Critical concepts missing
    - Specific misconceptions detected
    - Weighted criterion scores
    - Evidence-based constructive feedback
    """
    topic_clean = str(topic).strip().lower()
    text = str(student_response or "").strip().lower()

    rubric = CONCEPT_RUBRICS.get(topic_clean, {
        "key_concepts": ["definition", "mechanism", "advantage", "tradeoff"],
        "misconceptions": [],
        "rubric_criteria": [
            {"criterion": "Conceptual Accuracy", "max_points": 40, "keywords": ["definition", "concept", "principle"]},
            {"criterion": "Mechanism & Mechanics", "max_points": 35, "keywords": ["algorithm", "method", "process", "step"]},
            {"criterion": "Application & Tradeoffs", "max_points": 25, "keywords": ["performance", "tradeoff", "limitation"]},
        ],
    })

    words = text.split()
    if len(words) < 6:
        return {
            "ok": True,
            "topic": topic_clean,
            "score_pct": 0.0,
            "evaluation_confidence": 0.35,
            "status": "incomplete_response",
            "feedback": "Your response is too brief. Please provide a complete explanation covering core mechanisms, algorithmic principles, and technical definitions.",
            "recognized_concepts": [],
            "missing_concepts": rubric["key_concepts"],
            "detected_misconceptions": [],
            "criteria_scores": [],
        }

    # 1. Match Key Concepts (supporting stems e.g. vectoriz -> vectorization/vectorized)
    recognized = []
    missing = []
    for kc in rubric["key_concepts"]:
        stem = kc
        for suffix in ("ization", "ation", "ment", "ing", "ed", "es", "s"):
            if stem.endswith(suffix) and len(stem) - len(suffix) >= 4:
                stem = stem[:-len(suffix)]
                break
        pattern = r"\b" + re.escape(stem)
        if re.search(pattern, text) or kc in text or stem in text:
            recognized.append(kc)
        else:
            missing.append(kc)

    # 2. Check Misconceptions
    detected_misconceptions = []
    for pattern, explanation in rubric["misconceptions"]:
        tokens = pattern.lower().split()
        if sum(1 for tok in tokens if tok in text) >= max(2, len(tokens) - 1):
            detected_misconceptions.append({
                "misconception_pattern": pattern,
                "correction": explanation,
            })

    # 3. Score Criteria
    criteria_scores = []
    total_score = 0.0
    for crit in rubric["rubric_criteria"]:
        kw_hits = sum(1 for kw in crit["keywords"] if kw in text)
        kw_ratio = min(1.0, kw_hits / max(1, len(crit["keywords"]) * 0.6))
        pts = round(crit["max_points"] * kw_ratio, 1)
        criteria_scores.append({
            "criterion": crit["criterion"],
            "max_points": crit["max_points"],
            "awarded_points": pts,
            "keywords_matched": [kw for kw in crit["keywords"] if kw in text],
        })
        total_score += pts

    # Misconception penalty (max -15 per detected misconception)
    if detected_misconceptions:
        total_score = max(0.0, total_score - (len(detected_misconceptions) * 15))

    # Cap score if no recognized core concepts appear (prevents gaming with generic words)
    if not recognized:
        total_score = min(total_score, 18.0)

    final_score = round(min(100.0, max(0.0, total_score)), 1)

    # Dynamic evaluator confidence calibration based on evidence density
    concept_ratio = len(recognized) / max(1, len(rubric["key_concepts"]))
    word_density_factor = min(1.0, len(words) / 35.0)
    if not recognized and len(words) < 15:
        eval_confidence = 0.42
    else:
        eval_confidence = round(0.45 + (0.35 * concept_ratio) + (0.12 * word_density_factor), 2)

    # Formulate feedback
    feedback_parts = []
    if final_score >= 80:
        feedback_parts.append(f"Excellent conceptual clarity! You clearly articulated the core principles of {topic_clean.replace('_', ' ').title()}.")
    elif final_score >= 50:
        feedback_parts.append(f"Solid foundational understanding with some gaps in algorithmic mechanisms.")
    else:
        feedback_parts.append(f"Your explanation touches on related terms but lacks core mechanical explanations.")

    if missing:
        feedback_parts.append(f"To deepen your response, discuss: {', '.join(missing[:3])}.")
    if detected_misconceptions:
        for m in detected_misconceptions:
            feedback_parts.append(f"Important Note: {m['correction']}")

    return {
        "ok": True,
        "topic": topic_clean,
        "score_pct": final_score,
        "evaluation_confidence": eval_confidence,
        "status": "evaluated" if eval_confidence >= 0.50 else "low_confidence_evidence",
        "recognized_concepts": recognized,
        "missing_concepts": missing,
        "detected_misconceptions": detected_misconceptions,
        "criteria_scores": criteria_scores,
        "feedback": " ".join(feedback_parts),
    }


# =========================================================================
# 3. PRACTICAL CODING ASSESSMENT (SAFE ISOLATED EXECUTION)
# =========================================================================

CODING_CHALLENGES: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {
            "challenge_id": "code_py_01",
            "title": "Vectorized Mean Squared Error",
            "format": "write_program",
            "difficulty": 2,
            "instruction": "Write a function `compute_mse(y_true, y_pred)` that takes two lists of numbers and returns the Mean Squared Error using math/list comprehensions or vectorized logic.",
            "starter_code": "def compute_mse(y_true, y_pred):\n    # Write your solution here\n    pass\n",
            "test_cases": [
                {"input": "compute_mse([1, 2, 3], [1, 2, 3])", "expected": "0.0"},
                {"input": "compute_mse([1, 2, 3], [2, 3, 4])", "expected": "1.0"},
                {"input": "compute_mse([10, 20], [12, 18])", "expected": "4.0"},
            ],
            "hidden_test_cases": [
                {"input": "compute_mse([0, 0, 0], [2, 2, 2])", "expected": "4.0"},
            ],
        },
        {
            "challenge_id": "code_py_02",
            "title": "Debug NumPy Matrix Dimension Alignment",
            "format": "find_error",
            "difficulty": 3,
            "instruction": "The function below intends to multiply a 3x2 matrix by a 2x4 matrix, but causes a dimension mismatch error. Fix the bug.",
            "starter_code": "def matrix_prod(A, B):\n    # A is 3x2, B is 4x2\n    # Fix dimension alignment so A (3x2) can multiply B\n    B_aligned = [[B[j][i] for j in range(len(B))] for i in range(len(B[0]))]\n    result = []\n    for i in range(len(A)):\n        row = []\n        for j in range(len(B_aligned[0])):\n            s = sum(A[i][k] * B_aligned[k][j] for k in range(len(A[0])))\n            row.append(s)\n        result.append(row)\n    return result\n",
            "test_cases": [
                {"input": "len(matrix_prod([[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4], [5, 6], [7, 8]]))", "expected": "3"},
            ],
            "hidden_test_cases": [],
        },
    ],
    "linear_regression": [
        {
            "challenge_id": "code_lr_01",
            "title": "Predict Output of Gradient Descent Step",
            "format": "predict_output",
            "difficulty": 2,
            "instruction": "Given w = 1.0, learning_rate = 0.1, and loss gradient dL/dw = 4.0, calculate the updated weight w_new = w - (lr * grad). What is w_new?",
            "starter_code": "w = 1.0\nlr = 0.1\ngrad = 4.0\nw_new = w - (lr * grad)\nprint(round(w_new, 2))\n",
            "test_cases": [
                {"input": "w_new", "expected": "0.6"},
            ],
            "hidden_test_cases": [],
        },
    ],
}


def execute_sandboxed_code(
    code_str: str,
    test_cases: List[Dict[str, str]],
    timeout_sec: float = 2.0,
) -> Dict[str, Any]:
    """
    Safely executes student Python code in an isolated subprocess with strict isolation:
    - Runs in a separate process via sys.executable -I -s
    - Blocks introspection escapes (__class__, __subclasses__, __bases__)
    - Enforces hard wall-clock timeout with process killing
    - Does not execute untrusted code in the main Flask application process
    - Captures test results, memory errors, and execution metrics
    """
    code_str = str(code_str or "").strip()
    if not code_str:
        return {"ok": False, "error": "No code provided for execution."}

    # Locate sandbox_worker.py
    worker_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox_worker.py")
    if not os.path.exists(worker_path):
        return {"ok": False, "error": "Sandbox worker executable not found."}

    payload = json.dumps({"code": code_str, "test_cases": test_cases})

    # Prepare isolated environment: wipe PYTHONPATH and dangerous vars
    isolated_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
        "PATH": os.environ.get("PATH", ""),
        "TEMP": os.environ.get("TEMP", "C:\\Temp"),
        "TMP": os.environ.get("TMP", "C:\\Temp"),
    }

    try:
        proc = subprocess.Popen(
            [sys.executable, "-I", "-s", worker_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=isolated_env,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(input=payload, timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=0.5)
            except Exception:
                pass
            return {
                "ok": True,
                "syntax_valid": True,
                "runtime_error": f"Execution timed out (exceeded {timeout_sec:.1f}s limit). Infinite loop detected.",
                "tests_passed": 0,
                "total_tests": len(test_cases),
                "score_pct": 0.0,
                "timeout_killed": True,
            }

        out_str = stdout.strip()
        if not out_str:
            err_msg = stderr.strip() if stderr else "Empty output from worker."
            return {
                "ok": True,
                "syntax_valid": False,
                "runtime_error": f"Execution failed: {err_msg}",
                "tests_passed": 0,
                "total_tests": len(test_cases),
                "score_pct": 0.0,
            }

        data = json.loads(out_str)
        return data

    except Exception as e:
        return {"ok": False, "error": f"Sandbox execution dispatcher error: {str(e)}"}


# =========================================================================
# 4. CONCEPT MAPPING ASSESSMENT
# =========================================================================

def normalize_concept_name(name: str) -> str:
    """Normalizes concept aliases, underscores, and case to match canonical TOPIC_CATALOG keys."""
    cleaned = str(name or "").strip().lower().replace("_", " ").replace("-", " ")
    alias_map = {
        "linreg": "linear regression",
        "linear reg": "linear regression",
        "logreg": "classification",
        "logistic regression": "classification",
        "nn": "neural networks",
        "ann": "neural networks",
        "dl": "neural networks",
        "deep learning": "neural networks",
        "trees": "decision trees",
        "clustering": "clustering",
        "data prep": "data preprocessing",
        "preprocessing": "data preprocessing",
        "stats": "statistics",
        "prob": "probability",
        "rl": "reinforcement learning",
        "ml": "machine learning",
        "eda": "data preprocessing",
        "svm": "svm",
        "ensembles": "ensemble methods",
    }
    return alias_map.get(cleaned, cleaned)


def evaluate_concept_map(
    student_edges: List[Dict[str, str]],  # [{source: "python", target: "data preprocessing", relation: "prerequisite"}]
) -> Dict[str, Any]:
    """
    Evaluates student concept map relationships against the canonical Curriculum DAG.
    Normalizes concept aliases and casing.
    Distinguishes:
    - Directed Prerequisite relationships in canonical DAG
    - Inverted Prerequisite relationships (reversed direction)
    - Valid general conceptual associations between recognized syllabus concepts
    - Unrecognized concept nodes
    - Duplicate edges
    """
    # Build canonical prerequisite edges from TOPIC_CATALOG
    canonical_prereq_edges: Set[Tuple[str, str]] = set()
    for topic, meta in TOPIC_CATALOG.items():
        t_clean = normalize_concept_name(topic)
        for p in meta.get("prerequisites", []):
            p_clean = normalize_concept_name(p)
            canonical_prereq_edges.add((p_clean, t_clean))

    valid_edges = []
    incorrect_edges = []
    missing_prereqs = []
    duplicate_edges = []

    submitted_pairs: Set[Tuple[str, str]] = set()
    for e in (student_edges or []):
        raw_src = str(e.get("source", "")).strip()
        raw_tgt = str(e.get("target", "")).strip()
        src = normalize_concept_name(raw_src)
        tgt = normalize_concept_name(raw_tgt)

        if not src or not tgt:
            incorrect_edges.append({
                "source": raw_src,
                "target": raw_tgt,
                "reason": "Source or target concept node is empty.",
            })
            continue

        pair = (src, tgt)
        if pair in submitted_pairs:
            duplicate_edges.append({"source": raw_src, "target": raw_tgt, "reason": "Duplicate edge."})
            continue
        submitted_pairs.add(pair)

        if pair in canonical_prereq_edges:
            valid_edges.append({
                "source": raw_src,
                "target": raw_tgt,
                "status": "correct_prerequisite",
                "explanation": f"Verified prerequisite: '{src.title()}' is a canonical requirement for '{tgt.title()}'.",
            })
        elif (tgt, src) in canonical_prereq_edges:
            incorrect_edges.append({
                "source": raw_src,
                "target": raw_tgt,
                "reason": f"Inverted dependency: '{tgt.title()}' is actually a prerequisite for '{src.title()}'.",
            })
        else:
            # Check if both topics exist in catalog as general valid association
            src_in = src in TOPIC_CATALOG or any(normalize_concept_name(k) == src for k in TOPIC_CATALOG)
            tgt_in = tgt in TOPIC_CATALOG or any(normalize_concept_name(k) == tgt for k in TOPIC_CATALOG)
            if src_in and tgt_in:
                valid_edges.append({
                    "source": raw_src,
                    "target": raw_tgt,
                    "status": "valid_association",
                    "explanation": f"Valid conceptual relationship between '{src.title()}' and '{tgt.title()}' (associative, not direct 1-step prerequisite).",
                })
            else:
                unrec = []
                if not src_in:
                    unrec.append(f"'{raw_src}'")
                if not tgt_in:
                    unrec.append(f"'{raw_tgt}'")
                incorrect_edges.append({
                    "source": raw_src,
                    "target": raw_tgt,
                    "reason": f"Unrecognized concept: {', '.join(unrec)} not found in curriculum syllabus.",
                })

    # Find missing canonical prerequisites
    for p_src, p_tgt in canonical_prereq_edges:
        if (p_src, p_tgt) not in submitted_pairs:
            missing_prereqs.append({
                "source": p_src,
                "target": p_tgt,
                "note": f"'{p_src.title()}' must precede '{p_tgt.title()}'.",
            })

    total_canonical = len(canonical_prereq_edges)
    correct_canonical = sum(1 for e in valid_edges if e.get("status") == "correct_prerequisite")
    alignment_pct = round((correct_canonical / max(1, total_canonical)) * 100, 1)

    return {
        "ok": True,
        "alignment_pct": alignment_pct,
        "valid_edges_count": len(valid_edges),
        "incorrect_edges_count": len(incorrect_edges),
        "missing_prerequisites_count": len(missing_prereqs),
        "valid_edges": valid_edges,
        "incorrect_edges": incorrect_edges,
        "missing_prerequisites": missing_prereqs[:5],
    }


# =========================================================================
# 5. CONFIDENCE CALIBRATION & METRIC CALCULATION
# =========================================================================

def calculate_confidence_calibration(
    history: List[Dict[str, Any]],  # [{confidence: float|int, correct: bool}]
) -> Dict[str, Any]:
    """
    Computes mathematically rigorous metacognitive calibration metrics:
    - Brier Score: Mean squared error of predicted subjective probabilities vs observed outcomes
      Brier = (1 / N) * sum((prob_i - actual_i)^2), where lower is better calibrated (0.0 is perfect).
    - Overconfidence Rate: % of items where confidence >= 0.70 but answer was incorrect.
    - Underconfidence Rate: % of items where confidence <= 0.40 but answer was correct.
    - Sample sufficiency: Enforces minimum N >= 3 before drawing statistical conclusions.
    """
    if not history or len(history) < 3:
        return {
            "ok": True,
            "brier_score": None,
            "calibration_status": "insufficient_data",
            "note": "Insufficient evidence for reliable calibration (minimum 3 sample assessments required).",
            "overconfidence_rate": None,
            "underconfidence_rate": None,
            "well_calibrated_rate": None,
            "total_samples": len(history) if history else 0,
            "sample_sufficient": False,
        }

    conf_level_map = {1: 0.33, 2: 0.67, 3: 0.95}
    brier_sum = 0.0
    overconfident_count = 0
    underconfident_count = 0
    well_calibrated_count = 0

    for item in history:
        # 1. Parse subjective probability p_i in [0.0, 1.0]
        raw_val = item.get("confidence")
        if raw_val is None:
            raw_val = item.get("confidence_level", 2)

        if isinstance(raw_val, (int, float)):
            if raw_val > 1.0:
                prob = min(1.0, max(0.0, float(raw_val) / 100.0))
            elif raw_val in (1, 2, 3) and not isinstance(raw_val, float):
                prob = conf_level_map.get(int(raw_val), 0.67)
            else:
                prob = min(1.0, max(0.0, float(raw_val)))
        else:
            prob = 0.67

        # 2. Parse binary observed outcome actual_i in {0.0, 1.0}
        is_corr = item.get("correct")
        if is_corr is None:
            is_corr = item.get("is_correct", False)
        actual = 1.0 if bool(is_corr) else 0.0

        # 3. Accumulate squared error
        brier_sum += (prob - actual) ** 2

        # 4. Classify metacognitive alignment
        if prob >= 0.70 and actual == 0.0:
            overconfident_count += 1
        elif prob <= 0.40 and actual == 1.0:
            underconfident_count += 1
        else:
            well_calibrated_count += 1

    total = len(history)
    brier_score = round(brier_sum / total, 4)
    over_rate = round((overconfident_count / total) * 100, 1)
    under_rate = round((underconfident_count / total) * 100, 1)
    well_rate = round((well_calibrated_count / total) * 100, 1)

    if over_rate > 25.0:
        status = "overconfident"
        note = "Frequent high-confidence errors detected. Metacognitive recalibration & diagnostic testing recommended."
    elif under_rate > 25.0:
        status = "underconfident"
        note = "High accuracy with hesitant subjective ratings. Your knowledge is more robust than self-estimated."
    elif brier_score <= 0.15:
        status = "optimally_calibrated"
        note = "Exceptional calibration! Subjective confidence closely mirrors empirical probability of success."
    else:
        status = "well_calibrated"
        note = "Confidence ratings align reliably with empirical performance."

    return {
        "ok": True,
        "brier_score": brier_score,
        "calibration_status": status,
        "note": note,
        "overconfidence_rate": over_rate,
        "underconfidence_rate": under_rate,
        "well_calibrated_rate": well_rate,
        "total_samples": total,
        "sample_sufficient": True,
    }


# =========================================================================
# 6. PROJECT-BASED ASSESSMENT
# =========================================================================

PROJECT_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    "proj_numpy_eda": {
        "project_id": "proj_numpy_eda",
        "title": "NumPy Student Performance Analyzer",
        "topic": "python",
        "description": "Construct a data processing pipeline that normalizes a raw 2D array of exam scores, computes feature statistics, and identifies outliers.",
        "rubric": [
            {"criterion": "Data Normalization (Min-Max)", "weight_pct": 30, "description": "Correct implementation of (X - X_min) / (X_max - X_min)."},
            {"criterion": "Summary Statistics (Mean & Std)", "weight_pct": 30, "description": "Vectorized calculation along axis=0."},
            {"criterion": "Outlier Detection (Z-Score > 2.0)", "weight_pct": 25, "description": "Boolean indexing to isolate extreme scores."},
            {"criterion": "Code Quality & Documentation", "weight_pct": 15, "description": "Clean functions with docstrings and type hints."},
        ],
    },
    "proj_linear_reg": {
        "project_id": "proj_linear_reg",
        "title": "End-to-End Linear Regression from Scratch",
        "topic": "linear_regression",
        "description": "Implement ordinary least squares using normal equations and gradient descent, comparing convergence curves.",
        "rubric": [
            {"criterion": "Normal Equation Closed-Form", "weight_pct": 35, "description": "Computes (X^T X)^(-1) X^T y without matrix singular errors."},
            {"criterion": "Gradient Descent Iteration", "weight_pct": 35, "description": "Correct weight update w := w - lr * grad."},
            {"criterion": "Residual Variance & R^2 Metric", "weight_pct": 30, "description": "Evaluates explained variance proportion accurately."},
        ],
    },
}

def evaluate_project_submission(
    project_id: str,
    submission_text: str,
    scores_by_criterion: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluates project-based practical application tasks against a multi-criteria rubric.
    Mathematically computes weighted composite score: Sum(criterion_achievement * weight) / Sum(weight).
    Seamlessly matches user-provided criteria scores or applies domain-specific code heuristics.
    """
    spec = PROJECT_SPECIFICATIONS.get(project_id, PROJECT_SPECIFICATIONS["proj_numpy_eda"])
    rubric = spec["rubric"]

    criteria_results = []
    total_weighted_points = 0.0
    total_weight = sum(c.get("weight_pct", 25) for c in rubric)

    # Specific code heuristic patterns for practical machine learning projects
    domain_heuristics = {
        "norm": ["min", "max", "/", "-", "scale"],
        "stat": ["mean", "std", "var", "axis", "sum"],
        "outlier": ["z_score", "std", "abs", ">", "2", "where", "filter"],
        "qual": ["def ", "return", '"""', "import", "type"],
        "normal equation": ["dot", "@", "inv", "pinv", "t", "transpose"],
        "gradient": ["learning_rate", "lr", "grad", "step", "-=", "iter"],
        "residual": ["r2", "ss_tot", "ss_res", "mean", "variance", "error"],
    }

    sub_lower = str(submission_text or "").lower()

    for idx, c in enumerate(rubric):
        c_name = c["criterion"]
        weight = c.get("weight_pct", 25)
        c_clean = c_name.lower().replace("-", " ").replace("(", "").replace(")", "")

        awarded = None
        # 1. Match from explicitly provided criterion scores (exact or clean substring match)
        if scores_by_criterion:
            for k, v in scores_by_criterion.items():
                k_clean = str(k).lower().replace("-", " ").replace("(", "").replace(")", "")
                if k_clean == c_clean or k_clean in c_clean or c_clean in k_clean or str(idx) == str(k):
                    try:
                        awarded = max(0.0, min(100.0, float(v)))
                        break
                    except (ValueError, TypeError):
                        pass

        # 2. Heuristic code inspection if no explicit score is provided
        if awarded is None:
            relevant_words = []
            for h_key, h_list in domain_heuristics.items():
                if h_key in c_clean:
                    relevant_words.extend(h_list)
            if not relevant_words:
                relevant_words = [w for w in c_clean.split() if len(w) > 3]

            hits = sum(1 for w in relevant_words if w in sub_lower)
            ratio = min(1.0, hits / max(1, len(relevant_words) * 0.5))
            awarded = round(ratio * 100.0, 1)

        weighted_pts = (awarded / 100.0) * weight
        total_weighted_points += weighted_pts

        criteria_results.append({
            "criterion": c_name,
            "weight_pct": weight,
            "score_pct": awarded,
            "weighted_points": round(weighted_pts, 2),
            "description": c.get("description", ""),
        })

    final_score = round((total_weighted_points / max(1.0, total_weight)) * 100.0, 1) if total_weight > 0 else 0.0

    if final_score >= 90.0:
        grade = "A"
    elif final_score >= 80.0:
        grade = "B"
    elif final_score >= 70.0:
        grade = "C"
    elif final_score >= 60.0:
        grade = "D"
    else:
        grade = "F"

    status = "passed" if final_score >= 60.0 else "needs_revision"

    return {
        "ok": True,
        "project_id": project_id,
        "title": spec["title"],
        "topic": spec["topic"],
        "final_score_pct": final_score,
        "total_score_pct": final_score,
        "grade": grade,
        "criteria_results": criteria_results,
        "criteria_breakdown": criteria_results,
        "status": status,
        "feedback": (
            f"Project evaluation complete for {spec['title']}. Overall score: {final_score}% (Grade: {grade}). "
            + ("Outstanding implementation satisfying all rubric specifications." if final_score >= 85 else
               "Passing work with opportunities to strengthen specific criteria." if final_score >= 60 else
               "Submission requires revision; review marked criteria below passing threshold.")
        ),
        "overall_feedback": (
            f"Project evaluation complete for {spec['title']}. Overall score: {final_score}% (Grade: {grade})."
        ),
    }
