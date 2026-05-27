from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api import docs as docs_api
from backend.app.config import settings
from backend.app.db import postgres as postgres_module
from backend.app.db.models import Document
from backend.app.embeddings import voyage_client
from backend.app.main import app

pytestmark = pytest.mark.postgres

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample.pdf'


@pytest.fixture(autouse=True)
async def _wire(postgres_engine, monkeypatch, tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    sm = async_sessionmaker(postgres_engine, expire_on_commit=False)
    monkeypatch.setattr(postgres_module, '_engine', postgres_engine)
    monkeypatch.setattr(postgres_module, '_sessionmaker', sm)
    monkeypatch.setattr(settings, 'staging_dir', tmp_path)
    # Stop the BackgroundTask from actually ingesting during this test.
    monkeypatch.setattr(docs_api, 'ingest', _noop_ingest)
    yield
    await voyage_client.close()


async def _noop_ingest(doc_id) -> None:
    return None


async def test_upload_same_bytes_twice_is_idempotent(
    committing_session: AsyncSession,
) -> None:
    transport = ASGITransport(app=app)
    body = FIXTURE.read_bytes()

    async with AsyncClient(transport=transport, base_url='http://test') as client:
        r1 = await client.post(
            '/docs',
            files={'file': ('sample.pdf', body, 'application/pdf')},
        )
        assert r1.status_code == 201
        first = r1.json()
        assert first['status'] == 'pending'

        r2 = await client.post(
            '/docs',
            files={'file': ('sample.pdf', body, 'application/pdf')},
        )
        assert r2.status_code == 201
        second = r2.json()
        assert second['doc_id'] == first['doc_id']

    rows = (
        (
            await committing_session.execute(
                select(Document).where(Document.sha256 != None)  # noqa: E711
            )
        )
        .scalars()
        .all()
    )
    matching = [d for d in rows if str(d.id) == first['doc_id']]
    assert len(matching) == 1
