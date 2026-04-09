from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic

from app.core.config import settings
from app.core.exceptions import LMSException

_WINDOW_SECONDS = 60.0
_request_times: deque[float] = deque()
_request_lock = Lock()


def acquire_groq_slot() -> None:
    max_requests = max(1, settings.groq_max_requests_per_minute)
    now = monotonic()
    with _request_lock:
        while _request_times and (now - _request_times[0]) > _WINDOW_SECONDS:
            _request_times.popleft()
        if len(_request_times) >= max_requests:
            raise LMSException(
                status_code=429,
                detail=f"Groq quota protection active: limit {max_requests}/minute reached. Please retry in a few seconds.",
            )
        _request_times.append(now)
