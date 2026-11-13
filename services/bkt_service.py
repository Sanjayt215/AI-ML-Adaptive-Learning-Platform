"""
Bayesian Knowledge Tracing (BKT) Service.
Part of KT-RL Phase 2: Knowledge Tracing Engine & Learner State Modeling.

Implements standard single-skill Bayesian Knowledge Tracing:
  P(L0): Initial knowledge probability
  P(T):  Transition probability (learning step)
  P(G):  Guess probability (correct answer without mastery)
  P(S):  Slip probability (incorrect answer despite mastery)

Includes:
- Parameter validation and bounded observation updates.
- Chronological event replay over SQLite learner event store.
- Independent multi-KC update approximation with explicit documentation.
- Evidence quality tracking and assessment status flags.
- Deterministic state reconstruction and parameter versioning.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default heuristic parameter version
BKT_DEFAULT_VERSION = "bkt-heuristic-v1"


@dataclass(frozen=True)
class BKTParameters:
    """Represents a validated parameter set for Bayesian Knowledge Tracing."""
    p_l0: float = 0.20  # P(L0): Initial probability of knowing skill
    p_t: float = 0.15   # P(T):  Probability of learning transition
    p_g: float = 0.20   # P(G):  Probability of guess
    p_s: float = 0.10   # P(S):  Probability of slip
    version: str = BKT_DEFAULT_VERSION
    is_calibrated: bool = False  # Explicit flag: heuristic assumption vs fitted

    def __post_init__(self):
        for name, val in [("p_l0", self.p_l0), ("p_t", self.p_t), ("p_g", self.p_g), ("p_s", self.p_s)]:
            if not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                raise ValueError(f"Parameter '{name}' must be a float in [0.0, 1.0], got {val}")
        # Safeguard: Guess + Slip < 1.0 is a standard identifiability constraint for BKT
        if self.p_g + self.p_s >= 1.0:
            raise ValueError(
                f"Degenerate BKT parameters: P(G) + P(S) = {self.p_g + self.p_s:.3f} >= 1.0. "
                "Guess and slip must sum to less than 1.0 to ensure learning provides positive informational value."
            )


DEFAULT_PARAMS = BKTParameters()


def bkt_observation_update(p_known: float, is_correct: bool, params: BKTParameters = DEFAULT_PARAMS) -> float:
    """
    Computes the posterior mastery probability P(K | response) given prior mastery p_known and response correctness.

    Equations:
      Correct response:
        P(K | C) = [p * (1 - S)] / [p * (1 - S) + (1 - p) * G]

      Incorrect response:
        P(K | I) = [p * S] / [p * S + (1 - p) * (1 - G)]

    Returns:
      Posterior probability in [0.0, 1.0].
    """
    if not (0.0 <= p_known <= 1.0):
        raise ValueError(f"Prior probability p_known must be in [0.0, 1.0], got {p_known}")

    p = float(p_known)
    p_s = params.p_s
    p_g = params.p_g

    if is_correct:
        num = p * (1.0 - p_s)
        denom = num + (1.0 - p) * p_g
    else:
        num = p * p_s
        denom = num + (1.0 - p) * (1.0 - p_g)

    # Division-by-zero safeguard with numerical clipping
    if denom <= 1e-12:
        return 0.0 if not is_correct else 1.0

    post = num / denom
    # Clamp to [0.0, 1.0] to prevent floating point drift
    return max(0.0, min(1.0, post))


def bkt_transition_update(p_posterior: float, params: BKTParameters = DEFAULT_PARAMS) -> float:
    """
    Applies the learning transition update:
      P(K_next) = P(K | response) + (1 - P(K | response)) * P(T)

    Returns:
      Updated probability of mastery for the next opportunity in [0.0, 1.0].
    """
    if not (0.0 <= p_posterior <= 1.0):
        raise ValueError(f"Posterior probability must be in [0.0, 1.0], got {p_posterior}")

    p_next = p_posterior + (1.0 - p_posterior) * params.p_t
    return max(0.0, min(1.0, p_next))


def bkt_step(p_prior: float, is_correct: bool, params: BKTParameters = DEFAULT_PARAMS) -> Tuple[float, float]:
    """
    Executes a complete BKT step: observation update followed by learning transition.
    Returns:
      (posterior_after_observation, next_prior_after_transition)
    """
    p_post = bkt_observation_update(p_prior, is_correct, params)
    p_next = bkt_transition_update(p_post, params)
    return p_post, p_next


@dataclass
class KCState:
    """Represents the estimated mastery state of a single Knowledge Component."""
    kc_id: str
    mastery_probability: float  # Current P(K_next)
    prior_probability: float    # Probability before last observation
    observation_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    status: str = "not_assessed"  # "not_assessed" (0 obs) vs "assessed" (>= 1 obs)
    evidence_quality: str = "none"  # "none", "limited" (1-4), "moderate" (5-9), "solid" (>= 10)
    last_observed_timestamp: Optional[str] = None
    last_event_id: Optional[str] = None
    parameter_version: str = BKT_DEFAULT_VERSION
    parameters_calibrated: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kc_id": self.kc_id,
            "mastery_probability": round(self.mastery_probability, 4),
            "mastery_pct": round(self.mastery_probability * 100, 1),
            "prior_probability": round(self.prior_probability, 4),
            "observation_count": self.observation_count,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "status": self.status,
            "evidence_quality": self.evidence_quality,
            "last_observed_timestamp": self.last_observed_timestamp,
            "last_event_id": self.last_event_id,
            "parameter_version": self.parameter_version,
            "parameters_calibrated": self.parameters_calibrated,
            "notes": self.notes,
        }


def compute_evidence_quality(observation_count: int) -> str:
    if observation_count == 0:
        return "none"
    elif observation_count < 5:
        return "limited"
    elif observation_count < 10:
        return "moderate"
    else:
        return "solid"


def initialize_kc_state(kc_id: str, params: BKTParameters = DEFAULT_PARAMS) -> KCState:
    return KCState(
        kc_id=kc_id,
        mastery_probability=params.p_l0,
        prior_probability=params.p_l0,
        observation_count=0,
        correct_count=0,
        incorrect_count=0,
        status="not_assessed",
        evidence_quality="none",
        parameter_version=params.version,
        parameters_calibrated=params.is_calibrated,
        notes="Initialized with default heuristic prior; no learner observations recorded.",
    )


def update_kc_mastery(
    state: KCState,
    is_correct: bool,
    event_timestamp: Optional[str] = None,
    event_id: Optional[str] = None,
    params: BKTParameters = DEFAULT_PARAMS,
) -> KCState:
    """Updates a KC state following an observed response."""
    prior = state.mastery_probability
    p_post, p_next = bkt_step(prior, is_correct, params)

    obs_count = state.observation_count + 1
    corr_count = state.correct_count + (1 if is_correct else 0)
    incorr_count = state.incorrect_count + (0 if is_correct else 1)

    return KCState(
        kc_id=state.kc_id,
        mastery_probability=p_next,
        prior_probability=prior,
        observation_count=obs_count,
        correct_count=corr_count,
        incorrect_count=incorr_count,
        status="assessed",
        evidence_quality=compute_evidence_quality(obs_count),
        last_observed_timestamp=event_timestamp,
        last_event_id=event_id,
        parameter_version=params.version,
        parameters_calibrated=params.is_calibrated,
        notes=f"Updated via Bayesian rule from prior {prior:.3f} to posterior {p_post:.3f} and transition {p_next:.3f}.",
    )


def replay_learner_history(
    learner_id: str,
    events: Optional[List[Dict[str, Any]]] = None,
    params: BKTParameters = DEFAULT_PARAMS,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Reconstructs complete knowledge-tracing state for a learner by chronologically replaying all valid interaction events.

    Multi-KC update strategy:
      When an item maps to multiple Knowledge Components, each KC is updated independently using its current
      prior and the observed item correctness. This is an explicit first-order approximation documented in the audit.

    Returns:
      Dictionary containing:
        - learner_id
        - model: 'BKT'
        - parameter_version
        - topics: dict of kc_id -> KCState dict
        - unmapped_event_count
        - total_events_processed
        - replayed_at
    """
    from resources import TOPIC_CATALOG, get_question_by_id
    from services.learning_store import get_learner_events

    # If events list not provided, query the persistent store
    if events is None:
        events = get_learner_events(learner_id, limit=2000, reverse=False, db_path=db_path)

    # Initialize catalog KCs
    states: Dict[str, KCState] = {}
    for topic in TOPIC_CATALOG.keys():
        states[topic] = initialize_kc_state(topic, params)

    # Deterministic chronological sort with event_id tie-breaker
    sorted_events = sorted(
        events,
        key=lambda e: (e.get("event_timestamp") or "", e.get("event_id") or "")
    )

    unmapped_count = 0
    processed_count = 0
    excluded_count = 0

    for evt in sorted_events:
        item_id = evt.get("item_id")
        # Extract knowledge components: from event payload first, fallback to static item bank
        kcs = evt.get("knowledge_components")
        if isinstance(kcs, str):
            try:
                kcs = json.loads(kcs)
            except Exception:
                kcs = [kcs]
        if not kcs or not isinstance(kcs, list) or len(kcs) == 0:
            q_meta = get_question_by_id(item_id)
            if q_meta:
                kcs = q_meta.get("knowledge_components", [])

        if not kcs:
            unmapped_count += 1
            continue

        # Correctness evaluation
        is_corr_raw = evt.get("is_correct")
        if is_corr_raw is None:
            is_corr_raw = evt.get("correctness")
        if is_corr_raw is None:
            excluded_count += 1
            continue

        is_corr = bool(int(is_corr_raw))
        event_ts = evt.get("event_timestamp")
        event_id = evt.get("event_id")

        # Independent multi-KC update
        for kc in kcs:
            kc_clean = str(kc).strip().lower()
            if kc_clean not in states:
                states[kc_clean] = initialize_kc_state(kc_clean, params)

            states[kc_clean] = update_kc_mastery(
                states[kc_clean],
                is_correct=is_corr,
                event_timestamp=event_ts,
                event_id=event_id,
                params=params,
            )

        processed_count += 1

    return {
        "learner_id": learner_id,
        "model": "BKT",
        "parameter_version": params.version,
        "parameters_calibrated": params.is_calibrated,
        "parameters": asdict(params),
        "total_events_processed": processed_count,
        "unmapped_event_count": unmapped_count,
        "excluded_event_count": excluded_count,
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "topics": [s.to_dict() for s in states.values()],
        "topics_map": {k: s.to_dict() for k, s in states.items()},
    }


def get_mastery_by_learner(
    learner_id: str,
    params: BKTParameters = DEFAULT_PARAMS,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves current BKT mastery state for a learner."""
    return replay_learner_history(learner_id, params=params, db_path=db_path)


def get_kc_mastery(
    learner_id: str,
    kc_id: str,
    params: BKTParameters = DEFAULT_PARAMS,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves BKT mastery state for a specific Knowledge Component."""
    history = get_mastery_by_learner(learner_id, params=params, db_path=db_path)
    kc_clean = str(kc_id).strip().lower()
    return history["topics_map"].get(kc_clean)
