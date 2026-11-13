
from __future__ import annotations

import sys
from pathlib import Path
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from collections import deque
import json
import os
import random
import re
import time
from pathlib import Path

import uuid
from flask import Flask, jsonify, request, session, send_from_directory
from flask.sessions import SessionInterface, SessionMixin
import os
from werkzeug.exceptions import HTTPException

from resources import QUIZ_QUESTIONS, TOPIC_CATALOG, match_topics_from_text, normalize_topic, get_all_questions, get_question_by_id, validate_item_bank
from services.automl_service import build_learning_models, predict_level_with_models, predict_score_with_models
from services.catalog_service import (
    filter_options,
    project_for_topic,
    rank_courses,
    rank_kaggle_datasets,
    rank_live_and_dataset_videos,
    rank_catalog_videos,
)
from services.real_data_service import load_learning_dataset, load_optional_heart_dataset
from services.youtube_service import search_youtube_videos, youtube_api_available
from services.llm_tutor_service import generate_tutor_reply, load_dataset_registry
from services.learning_store import (
    init_db as init_learning_db,
    create_session as create_learning_session,
    get_session as get_learning_session,
    complete_session as complete_learning_session,
    log_event as log_learning_event,
    get_learner_events,
    get_learner_state,
)
from services.bkt_service import (
    get_mastery_by_learner,
    replay_learner_history,
    get_kc_mastery,
    BKTParameters,
    DEFAULT_PARAMS as BKT_DEFAULT_PARAMS,
)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "autolearn-fullstack-secret")

class ServerSideSession(dict, SessionMixin):
    def __init__(self, initial=None, sid=None):
        super().__init__(initial or {})
        self.sid = sid
        self.modified = False

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.modified = True

    def pop(self, key, default=None):
        self.modified = True
        return super().pop(key, default)

    def setdefault(self, key, default=None):
        self.modified = True
        return super().setdefault(key, default)


class ServerSideSessionInterface(SessionInterface):
    _sessions: dict[str, dict] = {}

    def open_session(self, app, request):
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        sid = request.cookies.get(cookie_name)
        if not sid or sid not in self._sessions:
            sid = uuid.uuid4().hex
            self._sessions[sid] = {}
        return ServerSideSession(self._sessions[sid], sid=sid)

    def save_session(self, app, session, response):
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if not session:
            if session.modified:
                self._sessions.pop(session.sid, None)
                response.delete_cookie(cookie_name, domain=domain, path=path)
            return

        self._sessions[session.sid] = dict(session)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        response.set_cookie(
            cookie_name,
            session.sid,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            samesite=samesite,
        )

app.session_interface = ServerSideSessionInterface()

# Serve favicon.ico to prevent 404/500 errors
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

LEARNING_DF, DATA_INFO = load_learning_dataset()
HEART_DF = load_optional_heart_dataset()
MODEL_BUNDLE = build_learning_models(LEARNING_DF)
DATASET_REGISTRY_DF = load_dataset_registry()
init_learning_db()

AI_FEATURES = [
    'LLM-ready tutor with doubt solving and local RAG fallback',
    'Embeddings-style retrieval over topic notes, datasets, and prerequisites',
    'Topic-aware adaptive quiz generation',
    'Weak-topic detection and learning score tracking',
    'Personalized path tracking with unlock logic',
    'Course, video, dataset, and mini-project recommendations',
    'AI/ML topic graph with prerequisite ordering',
]
ML_FEATURES = [
    'Performance prediction with classification and regression models',
    'Real-dataset ingestion for OULAD, UCI, and optional Kaggle score datasets',
    'Recommendation ranking for courses and videos',
    'Difficulty-aware quiz sequencing',
    'Path-based mastery scoring',
]


def level_from_score(score_pct: float) -> str:
    if score_pct < 45:
        return "beginner"
    if score_pct < 75:
        return "intermediate"
    return "advanced"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def parse_topics(syllabus_text: str, target_goal: str = "") -> list[str]:
    raw_tokens = []
    for token in re.split(r"[,\n;/|]+", f"{syllabus_text},{target_goal}"):
        token = token.strip()
        if token:
            raw_tokens.append(token)
    normalized = [normalize_topic(t) for t in raw_tokens]
    matched = match_topics_from_text(f"{syllabus_text}, {target_goal}")
    combined = []
    for topic in normalized + matched:
        if topic in TOPIC_CATALOG:
            combined.append(topic)
    return _dedupe(combined) or ["python"]


