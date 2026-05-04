# Pattern adapted from agent-platform/agent_platform/agent/events.py
# Adapted for knowledge-search: tool_result includes parsed `chunks`, done
# carries the parsed `citations` array, and a new `error` event surfaces
# mid-stream failures (SSE cannot switch to HTTP 500 once bytes are flowing).

from typing import Any, Literal, TypedDict


class TextEvent(TypedDict):
    type: Literal['text']
    delta: str


class ToolUseEvent(TypedDict):
    type: Literal['tool_use']
    id: str
    name: str
    arguments: dict[str, Any]


class ToolResultEvent(TypedDict):
    type: Literal['tool_result']
    id: str
    result: str
    chunks: list[dict[str, Any]]


class Citation(TypedDict):
    n: int
    chunk_id: int
    document_id: str
    filename: str
    page: int | None
    heading: str | None


class DoneEvent(TypedDict):
    type: Literal['done']
    answer: str
    citations: list[Citation]


class ErrorEvent(TypedDict):
    type: Literal['error']
    code: str
    detail: str
    retriable: bool


AgentEvent = TextEvent | ToolUseEvent | ToolResultEvent | DoneEvent | ErrorEvent


def text_event(delta: str) -> TextEvent:
    return {'type': 'text', 'delta': delta}


def tool_use_event(*, id: str, name: str, arguments: dict[str, Any]) -> ToolUseEvent:
    return {'type': 'tool_use', 'id': id, 'name': name, 'arguments': arguments}


def tool_result_event(*, id: str, result: str, chunks: list[dict[str, Any]]) -> ToolResultEvent:
    return {'type': 'tool_result', 'id': id, 'result': result, 'chunks': chunks}


def done_event(*, answer: str, citations: list[Citation]) -> DoneEvent:
    return {'type': 'done', 'answer': answer, 'citations': citations}


def error_event(*, code: str, detail: str, retriable: bool) -> ErrorEvent:
    return {'type': 'error', 'code': code, 'detail': detail, 'retriable': retriable}
