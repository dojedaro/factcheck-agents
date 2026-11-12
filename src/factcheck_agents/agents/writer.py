from __future__ import annotations

from collections.abc import Sequence

from factcheck_agents.agents.base import AgentContext, tag
from factcheck_agents.schemas import EvidenceItem, Report

SYSTEM = """\
You write the team's final report from evidence that has already been fact-checked.

- Use only the evidence provided. Don't add facts from your own knowledge.
- Cite evidence inline by id, like [F3], on every sentence that states a fact. Only use ids \
that appear in the evidence.
- Evidence marked verdict="partial" only partly supports its claim: hedge it, or state the \
weaker version.
- Where evidence conflicts, say so and cite both sides.
- Lead with the answer. Organize sections by theme, not by sub-question.
- Put real gaps and caveats in `limitations`. If the evidence can't answer the question, \
say that plainly instead of padding."""


class Writer:
    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    async def run(self, main_question: str, evidence: Sequence[EvidenceItem]) -> Report:
        items = (
            "\n\n".join(
                tag(
                    "evidence",
                    f"claim: {e.claim}\nquote: {e.quote}",
                    id=e.id,
                    verdict=e.verdict or "unverified",
                    source=e.source.title,
                )
                for e in evidence
            )
            or "<evidence_list>No evidence passed fact-checking.</evidence_list>"
        )
        completion = await self.ctx.call(
            "writer",
            lambda spec: self.ctx.llm.structured(
                spec,
                system=SYSTEM,
                prompt=f"{tag('main_question', main_question)}\n\n{items}",
                schema=Report,
            ),
            items=len(evidence),
        )
        return completion.output