def find_learning_order(topics: list[str]) -> list[str]:
    known = [t for t in topics if t in TOPIC_CATALOG]
    unknown = [t for t in topics if t not in TOPIC_CATALOG]
    graph = {k: v.get("prerequisites", []) for k, v in TOPIC_CATALOG.items()}
    indegree = {t: 0 for t in known}
    dependents = {t: [] for t in known}
    for t in known:
        for pre in graph.get(t, []):
            if pre in indegree:
                indegree[t] += 1
                dependents[pre].append(t)
    queue = deque(sorted([t for t, d in indegree.items() if d == 0]))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in dependents.get(node, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return _dedupe(order + known + unknown)


def recommend_recent_algorithms(avg_score: float) -> list[dict]:
    items = [
        {"name": "Gradient Boosting", "why": "Strong on structured student data and excellent for ranking learning readiness."},
        {"name": "Extra Trees", "why": "Fast ensemble baseline that handles mixed numeric and categorical learning signals well."},
        {"name": "AutoML", "why": "Tries multiple models and selects the best one automatically for your dataset."},
        {"name": "Hybrid Recommendation", "why": "Combines live YouTube API results with curated video and course datasets."},
        {"name": "Adaptive Quiz Engine", "why": "Generates topic-aware question variants from syllabus keywords, prerequisites, and project goals."},
        {"name": "Learning Path Tracker", "why": "Detects started, in-progress, and completed topics and updates progress in real time."},
        {"name": "Topic-Aware Tutor", "why": "Answers doubts using the selected syllabus topic, its prerequisites, resources, and the learner profile."},
    ]
    if avg_score >= 70:
        items.extend([
            {"name": "XGBoost / LightGBM", "why": "Common industry boosters for tabular prediction and ranking tasks."},
            {"name": "Semantic Resource Matching", "why": "Improves topic-to-resource matching beyond plain keyword search."},
            {"name": "Transformer and LLM Paths", "why": "Adds advanced AI learning tracks after fundamentals are strong."},
        ])
    else:
        items.append({"name": "Rule Engine + Prerequisite Graph", "why": "Stops learners from skipping fundamentals and preserves the right order."})
    return items


def _default_path_progress(topics: list[str]) -> dict[str, str]:
    progress = {}
    for i, topic in enumerate(topics):
        progress[topic] = "recommended" if i == 0 else "locked"
    return progress


def _coerce_path_progress(topics: list[str], stored: dict | None) -> dict[str, str]:
    progress = _default_path_progress(topics)
    if isinstance(stored, dict):
        for topic, status in stored.items():
            if topic in progress and status in {"completed", "in-progress", "recommended", "locked"}:
                progress[topic] = status
    unlocked_seen = False
    for topic in topics:
        if progress[topic] == "completed":
            unlocked_seen = True
            continue
        if not unlocked_seen and progress[topic] == "locked":
            progress[topic] = "recommended"
            unlocked_seen = True
        elif unlocked_seen and progress[topic] == "locked":
            break
    completed_count = sum(1 for s in progress.values() if s == "completed")
    if completed_count < len(topics):
        next_idx = min(completed_count, len(topics) - 1)
        next_topic = topics[next_idx]
        if progress[next_topic] == "locked":
            progress[next_topic] = "recommended"
    return progress


def _compute_learning_score(assessment: list[dict], progress: dict[str, str], activity: dict | None = None) -> float:
    if not assessment and not progress:
        return 0.0
    activity = activity or {}
    quiz_component = sum(item.get("score_pct", 0) for item in assessment) / max(len(assessment), 1) if assessment else 0.0
    weights = {"locked": 0.0, "recommended": 0.45, "in-progress": 0.7, "completed": 1.0}
    path_component = (sum(weights.get(status, 0.0) for status in progress.values()) / max(len(progress), 1)) * 100 if progress else 0.0
    streak = min(int(activity.get("completed_actions", 0)) * 6, 18)
    recency = min(int(activity.get("quiz_attempts", 0)) * 4, 12)
    score = (quiz_component * 0.6) + (path_component * 0.3) + streak + recency
    return round(min(score, 100.0), 1)


def _normalize_step_status(status: str) -> str:
    normalized = (status or '').strip().lower()
    if normalized in {'not started', 'not_started', 'start', 'recommended'}:
        return 'recommended'
    if normalized in {'in progress', 'in-progress', 'progress'}:
        return 'in-progress'
    if normalized in {'completed', 'done'}:
        return 'completed'
    return 'locked'


def _status_label(status: str) -> str:
    return {
        'completed': 'Completed',
        'in-progress': 'In Progress',
        'recommended': 'Not Started',
        'locked': 'Locked',
    }.get(status, str(status).title())


def _topic_resource_payload(topic: str, level: str) -> dict:
    topic = normalize_topic(topic)
    if topic not in TOPIC_CATALOG:
        topic = next((t for t in TOPIC_CATALOG if topic in TOPIC_CATALOG[t].get('aliases', [])), topic)
    rec = get_recommendations(topic, level, provider='all', video_mode='hybrid')
    
    # Normalize project: extract string from dict if needed
    project_str = rec['project']
    if isinstance(project_str, dict):
        project_str = project_str.get('project', 'Practice a small project on this topic.')
    
    return {
        'topic': topic,
        'level': level,
        'videos': rec['videos'][:4],
        'courses': rec['courses'][:4],
        'datasets': rec['datasets'][:3],
        'project': project_str,
    }


def _resolve_topic_for_resources(requested_topic: str, profile: dict | None = None) -> str:
    requested = normalize_topic(requested_topic or '')
    if requested in TOPIC_CATALOG:
        return requested
    for topic, meta in TOPIC_CATALOG.items():
        if requested in meta.get('aliases', []):
            return topic
        if requested in meta.get('prerequisites', []):
            return topic
    if profile and profile.get('topics'):
        if requested in profile['topics']:
            return requested
        for topic in profile['topics']:
            if requested in TOPIC_CATALOG.get(topic, {}).get('aliases', []):
                return topic
            if requested in TOPIC_CATALOG.get(topic, {}).get('prerequisites', []):
                return topic
        return profile['topics'][0]
    return 'python'


def _activity_metrics(profile: dict, assessment: list[dict]) -> dict:
    topics = profile.get('topics', [])
    completed_topics = sum(1 for status in profile.get('path_progress', {}).values() if status == 'completed')
    topic_completion_pct = round((completed_topics / max(len(topics), 1)) * 100, 1) if topics else 0.0

    quiz_pct = round(sum(r['score_pct'] for r in assessment) / max(len(assessment), 1), 1) if assessment else 0.0

    video_values = []
    for topic, topic_data in profile.get('video_activity', {}).items():
        for rec in topic_data.values():
            if rec.get('watched_pct') is not None:
                video_values.append(rec['watched_pct'])
    video_pct = round(sum(video_values) / max(len(video_values), 1), 1) if video_values else 0.0

    course_clicks = 0
    course_completions = 0
    for topic_data in profile.get('course_activity', {}).values():
        for rec in topic_data.values():
            course_clicks += int(rec.get('clicks', 0))
            if rec.get('completed'):
                course_completions += 1
    course_pct = min(100.0, course_clicks * 10 + course_completions * 25)

    tutor_pct = min(100.0, int(profile.get('activity', {}).get('tutor_questions', 0)) * 25)

    learning_score = round(
        quiz_pct * 0.25 + topic_completion_pct * 0.4 + video_pct * 0.2 + course_pct * 0.1 + tutor_pct * 0.05,
        1,
    )
    return {
        'topic_completion_pct': topic_completion_pct,
        'quiz_pct': quiz_pct,
        'video_pct': video_pct,
        'course_pct': course_pct,
        'tutor_pct': tutor_pct,
        'learning_score': min(100.0, learning_score),
    }


def _shuffle_options(question: dict, rng: random.Random) -> dict:
    options = list(question.get("options", []))
    rng.shuffle(options)
    result = dict(question)
    result["options"] = options
    return result


def _question_variants(topic: str, idx: int, question: dict, rng: random.Random) -> list[dict]:
    stems = [
        question.get("question") or question["q"],
        f"Topic check — {question.get('question') or question['q']}",
        f"Choose the best answer for {topic.title()}: {question.get('question') or question['q']}",
        f"Quick revision: {question.get('question') or question['q']}",
        f"Selected syllabus topic: {topic.title()}. {question.get('question') or question['q']}",
    ]
    variants = []
    base_item_id = question.get("item_id") or f"q_{re.sub(r'[^a-z0-9]', '_', topic.lower())}_{idx:02d}"
    kcs = question.get("knowledge_components") or [topic]
    prereqs = question.get("prerequisite_components") or TOPIC_CATALOG.get(topic, {}).get("prerequisites", [])
    diff = question.get("difficulty") or (2 if idx == 0 else 3)

    for n, stem in enumerate(stems):
        item = _shuffle_options(question, rng)
        item.update({
            "topic": topic,
            "base_index": idx,
            "index": f"{idx}_{n}_{rng.randint(1000,9999)}",
            "q": stem,
            "question": stem,
            "item_id": f"{base_item_id}_v{n}" if n > 0 else base_item_id,
            "canonical_item_id": base_item_id,
            "knowledge_components": kcs,
            "prerequisite_components": prereqs,
            "difficulty": diff,
            "correct_answer": question.get("correct_answer") or question.get("answer"),
        })
        variants.append(item)
    return variants


def _sample_distractors(topic: str, answer: str, rng: random.Random, pool: list[str], max_count: int = 3) -> list[str]:
    candidates = [p for p in pool if p and p != answer]
    rng.shuffle(candidates)
    return candidates[:max_count]


try:
    from supplemental_questions import get_supplemental_questions
except ImportError:
    from autolearn_fullstack.supplemental_questions import get_supplemental_questions


def _generated_questions_for_topic(topic: str, rng: random.Random) -> list[dict]:
    clean_topic = normalize_topic(topic)
    supp = get_supplemental_questions(clean_topic)
    res = []
    for item in supp:
        copied = dict(item)
        copied["options"] = list(item.get("options", []))
        rng.shuffle(copied["options"])
        res.append(copied)
    return res


def get_topic_quiz(topics: list[str], quiz_seed: int | None = None, excluded_ids: list[str] | set[str] | None = None) -> list[dict]:
    seed = quiz_seed if quiz_seed is not None else time.time_ns()
    rng = random.Random(seed)
    selected_topics = _dedupe([normalize_topic(t) for t in topics if normalize_topic(t) in QUIZ_QUESTIONS or normalize_topic(t) in TOPIC_CATALOG])
    if not selected_topics:
        selected_topics = ["python"]

    excluded_canonical = set(excluded_ids or [])
    quiz = []
    topic_count = min(max(len(selected_topics), 1), 6)
    per_topic = 3 if topic_count <= 4 else 2
    global_seen_canonical = set(excluded_canonical)

    for topic in selected_topics[:topic_count]:
        bank = list(QUIZ_QUESTIONS.get(topic, [])) + _generated_questions_for_topic(topic, rng)
        # Partition bank into fresh vs previously seen
        fresh_bank = [q for q in bank if (q.get("canonical_item_id") or q.get("item_id")) not in global_seen_canonical]
        if not fresh_bank:
            # If all items were seen, allow controlled revision across the bank
            fresh_bank = bank

        rng.shuffle(fresh_bank)
        picked_topic = []
        for idx, q in enumerate(fresh_bank):
            cid = q.get("canonical_item_id") or q.get("item_id") or f"{topic}_{idx}"
            if cid in global_seen_canonical and len(global_seen_canonical) < len(bank):
                continue
            variants = _question_variants(topic, idx, q, rng)
            chosen_var = rng.choice(variants) if variants else q
            chosen_var["canonical_item_id"] = cid
            picked_topic.append(chosen_var)
            global_seen_canonical.add(cid)
            if len(picked_topic) >= min(per_topic, len(bank)):
                break
        quiz.extend(picked_topic)

    rng.shuffle(quiz)
    return quiz[: min(12, len(quiz))]


def build_topic_results(chosen_topics: list[str], answers: dict, quiz_items: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for item in quiz_items:
        grouped.setdefault(normalize_topic(item["topic"]), []).append(item)

    results = []
    scored_topics = [t for t in chosen_topics if normalize_topic(t) in grouped]
    for topic in _dedupe(scored_topics):
        t = normalize_topic(topic)
        items = grouped.get(t, [])
        if not items:
            continue
        correct = 0
        for q in items:
            key = f"{q['topic']}_{q['index']}"
            if answers.get(key) == q["answer"]:
                correct += 1
        score_pct = round((correct / max(len(items), 1)) * 100, 1)
        predicted_level = predict_level_with_models(MODEL_BUNDLE, t, score_pct)
        predicted_exam_score = predict_score_with_models(MODEL_BUNDLE, t, score_pct)
        results.append({
            "topic": t,
            "score_pct": score_pct,
            "predicted_level": predicted_level,
            "predicted_exam_score": predicted_exam_score,
            "next_topics": TOPIC_CATALOG.get(t, {}).get("prerequisites", []),
        })

    if not results:
        score_pct = 0.0
        predicted_level = predict_level_with_models(MODEL_BUNDLE, "python", score_pct)
        results.append({
            "topic": "python",
            "score_pct": score_pct,
            "predicted_level": predicted_level,
            "predicted_exam_score": predict_score_with_models(MODEL_BUNDLE, "python", score_pct),
            "next_topics": TOPIC_CATALOG.get("python", {}).get("prerequisites", []),
        })
    return results


def get_recommendations(topic: str, level: str, provider: str = "all", video_mode: str = "hybrid") -> dict:
    topic = normalize_topic(topic)
    live_videos = search_youtube_videos(topic, max_results=6, level=level) if video_mode in {"hybrid", "live"} else []
    dataset_videos = rank_catalog_videos(topic, level, max_results=6) if video_mode in {"hybrid", "dataset"} else []

    if video_mode == "live":
        videos = live_videos or dataset_videos
        video_source = "live_youtube_api" if live_videos else "youtube_dataset_csv_fallback"
    elif video_mode == "dataset":
        videos = dataset_videos
        video_source = "youtube_dataset_csv"
    else:
        videos = rank_live_and_dataset_videos(topic, level, live_videos, max_results=8)
        if live_videos and dataset_videos:
            video_source = "hybrid_live_plus_dataset"
        elif live_videos:
            video_source = "live_youtube_api"
        else:
            video_source = "youtube_dataset_csv"

    courses = rank_courses(topic, level, provider=provider, max_results=6)
    kaggle_sets = rank_kaggle_datasets(topic, level, max_results=4)
    project = project_for_topic(topic, level)
    
    # Fallback to TOPIC_CATALOG if no results
    if topic in TOPIC_CATALOG:
        if not courses:
            courses = TOPIC_CATALOG[topic].get("courses", [])
        if not project:
            project = TOPIC_CATALOG[topic].get("project", "Practice a small project on this topic.")
    
    # Ensure project is a string
    if isinstance(project, dict):
        project = project.get('project', 'Practice a small project on this topic.')
    if not project:
        project = 'Practice a small project on this topic.'
    
    return {
        "videos": videos,
        "courses": courses,
        "project": project,
        "datasets": kaggle_sets,
        "video_source": video_source,
    }


def _build_learning_path(profile: dict, assessment: list[dict]) -> list[dict]:
    topic_levels = {r["topic"]: r["predicted_level"] for r in assessment}
    weak_topics = {r["topic"] for r in assessment if r["score_pct"] < 45}
    completed_topics = {r["topic"] for r in assessment if r["score_pct"] >= 75}
    stored_progress = _coerce_path_progress(profile.get("topics", []), profile.get("path_progress", {}))
    learning_path = []
    for idx, topic in enumerate(profile.get("topics", []), start=1):
        level = topic_levels.get(topic, "beginner")
        rec = _topic_resource_payload(topic, level)
        status = stored_progress.get(topic, "locked")
        if topic in completed_topics:
            status = "completed"
        elif topic in weak_topics and status == "locked":
            status = "recommended"
        video_activity = profile.get('video_activity', {}).get(topic, {})
        course_activity = profile.get('course_activity', {}).get(topic, {})
        video_progress = 0
        if video_activity:
            video_progress = int(max((item.get('watched_pct') or 0) for item in video_activity.values()))
        course_progress = 0
        if course_activity:
            course_completions = sum(1 for item in course_activity.values() if item.get('completed'))
            course_clicks = sum(int(item.get('clicks', 0)) for item in course_activity.values())
            course_progress = min(100, course_completions * 40 + course_clicks * 10)
        learning_path.append({
            "topic": topic,
            "level": level,
            "videos": rec["videos"],
            "courses": rec["courses"],
            "project": rec["project"],
            "datasets": rec["datasets"],
            "prerequisites": TOPIC_CATALOG.get(topic, {}).get("prerequisites", []),
            "order": idx,
            "status": status,
            "mastery": next((r["score_pct"] for r in assessment if r["topic"] == topic), 0.0),
            "video_progress": video_progress,
            "course_progress": course_progress,
            "resource_items": len(rec["videos"]) + len(rec["courses"]) + len(rec["datasets"]),
            "status_label": _status_label(status),
        })
    profile["path_progress"] = {item["topic"]: item["status"] for item in learning_path}
    session["profile"] = profile
    return learning_path


def _build_resources(profile: dict, assessment: list[dict]) -> list[dict]:
    if not profile or not profile.get('topics'):
        return []
    topic_levels = {r["topic"]: r["predicted_level"] for r in assessment} if assessment else {}
    resources = []
    for topic in profile['topics']:
        level = topic_levels.get(topic, "beginner")
        rec = _topic_resource_payload(topic, level)
        # Merge without duplicate keys - use level from rec which already contains it
        resources.append(rec)
    return resources


def _get_or_create_default_profile() -> dict:
    profile = session.get('profile')
    if profile and profile.get('topics'):
        return profile
    default_topics = find_learning_order(list(TOPIC_CATALOG.keys()))
    quiz_seed = int(time.time() * 1000)
    quiz_items = get_topic_quiz(default_topics, quiz_seed=quiz_seed)
    profile = {
        'syllabus_text': 'Artificial Intelligence, Machine Learning, Reinforcement Learning',
        'target_goal': 'Master AI, ML & RL',
        'topics': default_topics,
        'quiz_seed': quiz_seed,
        'path_progress': _default_path_progress(default_topics),
        'activity': {
            'quiz_attempts': 0,
            'completed_actions': 0,
            'tutor_questions': 0,
        },
        'video_activity': {},
        'course_activity': {},
    }
    session['profile'] = profile
    if not session.get('quiz_items'):
        session['quiz_items'] = quiz_items
    return profile


def _dashboard_payload():
    profile = session.get("profile")
    if not profile or not profile.get("topics"):
        profile = _get_or_create_default_profile()
    assessment = session.get("assessment")
    assessment = assessment or []
    avg_score = round(sum(r["score_pct"] for r in assessment) / max(len(assessment), 1), 1) if assessment else 0
    strengths = [r["topic"] for r in assessment if r["score_pct"] >= 75]
    weak = [r["topic"] for r in assessment if r["score_pct"] < 45]
    learning_path = _build_learning_path(profile, assessment) if profile.get("topics") else []
    resources = _build_resources(profile, assessment) if profile.get("topics") else []
    notifications = []
    if weak:
        notifications.append({"type": "warning", "title": "Focus next", "message": f"Revise {weak[0].title()} first before moving to harder topics."})
    if strengths:
        notifications.append({"type": "success", "title": "Strong area", "message": f"You are doing well in {strengths[0].title()}."})
    if profile.get("topics"):
        notifications.append({"type": "info", "title": "Plan ready", "message": f"{len(profile['topics'])} syllabus topics were mapped into your study plan."})
    activity = profile.get("activity", {})
    path_metrics = _activity_metrics(profile, assessment)
    learning_score = path_metrics["learning_score"]
    if learning_score >= 80:
        notifications.append({"type": "success", "title": "Learning score rising", "message": f"Your adaptive learning score is now {learning_score}%."})

    # Retrieve real BKT mastery for learner if available
    bkt_mastery = None
    learner_id = session.get("learner_id")
    if learner_id:
        try:
            bkt_mastery = get_mastery_by_learner(learner_id)
        except Exception as e:
            app.logger.warning(f"Could not load BKT mastery for dashboard: {e}")

    return {
        "profile": profile,
        "assessment": assessment,
        "avgScore": avg_score,
        "strengths": strengths,
        "weakTopics": weak,
        "modelScores": MODEL_BUNDLE.leaderboard,
        "modelName": MODEL_BUNDLE.best_model_name,
        "automlEngine": MODEL_BUNDLE.engine,
        "dataInfo": DATA_INFO,
        "modernFeatures": recommend_recent_algorithms(avg_score),
        "youtubeLive": youtube_api_available(),
        "learningPath": learning_path,
        "resources": resources,
        "quizItems": session.get("quiz_items", []),
        "notifications": notifications,
        "availableTopics": sorted(TOPIC_CATALOG.keys()),
        "learningScore": learning_score,
        "pathMetrics": path_metrics,
        "pathProgress": profile.get("path_progress", {}),
        "videoActivity": profile.get("video_activity", {}),
        "courseActivity": profile.get("course_activity", {}),
        "aiFeatures": AI_FEATURES,
        "mlFeatures": ML_FEATURES,
        "datasetRegistry": DATASET_REGISTRY_DF.to_dict(orient="records"),
        "datasetSources": DATA_INFO.get("sources", []),
        "llmMode": "openai" if os.environ.get("OPENAI_API_KEY") else "local_rag_fallback",
        "bktMastery": bkt_mastery,
    }


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        origin = request.headers.get("Origin", "")
        if origin in {"http://localhost:3000", "http://127.0.0.1:3000"}:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp


@app.after_request
def add_no_cache_headers(resp):
    resp.headers["Cache-Control"] = "no-store"
    origin = request.headers.get("Origin", "")
    if origin in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Vary"] = "Origin"
    return resp


@app.errorhandler(Exception)
def handle_api_error(err):
    if isinstance(err, HTTPException):
        code = err.code or 500
        description = err.description
    else:
        code = 500
        description = str(err) or "Internal server error"
    if request.path.startswith('/api/'):
        return jsonify({"ok": False, "error": description}), code
    raise err


@app.route("/")
def index():
    return jsonify({
        "message": "Backend API is running. Start the React frontend with npm start and open http://localhost:3000",
        "frontend": "http://localhost:3000",
        "api_status": "/api/status",
    })


@app.route('/api/status')
def api_status():
    return jsonify({"ok": True, "real_data_used": DATA_INFO["real_data_used"], "rows": DATA_INFO["rows"], "engine": MODEL_BUNDLE.engine})


@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.get_json(silent=True) or {}
    syllabus_text = (data.get('syllabus_text') or '').strip()
    target_goal = (data.get('target_goal') or '').strip()
    topics = find_learning_order(parse_topics(syllabus_text, target_goal))
    quiz_seed = int(time.time() * 1000)
    quiz_items = get_topic_quiz(topics, quiz_seed=quiz_seed)
    profile = {
        'syllabus_text': syllabus_text,
        'target_goal': target_goal,
        'topics': topics,
        'quiz_seed': quiz_seed,
        'path_progress': _default_path_progress(topics),
        'activity': {
            'quiz_attempts': 0,
            'completed_actions': 0,
            'tutor_questions': 0,
        },
        'video_activity': {},
        'course_activity': {},
    }
    session['profile'] = profile
    session['quiz_items'] = quiz_items
    session.pop('assessment', None)
    session.pop('answers', None)
    return jsonify({
        'ok': True,
        'profile': profile,
        'quizItems': quiz_items,
        'availableTopics': topics,
    })


@app.route('/api/quiz', methods=['GET', 'POST'])
def api_quiz():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()

    if request.method == 'GET':
        force_new = request.args.get('refresh') == '1'
        if force_new or not session.get('quiz_items'):
            quiz_seed = int(time.time() * 1000)
            profile['quiz_seed'] = quiz_seed
            profile.setdefault("activity", {"quiz_attempts": 0, "completed_actions": 0})
            session['profile'] = profile
            seen_history = session.get('quiz_seen_ids', [])
            new_items = get_topic_quiz(profile['topics'], quiz_seed=quiz_seed, excluded_ids=seen_history)
            session['quiz_items'] = new_items
            new_cids = [q.get('canonical_item_id') or q.get('item_id') for q in new_items if q.get('canonical_item_id') or q.get('item_id')]
            session['quiz_seen_ids'] = list(dict.fromkeys(seen_history + new_cids))
        return jsonify({'ok': True, 'quizItems': session.get('quiz_items', []), 'topics': profile['topics']})

    data = request.get_json(silent=True) or {}
    answers = data.get('answers') or {}
    response_times = data.get('response_times') or {}
    learner_id = data.get('learner_id') or session.get('learner_id') or f"learner_{abs(hash(str(profile.get('syllabus_text', 'default')))) % 1000000:06d}"
    session_id = data.get('session_id') or session.get('learning_session_id')
    attempt_num = int(profile.get('activity', {}).get('quiz_attempts', 0)) + 1

    quiz_items = session.get('quiz_items') or get_topic_quiz(profile['topics'], quiz_seed=profile.get('quiz_seed'))
    results = build_topic_results(profile['topics'], answers, quiz_items)
    profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0})
    profile['activity']['quiz_attempts'] = attempt_num
    session['profile'] = profile
    session['assessment'] = results
    session['answers'] = answers
    session['learner_id'] = learner_id

    # Background-safe learner event logging
    try:
        if not session_id:
            db_session = create_learning_session(
                learner_id=learner_id,
                session_type="quiz",
                target_topics=profile.get('topics', []),
                metadata={"seed": profile.get("quiz_seed")},
            )
            session_id = db_session["session_id"]
            session['learning_session_id'] = session_id

        for q in quiz_items:
            key = f"{q.get('topic')}_{q.get('index')}"
            if key in answers:
                submitted = answers.get(key)
                correct_ans = q.get("correct_answer") or q.get("answer")
                is_corr = int(submitted == correct_ans)
                rt_ms = response_times.get(key)
                log_learning_event(
                    session_id=session_id,
                    learner_id=learner_id,
                    item_id=q.get("item_id") or key,
                    knowledge_components=q.get("knowledge_components") or [q.get("topic")],
                    submitted_answer=submitted,
                    correctness=is_corr,
                    response_time_ms=rt_ms,
                    attempt_number=attempt_num,
                    interaction_type="quiz_answer",
                    metadata={
                        "topic": q.get("topic"),
                        "difficulty": q.get("difficulty"),
                        "canonical_item_id": q.get("canonical_item_id"),
                    },
                )
    except Exception as e:
        app.logger.warning(f"Error persisting learning events: {e}")

    payload = _dashboard_payload()
    return jsonify({'ok': True, 'session_id': session_id, 'learner_id': learner_id, **payload})


