from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TOPIC_ALIASES = {
    "nlp": [
        "nlp", "natural language processing", "text processing", "text classification",
        "sentiment analysis", "tokenization", "stemming", "lemmatization", "spacy", "nltk",
        "transformers", "language model", "bag of words", "tfidf", "tf-idf"
    ],
    "llm": [
        "llm", "large language model", "chatgpt", "gpt", "language model", "ai", "artificial intelligence"
    ],
    "model deployment": [
        "model deployment", "deployment", "ml deployment", "api serving", "model serving",
        "flask deployment", "fastapi", "docker", "containerization", "mlops", "inference api",
        "serving", "endpoint", "deploy"
    ],
    "classification": ["classification", "logistic regression", "binary classification", "multiclass"],
    "linear regression": ["linear regression", "regression", "ridge", "lasso", "elasticnet"],
    "decision trees": ["decision trees", "decision tree", "random forest", "xgboost", "tree"],
    "naive bayes": ["naive bayes", "bayes", "spam filtering"],
    "neural networks": ["neural networks", "deep learning", "backpropagation", "ann", "mlp"],
}

LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _normalize_text(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9+\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return set(_normalize_text(text).split())


def _canonical_topic(topic: str) -> str:
    topic = _normalize_text(topic)
    for canonical, aliases in TOPIC_ALIASES.items():
        if topic == canonical or topic in aliases:
            return canonical
        if topic and any(topic in alias or alias in topic for alias in aliases):
            return canonical
    return topic


def _topic_terms(topic: str) -> set[str]:
    canonical = _canonical_topic(topic)
    aliases = TOPIC_ALIASES.get(canonical, [canonical])
    terms = set()
    for alias in aliases:
        terms |= _tokens(alias)
    return terms


def _level_score(item_level: str, requested_level: str) -> float:
    a = LEVEL_ORDER.get(_normalize_text(item_level), 0)
    b = LEVEL_ORDER.get(_normalize_text(requested_level), 0)
    gap = abs(a - b)
    return {0: 1.0, 1: 0.7, 2: 0.35}.get(gap, 0.2)


def _relevance_score(topic: str, item_text: str) -> float:
    q_terms = _topic_terms(topic)
    i_terms = _tokens(item_text)
    if not q_terms or not i_terms:
        return 0.0
    overlap = len(q_terms & i_terms) / max(len(q_terms), 1)
    exact_bonus = 0.5 if _canonical_topic(topic) in _normalize_text(item_text) else 0.0

    item_norm = _normalize_text(item_text)
    penalties = 0.0
    # Softer penalties - avoid filtering out valid but tangential content
    if _canonical_topic(topic) == "nlp" and any(bad in item_norm for bad in ["k means", "linear regression"]):
        penalties += 0.2
    if _canonical_topic(topic) == "model deployment" and any(bad in item_norm for bad in ["backpropagation", "ridge", "lasso"]):
        penalties += 0.15

    return max(0.0, overlap + exact_bonus - penalties)


@lru_cache(maxsize=1)
def _load_csvs() -> dict[str, pd.DataFrame]:
    return {
        "videos": pd.read_csv(DATA_DIR / "youtube_videos_catalog.csv"),
        "courses": pd.read_csv(DATA_DIR / "online_courses_catalog.csv"),
        "datasets": pd.read_csv(DATA_DIR / "kaggle_datasets_catalog.csv"),
        "projects": pd.read_csv(DATA_DIR / "mini_projects_catalog.csv"),
    }


def _safe_col(df: pd.DataFrame, col: str, default):
    if col not in df.columns:
        df[col] = default
    return df[col]


def _score_frame(
    df: pd.DataFrame,
    topic: str,
    level: str,
    text_cols: Iterable[str],
    quality_col: str | None = None,
    fallback_level_col: str | None = None,
) -> pd.DataFrame:
    work = df.copy()

    for col in text_cols:
        _safe_col(work, col, "")
    _safe_col(work, "topic", "")

    if "level" not in work.columns:
        if fallback_level_col and fallback_level_col in work.columns:
            work["level"] = work[fallback_level_col].fillna("beginner")
        else:
            work["level"] = "beginner"

    joined = work[list(text_cols)].fillna("").astype(str).agg(" ".join, axis=1)
    work["_text"] = joined
    work["_relevance"] = work.apply(
        lambda r: max(
            _relevance_score(topic, r["_text"]),
            1.4 if _canonical_topic(topic) == _canonical_topic(r.get("topic", "")) else 0.0,
        ),
        axis=1,
    )
    work["_level"] = work["level"].fillna("beginner").map(lambda x: _level_score(str(x), level))
    work["_quality"] = 1.0

    if quality_col and quality_col in work.columns:
        numeric_quality = pd.to_numeric(work[quality_col], errors="coerce").fillna(0.0)
        mx = max(float(numeric_quality.max()), 1.0)
        work["_quality"] = numeric_quality / mx

    work["_score"] = work["_relevance"] * 0.65 + work["_level"] * 0.2 + work["_quality"] * 0.15
    work = work[work["_relevance"] >= 0.5]
    return work.sort_values(["_score"], ascending=False)


def filter_options(topic: str, level: str) -> dict:
    return {
        "canonical_topic": _canonical_topic(topic),
        "requested_level": _normalize_text(level),
    }


def rank_catalog_videos(topic: str, level: str, max_results: int = 6) -> list[dict]:
    videos = _load_csvs()["videos"]
    quality_col = "quality_score" if "quality_score" in videos.columns else ("relevance_score" if "relevance_score" in videos.columns else None)
    ranked = _score_frame(videos, topic, level, ["topic", "title", "channel"], quality_col=quality_col)

    rename_map = {}
    if "published_year" in ranked.columns and "year" not in ranked.columns:
        rename_map["published_year"] = "year"
    ranked = ranked.rename(columns=rename_map)

    cols = ["topic", "level", "title", "channel", "url", "duration_minutes", "views", "likes", "year", "dataset_source"]
    for c in cols:
        _safe_col(ranked, c, None)
    result = ranked[cols].head(max_results).to_dict(orient="records")
    # Ensure level is always present and sanitize NaN values
    for item in result:
        item.setdefault("level", "beginner")
        # Convert NaN/None to null for JSON compatibility
        for key in ["year", "views", "likes", "duration_minutes"]:
            if key in item:
                val = item[key]
                # Check for NaN, None, or other invalid values
                if val is None or (isinstance(val, float) and (val != val)):  # NaN check
                    item[key] = None
                else:
                    try:
                        item[key] = int(val) if isinstance(val, float) else val
                    except (ValueError, TypeError):
                        item[key] = None
    return result


def rank_courses(topic: str, level: str, provider: str = "all", max_results: int = 6) -> list[dict]:
    courses = _load_csvs()["courses"]
    if provider and provider != "all" and "platform" in courses.columns:
        courses = courses[courses["platform"].fillna("").str.lower() == provider.lower()]
    ranked = _score_frame(courses, topic, level, ["topic", "title", "platform"], quality_col="rating")
    cols = ["topic", "platform", "title", "level", "duration_hours", "rating", "learners", "certificate", "verified", "url", "language", "dataset_source"]
    for c in cols:
        _safe_col(ranked, c, None)
    result = ranked[cols].head(max_results).to_dict(orient="records")
    # Normalize platform -> provider for frontend consistency
    for item in result:
        if "platform" in item and "provider" not in item:
            item["provider"] = item.pop("platform")
        item.setdefault("provider", "Unknown")
        item.setdefault("level", "beginner")
    return result


def rank_kaggle_datasets(topic: str, level: str, max_results: int = 4) -> list[dict]:
    datasets = _load_csvs()["datasets"]
    ranked = _score_frame(datasets, topic, level, ["topic", "title", "description", "source"])
    cols = ["topic", "source", "title", "level", "url", "description"]
    for c in cols:
        _safe_col(ranked, c, None)
    result = ranked[cols].head(max_results).to_dict(orient="records")
    # Ensure level is always present
    for item in result:
        item.setdefault("level", "beginner")
    return result


def project_for_topic(topic: str, level: str) -> str | None:
    projects = _load_csvs()["projects"]
    ranked = _score_frame(projects, topic, level, ["topic", "project"], quality_col=None, fallback_level_col="difficulty")
    if ranked.empty:
        return None
    row = ranked.iloc[0]
    # Return project string directly, not a dict
    return str(row.get("project", "Practice a small project on this topic.")).strip()


def rank_live_and_dataset_videos(topic: str, level: str, live_videos: list[dict], max_results: int = 8) -> list[dict]:
    dataset_ranked = rank_catalog_videos(topic, level, max_results=max_results)
    merged = []
    seen = set()

    for item in live_videos or []:
        title = item.get("title", "")
        score = _relevance_score(topic, f"{title} {item.get('channel', '')}")
        if score < 0.5:
            continue
        row = dict(item)
        row.setdefault("dataset_source", "youtube_live_api")
        key = row.get("url") or title
        if key not in seen:
            seen.add(key)
            merged.append(row)

    for item in dataset_ranked:
        key = item.get("url") or item.get("title")
        if key not in seen:
            seen.add(key)
            merged.append(item)
        if len(merged) >= max_results:
            break

    return merged[:max_results]
