"""
Personalized Difficulty & Hysteresis Recovery Controller.
Part of KT-RL Phase 7: Advanced RL Improvements & Verified Integration.

Controls pedagogical challenge dynamically with hysteresis safeguards:
1. Anti-Oscillation Hysteresis:
   - Stepping UP difficulty requires 2 consecutive correct answers at the current level.
   - Stepping DOWN difficulty requires 2 consecutive incorrect answers.
   - Single isolated errors do NOT cause aggressive difficulty drops.
2. Finite State Machine:
   - CALIBRATION: Initial diagnostic phase (steps 1-3).
   - OPTIMAL_CHALLENGE: Main Zone of Proximal Development progression.
   - RECOVERY_SCAFFOLDING: Remedial difficulty step-down on repeated failure.
   - PREREQUISITE_REPAIR: Review foundational prerequisite KCs when blocked.
3. Prerequisite Invariant: Never overrides prerequisite eligibility masks.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class ControllerState(str, Enum):
    CALIBRATION = "CALIBRATION"
    OPTIMAL_CHALLENGE = "OPTIMAL_CHALLENGE"
    RECOVERY_SCAFFOLDING = "RECOVERY_SCAFFOLDING"
    PREREQUISITE_REPAIR = "PREREQUISITE_REPAIR"


class DifficultyRecoveryController:
    """Personalized difficulty and recovery manager with state machine and hysteresis."""

    def __init__(
        self,
        base_difficulty: int = 2,
        min_difficulty: int = 1,
        max_difficulty: int = 5,
        step_up_streak: int = 2,
        step_down_streak: int = 2,
    ):
        self.current_difficulty = base_difficulty
        self.min_difficulty = min_difficulty
        self.max_difficulty = max_difficulty
        self.step_up_streak = step_up_streak
        self.step_down_streak = step_down_streak

        self.state = ControllerState.CALIBRATION
        self.consecutive_correct: int = 0
        self.consecutive_incorrect: int = 0
        self.total_steps: int = 0

    def record_response(self, is_correct: bool) -> None:
        """Updates internal streaks and transitions controller state with hysteresis."""
        self.total_steps += 1

        if is_correct:
            self.consecutive_correct += 1
            self.consecutive_incorrect = 0
            # Hysteresis Step Up
            if self.consecutive_correct >= self.step_up_streak:
                if self.current_difficulty < self.max_difficulty:
                    self.current_difficulty += 1
                self.consecutive_correct = 0
                self.state = ControllerState.OPTIMAL_CHALLENGE
        else:
            self.consecutive_incorrect += 1
            self.consecutive_correct = 0
            # Hysteresis Step Down
            if self.consecutive_incorrect >= self.step_down_streak:
                if self.current_difficulty > self.min_difficulty:
                    self.current_difficulty -= 1
                self.consecutive_incorrect = 0
                self.state = ControllerState.RECOVERY_SCAFFOLDING

        # Calibration transition
        if self.total_steps > 3 and self.state == ControllerState.CALIBRATION:
            self.state = ControllerState.OPTIMAL_CHALLENGE

    def filter_candidates(
        self,
        action_mask: np.ndarray,
        item_bank: List[Dict[str, Any]],
    ) -> List[int]:
        """Filters eligible actions to items matching current target difficulty if available."""
        valid_indices = [i for i in range(len(item_bank)) if action_mask[i]]
        if not valid_indices:
            return []

        # Find items matching current difficulty level
        matching = [i for i in valid_indices if item_bank[i].get("difficulty") == self.current_difficulty]
        if matching:
            return matching

        # If exact match not available, find closest available difficulty
        closest = min(valid_indices, key=lambda i: abs(item_bank[i].get("difficulty", 2) - self.current_difficulty))
        target_diff = item_bank[closest].get("difficulty", 2)
        return [i for i in valid_indices if item_bank[i].get("difficulty") == target_diff]
