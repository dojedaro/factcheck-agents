"""Typed contracts between agents.

Every hand-off in the pipeline is one of these models. The LLM-facing models are sent to
the API as JSON schemas (structured outputs or a strict tool), so an agent can't hand the
next one a malformed message: it either validates or the call fails loudly.

Identifiers (``F1``, ``S3``...) are assigned by code, never by a model, so a model can't
invent a citation that looks valid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- planner


class SubQuestion(BaseModel):
    question: str = Field(description="One focused, independently researchable question.")
    rationale: str = Field(description="Why answering this helps answer the main question.")


class Plan(BaseModel):
    sub_questions: list[SubQuestion] = Field(
        description="Non-overlapping sub-questions that together cover the main question."
    )


# --------------------------------------------------------------------------- researcher


class Finding(BaseModel):
    claim: str = Field(description="One factual claim, stated plainly.")
    source_url: str = Field(description="URL of a page returned by web_search in this session.")
    quote: str = Field(description="A short verbatim excerpt from that page that supports the claim.")


class ResearchNotes(BaseModel):
    summary: str = Field(description="Two or three sentences answering the sub-question.")
    findings: list[Finding]
    open_gaps: list[str] = Field(description="What you could not establish from sources.")


# --------------------------------------------------------------------------- critic

Verdict = Literal["supported", "partial", "unsupported"]


class ClaimVerdict(BaseModel):
    finding_id: str = Field(description="The id of the finding being judged, e.g. F3.")
    verdict: Verdict
    reason: str = Field(description="One sentence explaining the verdict.")


class Critique(BaseModel):
    verdicts: list[ClaimVerdict]
    follow_up_questions: list[str] = Field(
        description="Important gaps worth one more round of research. Empty if coverage is adequate."
    )


# --------------------------------------------------------------------------- writer


class ReportSection(BaseModel):
    heading: str
    body: str = Field(description="Markdown prose. Cite findings inline as [F1], [F2].")


class Report(BaseModel):
    title: str
    executive_summary: str = Field(description="Three to five sentences. Cite findings inline.")
    sections: list[ReportSection]
    limitations: list[str] = Field(description="Known gaps, conflicting evidence, or caveats.")


# --------------------------------------------------------------------------- baseline


class BaselineOutput(BaseModel):
    """What the single-agent baseline submits: its evidence and its report in one go."""

    findings: list[Finding]
    report: Report = Field(description="Cite findings by their 1-based position: [F1] is the first finding.")


# --------------------------------------------------------------------------- judge


class Judgment(BaseModel):
    winner: Literal["A", "B", "tie"]
    reasoning: str = Field(description="Two or three sentences comparing the reports on the rubric.")


# --------------------------------------------------------------------------- internal records


@dataclass(frozen=True, slots=True)
class Source:
    """A page that a web_search call really returned. The only thing a finding may cite."""

    url: str
    title: str
    page_age: str | None = None


@dataclass(slots=True)
class EvidenceItem:
    """A finding after code has checked its source and given it an id."""

    id: str
    sub_question: str
    claim: str
    quote: str
    source: Source
    verdict: Verdict | None = None
    verdict_reason: str = ""

    @property
    def accepted(self) -> bool:
        return self.verdict in ("supported", "partial")


@dataclass(slots=True)
class RunMetrics:
    sub_questions: int = 0
    research_rounds: int = 0
    researcher_failures: int = 0
    findings_submitted: int = 0
    findings_ungrounded: int = 0  # cited a URL no search returned
    findings_supported: int = 0
    findings_partial: int = 0
    findings_unsupported: int = 0
    citations_used: int = 0
    citations_invalid: int = 0  # writer cited an id that doesn't exist or was rejected
    cost_usd: float = 0.0
    wall_seconds: float = 0.0
    stopped_by_budget: bool = False


@dataclass(slots=True)
class RunResult:
    question: str
    report: Report
    evidence: list[EvidenceItem]
    metrics: RunMetrics
    cited: list[EvidenceItem] = field(default_factory=list)  # evidence the final report cites
    warnings: list[str] = field(default_factory=list)
