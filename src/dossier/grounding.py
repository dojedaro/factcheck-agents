"""Deterministic checks that don't trust any model.

Two places where a multi-agent system quietly fabricates:

1. A researcher cites a URL its searches never returned (a plausible-looking hallucination).
2. The writer cites an evidence id that doesn't exist or that the critic rejected.

Both are checked here in plain code, after the models are done, and every violation is
counted in the run metrics instead of being silently patched.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from urllib.parse import urlsplit, urlunsplit

from dossier.schemas import EvidenceItem, Finding, Report, ReportSection, Source

CITATION = re.compile(r"\[(F\d+)\]")
_MARKER_WITH_SPACE = re.compile(r"(\s?)\[(F\d+)\]")


def normalize_url(url: str) -> str:
    """Compare URLs the way a human would: ignore scheme, ``www.``, fragments, trailing slash."""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    return urlunsplit(("", host, path, parts.query, ""))


def ground_findings(
    findings: Iterable[Finding],
    sources: Iterable[Source],
    *,
    sub_question: str,
    ids: Iterator[str],
) -> tuple[list[EvidenceItem], int]:
    """Keep findings whose URL a search really returned. Returns ``(evidence, n_ungrounded)``."""
    by_url = {normalize_url(s.url): s for s in sources}
    evidence: list[EvidenceItem] = []
    ungrounded = 0
    for f in findings:
        source = by_url.get(normalize_url(f.source_url))
        if source is None or not f.quote.strip():
            ungrounded += 1
            continue
        evidence.append(EvidenceItem(next(ids), sub_question, f.claim, f.quote.strip(), source))
    return evidence, ungrounded


def cited_ids(report: Report) -> set[str]:
    return set(CITATION.findall(_all_text(report)))


def strip_invalid_citations(report: Report, valid_ids: set[str]) -> tuple[Report, int]:
    """Remove citation markers that point at nothing. Returns ``(clean_report, n_removed)``."""
    removed = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal removed
        if m.group(2) in valid_ids:
            return m.group(0)
        removed += 1
        return ""

    def clean(text: str) -> str:
        return _MARKER_WITH_SPACE.sub(repl, text)

    cleaned = Report(
        title=report.title,
        executive_summary=clean(report.executive_summary),
        sections=[ReportSection(heading=s.heading, body=clean(s.body)) for s in report.sections],
        limitations=[clean(x) for x in report.limitations],
    )
    return cleaned, removed


def _all_text(report: Report) -> str:
    return "\n".join([report.executive_summary, *(s.body for s in report.sections), *report.limitations])
