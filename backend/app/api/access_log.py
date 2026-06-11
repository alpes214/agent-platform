from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import AccessLog
from backend.app.db.postgres import get_session

router = APIRouter(tags=['access-log'])


class AccessLogIn(BaseModel):
    ip: Annotated[str | None, Field(max_length=64)] = None
    country: Annotated[str | None, Field(max_length=8)] = None
    region: Annotated[str | None, Field(max_length=64)] = None
    city: Annotated[str | None, Field(max_length=128)] = None
    lat: Decimal | None = None
    lon: Decimal | None = None
    user_agent: Annotated[str | None, Field(max_length=1024)] = None
    path: Annotated[str, Field(max_length=512)]
    referer: Annotated[str | None, Field(max_length=2048)] = None
    gate: Annotated[str, Field(pattern=r'^(magic-link|cookie|denied|landing)$')]


@router.post('/access-log', status_code=204)
async def write_access_log(
    payload: AccessLogIn, session: AsyncSession = Depends(get_session)
) -> None:
    session.add(AccessLog(**payload.model_dump()))
    await session.commit()
