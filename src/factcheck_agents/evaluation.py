"""Is the team worth it? Team vs. single-agent baseline on the same questions.

Two kinds of evidence, reported side by side:

* Deterministic metrics from the grounding checks (ungrounded findings, invalid citations,
  cost, latency). No model involved, so no judge bias.
* A pairwise LLM judge, run twice per question with the reports' positions swapped. A side
  only wins if it wins in both orders; a split verdict is a tie. This cancels position bias,
  the most common failure of LLM judges.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from factcheck_agents.agents.base import AgentContext, tag
from factcheck_agents.budget import Budget
from factcheck_agents.config import Settings
from factcheck_agents.llm.base import LLM
from factcheck_agents.orchestrator import ResearchTeam
from factcheck_agents.render import to_markdown
from factcheck_agents.schemas import Judgment, RunMetrics, RunResult
from factcheck_agents.tracing import Tracer

JUDGE_SYSTEM = """\
You compare two research reports that answer the same question. Each report lists its \
references with the quoted evidence it relied on.

Judge on, in order of importance:
1. Faithfulness - are claims backed by the quoted evidence? Penalize claims with no citation \
or with citations whose quote doesn't support them.
2. Coverage - does it address the important parts of the question, including risks or \
counter-evidence?
3. Usefulness - is it clear, well organized and direct about uncertainty?

Length is not quality. Ignore which report comes first. Answer "tie" if neither is clearly \
better."""

Outcome = Literal["team", "baseline", "tie"]


@dataclass(slots=True)
class QuestionResult:
    question: str
    outcome: Outcome
    judgments: tuple[str, str]
    team: RunMetrics
    baseline: RunMetrics
    judge_cost_usd: float = 0.0  # both judge calls; not part of either side's cost


def verdict_from_swapped(first: Judgment, second: Judgment) -> Outcome:
    """``first`` saw (team=A, baseline=B); ``second`` saw them swapped."""
    if first.winner == "A" and second.winner == "B":
        return "team"
    if first.winner == "B" and second.winner == "A":
        return "baseline"
    return "tie"


async def judge(
    llm: LLM, settings: Settings, question: str, a: RunResult, b: RunResult, budget: Budget
) -> Judgment:
    """Compare two reports. Spend is charged to ``budget`` so the eval can report what judging cost."""
    ctx = AgentContext(llm, settings, budget, Tracer())
    prompt = "\n\n".join(
        [
            tag("question", question),
            tag("report", to_markdown(a), id="A"),
            tag("report", to_markdown(b), id="B"),
        ]
    )
    completion = await ctx.call(
        "judge", lambda spec: llm.structured(spec, system=JUDGE_SYSTEM, prompt=prompt, schema=Judgment)
    )
    return completion.output


async def compare(llm: LLM, settings: Settings, question: str, out_dir: Path, slug: str) -> QuestionResult:
    team = ResearchTeam(llm, settings)
    team_tracer, base_tracer = Tracer(), Tracer()
    team_result = await team.run(question, team_tracer)
    base_result = await team.run_baseline(question, base_tracer)

    judge_budget = Budget(settings.budget_usd)
    first = await judge(llm, settings, question, team_result, base_result, judge_budget)
    second = await judge(llm, settings, question, base_result, team_result, judge_budget)

    _save_run(out_dir, f"{slug}-team", team_result, team_tracer)
    _save_run(out_dir, f"{slug}-baseline", base_result, base_tracer)

    return QuestionResult(
        question,
        verdict_from_swapped(first, second),
        (first.reasoning, second.reasoning),
        team_result.metrics,
        base_result.metrics,
        judge_budget.spent_usd,
    )


async def run_eval(llm: LLM, settings: Settings, questions: list[str], out_dir: Path) -> str:
    # Sequential on purpose: kinder to rate limits, and wall-time numbers aren't skewed by contention.
    results = [await compare(llm, settings, q, out_dir, f"q{i:02d}") for i, q in enumerate(questions, 1)]
    summary = summarize(results)
    _save_eval(out_dir, results, summary)
    return summary


# File writes are small and synchronous, so they live outside the coroutines.
def _save_run(out_dir: Path, stem: str, result: RunResult, tracer: Tracer) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.md").write_text(to_markdown(result), encoding="utf-8")
    tracer.dump(out_dir / f"{stem}.trace.jsonl")


def _save_eval(out_dir: Path, results: list[QuestionResult], summary: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + "\n")
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")


def summarize(results: list[QuestionResult]) -> str:
    n = len(results)
    wins = {o: sum(r.outcome == o for r in results) for o in ("team", "baseline", "tie")}

    def mean(side: str, field: str) -> float:
        return statistics.fmean(getattr(getattr(r, side), field) for r in results) if results else 0.0

    def rate(side: str, num: str, den: str) -> str:
        total = sum(getattr(getattr(r, side), den) for r in results)
        part = sum(getattr(getattr(r, side), num) for r in results)
        return f"{part / total:.0%}" if total else "n/a"

    rows = [
        ("Judge wins (both orders)", str(wins["team"]), str(wins["baseline"])),
        ("Mean cost (USD)", f"{mean('team', 'cost_usd'):.3f}", f"{mean('baseline', 'cost_usd'):.3f}"),
        (
            "Mean wall time (s)",
            f"{mean('team', 'wall_seconds'):.0f}",
            f"{mean('baseline', 'wall_seconds'):.0f}",
        ),
        (
            "Mean citations in report",
            f"{mean('team', 'citations_used'):.1f}",
            f"{mean('baseline', 'citations_used'):.1f}",
        ),
        (
            "Findings citing an unsearched URL",
            rate("team", "findings_ungrounded", "findings_submitted"),
            rate("baseline", "findings_ungrounded", "findings_submitted"),
        ),
        (
            "Findings rejected by critic",
            rate("team", "findings_unsupported", "findings_submitted"),
            "n/a (no critic)",
        ),
        (
            "Invalid citations removed",
            str(sum(r.team.citations_invalid for r in results)),
            str(sum(r.baseline.citations_invalid for r in results)),
        ),
    ]
    lines = [
        f"# Team vs. single agent ({n} questions, {wins['tie']} ties)",
        "",
        "| Metric | Team | Baseline |",
        "|---|---|---|",
        *(f"| {a} | {b} | {c} |" for a, b, c in rows),
        "",
        f"Judging cost ${sum(r.judge_cost_usd for r in results):.3f} in total (two calls per question), "
        "not included in either side's cost.",
    ]
    return "\n".join(lines) + "\n"
