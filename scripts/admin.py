import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from backend.app.config import settings
from backend.app.db.postgres import close_postgres, session_factory
from backend.app.queue.app import app as procrastinate_app
from backend.app.queue.tasks import ingest_document

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger('admin')


async def status() -> None:
    sm = session_factory()
    async with sm() as s:
        by_status = (await s.execute(text(
            'SELECT status, count(*) FROM documents GROUP BY status ORDER BY status'
        ))).all()
        chunks = (await s.execute(text('SELECT count(*) FROM doc_chunks'))).scalar() or 0
        jobs = (await s.execute(text(
            'SELECT status, count(*) FROM procrastinate_jobs GROUP BY status ORDER BY status'
        ))).all()
    staging_files = sum(1 for _ in settings.staging_dir.glob('*.pdf'))
    log.info('documents by status:')
    if by_status:
        for stat, n in by_status:
            log.info(f'  {stat:12} {n}')
    else:
        log.info('  (none)')
    log.info(f'doc_chunks:   {chunks}')
    log.info(f'staging pdfs: {staging_files}')
    log.info('procrastinate_jobs:')
    if jobs:
        for stat, n in jobs:
            log.info(f'  {stat:12} {n}')
    else:
        log.info('  (empty)')


async def reset_doc(doc_id: str) -> None:
    sm = session_factory()
    async with sm() as s:
        result = await s.execute(text('DELETE FROM documents WHERE id = :id'), {'id': doc_id})
        await s.commit()
    (settings.staging_dir / f'{doc_id}.pdf').unlink(missing_ok=True)
    log.info(f'deleted {result.rowcount} doc(s) matching id={doc_id}')


async def reset_failed() -> None:
    sm = session_factory()
    async with sm() as s:
        ids = (await s.execute(text(
            "SELECT id FROM documents WHERE status = 'failed'"
        ))).scalars().all()
        await s.execute(text("DELETE FROM documents WHERE status = 'failed'"))
        await s.commit()
    for did in ids:
        (settings.staging_dir / f'{did}.pdf').unlink(missing_ok=True)
    log.info(f'deleted {len(ids)} failed doc(s)')


async def reset_all() -> None:
    sm = session_factory()
    async with sm() as s:
        await s.execute(text(
            'TRUNCATE documents, doc_chunks, procrastinate_jobs RESTART IDENTITY CASCADE'
        ))
        await s.commit()
    removed = 0
    for f in settings.staging_dir.glob('*.pdf'):
        f.unlink()
        removed += 1
    log.info(
        f'truncated documents + doc_chunks + procrastinate_jobs; '
        f'removed {removed} staging file(s)'
    )


async def reingest(doc_id: str) -> None:
    if not (settings.staging_dir / f'{doc_id}.pdf').exists():
        log.warning(f'no staged file at {settings.staging_dir}/{doc_id}.pdf — ingest will fail')
    sm = session_factory()
    async with sm() as s:
        await s.execute(
            text('DELETE FROM doc_chunks WHERE document_id = :id'),
            {'id': doc_id},
        )
        await s.execute(
            text(
                "UPDATE documents SET status='pending', chunk_count=NULL, "
                "page_count=NULL, error_message=NULL WHERE id = :id"
            ),
            {'id': doc_id},
        )
        await s.commit()
    async with procrastinate_app.open_async():
        await ingest_document.defer_async(doc_id=doc_id)
    log.info(f're-enqueued {doc_id}')


async def reingest_all() -> None:
    sm = session_factory()
    async with sm() as s:
        ids = (await s.execute(text('SELECT id FROM documents'))).scalars().all()
        await s.execute(text('DELETE FROM doc_chunks'))
        await s.execute(text(
            "UPDATE documents SET status='pending', chunk_count=NULL, "
            "page_count=NULL, error_message=NULL"
        ))
        await s.commit()
    async with procrastinate_app.open_async():
        for did in ids:
            await ingest_document.defer_async(doc_id=str(did))
    log.info(f're-enqueued {len(ids)} doc(s)')


async def vacuum_staging() -> None:
    sm = session_factory()
    async with sm() as s:
        known = {
            str(r)
            for r in (await s.execute(text('SELECT id FROM documents'))).scalars().all()
        }
    removed = 0
    for f in settings.staging_dir.glob('*.pdf'):
        if f.stem not in known:
            f.unlink()
            removed += 1
    log.info(f'vacuumed {removed} orphan staging file(s)')


NO_ARG: dict[str, Callable[[], Awaitable[None]]] = {
    'status': status,
    'reset-all': reset_all,
    'reset-failed': reset_failed,
    'reingest-all': reingest_all,
    'vacuum-staging': vacuum_staging,
}
ONE_ARG: dict[str, Callable[[str], Awaitable[None]]] = {
    'reset-doc': reset_doc,
    'reingest': reingest,
}


async def main() -> None:
    args = sys.argv[1:] or ['status']
    cmd, *rest = args
    if cmd in NO_ARG:
        if rest:
            sys.exit(f'{cmd} takes no arguments')
        await NO_ARG[cmd]()
    elif cmd in ONE_ARG:
        if len(rest) != 1:
            sys.exit(f'usage: admin.py {cmd} <doc_id>')
        await ONE_ARG[cmd](rest[0])
    else:
        known = ', '.join({**NO_ARG, **ONE_ARG})
        sys.exit(f'unknown command: {cmd}\nknown: {known}')
    await close_postgres()


if __name__ == '__main__':
    asyncio.run(main())
