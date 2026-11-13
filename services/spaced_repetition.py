"""
Explicit Spaced Repetition Scheduling (SRS) Engine.
Part of KT-RL Phase 8: Advanced Policy Audit & RL Improvement Plan.

Implements:
1. Half-Life / Leitner Spaced Repetition System:
   - Tracks stability S and retrieval strength R(t) = 2^(-delta_t / S).
   - Stability expands exponentially with successful retrievals: S_{n+1} = S_n * 2.0.
   - Resets on lapse / incorrect response to S = 1.0.
   - Flags items as "due for review" when retrievability drops below retrieval threshold (R <= 0.85).
2. Fixed-Interval Revision Policy:
   - Rigidly reviews items at fixed step intervals (e.g., every 5 steps) regardless of mastery or retrievability.
3. Comparative Evaluation Harness:
   - Evaluates Spaced Repetition vs Fixed-Interval Revision vs No-Revision on long-horizon retention.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import TOPIC_CATALOG


@dataclass
class KCSpacingState:
    """Represents longitudinal memory stability and retrieval strength for a Knowledge Component."""
    kc_id: str
    repetition_count: int = 0
    stability: float = 1.0           # Half-life / interval in steps or time units
    last_reviewed_step: int = 0
    last_was_correct: bool = True
    total_reviews: int = 0

    def compute_retrievability(self, current_step: int) -> float:
        """Computes current recall probability R(t) = 2^(-delta_t / S)."""
        elapsed = max(0, current_step - self.last_reviewed_step)
        if self.stability <= 0.0:
            return 0.0
        return float(math.pow(2.0, -elapsed / self.stability))

    def update_after_review(self, current_step: int, is_correct: bool) -> None:
        """Updates memory stability based on retrieval outcome."""
        self.total_reviews += 1
        self.last_reviewed_step = current_step
        self.last_was_correct = is_correct

        if is_correct:
            self.repetition_count += 1
            # Stability expands: 1 -> 2 -> 4 -> 8 -> 16...
            self.stability = max(1.0, self.stability * 2.0)
        else:
            # Lapse resets stability to base interval
            self.repetition_count = 0
            self.stability = 1.0


class SpacedRepetitionScheduler:
    """
    Manages explicit spaced repetition schedules across all Knowledge Components.
    Interleaves urgent reviews with curriculum progression.
    """

    def __init__(
        self,
        retrieval_threshold: float = 0.85,
        topics: Optional[List[str]] = None,
    ):
        self.retrieval_threshold = retrieval_threshold
        if topics is None:
            topics = sorted(list(TOPIC_CATALOG.keys()))
        self.topics = topics
        self.kc_states: Dict[str, KCSpacingState] = {
            t: KCSpacingState(kc_id=t) for t in self.topics
        }

    def record_practice(self, kc_id: str, current_step: int, is_correct: bool) -> None:
        """Records a practice attempt and updates spacing schedule."""
        kc_clean = str(kc_id).strip().lower()
        if kc_clean not in self.kc_states:
            self.kc_states[kc_clean] = KCSpacingState(kc_id=kc_clean)
        self.kc_states[kc_clean].update_after_review(current_step, is_correct)

    def get_due_topics(self, current_step: int) -> List[Tuple[str, float]]:
        """
        Returns list of (topic, retrievability) for topics introduced and due for review
        (R(t) <= retrieval_threshold), sorted by lowest retrievability (highest urgency).
        """
        due = []
        for t, state in self.kc_states.items():
            if state.total_reviews > 0:  # Only review topics that have been previously practiced
                r = state.compute_retrievability(current_step)
                if r <= self.retrieval_threshold:
                    due.append((t, r))
        # Sort by lowest retrievability first
        due.sort(key=lambda x: x[1])
        return due

    def get_topic_retrievability(self, kc_id: str, current_step: int) -> float:
        """Returns current predicted recall probability for a topic."""
        kc_clean = str(kc_id).strip().lower()
        state = self.kc_states.get(kc_clean)
        if not state or state.total_reviews == 0:
            return 1.0  # Not yet practiced, no decay
        return state.compute_retrievability(current_step)


# ---------------------------------------------------------------------------
# Policy Implementations
# ---------------------------------------------------------------------------

def policy_explicit_spaced_repetition(
    env: Any,
    obs: np.ndarray,
    info: Dict[str, Any],
    scheduler: SpacedRepetitionScheduler,
) -> int:
    """
    Selects action using Explicit Spaced Repetition Scheduling:
    1. If any previously practiced eligible topic is due (R(t) <= 0.85), review it.
    2. Otherwise, progress curriculum to weakest prerequisite-ready unmastered topic.
    """
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # 1. Check for due reviews
    due_topics = scheduler.get_due_topics(current_step=env.current_step)
    for topic, retrievability in due_topics:
        # Find eligible items matching this due topic
        matching = [i for i in valid_indices if env.item_bank[i].get("topic") == topic]
        if matching:
            # Pick moderate difficulty exercise for review
            return min(matching, key=lambda i: abs(env.item_bank[i].get("difficulty", 2) - 2))

    # 2. If no review is due, choose weakest eligible topic (curriculum progression)
    def weakness_score(i: int) -> float:
        item = env.item_bank[i]
        top = item.get("topic", "")
        state = env.bkt_states.get(top)
        prob = state.mastery_probability if state else 0.20
        return (1.0 - prob)

    return max(valid_indices, key=weakness_score)


def policy_fixed_interval_revision(
    env: Any,
    obs: np.ndarray,
    info: Dict[str, Any],
    review_interval: int = 5,
    history_tracker: Optional[List[str]] = None,
) -> int:
    """
    Rigidly schedules revision every `review_interval` steps (e.g., every 5 steps)
    regardless of retrievability or student mastery.
    """
    mask = info.get("action_mask")
    if mask is None:
        mask = env.get_action_mask()
    valid_indices = [i for i in range(env.num_actions) if mask[i]]
    if not valid_indices:
        return 0

    # Every N steps, perform a revision review of an earlier practiced topic
    is_revision_step = (env.current_step > 0 and env.current_step % review_interval == 0)

    if is_revision_step and history_tracker:
        # Pick the oldest practiced topic in history
        for old_topic in history_tracker:
            matching = [i for i in valid_indices if env.item_bank[i].get("topic") == old_topic]
            if matching:
                return matching[0]

    # Standard progression
    def score_progression(i: int) -> float:
        top = env.item_bank[i].get("topic", "")
        s = env.bkt_states.get(top)
        return 1.0 - (s.mastery_probability if s else 0.20)

    return max(valid_indices, key=score_progression)


def run_spaced_vs_fixed_interval_benchmark(
    seeds: Optional[List[int]] = None,
    archetypes: Optional[List[str]] = None,
    active_steps: int = 25,
    delay_days: float = 7.0,
) -> Dict[str, Any]:
    """
    Simulates and compares:
    1. Explicit Spaced Repetition (SRS)
    2. Fixed-Interval Revision (Every 5 steps)
    3. Greedy Progression (No revision)
    Under identical seeds and archetypes over a 7-day delayed retention interval.
    """
    from services.rl_env import ExerciseSelectionEnv
    from services.learner_simulator import ARCHETYPES

    if seeds is None:
        seeds = [101, 202, 303, 404, 505]
    if archetypes is None:
        archetypes = list(ARCHETYPES.keys())

    comparisons = {
        "explicit_spaced_repetition": {"immediate_gain": [], "delayed_gain": [], "retention_rate": [], "forgetting_loss": []},
        "fixed_interval_revision": {"immediate_gain": [], "delayed_gain": [], "retention_rate": [], "forgetting_loss": []},
        "greedy_no_revision": {"immediate_gain": [], "delayed_gain": [], "retention_rate": [], "forgetting_loss": []},
    }

    for arch in archetypes:
        for seed in seeds:
            # 1. Explicit Spaced Repetition Run
            env_srs = ExerciseSelectionEnv(max_steps=active_steps, step_time_delta=0.05)
            obs, info = env_srs.reset(seed=seed, options={"archetype": arch})
            scheduler = SpacedRepetitionScheduler()
            init_m = float(np.mean(list(env_srs.learner.get_all_hidden_mastery().values())))

            for _ in range(active_steps):
                act = policy_explicit_spaced_repetition(env_srs, obs, info, scheduler)
                obs, r, term, trunc, step_info = env_srs.step(act)
                scheduler.record_practice(
                    kc_id=step_info.get("topic", "python"),
                    current_step=env_srs.current_step,
                    is_correct=step_info.get("is_correct", False),
                )
                if term or trunc:
                    break

            post_m = float(np.mean(list(env_srs.learner.get_all_hidden_mastery().values())))
            # 7-day retention delay
            env_srs.learner.apply_forgetting(delta_time=delay_days)
            del_m = float(np.mean(list(env_srs.learner.get_all_hidden_mastery().values())))

            imm_g = post_m - init_m
            del_g = del_m - init_m
            ret_rate = (del_m / post_m) if post_m > 1e-4 else 0.0
            loss = post_m - del_m

            comparisons["explicit_spaced_repetition"]["immediate_gain"].append(imm_g)
            comparisons["explicit_spaced_repetition"]["delayed_gain"].append(del_g)
            comparisons["explicit_spaced_repetition"]["retention_rate"].append(ret_rate)
            comparisons["explicit_spaced_repetition"]["forgetting_loss"].append(loss)

            # 2. Fixed-Interval Revision Run
            env_fix = ExerciseSelectionEnv(max_steps=active_steps, step_time_delta=0.05)
            obs, info = env_fix.reset(seed=seed, options={"archetype": arch})
            history_tracker: List[str] = []
            init_m_fix = float(np.mean(list(env_fix.learner.get_all_hidden_mastery().values())))

            for _ in range(active_steps):
                act = policy_fixed_interval_revision(env_fix, obs, info, review_interval=5, history_tracker=history_tracker)
                obs, r, term, trunc, step_info = env_fix.step(act)
                t = step_info.get("topic")
                if t and t not in history_tracker:
                    history_tracker.append(t)
                if term or trunc:
                    break

            post_m_fix = float(np.mean(list(env_fix.learner.get_all_hidden_mastery().values())))
            env_fix.learner.apply_forgetting(delta_time=delay_days)
            del_m_fix = float(np.mean(list(env_fix.learner.get_all_hidden_mastery().values())))

            comparisons["fixed_interval_revision"]["immediate_gain"].append(post_m_fix - init_m_fix)
            comparisons["fixed_interval_revision"]["delayed_gain"].append(del_m_fix - init_m_fix)
            comparisons["fixed_interval_revision"]["retention_rate"].append((del_m_fix / post_m_fix) if post_m_fix > 1e-4 else 0.0)
            comparisons["fixed_interval_revision"]["forgetting_loss"].append(post_m_fix - del_m_fix)

            # 3. Greedy No-Revision Run
            env_grd = ExerciseSelectionEnv(max_steps=active_steps, step_time_delta=0.05)
            obs, info = env_grd.reset(seed=seed, options={"archetype": arch})
            init_m_grd = float(np.mean(list(env_grd.learner.get_all_hidden_mastery().values())))

            for _ in range(active_steps):
                mask = info.get("action_mask")
                if mask is None:
                    mask = env_grd.get_action_mask()
                valids = [i for i in range(env_grd.num_actions) if mask[i]]
                act = max(valids, key=lambda i: 1.0 - env_grd.bkt_states.get(env_grd.item_bank[i]["topic"]).mastery_probability)
                obs, r, term, trunc, step_info = env_grd.step(act)
                if term or trunc:
                    break

            post_m_grd = float(np.mean(list(env_grd.learner.get_all_hidden_mastery().values())))
            env_grd.learner.apply_forgetting(delta_time=delay_days)
            del_m_grd = float(np.mean(list(env_grd.learner.get_all_hidden_mastery().values())))

            comparisons["greedy_no_revision"]["immediate_gain"].append(post_m_grd - init_m_grd)
            comparisons["greedy_no_revision"]["delayed_gain"].append(del_m_grd - init_m_grd)
            comparisons["greedy_no_revision"]["retention_rate"].append((del_m_grd / post_m_grd) if post_m_grd > 1e-4 else 0.0)
            comparisons["greedy_no_revision"]["forgetting_loss"].append(post_m_grd - del_m_grd)

    summary = {}
    for pol, data in comparisons.items():
        summary[pol] = {
            "mean_immediate_gain": round(float(np.mean(data["immediate_gain"])), 4),
            "std_immediate_gain": round(float(np.std(data["immediate_gain"])), 4),
            "mean_delayed_gain": round(float(np.mean(data["delayed_gain"])), 4),
            "std_delayed_gain": round(float(np.std(data["delayed_gain"])), 4),
            "mean_retention_rate": round(float(np.mean(data["retention_rate"])), 4),
            "mean_forgetting_loss": round(float(np.mean(data["forgetting_loss"])), 4),
        }

    return {
        "title": "Spaced Repetition vs Fixed-Interval Revision Benchmark",
        "delay_days": delay_days,
        "active_steps": active_steps,
        "n_episodes": len(seeds) * len(archetypes),
        "results": summary,
    }
