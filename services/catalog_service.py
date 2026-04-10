from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import log10
from pathlib import Path
from typing import Dict, List

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'

LEVEL_WEIGHT = {'beginner': 1.0, 'intermediate': 1.2, 'advanced': 1.35}


@lru_cache(maxsize=1)
def load_video_catalog() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / 'youtube_videos_catalog.csv')


@lru_cache(maxsize=1)
def load_course_catalog() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / 'online_courses_catalog.csv')
    for col in ['certificate', 'verified']:
        df[col] = df[col].astype(str).str.lower().isin(['true', '1', 'yes'])
    return df


@lru_cache(maxsize=1)
def load_kaggle_catalog() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / 'kaggle_datasets_catalog.csv')


@lru_cache(maxsize=1)
def load_project_catalog() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / 'mini_projects_catalog.csv')



def _topic_similarity(candidate_topic: str, requested_topic: str) -> float:
    a = set(str(candidate_topic).lower().split())
    b = set(str(requested_topic).lower().split())
    if str(candidate_topic).lower() == str(requested_topic).lower():
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)



def rank_catalog_videos(topic: str, level: str, max_results: int = 6) -> List[Dict]:
    df = load_video_catalog().copy()
    df['topic_similarity'] = df['topic'].apply(lambda x: _topic_similarity(x, topic))
    df['level_match'] = (df['level'].str.lower() == level.lower()).astype(float)
    df['score'] = (
        df['quality_score'].astype(float) * 0.42
        + df['topic_similarity'] * 3.2
        + df['level_match'] * 1.8
        + df['views'].apply(lambda x: min(log10(max(float(x), 1.0)), 8.0)) * 0.35
        + (df['published_year'].astype(float) - 2018).clip(lower=0) * 0.08
    )
    df = df.sort_values(['score', 'views', 'quality_score'], ascending=False)
    rows = df.head(max_results).to_dict(orient='records')
    return [
        {
            'title': r['title'],
            'channel': r['channel'],
            'url': r['url'],
            'viewCount': int(r['views']),
            'duration': f"{int(r['duration_minutes'])} min",
            'published_at': f"{int(r['published_year'])}-01-01T00:00:00Z",
            'source': 'youtube_dataset_csv',
            'rank_score': round(float(r['score']), 3),
        }
        for r in rows
    ]



def rank_live_and_dataset_videos(topic: str, level: str, live_videos: List[Dict], max_results: int = 8) -> List[Dict]:
    dataset_videos = rank_catalog_videos(topic, level, max_results=max_results)
    combined = []
    seen = set()

    def score_live(video: Dict) -> float:
        title = str(video.get('title', ''))
        channel = str(video.get('channel', ''))
        views = float(video.get('viewCount') or 0)
        recency_bonus = 0.6 if str(video.get('published_at', ''))[:4] in {'2025', '2026', '2024'} else 0.25
        level_bonus = 0.8 if level.lower() in title.lower() else 0.2
        topic_bonus = 1.8 if topic.lower() in title.lower() else 0.9
        return topic_bonus + level_bonus + recency_bonus + min(log10(max(views, 1.0)), 8.0) * 0.3 + (0.2 if 'tutorial' in title.lower() else 0)

    for item in live_videos:
        key = item.get('url')
        if key and key not in seen:
            item = dict(item)
            item['rank_score'] = round(score_live(item), 3)
            combined.append(item)
            seen.add(key)
    for item in dataset_videos:
        key = item.get('url')
        if key and key not in seen:
            combined.append(item)
            seen.add(key)

    combined.sort(key=lambda x: float(x.get('rank_score', 0)), reverse=True)
    return combined[:max_results]



def rank_courses(topic: str, level: str, provider: str = 'all', max_results: int = 6) -> List[Dict]:
    df = load_course_catalog().copy()
    if provider != 'all':
        df = df[df['platform'].str.lower() == provider.lower()]
    df['topic_similarity'] = df['topic'].apply(lambda x: _topic_similarity(x, topic))
    df['level_match'] = (df['level'].str.lower() == level.lower()).astype(float)
    df['score'] = (
        df['topic_similarity'] * 3.0
        + df['level_match'] * 1.8
        + df['rating'].astype(float) * 0.85
        + df['learners'].apply(lambda x: min(log10(max(float(x), 1.0)), 7.0)) * 0.45
        + df['certificate'].astype(int) * 0.5
        + df['verified'].astype(int) * 0.45
    )
    df = df.sort_values(['score', 'rating', 'learners'], ascending=False)
    rows = df.head(max_results).to_dict(orient='records')
    results = []
    for r in rows:
        results.append(
            {
                'title': r['title'],
                'provider': r['platform'],
                'url': r['url'],
                'certificate': bool(r['certificate']),
                'verified': bool(r['verified']),
                'rating': float(r['rating']),
                'learners': int(r['learners']),
                'duration_hours': int(r['duration_hours']),
                'level': r['level'],
                'source': r['dataset_source'],
                'rank_score': round(float(r['score']), 3),
            }
        )
    return results



def rank_kaggle_datasets(topic: str, level: str = 'beginner', max_results: int = 4) -> List[Dict]:
    df = load_kaggle_catalog().copy()
    df['topic_similarity'] = df['topic'].apply(lambda x: _topic_similarity(x, topic))
    df['level_match'] = (df['level'].str.lower() == level.lower()).astype(float)
    df['score'] = df['topic_similarity'] * 3 + df['level_match'] * 1.4
    df = df.sort_values(['score', 'title'], ascending=[False, True])
    return df.head(max_results).to_dict(orient='records')



def project_for_topic(topic: str, level: str) -> str:
    df = load_project_catalog().copy()
    df['topic_similarity'] = df['topic'].apply(lambda x: _topic_similarity(x, topic))
    df['difficulty_weight'] = df['difficulty'].str.lower().map(LEVEL_WEIGHT).fillna(1.0)
    target_weight = LEVEL_WEIGHT.get(level.lower(), 1.0)
    df['difficulty_gap'] = (df['difficulty_weight'] - target_weight).abs()
    df['score'] = df['topic_similarity'] * 3 - df['difficulty_gap']
    row = df.sort_values(['score'], ascending=False).iloc[0]
    return str(row['project'])



def filter_options() -> Dict[str, List[str]]:
    courses = load_course_catalog()
    return {
        'providers': ['all'] + sorted(courses['platform'].dropna().unique().tolist()),
        'levels': ['all', 'beginner', 'intermediate', 'advanced'],
        'video_modes': ['hybrid', 'live', 'dataset'],
    }
