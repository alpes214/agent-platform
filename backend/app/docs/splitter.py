from collections.abc import Iterator
from functools import cache

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from backend.app.config import settings
from backend.app.docs.loader import PageRange
from backend.app.repos.docs import ChunkData

# Tokens are roughly 4 chars on English text; pymupdf4llm's output is closer
# to 3.5-4. The langchain splitter is char-based, so we multiply by 4.
_CHARS_PER_TOKEN = 4

_HEADER_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[('#', 'h1'), ('##', 'h2'), ('###', 'h3')]
)


def split(markdown: str, page_ranges: list[PageRange]) -> list[ChunkData]:
    if not markdown.strip():
        return []
    chunks: list[ChunkData] = []
    for page, section_text, heading in _walk_sections(markdown, page_ranges):
        for piece in _fit_to_size(section_text):
            chunks.append(_make_chunk(piece, page, heading))
    return chunks


# Yields (page, section_text, heading) for every header-bounded section,
# inheriting the most recent heading across page boundaries.
def _walk_sections(
    markdown: str, page_ranges: list[PageRange]
) -> Iterator[tuple[int | None, str, str | None]]:
    current_heading: str | None = None
    for page_text, page_number in _page_slices(markdown, page_ranges):
        for section_text, section_heading in _sections(page_text):
            if section_heading is not None:
                current_heading = section_heading
            yield page_number, section_text, current_heading


def _page_slices(
    markdown: str, page_ranges: list[PageRange]
) -> Iterator[tuple[str, int | None]]:
    if not page_ranges:
        yield markdown, None
        return
    for r in page_ranges:
        text = markdown[r.start_offset : r.end_offset]
        if text.strip():
            yield text, r.page_number


def _sections(page_text: str) -> Iterator[tuple[str, str | None]]:
    for section in _HEADER_SPLITTER.split_text(page_text):
        text = section.page_content.strip()
        if text:
            yield text, _deepest_heading(section.metadata)


def _fit_to_size(text: str) -> Iterator[str]:
    if len(text) <= _chunk_chars():
        yield text
        return
    for piece in _recursive_splitter().split_text(text):
        piece = piece.strip()
        if piece:
            yield piece


def _make_chunk(text: str, page: int | None, heading: str | None) -> ChunkData:
    return ChunkData(text=text, embedding=[], page=page, heading=heading)


def _deepest_heading(metadata: dict[str, str]) -> str | None:
    for key in ('h3', 'h2', 'h1'):
        value = metadata.get(key)
        if value:
            return value
    return None


@cache
def _chunk_chars() -> int:
    return settings.docs_chunk_size * _CHARS_PER_TOKEN


@cache
def _recursive_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=_chunk_chars(),
        chunk_overlap=settings.docs_chunk_overlap * _CHARS_PER_TOKEN,
    )
