"""A deterministic stand-in for Claude, for tests, CI and ``--fake`` demos.

It implements the same two methods as :class:`~dossier.llm.anthropic_llm.AnthropicLLM` and
reads the same prompts, so the orchestrator, grounding checks and metrics run for real.
Knobs inject the failures the system is supposed to survive.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, cast

from dossier.config import ModelSpec
from dossier.llm.base import Completion, LLMError, T
from dossier.pricing import TokenUsage
from dossier.schemas import (
    BaselineOutput,
    ClaimVerdict,
    Critique,
    Finding,
    Judgment,
    Plan,
    Report,
    ReportSection,
    ResearchNotes,
    Source,
    SubQuestion,
)

_ID = re.compile(r'<evidence id="(F\d+)"[^>]*>(.*?)</evidence>', re.S)
_TAG = re.compile(r"<(\w+)[^>]*>\n(.*?)\n</\1>", re.S)
CALL_USAGE = TokenUsage(input_tokens=2_000, output_tokens=500)


@dataclass
class FakeLLM:
    fail_on: tuple[str, ...] = ()  # research on a sub-question containing one of these raises
    weak_on: tuple[str, ...] = ()  # ...or returns a quote the critic will reject
    fabricate_source: bool = False  # each researcher also cites a URL no search returned
    fabricate_citation: bool = False  # the writer cites an evidence id that doesn't exist
    follow_ups: tuple[str, ...] = ()  # the critic's first review asks for these
    latency_s: float = 0.0
    calls: list[str] = field(default_factory=list)
    _critiques: int = 0

    async def structured(
        self, spec: ModelSpec, *, system: str, prompt: str, schema: type[T]
    ) -> Completion[T]:
        await self._tick(schema.__name__)
        handler = {Plan: self._plan, Critique: self._critique, Report: self._report, Judgment: self._judge}
        if schema not in handler:
            raise LLMError(f"FakeLLM has no structured handler for {schema.__name__}")
        output = handler[schema](prompt)
        return Completion(cast(T, output), spec.model, CALL_USAGE)

    async def research(
        self,
        spec: ModelSpec,
        *,
        system: str,
        prompt: str,
        schema: type[T],
        max_searches: int,
        max_turns: int,
    ) -> Completion[T]:
        await self._tick(schema.__name__)
        tags = _tags(prompt)
        topic = tags.get("your_sub_question") or tags.get("research_question") or prompt
        if any(s in topic for s in self.fail_on):
            raise LLMError(f"injected failure for {topic!r}")

        sources = [
            Source(f"https://example.org/{_slug(topic)}/{i}", f"Source {i} on {topic}") for i in (1, 2)
        ]
        weak = any(s in topic for s in self.weak_on)
        findings = [
            Finding(
                claim=f"Claim {i} about {topic}",
                source_url=src.url,
                quote="(vague, unrelated text)" if weak else f"Evidence {i} that supports claim {i}.",
            )
            for i, src in enumerate(sources, start=1)
        ]
        if self.fabricate_source:
            findings.append(Finding(claim="Invented", source_url="https://not-searched.example/x", quote="q"))

        output: Any
        if schema is BaselineOutput:
            body = " ".join(f"{f.claim} [F{i}]." for i, f in enumerate(findings, start=1))
            output = BaselineOutput(findings=findings, report=_mk_report(topic, body))
        elif schema is ResearchNotes:
            output = ResearchNotes(summary=f"Summary of {topic}", findings=findings, open_gaps=[])
        else:
            raise LLMError(f"FakeLLM has no research handler for {schema.__name__}")
        usage = CALL_USAGE + TokenUsage(web_searches=2)
        return Completion(output, spec.model, usage, sources=sources)

    # ------------------------------------------------------------------ handlers

    def _plan(self, prompt: str) -> Plan:
        q = _tags(prompt)["research_question"]
        aspects = ["background and definitions", "current evidence", "risks and counter-evidence"]
        return Plan(sub_questions=[SubQuestion(question=f"{q} - {a}", rationale=a) for a in aspects])

    def _critique(self, prompt: str) -> Critique:
        verdicts = [
            ClaimVerdict(
                finding_id=fid,
                verdict="unsupported" if "(vague, unrelated text)" in body else "supported",
                reason="checked by fake critic",
            )
            for fid, body in _ID.findall(prompt)
        ]
        follow_ups = list(self.follow_ups) if self._critiques == 0 else []
        self._critiques += 1
        return Critique(verdicts=verdicts, follow_up_questions=follow_ups)

    def _report(self, prompt: str) -> Report:
        ids = [fid for fid, _ in _ID.findall(prompt)]
        if self.fabricate_citation:
            ids.append("F999")
        body = " ".join(f"A cited fact [{fid}]." for fid in ids) or "The evidence was insufficient."
        return _mk_report(_tags(prompt).get("main_question", "report"), body)

    def _judge(self, prompt: str) -> Judgment:
        # Always prefers whichever report is shown first, so a position-swapped pair of
        # judgments disagrees: exactly the bias the eval's swap is designed to cancel.
        return Judgment(winner="A", reasoning="fake judge prefers position A")

    async def _tick(self, label: str) -> None:
        self.calls.append(label)
        if self.latency_s:
            await asyncio.sleep(self.latency_s)


def _mk_report(topic: str, body: str) -> Report:
    return Report(
        title=f"Report: {topic}",
        executive_summary=body,
        sections=[ReportSection(heading="Findings", body=body)],
        limitations=["Generated by FakeLLM."],
    )


def _tags(prompt: str) -> dict[str, str]:
    return {name: body for name, body in _TAG.findall(prompt)}


def _slug(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:10]
