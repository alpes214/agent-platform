from contextlib import closing
from dataclasses import dataclass
from typing import Any, NamedTuple

import pymupdf
import pymupdf4llm

_PAGE_SEPARATOR = "\n\n"


@dataclass(frozen=True)
class PageRange:
    start_offset: int
    end_offset: int
    page_number: int


def pdf_to_markdown(file_bytes: bytes) -> tuple[str, list[PageRange]]:
    pages = _extract_pages(file_bytes)
    markdown = _PAGE_SEPARATOR.join(page.text for page in pages)

    ranges: list[PageRange] = []
    offset = 0
    for page in pages:
        ranges.append(PageRange(offset, offset + len(page.text), page.number))
        offset += len(page.text) + len(_PAGE_SEPARATOR)
    return markdown, ranges


class _Page(NamedTuple):
    text: str
    number: int


def _extract_pages(file_bytes: bytes) -> list[_Page]:
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")  # type: ignore[no-untyped-call]
    with closing(doc):
        # page_chunks=True returns one dict per page; without it, to_markdown
        # returns a single concatenated string with no page boundaries.
        raw: list[dict[str, Any]] = pymupdf4llm.to_markdown(doc, page_chunks=True)

    pages: list[_Page] = []
    for i, raw_page in enumerate(raw, start=1):
        text = raw_page.get("text", "")
        meta = raw_page.get("metadata") or {}
        pages.append(_Page(text=text, number=_page_number(meta, fallback=i)))
    return pages


def _page_number(meta: dict[str, Any], fallback: int) -> int:
    pn = meta.get("page_number")
    return pn if isinstance(pn, int) else fallback
