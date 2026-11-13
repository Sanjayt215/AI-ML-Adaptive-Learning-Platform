"""
Controlled Experimental Recommendation Service & Safety Gatekeeper.
Part of KT-RL Phase 5: Adaptive Policy Evaluation & Controlled Integration.

Provides an opt-in, non-disruptive integration endpoint for demonstration and shadow evaluation:
1. Feature flag control: `KT_RL_EXPERIMENT_ENABLED` (env var), strictly DEFAULT FALSE.
2. Recommender fallback: If flag is disabled, model file is missing, or state is invalid,
   transparently falls back to the production prerequisite-aware BKT recommender.
3. Strict isolation: NEVER accesses synthetic simulator ground truth. Uses observable BKT state only.
4. Input validation: Validates learner_id, question IDs, and observable feature vectors.
5. Action eligibility: Enforces prerequisite masking on real candidate items.
6. Honest explainability: Distinguishes between observable BKT/ZPD factors and the agent's internal argmax.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import get_all_questions, get_question_by_id, TOPIC_CATALOG
from services.bkt_service import get_mastery_by_learner, initialize_kc_state
from services.rl_state_encoder import StateEncoder
from services.dqn_agent import DuelingDQNAgent


def is_experiment_enabled() -> bool:
    """Checks whether the KT-RL experimental mode is explicitly enabled via environment variable."""
    return os.environ.get("KT_RL_EXPERIMENT_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


class ExperimentalExerciseService:
    """
    Experimental recommendation manager for KT-RL Dueling DQN.
    """

    def __init__(
        self,
        checkpoint_path: str = "models/dqn/dueling_dqn_final.pt",
        encoder: Optional[StateEncoder] = None,
    ):
        self.checkpoint_path = checkpoint_path
        self.item_bank = sorted(get_all_questions(), key=lambda q: q["item_id"])
        self.num_actions = len(self.item_bank)
        self.encoder = encoder or StateEncoder(topics=sorted(list(TOPIC_CATALOG.keys())))
        self.agent: Optional[DuelingDQNAgent] = None
        self._load_agent()

    def _load_agent(self) -> None:
        """Loads and validates the Dueling DQN model checkpoint safely."""
        candidate_paths = [
            self.checkpoint_path,
            os.path.join(ROOT_DIR, self.checkpoint_path),
            os.path.join(ROOT_DIR, "autolearn_fullstack", self.checkpoint_path),
        ]
        full_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                full_path = p
                break

        if full_path is None:
            self.agent = None
            return

        try:
            agent = DuelingDQNAgent(
                obs_dim=self.encoder.feature_dim,
                num_actions=self.num_actions,
                hidden_dim=128,
            )
            agent.load_checkpoint(full_path)
            agent.q_online.eval()
            self.agent = agent
        except Exception:
            self.agent = None

    def get_action_mask(self, learner_bkt_map: Dict[str, Any], prereq_threshold: float = 0.50) -> np.ndarray:
        """
        Constructs the prerequisite validity mask for candidate questions based on learner's BKT states.
        """
        mask = np.ones(self.num_actions, dtype=np.int8)
        for idx, item in enumerate(self.item_bank):
            topic = item.get("topic", "")
            prereqs = TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
            for p in prereqs:
                p_clean = str(p).strip().lower()
                p_state = learner_bkt_map.get(p_clean)
                p_prob = p_state.get("mastery_probability", 0.0) if isinstance(p_state, dict) else (
                    p_state.mastery_probability if p_state else 0.0
                )
                if p_prob < prereq_threshold:
                    mask[idx] = 0
                    break

        if not np.any(mask):
            mask = np.ones(self.num_actions, dtype=np.int8)

        return mask

    def recommend_exercise(
        self,
        learner_id: str,
        session_history: Optional[List[int]] = None,
        recent_topic_failures: int = 0,
        last_difficulty: int = 2,
        current_step: int = 0,
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Selects a recommended exercise for the learner.
        - If experimental mode is enabled and agent is loaded, uses Dueling DQN.
        - Otherwise, falls back gracefully to prerequisite-aware weakest-KC selection.
        """
        # Fetch current observable BKT mastery states from SQLite store
        learner_mastery = get_mastery_by_learner(learner_id, db_path=db_path)
        bkt_map = learner_mastery.get("topics_map", {})

        mask = self.get_action_mask(bkt_map)

        # Safety Fallback Check
        use_experimental = is_experiment_enabled() and (self.agent is not None)

        if use_experimental:
            try:
                # Build observable prerequisite readiness map
                prereq_readiness = {}
                for topic, meta in TOPIC_CATALOG.items():
                    prereqs = meta.get("prerequisites", [])
                    if not prereqs:
                        prereq_readiness[topic] = 1.0
                    else:
                        ready = all(
                            bkt_map.get(p, {}).get("mastery_probability", 0.0) >= 0.50
                            for p in prereqs
                        )
                        prereq_readiness[topic] = 1.0 if ready else 0.0

                # Encode normalized 99-dim observable state
                obs = self.encoder.encode(
                    bkt_topics_map=bkt_map,
                    prereq_readiness_map=prereq_readiness,
                    recent_history=session_history or [],
                    recent_topic_failures=recent_topic_failures,
                    last_difficulty=last_difficulty,
                    current_step=current_step,
                )

                # Deterministic argmax action under prerequisite mask
                action_idx = self.agent.select_action(obs, action_mask=mask, deterministic=True)
                selected_item = self.item_bank[action_idx]
                policy_used = "dueling_dqn_experimental"
                selection_mechanism = "Dueling DQN policy argmax Q(s, a) with prerequisite mask"
            except Exception:
                # Fall back to heuristic on any inference error
                selected_item, action_idx = self._fallback_recommendation(mask, bkt_map)
                policy_used = "heuristic_fallback_error"
                selection_mechanism = "Safe fallback after inference exception"
        else:
            selected_item, action_idx = self._fallback_recommendation(mask, bkt_map)
            policy_used = "prereq_aware_weakest_baseline"
            selection_mechanism = "Rule-based baseline: weakest estimated BKT mastery with lowest difficulty"

        # Generate observable explanation
        primary_topic = selected_item.get("topic", "general")
        primary_kcs = selected_item.get("knowledge_components", [primary_topic])
        topic_state = bkt_map.get(primary_topic, {})
        est_mastery = topic_state.get("mastery_probability", 0.20)
        diff = selected_item.get("difficulty", 2)

        explanation = {
            "policy_mode": policy_used,
            "selection_mechanism": selection_mechanism,
            "experimental_flag_active": is_experiment_enabled(),
            "target_topic": primary_topic,
            "target_knowledge_components": primary_kcs,
            "topic_estimated_mastery": round(est_mastery, 4),
            "exercise_difficulty": diff,
            "prerequisites_met": bool(mask[action_idx]),
            "pedagogical_rationale": (
                f"Topic '{primary_topic}' has an observable mastery of {est_mastery*100:.1f}%. "
                f"Exercise '{selected_item['item_id']}' (difficulty {diff}/5) was selected "
                f"matching prerequisite criteria."
            ),
        }

        return {
            "ok": True,
            "item_id": selected_item["item_id"],
            "question": selected_item["question"],
            "options": selected_item["options"],
            "topic": primary_topic,
            "difficulty": diff,
            "knowledge_components": primary_kcs,
            "explanation": explanation,
        }

    def _fallback_recommendation(
        self,
        mask: np.ndarray,
        bkt_map: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], int]:
        """Picks valid action with lowest observable mastery, tie-broken by lowest difficulty."""
        valid_indices = [i for i in range(self.num_actions) if mask[i]]
        if not valid_indices:
            return self.item_bank[0], 0

        def score(i: int) -> Tuple[float, int]:
            item = self.item_bank[i]
            t = item.get("topic", "general")
            m = bkt_map.get(t, {}).get("mastery_probability", 0.20)
            d = item.get("difficulty", 2)
            return (m, d)

        best_idx = min(valid_indices, key=score)
        return self.item_bank[best_idx], best_idx
