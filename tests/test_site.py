"""The replay viewer's data bundle, built from real CLI output of the fake model ($0)."""

from __future__ import annotations

import json
from pathlib import Path

from factcheck_agents.cli import main
from factcheck_agents.site_data import build_bundle


def _only_dir(root: Path) -> Path:
    (d,) = [p for p in root.iterdir() if p.is_dir()]
    return d


def test_bundle_from_a_team_run(tmp_path: Path) -> None:
    assert main(["run", "Does the bundle work?", "--fake", "--out", str(tmp_path / "runs")]) == 0
    bundle = build_bundle([_only_dir(tmp_path / "runs")], [])

    (run,) = bundle["runs"]
    assert run["mode"] == "team"
    assert run["question"] == "Does the bundle work?"
    assert run["metrics"]["findings_submitted"] > 0
    # Times are relative, so the viewer can replay from zero.
    assert min(s["start"] for s in run["spans"]) == 0
    assert all(s["end"] >= s["start"] for s in run["spans"])
    # Request ids are debugging noise on a public page.
    assert not any("request_ids" in s["attrs"] for s in run["spans"])


def test_bundle_from_a_baseline_run(tmp_path: Path) -> None:
    assert main(["run", "Baseline?", "--baseline", "--fake", "--out", str(tmp_path / "runs")]) == 0
    (run,) = build_bundle([_only_dir(tmp_path / "runs")], [])["runs"]
    assert run["mode"] == "baseline"


def test_bundle_from_an_eval_links_questions_to_runs(tmp_path: Path) -> None:
    assert main(["eval", "--fake", "--limit", "2", "--out", str(tmp_path / "runs")]) == 0
    bundle = build_bundle([], [_only_dir(tmp_path / "runs")])

    (ev,) = bundle["evals"]
    assert len(ev["questions"]) == 2
    run_ids = {r["id"] for r in bundle["runs"]}
    for q in ev["questions"]:
        assert q["team_run"] in run_ids and q["baseline_run"] in run_ids
        assert set(q["judgments"]) == {"team_as_a", "team_as_b"}
    assert all(r["spans"] for r in bundle["runs"])


def test_site_command_writes_json(tmp_path: Path) -> None:
    assert main(["run", "Q?", "--fake", "--out", str(tmp_path / "runs")]) == 0
    out = tmp_path / "site" / "bundle.json"
    assert main(["site", "--run", str(_only_dir(tmp_path / "runs")), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["version"] == 1


def test_committed_examples_build() -> None:
    """The data the published viewer is built from must stay loadable."""
    root = Path(__file__).resolve().parents[1]
    runs = sorted(p for p in (root / "examples" / "runs").iterdir() if p.is_dir())
    evals = sorted(p for p in (root / "evals" / "results").iterdir() if p.is_dir())
    bundle = build_bundle(runs, evals)
    assert {r["mode"] for r in bundle["runs"]} == {"team", "baseline"}
    assert all(r["spans"] for r in bundle["runs"])
