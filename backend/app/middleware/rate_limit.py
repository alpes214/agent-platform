import logging
import time
from collections import defaultdict, deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger(__name__)

_HEADER_NAME = b'x-internal-secret'

# Per-path-class request budgets. /ask is expensive (LLM tokens), give it a
# tight bucket; everything else is cheap (read endpoints, DB lookups).
_BUDGETS: dict[str, tuple[int, float]] = {
    'ask': (60, 60.0),    # 60 requests per 60s
    'other': (600, 60.0),  # 600 requests per 60s
}


def _budget_for(path: str) -> tuple[int, float]:
    if path == '/ask':
        return _BUDGETS['ask']
    return _BUDGETS['other']


class RateLimitMiddleware:
    """Pure-ASGI in-memory token-bucket rate limit.

    Keyed by source IP. Bypassed when the request carries a valid
    X-Internal-Secret (BFF is trusted; rate-limiting per browser client
    happens at the BFF layer instead — deferred to a later phase).

    Bucket state is per-process (no Redis), which is fine here because the
    server runs one fastapi container with one uvicorn worker. If we ever
    scale to multiple workers this needs to move to Redis or a shared store.
    """

    def __init__(self, app: ASGIApp, secret: str) -> None:
        self._app = app
        self._secret = secret.encode() if secret else b''
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] != 'http':
            await self._app(scope, receive, send)
            return

        # BFF bypass — valid internal secret skips the bucket entirely.
        if self._secret:
            for name, value in scope['headers']:
                if name == _HEADER_NAME and value == self._secret:
                    await self._app(scope, receive, send)
                    return

        path = scope['path']
        client_ip = scope['client'][0] if scope.get('client') else 'unknown'
        max_requests, window = _budget_for(path)
        bucket_key = (client_ip, 'ask' if path == '/ask' else 'other')
        bucket = self._buckets[bucket_key]

        now = time.monotonic()
        # Evict timestamps outside the window.
        while bucket and now - bucket[0] >= window:
            bucket.popleft()

        if len(bucket) >= max_requests:
            retry_after = max(1, int(window - (now - bucket[0])))
            log.warning(
                'rate-limit reject path=%s remote=%s bucket=%d/%d',
                path,
                client_ip,
                len(bucket),
                max_requests,
            )
            response = JSONResponse(
                status_code=429,
                content={
                    'detail': 'rate limit exceeded',
                    'retry_after_seconds': retry_after,
                },
                headers={'retry-after': str(retry_after)},
            )
            await response(scope, receive, send)
            return

        bucket.append(now)
        await self._app(scope, receive, send)
