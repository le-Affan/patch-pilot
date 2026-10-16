"""HTML builders for the UI. Pure functions: data in, HTML string out."""
from __future__ import annotations

import difflib
import re
from html import escape
from pathlib import Path

REPO_URL = "https://github.com/le-Affan/patch-pilot"

LOGO = (
    '<svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">'
    '<rect width="28" height="28" rx="7" fill="#5b9bf5"/>'
    '<path d="M9 14h10M14 9v10" stroke="#08101c" stroke-width="2.2" stroke-linecap="round"/>'
    "</svg>"
)


def css() -> str:
    return "<style>" + (Path(__file__).parent / "styles.css").read_text(encoding="utf-8") + "</style>"


def wordmark() -> str:
    return (
        '<div class="pp-head"><div class="pp-brand">' + LOGO +
        '<div><div class="name">PatchPilot</div>'
        '<div class="tag">Runs your broken Python, diagnoses the failure, patches it, and re-runs until it passes.</div></div></div>'
        '<span class="pp-pill">Demo only &middot; do not paste sensitive code</span></div>'
    )


def side_section(label: str, first: bool = False) -> str:
    return f'<div class="pp-side-section{" first" if first else ""}">{escape(label)}</div>'


def usage_meter(used: int, total: int) -> str:
    segs = "".join(
        f'<span class="{"full" if used >= total else "on"}"></span>' if i < used else "<span></span>"
        for i in range(total)
    )
    return f'<div class="pp-meter">{segs}</div><div class="pp-meta">{used} of {total} repair runs used</div>'


def model_badge(model: str | None, replay: bool) -> str:
    if replay:
        return '<span class="pp-badge">replay mode</span><div class="pp-meta" style="margin-top:8px">No API key set. Samples replay recorded fixes.</div>'
    return f'<span class="pp-badge">{escape(model or "")}</span>'


def editor_bar(lines: int, max_lines: int) -> str:
    over = " over" if lines > max_lines else ""
    return (
        '<div class="pp-editor-bar"><span class="file"><i></i>main.py</span>'
        f'<span class="count{over}">{lines} / {max_lines} lines</span></div>'
    )


def panel_title(text: str) -> str:
    return f'<div class="pp-panel-title">{escape(text)}</div>'


def notice(msg: str, kind: str = "warn") -> str:
    cls = {"warn": "", "err": " err", "info": " info"}[kind]
    return f'<div class="pp-notice{cls}">{escape(msg)}</div>'


def empty_state() -> str:
    return (
        '<div class="pp-empty"><h3>No runs yet</h3>'
        "<p>Results appear here as the agent works.</p><ol>"
        "<li><b>01</b>Pick a sample or paste Python into the editor</li>"
        "<li><b>02</b>Press Fix it. The agent runs the code and reads the failure</li>"
        "<li><b>03</b>Each attempt shows its diagnosis, patch and result until the code passes</li>"
        "</ol></div>"
    )


def code_block(text: str, err: bool = False) -> str:
    # U+200B on empty lines keeps the markdown HTML block from ending early.
    safe = "\n".join(line if line.strip() else "​" for line in escape(text.rstrip("\n")).split("\n"))
    return f'<pre class="pp-code{" err" if err else ""}">{safe or "&nbsp;"}</pre>'


CHEV = '<span class="pp-chev"></span>'
_STATUS = {"passed": "Passed", "failed": "Failed", "running": "Running"}


def _status(status: str) -> str:
    return f'<span class="pp-status {status}">{_STATUS[status]}</span>'


def step(s: dict) -> str:
    """s: status, title, diag, error, code, output (all optional but status/title)."""
    status = s["status"]
    expandable = status != "running" and bool(s.get("error") or s.get("code"))
    chev = CHEV if expandable else ""
    head = (
        f'<div class="pp-sum-row"><span class="pp-sum-left">{chev}<span class="pp-sum-title">{escape(s["title"])}</span></span>{_status(status)}</div>'
        + (f'<div class="pp-sum-diag">{escape(s["diag"])}</div>' if s.get("diag") else "")
    )
    if status == "running":
        card = f'<div class="pp-card"><div class="pp-sum">{head}<div class="pp-progress"></div></div></div>'
    else:
        parts = []
        if s.get("error"):
            parts.append(f'<div><div class="pp-lbl">Error</div>{code_block(s["error"], err=True)}</div>')
        if s.get("code"):
            parts.append(f'<div><div class="pp-lbl">Patched code</div>{code_block(s["code"])}</div>')
        if s.get("output") is not None and s.get("code"):
            parts.append(f'<div><div class="pp-lbl">Output</div>{code_block(s["output"] or "(no output)")}</div>')
        if parts:
            card = f'<details class="pp-card"><summary>{head}</summary><div class="pp-body">{"".join(parts)}</div></details>'
        else:
            card = f'<div class="pp-card"><div class="pp-sum">{head}</div></div>'
    return f'<div class="pp-step {status}"><span class="pp-dot"></span>{card}</div>'


def timeline(steps: list[dict]) -> str:
    return '<div class="pp-tl"><div class="pp-tl-title">Attempt log</div>' + "".join(step(s) for s in steps) + "</div>"


def banner(passed: bool, attempts: int, max_attempts: int = 4) -> str:
    if passed:
        title = "Already passing" if attempts == 0 else f"Fixed in {attempts} attempt{'s' if attempts != 1 else ''}"
        cls = "ok"
    else:
        title, cls = "Could not fix", "bad"
    meta = f"{attempts} of {max_attempts} attempts used"
    return f'<div class="pp-banner {cls}"><span class="dot"></span><span class="t">{title}</span><span class="m">{meta}</span></div>'


_HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def diff_html(a: str, b: str) -> str:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(), "original.py", "fixed.py", n=3, lineterm=""))
    if not lines:
        return '<div class="pp-notice info">No changes.</div>'
    rows, old, new = [], 0, 0
    for ln in lines[2:]:
        m = _HUNK.match(ln)
        if m:
            old, new = int(m.group(1)), int(m.group(2))
            rows.append(f'<tr class="hunk"><td colspan="4">{escape(ln)}</td></tr>')
        elif ln.startswith("+"):
            rows.append(f'<tr class="add"><td class="n"></td><td class="n">{new}</td><td class="s">+</td><td class="c">{escape(ln[1:]) or "&#8203;"}</td></tr>')
            new += 1
        elif ln.startswith("-"):
            rows.append(f'<tr class="del"><td class="n">{old}</td><td class="n"></td><td class="s">&minus;</td><td class="c">{escape(ln[1:]) or "&#8203;"}</td></tr>')
            old += 1
        else:
            rows.append(f'<tr><td class="n">{old}</td><td class="n">{new}</td><td class="s"></td><td class="c">{escape(ln[1:]) or "&#8203;"}</td></tr>')
            old += 1
            new += 1
    return f'<div class="pp-diff"><div class="pp-diff-scroll"><table class="pp-dt">{"".join(rows)}</table></div></div>'


def side_by_side(original: str, fixed: str) -> str:
    return (
        '<div class="pp-split">'
        f'<div><div class="pp-lbl">Original</div>{code_block(original)}</div>'
        f'<div><div class="pp-lbl">Fixed</div>{code_block(fixed)}</div></div>'
    )


def footer() -> str:
    return (
        '<div class="pp-foot"><span>PatchPilot &middot; demo project, Python only, not a hardened sandbox</span>'
        f'<a href="{REPO_URL}" target="_blank" rel="noopener">le-Affan/patch-pilot</a></div>'
    )
