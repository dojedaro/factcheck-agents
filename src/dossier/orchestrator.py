"""The team: plan -> parallel research -> critique (-> one follow-up round) -> write -> verify.

Control flow lives in code, not in a model. Models decide *what* to research and *what* to
say; code decides how many agents run, in what order, under what budget, and which
evidence is allowed into the report. That split is what makes the system debuggable.

Failure policy:
* A researcher that errors or times out costs its sub-question, not the run.
* Hitting the budget stops new research; the critic and writer still finish on the reserve.
* If every researcher fails, the writer still runs and says the evidence is insufficient.
"""

from __future__ import annotations

import asyncio
import itertools
import time
from collections.abc import Sequence

from dossier.agents import (
    AgentContext,
    Baseline,
    Critic,
    Planner,
    Researcher,
    ResearchOutcome,
    Writer,
    apply_verdicts,
)
from dossier.budget import Budget, BudgetExceededError
from dossier.config import Settings
from dossier.grounding import cited_ids, ground_findings, strip_invalid_citations
from dossier.llm.base import LLM
from dossier.schemas import EvidenceItem, Finding, Report, RunMetrics, RunResult, Source
from dossier.tracing import Tracer


class ResearchTeam:
    def __init__(self, llm: LLM, settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = settings or Settings()

    async def run(self, question: str, tracer: Tracer | None = None) -> RunResult:
        ctx = AgentContext(self.llm, self.settings, Budget(self.settings.budget_usd), tracer or Tracer())
        return await _TeamRun(ctx, question).execute()

    async def run_baseline(self, question: str, tracer: Tracer | None = None) -> RunResult:
        """Single-agent control: same model and tools, a matching search allowance, no team."""
        ctx = AgentContext(self.llm, self.settings, Budget(self.settings.budget_usd), tracer or Tracer())
        started = time.perf_counter()
        metrics = RunMetrics(sub_questions=1, research_rounds=1)
        search_allowance = self.settings.max_searches_per_researcher * self.settings.max_sub_questions
        async with ctx.tracer.span("baseline", question=question):
            output, sources = await Baseline(ctx).run(question, max_searches=search_allowance)
        # Ids follow the baseline's own list positions, so a dropped finding leaves a dangling
        # citation that the grounding check counts as invalid - the same rule the team faces.
        evidence, metrics.findings_ungrounded = _ground_by_position(output.findings, sources, question)
        for e in evidence:
            e.verdict = "supported"  # nobody checks the baseline; it vouches for itself
        metrics.findings_submitted = len(output.findings)
        return _finish(question, output.report, evidence, metrics, ctx.budget, started, warnings=[])


class _TeamRun:
    """State for one run of the team. Created per question, never reused."""

    def __init__(self, ctx: AgentContext, question: str) -> None:
        self.ctx = ctx
        self.question = question
        self.metrics = RunMetrics()
        self.evidence: list[EvidenceItem] = []
        self.warnings: list[str] = []
        self._ids = (f"F{i}" for i in itertools.count(1))

    async def execute(self) -> RunResult:
        started = time.perf_counter()
        async with self.ctx.tracer.span("team", question=self.question):
            plan = await Planner(self.ctx).run(self.question)
            self.metrics.sub_questions = len(plan.sub_questions)
            pending = [sq.question for sq in plan.sub_questions]

            while pending:
                self.metrics.research_rounds += 1
                new_evidence = await self._research_round(pending)
                pending = await self._critique(new_evidence)
                if self.metrics.research_rounds > self.ctx.settings.max_follow_up_rounds:
                    break
                if self.metrics.stopped_by_budget:
                    break

            accepted = [e for e in self.evidence if e.accepted]
            report = await Writer(self.ctx).run(self.question, accepted)

        return _finish(
            self.question, report, self.evidence, self.metrics, self.ctx.budget, started, self.warnings
        )

    async def _research_round(self, sub_questions: Sequence[str]) -> list[EvidenceItem]:
        settings = self.ctx.settings
        gate = asyncio.Semaphore(settings.max_parallel_researchers)
        researcher = Researcher(self.ctx)

        async def investigate(sub_question: str) -> ResearchOutcome | BaseException:
            async with gate:
                try:
                    async with (
                        self.ctx.tracer.span("researcher", sub_question=sub_question),
                        asyncio.timeout(settings.researcher_timeout_s),
                    ):
                        return await researcher.run(self.question, sub_question)
                except Exception as exc:  # noqa: BLE001 - one researcher failing must not sink the team
                    return exc

        async with self.ctx.tracer.span("research_round", round=self.metrics.research_rounds):
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(investigate(q)) for q in sub_questions]
            outcomes = [t.result() for t in tasks]

        new_evidence: list[EvidenceItem] = []
        for sub_question, outcome in zip(sub_questions, outcomes, strict=True):
            if isinstance(outcome, BaseException):
                self.metrics.researcher_failures += 1
                if isinstance(outcome, BudgetExceededError):
                    self.metrics.stopped_by_budget = True
                self.warnings.append(f"researcher failed on {sub_question!r}: {type(outcome).__name__}")
                continue
            self.metrics.findings_submitted += len(outcome.notes.findings)
            grounded, ungrounded = ground_findings(
                outcome.notes.findings,
                outcome.sources,
                sub_question=sub_question,
                ids=self._ids,
            )
            self.metrics.findings_ungrounded += ungrounded
            new_evidence.extend(grounded)

        self.evidence.extend(new_evidence)
        return new_evidence

    async def _critique(self, new_evidence: list[EvidenceItem]) -> list[str]:
        """Judge the new evidence. Returns follow-up questions worth another round."""
        if not new_evidence:
            return []
        try:
            critique = await Critic(self.ctx).run(self.question, new_evidence)
        except BudgetExceededError:
            self.metrics.stopped_by_budget = True
            self.warnings.append("budget ran out before fact-checking; unchecked evidence excluded")
            return []
        self.warnings.extend(apply_verdicts(new_evidence, critique))
        return critique.follow_up_questions


