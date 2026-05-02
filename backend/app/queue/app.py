from procrastinate import App, PsycopgConnector

from backend.app.config import settings


def _psycopg_conninfo(database_url: str) -> str:
    url = database_url
    if url.startswith('postgresql+asyncpg://'):
        url = 'postgresql://' + url[len('postgresql+asyncpg://') :]
    return url


app = App(
    connector=PsycopgConnector(conninfo=_psycopg_conninfo(settings.database_url)),
    import_paths=['backend.app.queue.tasks'],
)
