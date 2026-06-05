from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.app.config import settings
from backend.app.db.models import AccessLog, DocChunk, Document


class DocumentAdmin(ModelView, model=Document):
    name_plural = 'Documents'
    icon = 'fa-solid fa-file-pdf'
    column_list = [
        Document.id,
        Document.filename,
        Document.status,
        Document.uploaded_at,
        Document.page_count,
        Document.chunk_count,
    ]
    column_searchable_list = [Document.filename, Document.status]
    column_sortable_list = [Document.uploaded_at, Document.filename, Document.status]
    column_default_sort = [(Document.uploaded_at, True)]
    can_create = False
    page_size = 50


class DocChunkAdmin(ModelView, model=DocChunk):
    name_plural = 'Doc Chunks'
    icon = 'fa-solid fa-puzzle-piece'
    column_list = [DocChunk.id, DocChunk.document_id, DocChunk.page, DocChunk.heading]
    column_searchable_list = [DocChunk.document_id]
    column_sortable_list = [DocChunk.id, DocChunk.page]
    column_default_sort = [(DocChunk.id, False)]
    can_create = False
    can_edit = False
    page_size = 50


class AccessLogAdmin(ModelView, model=AccessLog):
    name = 'Access Log'
    name_plural = 'Access Log'
    icon = 'fa-solid fa-globe'
    column_list = [
        AccessLog.ts,
        AccessLog.country,
        AccessLog.city,
        AccessLog.gate,
        AccessLog.path,
        AccessLog.ip,
    ]
    column_searchable_list = [
        AccessLog.country,
        AccessLog.city,
        AccessLog.gate,
        AccessLog.path,
    ]
    column_sortable_list = [AccessLog.ts, AccessLog.country, AccessLog.gate]
    column_default_sort = [(AccessLog.ts, True)]
    page_size = 50
    can_create = False
    can_edit = False
    can_delete = True


def mount_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    admin = Admin(app, engine, base_url=f'/{settings.admin_prefix}')
    admin.add_view(DocumentAdmin)
    admin.add_view(DocChunkAdmin)
    admin.add_view(AccessLogAdmin)
    return admin
