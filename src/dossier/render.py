"""Turn a run result into a Markdown report with a references section."""

from __future__ import annotations

from dossier.schemas import RunResult


def to_markdown(result: RunResult) -> str:
    r, m = result.report, result.metrics
    out = [f"# {r.title}", "", f"> {result.question}", "", r.executive_summary, ""]
    for section in r.sections:
        out += [f"## {section.heading}", "", section.body, ""]
    if r.limitations:
        out += ["## Limitations", "", *(f"- {x}" for x in r.limitations), ""]
    if result.cited:
        out += ["## References", ""]
        for e in sorted(result.cited, key=lambda e: int(e.id[1:])):
            hedge = " *(partially supported)*" if e.verdict == "partial" else ""
            out.append(f'- **[{e.id}]** [{e.source.title}]({e.source.url}){hedge}: "{e.quote}"')
        out.append("")
    out += [
        "---",
        f"*{m.sub_questions} sub-questions, {m.research_rounds} research round(s), "
        f"{m.findings_supported + m.findings_partial}/{m.findings_submitted} findings passed checks, "
        f"{m.citations_used} cited. Cost ${m.cost_usd:.2f}, {m.wall_seconds:.0f}s.*",
    ]
    return "\n".join(out) + "\n"
