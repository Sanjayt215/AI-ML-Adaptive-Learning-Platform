from __future__ import annotations

import os
from typing import List, Dict

import requests

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'


def youtube_api_available() -> bool:
    return bool(os.getenv('YOUTUBE_API_KEY'))


def search_youtube_videos(query: str, max_results: int = 6, level: str | None = None) -> List[Dict]:
    """Return curated live YouTube search results if API key exists, else empty list.
    Uses search.list followed by videos.list to get duration and statistics.
    """
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or not query.strip():
        return []

    full_query = query.strip()
    if level:
        full_query += f' {level} tutorial machine learning'

    try:
        search_resp = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                'part': 'snippet',
                'q': full_query,
                'type': 'video',
                'maxResults': max_results,
                'videoEmbeddable': 'true',
                'safeSearch': 'strict',
                'key': api_key,
            },
            timeout=15,
        )
        search_resp.raise_for_status()
        items = search_resp.json().get('items', [])
        video_ids = [item['id']['videoId'] for item in items if item.get('id', {}).get('videoId')]
        stats = {}
        if video_ids:
            video_resp = requests.get(
                YOUTUBE_VIDEOS_URL,
                params={
                    'part': 'contentDetails,statistics',
                    'id': ','.join(video_ids),
                    'key': api_key,
                },
                timeout=15,
            )
            video_resp.raise_for_status()
            for item in video_resp.json().get('items', []):
                stats[item['id']] = {
                    'duration': item.get('contentDetails', {}).get('duration'),
                    'viewCount': item.get('statistics', {}).get('viewCount'),
                }

        results = []
        for item in items:
            vid = item.get('id', {}).get('videoId')
            if not vid:
                continue
            snippet = item.get('snippet', {})
            meta = stats.get(vid, {})
            results.append(
                {
                    'title': snippet.get('title', 'Untitled Video'),
                    'channel': snippet.get('channelTitle', 'Unknown Channel'),
                    'url': f'https://www.youtube.com/watch?v={vid}',
                    'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url'),
                    'published_at': snippet.get('publishedAt'),
                    'description': snippet.get('description', ''),
                    'duration': meta.get('duration'),
                    'viewCount': meta.get('viewCount'),
                    'source': 'youtube_api',
                }
            )
        return results
    except Exception:
        return []
