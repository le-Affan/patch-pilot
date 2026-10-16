import difflib

import streamlit as st

from patchpilot.agent import repair
from patchpilot.llm import diagnose_and_fix, get_api_key, get_model
from patchpilot.samples import SAMPLES, recorded_fixer_for

MAX_LINES = 200
MAX_RUNS = 5

st.set_page_config(page_title="PatchPilot", page_icon="🛠️", layout="wide")
st.session_state.setdefault("runs", 0)

st.title("🛠️ PatchPilot")
st.caption("An autonomous agent that runs your buggy Python, diagnoses the failure, patches it, and re-runs until it passes.")
st.warning("Demo only. Do not paste sensitive code or secrets. Code runs in a basic subprocess, not a hardened sandbox.")

has_key = bool(get_api_key())
if not has_key:
    st.info("No `ANTHROPIC_API_KEY` configured. Running in **replay mode**: the built-in samples use pre-recorded fixes.")

with st.sidebar:
    st.header("Settings")
    choice = st.selectbox("Sample program", ["(custom)"] + list(SAMPLES))
    max_attempts = st.slider("Max attempts", 1, 4, 4)
    st.caption(f"Repair runs used: {st.session_state.runs}/{MAX_RUNS}")
    if has_key:
        st.caption(f"Model: `{get_model()}`")

default = SAMPLES[choice]["code"] if choice in SAMPLES else ""
# Reset the editor when the sample selection changes.
if st.session_state.get("_last_choice") != choice:
    st.session_state["_last_choice"] = choice
    st.session_state["code"] = default

code = st.text_area("Buggy Python code", key="code", height=300)
go = st.button("Fix it", type="primary")


def unified(a: str, b: str) -> str:
    return "".join(
        difflib.unified_diff(
            a.splitlines(keepends=True), b.splitlines(keepends=True), "original.py", "fixed.py"
        )
    )


if go:
    if not code.strip():
        st.error("Paste some code or pick a sample.")
        st.stop()
    if len(code.splitlines()) > MAX_LINES:
        st.error(f"Input too long. Max {MAX_LINES} lines.")
        st.stop()
    if st.session_state.runs >= MAX_RUNS:
        st.error(f"Demo limit reached ({MAX_RUNS} repair runs per session). Refresh to start over.")
        st.stop()

    if has_key:
        fixer = diagnose_and_fix
    else:
        fixer = recorded_fixer_for(code)
        if fixer is None:
            st.error("Replay mode only supports the built-in samples. Configure `ANTHROPIC_API_KEY` to fix custom code.")
            st.stop()

    st.session_state.runs += 1
    st.subheader("Live log")
    final = None
    for ev in repair(code, fixer, max_attempts):
        if ev.kind == "initial_run":
            if ev.passed:
                st.success("Code already runs cleanly. Nothing to fix.")
            else:
                with st.expander("Initial run: failed", expanded=True):
                    st.code(ev.output, language="text")
        elif ev.kind == "attempt":
            badge = "✅ passed" if ev.passed else "❌ still failing"
            with st.expander(f"Attempt {ev.attempt}: {badge}", expanded=True):
                if ev.error:
                    st.error(f"Agent error: {ev.error}")
                    continue
                st.markdown("**Error before patch**")
                st.code(ev.extra.get("error_before", ""), language="text")
                st.markdown("**Diagnosis**")
                st.write(ev.diagnosis)
                st.markdown("**Patched code**")
                st.code(ev.code, language="python")
                st.markdown("**Run output**")
                st.code(ev.output or "(no output)", language="text")
        elif ev.kind == "done":
            final = ev

    if final:
        st.subheader("Result")
        if final.passed:
            st.success("SUCCESS: code now runs cleanly.")
        else:
            st.error("FAILED: could not fix within the attempt limit.")
        left, right = st.columns(2)
        left.markdown("**Original**")
        left.code(final.original, language="python")
        right.markdown("**Fixed**")
        right.code(final.code, language="python")
        st.markdown("**Unified diff**")
        st.code(unified(final.original, final.code) or "(no changes)", language="diff")
        st.markdown("**Final run output**")
        st.code(final.output or "(no output)", language="text")
