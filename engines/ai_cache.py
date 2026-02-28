# engines/ai_cache.py
#
# Simple in-memory + file cache for AI responses.
# The Inference API free tier has rate limits (~30k tokens/month on free).
# Caching ensures the same plan doesn't trigger two identical API calls
# if the user refreshes the page.
#
# Cache keys are based on a hash of the input data.
# Cache TTL: 24 hours (one per day per plan is sufficient).

import json
import hashlib
import os
from datetime import datetime, timedelta

CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_cache.json')

def _load_cache() -> dict:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_cache(cache: dict):
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

def _make_key(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()

def get_cached(data: dict) -> str | None:
    """Returns cached response if it exists and is less than 24 hours old."""
    cache = _load_cache()
    key   = _make_key(data)
    entry = cache.get(key)

    if not entry:
        return None

    cached_at = datetime.fromisoformat(entry['cached_at'])
    if datetime.now() - cached_at > timedelta(hours=24):
        return None

    return entry['response']

def set_cached(data: dict, response: str):
    """Stores a response in the cache with a timestamp."""
    cache = _load_cache()
    key   = _make_key(data)
    cache[key] = {
        "response":  response,
        "cached_at": datetime.now().isoformat()
    }
    _save_cache(cache)

def clear_cache():
    """Wipes the entire cache. Called from UI if user wants fresh responses."""
    if os.path.exists(CACHE_PATH):
        os.remove(CACHE_PATH)
