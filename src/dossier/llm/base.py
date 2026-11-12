"""The model interface every agent talks to.

Two operations cover the whole team:

* ``structured`` - one call, output validated against a Pydantic model (planner, critic,
  writer, judge).
* ``research`` - a tool loop with web search that ends when the model submits a result
  matching a Pydantic model; it also returns every page the searches really returned
  (researchers, baseline).

Keeping the surface this small is what makes the fake model in tests honest: it implements
the same two methods, so the orchestrator runs unchanged against either.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from dossier.config import ModelSpec
from dossier.pricing import TokenUsage
from dossier.schemas import Source

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """A model call finished but produced nothing usable."""


class RefusalError(LLMError):
    pass


class TruncatedError(LLMError):
    pass


@dataclass(slots=True)
class Completion(Generic[T]):
    output: T
    model: str  # the model that served the request (may differ from the one asked for, on fallback)
    usage: TokenUsage
    sources: list[Source] = field(default_factory=list)
    request_ids: list[str] = field(default_factory=list)


class LLM(Protocol):
    async def structured(
        self, spec: ModelSpec, *, system: str, prompt: str, schema: type[T]
    ) -> Completion[T]: ...

    async def research(
        self,
        spec: ModelSpec,
        *,
        system: str,
        prompt: str,
        schema: type[T],
        max_searches: int,
        max_turns: int,
    ) -> Completion[T]: ...
