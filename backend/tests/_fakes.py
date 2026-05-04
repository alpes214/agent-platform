# Pattern adapted from agent-platform/tests/conftest.py
# A scriptable fake for AsyncOpenAI's chat.completions.create. Each call pops
# the next entry from `.responses` and records kwargs into `.calls`.

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction
    type: str = 'function'


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list[FakeToolCall] | None = None


@dataclass
class FakeChoice:
    message: FakeMessage
    finish_reason: str = 'stop'


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]
    usage: Any | None = None


def completion_text(text: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(message=FakeMessage(content=text))])


def completion_tool_call(
    *, id: str, name: str, arguments: dict[str, Any], content: str | None = None
) -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                message=FakeMessage(
                    content=content,
                    tool_calls=[
                        FakeToolCall(
                            id=id,
                            function=FakeFunction(name=name, arguments=json.dumps(arguments)),
                        )
                    ],
                ),
                finish_reason='tool_calls',
            )
        ]
    )


def completion_malformed_tool_call(*, id: str, name: str, raw_arguments: str) -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                message=FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            id=id,
                            function=FakeFunction(name=name, arguments=raw_arguments),
                        )
                    ],
                ),
                finish_reason='tool_calls',
            )
        ]
    )


@dataclass
class FakeOpenAI:
    responses: list[Any] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        outer = self

        class _Completions:
            async def create(self, **kwargs: Any) -> Any:
                outer.calls.append(kwargs)
                if not outer.responses:
                    raise AssertionError('FakeOpenAI: no more scripted responses')
                resp = outer.responses.pop(0)
                if isinstance(resp, Exception):
                    raise resp
                return resp

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()

    async def close(self) -> None:
        return None
