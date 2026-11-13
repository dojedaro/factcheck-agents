"""Bundle saved runs and eval results into one JSON file for the static replay viewer.

The viewer in ``site/`` is plain HTML and JavaScript with no build step. Everything it shows
comes from files earlier runs already wrote, so publishing it costs nothing and nobody can
spend API credit through it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from factcheck_agents import tracing

# Span attributes that are useful in a local debugging session but noise on a public page.
_DROP_ATTRS = {"request_ids"}


def _spans(trace_path: Path) -> list[dict[str, Any]]:
    """Load a trace with times relative to the first span, so the viewer can replay it from 0."""
    raw = tracing.load(trace_path)
    if not raw:
        return []
    t0 = min(s["start"] for s in raw)
    spans = []
    for s in raw:
        start = s["start"] - t0
        spans.append(
            {
                "id": s["id"],
                "parent_id": s["parent_id"],
                "name": s["name"],
                "start": round(start, 3),
                "end": round(start + s["duration_s"], 3),
                "status": s["status"],
                "model": s["model"],
                "usage": s["usage"],
                "cost_usd": s["cost_usd"],
                "attrs": {k: v for k, v in s["attrs"].items() if k not in _DROP_ATTRS},
            }
        )
    return spans


def _mode(spans: list[dict[str, Any]]) -> str:
    roots = [s["name"] for s in spans if s["parent_id"] is None]
    return "baseline" if roots == ["baseline"] else "team"


def _question(report_md: str) -> str:
    for line in report_md.splitlines():
        if line.startswith("> "):
            return line[2:].strip()
    return ""


def load_run(run_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    """One ``factcheck run`` output folder: report.md, metrics.json and trace.jsonl."""
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    spans = _spans(run_dir / "trace.jsonl")
    return {
        "id": run_id or run_dir.name,
        "question": _question(report),
        "mode": _mode(spans),
        "report_md": report,
        "metrics": json.loads((run_dir / "metrics.json").read_text(encoding="utf-8")),
        "spans": spans,
    }


def load_eval(eval_dir: Path, eval_id: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """One ``factcheck eval`` output folder. Returns the eval summary and the runs it produced."""
    eval_id = eval_id or eval_dir.name
    lines = (eval_dir / "results.jsonl").read_text(encoding="utf-8").splitlines()
    questions, runs = [], []
    for i, line in enumerate((x for x in lines if x.strip()), 1):
        row = json.loads(line)
        ids = {}
        for side in ("team", "baseline"):
            stem = f"q{i:02d}-{side}"
            trace = eval_dir / f"{stem}.trace.jsonl"
            run_id = f"{eval_id}/{stem}"
            ids[side] = run_id
            runs.append(
                {
                    "id": run_id,
                    "question": row["question"],
                    "mode": side,
                    "report_md": (eval_dir / f"{stem}.md").read_text(encoding="utf-8"),
                    "metrics": row[side],
                    "spans": _spans(trace) if trace.is_file() else [],
                }
            )
        questions.append(
            {
                "question": row["question"],
                "outcome": row["outcome"],
                # The judge saw the team as report A first, then as report B.
                "judgments": {"team_as_a": row["judgments"][0], "team_as_b": row["judgments"][1]},
                "team_run": ids["team"],
                "baseline_run": ids["baseline"],
            }
        )
    summary_path = eval_dir / "summary.md"
    summary = summary_path.read_text(encoding="utf-8") if summary_path.is_file() else ""
    return {"id": eval_id, "summary_md": summary, "questions": questions}, runs


def build_bundle(run_dirs: list[Path], eval_dirs: list[Path]) -> dict[str, Any]:
    runs = [load_run(d) for d in run_dirs]
    evals = []
    for d in eval_dirs:
        ev, ev_runs = load_eval(d)
        evals.append(ev)
        runs += ev_runs
    return {"version": 1, "runs": runs, "evals": evals}


def write_bundle(run_dirs: list[Path], eval_dirs: list[Path], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_bundle(run_dirs, eval_dirs), indent=1), encoding="utf-8")
    return out
