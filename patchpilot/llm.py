"""Anthropic call: ask for a diagnosis and a fixed program as strict JSON."""
from __future__ import annotations

import json
import os
import re

DEFAULT_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You are PatchPilot, an expert Python debugger.
You get a Python program and the output of running it (an error, or a failing assertion).
Reply with ONLY a JSON object, no markdown fences, no prose:
{"diagnosis": "<short explanation of the root cause>", "fixed_code": "<the complete corrected program>"}
Rules: return the full program, not a diff. Fix the bug in the code, never edit assertions
or tests to make them pass. Keep changes minimal. Use only the standard library."""


def get_model() -> str:
    return _secret("PATCHPILOT_MODEL") or DEFAULT_MODEL


def get_api_key() -> str | None:
    return _secret("ANTHROPIC_API_KEY")


def _secret(name: str) -> str | None:
    val = os.environ.get(name)
    if val:
        return val
    try:
        import streamlit as st

        val = st.secrets.get(name)
        return str(val) if val else None
    except Exception:
        return None


def parse_response(text: str) -> dict:
    """Defensively extract {diagnosis, fixed_code} from model text."""
    text = text.strip()
    candidates = [text]
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        candidates.append(fence.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for c in candidates:
        try:
            data = json.loads(c)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("fixed_code"), str):
            return {
                "diagnosis": str(data.get("diagnosis", "")).strip(),
                "fixed_code": data["fixed_code"],
            }
    # Last resort: a bare python code fence.
    code = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if code:
        return {"diagnosis": "(model returned code without a diagnosis)", "fixed_code": code.group(1)}
    raise ValueError("Could not parse model response as JSON")


def diagnose_and_fix(code: str, run_output: str, history: list[dict] | None = None) -> dict:
    """Return {"diagnosis": str, "fixed_code": str}."""
    import anthropic

    client = anthropic.Anthropic(api_key=get_api_key())
    prior = ""
    if history:
        prior = "\n\nPrevious failed attempts (do not repeat them):\n" + "\n".join(
            f"- Attempt {h['attempt']}: {h['diagnosis']} -> still failing with: {h['output'][-300:]}"
            for h in history
        )
    user = (
        f"Program:\n```python\n{code}\n```\n\nRun output (stdout+stderr):\n```\n{run_output}\n```"
        f"{prior}\n\nReturn the JSON object now."
    )
    resp = client.messages.create(
        model=get_model(),
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return parse_response(text)
