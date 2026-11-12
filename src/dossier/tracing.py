"""Structured traces: one span per agent step, nested correctly across parallel tasks.

The current span lives in a ``ContextVar``, and asyncio copies the context into each task,
so a researcher's LLM call nests under that researcher even while four of them run at once.
Traces are written as JSON Lines and rendered as a tree by ``dossier trace``.
"""

from __future__ import annotations

import itertools
import json
import time
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from dossier.pricing import TokenUsage


@dataclass(slots=True)
class Span:
    id: int
    parent_id: int | None
    name: str
    start: float
    end: float | None = None
    status: str = "ok"
    model: str | None = None
    usage: TokenUsage = field(default_factory=TokenUsage)
    cost_usd: float = 0.0
    attrs: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return (self.end or time.perf_counter()) - self.start

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration_s"] = round(self.duration_s, 3)
        return data


_current: ContextVar[Span | None] = ContextVar("dossier_current_span", default=None)


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._ids = itertools.count(1)

    @asynccontextmanager
    async def span(self, name: str, **attrs: Any) -> AsyncIterator[Span]:
        parent = _current.get()
        span = Span(next(self._ids), parent.id if parent else None, name, time.perf_counter(), attrs=attrs)
        self.spans.append(span)
        token = _current.set(span)
        try:
            yield span
        except BaseException as exc:
            span.status = f"error: {type(exc).__name__}: {exc}"[:300]
            raise
        finally:
            span.end = time.perf_counter()
            _current.reset(token)

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for s in self.spans:
                f.write(json.dumps(s.to_json(), default=str) + "\n")


def load(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def render_tree(spans: Iterable[dict[str, Any]]) -> str:
    """Render spans as an indented tree with duration, cost and status."""
    spans = list(spans)
    children: dict[int | None, list[dict[str, Any]]] = {}
    for s in spans:
        children.setdefault(s["parent_id"], []).append(s)

    lines: list[str] = []

    def walk(parent: int | None, depth: int) -> None:
        for s in sorted(children.get(parent, []), key=lambda x: x["start"]):
            label = s["name"] + "".join(f" {k}={v!r}" for k, v in s["attrs"].items() if k != "request_ids")
            cost = f"${s['cost_usd']:.4f}" if s["cost_usd"] else ""
            flag = "" if s["status"] == "ok" else f"  !! {s['status']}"
            lines.append(f"{'  ' * depth}{label:<70.70} {s['duration_s']:>7.2f}s {cost:>9}{flag}")
            walk(s["id"], depth + 1)

    walk(None, 0)
    total = sum(s["cost_usd"] for s in spans)
    lines.append(f"\ntotal cost ${total:.4f} across {sum(1 for s in spans if s['model'])} model calls")
    return "\n".join(lines)
