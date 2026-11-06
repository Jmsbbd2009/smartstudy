import threading
import time
from collections import defaultdict
from fastapi import HTTPException, Request
import redis
from app.core.config import settings

_lock = threading.Lock()
_local = defaultdict(list)
client = redis.Redis.from_url(settings.redis_url) if settings.redis_url else None
_script = (
    "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"
)


def limit(key, maximum=20, seconds=60):
    if client:
        try:
            count = int(client.eval(_script, 1, "limit:" + key, seconds))
        except redis.RedisError:
            raise HTTPException(503, "Rate limiter temporarily unavailable")
        if count > maximum:
            raise HTTPException(429, "Too many requests", headers={"Retry-After": str(seconds)})
    else:
        with _lock:
            current = time.monotonic()
            values = [v for v in _local[key] if current - v < seconds]
            if len(values) >= maximum:
                raise HTTPException(429, "Too many requests", headers={"Retry-After": str(seconds)})
            _local[key] = values + [current]


def auth_limit(request: Request):
    # Trust only the connected peer; reverse proxy must not supply arbitrary forwarded identities.
    limit("auth:" + (request.client.host if request.client else "unknown"), 30, 60)
