import threading
import time
import os
import json
from typing import Any, Optional

# Try Redis; gracefully fall back to in-memory cache if unavailable
# DESABILITADO: Redis causando timeout na inicialização
# Usando cache em memória apenas
_redis_client = None
_REDIS_PREFIX = os.getenv('REDIS_PREFIX', 'ippel:')


def _rkey(key: str) -> str:
    return f"{_REDIS_PREFIX}q:{key}"


# In-memory fallback store
query_cache: dict[str, dict[str, Any]] = {}
cache_lock = threading.Lock()


def cache_query(key: str, data: Any, ttl: int = 300) -> None:
    # Prefer Redis
    if _redis_client is not None:
        try:
            _redis_client.set(_rkey(key), json.dumps(data, ensure_ascii=False), ex=int(ttl))
            return
        except Exception:
            # Fallback to memory on any Redis error
            pass
    # Fallback: in-memory with TTL metadata
    with cache_lock:
        query_cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': int(ttl),
        }


def get_cached_query(key: str) -> Optional[Any]:
    # Prefer Redis
    if _redis_client is not None:
        try:
            raw = _redis_client.get(_rkey(key))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            # On Redis issue, fall back to memory
            pass
    # Fallback: in-memory with expiry check
    with cache_lock:
        entry = query_cache.get(key)
        if not entry:
            return None
        if time.time() - entry['timestamp'] < entry['ttl']:
            return entry['data']
        # expired
        query_cache.pop(key, None)
        return None


def clear_expired_cache() -> None:
    # Redis handles expiry itself; only prune in-memory fallback
    now = time.time()
    with cache_lock:
        expired = [k for k, v in query_cache.items() if now - v['timestamp'] > v['ttl']]
        for k in expired:
            query_cache.pop(k, None)


def clear_rnc_cache(user_id: int | None = None) -> None:
    pattern = 'rncs_list_*' if user_id is None else f'rncs_list_{user_id}_*'
    if _redis_client is not None:
        try:
            full_pat = _rkey(pattern)
            # Use SCAN to avoid blocking
            to_del = []
            for k in _redis_client.scan_iter(match=full_pat, count=500):
                to_del.append(k)
                if len(to_del) >= 1000:
                    _redis_client.delete(*to_del)
                    to_del.clear()
            if to_del:
                _redis_client.delete(*to_del)
        except Exception:
            # ignore and fall back to in-memory clearing
            pass
    # Always clear in-memory fallback too
    with cache_lock:
        keys = list(query_cache.keys())
        for k in keys:
            if not k.startswith('rncs_list_'):
                continue
            if user_id is None or f"rncs_list_{user_id}_" in k:
                query_cache.pop(k, None)


def redis_enabled() -> bool:
    return _redis_client is not None
