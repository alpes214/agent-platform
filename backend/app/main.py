import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api import ask, docs, search, transcribe
from backend.app.config import settings
from backend.app.db.postgres import close_postgres, init_postgres
from backend.app.db.postgres import status as pg_status
from backend.app.embeddings import tei_client
from backend.app.logging_conf import configure_logging
from backend.app.middleware.correlation import CorrelationIdMiddleware
from backend.app.middleware.internal_secret import InternalSecretMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.queue.app import app as procrastinate_app

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    settings.staging_dir.mkdir(parents=True, exist_ok=True)
    await init_postgres()
    await procrastinate_app.open_async()
    log.info('knowledge-search started')
    try:
        yield
    finally:
        await procrastinate_app.close_async()
        await tei_client.close()
        await close_postgres()
        log.info('knowledge-search stopped')


app = FastAPI(
    title='Knowledge Search',
    lifespan=lifespan,
    docs_url='/api-docs',
    redoc_url='/api-redoc',
)
# Middleware ordering: Starlette executes middlewares in REVERSE add-order.
# Source order below (top to bottom) is INNERMOST to OUTERMOST, so execution
# at request time is OUTERMOST to INNERMOST:
#   CorrelationId  → tags every log line in the request with a request_id
#   RateLimit      → token-bucket per source IP (bypassed by valid secret)
#   InternalSecret → gates non-exempt paths on the shared header
#   <handler>
#
# CORS middleware removed in Phase 7 step 11: the browser is now same-origin
# with the BFF, so cross-origin handshakes are not part of the request path.
app.add_middleware(
    InternalSecretMiddleware,
    secret=settings.internal_secret,
    enforce=settings.enforce_internal_secret,
)
app.add_middleware(RateLimitMiddleware, secret=settings.internal_secret)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(docs.router)
app.include_router(search.router)
app.include_router(ask.router)
app.include_router(transcribe.router)


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok', 'postgres': pg_status()}
