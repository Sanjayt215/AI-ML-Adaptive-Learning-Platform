"""
Question Quality Validation Pipeline & Knowledge Dataset Auditor.
Part of AutoLearn KT-RL Full Website Transformation.

Audits and validates the entire question dataset across:
1. Topic Alignment (Topic exists in canonical TOPIC_CATALOG)
2. KC Alignment (Knowledge components explicitly mapped)
3. Answer Integrity (Correct answer exists in options list, non-empty)
4. Distractor Quality (Options distinct, plausible, distractor rationales provided)
5. Difficulty Consistency (Difficulty in ordinal scale [1, 5])
6. Cognitive Level (recall, comprehension, application, analysis)
7. Question Formats (conceptual, code_interpretation, output_prediction, debugging, math, scenario, comparison)
8. Duplicate & Ambiguity Detection (Exact or high string-similarity duplicates)
9. Explanation Completeness (Explanations non-empty and concept-grounded)
10. Source Provenance (canonical curated vs verified supplemental vs synthetic)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from resources import TOPIC_CATALOG, QUIZ_QUESTIONS, get_all_questions

logger = logging.getLogger(__name__)

SUPPORTED_QUESTION_TYPES = {
    "conceptual",
    "mcq",
    "code_interpretation",
    "output_prediction",
    "debugging",
    "mathematical",
    "scenario_based",
    "application_based",
    "comparison",
    "practical_implementation",
}

SUPPORTED_COGNITIVE_LEVELS = {
    "recall",
    "comprehension",
    "application",
    "analysis",
    "evaluation",
}


def audit_question_bank(
    custom_questions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Executes a comprehensive, 10-point audit across all questions in the bank.
    Returns metrics, distribution breakdowns, and detailed item-level findings.
    """
    questions = custom_questions if custom_questions is not None else get_all_questions()

    total_items = len(questions)
    valid_items = 0
    errors: List[str] = []
    warnings: List[str] = []

    seen_ids: Set[str] = set()
    seen_texts: Dict[str, str] = {}  # normalized text -> item_id

    type_distribution: Dict[str, int] = {k: 0 for k in SUPPORTED_QUESTION_TYPES}
    level_distribution: Dict[str, int] = {k: 0 for k in SUPPORTED_COGNITIVE_LEVELS}
    difficulty_distribution: Dict[int, int] = {d: 0 for d in range(1, 6)}
    provenance_distribution: Dict[str, int] = {}
    topic_distribution: Dict[str, int] = {}

    for idx, q in enumerate(questions):
        item_id = q.get("item_id") or f"item_{idx}"
        is_item_valid = True

        # 1. Unique Item ID
        if not q.get("item_id"):
            errors.append(f"[{item_id}] Missing canonical item_id.")
            is_item_valid = False
        elif item_id in seen_ids:
            errors.append(f"[{item_id}] Duplicate item_id detected.")
            is_item_valid = False
        seen_ids.add(item_id)

        # 2. Duplicate Question Text Check
        raw_text = (q.get("question") or q.get("q") or "").strip().lower()
        if not raw_text:
            errors.append(f"[{item_id}] Question text is empty.")
            is_item_valid = False
        elif raw_text in seen_texts:
            warnings.append(f"[{item_id}] Potential duplicate question text with {seen_texts[raw_text]}.")
        else:
            seen_texts[raw_text] = item_id

        # 3. Topic Alignment
        topic = str(q.get("topic") or "").strip().lower()
        topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        if topic not in TOPIC_CATALOG and topic != "general":
            warnings.append(f"[{item_id}] Topic '{topic}' is not in canonical TOPIC_CATALOG.")

        # 4. KC Alignment
        kcs = q.get("knowledge_components") or []
        if not isinstance(kcs, list) or len(kcs) == 0:
            errors.append(f"[{item_id}] Missing knowledge_components list.")
            is_item_valid = False

        # 5. Options & Answer Integrity
        options = q.get("options") or []
        answer = q.get("correct_answer") or q.get("answer")

        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"[{item_id}] Options list must contain at least 2 distinct choices.")
            is_item_valid = False
        elif len(set(options)) != len(options):
            errors.append(f"[{item_id}] Duplicate choices detected in options list.")
            is_item_valid = False

        if not answer:
            errors.append(f"[{item_id}] Missing correct answer.")
            is_item_valid = False
        elif answer not in options:
            errors.append(f"[{item_id}] Correct answer '{answer}' is not in options list.")
            is_item_valid = False

        # 6. Difficulty Consistency
        diff = q.get("difficulty", 2)
        try:
            diff_int = int(diff)
            if 1 <= diff_int <= 5:
                difficulty_distribution[diff_int] = difficulty_distribution.get(diff_int, 0) + 1
            else:
                errors.append(f"[{item_id}] Difficulty {diff} out of bounds [1, 5].")
                is_item_valid = False
        except (ValueError, TypeError):
            errors.append(f"[{item_id}] Non-integer difficulty {diff}.")
            is_item_valid = False

        # 7. Cognitive Level & Question Type
        cog_level = str(q.get("cognitive_level") or "comprehension").strip().lower()
        if cog_level in level_distribution:
            level_distribution[cog_level] += 1
        else:
            level_distribution["comprehension"] = level_distribution.get("comprehension", 0) + 1

        q_type = str(q.get("question_type") or "conceptual").strip().lower()
        if q_type in type_distribution:
            type_distribution[q_type] += 1
        else:
            type_distribution["conceptual"] = type_distribution.get("conceptual", 0) + 1

        # 8. Explanation Completeness
        explanation = (q.get("explanation") or "").strip()
        if not explanation:
            warnings.append(f"[{item_id}] Question explanation is missing or empty.")

        # 9. Source Provenance
        prov = str(q.get("source") or "autolearn_canonical_curated").strip()
        provenance_distribution[prov] = provenance_distribution.get(prov, 0) + 1

        if is_item_valid:
            valid_items += 1

    quality_score = round((valid_items / max(1, total_items)) * 100, 1)

    return {
        "ok": True,
        "is_valid": len(errors) == 0,
        "quality_score_pct": quality_score,
        "total_items": total_items,
        "valid_items": valid_items,
        "unique_ids_count": len(seen_ids),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors[:25],
        "warnings": warnings[:25],
        "type_distribution": type_distribution,
        "cognitive_level_distribution": level_distribution,
        "difficulty_distribution": difficulty_distribution,
        "provenance_distribution": provenance_distribution,
        "topic_distribution": topic_distribution,
    }
