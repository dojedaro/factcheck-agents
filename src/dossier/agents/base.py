"""What every agent shares: the model, the settings, the budget and the tracer.

``AgentContext.call`` is the single choke point for model calls, so budget checks, cost
accounting and tracing can't be forgotten by an individual agent.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from xml.sax.saxutils import escape

from dossier.budget import Budget
from dossier.config import ModelSpec, Role, Settings
from dossier.llm.base import LLM, Completion, T
from dossier.pricing import cost_usd, is_priced
from dossier.tracing import Tracer

# Roles that must stop early to leave money for the critic and writer to finish the run.
_RESERVE_GUARDED: frozenset[Role] = frozenset({"planner", "researcher"})


@dataclass(slots=True)
class AgentContext:
    llm: LLM
    settings: Settings
    budget: Budget
    tracer: Tracer

    def spec(self, role: Role) -> ModelSpec:
        return self.settings.models.for_role(role)

    async def call(
        self,
        role: Role,
        invoke: Callable[[ModelSpec], Awaitable[Completion[T]]],
        **attrs: Any,
    ) -> Completion[T]:
        reserve = self.settings.finish_reserve_usd if role in _RESERVE_GUARDED else 0.0
        self.budget.ensure(keep_in_reserve=reserve)
        spec = self.spec(role)
        async with self.tracer.span(f"llm:{role}", **attrs) as span:
            completion = await invoke(spec)
            cost = cost_usd(completion.model, completion.usage)
            self.budget.charge(cost)
            span.model, span.usage, span.cost_usd = completion.model, completion.usage, cost
            span.attrs["request_ids"] = completion.request_ids
            if completion.model != spec.model:
                span.attrs["served_by_fallback"] = completion.model
            if not is_priced(completion.model):
                span.attrs["pricing"] = "unknown model; billed at the highest known rate"
        return completion


def tag(name: str, body: str, **attrs: str) -> str:
    """Wrap untrusted text in an XML-style tag so prompts keep data and instructions apart."""
    attr_text = "".join(f' {k}="{escape(v, {chr(34): "&quot;"})}"' for k, v in attrs.items())
    return f"<{name}{attr_text}>\n{escape(body)}\n</{name}>"
