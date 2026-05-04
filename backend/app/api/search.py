from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.db.postgres import get_session
from backend.app.embeddings.tei_client import TeiUnavailable
from backend.app.search.service import search_chunks

router = APIRouter(tags=['search'])


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: int
    document_id: UUID
    filename: str
    page: int | None
    heading: str | None
    text: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@router.get('/search', response_model=SearchResponse)
async def search(
    q: Annotated[str, Query(min_length=1, max_length=2000)],
    k: Annotated[int, Query(ge=1, le=100)] = settings.docs_top_k,
    doc_id: Annotated[list[UUID] | None, Query()] = None,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail='q must not be whitespace')

    try:
        chunks = await search_chunks(session, query, k=k, doc_ids=doc_id)
    except TeiUnavailable as e:
        raise HTTPException(
            status_code=503, detail=f'embedding service unavailable: {e}'
        ) from e

    return SearchResponse(
        query=query,
        results=[SearchResult.model_validate(r) for r in chunks],
    )
