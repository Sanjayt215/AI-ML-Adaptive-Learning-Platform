"""
Curriculum-Level Planning Service.
Part of KT-RL Phase 8: Advanced Policy Audit & RL Improvement Plan.

Implements:
1. Prerequisite DAG Topological Sort & Dependency Depth Analysis across the 30 canonical topics.
2. Active Learning Frontier Identification (Ready, In-Progress, Mastered, Locked).
3. Goal-Oriented Trajectory Planning (e.g., 'machine learning', 'deep learning', 'full curriculum').
4. Milestone Stage Decomposition with exercise item sequencing.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure path resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from resources import TOPIC_CATALOG, get_all_questions
from services.bkt_service import get_mastery_by_learner

logger = logging.getLogger(__name__)

DEFAULT_MASTERY_TARGET = 0.80
DEFAULT_PREREQ_READINESS_THRESHOLD = 0.60


class CurriculumPlanner:
    """
    Computes pedagogical curriculum plans using the prerequisite DAG
    and current Bayesian Knowledge Tracing mastery estimates.
    """

    def __init__(
        self,
        target_mastery: float = DEFAULT_MASTERY_TARGET,
        prereq_threshold: float = DEFAULT_PREREQ_READINESS_THRESHOLD,
    ):
        self.target_mastery = target_mastery
        self.prereq_threshold = prereq_threshold
        self.catalog = dict(TOPIC_CATALOG)
        self.all_questions = get_all_questions()

        # Precompute DAG structures
        self.adjacency, self.reverse_adjacency = self._build_graphs()
        self.depth_map = self._compute_depth_map()
        self.topological_order = self._compute_topological_order()

    def _build_graphs(self) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """Builds forward (prereq -> descendant) and reverse (child -> prereqs) adjacency lists."""
        forward: Dict[str, List[str]] = {t: [] for t in self.catalog}
        reverse: Dict[str, List[str]] = {t: [] for t in self.catalog}

        for topic, meta in self.catalog.items():
            prereqs = meta.get("prerequisites", [])
            for p in prereqs:
                p_clean = str(p).strip().lower()
                if p_clean in forward:
                    forward[p_clean].append(topic)
                reverse.setdefault(topic, []).append(p_clean)

        return forward, reverse

    def _compute_depth_map(self) -> Dict[str, int]:
        """Calculates prerequisite depth for each topic (Layer 0 = foundational, Layer 1 = intermediate, etc.)."""
        depths: Dict[str, int] = {}

        def get_depth(node: str, visited: Set[str]) -> int:
            if node in depths:
                return depths[node]
            if node in visited:
                return 0  # Cycle safeguard
            visited.add(node)
            prereqs = self.reverse_adjacency.get(node, [])
            if not prereqs:
                depths[node] = 0
            else:
                depths[node] = 1 + max(get_depth(p, visited) for p in prereqs if p in self.catalog)
            return depths[node]

        for t in self.catalog:
            get_depth(t, set())
        return depths

    def _compute_topological_order(self) -> List[str]:
        """Computes deterministic topological ordering of topics according to prerequisite DAG."""
        in_degree = {t: len(self.reverse_adjacency.get(t, [])) for t in self.catalog}
        queue = sorted([t for t, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for child in sorted(self.adjacency.get(node, [])):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
                    queue.sort()

        # Append any unvisited nodes if disconnected
        for t in sorted(self.catalog.keys()):
            if t not in order:
                order.append(t)
        return order

    def analyze_learner_frontier(
        self,
        bkt_mastery_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Classifies all 30 curriculum topics into:
        - Mastered: P(K) >= target_mastery
        - In-Progress: prereq met and 0.20 <= P(K) < target_mastery
        - Ready Frontier: all prerequisites satisfied, ready to begin
        - Locked: blocked by one or more unmastered prerequisites
        """
        mastered = []
        in_progress = []
        ready_frontier = []
        locked = []

        for topic in self.topological_order:
            m_state = bkt_mastery_map.get(topic, {})
            p_val = m_state.get("mastery_probability", 0.20) if isinstance(m_state, dict) else (
                getattr(m_state, "mastery_probability", 0.20)
            )

            prereqs = self.reverse_adjacency.get(topic, [])
            prereqs_met = True
            missing_prereqs = []

            for p in prereqs:
                p_state = bkt_mastery_map.get(p, {})
                p_prob = p_state.get("mastery_probability", 0.20) if isinstance(p_state, dict) else (
                    getattr(p_state, "mastery_probability", 0.20)
                )
                if p_prob < self.prereq_threshold:
                    prereqs_met = False
                    missing_prereqs.append({"topic": p, "current_mastery": round(p_prob, 3)})

            if p_val >= self.target_mastery:
                mastered.append({
                    "topic": topic,
                    "mastery": round(p_val, 3),
                    "depth": self.depth_map.get(topic, 0),
                })
            elif not prereqs_met:
                locked.append({
                    "topic": topic,
                    "current_mastery": round(p_val, 3),
                    "missing_prerequisites": missing_prereqs,
                    "depth": self.depth_map.get(topic, 0),
                })
            else:
                item_info = {
                    "topic": topic,
                    "current_mastery": round(p_val, 3),
                    "depth": self.depth_map.get(topic, 0),
                    "recommended_next_step": "practice" if p_val >= 0.40 else "foundational_exercises",
                }
                if p_val >= 0.40:
                    in_progress.append(item_info)
                else:
                    ready_frontier.append(item_info)

        return {
            "mastered_count": len(mastered),
            "in_progress_count": len(in_progress),
            "ready_count": len(ready_frontier),
            "locked_count": len(locked),
            "mastered": mastered,
            "in_progress": in_progress,
            "ready_frontier": ready_frontier,
            "locked": locked,
        }

    def generate_curriculum_plan(
        self,
        learner_id: str,
        target_goal: str = "full_curriculum",
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates an end-to-step curriculum plan tailored to the learner's current mastery:
        1. Identifies frontier opportunities.
        2. Organizes topics into pedagogical milestones (Stages 1 through 4).
        3. Sequences concrete exercise item IDs from the canonical question bank.
        """
        # Fetch current BKT mastery
        try:
            bkt_data = get_mastery_by_learner(learner_id, db_path=db_path)
            raw_topics = bkt_data.get("topics", {})
            if isinstance(raw_topics, list):
                bkt_map = {t.get("kc_id", t.get("topic")): t for t in raw_topics}
            elif isinstance(raw_topics, dict):
                bkt_map = raw_topics
            else:
                bkt_map = {}
        except Exception:
            bkt_map = {}

        frontier = self.analyze_learner_frontier(bkt_map)

        # Stage decomposition by DAG depth
        stages = {
            1: {"title": "Stage 1: Core Foundations", "topics": []},
            2: {"title": "Stage 2: Intermediate Data & Algorithms", "topics": []},
            3: {"title": "Stage 3: Applied Machine Learning", "topics": []},
            4: {"title": "Stage 4: Advanced Specializations", "topics": []},
        }

        for topic in self.topological_order:
            d = self.depth_map.get(topic, 0)
            stage_num = 1 if d == 0 else 2 if d == 1 else 3 if d == 2 else 4
            
            m_state = bkt_map.get(topic, {})
            p_val = m_state.get("mastery_probability", 0.20) if isinstance(m_state, dict) else (
                getattr(m_state, "mastery_probability", 0.20)
            )

            # Find matching items in question bank
            topic_items = [
                q["item_id"] for q in self.all_questions
                if q.get("topic") == topic or topic in q.get("knowledge_components", [])
            ]

            status = "mastered" if p_val >= self.target_mastery else (
                "in_progress" if any(t["topic"] == topic for t in frontier["in_progress"]) else (
                    "ready" if any(t["topic"] == topic for t in frontier["ready_frontier"]) else "locked"
                )
            )

            stages[stage_num]["topics"].append({
                "topic": topic,
                "depth": d,
                "status": status,
                "current_mastery": round(p_val, 3),
                "available_items_count": len(topic_items),
                "sample_items": topic_items[:3],
            })

        # Planned next 5 exercise sequence from ready / in-progress frontier
        planned_trajectory = []
        prioritized_topics = [t["topic"] for t in frontier["in_progress"]] + [t["topic"] for t in frontier["ready_frontier"]]

        for t in prioritized_topics:
            matching_qs = [
                q for q in self.all_questions
                if q.get("topic") == t or t in q.get("knowledge_components", [])
            ]
            matching_qs.sort(key=lambda q: q.get("difficulty", 2))
            for q in matching_qs:
                if q["item_id"] not in [p["item_id"] for p in planned_trajectory]:
                    planned_trajectory.append({
                        "item_id": q["item_id"],
                        "topic": t,
                        "difficulty": q.get("difficulty", 2),
                        "question": q.get("question") or q.get("q"),
                    })
                if len(planned_trajectory) >= 5:
                    break
            if len(planned_trajectory) >= 5:
                break

        return {
            "ok": True,
            "learner_id": learner_id,
            "target_goal": target_goal,
            "mastery_target_threshold": self.target_mastery,
            "prerequisite_readiness_threshold": self.prereq_threshold,
            "curriculum_summary": {
                "total_topics": len(self.catalog),
                "mastered": frontier["mastered_count"],
                "in_progress": frontier["in_progress_count"],
                "ready_frontier": frontier["ready_count"],
                "locked": frontier["locked_count"],
            },
            "active_frontier": frontier["ready_frontier"],
            "stages": [
                {"stage_number": k, "stage_title": v["title"], "topics": v["topics"]}
                for k, v in stages.items()
            ],
            "planned_trajectory": planned_trajectory,
        }
