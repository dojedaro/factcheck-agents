from __future__ import annotations

from collections.abc import Sequence

from factcheck_agents.agents.base import AgentContext, tag
from factcheck_agents.schemas import Critique, EvidenceItem

SYSTEM = """\
You are the team's fact-checker. You did not do the research, and your job is to catch \
claims that the cited quote does not support.

For every evidence item, judge ONLY whether its quote supports its claim:
- supported: the quote states the claim, or makes it directly evident.
- partial: the quote supports part of the claim, or a weaker version of it.
- unsupported: the quote doesn't back the claim, contradicts it, or is too vague to tell.
Don't use your own knowledge to rescue a claim the quote doesn't support. Return exactly \
one verdict per item, using its id.

Then list at most {max_follow_ups} follow-up questions, only for gaps that would change the \
answer to the main question. An empty list is the right answer when coverage is adequate."""

MAX_FOLLOW_UPS = 2


class Critic:
    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    async def run(self, main_question: str, evidence: Sequence[EvidenceItem]) -> Critique:
        items = "\n\n".join(
            tag(
                "evidence",
                f"claim: {e.claim}\nquote: {e.quote}",
                id=e.id,
                source=e.source.title,
                sub_question=e.sub_question,
            )
            for e in evidence
        )
        completion = await self.ctx.call(
            "critic",
            lambda spec: self.ctx.llm.structured(
                spec,
                system=SYSTEM.format(max_follow_ups=MAX_FOLLOW_UPS),
                prompt=f"{tag('main_question', main_question)}\n\n{items}",
                schema=Critique,
            ),
            items=len(evidence),
        )
        critique = completion.output
        return Critique(
            verdicts=critique.verdicts,
            follow_up_questions=critique.follow_up_questions[:MAX_FOLLOW_UPS],
        )


def apply_verdicts(evidence: Sequence[EvidenceItem], critique: Critique) -> list[str]:
    """Attach verdicts to evidence. Returns warnings for ids the critic invented or skipped."""
    by_id = {e.id: e for e in evidence}
    warnings: list[str] = []
    for v in critique.verdicts:
        item = by_id.get(v.finding_id)
        if item is None:
            warnings.append(f"critic judged unknown id {v.finding_id}")
            continue
        item.verdict, item.verdict_reason = v.verdict, v.reason
    skipped = [e.id for e in evidence if e.verdict is None]
    if skipped:
        # Unjudged evidence is excluded from the report: no verdict means not verified.
        warnings.append(f"critic returned no verdict for {', '.join(skipped)}; excluded")
    return warnings
