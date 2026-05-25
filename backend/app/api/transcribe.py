import asyncio
import logging
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

from backend.app.config import settings

log = logging.getLogger(__name__)
router = APIRouter(tags=['transcribe'])

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        log.info(
            'loading whisper model=%s device=%s compute=%s',
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
        )
        _model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    return _model


def _transcribe_sync(path: str) -> str:
    segments, _ = _get_model().transcribe(path, vad_filter=True)
    return ' '.join(s.text for s in segments).strip()


@router.post('/transcribe')
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    body = await file.read()
    if not body:
        raise HTTPException(status_code=400, detail='Empty audio')
    with tempfile.NamedTemporaryFile(suffix='.webm') as f:
        f.write(body)
        f.flush()
        text = await asyncio.to_thread(_transcribe_sync, f.name)
    log.info('transcribed %d bytes -> %d chars', len(body), len(text))
    return {'text': text}