# ============================================================================
# PHASE 1 KT-RL DATA FOUNDATION & INTERACTION ENDPOINTS
# ============================================================================

@app.route('/api/learning/sessions', methods=['POST'])
def api_learning_sessions_create():
    data = request.get_json(silent=True) or {}
    learner_id = (data.get('learner_id') or '').strip()
    if not learner_id:
        return jsonify({'ok': False, 'error': 'learner_id is required'}), 400
    session_type = data.get('session_type', 'practice')
    target_topics = data.get('target_topics', [])
    metadata = data.get('metadata')

    try:
        sess = create_learning_session(
            learner_id=learner_id,
            session_type=session_type,
            target_topics=target_topics,
            metadata=metadata,
        )
        return jsonify({'ok': True, 'session': sess}), 201
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/learning/sessions/<session_id>', methods=['GET'])
def api_learning_sessions_get(session_id):
    sess = get_learning_session(session_id)
    if not sess:
        return jsonify({'ok': False, 'error': 'Session not found'}), 404
    return jsonify({'ok': True, 'session': sess})


@app.route('/api/learning/sessions/<session_id>/complete', methods=['POST'])
def api_learning_sessions_complete(session_id):
    sess = complete_learning_session(session_id)
    if not sess:
        return jsonify({'ok': False, 'error': 'Session not found'}), 404
    return jsonify({'ok': True, 'session': sess})


@app.route('/api/learning/events', methods=['POST'])
def api_learning_events_log():
    data = request.get_json(silent=True) or {}
    required_fields = ['session_id', 'learner_id', 'item_id', 'correctness']
    for rf in required_fields:
        if rf not in data:
            return jsonify({'ok': False, 'error': f"Field '{rf}' is required"}), 400

    try:
        evt = log_learning_event(
            session_id=data['session_id'],
            learner_id=data['learner_id'],
            item_id=data['item_id'],
            knowledge_components=data.get('knowledge_components', []),
            submitted_answer=data.get('submitted_answer'),
            correctness=int(data['correctness']),
            response_time_ms=data.get('response_time_ms'),
            attempt_number=int(data.get('attempt_number', 1)),
            interaction_type=data.get('interaction_type', 'quiz_answer'),
            metadata=data.get('metadata'),
        )
        return jsonify({'ok': True, 'event': evt}), 201
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/learning/events/<learner_id>', methods=['GET'])
def api_learning_events_get(learner_id):
    limit = int(request.args.get('limit', 100))
    events = get_learner_events(learner_id, limit=limit)
    return jsonify({'ok': True, 'learner_id': learner_id, 'count': len(events), 'events': events})


