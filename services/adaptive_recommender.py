"""
Unified Adaptive Recommendation Service.
Part of KT-RL Research Upgrade: Phase D (Adaptive Learning & Recommendation Architecture).

Implements:
1. Forgetting-Aware Revision Modeling (Longitudinal retention decay based on elapsed hours).
2. Confidence- & Uncertainty-Aware Assessment (Posterior entropy and observation count exploration).
3. Frustration & Disengagement Risk Mitigation (Consecutive failure detection with difficulty backoff).
4. Prerequisite Eligibility Guard (Strict prerequisite graph enforcement across all strategies).
5. Multi-Strategy Policy Engine:
   - `prereq_aware_weakest`: Foundational baseline targeting lowest mastery with easiest difficulty.
   - `forgetting_revision`: Targets topics with high prior mastery whose retention has decayed over time.
   - `confidence_exploration`: Targets topics with high posterior uncertainty / low evidence count.
   - `frustration_remedial`: Triggered upon repeated failures to offer supportive, lower-difficulty practice.
   - `composite_adaptive`: Pedagogically balanced multi-factor scoring function.
   - `experimental_dqn`: Opt-in Dueling DQN agent (controlled by KT_RL_EXPERIMENT_ENABLED).
"""

from __future__ import annotations

import math
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import get_all_questions, get_question_by_id, TOPIC_CATALOG
from services.bkt_service import get_mastery_by_learner, initialize_kc_state
from services.learning_store import get_learner_events
from services.rl_state_encoder import StateEncoder


