import asyncio
import logging
from typing import Any

import httpx

from backend.app.config import settings

log = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

# Voyage free tier rate-limits aggressively (429). Retry transient 429/5xx with
# exponential backoff, honouring the Retry-After header when present.
_MAX_RETRIES = 5
_MAX_BACKOFF_SECONDS = 60.0


class EmbeddingsUnavailable(Exception):
    pass


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get('retry-after')
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None  # HTTP-date form unsupported; fall back to exponential backoff


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.embed_base_url,
            timeout=httpx.Timeout(settings.embed_timeout_seconds, connect=5.0),
            headers={'Authorization': f'Bearer {settings.embed_api_key}'},
        )
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def _embed_batch(batch: list[str], input_type: str) -> list[list[float]]:
    # Voyage's /embeddings is OpenAI-shaped but adds input_type ('document' vs
    # 'query'), which materially improves retrieval quality.
    payload: dict[str, Any] = {
        'model': settings.embed_model,
        'input': batch,
        'input_type': input_type,
    }
    response: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await _get_client().post('/embeddings', json=payload)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise EmbeddingsUnavailable(str(e) or e.__class__.__name__) from e
        retriable = response.status_code == 429 or response.status_code >= 500
        if retriable and attempt < _MAX_RETRIES:
            delay = _retry_after_seconds(response)
            if delay is None:
                delay = min(2.0 * 2**attempt, _MAX_BACKOFF_SECONDS)
            log.warning(
                'embeddings %d, backing off %.1fs (attempt %d/%d)',
                response.status_code, delay, attempt + 1, _MAX_RETRIES,
            )
            await asyncio.sleep(delay)
            continue
        break
    assert response is not None
    response.raise_for_status()
    body = response.json()

    data = body.get('data') or []
    if len(data) != len(batch):
        raise ValueError(
            f'embeddings provider returned {len(data)} vectors for {len(batch)} inputs'
        )
    vectors = [item['embedding'] for item in data]
    for v in vectors:
        if len(v) != settings.embed_dim:
            raise ValueError(
                f'embeddings provider returned vector of dim {len(v)}, '
                f'expected {settings.embed_dim}'
            )
    return vectors


async def embed(texts: list[str], input_type: str = 'document') -> list[list[float]]:
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
            'embed batch %d/%d size=%d chars_total=%d chars_max=%d total_chunks=%d input_type=%s',
            batch_num, total_batches, len(batch), chars_total, chars_max, len(texts), input_type,
        )
        vectors = await _embed_batch(batch, input_type)
        out.extend(vectors)
    return out
