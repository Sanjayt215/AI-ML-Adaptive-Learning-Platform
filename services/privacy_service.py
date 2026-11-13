"""
Privacy and Research Data Anonymization Service.
Part of KT-RL Phase 8: Real-World Validation Readiness & Safe Pilot Infrastructure.

Provides:
- Irreversible cryptographic pseudonymization (HMAC-SHA256 with research salt).
- PII stripping and data minimization (FERPA & IRB compliant).
- Anonymized research dataset generation for educational outcome evaluations.
- Temporal de-identification (converting wall-clock timestamps into relative sequence offsets).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

try:
    from services.learning_store import get_connection, get_db_path
    from services.assessment_service import get_learner_assessments, compare_pre_post_assessments
    from services.bkt_service import get_mastery_by_learner
except ImportError:
    from autolearn_fullstack.services.learning_store import get_connection, get_db_path
    from autolearn_fullstack.services.assessment_service import get_learner_assessments, compare_pre_post_assessments
    from autolearn_fullstack.services.bkt_service import get_mastery_by_learner

logger = logging.getLogger(__name__)

# Default salt for research pseudonymization (can be overridden by environment variable)
DEFAULT_RESEARCH_SALT = os.environ.get("AUTOLEARN_RESEARCH_SALT", "AutoLearn-KT-RL-Phase8-Cryptographic-Salt-2026")


def pseudonymize_learner_id(learner_id: str, salt: Optional[str] = None) -> str:
    """
    Applies HMAC-SHA256 with a secure research salt to convert learner_id
    into an irreversible, consistent pseudonym.
    Returns format: 'subj_' + first 16 hex characters.
    """
    if not learner_id or not isinstance(learner_id, str):
        return "subj_anonymous"

    effective_salt = (salt or DEFAULT_RESEARCH_SALT).encode("utf-8")
    message = learner_id.strip().encode("utf-8")

    digest = hmac.new(effective_salt, message, hashlib.sha256).hexdigest()
    return f"subj_{digest[:16]}"


def strip_personal_identifiers(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively strips forbidden PII fields from records.
    Removes: name, email, ip, address, password, token, user_name, full_name, etc.
    """
    forbidden_keys = {
        "name", "fullname", "firstname", "lastname", "email", "mail",
        "ip", "ipaddress", "password", "token", "authtoken", "jwt",
        "sessiontoken", "phone", "studentid", "ssn", "userid", "username"
    }

    sanitized = {}
    for k, v in data.items():
        norm_key = k.lower().replace("_", "")
        if norm_key in forbidden_keys:
            continue
        if isinstance(v, dict):
            sanitized[k] = strip_personal_identifiers(v)
        elif isinstance(v, list):
            sanitized[k] = [
                strip_personal_identifiers(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized


def export_anonymized_research_dataset(
    db_path: Optional[str] = None,
    salt: Optional[str] = None,
    include_events: bool = True
) -> Dict[str, Any]:
    """
    Exports a clean, privacy-conscious, FERPA/IRB-compliant research dataset.
    - Learner IDs are cryptographically pseudonymized.
    - Timestamps are converted to relative seconds from first event.
    - All PII is strictly stripped.
    - Includes assessment comparisons (gross gain, normalized gain, retention)
      and interaction trajectories.
    """
    from services.assessment_service import init_assessment_tables
    init_assessment_tables(db_path)

    conn = get_connection(db_path)
    try:
        # 1. Fetch all distinct learners from learning_events and assessment_sessions
        learner_rows = conn.execute(
            """
            SELECT DISTINCT learner_id FROM learning_events
            UNION
            SELECT DISTINCT learner_id FROM assessment_sessions;
            """
        ).fetchall()
        learners = [r["learner_id"] for r in learner_rows if r["learner_id"]]

        participants: List[Dict[str, Any]] = []

        for l_id in learners:
            subj_id = pseudonymize_learner_id(l_id, salt=salt)

            # Retrieve assessment history and comparison
            comparison = compare_pre_post_assessments(l_id, db_path=db_path)
            raw_assessments = get_learner_assessments(l_id, db_path=db_path)

            anonymized_assessments = []
            for asm in raw_assessments:
                anonymized_assessments.append({
                    "assessment_type": asm.get("assessment_type"),
                    "status": asm.get("status"),
                    "score": asm.get("score"),
                    "total_questions": asm.get("total_questions"),
                    "accuracy": asm.get("accuracy"),
                    "duration_seconds": asm.get("duration_seconds"),
                    "kc_scores": asm.get("kc_scores"),
                })

            # Retrieve learning events
            anonymized_events = []
            if include_events:
                evts = conn.execute(
                    """
                    SELECT item_id, knowledge_components, is_correct, response_time_ms,
                           attempt_number, difficulty, event_timestamp, source
                    FROM learning_events
                    WHERE learner_id = ?
                    ORDER BY event_timestamp ASC;
                    """,
                    (l_id,),
                ).fetchall()

                base_time = None
                from datetime import datetime
                for idx, ev in enumerate(evts):
                    ts_str = ev["event_timestamp"]
                    rel_sec = 0.0
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if base_time is None:
                            base_time = ts
                        rel_sec = round((ts - base_time).total_seconds(), 2)
                    except Exception:
                        pass

                    kcs = ev["knowledge_components"]
                    if isinstance(kcs, str):
                        try:
                            kcs = json.loads(kcs)
                        except Exception:
                            kcs = [kcs]

                    anonymized_events.append({
                        "step_index": idx + 1,
                        "relative_time_seconds": rel_sec,
                        "item_id": ev["item_id"],
                        "knowledge_components": kcs,
                        "is_correct": int(ev["is_correct"]),
                        "response_time_ms": ev["response_time_ms"],
                        "attempt_number": ev["attempt_number"],
                        "difficulty": ev["difficulty"],
                        "recommendation_source": ev["source"],
                    })

            # Extract BKT final state
            try:
                bkt_state = get_mastery_by_learner(l_id, db_path=db_path)
                final_bkt_mastery = {
                    kc: round(v.get("p_l", 0.0), 4) if isinstance(v, dict) else round(getattr(v, "p_l", 0.0), 4)
                    for kc, v in bkt_state.get("topics", {}).items()
                }
            except Exception:
                final_bkt_mastery = {}

            participants.append({
                "participant_id": subj_id,
                "has_pre_post_comparison": comparison.get("has_comparison", False),
                "metrics": comparison.get("metrics") if comparison.get("has_comparison") else None,
                "assessments": anonymized_assessments,
                "total_events": len(anonymized_events),
                "final_bkt_mastery": final_bkt_mastery,
                "event_sequence": anonymized_events,
            })

        return {
            "dataset_name": "AutoLearn KT-RL Anonymized Research Dataset",
            "version": "1.0",
            "compliance": {
                "ferpa_compliant": True,
                "data_minimization_applied": True,
                "pseudonymization_method": "HMAC-SHA256",
                "pii_fields_retained": False,
                "temporal_deidentification": "Relative session seconds",
            },
            "summary": {
                "total_participants": len(participants),
                "participants_with_pre_post": sum(1 for p in participants if p["has_pre_post_comparison"]),
            },
            "participants": participants,
        }
    finally:
        conn.close()
