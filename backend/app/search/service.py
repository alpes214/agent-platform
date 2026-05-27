import logging
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.embeddings import voyage_client
from backend.app.repos.docs import ChunkResult, vector_search

log = logging.getLogger(__name__)


async def search_chunks(
    session: AsyncSession,
    query: str,
    *,
    k: int,
    doc_ids: list[UUID] | None = None,
) -> list[ChunkResult]:
    start = time.monotonic()

    query_vec = await _embed_query(query)
    candidates = await _retrieve(
        session, query_vec, k=k * settings.search_oversample_factor, doc_ids=doc_ids
    )
    ranked = _rank(candidates, query)
    kept, dropped_count, top_dropped = _filter(ranked)

    doc_filter = [str(d) for d in (doc_ids or [])]
    latency_ms = int((time.monotonic() - start) * 1000)
    log.info(
        'search q=%r k=%d filter=%s returned=%d dropped=%d top_dropped=%.3f latency_ms=%d',
        query, k, doc_filter, len(kept), dropped_count, top_dropped, latency_ms,
    )

    return kept[:k]


async def _embed_query(query: str) -> list[float]:
    [vec] = await voyage_client.embed([query], input_type='query')
    return vec


async def _retrieve(
    session: AsyncSession,
    query_vec: list[float],
    *,
    k: int,
    doc_ids: list[UUID] | None,
) -> list[ChunkResult]:
    return await vector_search(session, query_vec, k=k, doc_ids=doc_ids)


# Identity in v0. Replace with cross-encoder / XGBoost reranker in a future phase
# without touching callers; bump settings.search_oversample_factor when this stops
# being a no-op so _retrieve fetches enough candidates to rank from.
def _rank(results: list[ChunkResult], query: str) -> list[ChunkResult]:
    return results


def _filter(
    results: list[ChunkResult],
) -> tuple[list[ChunkResult], int, float]:
    threshold = settings.search_min_score
    kept = [r for r in results if r.score >= threshold]
    dropped = [r for r in results if r.score < threshold]
    top_dropped = max((r.score for r in dropped), default=0.0)
    return kept, len(dropped), top_dropped
