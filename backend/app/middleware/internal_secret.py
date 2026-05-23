import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger(__name__)

_HEADER_NAME = b'x-internal-secret'

# Paths that bypass the secret check. Liveness probes (/health) must stay
# unauth'd so external monitors and Docker healthchecks keep working;
# OpenAPI docs are local-debug surface that nobody but a developer hits.
_EXEMPT_PATHS = frozenset({
    '/health',
    '/openapi.json',
    '/api-docs',
    '/api-redoc',
})


class InternalSecretMiddleware:
    """Pure-ASGI middleware that gates requests on a shared secret header.

    Pure ASGI (rather than `BaseHTTPMiddleware`) so it doesn't interfere with
    streaming responses — important for the SSE `/ask` endpoint.
    """

    def __init__(self, app: ASGIApp, secret: str, enforce: bool) -> None:
        self._app = app
        self._secret = secret.encode() if secret else b''
        self._enforce = enforce

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] != 'http':
            await self._app(scope, receive, send)
            return

        path = scope['path']
        if path in _EXEMPT_PATHS or not self._secret:
            await self._app(scope, receive, send)
            return

        provided: bytes | None = None
        for name, value in scope['headers']:
            if name == _HEADER_NAME:
                provided = value
                break

        if provided == self._secret:
            await self._app(scope, receive, send)
            return

        client_host = scope['client'][0] if scope.get('client') else '?'
        if self._enforce:
            log.warning(
                'internal-secret reject path=%s remote=%s', path, client_host
            )
            response = JSONResponse(
                status_code=403,
                content={'detail': 'missing or invalid internal secret'},
            )
            await response(scope, receive, send)
            return

        log.warning(
            'internal-secret missing (warn-only) path=%s remote=%s',
            path,
            client_host,
        )

        async def send_with_warn_header(message: Message) -> None:
            # On the response-start, append a header signaling the request
            # was waved through during warn-only mode so debugging is obvious.
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append(
                    (b'x-internal-secret-warning', b'missing-or-invalid')
                )
                message['headers'] = headers
            await send(message)

        await self._app(scope, receive, send_with_warn_header)
