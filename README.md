# factcheck-agents

**A multi-agent research team built directly on the Claude API, with no agent framework.**
A planner splits a question, researchers investigate the parts in parallel with web search, a
critic fact-checks every claim against its quoted source, and a writer turns what survives into
a cited report. Plain code then checks every citation before you see it.

It ships with an eval that compares the team against a single agent on the same model and tools.
A team is only worth its complexity if it does measurably better per dollar, and in the first
measured run [it didn't yet](#results-5-questions-2026-11-12). The README says why and what to try next.

[![CI](https://github.com/dojedaro/factcheck-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/dojedaro/factcheck-agents/actions/workflows/ci.yml)

**[Replay real runs in the browser →](https://dojedaro.github.io/factcheck-agents/)** Watch the
researchers work in parallel, see what the checks rejected and where the money went, click any
citation to see its source and quote, and read the judge's reasoning for every eval question.
The page replays saved traces, so it makes no API calls.

```mermaid
flowchart LR
    Q([question]) --> P[Planner]
    P -->|2-4 sub-questions| R1[Researcher]
    P --> R2[Researcher]
    P --> R3[Researcher]
    R1 & R2 & R3 -->|findings + quotes + URLs| G{{"grounding check<br/>(code)"}}
    G -->|evidence F1..Fn| C[Critic]
    C -.->|follow-up questions<br/>max 1 extra round| R4[Researcher]
    R4 -.-> G
    C -->|supported / partial only| W[Writer]
    W --> V{{"citation check<br/>(code)"}}
    V --> Out([cited report + trace + metrics])
```

## Why it's built this way

| Decision | Why |
|---|---|
| **No framework.** Orchestration is under 200 lines of `asyncio` (`orchestrator.py`). | You can read the whole control flow in one file. Agents decide *what* to research and *what* to say; code decides how many run, in what order, under what budget, and which evidence may be used. |
| **Typed hand-offs.** Each agent's output is a Pydantic model, enforced by structured outputs or a strict tool schema (`schemas.py`). | An agent can't pass the next one malformed data: it validates or the call fails. |
| **Evidence ids come from code.** A model never makes up `F7`. | A model can't invent a citation that looks valid. |
| **Grounding is checked in code.** A finding must cite a URL that one of *that researcher's own searches* returned (`grounding.py`). | This catches the most common multi-agent fabrication, a real-looking URL from memory, without trusting any model. |
| **The critic isn't the researcher.** It judges each claim *only* against its quote. | A model checking its own work tends to approve it. Unsupported claims are dropped before writing. |
| **The writer's citations are checked too.** Citations to ids that don't exist or were rejected are stripped and counted. | Every number in the report traces back to a quote and a URL. |
| **Failure isolation.** Each researcher has a timeout; one failure costs one sub-question, not the run. | `asyncio.TaskGroup` gives structured concurrency; per-task error capture keeps one failure from cancelling the others. |
| **A budget with a reserve.** Research stops when spending reaches `budget - reserve`; the critic and writer finish on the reserve. | A run that runs out of money still ends with a report, not an exception. |
| **Traces.** Every agent step is a span, nested correctly across parallel tasks via `contextvars`. | `factcheck trace` shows who did what, how long it took and what it cost. |
| **Refusal fallbacks.** On a safety-classifier decline the API retries on a fallback model in the same call (`fallbacks="default"`). The trace records which model actually answered. | One false-positive refusal doesn't fail a researcher. |
| **A fake model for tests.** It implements the same two-method interface as the real client. | The whole pipeline runs in CI with no API key and costs $0. |

## Quick start

```bash
pip install -e ".[dev]"

# Offline: full pipeline against the fake model, $0
factcheck run "Should a mid-size bank adopt passkeys?" --fake

# Real run: put ANTHROPIC_API_KEY=... in a .env file (gitignored), or run `ant auth login`
factcheck run "Should a mid-size bank adopt passkeys?"
factcheck run "..." --baseline                      # the single-agent control
factcheck --config configs/quick.toml run "..."     # fewer sub-questions, no follow-up round

factcheck trace runs/<run>/trace.jsonl              # where the time and money went
```

Each run writes `report.md`, `metrics.json` and `trace.jsonl` to `runs/<timestamp>-<slug>/`.

```
team question='What are the security trade-offs between passkeys and S  105.61s
  llm:planner                                                               6.26s   $0.0105
  research_round round=1                                                   60.33s
    researcher sub_question='What attacks are SMS one-time codes vulnerabl   60.33s
      llm:researcher sub_question='What attacks are SMS one-time codes vulne   60.33s   $0.5149
    researcher sub_question='What are the security risks, limitations and    45.43s
      llm:researcher sub_question='What are the security risks, limitations    45.43s   $0.3352
  llm:critic items=12                                                      14.14s   $0.0465
  llm:writer items=12                                                      24.87s   $0.0614

total cost $0.9684 across 5 model calls
```
<sub>A real run (`configs/quick.toml`), before prompt caching was added. The two researchers ran in parallel: the research round took as long as the slower one.</sub>

## Does the team beat one agent?

`factcheck eval` runs the team and the single-agent baseline on `evals/questions.jsonl`, using the
same model, the same web search tool and a matching search allowance. It then reports two kinds
of evidence:

- **Deterministic metrics** from the grounding checks: findings that cite a URL no search
  returned, citations removed, findings the critic rejected, cost and wall time. No model is
  involved, so there's no judge bias.
- **A pairwise LLM judge**, run twice per question with the reports' positions swapped. A side
  wins only if it wins in both orders; a split verdict counts as a tie. This cancels position
  bias, the most common failure of LLM judges. The fake judge in the test suite always prefers
  position A, and a test checks that the swap turns every one of its verdicts into a tie.

### Results (5 questions, 2026-11-12)

Run on `configs/quick.toml` to fit a small budget: the team got 2 sub-questions and **no
follow-up round**, against a single agent with the same total search allowance (6 searches).
All agents used Claude Opus 5.5. The reports, judge reasoning and metrics are in
[`evals/results/2026-11-12-quick/`](evals/results/2026-11-12-quick/).

| | Team | Single agent |
|---|---|---|
| Judge wins (must win in both orders) | 2 | **3** |
| Mean cost per question | $0.90 | **$0.63** |
| Mean wall time | 98 s | **83 s** |
| Findings citing a URL no search returned | 0% | 0% |
| Findings the critic rejected | 3% | (no critic) |
| Citations to missing or rejected evidence | 0 | 0 |

**The single agent won this round**, and the judge's reasoning shows why:

- **The team lost on coverage, not accuracy.** In every loss the judge said the team's report
  was the *more faithful* one, but that it left out central topics: SIM swapping and account
  recovery for passkeys, the 10^25 FLOP systemic-risk threshold for the EU AI Act. With only two
  sub-questions and no follow-up round, the planner's split decided what got researched, and
  nothing caught the gaps.
- **The team won where faithfulness decided it.** On sodium-ion batteries and four-day weeks,
  the judge preferred the team for tying claims to quotes and flagging partial support.
- **Neither side fabricated sources.** Both had 0% findings citing an unsearched URL. On current
  models, the bigger quality lever is coverage, not catching made-up citations.

What this suggests trying next, each measurable with the same eval:

1. **Turn the follow-up round back on.** The critic already lists coverage gaps; in these runs
   no budget was set aside to research them.
2. **Ask the planner for coverage explicitly**, for example by listing the angles a reader would
   expect before splitting.
3. **Re-measure cost with prompt caching** (added after this eval). On a single-agent re-run of
   the same question, caching cut cost from $0.51 to $0.34.

A 5-question eval is small, and a 2-3 split is not statistically significant. The point of the
harness is that each of these changes can now be tested against a number instead of a hunch.

## Replay viewer

`site/` is a static page (plain HTML, CSS and JavaScript, no build step or dependencies) that
replays saved runs. `factcheck site` bundles run and eval folders into the one JSON file it reads:

```bash
factcheck site --run examples/runs/2026-11-12-team-passkeys --eval evals/results/2026-11-12-quick
python -m http.server -d site 8000      # then open http://localhost:8000
```

On every push to `main`, a workflow (`.github/workflows/pages.yml`) builds the bundle from
`examples/runs/` and `evals/results/` and publishes the page to GitHub Pages. Reports are model
output, so the viewer escapes all HTML before rendering its small Markdown subset and only
links to `http(s)` URLs.

## Configuration

Defaults are in `src/factcheck_agents/config.py`, and any TOML file can override them:

```toml
# configs/cheap-workers.toml: researchers do most of the reading, so they dominate cost
[models.researcher]
model = "claude-sonnet-5-5"
effort = "medium"
```

Every role (`planner`, `researcher`, `critic`, `writer`, `baseline`, `judge`) has its own model,
effort level and token limit. Run the eval before and after a change to see what it costs in quality.

## Layout

```
src/factcheck_agents/
  orchestrator.py    the team's control flow, plus the baseline
  agents/            planner, researcher, critic, writer, baseline: one prompt + one call each
  llm/               the model interface; Claude client; deterministic fake
  grounding.py       URL and citation checks that trust no model
  schemas.py         typed contracts between agents
  budget.py  pricing.py  tracing.py
  evaluation.py      team vs. baseline, swapped-position judge
  site_data.py       bundles saved runs for the replay viewer
site/                the static replay viewer (GitHub Pages)
examples/runs/       two real runs, kept for the viewer
tests/               43 tests; the real client is tested against a stubbed SDK
```

## Limitations

- **The critic checks claims against quotes, not quotes against pages.** Web search returns
  page content encrypted, so code can't confirm that a quote appears on the page. The URL
  check is deterministic; the quote check is not.
- **The budget is soft.** Researchers run in parallel, so several can pass the budget check at
  once. The overshoot is at most one call per parallel researcher, which the reserve absorbs.
- **Fallback costs are approximate.** If a fallback model serves part of a request, the whole
  call is billed at that model's rates.
- Prices in `pricing.py` are hard-coded (first-party API, 2026-11). Check the pricing page
  before relying on them for real spend.

## License

MIT
