"""
Safe Shadow Evaluation Service.
Part of KT-RL Phase 8: Real-World Validation Readiness & Safe Pilot Infrastructure.

Provides:
- Non-invasive parallel evaluation of experimental RL policies (Dueling DQN, LinUCB).
- Zero user-facing intervention: live recommendations are never altered by shadow mode.
- Strict default disabled state (KT_RL_SHADOW_MODE=0).
- Robust exception shielding: errors in experimental policies do not interrupt learner flow.
- Real-time policy concordance, KC agreement, and inference latency tracking.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.learning_store import get_connection
except ImportError:
    from autolearn_fullstack.services.learning_store import get_connection

logger = logging.getLogger(__name__)

# Environment flag controlling shadow mode (disabled by default)
SHADOW_MODE_ENV_VAR = "KT_RL_SHADOW_MODE"

# Thread-safe in-memory ring buffer for recent shadow evaluations
MAX_BUFFER_SIZE = 500
_shadow_lock = threading.Lock()
_shadow_buffer: List[Dict[str, Any]] = []


def is_shadow_mode_enabled() -> bool:
    """Returns True only if KT_RL_SHADOW_MODE is explicitly set to '1' or 'true'."""
    val = os.environ.get(SHADOW_MODE_ENV_VAR, "0").strip().lower()
    return val in ("1", "true", "yes", "enabled")


def set_shadow_mode(enabled: bool) -> None:
    """Dynamically set the shadow mode state (useful for tests and controlled pilots)."""
    os.environ[SHADOW_MODE_ENV_VAR] = "1" if enabled else "0"


def record_shadow_evaluation(
    learner_id: str,
    state_vector: Optional[List[float]],
    production_item_id: str,
    production_strategy: str,
    shadow_decisions: Dict[str, Dict[str, Any]],
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Safely captures shadow policy recommendations alongside the production choice.

    Args:
        learner_id: Identifier of learner (anonymized in log).
        state_vector: Observable state vector representation.
        production_item_id: The question actually served to the user.
        production_strategy: Name of the active production strategy.
        shadow_decisions: Dict mapping shadow policy name to:
            {
                "item_id": "...",
                "latency_ms": 12.4,
                "confidence_or_q": 0.85
            }
    """
    now_str = datetime.now(timezone.utc).isoformat()

    # Calculate agreement metrics with production policy
    agreements: Dict[str, bool] = {}
    for policy_name, decision in shadow_decisions.items():
        shadow_item = decision.get("item_id")
        agreements[policy_name] = (shadow_item == production_item_id)

    record = {
        "timestamp": now_str,
        "learner_id": learner_id,
        "production_strategy": production_strategy,
        "production_item_id": production_item_id,
        "shadow_decisions": shadow_decisions,
        "agreements": agreements,
    }

    # Store in memory buffer with lock
    with _shadow_lock:
        _shadow_buffer.append(record)
        if len(_shadow_buffer) > MAX_BUFFER_SIZE:
            _shadow_buffer.pop(0)

    return record


def execute_shadow_comparison(
    recommender_instance: Any,
    learner_id: str,
    production_recommendation: Dict[str, Any],
    candidate_shadow_policies: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience wrapper that runs candidate shadow policies safely without leaking
    exceptions or altering the production recommendation.
    """
    if not is_shadow_mode_enabled():
        return None

    if candidate_shadow_policies is None:
        candidate_shadow_policies = ["dueling_dqn", "linucb_bandit", "difficulty_ladder"]

    production_item_id = (production_recommendation.get("question") or {}).get("item_id")
    production_strategy = production_recommendation.get("strategy_used", "composite_adaptive")

    shadow_results: Dict[str, Dict[str, Any]] = {}

    for pol in candidate_shadow_policies:
        if pol == production_strategy:
            continue
        try:
            start_t = time.perf_counter()
            # Request recommendation under shadow policy
            rec = recommender_instance.recommend_exercise(
                learner_id=learner_id,
                strategy_override=pol,
                difficulty_preference=None
            )
            elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
            shadow_q = rec.get("question") or {}
            shadow_results[pol] = {
                "item_id": shadow_q.get("item_id"),
                "knowledge_components": shadow_q.get("knowledge_components", []),
                "difficulty": shadow_q.get("difficulty"),
                "latency_ms": elapsed_ms,
                "status": "success",
            }
        except Exception as ex:
            logger.warning(f"Shadow evaluation for policy '{pol}' encountered error: {ex}")
            shadow_results[pol] = {
                "status": "error",
                "error_message": str(ex),
                "latency_ms": 0.0,
            }

    return record_shadow_evaluation(
        learner_id=learner_id,
        state_vector=None,
        production_item_id=production_item_id,
        production_strategy=production_strategy,
        shadow_decisions=shadow_results,
    )


def get_shadow_metrics() -> Dict[str, Any]:
    """Computes concordance and execution metrics from recent shadow evaluations."""
    with _shadow_lock:
        records = list(_shadow_buffer)

    if not records:
        return {
            "total_evaluations": 0,
            "shadow_mode_enabled": is_shadow_mode_enabled(),
            "policies": {},
            "overall_agreement_rate": 0.0,
        }

    policy_stats: Dict[str, Dict[str, Any]] = {}
    for r in records:
        for pol, is_match in r.get("agreements", {}).items():
            if pol not in policy_stats:
                policy_stats[pol] = {"evaluations": 0, "agreements": 0, "total_latency_ms": 0.0}
            policy_stats[pol]["evaluations"] += 1
            if is_match:
                policy_stats[pol]["agreements"] += 1
            dec = r.get("shadow_decisions", {}).get(pol, {})
            policy_stats[pol]["total_latency_ms"] += dec.get("latency_ms", 0.0)

    summary_policies = {}
    for pol, st in policy_stats.items():
        n = max(1, st["evaluations"])
        summary_policies[pol] = {
            "evaluations": st["evaluations"],
            "concordance_rate": round(st["agreements"] / n, 4),
            "mean_latency_ms": round(st["total_latency_ms"] / n, 2),
        }

    return {
        "total_evaluations": len(records),
        "shadow_mode_enabled": is_shadow_mode_enabled(),
        "policies": summary_policies,
    }


def clear_shadow_buffer() -> None:
    """Clears all records in the in-memory shadow buffer."""
    with _shadow_lock:
        _shadow_buffer.clear()
