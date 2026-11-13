"""
Adaptive Exploration & Assessment Selection Controller.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Balances diagnostic assessment probes with pedagogical mastery practice:
1. Dynamic Assessment Gating: If learner evidence is low (< 2 observations per KC)
   and entropy is high (H(p) > 0.8), triggers a diagnostic exploration probe.
2. Anti-Trap Safeguards: Caps diagnostic probes to max 2 consecutive probes per KC,
   preventing the system from endlessly questioning uncertain topics without practice.
3. Prerequisite Invariant: Exploration NEVER bypasses prerequisite eligibility.
4. Difficulty Suitability: Diagnostic items are restricted to foundational difficulties (1 or 2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from resources import get_all_questions, TOPIC_CATALOG


@dataclass
class ExplorationConfig:
    min_evidence_threshold: int = 2     # Below this attempt count, KC is candidate for probe
    high_entropy_threshold: float = 0.80 # Shannon entropy threshold for diagnostic value
    max_consecutive_probes: int = 2     # Cap on diagnostic questions for the same KC
    diagnostic_max_difficulty: int = 2  # Probes should use beginner/intermediate items


class AdaptiveExplorationController:
    """
    Pedagogical exploration manager that dynamically selects between:
    - Diagnostic Probe (identifying latent student baseline)
    - Learning Practice (remediating identified deficits or spaced review)
    """

    def __init__(self, config: Optional[ExplorationConfig] = None):
        self.config = config or ExplorationConfig()
        self.consecutive_probes_by_kc: Dict[str, int] = {}

    def should_explore(
        self,
        kc_id: str,
        bkt_mastery: float,
        attempt_count: int,
    ) -> bool:
        """Determines whether a KC warrants a diagnostic exploration probe."""
        # 1. Probe cap check
        if self.consecutive_probes_by_kc.get(kc_id, 0) >= self.config.max_consecutive_probes:
            return False

        # 2. Evidence threshold
        if attempt_count >= self.config.min_evidence_threshold:
            return False

        # 3. Shannon entropy calculation
        p = max(1e-5, min(1.0 - 1e-5, bkt_mastery))
        entropy = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)

        return entropy >= self.config.high_entropy_threshold

    def select_action(
        self,
        bkt_map: Dict[str, Any],
        action_mask: np.ndarray,
        item_bank: List[Dict[str, Any]],
        fallback_action_fn: Any = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Selects next question action considering adaptive exploration.
        Returns: (selected_action_idx, decision_metadata)
        """
        valid_indices = [i for i in range(len(item_bank)) if action_mask[i]]
        if not valid_indices:
            return 0, {"mode": "fallback_no_valid", "kc": "none"}

        # Check for eligible diagnostic probe candidates
        probe_candidates = []
        for idx in valid_indices:
            item = item_bank[idx]
            kcs = item.get("knowledge_components", [])
            primary_kc = kcs[0] if kcs else item.get("topic", "python")
            diff = item.get("difficulty", 2)

            kc_state = bkt_map.get(primary_kc, {})
            p_val = kc_state.get("mastery_probability", 0.20) if isinstance(kc_state, dict) else getattr(kc_state, "mastery_probability", 0.20)
            attempts = kc_state.get("attempt_count", 0) if isinstance(kc_state, dict) else getattr(kc_state, "attempt_count", 0)

            if diff <= self.config.diagnostic_max_difficulty:
                if self.should_explore(primary_kc, p_val, attempts):
                    probe_candidates.append((idx, primary_kc))

        if probe_candidates:
            # Select first diagnostic probe candidate
            chosen_idx, chosen_kc = probe_candidates[0]
            self.consecutive_probes_by_kc[chosen_kc] = self.consecutive_probes_by_kc.get(chosen_kc, 0) + 1
            return chosen_idx, {
                "mode": "diagnostic_probe",
                "kc": chosen_kc,
                "consecutive_probes": self.consecutive_probes_by_kc[chosen_kc],
            }

        # Otherwise, fall back to learning practice
        if fallback_action_fn is not None:
            chosen = fallback_action_fn()
        else:
            chosen = valid_indices[0]

        # Reset consecutive probe count on selected practice KC
        item = item_bank[chosen]
        kcs = item.get("knowledge_components", [])
        primary = kcs[0] if kcs else item.get("topic", "python")
        self.consecutive_probes_by_kc[primary] = 0

        return chosen, {"mode": "learning_practice", "kc": primary}
