from factcheck_agents.grounding import cited_ids, ground_findings, normalize_url, strip_invalid_citations
from factcheck_agents.schemas import Finding, Report, ReportSection, Source


def ids(prefix: str = "F"):
    n = 0
    while True:
        n += 1
        yield f"{prefix}{n}"


def test_normalize_url_ignores_cosmetic_differences():
    assert normalize_url("https://www.Example.com/a/b/#frag") == normalize_url("http://example.com/a/b")
    assert normalize_url("https://example.com/a?x=1") != normalize_url("https://example.com/a?x=2")


def test_findings_must_cite_a_searched_url_and_carry_a_quote():
    sources = [Source("https://example.com/real", "Real")]
    findings = [
        Finding(claim="ok", source_url="https://www.example.com/real/", quote="  supporting text "),
        Finding(claim="invented url", source_url="https://elsewhere.com/fake", quote="q"),
        Finding(claim="no quote", source_url="https://example.com/real", quote="   "),
    ]

    evidence, ungrounded = ground_findings(findings, sources, sub_question="sq", ids=ids())

    assert [e.claim for e in evidence] == ["ok"]
    assert evidence[0].id == "F1"
    assert evidence[0].quote == "supporting text"
    assert evidence[0].source.title == "Real"
    assert ungrounded == 2


def _report(body: str) -> Report:
    return Report(
        title="t",
        executive_summary=body,
        sections=[ReportSection(heading="h", body=body)],
        limitations=[f"caveat {body}"],
    )


def test_invalid_citations_are_removed_and_counted_everywhere():
    report = _report("Fact one [F1]. Fact two [F2][F9].")

    clean, removed = strip_invalid_citations(report, valid_ids={"F1", "F2"})

    assert removed == 3  # F9 in the summary, the section, and the limitation
    assert clean.executive_summary == "Fact one [F1]. Fact two [F2]."
    assert cited_ids(clean) == {"F1", "F2"}


def test_valid_report_is_unchanged():
    report = _report("All good [F1].")
    clean, removed = strip_invalid_citations(report, valid_ids={"F1"})
    assert removed == 0
    assert clean == report
