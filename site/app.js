"use strict";

// Static replay viewer for factcheck-agents. Reads data/bundle.json (built by `factcheck site`)
// and makes no network calls beyond that one file.

const LABELS = {
  "2026-11-12-team-passkeys": "Team · passkeys vs SMS codes (first real run)",
  "2026-11-12-baseline-passkeys": "Single agent · passkeys vs SMS codes (with prompt caching)",
};
const EVAL_NOTES = {
  "2026-11-12-quick":
    "5 questions on configs/quick.toml: the team got 2 sub-questions and no follow-up round, against " +
    "one agent with the same model (Claude Opus 5.5), the same web search tool and the same total " +
    "search allowance. The team runs predate prompt caching.",
};
const PLAYBACK_SECONDS = 14;

const $ = (sel) => document.querySelector(sel);
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const usd = (x, digits = 2) => `$${x.toFixed(digits)}`;
const secs = (x) => `${x.toFixed(x < 10 ? 1 : 0)}s`;
const short = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

let bundle;
let current; // { run, rows, total, refs }
let t = 0;
let playing = false;
let lastFrame = 0;

// ---------- Markdown (escape first, then a small safe subset) ----------

function inline(text) {
  let s = esc(text);
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  s = s.replace(/\[(F\d+)\]/g, '<a class="cite" data-ref="$1" href="#" role="button">$1</a>');
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  return s;
}

function parseRefs(md) {
  const refs = {};
  const re = /^- \*\*\[(F\d+)\]\*\* \[(.*)\]\((https?:[^\s)]+)\)( \*\(partially supported\)\*)?: "(.*)"$/;
  for (const line of md.split("\n")) {
    const m = line.match(re);
    if (m) refs[m[1]] = { title: m[2], url: m[3], partial: Boolean(m[4]), quote: m[5] };
  }
  return refs;
}