def _ground_by_position(
    findings: Sequence[Finding], sources: Sequence[Source], question: str
) -> tuple[list[EvidenceItem], int]:
    """Ground the baseline's findings, keeping each one's id equal to its list position."""
    evidence: list[EvidenceItem] = []
    ungrounded = 0
    for i, finding in enumerate(findings, start=1):
        kept, dropped = ground_findings([finding], sources, sub_question=question, ids=iter([f"F{i}"]))
        evidence.extend(kept)
        ungrounded += dropped
    return evidence, ungrounded


def _finish(
    question: str,
    report: Report,
    evidence: list[EvidenceItem],
    metrics: RunMetrics,
    budget: Budget,
    started: float,
    warnings: list[str],
) -> RunResult:
    """Final grounding check and metrics. Shared by the team and the baseline."""
    accepted_ids = {e.id for e in evidence if e.accepted}
    report, metrics.citations_invalid = strip_invalid_citations(report, accepted_ids)
    used = cited_ids(report)

    metrics.citations_used = len(used)
    metrics.findings_supported = sum(e.verdict == "supported" for e in evidence)
    metrics.findings_partial = sum(e.verdict == "partial" for e in evidence)
    metrics.findings_unsupported = sum(e.verdict == "unsupported" for e in evidence)
    metrics.cost_usd = round(budget.spent_usd, 6)
    metrics.wall_seconds = round(time.perf_counter() - started, 2)
    if metrics.citations_invalid:
        warnings.append(f"removed {metrics.citations_invalid} citation(s) to missing or rejected evidence")

    cited = [e for e in evidence if e.id in used]
    return RunResult(question, report, evidence, metrics, cited=cited, warnings=warnings)