@app.route('/api/learning/state/<learner_id>', methods=['GET'])
def api_learning_state_get(learner_id):
    state = get_learner_state(learner_id)
    return jsonify({'ok': True, 'learner_id': learner_id, 'state': state})


@app.route('/api/learning/items', methods=['GET'])
def api_learning_items_list():
    items = get_all_questions()
    validation = validate_item_bank()
    return jsonify({
        'ok': True,
        'count': len(items),
        'items': items,
        'item_bank_validation': validation,
    })


# ============================================================================
# PHASE 2 KT-RL BAYESIAN KNOWLEDGE TRACING (BKT) ENDPOINTS
# ============================================================================

@app.route('/api/learning/mastery/<learner_id>', methods=['GET'])
def api_learning_mastery_get(learner_id):
    learner_id_clean = (learner_id or '').strip()
    if not learner_id_clean:
        return jsonify({'ok': False, 'error': 'learner_id is required'}), 400

    try:
        mastery_data = get_mastery_by_learner(learner_id_clean)
        return jsonify({'ok': True, **mastery_data})
    except Exception as e:
        app.logger.error(f"Error computing BKT mastery for {learner_id}: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/learning/mastery/<learner_id>/replay', methods=['POST'])
def api_learning_mastery_replay(learner_id):
    learner_id_clean = (learner_id or '').strip()
    if not learner_id_clean:
        return jsonify({'ok': False, 'error': 'learner_id is required'}), 400

    data = request.get_json(silent=True) or {}
    params = BKT_DEFAULT_PARAMS

    # Optional custom parameter overrides for experimentation
    if "parameters" in data:
        p_dict = data["parameters"]
        try:
            params = BKTParameters(
                p_l0=float(p_dict.get("p_l0", params.p_l0)),
                p_t=float(p_dict.get("p_t", params.p_t)),
                p_g=float(p_dict.get("p_g", params.p_g)),
                p_s=float(p_dict.get("p_s", params.p_s)),
                version=str(p_dict.get("version", "custom-experimental")),
                is_calibrated=bool(p_dict.get("is_calibrated", False)),
            )
        except Exception as err:
            return jsonify({'ok': False, 'error': f'Invalid BKT parameters: {err}'}), 400

    try:
        replayed = replay_learner_history(learner_id_clean, params=params)
        return jsonify({'ok': True, **replayed})
    except Exception as e:
        app.logger.error(f"Error replaying BKT history for {learner_id}: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/learning/mastery/<learner_id>/<kc_id>', methods=['GET'])
def api_learning_mastery_kc_get(learner_id, kc_id):
    learner_id_clean = (learner_id or '').strip()
    kc_id_clean = (kc_id or '').strip()
    if not learner_id_clean or not kc_id_clean:
        return jsonify({'ok': False, 'error': 'learner_id and kc_id are required'}), 400

    try:
        kc_state = get_kc_mastery(learner_id_clean, kc_id_clean)
        if not kc_state:
            return jsonify({'ok': False, 'error': f"Knowledge component '{kc_id}' not found in catalog"}), 404
        return jsonify({'ok': True, 'learner_id': learner_id_clean, 'topic': kc_state})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/context')
def api_context():
    return jsonify(_dashboard_payload())


@app.route('/api/reset', methods=['POST'])
def api_reset():
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/search')
def api_search():
    query = (request.args.get('q') or '').strip().lower()
    payload = _dashboard_payload()
    pool = []
    for card in payload.get('resources', []):
        for course in card.get('courses', []):
            pool.append({'kind': 'course', 'topic': card['topic'], 'title': course.get('title', ''), 'url': course.get('url', ''), 'provider': course.get('provider', '')})
        for video in card.get('videos', []):
            pool.append({'kind': 'video', 'topic': card['topic'], 'title': video.get('title', ''), 'url': video.get('url', ''), 'provider': video.get('channel', '')})
        for ds in card.get('datasets', []):
            pool.append({'kind': 'dataset', 'topic': card['topic'], 'title': ds.get('title', ''), 'url': ds.get('url', ''), 'provider': ds.get('source', '')})
    if not query:
        return jsonify({'ok': True, 'results': pool[:10]})
    results = [item for item in pool if query in item['title'].lower() or query in item['topic'].lower() or query in item.get('provider', '').lower()]
    return jsonify({'ok': True, 'results': results[:12]})


@app.route('/api/notifications')
def api_notifications():
    payload = _dashboard_payload()
    return jsonify({'ok': True, 'notifications': payload.get('notifications', [])})


@app.route('/api/path/update', methods=['POST'])
def api_path_update():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    data = request.get_json(silent=True) or {}
    topic = normalize_topic(data.get('topic') or '')
    status = (data.get('status') or '').strip().lower()
    if topic not in profile.get('topics', []):
        return jsonify({'ok': False, 'error': 'Unknown topic for this plan.'}), 400
    if status not in {'recommended', 'in-progress', 'completed', 'locked'}:
        return jsonify({'ok': False, 'error': 'Invalid path status.'}), 400
    progress = _coerce_path_progress(profile.get('topics', []), profile.get('path_progress', {}))
    progress[topic] = status
    topics = profile.get('topics', [])
    if status == 'completed':
        idx = topics.index(topic)
        if idx + 1 < len(topics) and progress[topics[idx + 1]] == 'locked':
            progress[topics[idx + 1]] = 'recommended'
    elif status == 'in-progress':
        for prereq in TOPIC_CATALOG.get(topic, {}).get('prerequisites', []):
            if prereq in topics and progress.get(prereq) == 'locked':
                progress[prereq] = 'recommended'
    profile['path_progress'] = progress
    profile.setdefault("activity", {"quiz_attempts": 0, "completed_actions": 0, "tutor_questions": 0})
    if status in {'completed', 'in-progress'}:
        profile['activity']['completed_actions'] = int(profile['activity'].get('completed_actions', 0)) + 1
    session['profile'] = profile
    return jsonify({'ok': True, **_dashboard_payload()})


@app.route('/api/path/step/update', methods=['POST'])
def api_path_step_update():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    data = request.get_json(silent=True) or {}
    topic = normalize_topic(data.get('topic') or '')
    status = _normalize_step_status(data.get('status') or '')
    if topic not in profile.get('topics', []):
        return jsonify({'ok': False, 'error': 'Unknown topic for this plan.'}), 400
    progress = _coerce_path_progress(profile.get('topics', []), profile.get('path_progress', {}))
    progress[topic] = status
    topics = profile.get('topics', [])
    if status == 'completed':
        idx = topics.index(topic)
        if idx + 1 < len(topics) and progress[topics[idx + 1]] == 'locked':
            progress[topics[idx + 1]] = 'recommended'
    elif status == 'in-progress':
        for prereq in TOPIC_CATALOG.get(topic, {}).get('prerequisites', []):
            if prereq in topics and progress.get(prereq) == 'locked':
                progress[prereq] = 'recommended'
    profile['path_progress'] = progress
    profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0, 'tutor_questions': 0})
    profile['activity']['completed_actions'] = int(profile['activity'].get('completed_actions', 0)) + 1
    session['profile'] = profile
    return jsonify({'ok': True, **_dashboard_payload()})


@app.route('/api/path/resources')
def api_path_resources():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    topic_query = request.args.get('topic', '')
    topic = _resolve_topic_for_resources(topic_query, profile)
    assessment = session.get('assessment') or []
    level = next((r['predicted_level'] for r in assessment if r.get('topic') == topic), 'beginner')
    resources = _topic_resource_payload(topic, level)
    return jsonify({'ok': True, 'topic': topic, 'resources': resources})


@app.route('/api/path/video/track', methods=['POST'])
def api_path_video_track():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    data = request.get_json(silent=True) or {}
    topic = _resolve_topic_for_resources(data.get('topic', ''), profile)
    if not topic:
        return jsonify({'ok': False, 'error': 'Invalid topic.'}), 400
    url = (data.get('url') or '').strip()
    watched_seconds = int(data.get('watched_seconds') or 0)
    watched_pct = float(data.get('watched_pct') or 0)
    event = (data.get('event') or '').strip().lower()
    video_activity = profile.setdefault('video_activity', {}).setdefault(topic, {})
    entry = video_activity.setdefault(url, {'clicks': 0, 'watched_seconds': 0, 'watched_pct': 0.0, 'events': []})
    if event == 'start':
        entry['events'].append({'event': 'start', 'at': time.time()})
    if watched_seconds:
        entry['watched_seconds'] = max(entry['watched_seconds'], watched_seconds)
    if watched_pct:
        entry['watched_pct'] = max(entry['watched_pct'], watched_pct)
    if event == 'click':
        entry['clicks'] = int(entry.get('clicks', 0)) + 1
    if watched_pct >= 40 and profile.get('path_progress', {}).get(topic) not in {'in-progress', 'completed'}:
        profile['path_progress'] = _coerce_path_progress(profile.get('topics', []), profile.get('path_progress', {}))
        profile['path_progress'][topic] = 'in-progress'
    if watched_pct >= 80:
        profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0, 'tutor_questions': 0})
        profile['activity']['completed_actions'] = int(profile['activity'].get('completed_actions', 0)) + 1
    session['profile'] = profile
    return jsonify({'ok': True, **_dashboard_payload()})


@app.route('/api/path/course/track', methods=['POST'])
def api_path_course_track():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    data = request.get_json(silent=True) or {}
    topic = _resolve_topic_for_resources(data.get('topic', ''), profile)
    if not topic:
        return jsonify({'ok': False, 'error': 'Invalid topic.'}), 400
    url = (data.get('url') or '').strip()
    action = (data.get('action') or '').strip().lower()
    if not url or action not in {'click', 'completed'}:
        return jsonify({'ok': False, 'error': 'Invalid course track payload.'}), 400
    course_activity = profile.setdefault('course_activity', {}).setdefault(topic, {})
    entry = course_activity.setdefault(url, {'clicks': 0, 'revisits': 0, 'completed': False, 'last_action': None})
    if action == 'click':
        entry['clicks'] = int(entry.get('clicks', 0)) + 1
        entry['revisits'] = int(entry.get('revisits', 0)) + 1
        entry['last_action'] = 'click'
    elif action == 'completed':
        entry['completed'] = True
        entry['last_action'] = 'completed'
    profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0, 'tutor_questions': 0})
    profile['activity']['completed_actions'] = int(profile['activity'].get('completed_actions', 0)) + 1
    if action == 'completed' and profile.get('path_progress', {}).get(topic) == 'locked':
        profile['path_progress'] = _coerce_path_progress(profile.get('topics', []), profile.get('path_progress', {}))
        profile['path_progress'][topic] = 'recommended'
    session['profile'] = profile
    return jsonify({'ok': True, **_dashboard_payload()})


@app.route('/api/path/progress')
def api_path_progress():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    assessment = session.get('assessment') or []
    metrics = _activity_metrics(profile, assessment)
    return jsonify({
        'ok': True,
        'pathProgress': profile.get('path_progress', {}),
        'learningScore': metrics['learning_score'],
        'pathMetrics': metrics,
        'videoActivity': profile.get('video_activity', {}),
        'courseActivity': profile.get('course_activity', {}),
    })