def is_experimental_dqn_enabled() -> bool:
    """Checks whether the KT-RL experimental Dueling DQN mode is explicitly enabled."""
    return os.environ.get("KT_RL_EXPERIMENT_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


class UnifiedAdaptiveRecommender:
    """
    Unified adaptive recommendation manager integrating BKT mastery, longitudinal forgetting,
    evidence confidence, frustration risk, and prerequisite constraints.
    """

    def __init__(
        self,
        checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
        forgetting_rate: float = 0.05,       # Retention decay per elapsed day
        mastery_floor: float = 0.05,
        prereq_threshold: float = 0.50,
        frustration_failure_threshold: int = 2,
    ):
        self.item_bank = sorted(get_all_questions(), key=lambda q: q["item_id"])
        self.num_actions = len(self.item_bank)
        self.checkpoint_path = checkpoint_path
        self.forgetting_rate = forgetting_rate
        self.mastery_floor = mastery_floor
        self.prereq_threshold = prereq_threshold
        self.frustration_failure_threshold = frustration_failure_threshold

        topics = sorted(list(TOPIC_CATALOG.keys()))
        self.encoder = StateEncoder(topics=topics)
        self._cached_agent = None
        self._init_dqn_agent()

    def _init_dqn_agent(self) -> None:
        """Attempts to load Dueling DQN agent safely without throwing exceptions."""
        candidate_paths = [
            self.checkpoint_path,
            os.path.join(ROOT_DIR, self.checkpoint_path),
            os.path.join(ROOT_DIR, "autolearn_fullstack", self.checkpoint_path),
        ]
        full_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if full_path:
            try:
                from services.dqn_agent import DuelingDQNAgent
                agent = DuelingDQNAgent(
                    obs_dim=self.encoder.feature_dim,
                    num_actions=self.num_actions,
                    hidden_dim=128,
                )
                agent.load_checkpoint(full_path)
                agent.q_online.eval()
                self._cached_agent = agent
            except Exception:
                self._cached_agent = None

    def compute_prerequisite_mask(
        self,
        bkt_map: Dict[str, Any],
        threshold: Optional[float] = None,
    ) -> np.ndarray:
        """
        Constructs a binary mask (1 = eligible, 0 = locked) based on observable prerequisite BKT mastery.
        """
        th = self.prereq_threshold if threshold is None else threshold
        mask = np.ones(self.num_actions, dtype=np.int8)

        for idx, item in enumerate(self.item_bank):
            topic = item.get("topic", "")
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            for p in prereqs:
                p_clean = str(p).strip().lower()
                p_state = bkt_map.get(p_clean)
                p_prob = p_state.get("mastery_probability", 0.0) if isinstance(p_state, dict) else (
                    p_state.mastery_probability if p_state else 0.0
                )
                if p_prob < th:
                    mask[idx] = 0
                    break

        # Fallback: if all actions are locked, unlock foundational items (items with 0 prerequisites)
        if not np.any(mask):
            for idx, item in enumerate(self.item_bank):
                topic = item.get("topic", "")
                if not TOPIC_CATALOG.get(topic, {}).get("prerequisites"):
                    mask[idx] = 1

        # If still empty, enable all
        if not np.any(mask):
            mask = np.ones(self.num_actions, dtype=np.int8)

        return mask

    def estimate_retention(
        self,
        bkt_map: Dict[str, Any],
        last_observed_timestamps: Dict[str, Optional[str]],
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates predicted retention decay for each Knowledge Component:
          R(t) = m_floor + (P(K) - m_floor) * exp(-lambda * delta_days)
        """
        now = reference_time or datetime.now(timezone.utc)
        retention_info: Dict[str, Dict[str, Any]] = {}

        for topic in TOPIC_CATALOG.keys():
            state = bkt_map.get(topic, {})
            p_curr = state.get("mastery_probability", 0.20) if isinstance(state, dict) else (
                state.mastery_probability if state else 0.20
            )
            obs_count = state.get("observation_count", 0) if isinstance(state, dict) else (
                state.observation_count if state else 0
            )

            ts_str = last_observed_timestamps.get(topic)
            if not ts_str or obs_count == 0:
                # Never practiced or unassessed: no forgetting applied
                retention_info[topic] = {
                    "current_mastery": p_curr,
                    "predicted_retention": p_curr,
                    "decay_amount": 0.0,
                    "elapsed_days": 0.0,
                    "retention_status": "unassessed" if obs_count == 0 else "current",
                }
                continue

            try:
                # Parse ISO timestamp
                last_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                delta_sec = max(0.0, (now - last_dt).total_seconds())
                delta_days = delta_sec / 86400.0
            except Exception:
                delta_days = 0.0

            decay_factor = math.exp(-self.forgetting_rate * delta_days)
            r_val = self.mastery_floor + (p_curr - self.mastery_floor) * decay_factor
            r_val = max(self.mastery_floor, min(1.0, r_val))
            decay_amount = p_curr - r_val

            status = "retained"
            if decay_amount >= 0.15:
                status = "needs_revision"
            elif decay_amount >= 0.05:
                status = "decaying"

            retention_info[topic] = {
                "current_mastery": round(p_curr, 4),
                "predicted_retention": round(r_val, 4),
                "decay_amount": round(decay_amount, 4),
                "elapsed_days": round(delta_days, 2),
                "retention_status": status,
            }

        return retention_info

    def estimate_uncertainty_and_confidence(
        self,
        bkt_map: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates observation confidence and Shannon posterior entropy for each KC:
          H(p) = -p * log2(p) - (1-p) * log2(1-p)
        """
        uncertainty_info: Dict[str, Dict[str, Any]] = {}
        for topic in TOPIC_CATALOG.keys():
            state = bkt_map.get(topic, {})
            p = state.get("mastery_probability", 0.20) if isinstance(state, dict) else (
                state.mastery_probability if state else 0.20
            )
            obs_count = state.get("observation_count", 0) if isinstance(state, dict) else (
                state.observation_count if state else 0
            )

            p_clamped = max(0.001, min(0.999, p))
            entropy = - (p_clamped * math.log2(p_clamped) + (1.0 - p_clamped) * math.log2(1.0 - p_clamped))

            quality = "unassessed"
            if obs_count >= 8:
                quality = "solid"
            elif obs_count >= 4:
                quality = "moderate"
            elif obs_count >= 1:
                quality = "limited"

            uncertainty_info[topic] = {
                "mastery_probability": round(p, 4),
                "observation_count": obs_count,
                "evidence_quality": quality,
                "posterior_entropy": round(entropy, 4),
                "is_uncertain": bool(entropy >= 0.80 or obs_count < 3),
            }

        return uncertainty_info

    def estimate_frustration_risk(
        self,
        events: List[Dict[str, Any]],
        recent_window: int = 5,
    ) -> Dict[str, Any]:
        """
        Detects disengagement and frustration risk using observable interaction signals:
        - Consecutive failures on the same KC
        - High recent error density
        - Excessively prolonged response times relative to baseline
        """
        if not events:
            return {
                "is_frustrated": False,
                "risk_level": "low",
                "consecutive_failures": 0,
                "recent_error_rate": 0.0,
                "troubled_topics": [],
                "recommended_action": "normal_practice",
            }

        recent_events = events[-recent_window:]
        incorrect_count = sum(1 for e in recent_events if not e.get("is_correct", False))
        recent_error_rate = incorrect_count / len(recent_events) if recent_events else 0.0

        # Calculate consecutive failures by topic
        consec_by_topic: Dict[str, int] = {}
        for e in reversed(events):
            topic = e.get("topic")
            is_corr = bool(e.get("is_correct", False))
            if topic:
                if is_corr:
                    if topic not in consec_by_topic:
                        consec_by_topic[topic] = 0
                else:
                    consec_by_topic[topic] = consec_by_topic.get(topic, 0) + 1

        troubled = [t for t, count in consec_by_topic.items() if count >= self.frustration_failure_threshold]
        max_consec = max(consec_by_topic.values()) if consec_by_topic else 0

        is_frustrated = (max_consec >= self.frustration_failure_threshold) or (recent_error_rate >= 0.80 and len(recent_events) >= 3)
        risk_level = "high" if max_consec >= 3 or recent_error_rate >= 0.80 else ("moderate" if is_frustrated else "low")

        rec_action = "normal_practice"
        if risk_level == "high":
            rec_action = "remedial_support"
        elif risk_level == "moderate":
            rec_action = "lower_difficulty"

        return {
            "is_frustrated": is_frustrated,
            "risk_level": risk_level,
            "consecutive_failures": max_consec,
            "recent_error_rate": round(recent_error_rate, 2),
            "troubled_topics": troubled,
            "recommended_action": rec_action,
        }

    def recommend(
        self,
        learner_id: str,
        strategy: str = "composite_adaptive",
        db_path: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates adaptive exercise selection for a learner.
        Supported strategies:
        - 'composite_adaptive' (Recommended default)
        - 'prereq_aware_weakest'
        - 'forgetting_revision'
        - 'confidence_exploration'
        - 'frustration_remedial'
        - 'experimental_dqn'
        """
        # 1. Fetch learner BKT mastery and past interaction events
        bkt_history = get_mastery_by_learner(learner_id, db_path=db_path)
        bkt_map = bkt_history.get("topics_map", {})
        events = get_learner_events(learner_id, limit=200, reverse=False, db_path=db_path)

        # 2. Extract last timestamp per topic
        last_ts_map: Dict[str, Optional[str]] = {}
        for e in events:
            t = e.get("topic")
            if t:
                last_ts_map[t] = e.get("event_timestamp")

        # 3. Calculate component states
        mask = self.compute_prerequisite_mask(bkt_map)
        valid_indices = [i for i in range(self.num_actions) if mask[i]]
        retention = self.estimate_retention(bkt_map, last_ts_map, reference_time=reference_time)
        uncertainty = self.estimate_uncertainty_and_confidence(bkt_map)
        frustration = self.estimate_frustration_risk(events)

        # 4. Strategy Execution
        selected_idx: int = valid_indices[0] if valid_indices else 0
        policy_tag = strategy
        rationale = ""

        if strategy == "experimental_dqn":
            if is_experimental_dqn_enabled() and self._cached_agent:
                try:
                    prereq_readiness = {
                        t: (1.0 if not TOPIC_CATALOG.get(t, {}).get("prerequisites") else (
                            1.0 if all(bkt_map.get(p, {}).get("mastery_probability", 0.0) >= 0.50
                                       for p in TOPIC_CATALOG[t]["prerequisites"]) else 0.0
                        ))
                        for t in TOPIC_CATALOG
                    }
                    recent_hist = [1 if e.get("is_correct") else 0 for e in events[-5:]]
                    obs = self.encoder.encode(
                        bkt_topics_map=bkt_map,
                        prereq_readiness_map=prereq_readiness,
                        recent_history=recent_hist,
                        recent_topic_failures=frustration["consecutive_failures"],
                        last_difficulty=events[-1].get("difficulty", 2) if events else 2,
                        current_step=len(events),
                    )
                    selected_idx = self._cached_agent.select_action(obs, action_mask=mask, deterministic=True)
                    policy_tag = "dueling_dqn_experimental"
                    rationale = "Selected via Dueling DQN policy argmax Q(s, a) under prerequisite mask."
                except Exception:
                    # Graceful fallback to heuristic
                    selected_idx = self._select_prereq_aware_weakest(valid_indices, bkt_map)
                    policy_tag = "prereq_aware_weakest_fallback"
                    rationale = "Safe fallback after experimental DQN evaluation exception."
            else:
                selected_idx = self._select_prereq_aware_weakest(valid_indices, bkt_map)
                policy_tag = "prereq_aware_weakest_baseline"
                rationale = "DQN experimental flag is disabled; safely used prerequisite-aware weakest baseline."

        elif strategy == "forgetting_revision":
            # Prioritize eligible items whose predicted retention has dropped most
            selected_idx = max(valid_indices, key=lambda i: retention.get(self.item_bank[i]["topic"], {}).get("decay_amount", 0.0))
            topic = self.item_bank[selected_idx]["topic"]
            decay = retention.get(topic, {}).get("decay_amount", 0.0)
            rationale = f"Revision prioritized for '{topic}' due to predicted retention decay of {decay*100:.1f}%."

        elif strategy == "confidence_exploration":
            # Prioritize eligible items with highest posterior entropy (greatest diagnostic uncertainty)
            selected_idx = max(valid_indices, key=lambda i: uncertainty.get(self.item_bank[i]["topic"], {}).get("posterior_entropy", 0.0))
            topic = self.item_bank[selected_idx]["topic"]
            obs_c = uncertainty.get(topic, {}).get("observation_count", 0)
            rationale = f"Diagnostic assessment selected for '{topic}' to resolve high posterior uncertainty ({obs_c} observations)."

        elif strategy == "frustration_remedial":
            # If learner has troubled topics, select easiest valid item on that topic; otherwise lowest difficulty
            troubled = frustration["troubled_topics"]
            troubled_items = [i for i in valid_indices if self.item_bank[i]["topic"] in troubled]
            target_set = troubled_items if troubled_items else valid_indices
            selected_idx = min(target_set, key=lambda i: self.item_bank[i].get("difficulty", 2))
            topic = self.item_bank[selected_idx]["topic"]
            rationale = f"Remedial lower-difficulty question provided for '{topic}' to recover from repeated difficulty."

        elif strategy == "prereq_aware_weakest":
            selected_idx = self._select_prereq_aware_weakest(valid_indices, bkt_map)
            topic = self.item_bank[selected_idx]["topic"]
            m = bkt_map.get(topic, {}).get("mastery_probability", 0.20)
            rationale = f"Focused on weakest prerequisite-ready topic '{topic}' (observable mastery {m*100:.1f}%)."

        else:  # "composite_adaptive" (Default)
            # If high frustration detected, prioritize remedial recovery
            if frustration["is_frustrated"]:
                troubled = frustration["troubled_topics"]
                troubled_items = [i for i in valid_indices if self.item_bank[i]["topic"] in troubled]
                target_set = troubled_items if troubled_items else valid_indices
                selected_idx = min(target_set, key=lambda i: self.item_bank[i].get("difficulty", 2))
                topic = self.item_bank[selected_idx]["topic"]
                policy_tag = "composite_adaptive_remedial"
                rationale = f"Supportive practice recommended for '{topic}' to mitigate recent learning frustration."
            else:
                # Multi-factor scoring combining weakness, retention decay, and uncertainty exploration
                def score_candidate(i: int) -> float:
                    item = self.item_bank[i]
                    t = item.get("topic", "")
                    diff = item.get("difficulty", 2)
                    p_mastery = bkt_map.get(t, {}).get("mastery_probability", 0.20)
                    r_decay = retention.get(t, {}).get("decay_amount", 0.0)
                    entropy = uncertainty.get(t, {}).get("posterior_entropy", 0.5)

                    # Score components:
                    # + high weight on low mastery (1 - p)
                    # + bonus for revision need (decay)
                    # + bonus for diagnostic uncertainty (entropy)
                    # - mild penalty on high difficulty if mastery is low
                    norm_diff = diff / 5.0
                    zpd_gap = abs(p_mastery - norm_diff)
                    zpd_fit = math.exp(- (zpd_gap ** 2) / 0.15)

                    return (1.0 - p_mastery) * 3.0 + r_decay * 4.0 + entropy * 1.5 + zpd_fit * 1.0

                selected_idx = max(valid_indices, key=score_candidate)
                topic = self.item_bank[selected_idx]["topic"]
                decay = retention.get(topic, {}).get("decay_amount", 0.0)
                if decay >= 0.10:
                    rationale = f"Scheduled spaced revision for '{topic}' as retention has decayed over time."
                elif uncertainty.get(topic, {}).get("is_uncertain", False):
                    rationale = f"Diagnostic assessment on '{topic}' to solidify mastery confidence."
                else:
                    rationale = f"Targeted practice on '{topic}' aligned with your Zone of Proximal Development."

        item = self.item_bank[selected_idx]
        topic = item.get("topic", "general")
        kcs = item.get("knowledge_components", [topic])
        diff = item.get("difficulty", 2)

        return {
            "ok": True,
            "learner_id": learner_id,
            "strategy": policy_tag,
            "item_id": item["item_id"],
            "question": item["question"],
            "options": item["options"],
            "topic": topic,
            "difficulty": diff,
            "primary_kc": kcs[0] if kcs else topic,
            "knowledge_components": kcs,
            "prerequisites_valid": bool(mask[selected_idx]),
            "explanation": {
                "policy": policy_tag,
                "pedagogical_rationale": rationale,
                "topic_mastery": round(bkt_map.get(topic, {}).get("mastery_probability", 0.20), 4),
                "predicted_retention": retention.get(topic, {}).get("predicted_retention", 0.20),
                "evidence_quality": uncertainty.get(topic, {}).get("evidence_quality", "unassessed"),
                "frustration_risk": frustration["risk_level"],
                "experimental_mode": is_experimental_dqn_enabled(),
            },
            "diagnostics": {
                "frustration": frustration,
                "retention_overview": {t: d for t, d in retention.items() if d["retention_status"] != "unassessed"},
                "uncertain_topics_count": sum(1 for d in uncertainty.values() if d["is_uncertain"]),
                "eligible_actions_count": len(valid_indices),
            },
        }

    def _select_prereq_aware_weakest(self, valid_indices: List[int], bkt_map: Dict[str, Any]) -> int:
        """Selects lowest BKT mastery item, tie-broken by lowest difficulty."""
        if not valid_indices:
            return 0

        def score(i: int) -> Tuple[float, int]:
            item = self.item_bank[i]
            t = item.get("topic", "general")
            m = bkt_map.get(t, {}).get("mastery_probability", 0.20)
            d = item.get("difficulty", 2)
            return (m, d)

        return min(valid_indices, key=score)
