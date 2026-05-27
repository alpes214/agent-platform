import logging

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from backend.app.config import settings

log = logging.getLogger(__name__)
router = APIRouter(tags=['transcribe'])

# Groq serves whisper-large-v3 at the same OpenAI-compatible base_url/key used
# for the LLM. transcriptions is a multipart endpoint; the OpenAI SDK handles it.
_WHISPER_MODEL = 'whisper-large-v3'

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=httpx.Timeout(settings.llm_timeout_seconds, connect=5.0),
        )
    return _client


@router.post('/transcribe')
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    body = await file.read()
    if not body:
        raise HTTPException(status_code=400, detail='Empty audio')
    try:
        result = await _get_client().audio.transcriptions.create(
            model=_WHISPER_MODEL,
            file=(file.filename or 'audio.webm', body),
        )
    except (APIConnectionError, APITimeoutError) as e:
        raise HTTPException(status_code=503, detail=f'transcription unavailable: {e}') from e
    text = (result.text or '').strip()
    log.info('transcribed %d bytes -> %d chars', len(body), len(text))
    return {'text': text}