@app.route('/api/learning-path', methods=['GET'])
def api_learning_path():
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    topics = profile.get('topics', [])
    assessment = session.get('assessment') or []
    path_progress = profile.get('path_progress', {})

    steps = []
    completed_count = 0
    for idx, t in enumerate(topics):
        meta = TOPIC_CATALOG.get(t, {})
        status = path_progress.get(t, 'ready' if idx == 0 else 'locked')
        score_match = next((a for a in assessment if a.get('topic') == t), None)
        if score_match and score_match.get('score_pct', 0) >= 70:
            status = 'completed'
        elif score_match:
            status = 'in-progress'

        if status == 'completed':
            completed_count += 1

        steps.append({
            'topic': t,
            'title': t.replace('_', ' ').title(),
            'status': status,
            'prerequisites': meta.get('prerequisites', []),
            'level': 'beginner' if idx < 3 else ('intermediate' if idx < 8 else 'advanced'),
            'estimated_hours': 6 + (idx % 5) * 2,
            'project': meta.get('project', f'Hands-on practical exercise on {t}.'),
        })

    overall_pct = int(round((completed_count / max(1, len(topics))) * 100))
    return jsonify({
        'ok': True,
        'steps': steps,
        'overall_progress_pct': overall_pct,
        'topics': topics,
    })


@app.route('/api/tutor', methods=['POST'])
def api_tutor():
    data = request.get_json(silent=True) or {}
    raw_question = (data.get('question') or '').strip()
    profile = session.get('profile')
    if not profile or not profile.get('topics'):
        profile = _get_or_create_default_profile()
    assessment = session.get('assessment') or []
    if not raw_question:
        return jsonify({'ok': False, 'error': 'Ask a question first.'}), 400
    profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0, 'tutor_questions': 0})
    profile['activity']['tutor_questions'] = int(profile['activity'].get('tutor_questions', 0)) + 1
    session['profile'] = profile
    reply = generate_tutor_reply(raw_question, profile, assessment)
    return jsonify({
        'ok': True,
        'answer': reply.answer,
        'topic': reply.detected_topic,
        'mode': reply.mode,
        'retrieved': reply.retrieved,
        'model': reply.model,
    })
    profile.setdefault('activity', {'quiz_attempts': 0, 'completed_actions': 0, 'tutor_questions': 0})
    profile['activity']['tutor_questions'] = int(profile['activity'].get('tutor_questions', 0)) + 1
    session['profile'] = profile
    reply = generate_tutor_reply(raw_question, profile, assessment)
    return jsonify({
        'ok': True,
        'answer': reply.answer,
        'topic': reply.detected_topic,
        'mode': reply.mode,
        'retrieved': reply.retrieved_chunks,
        'related_resources': reply.related_resources,
    })


@app.route('/api/features')
def api_features():
    return jsonify({
        'ok': True,
        'aiFeatures': AI_FEATURES,
        'mlFeatures': ML_FEATURES,
        'datasets': DATASET_REGISTRY_DF.to_dict(orient='records'),
        'dataInfo': DATA_INFO,
        'llmMode': 'openai' if os.environ.get('OPENAI_API_KEY') else 'local_rag_fallback',
    })


@app.route('/api/experimental/recommendation', methods=['POST'])
def api_experimental_recommendation():
    """
    Opt-in experimental exercise recommendation endpoint.
    Controlled by KT_RL_EXPERIMENT_ENABLED environment variable.
    Strictly isolated from synthetic ground truth. Falls back gracefully to baseline logic.
    """
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or 'anonymous').strip()
    session_history = data.get('session_history', [])
    recent_failures = int(data.get('recent_topic_failures', 0))
    last_difficulty = int(data.get('last_difficulty', 2))
    current_step = int(data.get('current_step', 0))

    try:
        from services.experimental_recommendation_service import ExperimentalExerciseService
        service = ExperimentalExerciseService()
        result = service.recommend_exercise(
            learner_id=learner_id,
            session_history=session_history,
            recent_topic_failures=recent_failures,
            last_difficulty=last_difficulty,
            current_step=current_step,
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': 'Experimental recommendation service encountered an error.',
            'fallback_used': True,
        }), 500