function markdown(md, refs) {
  const out = [];
  let list = null;
  let table = null;
  const closeBlocks = () => {
    if (list) out.push("</ul>"), (list = null);
    if (table) out.push(renderTable(table)), (table = null);
  };
  for (const raw of md.split("\n")) {
    const line = raw.trimEnd();
    let m;
    if (line.startsWith("|")) {
      if (list) out.push("</ul>"), (list = null);
      (table ||= []).push(line);
      continue;
    }
    if ((m = line.match(/^- (.*)$/))) {
      if (table) out.push(renderTable(table)), (table = null);
      if (!list) out.push("<ul>"), (list = true);
      const ref = line.match(/^- \*\*\[(F\d+)\]\*\*/);
      if (ref) {
        const cls = refs[ref[1]]?.partial ? "ref partial" : "ref";
        out.push(`<li class="${cls}" id="ref-${ref[1]}">${inline(m[1])}</li>`);
      } else {
        out.push(`<li>${inline(m[1])}</li>`);
      }
      continue;
    }
    closeBlocks();
    if (!line.trim()) continue;
    if ((m = line.match(/^(#{1,4}) (.*)$/))) out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`);
    else if (line === "---") out.push("<hr>");
    else if (line.startsWith("> ")) out.push(`<blockquote>${inline(line.slice(2))}</blockquote>`);
    else out.push(`<p>${inline(line)}</p>`);
  }
  closeBlocks();
  return out.join("\n");
}

function renderTable(lines) {
  const cells = (l) => l.replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  const body = lines.filter((l) => !/^\|[\s:|-]+\|$/.test(l));
  const [head, ...rows] = body;
  return (
    "<table><thead><tr>" + cells(head).map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>" +
    rows.map((r) => "<tr>" + cells(r).map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>").join("") +
    "</tbody></table>"
  );
}

// ---------- Timeline rows from spans ----------

function buildRows(run) {
  const spans = run.spans;
  const byId = Object.fromEntries(spans.map((s) => [s.id, s]));
  const kids = {};
  for (const s of spans) (kids[s.parent_id] ||= []).push(s);
  for (const k in kids) kids[k].sort((a, b) => a.start - b.start || a.id - b.id);

  const rows = [];
  let researcherN = 0;
  const walk = (parentId, depth) => {
    for (const s of kids[parentId] || []) {
      const parent = byId[s.parent_id];
      // A researcher's model call has the same extent as the researcher: show them as one row.
      const merged = s.name.startsWith("llm:") && parent && parent.name === "researcher";
      if (!merged) {
        const child = (kids[s.id] || []).find((c) => c.name.startsWith("llm:"));
        const mergeChild = s.name === "researcher" && child;
        const row = describe(s, run.mode, s.name === "researcher" ? ++researcherN : 0);
        row.depth = depth;
        row.cost = s.cost_usd + (mergeChild ? child.cost_usd : 0);
        row.searches = s.usage.web_searches + (mergeChild ? child.usage.web_searches : 0);
        row.costAt = row.cost ? s.end : null;
        rows.push(row);
      }
      walk(s.id, merged ? depth : depth + 1);
    }
  };
  walk(null, 0);
  return rows;
}

function describe(s, mode, n) {
  const a = s.attrs || {};
  const base = { span: s, start: s.start, end: s.end, error: s.status !== "ok", title: "", sub: "" };
  const agent = mode === "baseline" ? "base" : "team";
  switch (s.name) {
    case "team": return { ...base, label: "Whole run", kind: "group" };
    case "baseline": return { ...base, label: "Whole run (single agent)", kind: "group" };
    case "research_round": return { ...base, label: `Research round ${a.round ?? ""}`, kind: "group" };
    case "llm:planner": return { ...base, label: "Planner", sub: "splits the question", kind: agent };
    case "researcher":
      return { ...base, label: `Researcher ${n}`, sub: a.sub_question || "", title: a.sub_question || "", kind: agent };
    case "llm:critic": return { ...base, label: "Critic", sub: `${a.items ?? "?"} findings checked`, kind: agent };
    case "llm:writer": return { ...base, label: "Writer", sub: `${a.items ?? "?"} findings to cite`, kind: agent };
    case "llm:baseline": return { ...base, label: "Single agent", sub: "searches, reads and writes alone", kind: agent };
    default: return { ...base, label: s.name, kind: agent };
  }
}

// ---------- Replay tab ----------

function renderRun(run) {
  const rows = buildRows(run);
  const total = Math.max(0.001, ...run.spans.map((s) => s.end));
  current = { run, rows, total, refs: parseRefs(run.report_md) };

  $("#run-mode").className = `badge ${run.mode}`;
  $("#run-mode").textContent = run.mode === "team" ? "multi-agent team" : "single-agent baseline";
  $("#run-question").textContent = run.question;
  renderStats(run);
  renderTimelineSkeleton(rows, total);
  renderFunnel(run);
  renderCosts(run);
  $("#report").innerHTML = markdown(run.report_md, current.refs);
  for (const a of $("#report").querySelectorAll(".cite")) {
    if (current.refs[a.dataset.ref]?.partial) a.classList.add("partial");
  }
  playing = false;
  setTime(total);
}

function renderStats(run) {
  const m = run.metrics;
  const calls = run.spans.filter((s) => s.model).length;
  const searches = run.spans.reduce((n, s) => n + s.usage.web_searches, 0);
  const passed = m.findings_supported + m.findings_partial;
  const stats = [
    [usd(m.cost_usd), "total cost"],
    [secs(m.wall_seconds), "wall time"],
    [String(calls), "Claude calls"],
    [String(searches), "web searches"],
    [run.mode === "team" ? `${passed}/${m.findings_submitted}` : String(m.findings_submitted),
      run.mode === "team" ? "findings passed checks" : "findings (no critic)"],
    [String(m.citations_used), "citations in report"],
  ];
  $("#stats").innerHTML = stats
    .map(([v, k]) => `<div class="stat"><div class="v">${esc(v)}</div><div class="k">${esc(k)}</div></div>`)
    .join("");
}

function renderTimelineSkeleton(rows, total) {
  const html = rows
    .map((r, i) => {
      const left = (r.start / total) * 100;
      const width = Math.max(0.4, ((r.end - r.start) / total) * 100);
      const sub = r.sub ? ` <span class="sub">· ${esc(r.sub)}</span>` : "";
      // Only label bars wide enough to hold the text; the cost table below has every number.
      const tag = r.cost && width > 7 ? `<span class="tag">${usd(r.cost)}</span>` : "";
      const title = esc(r.title || `${r.label} ${r.sub}`.trim());
      return `<div class="row">
        <div class="label" style="padding-left:${r.depth * 14}px" title="${title}">${esc(r.label)}${sub}</div>
        <div class="track"><div class="bar kind-${r.kind}${r.error ? " error" : ""}" id="bar-${i}"
          style="left:${left}%;width:${width}%"><div class="fill"></div>${tag}</div></div>
      </div>`;
    })
    .join("");
  $("#timeline").innerHTML = html + '<div class="playhead" id="playhead"></div>';
}

function setTime(newT) {
  const { rows, total, run } = current;
  t = Math.min(Math.max(0, newT), total);
  rows.forEach((r, i) => {
    const bar = document.getElementById(`bar-${i}`);
    const frac = r.end > r.start ? (t - r.start) / (r.end - r.start) : t >= r.end ? 1 : 0;
    bar.querySelector(".fill").style.width = `${Math.min(1, Math.max(0, frac)) * 100}%`;
    bar.classList.toggle("running", t > r.start && t < r.end && playing);
  });
  // Place the playhead over the bar area, which starts after the label column.
  const track = document.querySelector("#timeline .track");
  const ph = $("#playhead");
  if (track) {
    const box = $("#timeline").getBoundingClientRect();
    const tb = track.getBoundingClientRect();
    ph.style.left = `${tb.left - box.left + (t / total) * tb.width}px`;
    ph.style.display = t > 0 && t < total ? "block" : "none";
  }
  const spent = run.spans.filter((s) => s.end <= t + 1e-9).reduce((x, s) => x + s.cost_usd, 0);
  $("#clock").textContent = `${secs(t)} / ${secs(total)} · ${usd(spent)}`;
  $("#scrub").value = String(Math.round((t / total) * 1000));
  $("#narration").textContent = narrate(run, t, total);
  $("#play").textContent = playing ? "❚❚ Pause" : "▶ Play";
}

function narrate(run, t, total) {
  const m = run.metrics;
  if (t >= total) {
    const passed = m.findings_supported + m.findings_partial;
    return run.mode === "team"
      ? `Done in ${secs(total)} for ${usd(m.cost_usd)}: ${passed} of ${m.findings_submitted} findings passed the ` +
          `grounding and critic checks, and the report cites ${m.citations_used}.`
      : `Done in ${secs(total)} for ${usd(m.cost_usd)}: one agent wrote a report citing ${m.citations_used} findings, ` +
          `with no separate critic.`;
  }
  if (t <= 0) return `Press play to replay this run at about ${Math.round(total / PLAYBACK_SECONDS)}× speed.`;
  const live = run.spans.filter((s) => s.start <= t && t < s.end).map((s) => s.name);
  const researchers = live.filter((n) => n === "researcher").length;
  if (live.includes("llm:planner")) return "The planner is splitting the question into sub-questions.";
  if (researchers > 1) return `${researchers} researchers are searching the web in parallel, one per sub-question.`;
  if (researchers === 1)
    return "One researcher is still working; the others have finished. The round ends when the slowest is done.";
  if (live.includes("llm:critic"))
    return "Code has checked every cited URL against the researchers' own searches. Now the critic judges each claim against its quote.";
  if (live.includes("llm:writer"))
    return "The writer drafts the report from findings that passed. Code then strips any citation to rejected evidence.";
  if (live.includes("llm:baseline")) return "A single agent searches, reads and writes the whole report by itself.";
  return "Between steps.";
}

function frame(now) {
  if (!playing) return;
  const dt = (now - lastFrame) / 1000;
  lastFrame = now;
  setTime(t + dt * (current.total / PLAYBACK_SECONDS));
  if (t >= current.total) {
    playing = false;
    setTime(t);
    return;
  }
  requestAnimationFrame(frame);
}

function play() {
  if (playing) {
    playing = false;
    setTime(t);
    return;
  }
  if (t >= current.total) t = 0;
  playing = true;
  lastFrame = performance.now();
  requestAnimationFrame(frame);
}

function renderFunnel(run) {
  const m = run.metrics;
  const max = Math.max(1, m.findings_submitted);
  const pct = (n) => `${(n / max) * 100}%`;
  const row = (label, segs, n) =>
    `<div class="funnel-row"><div>${label}</div><div class="barbg">${segs
      .filter(([v]) => v > 0)
      .map(([v, cls, tip]) => `<div class="seg ${cls}" style="width:${pct(v)}" title="${esc(tip)}: ${v}"></div>`)
      .join("")}</div><div class="n">${n}</div></div>`;
  const grounded = m.findings_submitted - m.findings_ungrounded;
  let html =
    row("Findings submitted", [[m.findings_submitted, "team", "submitted"]], m.findings_submitted) +
    row(
      "Cited URL came from a real search",
      [[grounded, "ok", "grounded"], [m.findings_ungrounded, "bad", "rejected by code"]],
      grounded,
    );
  if (run.mode === "team") {
    html += row(
      "Critic: quote supports the claim",
      [
        [m.findings_supported, "ok", "supported"],
        [m.findings_partial, "warn", "partially supported"],
        [m.findings_unsupported, "bad", "unsupported (dropped)"],
      ],
      m.findings_supported + m.findings_partial,
    );
  }
  html += row("Cited in the final report", [[m.citations_used, "team", "cited"]], m.citations_used);
  html += `<div class="legend"><span><i class="seg ok"></i>passed</span><span><i class="seg warn"></i>partially supported (kept, hedged)</span><span><i class="seg bad"></i>rejected</span></div>`;
  const notes = [];
  if (run.mode === "baseline") notes.push("The single agent has no critic, so its findings go straight into the report.");
  notes.push(
    m.citations_invalid
      ? `${m.citations_invalid} citation(s) to missing or rejected evidence were stripped from the report.`
      : "No citations had to be stripped from the report.",
  );
  if (m.stopped_by_budget) notes.push("Research stopped early because the budget ran low.");
  html += `<p class="hint">${notes.map(esc).join(" ")}</p>`;
  $("#funnel").innerHTML = html;
}

function renderCosts(run) {
  const roles = {};
  for (const s of run.spans.filter((x) => x.model)) {
    const role = s.name.replace(/^llm:/, "");
    const r = (roles[role] ||= { calls: 0, input: 0, cached: 0, output: 0, searches: 0, cost: 0, models: new Set() });
    const u = s.usage;
    r.calls += 1;
    r.input += u.input_tokens + u.cache_read_tokens + u.cache_write_tokens;
    r.cached += u.cache_read_tokens;
    r.output += u.output_tokens;
    r.searches += u.web_searches;
    r.cost += s.cost_usd;
    r.models.add(s.model);
  }
  const total = Object.values(roles).reduce((x, r) => x + r.cost, 0) || 1;
  const k = (n) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));
  const body = Object.entries(roles)
    .sort((a, b) => b[1].cost - a[1].cost)
    .map(
      ([role, r]) => `<tr><td>${esc(role)}<div class="hint" style="margin:0">${esc([...r.models].join(", "))}</div></td>
        <td class="num">${r.calls}</td><td class="num">${r.searches}</td>
        <td class="num">${k(r.input)}${r.cached ? ` <span class="muted">(${Math.round((r.cached / r.input) * 100)}% cached)</span>` : ""}</td>
        <td class="num">${k(r.output)}</td>
        <td class="num">${usd(r.cost, 3)} <span class="muted">${Math.round((r.cost / total) * 100)}%</span></td></tr>`,
    )
    .join("");
  $("#costs").innerHTML = `<table><thead><tr><th>Role</th><th class="num">Calls</th><th class="num">Searches</th>
    <th class="num">Tokens in</th><th class="num">Tokens out</th><th class="num">Cost</th></tr></thead><tbody>${body}</tbody></table>
    <p class="hint">Costs come from token counts in the API responses, priced in <code>pricing.py</code>.</p>`;
}

// ---------- Citation popover ----------

let pop;
function closePop() {
  pop?.remove();
  pop = null;
}
function openPop(a) {
  closePop();
  const ref = current.refs[a.dataset.ref];
  pop = document.createElement("div");
  pop.className = "pop";
  pop.innerHTML = ref
    ? `<a class="src" href="${esc(ref.url)}" target="_blank" rel="noopener noreferrer">${esc(ref.title)} ↗</a>
       <q>${esc(ref.quote)}</q>
       <span class="verdict" style="color:var(${ref.partial ? "--warn" : "--ok"})">${
         ref.partial ? "Critic: partially supported (the report hedges this claim)" : "Critic: supported by the quote"
       }</span>
       <a href="#ref-${esc(a.dataset.ref)}" data-jump="${esc(a.dataset.ref)}">Jump to reference</a>`
    : `<span>${esc(a.dataset.ref)} is not in this report's references.</span>`;
  document.body.appendChild(pop);
  const r = a.getBoundingClientRect();
  const left = Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - pop.offsetWidth - 12);
  pop.style.left = `${Math.max(8, left)}px`;
  pop.style.top = `${window.scrollY + r.bottom + 6}px`;
}

document.addEventListener("click", (e) => {
  const cite = e.target.closest(".cite:not(.demo)");
  const jump = e.target.closest("[data-jump]");
  if (cite) {
    e.preventDefault();
    openPop(cite);
  } else if (jump) {
    e.preventDefault();
    const li = document.getElementById(`ref-${jump.dataset.jump}`);
    closePop();
    if (li) {
      li.scrollIntoView({ block: "center" });
      li.classList.add("flash");
      setTimeout(() => li.classList.remove("flash"), 1600);
    }
  } else if (pop && !e.target.closest(".pop")) {
    closePop();
  }
});
document.addEventListener("keydown", (e) => e.key === "Escape" && closePop());

// ---------- Eval tab ----------

function renderEval() {
  const runs = Object.fromEntries(bundle.runs.map((r) => [r.id, r]));
  const parts = bundle.evals.map((ev) => {
    const qs = ev.questions;
    const wins = { team: 0, baseline: 0, tie: 0 };
    for (const q of qs) wins[q.outcome] += 1;
    const mean = (side, f) => qs.reduce((x, q) => x + runs[q[`${side}_run`]].metrics[f], 0) / (qs.length || 1);
    const rate = (side, num, den) => {
      const d = qs.reduce((x, q) => x + runs[q[`${side}_run`]].metrics[den], 0);
      return d ? `${Math.round((qs.reduce((x, q) => x + runs[q[`${side}_run`]].metrics[num], 0) / d) * 100)}%` : "n/a";
    };
    const card = (title, team, base, note = "") =>
      `<div class="stat"><div class="k">${title}</div><div class="versus"><span class="t">${team}</span>
       <span class="muted" style="font-size:14px">vs</span><span class="b">${base}</span></div>${note ? `<div class="k">${note}</div>` : ""}</div>`;

    const items = qs
      .map((q, i) => {
        const tm = runs[q.team_run].metrics;
        const bm = runs[q.baseline_run].metrics;
        const label = { team: "team wins", baseline: "single agent wins", tie: "tie" }[q.outcome];
        return `<details class="qrow"><summary class="qline">
            <span class="muted">Q${i + 1}</span><span>${esc(q.question)}</span>
            <span><span class="badge ${q.outcome}">${label}</span></span>
            <span class="side">${usd(tm.cost_usd)} · ${secs(tm.wall_seconds)} · ${tm.citations_used} cited</span>
            <span class="side">${usd(bm.cost_usd)} · ${secs(bm.wall_seconds)} · ${bm.citations_used} cited</span>
          </summary>
          <div class="judgments">
            <div class="judgment"><h3>Judge, order 1 (team shown as report A)</h3>${esc(q.judgments.team_as_a)}</div>
            <div class="judgment"><h3>Judge, order 2 (team shown as report B)</h3>${esc(q.judgments.team_as_b)}</div>
          </div>
          <div class="qlinks"><a href="#run=${encodeURIComponent(q.team_run)}">Replay the team run →</a>
            <a href="#run=${encodeURIComponent(q.baseline_run)}">Replay the single-agent run →</a></div>
        </details>`;
      })
      .join("");

    return `<article class="card">
      <h2>Does the team beat one agent? <span class="muted">(${esc(ev.id)})</span></h2>
      <p class="hint" style="margin-top:0">${esc(EVAL_NOTES[ev.id] || "")} A pairwise judge compares the two reports
        twice, swapping their positions; a side only wins if it wins in both orders, which cancels position bias.</p>
      <div class="legend" style="margin-bottom:12px"><span><i class="seg team"></i>team</span>
        <span><i style="background:var(--base)"></i>single agent</span></div>
      <div class="eval-cards">
        ${card("Judge wins (both orders)", wins.team, wins.baseline, wins.tie ? `${wins.tie} ties` : "0 ties")}
        ${card("Mean cost per question", usd(mean("team", "cost_usd")), usd(mean("baseline", "cost_usd")))}
        ${card("Mean wall time", secs(mean("team", "wall_seconds")), secs(mean("baseline", "wall_seconds")))}
        ${card("Findings citing an unsearched URL", rate("team", "findings_ungrounded", "findings_submitted"),
          rate("baseline", "findings_ungrounded", "findings_submitted"))}
      </div>
      <div class="qline qhead"><span></span><span>Question (click for the judge's reasoning)</span><span>Verdict</span>
        <span class="side">Team</span><span class="side">Single agent</span></div>
      ${items}
    </article>`;
  });

  $("#eval").innerHTML =
    parts.join("") +
    `<article class="card"><h2>What the results say</h2><ul class="takeaways">
      <li><strong>The team lost on coverage, not accuracy.</strong> In each loss the judge called the team's report the
        more faithful one, but it missed central topics. With two sub-questions and no follow-up round, the planner's
        split decided what got researched, and nothing caught the gaps.</li>
      <li><strong>The team won where faithfulness decided it.</strong> On sodium-ion batteries and four-day weeks, the
        judge preferred the team for tying claims to quotes and flagging partial support.</li>
      <li><strong>Neither side cited a URL its searches didn't return.</strong> On current models, coverage is the
        bigger lever than catching made-up citations.</li>
      <li><strong>Next experiments:</strong> turn the critic's follow-up round back on, ask the planner for coverage
        explicitly, and re-measure cost with prompt caching. Five questions and a 2-3 split are not statistically
        significant; the point of the harness is that each change can now be measured.</li>
    </ul></article>`;
}

// ---------- Routing and boot ----------

function populatePicker() {
  const sel = $("#run-select");
  const evalRunIds = new Set();
  const groups = [];
  for (const ev of bundle.evals) {
    const opts = ev.questions.flatMap((q, i) => {
      evalRunIds.add(q.team_run);
      evalRunIds.add(q.baseline_run);
      return [
        [q.team_run, `Q${i + 1} · team · ${short(q.question, 60)}`],
        [q.baseline_run, `Q${i + 1} · single agent · ${short(q.question, 60)}`],
      ];
    });
    groups.push([`Eval ${ev.id} (${ev.questions.length} questions)`, opts]);
  }
  const single = bundle.runs
    .filter((r) => !evalRunIds.has(r.id))
    .map((r) => [r.id, LABELS[r.id] || `${r.mode} · ${short(r.question, 60)}`]);
  groups.unshift(["Single runs", single]);
  sel.innerHTML = groups
    .filter(([, opts]) => opts.length)
    .map(
      ([label, opts]) =>
        `<optgroup label="${esc(label)}">${opts.map(([id, text]) => `<option value="${esc(id)}">${esc(text)}</option>`).join("")}</optgroup>`,
    )
    .join("");
  sel.addEventListener("change", () => (location.hash = `run=${encodeURIComponent(sel.value)}`));
}

function route() {
  closePop();
  const hash = decodeURIComponent(location.hash.slice(1));
  const tab = hash === "eval" ? "eval" : "replay";
  $("#tab-replay").hidden = tab !== "replay";
  $("#tab-eval").hidden = tab !== "eval";
  for (const a of document.querySelectorAll(".tabs a")) a.setAttribute("aria-selected", String(a.dataset.tab === tab));
  if (tab === "replay") {
    const id = hash.startsWith("run=") ? hash.slice(4) : bundle.runs[0].id;
    const run = bundle.runs.find((r) => r.id === id) || bundle.runs[0];
    $("#run-select").value = run.id;
    if (!current || current.run.id !== run.id) renderRun(run);
    window.scrollTo(0, 0);
  }
}

async function boot() {
  try {
    const res = await fetch("data/bundle.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    bundle = await res.json();
  } catch (err) {
    document.querySelector("main").innerHTML =
      `<p class="card">Could not load <code>data/bundle.json</code> (${esc(err.message)}). Build it with
       <code>factcheck site</code>; see the README.</p>`;
    return;
  }
  populatePicker();
  renderEval();
  $("#play").addEventListener("click", play);
  $("#restart").addEventListener("click", () => {
    playing = false;
    setTime(0);
  });
  $("#scrub").addEventListener("input", (e) => {
    playing = false;
    setTime((Number(e.target.value) / 1000) * current.total);
  });
  window.addEventListener("resize", () => current && setTime(t));
  window.addEventListener("hashchange", route);
  route();
}

boot();
