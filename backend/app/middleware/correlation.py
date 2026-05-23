import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.logging_conf import request_id_var

_HEADER_NAME = b'x-request-id'
_HEADER_NAME_STR = 'x-request-id'


class CorrelationIdMiddleware:
    """Pure-ASGI middleware that propagates an end-to-end request id.

    - Reads X-Request-Id from the incoming request; generates one if missing.
    - Stores it on a contextvar so every log line in the same request is
      tagged with that id (see backend/app/logging_conf.py).
    - Emits the same id back as the X-Request-Id response header so the
      Next.js BFF (and curl during debugging) can correlate a browser
      request to a server log line by id.

    If the BFF (or an OTel auto-instrumentor) is already setting traceparent,
    callers should still get a stable correlation id — we just generate one
    if the request didn't carry an explicit X-Request-Id.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] != 'http':
            await self._app(scope, receive, send)
            return

        request_id: str | None = None
        for name, value in scope['headers']:
            if name == _HEADER_NAME:
                request_id = value.decode('latin-1')
                break
        if not request_id:
            request_id = uuid.uuid4().hex

        token = request_id_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                # Don't duplicate if upstream already set it.
                already_set = any(name == _HEADER_NAME for name, _ in headers)
                if not already_set:
                    headers.append(
                        (_HEADER_NAME, request_id.encode('latin-1'))
                    )
                message['headers'] = headers
            await send(message)

        try:
            await self._app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)
