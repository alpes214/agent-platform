import json
from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent import ask_loop
from backend.app.agent.events import AgentEvent
from backend.app.agent.prompts import SYSTEM_PROMPT
from backend.app.agent.tools import TOOLS, dispatch
from backend.app.config import settings
from backend.app.db.postgres import get_session

router = APIRouter(tags=['ask'])


class AskRequest(BaseModel):
    question: Annotated[str, Field(min_length=1, max_length=2000)]


@router.post('/ask')
async def ask(
    payload: AskRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail='question must not be whitespace')

    return StreamingResponse(
        _stream_events(request, question, session),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-transform',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


async def _stream_events(
    request: Request, question: str, session: AsyncSession
) -> AsyncIterator[bytes]:
    llm_client = AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=httpx.Timeout(settings.llm_timeout_seconds, connect=5.0),
    )
    try:
        async for event in ask_loop.run(
            question=question,
            tools=TOOLS,
            dispatch=dispatch,
            system_prompt=SYSTEM_PROMPT,
            llm_client=llm_client,  # type: ignore[arg-type]
            session=session,
            max_iterations=settings.max_agent_iterations,
            is_disconnected=request.is_disconnected,
        ):
            yield _format_sse(event)
    finally:
        await llm_client.close()


def _format_sse(event: AgentEvent) -> bytes:
    return f'event: {event["type"]}\ndata: {json.dumps(event)}\n\n'.encode()
