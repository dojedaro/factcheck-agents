"""Command line: ``dossier run``, ``dossier eval``, ``dossier trace``."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dossier import tracing
from dossier.config import Settings
from dossier.evaluation import run_eval
from dossier.llm.base import LLM
from dossier.orchestrator import ResearchTeam
from dossier.render import to_markdown
from dossier.tracing import Tracer


def load_dotenv(path: Path = Path(".env")) -> None:
    """Load KEY=value lines from a local .env file. Real environment variables win."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _make_llm(fake: bool, settings: Settings) -> LLM:
    if fake:
        from dossier.llm.fake import FakeLLM

        return FakeLLM()
    from dossier.llm.anthropic_llm import AnthropicLLM

    return AnthropicLLM(use_fallbacks=settings.use_fallbacks)


def _run_dir(root: Path, label: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:40]
    path = root / f"{datetime.now():%Y%m%d-%H%M%S}-{slug}"
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _cmd_run(args: argparse.Namespace, settings: Settings) -> int:
    team = ResearchTeam(_make_llm(args.fake, settings), settings)
    tracer = Tracer()
    result = await (team.run_baseline if args.baseline else team.run)(args.question, tracer)
    out = _run_dir(args.out, args.question)
    (out / "report.md").write_text(to_markdown(result), encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(asdict(result.metrics), indent=2), encoding="utf-8")
    tracer.dump(out / "trace.jsonl")

    print(to_markdown(result))
    for w in result.warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"\nwrote {out}", file=sys.stderr)
    return 0


async def _cmd_eval(args: argparse.Namespace, settings: Settings) -> int:
    questions = [
        json.loads(line)["question"] for line in args.questions.read_text("utf-8").splitlines() if line
    ]
    if args.limit:
        questions = questions[: args.limit]
    out = _run_dir(args.out, "eval")
    print(await run_eval(_make_llm(args.fake, settings), settings, questions, out))
    print(f"wrote {out}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dossier", description=__doc__)
    parser.add_argument("--config", type=Path, help="TOML file overriding default settings")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="research a question and write a cited report")
    run.add_argument("question")
    run.add_argument("--baseline", action="store_true", help="use the single-agent baseline instead")

    ev = sub.add_parser("eval", help="compare the team against the single-agent baseline")
    ev.add_argument("--questions", type=Path, default=Path("evals/questions.jsonl"))
    ev.add_argument("--limit", type=int, default=0)

    for p in (run, ev):
        p.add_argument("--fake", action="store_true", help="use the offline fake model ($0)")
        p.add_argument("--out", type=Path, default=Path("runs"))

    tr = sub.add_parser("trace", help="print a trace file as a tree")
    tr.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    if args.command == "trace":
        print(tracing.render_tree(tracing.load(args.path)))
        return 0

    load_dotenv()
    settings = Settings.load(args.config)
    handler = _cmd_run if args.command == "run" else _cmd_eval
    return asyncio.run(handler(args, settings))


if __name__ == "__main__":
    raise SystemExit(main())
