import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.embeddings.voyage_client import EmbeddingsUnavailable
from backend.app.search.service import search_chunks


class ToolFailed(Exception):
    def __init__(self, *, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class LLMUnavailable(Exception):
    pass


TOOLS: list[dict[str, Any]] = [
    {
        'type': 'function',
        'function': {
            'name': 'search_docs',
            'description': (
                'Search the document corpus for chunks relevant to a query. '
                'Use this when you need information from the documents to answer the user.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Natural-language search query',
                    },
                    'k': {
                        'type': 'integer',
                        'description': 'How many chunks to retrieve',
                        'default': 5,
                        'minimum': 1,
                        'maximum': 20,
                    },
                },
                'required': ['query'],
            },
        },
    },
]


async def dispatch(
    name: str, arguments: dict[str, Any], session: AsyncSession
) -> tuple[str, list[dict[str, Any]]]:
    if name != 'search_docs':
        raise ToolFailed(code='tool_failed', detail=f'unknown tool: {name}')

    # Server-side validation -- never trust the LLM to honour the JSON schema.
    query = str(arguments.get('query', '')).strip()
    if not query:
        raise ToolFailed(code='tool_failed', detail='empty query')
    k_raw = arguments.get('k', 5)
    try:
        k = max(1, min(int(k_raw), 20))
    except (TypeError, ValueError):
        k = 5

    try:
        chunks = await search_chunks(session, query, k=k)
    except EmbeddingsUnavailable as e:
        raise ToolFailed(
            code='tool_failed', detail=f'embedding service unavailable: {e}'
        ) from e

    max_chars = settings.tool_result_text_max_chars
    payload = [
        {
            'chunk_id': c.chunk_id,
            'document_id': str(c.document_id),
            'filename': c.filename,
            'page': c.page,
            'heading': c.heading,
            'text': c.text[:max_chars],
            'score': round(c.score, 3),
        }
        for c in chunks
    ]
    return json.dumps(payload), payload
