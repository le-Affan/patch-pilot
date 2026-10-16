import streamlit as st

from patchpilot import components as ui
from patchpilot.agent import repair
from patchpilot.llm import diagnose_and_fix, get_api_key, get_model
from patchpilot.samples import SAMPLES, recorded_fixer_for

MAX_LINES = 200
MAX_RUNS = 5

st.set_page_config(page_title="PatchPilot", page_icon=None, layout="wide", initial_sidebar_state="expanded")
st.html(ui.css())
st.session_state.setdefault("runs", 0)
st.session_state.setdefault("steps", [])
st.session_state.setdefault("final", None)

has_key = bool(get_api_key())
names = list(SAMPLES)

# ---------------- sidebar ----------------
with st.sidebar:
    st.html(ui.side_section("Input", first=True))
    choice = st.selectbox("Sample program", names + ["(custom)"], index=0)
    st.html(ui.side_section("Agent"))
    max_attempts = st.slider("Max attempts", 1, 4, 4)
    st.html(ui.side_section("Usage"))
    meter_ph = st.empty()
    meter_ph.html(ui.usage_meter(st.session_state.runs, MAX_RUNS))
    st.html(ui.side_section("Model"))
    st.html(ui.model_badge(get_model() if has_key else None, replay=not has_key))

default = SAMPLES[choice]["code"] if choice in SAMPLES else ""
# Reset the editor when the sample selection changes.
if st.session_state.get("_last_choice") != choice:
    st.session_state["_last_choice"] = choice
    st.session_state["code"] = default

# ---------------- header ----------------
st.markdown(ui.wordmark(), unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

with left:
    st.html(ui.panel_title("Editor"))
    st.html(ui.editor_bar(len(st.session_state.get("code", "").splitlines()), MAX_LINES))
    code = st.text_area(
        "Buggy Python code",
        key="code",
        height=440,
        label_visibility="collapsed",
        placeholder="Paste Python here, or pick a sample in the sidebar.",
    )
    st.html('<div class="pp-actions"></div>')
    at_cap = st.session_state.runs >= MAX_RUNS
    go = st.button("Fix it", type="primary", disabled=at_cap)

with right:
    st.html(ui.panel_title("Results"))
    notice_ph = st.empty()
    banner_ph = st.empty()
    tabs_ct = st.container()
    log_ph = st.empty()


def render_final(final: dict, n_attempts: int, max_n: int) -> None:
    banner_ph.html(ui.banner(final["passed"], n_attempts, max_n))
    with tabs_ct:
        t_diff, t_cmp, t_out = st.tabs(["Diff", "Original vs Fixed", "Output"])
        with t_diff:
            st.html(ui.diff_html(final["original"], final["code"]))
        with t_cmp:
            st.html(ui.side_by_side(final["original"], final["code"]))
        with t_out:
            st.html(ui.code_block(final["output"] or "(no output)"))


def attempt_count(steps: list) -> int:
    return sum(1 for s in steps if s["title"].startswith("Attempt"))


def problem(msg: str):
    notice_ph.html(ui.notice(msg, "err"))
    log_ph.html("")


if go:
    problem_msg = None
    if not code.strip():
        problem_msg = "Paste some code or pick a sample."
    elif len(code.splitlines()) > MAX_LINES:
        problem_msg = f"Input too long. Max {MAX_LINES} lines."
    elif st.session_state.runs >= MAX_RUNS:
        problem_msg = f"Demo limit reached ({MAX_RUNS} repair runs per session). Refresh to start over."
    fixer = None
    if problem_msg is None:
        fixer = diagnose_and_fix if has_key else recorded_fixer_for(code)
        if fixer is None:
            problem_msg = "Replay mode only supports the built-in samples. Set OPENROUTER_API_KEY to fix custom code."

    if problem_msg:
        problem(problem_msg)
    else:
        st.session_state.runs += 1
        meter_ph.html(ui.usage_meter(st.session_state.runs, MAX_RUNS))
        steps: list[dict] = []
        st.session_state.final = None

        def draw(running_title: str | None = None):
            shown = list(steps)
            if running_title:
                shown.append({"status": "running", "title": running_title, "diag": "Working..."})
            log_ph.html(ui.timeline(shown))

        draw("Initial run")
        final = None
        for ev in repair(code, fixer, max_attempts):
            if ev.kind == "initial_run":
                lines = ev.output.strip().splitlines()
                steps.append({
                    "status": "passed" if ev.passed else "failed",
                    "title": "Initial run",
                    "diag": "Exited cleanly" if ev.passed else (lines[-1] if lines else "Failed"),
                    "error": None if ev.passed else ev.output,
                })
                if not ev.passed:
                    draw("Attempt 1")
            elif ev.kind == "attempt":
                if ev.error:
                    steps.append({"status": "failed", "title": f"Attempt {ev.attempt}", "diag": ev.error})
                else:
                    steps.append({
                        "status": "passed" if ev.passed else "failed",
                        "title": f"Attempt {ev.attempt}",
                        "diag": ev.diagnosis,
                        "error": ev.extra.get("error_before", ""),
                        "code": ev.code,
                        "output": ev.output,
                    })
                    if not ev.passed and ev.attempt < max_attempts:
                        draw(f"Attempt {ev.attempt + 1}")
            elif ev.kind == "done":
                final = {"passed": ev.passed, "code": ev.code, "original": ev.original, "output": ev.output}
        draw()
        if final:
            st.session_state.steps, st.session_state.final = steps, final
            render_final(final, attempt_count(steps), max_attempts)
elif st.session_state.final:
    log_ph.html(ui.timeline(st.session_state.steps))
    render_final(st.session_state.final, attempt_count(st.session_state.steps), max_attempts)
else:
    if at_cap:
        notice_ph.html(ui.notice(f"Demo limit reached ({MAX_RUNS} repair runs per session). Refresh to start over.", "err"))
    log_ph.html(ui.empty_state())

if at_cap and (go or st.session_state.final):
    notice_ph.html(ui.notice(f"Demo limit reached ({MAX_RUNS} repair runs per session). Refresh to start over.", "info"))

st.html(ui.footer())