@app.route('/api/adaptive/recommendation', methods=['GET', 'POST'])
def api_adaptive_recommendation():
    """
    Unified Adaptive Exercise Recommendation endpoint.
    Dynamically balances BKT mastery, longitudinal forgetting, posterior uncertainty,
    and disengagement/frustration risk while enforcing prerequisite eligibility.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
    else:
        data = request.args.to_dict()

    learner_id = str(data.get('learner_id') or data.get('user_id') or session.get('learner_id') or 'anonymous').strip()
    strategy = str(data.get('strategy') or 'composite_adaptive').strip().lower()

    try:
        from services.adaptive_recommender import UnifiedAdaptiveRecommender
        recommender = UnifiedAdaptiveRecommender()
        result = recommender.recommend(learner_id=learner_id, strategy=strategy)

        # Phase 8: Safe Shadow Evaluation hook (strictly executes only if KT_RL_SHADOW_MODE=1)
        try:
            from services.shadow_evaluation import is_shadow_mode_enabled, execute_shadow_comparison
            if is_shadow_mode_enabled():
                execute_shadow_comparison(recommender, learner_id, result)
        except Exception as shadow_err:
            app.logger.warning(f"Shadow evaluation hook warning: {shadow_err}")

        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error generating adaptive recommendation: {e}")
        return jsonify({
            'ok': False,
            'error': 'Failed to generate adaptive recommendation.',
        }), 500


@app.route('/api/adaptive/diagnostics', methods=['GET'])
def api_adaptive_diagnostics():
    """
    Retrieves observable adaptive diagnostics for a learner:
    retention decay, evidence confidence, frustration signals, and prerequisite status.
    """
    learner_id = str(request.args.get('learner_id') or request.args.get('user_id') or session.get('learner_id') or 'anonymous').strip()
    try:
        from services.adaptive_recommender import UnifiedAdaptiveRecommender
        recommender = UnifiedAdaptiveRecommender()
        res = recommender.recommend(learner_id=learner_id, strategy='composite_adaptive')
        return jsonify({
            'ok': True,
            'learner_id': learner_id,
            'diagnostics': res.get('diagnostics', {}),
            'explanation': res.get('explanation', {}),
        }), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/practice/submit', methods=['POST'])
def api_practice_submit():
    """
    Submits an individual practice response for an adaptive exercise.
    Evaluates correctness, logs learning event in SQLite, and returns feedback.
    """
    data = request.get_json(silent=True) or {}
    item_id = str(data.get('item_id') or '').strip()
    selected_option = str(data.get('selected_option') or '').strip()
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'anonymous').strip()
    response_time_ms = int(data.get('response_time_ms') or 2000)

    if not item_id or not selected_option:
        return jsonify({'ok': False, 'error': 'item_id and selected_option are required'}), 400

    q = get_question_by_id(item_id)
    if not q:
        return jsonify({'ok': False, 'error': f"Question '{item_id}' not found"}), 404

    correct_answer = q.get('answer') or q.get('correct_answer') or ''
    is_correct = (selected_option.strip().lower() == correct_answer.strip().lower())
    topic = q.get('topic') or 'general'
    kcs = q.get('knowledge_components') or [topic]

    # Log learning event in SQLite
    try:
        session_id = data.get('session_id')
        if not session_id:
            db_session = create_learning_session(
                learner_id=learner_id,
                session_type='adaptive_practice',
                metadata={'source': 'in_place_practice'}
            )
            session_id = db_session['session_id']

        log_learning_event(
            session_id=session_id,
            learner_id=learner_id,
            item_id=item_id,
            knowledge_components=kcs,
            submitted_answer=selected_option,
            correctness=1 if is_correct else 0,
            response_time_ms=response_time_ms,
            attempt_number=1,
            interaction_type='adaptive_exercise',
            metadata={'topic': topic, 'difficulty': q.get('difficulty', 2)},
        )
    except Exception as log_err:
        app.logger.warning(f"Error logging practice event: {log_err}")

    # Fetch updated BKT mastery for this topic
    try:
        from services.bkt_service import get_kc_mastery
        updated_mastery = get_kc_mastery(learner_id, topic)
    except Exception:
        updated_mastery = None

    return jsonify({
        'ok': True,
        'item_id': item_id,
        'topic': topic,
        'is_correct': is_correct,
        'selected_option': selected_option,
        'correct_answer': correct_answer,
        'difficulty': q.get('difficulty', 2),
        'updated_mastery': updated_mastery,
    }), 200



# ============================================================================
# PHASE 8 PRE/POST ASSESSMENT, PRIVACY EXPORT & SHADOW EVALUATION ENDPOINTS
# ============================================================================

@app.route('/api/assessment/config', methods=['GET'])
def api_assessment_config():
    """Returns assessment framework metadata, supported types, and question counts."""
    try:
        from services.assessment_service import DEFAULT_ASSESSMENT_LENGTH, SESSION_TIMEOUT_MINUTES
        from resources import get_all_questions
        total_items = len(get_all_questions())
        return jsonify({
            'ok': True,
            'default_length': DEFAULT_ASSESSMENT_LENGTH,
            'timeout_minutes': SESSION_TIMEOUT_MINUTES,
            'supported_types': ['pre', 'post', 'retention'],
            'total_available_questions': total_items,
        }), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/start', methods=['POST'])
def api_assessment_start():
    """Initializes an assessment session (pre, post, retention) with answer-concealed questions."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('user_id') or data.get('learner_id') or session.get('learner_id') or 'anonymous').strip()
    assessment_type = str(data.get('assessment_type') or 'pre').strip().lower()
    num_questions = int(data.get('num_questions') or 10)

    try:
        from services.assessment_service import start_assessment_session
        result = start_assessment_session(
            learner_id=learner_id,
            assessment_type=assessment_type,
            num_questions=num_questions
        )
        return jsonify({'ok': True, 'assessment': result}), 200
    except Exception as e:
        app.logger.error(f"Error starting assessment: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/assessment/submit', methods=['POST'])
def api_assessment_submit():
    """Evaluates student answers, scores assessment session, and returns per-KC breakdown."""
    data = request.get_json(silent=True) or {}
    assessment_id = data.get('assessment_id')
    responses = data.get('responses') or []

    if not assessment_id:
        return jsonify({'ok': False, 'error': 'assessment_id is required'}), 400

    try:
        from services.assessment_service import submit_assessment_session
        result = submit_assessment_session(
            assessment_id=assessment_id,
            responses=responses
        )
        return jsonify({'ok': True, 'results': result}), 200
    except Exception as e:
        app.logger.error(f"Error submitting assessment: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.route('/api/assessment/history/<learner_id>', methods=['GET'])
def api_assessment_history(learner_id):
    """Retrieves all past assessment sessions for a specific learner."""
    try:
        from services.assessment_service import get_learner_assessments
        records = get_learner_assessments(learner_id=learner_id)
        return jsonify({'ok': True, 'learner_id': learner_id, 'assessments': records}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/compare/<learner_id>', methods=['GET'])
def api_assessment_compare(learner_id):
    """Calculates learning gain, normalized gain (Hake's g), and retention deltas for a learner."""
    try:
        from services.assessment_service import compare_pre_post_assessments
        comparison = compare_pre_post_assessments(learner_id=learner_id)
        return jsonify({'ok': True, 'comparison': comparison}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/export', methods=['GET'])
def api_research_export():
    """Exports a FERPA/IRB compliant anonymized research dataset with cryptographic pseudonyms."""
    salt = request.args.get('salt')
    include_events = request.args.get('include_events', 'true').lower() in ('true', '1')
    try:
        from services.privacy_service import export_anonymized_research_dataset
        dataset = export_anonymized_research_dataset(salt=salt, include_events=include_events)
        return jsonify({'ok': True, 'dataset': dataset}), 200
    except Exception as e:
        app.logger.error(f"Error generating research export: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/shadow_metrics', methods=['GET'])
def api_research_shadow_metrics():
    """Returns concordance rates, agreement metrics, and execution latencies for shadow policies."""
    try:
        from services.shadow_evaluation import get_shadow_metrics
        metrics = get_shadow_metrics()
        return jsonify({'ok': True, 'metrics': metrics}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/learner_progress/<learner_id>', methods=['GET'])
def api_research_learner_progress(learner_id):
    """Provides a holistic view of learner growth: BKT trajectory, assessment deltas, and explanations."""
    try:
        from services.assessment_service import compare_pre_post_assessments
        from services.bkt_service import get_mastery_by_learner
        from services.adaptive_recommender import UnifiedAdaptiveRecommender

        mastery_data = get_mastery_by_learner(learner_id)
        comparison = compare_pre_post_assessments(learner_id)
        recommender = UnifiedAdaptiveRecommender()
        diag = recommender.recommend(learner_id=learner_id, strategy='composite_adaptive')

        return jsonify({
            'ok': True,
            'learner_id': learner_id,
            'bkt_mastery': mastery_data,
            'assessment_comparison': comparison,
            'recommendation_explanation': diag.get('explanation', {}),
        }), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/curriculum/plan', methods=['GET'])
def api_curriculum_plan():
    """Generates personalized multi-stage curriculum plan using prerequisite DAG and BKT mastery."""
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'anonymous').strip()
    target_goal = str(request.args.get('target_goal') or 'full_curriculum').strip()
    try:
        from services.curriculum_planner import CurriculumPlanner
        planner = CurriculumPlanner()
        plan = planner.generate_curriculum_plan(learner_id=learner_id, target_goal=target_goal)
        return jsonify(plan), 200
    except Exception as e:
        app.logger.error(f"Error generating curriculum plan: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/diagnostic/calibration', methods=['GET'])
def api_diagnostic_calibration():
    """Evaluates probabilistic calibration (ECE, MCE, Brier score) of BKT predictions."""
    learner_id = request.args.get('learner_id')
    try:
        from services.learning_store import get_learner_events
        from services.diagnostic_calibration import evaluate_bkt_calibration
        from services.bkt_service import DEFAULT_PARAMS

        events = get_learner_events(learner_id=learner_id, limit=1000) if learner_id else []
        preds = []
        labels = []
        for ev in events:
            # Predict probability of correct answer from prior or default
            p_prior = 0.20
            p_correct = DEFAULT_PARAMS.p_g + (1.0 - DEFAULT_PARAMS.p_g - DEFAULT_PARAMS.p_s) * p_prior
            preds.append(p_correct)
            labels.append(int(ev.get("is_correct", 0)))

        # Default synthetic calibration baseline if events empty
        if not preds:
            preds = [0.85, 0.75, 0.65, 0.45, 0.35, 0.25, 0.90, 0.80, 0.60, 0.30]
            labels = [1, 1, 1, 0, 0, 0, 1, 1, 0, 0]

        report = evaluate_bkt_calibration(preds, labels)
        return jsonify({'ok': True, 'calibration': report}), 200
    except Exception as e:
        app.logger.error(f"Error calculating calibration: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/revision/plan', methods=['GET'])
def api_revision_plan():
    """Returns the spaced repetition schedule (due-today queue and upcoming revisions) for a learner."""
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'anonymous').strip()
    try:
        from services.learning_store import get_learner_events
        from services.spaced_repetition import SpacedRepetitionScheduler

        events = get_learner_events(learner_id=learner_id, limit=500, reverse=False)
        scheduler = SpacedRepetitionScheduler()
        for step, ev in enumerate(events, 1):
            kc = ev.get('topic') or ev.get('kc_id')
            is_corr = bool(ev.get('is_correct', False))
            if kc:
                scheduler.record_practice(kc, step, is_corr)

        current_step = max(len(events), 1)
        due_list = []
        upcoming_list = []

        for kc_id, state in scheduler.kc_states.items():
            if state.total_reviews > 0:
                retrievability = state.compute_retrievability(current_step)
                elapsed = max(0, current_step - state.last_reviewed_step)
                item = {
                    'kc_id': kc_id,
                    'topic': kc_id,
                    'retrievability': round(retrievability, 3),
                    'retrievability_pct': round(retrievability * 100, 1),
                    'stability': round(state.stability, 2),
                    'repetition_count': state.repetition_count,
                    'total_reviews': state.total_reviews,
                    'last_reviewed_step': state.last_reviewed_step,
                    'elapsed_steps': elapsed,
                    'last_was_correct': state.last_was_correct,
                    'status': 'due' if retrievability <= scheduler.retrieval_threshold else 'retained'
                }
                if item['status'] == 'due':
                    due_list.append(item)
                else:
                    upcoming_list.append(item)

        due_list.sort(key=lambda x: x['retrievability'])
        upcoming_list.sort(key=lambda x: x['retrievability'])

        total_practiced = len(due_list) + len(upcoming_list)
        avg_retrievability = (
            round(sum(x['retrievability'] for x in (due_list + upcoming_list)) / total_practiced, 3)
            if total_practiced > 0 else 1.0
        )

        return jsonify({
            'ok': True,
            'learner_id': learner_id,
            'current_step': current_step,
            'retrieval_threshold': scheduler.retrieval_threshold,
            'due_today': due_list,
            'upcoming': upcoming_list,
            'summary': {
                'total_practiced_kcs': total_practiced,
                'due_count': len(due_list),
                'retained_count': len(upcoming_list),
                'avg_retrievability': avg_retrievability,
                'avg_retrievability_pct': round(avg_retrievability * 100, 1),
            }
        }), 200
    except Exception as e:
        app.logger.error(f"Error calculating revision plan: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/research/benchmark', methods=['GET'])
def api_research_benchmark():
    """Returns the comprehensive 10-policy benchmark comparison results and metadata."""
    try:
        report_path = os.path.join(str(BASE_DIR), 'reports', 'phase8_benchmark_results.json')
        if not os.path.exists(report_path):
            alt_path = os.path.join(os.path.dirname(str(BASE_DIR)), 'reports', 'phase8_benchmark_results.json')
            if os.path.exists(alt_path):
                report_path = alt_path

        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({'ok': True, 'data': data}), 200
        else:
            return jsonify({'ok': False, 'error': 'Benchmark results file not found'}), 404
    except Exception as e:
        app.logger.error(f"Error reading benchmark results: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================================================
# PERSONALIZED LEARNING ASSISTANT & SMART EXAM PREP ENDPOINTS
# ============================================================================

@app.route('/api/assistant/start', methods=['POST'])
def api_assistant_start():
    """Starts a personalized learning session (continue, weak_topics, exam_prep, revision)."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    mode = str(data.get('mode') or 'continue').strip().lower()
    topic = data.get('topic')
    exam_id = data.get('exam_id')

    try:
        from services.adaptive_tutor import AdaptiveTutorService
        tutor = AdaptiveTutorService()
        result = tutor.start_tutor_session(
            learner_id=learner_id,
            mode=mode,
            topic=topic,
            exam_id=exam_id,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error starting assistant session: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assistant/step', methods=['POST'])
def api_assistant_step():
    """Submits a student's answer, logs event, updates BKT, and selects next pedagogical action."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    item_id = data.get('item_id')
    selected_option = data.get('selected_option')
    response_time_ms = int(data.get('response_time_ms') or 2000)

    if not session_id or not item_id or not selected_option:
        return jsonify({'ok': False, 'error': 'session_id, item_id, and selected_option are required'}), 400

    try:
        from services.adaptive_tutor import AdaptiveTutorService
        tutor = AdaptiveTutorService()
        result = tutor.process_student_step(
            session_id=session_id,
            item_id=item_id,
            selected_option=selected_option,
            response_time_ms=response_time_ms,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error processing assistant step: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assistant/intervention', methods=['POST'])
@app.route('/api/workflow/assistance', methods=['POST'])
def api_assistant_intervention():
    """Requests on-demand pedagogical support: explain, worked_example, easier_step, inspect_prerequisites."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    intervention_type = data.get('intervention_type') or data.get('action')
    item_id = data.get('item_id')
    topic = data.get('topic')
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    selected_option = data.get('selected_option')

    if not intervention_type:
        return jsonify({'ok': False, 'error': 'intervention_type is required'}), 400

    try:
        from services.session_manager import handle_assistance_request
        result = handle_assistance_request(
            session_id=session_id,
            action=intervention_type,
            item_id=item_id,
            topic=topic,
            learner_id=learner_id,
            selected_option=selected_option,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error requesting intervention: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/exam/create', methods=['POST'])
def api_exam_create():
    """Creates a personalized, prerequisite-ordered day-by-day exam preparation schedule."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    exam_name = str(data.get('exam_name') or 'Upcoming AI/ML Exam').strip()
    exam_date = str(data.get('exam_date') or '').strip()
    daily_minutes = int(data.get('daily_minutes') or 45)
    syllabus_topics = data.get('syllabus_topics') or []

    try:
        from services.exam_planner import create_smart_exam_plan
        plan = create_smart_exam_plan(
            learner_id=learner_id,
            exam_name=exam_name,
            exam_date=exam_date,
            daily_minutes=daily_minutes,
            syllabus_topics=syllabus_topics,
        )
        return jsonify(plan), 200
    except Exception as e:
        app.logger.error(f"Error creating exam plan: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/exam/plan/<learner_id>', methods=['GET'])
def api_exam_plan_get(learner_id):
    """Retrieves active smart exam preparation plan with remaining days & progress."""
    try:
        from services.exam_planner import get_smart_exam_plan
        plan = get_smart_exam_plan(learner_id=learner_id)
        if plan:
            return jsonify({'ok': True, 'plan': plan}), 200
        else:
            return jsonify({'ok': False, 'plan': None, 'message': 'No active exam plan found'}), 200
    except Exception as e:
        app.logger.error(f"Error retrieving exam plan: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/exam/rebalance', methods=['POST'])
def api_exam_rebalance():
    """Dynamically rebalances remaining study days based on BKT performance & availability."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    plan_id = str(data.get('plan_id') or '').strip()
    new_daily_minutes = data.get('new_daily_minutes')

    if not plan_id:
        return jsonify({'ok': False, 'error': 'plan_id is required'}), 400

    try:
        from services.exam_planner import rebalance_exam_plan
        result = rebalance_exam_plan(
            learner_id=learner_id,
            plan_id=plan_id,
            new_daily_minutes=new_daily_minutes,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error rebalancing exam plan: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/exam/activity/complete', methods=['POST'])
def api_exam_activity_complete():
    """Marks a scheduled exam preparation activity as completed."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    plan_id = str(data.get('plan_id') or '').strip()
    activity_id = str(data.get('activity_id') or '').strip()
    score = data.get('score')

    if not plan_id or not activity_id:
        return jsonify({'ok': False, 'error': 'plan_id and activity_id are required'}), 400

    try:
        from services.exam_planner import complete_exam_activity
        result = complete_exam_activity(
            learner_id=learner_id,
            plan_id=plan_id,
            activity_id=activity_id,
            score=score,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error completing exam activity: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# =========================================================================
# DISTINCT WORKFLOW ENDPOINTS (Phase 2 & Phase 3)
# =========================================================================

@app.route('/api/workflow/continue/<learner_id>', methods=['GET'])
def api_workflow_continue(learner_id):
    """Workflow A: Continue Learning (Curriculum DAG frontier progression)."""
    try:
        from services.distinct_workflows import continue_learning
        result = continue_learning(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error in continue_learning workflow: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/weak-topics/<learner_id>', methods=['GET'])
def api_workflow_weak_topics(learner_id):
    """Workflow B: Improve My Weak Topics (Prerequisite repair & targeted remediation)."""
    try:
        from services.distinct_workflows import improve_weak_topics
        result = improve_weak_topics(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error in improve_weak_topics workflow: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/exam-prep/<learner_id>', methods=['GET'])
def api_workflow_exam_prep_get(learner_id):
    """Workflow C: Prepare for an Exam (Retrieve active schedule & today's task)."""
    try:
        from services.distinct_workflows import prepare_for_exam
        result = prepare_for_exam(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error retrieving exam prep workflow: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/exam-prep', methods=['POST'])
def api_workflow_exam_prep_post():
    """Workflow C: Prepare for an Exam (Configure new exam roadmap)."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    exam_date = data.get('exam_date')
    syllabus_topics = data.get('syllabus_topics')
    daily_minutes = int(data.get('daily_minutes') or 45)
    target_score_pct = int(data.get('target_score_pct') or 85)

    try:
        from services.distinct_workflows import prepare_for_exam
        result = prepare_for_exam(
            learner_id=learner_id,
            exam_date=exam_date,
            syllabus_topics=syllabus_topics,
            daily_minutes=daily_minutes,
            target_score_pct=target_score_pct,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error configuring exam prep workflow: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/revision/<learner_id>', methods=['GET'])
def api_workflow_revision(learner_id):
    """Workflow D: Revise Previous Topics (Spaced repetition & retrievability decay)."""
    try:
        from services.distinct_workflows import revise_previous_topics
        result = revise_previous_topics(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error in revise_previous_topics workflow: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/step', methods=['POST'])
def api_workflow_step():
    """Submits student's response within any of the 4 distinct workflows."""
    data = request.get_json(silent=True) or {}
    workflow_type = data.get('workflow_type', 'continue_learning')
    session_id = data.get('session_id')
    item_id = data.get('item_id')
    selected_option = data.get('selected_option')
    response_time_ms = int(data.get('response_time_ms') or 2000)

    if not session_id or not item_id or selected_option is None:
        return jsonify({'ok': False, 'error': 'session_id, item_id, and selected_option are required'}), 400

    try:
        from services.distinct_workflows import submit_workflow_step
        result = submit_workflow_step(
            workflow_type=workflow_type,
            session_id=session_id,
            item_id=item_id,
            selected_option=selected_option,
            response_time_ms=response_time_ms,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error submitting workflow step: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/session/<session_id>', methods=['GET'])
def api_workflow_session_get(session_id):
    """Retrieves or restores active session state across page refreshes."""
    try:
        from services.session_manager import get_unified_session
        sess, err = get_unified_session(session_id)
        if err:
            return jsonify(err), 400
        return jsonify({'ok': True, 'session': sess}), 200
    except Exception as e:
        app.logger.error(f"Error retrieving session {session_id}: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/mock-exam/start', methods=['POST'])
def api_workflow_mock_exam_start():
    """Initializes a timed multi-question Mock Exam Simulation for Workflow C."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    plan_id = data.get('plan_id')
    num_questions = int(data.get('num_questions') or 5)
    syllabus_topics = data.get('syllabus_topics')

    try:
        from services.distinct_workflows import start_mock_exam
        result = start_mock_exam(
            learner_id=learner_id,
            plan_id=plan_id,
            num_questions=num_questions,
            syllabus_topics=syllabus_topics,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error starting mock exam: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/mock-exam/submit', methods=['POST'])
def api_workflow_mock_exam_submit():
    """Scores and completes a timed Mock Exam submission."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    answers = data.get('answers') or {}

    if not session_id or not answers:
        return jsonify({'ok': False, 'error': 'session_id and answers dictionary are required'}), 400

    try:
        from services.distinct_workflows import submit_mock_exam
        result = submit_mock_exam(session_id=session_id, answers=answers)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error submitting mock exam: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/spaced-review/submit', methods=['POST'])
def api_workflow_spaced_review_submit():
    """Submits student's flashcard recall rating (lapse, hard, good, easy) and updates intervals."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    item_id = data.get('item_id')
    recall_rating = data.get('recall_rating') or 'good'

    if not session_id or not item_id:
        return jsonify({'ok': False, 'error': 'session_id and item_id are required'}), 400

    try:
        from services.distinct_workflows import submit_spaced_review
        result = submit_spaced_review(
            session_id=session_id,
            item_id=item_id,
            recall_rating=recall_rating,
        )
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error submitting spaced review: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500



@app.route('/api/rl/research-lab', methods=['GET'])
@app.route('/api/rl/research-lab/<learner_id>', methods=['GET'])
def api_rl_research_lab(learner_id='learner_default'):
    """RL Research Lab telemetry exposing Dueling Double DQN and LinUCB comparisons."""
    try:
        from services.distinct_workflows import get_rl_research_telemetry
        result = get_rl_research_telemetry(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error retrieving RL research telemetry: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/learner/intelligence', methods=['GET'])
@app.route('/api/learner/intelligence/<learner_id>', methods=['GET'])
def api_learner_intelligence(learner_id=None):
    """Shared Learner Intelligence Layer: 12-dimensional consolidated learner profile."""
    if not learner_id:
        learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.learner_intelligence import get_unified_learner_intelligence
        result = get_unified_learner_intelligence(learner_id=learner_id)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error retrieving learner intelligence: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/questions/quality-report', methods=['GET'])
def api_questions_quality_report():
    """Question Quality Validation Pipeline: 10-point audit and quality scoring."""
    try:
        from services.question_validator import audit_question_bank
        result = audit_question_bank()
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error executing question quality audit: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/rl/intelligence', methods=['GET'])
@app.route('/api/rl/intelligence/<learner_id>', methods=['GET'])
def api_rl_intelligence(learner_id=None):
    """
    Dedicated RL Intelligence Center telemetry:
    - Live Learner State
    - Recommendation Intelligence & Grounded Rationale
    - RL Policy Laboratory (Composite Adaptive vs Dueling DQN vs LinUCB)
    - Reward Analytics (Multi-objective reward breakdown)
    - Policy Benchmark Comparison
    - Policy Safety & Action Masking
    """
    if not learner_id:
        learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.distinct_workflows import get_rl_research_telemetry
        from services.learner_intelligence import get_unified_learner_intelligence
        base_telemetry = get_rl_research_telemetry(learner_id=learner_id)
        intel = get_unified_learner_intelligence(learner_id=learner_id)

        # Decompose multi-objective reward formulation
        reward_spec = {
            "formula": "R_t = R_mastery + R_info + R_match + R_penalty + R_invalid + R_step",
            "weights": {
                "w_mastery_gain": 10.0,
                "w_info_gain": 0.5,
                "w_challenge_match": 0.4,
                "w_failure_penalty": 0.8,
                "w_invalid_penalty": 2.0,
                "w_step_cost": 0.05,
            },
            "recent_sample_breakdown": {
                "r_mastery_gain": round(float(intel["knowledge_state"]["learning_velocity"]) * 10.0, 2),
                "r_info_gain": round(float(intel["assessment_performance"]["diagnostic_entropy_bits"]) * 0.5, 3),
                "r_challenge_match": 0.35,
                "r_failure_penalty": -0.8 if intel["recent_intervention_history"]["is_frustration_detected"] else 0.0,
                "r_step_cost": -0.05,
                "net_scalar_reward": round(
                    float(intel["knowledge_state"]["learning_velocity"]) * 10.0
                    + float(intel["assessment_performance"]["diagnostic_entropy_bits"]) * 0.5
                    + 0.35
                    - (0.8 if intel["recent_intervention_history"]["is_frustration_detected"] else 0.0)
                    - 0.05,
                    2
                ),
            },
        }

        # Policy Safety & Action Masking
        safety = {
            "production_policy": "Composite Adaptive Policy (BKT + Recovery Controller + LinUCB)",
            "experimental_policy": "Dueling Double DQN (99-dim observation, 52 discrete actions)",
            "experimental_status": "DISABLED_BY_DEFAULT",
            "shadow_evaluation_active": os.environ.get("KT_RL_SHADOW_MODE", "0") in ("1", "true"),
            "action_masking_enforced": True,
            "fallback_mechanism": "Difficulty Hysteresis Controller fallback on anomaly detection",
            "unsupported_actions_blocked": True,
        }

        return jsonify({
            "ok": True,
            "learner_id": learner_id,
            "live_learner_state": intel,
            "policy_laboratory": {
                "production": base_telemetry.get("production_policy"),
                "experimental": base_telemetry.get("experimental_dqn"),
                "contextual_bandit": base_telemetry.get("contextual_bandit"),
            },
            "reward_analytics": reward_spec,
            "benchmark_comparison": base_telemetry.get("policy_comparison_benchmark", []),
            "diagnostic_entropy": base_telemetry.get("diagnostic_entropy_sampling", []),
            "safety_and_invariants": safety,
        }), 200
    except Exception as e:
        app.logger.error(f"Error compiling RL intelligence: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/workflow/tutor/action', methods=['POST'])
def api_workflow_tutor_action():
    """Unified handler for all AI Tutor assistance actions."""
    return api_assistant_intervention()


# =========================================================================
# MULTI-METHOD KNOWLEDGE ASSESSMENT ENDPOINTS
# =========================================================================

@app.route('/api/assessment/diagnostic/<topic>', methods=['GET'])
def api_assessment_diagnostic_get(topic):
    """Method 1: Pre-topic Diagnostic Assessment with EIG optimization and prerequisite checks."""
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.multi_method_assessment import generate_diagnostic_assessment
        res = generate_diagnostic_assessment(topic=topic, learner_id=learner_id)
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error generating diagnostic assessment: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/diagnostic/submit', methods=['POST'])
def api_assessment_diagnostic_submit():
    """Evaluates diagnostic answers and calculates calibrated BKT prior."""
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    topic = str(data.get('topic') or 'python').strip()
    answers = data.get('answers') or {}
    try:
        from services.multi_method_assessment import evaluate_diagnostic_assessment
        res = evaluate_diagnostic_assessment(learner_id=learner_id, topic=topic, answers=answers)
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error evaluating diagnostic assessment: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/conceptual/evaluate', methods=['POST'])
def api_assessment_conceptual_evaluate():
    """Method 2: Conceptual Understanding Assessment with rubric scoring & misconception detection."""
    data = request.get_json(silent=True) or {}
    topic = str(data.get('topic') or 'python').strip()
    prompt = str(data.get('prompt') or '').strip()
    response_text = str(data.get('response') or '').strip()
    try:
        from services.multi_method_assessment import evaluate_conceptual_explanation
        res = evaluate_conceptual_explanation(topic=topic, prompt=prompt, student_response=response_text)
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error evaluating conceptual explanation: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/coding/challenges', methods=['GET'])
def api_assessment_coding_challenges():
    """Method 3: Returns available practical coding and debugging challenges."""
    topic = str(request.args.get('topic') or 'python').strip()
    try:
        from services.multi_method_assessment import CODING_CHALLENGES
        challenges = CODING_CHALLENGES.get(topic, CODING_CHALLENGES.get('python', []))
        return jsonify({'ok': True, 'topic': topic, 'challenges': challenges}), 200
    except Exception as e:
        app.logger.error(f"Error fetching coding challenges: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/coding/execute', methods=['POST'])
def api_assessment_coding_execute():
    """Method 3: Sandboxed isolated Python code execution against test cases."""
    data = request.get_json(silent=True) or {}
    code_str = data.get('code') or ''
    test_cases = data.get('test_cases') or []
    try:
        from services.multi_method_assessment import execute_sandboxed_code
        res = execute_sandboxed_code(code_str=code_str, test_cases=test_cases)
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error executing sandboxed code: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/concept-map/evaluate', methods=['POST'])
def api_assessment_concept_map_evaluate():
    """Method 4: Concept Mapping Assessment against Curriculum DAG."""
    data = request.get_json(silent=True) or {}
    edges = data.get('edges') or []
    try:
        from services.multi_method_assessment import evaluate_concept_map
        res = evaluate_concept_map(student_edges=edges)
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error evaluating concept map: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/confidence/calibrate', methods=['POST'])
def api_assessment_confidence_calibrate():
    """Method 6: Confidence Calibration & Brier Score Analysis."""
    data = request.get_json(silent=True) or {}
    history = data.get('history') or []
    try:
        from services.multi_method_assessment import calculate_confidence_calibration
        res = calculate_confidence_calibration(history=history)
        return jsonify({'ok': True, 'calibration': res}), 200
    except Exception as e:
        app.logger.error(f"Error calculating confidence calibration: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/assessment/project/evaluate', methods=['POST'])
def api_assessment_project_evaluate():
    """Method 8: Project-Based Assessment with rubric evaluation."""
    data = request.get_json(silent=True) or {}
    project_id = str(data.get('project_id') or 'proj_numpy_eda').strip()
    submission_text = str(data.get('submission') or '').strip()
    criterion_scores = data.get('criterion_scores')
    try:
        from services.multi_method_assessment import evaluate_project_submission
        res = evaluate_project_submission(
            project_id=project_id,
            submission_text=submission_text,
            scores_by_criterion=criterion_scores,
        )
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error evaluating project submission: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500






# =========================================================================
# PERSONALIZED STUDENT JOURNEY API ROUTES (STEPS 1 - 10)
# =========================================================================

@app.route('/api/journey/status', methods=['GET'])
def api_journey_status():
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.personalized_journey import SUBJECT_COURSES, get_weak_topics_priority
        from services.learning_store import get_latest_diagnostic_assessment, get_mock_examinations_for_learner

        latest_diag = get_latest_diagnostic_assessment(learner_id)
        mock_exams = get_mock_examinations_for_learner(learner_id)
        weak_data = get_weak_topics_priority(learner_id)

        # Determine current educational journey stage
        if not latest_diag:
            stage = "select_and_diagnostic"
            next_action = "Select a course track and take the initial diagnostic assessment."
        elif len(weak_data.get("weak_topics_ranked", [])) > 0:
            stage = "weak_topics"
            top_weak = weak_data["weak_topics_ranked"][0]["topic_title"]
            next_action = f"Focus on your highest priority weak topic: {top_weak}."
        elif len(mock_exams) == 0:
            stage = "mock_exam"
            next_action = "Create and complete your first personalized multi-method mock exam."
        else:
            stage = "progress"
            next_action = "Continue personalized curriculum advancement and spaced repetition."

        return jsonify({
            'ok': True,
            'learner_id': learner_id,
            'stage': stage,
            'next_action': next_action,
            'courses': SUBJECT_COURSES,
            'has_completed_diagnostic': latest_diag is not None,
            'latest_diagnostic': latest_diag,
            'weak_topics_count': len(weak_data.get("weak_topics_ranked", [])),
            'top_weak_topic': weak_data["weak_topics_ranked"][0] if weak_data.get("weak_topics_ranked") else None,
            'mock_exams_count': len(mock_exams),
            'latest_mock_exam': mock_exams[0] if mock_exams else None,
        }), 200
    except Exception as e:
        app.logger.error(f"Error in api_journey_status: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/diagnostic/start', methods=['POST'])
def api_journey_diagnostic_start():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    subject = str(data.get('subject') or 'ai_ml_core').strip()
    difficulty = str(data.get('difficulty') or 'adaptive').strip()
    selected_topics = data.get('selected_topics')
    num_questions = int(data.get('num_questions') or 10)

    try:
        from services.personalized_journey import start_initial_diagnostic
        res = start_initial_diagnostic(
            learner_id=learner_id,
            subject=subject,
            difficulty=difficulty,
            selected_topics=selected_topics,
            num_questions=num_questions,
        )
        session['diagnostic_id'] = res['diagnostic_id']
        session['learner_id'] = learner_id
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error starting initial diagnostic: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/diagnostic/submit', methods=['POST'])
def api_journey_diagnostic_submit():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    diagnostic_id = str(data.get('diagnostic_id') or session.get('diagnostic_id') or f"diag_{uuid.uuid4().hex[:12]}").strip()
    answers = data.get('answers') or {}
    response_times = data.get('response_times') or {}
    duration_seconds = int(data.get('duration_seconds') or 120)

    try:
        from services.personalized_journey import submit_initial_diagnostic
        res = submit_initial_diagnostic(
            learner_id=learner_id,
            diagnostic_id=diagnostic_id,
            answers=answers,
            response_times=response_times,
            duration_seconds=duration_seconds,
        )
        return jsonify(res), 200
    except Exception as e:
        app.logger.error(f"Error submitting initial diagnostic: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/report/latest', methods=['GET'])
def api_journey_report_latest():
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.learning_store import get_latest_diagnostic_assessment
        report = get_latest_diagnostic_assessment(learner_id)
        if not report:
            return jsonify({'ok': False, 'error': 'No diagnostic assessment found for this student.'}), 404
        return jsonify({'ok': True, 'report': report}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/weak-topics', methods=['GET'])
def api_journey_weak_topics():
    learner_id = str(request.args.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    try:
        from services.personalized_journey import get_weak_topics_priority
        res = get_weak_topics_priority(learner_id)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/topic-exam/generate', methods=['POST'])
def api_journey_topic_exam_generate():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    topic = str(data.get('topic') or 'linear_regression').strip()
    num_questions = int(data.get('num_questions') or 5)
    difficulty = int(data.get('difficulty') or 2)
    include_prereqs = bool(data.get('include_prereqs', True))

    try:
        from services.personalized_journey import generate_topic_targeted_exam
        res = generate_topic_targeted_exam(
            learner_id=learner_id,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            include_prereqs=include_prereqs,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/topic-exam/submit', methods=['POST'])
def api_journey_topic_exam_submit():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    exam_id = str(data.get('exam_id') or f"exam_{uuid.uuid4().hex[:12]}").strip()
    topic = str(data.get('topic') or 'linear_regression').strip()
    answers = data.get('answers') or {}
    duration_seconds = int(data.get('duration_seconds') or 180)

    try:
        from services.personalized_journey import submit_topic_targeted_exam
        res = submit_topic_targeted_exam(
            learner_id=learner_id,
            exam_id=exam_id,
            topic=topic,
            answers=answers,
            duration_seconds=duration_seconds,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/concept/<topic>', methods=['GET'])
def api_journey_concept(topic):
    try:
        from services.concept_teaching import get_full_concept_teaching
        res = get_full_concept_teaching(topic)
        return jsonify({'ok': True, 'topic': topic, 'concept': res}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/concept/mistake-analysis', methods=['POST'])
def api_journey_concept_mistake_analysis():
    data = request.get_json(silent=True) or {}
    item_id = str(data.get('item_id') or 'q_py_01').strip()
    submitted_answer = str(data.get('submitted_answer') or '').strip()
    topic = data.get('topic')

    try:
        from services.concept_teaching import analyze_student_mistake
        res = analyze_student_mistake(
            item_id=item_id,
            submitted_answer=submitted_answer,
            topic=topic,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/learning-method/record', methods=['POST'])
def api_journey_learning_method_record():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    topic = str(data.get('topic') or 'python').strip()
    method = str(data.get('method') or 'explanation').strip()
    user_input = data.get('user_input')
    duration_seconds = int(data.get('duration_seconds') or 60)

    try:
        from services.personalized_journey import record_learning_method_activity
        res = record_learning_method_activity(
            learner_id=learner_id,
            topic=topic,
            method=method,
            user_input=user_input,
            duration_seconds=duration_seconds,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/topic-evaluation/submit', methods=['POST'])
def api_journey_topic_evaluation_submit():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    topic = str(data.get('topic') or 'python').strip()
    method = str(data.get('method') or 'conceptual').strip()
    submission = data.get('submission')

    try:
        from services.personalized_journey import evaluate_topic_understanding_activity
        res = evaluate_topic_understanding_activity(
            learner_id=learner_id,
            topic=topic,
            method=method,
            submission=submission,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/mock-exam/generate', methods=['POST'])
def api_journey_mock_exam_generate():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    title = str(data.get('title') or 'Personalized AI/ML Multi-Method Mock Exam').strip()
    method = str(data.get('method') or 'mixed').strip()
    topics = data.get('topics')
    difficulty = int(data.get('difficulty') or 3)
    duration_minutes = int(data.get('duration_minutes') or 25)
    num_questions = int(data.get('num_questions') or 8)
    include_prereqs = bool(data.get('include_prereqs', True))

    try:
        from services.personalized_journey import generate_personalized_mock_exam
        res = generate_personalized_mock_exam(
            learner_id=learner_id,
            title=title,
            method=method,
            topics=topics,
            difficulty=difficulty,
            duration_minutes=duration_minutes,
            num_questions=num_questions,
            include_prereqs=include_prereqs,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/journey/mock-exam/submit', methods=['POST'])
def api_journey_mock_exam_submit():
    data = request.get_json(silent=True) or {}
    learner_id = str(data.get('learner_id') or session.get('learner_id') or 'learner_default').strip()
    exam_id = str(data.get('exam_id') or f"mock_{uuid.uuid4().hex[:12]}").strip()
    answers = data.get('answers') or {}
    duration_seconds = int(data.get('duration_seconds') or 600)

    try:
        from services.personalized_journey import submit_personalized_mock_exam
        res = submit_personalized_mock_exam(
            learner_id=learner_id,
            exam_id=exam_id,
            answers=answers,
            duration_seconds=duration_seconds,
        )
        return jsonify(res), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
