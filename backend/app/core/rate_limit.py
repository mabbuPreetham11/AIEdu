from slowapi import Limiter

from app.core.config import settings

limiter = Limiter(
    key_func=lambda request: request.client.host if request.client else "anonymous",
    default_limits=[settings.rate_limit],
)
