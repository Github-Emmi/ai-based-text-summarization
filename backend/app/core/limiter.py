"""slowapi rate-limiter singleton.

Import `limiter` wherever you need to apply rate limits:

    from app.core.limiter import limiter

    @router.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request, ...):
        ...

Wire into the app in create_app() (done in main.py):

    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Note: every route that uses @limiter.limit() MUST include `request: Request`
as a plain function parameter (not a Depends) — slowapi reads it directly.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
