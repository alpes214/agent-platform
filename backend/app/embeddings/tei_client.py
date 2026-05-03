import logging
from typing import Any

import httpx

from backend.app.config import settings

log = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


class TeiUnavailable(Exception):
    pass


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        # TEI ignores Authorization; sent for future-compat with auth-gated endpoints.
        _client = httpx.AsyncClient(
            base_url=settings.embed_base_url,
            timeout=httpx.Timeout(settings.embed_timeout_seconds, connect=5.0),
            headers={'Authorization': f'Bearer {settings.llm_api_key}'},
        )
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def _embed_batch(batch: list[str]) -> list[list[float]]:
    payload: dict[str, Any] = {'model': settings.embed_model, 'input': batch}
    try:
        response = await _get_client().post('/embeddings', json=payload)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise TeiUnavailable(str(e) or e.__class__.__name__) from e
    response.raise_for_status()
    body = response.json()

    data = body.get('data') or []
    if len(data) != len(batch):
        raise ValueError(f'TEI returned {len(data)} embeddings for {len(batch)} inputs')
    vectors = [item['embedding'] for item in data]
    for v in vectors:
        if len(v) != settings.embed_dim:
            raise ValueError(f'TEI returned vector of dim {len(v)}, expected {settings.embed_dim}')
    return vectors


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    out: list[list[float]] = []
    batch_size = settings.embed_batch_size
    total_batches = (len(texts) + batch_size - 1) // batch_size
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_num = i // batch_size + 1
        chars_total = sum(len(t) for t in batch)
        chars_max = max(len(t) for t in batch)
        log.info(
            'embed batch %d/%d size=%d chars_total=%d chars_max=%d total_chunks=%d',
            batch_num, total_batches, len(batch), chars_total, chars_max, len(texts),
        )
        vectors = await _embed_batch(batch)
        out.extend(vectors)
    return out
