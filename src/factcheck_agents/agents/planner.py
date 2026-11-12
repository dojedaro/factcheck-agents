from __future__ import annotations

from factcheck_agents.agents.base import AgentContext, tag
from factcheck_agents.schemas import Plan

SYSTEM = """\
You are the lead analyst of a small research team. You split a research question into \
sub-questions that separate researchers will investigate in parallel, without talking to \
each other.

Good sub-questions:
- are answerable from public web sources,
- don't overlap, so no two researchers duplicate work,
- together cover what a careful reader needs to answer the main question,
- include at least one that looks for counter-evidence, risks or limitations.

Return between 2 and {max_n} sub-questions. Use fewer when the question is narrow: every \
sub-question costs a researcher."""


class Planner:
    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx

    async def run(self, question: str) -> Plan:
        max_n = self.ctx.settings.max_sub_questions
        completion = await self.ctx.call(
            "planner",
            lambda spec: self.ctx.llm.structured(
                spec,
                system=SYSTEM.format(max_n=max_n),
                prompt=tag("research_question", question),
                schema=Plan,
            ),
        )
        plan = completion.output
        # Enforce the cap in code; the prompt is a request, not a guarantee.
        return Plan(sub_questions=plan.sub_questions[:max_n])
