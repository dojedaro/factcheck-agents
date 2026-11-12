"""The orchestrator, end to end, against the fake model. These are the behaviors that matter:
grounding, failure isolation, budgets, parallelism and trace structure."""

import time

import pytest

from factcheck_agents.config import Settings
from factcheck_agents.llm.fake import FakeLLM
from factcheck_agents.orchestrator import ResearchTeam
from factcheck_agents.render import to_markdown
from factcheck_agents.tracing import Tracer

Q = "Should a mid-size bank adopt passkeys for retail customers?"


async def run(llm: FakeLLM, **settings: object):
    tracer = Tracer()
    result = await ResearchTeam(llm, Settings(**settings)).run(Q, tracer)
    return result, tracer


async def test_happy_path_cites_every_verified_finding():
    result, _ = await run(FakeLLM())

    m = result.metrics
    assert m.sub_questions == 3
    assert m.research_rounds == 1
    assert m.findings_submitted == m.findings_supported == 6
    assert m.citations_used == 6
    assert m.citations_invalid == m.findings_ungrounded == m.researcher_failures == 0
    assert m.cost_usd > 0
    assert len(result.cited) == 6
    assert "## References" in to_markdown(result)


async def test_one_failing_researcher_does_not_sink_the_team():
    result, tracer = await run(FakeLLM(fail_on=("risks",)))

    assert result.metrics.researcher_failures == 1
    assert result.metrics.findings_supported == 4
    assert any("researcher failed" in w for w in result.warnings)
    failed = [s for s in tracer.spans if s.name == "researcher" and s.status != "ok"]
    assert len(failed) == 1


async def test_findings_citing_unsearched_urls_never_reach_the_writer():
    result, _ = await run(FakeLLM(fabricate_source=True))

    assert result.metrics.findings_ungrounded == 3  # one per researcher
    assert all("not-searched" not in e.source.url for e in result.evidence)


async def test_critic_rejections_are_excluded_from_the_report():
    result, _ = await run(FakeLLM(weak_on=("current evidence",)))

    rejected = {e.id for e in result.evidence if e.verdict == "unsupported"}
    assert len(rejected) == 2
    assert result.metrics.findings_unsupported == 2
    assert rejected.isdisjoint(e.id for e in result.cited)


async def test_writer_citations_to_missing_evidence_are_stripped():
    result, _ = await run(FakeLLM(fabricate_citation=True))

    assert result.metrics.citations_invalid > 0
    assert "[F999]" not in to_markdown(result)


async def test_follow_up_round_runs_once_then_stops():
    llm = FakeLLM(follow_ups=("What do regulators require?", "What did peers report?"))
    result, _ = await run(llm, max_follow_up_rounds=1)

    assert result.metrics.research_rounds == 2
    assert result.metrics.findings_supported == 10  # 3 + 2 researchers x 2 findings
    assert llm.calls.count("Critique") == 2


async def test_follow_ups_disabled():
    result, _ = await run(FakeLLM(follow_ups=("more?",)), max_follow_up_rounds=0)
    assert result.metrics.research_rounds == 1


async def test_budget_stops_research_but_the_run_still_ends_in_a_report():
    # Planner costs $0.018; with $0.03 total and $0.02 reserved, no researcher may start.
    result, _ = await run(FakeLLM(), budget_usd=0.03, finish_reserve_usd=0.02)

    assert result.metrics.stopped_by_budget
    assert result.metrics.researcher_failures == 3
    assert result.report.title  # writer ran on the reserve
    assert result.metrics.citations_used == 0


async def test_researchers_run_in_parallel_up_to_the_limit():
    started = time.perf_counter()
    await run(FakeLLM(latency_s=0.2), max_parallel_researchers=3)
    parallel = time.perf_counter() - started

    started = time.perf_counter()
    await run(FakeLLM(latency_s=0.2), max_parallel_researchers=1)
    serial = time.perf_counter() - started

    # planner + critic + writer = 0.6s either way; researchers add 0.2s vs 0.6s.
    assert parallel < serial - 0.25


async def test_llm_spans_nest_under_their_researcher_even_in_parallel():
    _, tracer = await run(FakeLLM(latency_s=0.05))

    by_id = {s.id: s for s in tracer.spans}
    research_calls = [s for s in tracer.spans if s.name == "llm:researcher"]
    assert len(research_calls) == 3
    for call in research_calls:
        parent = by_id[call.parent_id]
        assert parent.name == "researcher"
        assert parent.attrs["sub_question"] == call.attrs["sub_question"]


async def test_baseline_gets_the_same_grounding_checks():
    llm = FakeLLM(fabricate_source=True)
    result = await ResearchTeam(llm, Settings()).run_baseline(Q)

    assert result.metrics.findings_submitted == 3
    assert result.metrics.findings_ungrounded == 1
    # The baseline cited its invented finding as [F3]; that citation must be removed.
    assert result.metrics.citations_invalid >= 1
    assert llm.calls == ["BaselineOutput"]


@pytest.mark.parametrize("bad", [{"max_sub_questions": 0}, {"budget_usd": 0}, {"unknown_knob": 1}])
def test_settings_reject_invalid_values(bad):
    with pytest.raises(ValueError):
        Settings(**bad)
