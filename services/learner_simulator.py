"""
Synthetic Learner Simulator.
Part of KT-RL Phase 3: Learner Simulator & Reinforcement Learning Environment.

Responsibilities:
- Models 4 distinct synthetic learner archetypes (Fast, Typical, Struggling, Inconsistent).
- Maintains hidden ground-truth mastery m in [0, 1] per Knowledge Component.
- Models response generation based on sigmoid sensitivity, item difficulty, and archetype noise.
- Implements bounded skill learning transitions upon practice opportunities.
- Implements exponential time-decay forgetting.
- Strictly encapsulates hidden simulation truth from agent-visible observations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class LearnerArchetype:
    """Configuration profile for a synthetic learner archetype."""
    name: str
    description: str
    learning_rate: float        # alpha: transition rate per practice opportunity
    base_sensitivity: float     # k: sigmoid sensitivity to mastery vs difficulty gap
    slip_rate: float            # Probability of accidental error despite high mastery
    guess_rate: float           # Probability of lucky guess despite low mastery
    forgetting_rate: float      # lambda: decay rate per elapsed unit time
    initial_mastery_mean: float # Mean of initial mastery beta/normal distribution
    initial_mastery_std: float  # Variance of initial mastery across topics
    noise_std: float            # Random execution noise added to response logit


ARCHETYPES: Dict[str, LearnerArchetype] = {
    "fast_learner": LearnerArchetype(
        name="fast_learner",
        description="Learns rapidly with high retention and low slip probability.",
        learning_rate=0.28,
        base_sensitivity=3.5,
        slip_rate=0.04,
        guess_rate=0.15,
        forgetting_rate=0.01,
        initial_mastery_mean=0.35,
        initial_mastery_std=0.12,
        noise_std=0.05,
    ),
    "typical_learner": LearnerArchetype(
        name="typical_learner",
        description="Moderate learning pace, standard retention, balanced responses.",
        learning_rate=0.16,
        base_sensitivity=2.5,
        slip_rate=0.09,
        guess_rate=0.20,
        forgetting_rate=0.03,
        initial_mastery_mean=0.22,
        initial_mastery_std=0.10,
        noise_std=0.08,
    ),
    "struggling_learner": LearnerArchetype(
        name="struggling_learner",
        description="Lower learning rate, higher slip chance, vulnerable to difficulty spikes.",
        learning_rate=0.08,
        base_sensitivity=2.0,
        slip_rate=0.18,
        guess_rate=0.18,
        forgetting_rate=0.06,
        initial_mastery_mean=0.12,
        initial_mastery_std=0.08,
        noise_std=0.12,
    ),
    "inconsistent_learner": LearnerArchetype(
        name="inconsistent_learner",
        description="Variable responses with higher guessing and lapse rates.",
        learning_rate=0.14,
        base_sensitivity=1.8,
        slip_rate=0.22,
        guess_rate=0.28,
        forgetting_rate=0.04,
        initial_mastery_mean=0.24,
        initial_mastery_std=0.15,
        noise_std=0.22,
    ),
}


class SyntheticLearner:
    """
    Simulates an individual learner with ground-truth latent mastery.
    Hidden true mastery values are strictly encapsulated and not leaked to the policy.
    """

    def __init__(
        self,
        archetype_name: str = "typical_learner",
        topics: Optional[List[str]] = None,
        seed: Optional[int] = None,
        mastery_floor: float = 0.05,
    ):
        if archetype_name not in ARCHETYPES:
            raise ValueError(f"Unknown archetype '{archetype_name}'. Choose from: {list(ARCHETYPES.keys())}")

        self.archetype = ARCHETYPES[archetype_name]
        self.rng = random.Random(seed)
        self.mastery_floor = mastery_floor
        self.simulated_time: float = 0.0  # Simulated continuous time steps

        # Import canonical topic catalog if topics not provided
        if topics is None:
            try:
                from resources import TOPIC_CATALOG
            except ImportError:
                from autolearn_fullstack.resources import TOPIC_CATALOG
            self.topics = sorted(list(TOPIC_CATALOG.keys()))
        else:
            self.topics = sorted(list(topics))

        # Hidden ground-truth mastery dictionary {kc_id: float in [0.0, 1.0]}
        self._hidden_mastery: Dict[str, float] = {}
        self._initialize_hidden_mastery()

    def _initialize_hidden_mastery(self) -> None:
        """Initializes diverse starting mastery levels per topic based on archetype."""
        mean = self.archetype.initial_mastery_mean
        std = self.archetype.initial_mastery_std

        for idx, topic in enumerate(self.topics):
            # Add mild topic-specific variance so foundational skills start slightly higher
            bonus = 0.08 if idx < 3 else -0.04 if idx > 20 else 0.0
            val = self.rng.gauss(mean + bonus, std)
            clamped = max(self.mastery_floor, min(0.95, val))
            self._hidden_mastery[topic] = clamped

    def get_hidden_mastery(self, kc_id: str) -> float:
        """Access hidden mastery (for environment evaluation/simulation ONLY)."""
        return self._hidden_mastery.get(kc_id, self.mastery_floor)

    def get_all_hidden_mastery(self) -> Dict[str, float]:
        """Returns a snapshot of hidden mastery dictionary."""
        return dict(self._hidden_mastery)

    def simulate_response(
        self,
        knowledge_components: List[str],
        difficulty: int,
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Simulates the learner's response correctness to an exercise.

        Parameters:
          knowledge_components: List of skill IDs required.
          difficulty: Question difficulty on 1-5 scale.

        Response model:
          1. Aggregated hidden mastery m = mean(m_k) across relevant KCs.
          2. Normalized item difficulty d in [0.1, 0.9]: d = difficulty / 5.5.
          3. Base probability p_base = sigma(k * (m - d) + noise).
          4. Adjusted for guess and slip:
             P(Correct) = Guess + (1 - Guess - Slip) * p_base
          5. Binary response sampled via RNG.

        Returns:
          (is_correct, p_correct, diagnostic_dict)
        """
        if not knowledge_components:
            # Fallback for unmapped items
            agg_m = self.archetype.initial_mastery_mean
        else:
            mastery_vals = [self.get_hidden_mastery(kc) for kc in knowledge_components]
            agg_m = sum(mastery_vals) / len(mastery_vals)

        # Normalize 1-5 difficulty to [0.18, 0.90]
        norm_d = max(0.1, min(1.0, float(difficulty) / 5.5))

        k = self.archetype.base_sensitivity
        noise = self.rng.gauss(0.0, self.archetype.noise_std)
        logit = k * (agg_m - norm_d) + noise

        # Sigmoid activation
        p_base = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, logit))))

        # Apply slip and guess bounds
        p_guess = self.archetype.guess_rate
        p_slip = self.archetype.slip_rate
        p_correct = p_guess + (1.0 - p_guess - p_slip) * p_base
        p_correct = max(0.01, min(0.99, p_correct))

        is_correct = self.rng.random() < p_correct

        diagnostics = {
            "aggregated_mastery": round(agg_m, 4),
            "normalized_difficulty": round(norm_d, 4),
            "p_correct": round(p_correct, 4),
            "p_base": round(p_base, 4),
            "archetype": self.archetype.name,
        }
        return is_correct, p_correct, diagnostics

    def apply_learning(
        self,
        knowledge_components: List[str],
        is_correct: bool,
    ) -> Dict[str, float]:
        """
        Updates ground-truth mastery after practice opportunity:
          m_{t+1} = m_t + alpha * (1 - m_t)

        If incorrect, learning still occurs via feedback/solution exposure, but at 50% rate.
        Returns:
          Dictionary of mastery improvements {kc_id: delta_m}.
        """
        deltas = {}
        effective_alpha = self.archetype.learning_rate if is_correct else (self.archetype.learning_rate * 0.5)

        for kc in knowledge_components:
            if kc in self._hidden_mastery:
                curr_m = self._hidden_mastery[kc]
                delta = effective_alpha * (1.0 - curr_m)
                new_m = max(self.mastery_floor, min(1.0, curr_m + delta))
                self._hidden_mastery[kc] = new_m
                deltas[kc] = delta
        return deltas

    def apply_forgetting(self, delta_time: float) -> Dict[str, float]:
        """
        Applies exponential forgetting decay over simulated elapsed time:
          m(t + dt) = m_min + (m(t) - m_min) * exp(-lambda * dt)

        Returns:
          Dictionary of decays {kc_id: decay_amount}.
        """
        if delta_time <= 0.0:
            return {kc: 0.0 for kc in self._hidden_mastery}

        decays = {}
        decay_factor = math.exp(-self.archetype.forgetting_rate * delta_time)
        floor = self.mastery_floor

        for kc, curr_m in self._hidden_mastery.items():
            new_m = floor + (curr_m - floor) * decay_factor
            new_m = max(floor, min(1.0, new_m))
            decay_amount = curr_m - new_m
            self._hidden_mastery[kc] = new_m
            decays[kc] = decay_amount

        self.simulated_time += delta_time
        return decays
