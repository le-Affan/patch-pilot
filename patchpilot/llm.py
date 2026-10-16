"""OpenRouter call: ask for a diagnosis and a fixed program as strict JSON."""
from __future__ import annotations

import json
import os
import re

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are PatchPilot, an expert Python debugger.
You get a Python program and the output of running it (an error, or a failing assertion).
Reply with ONLY a JSON object, no markdown fences, no prose:
{"diagnosis": "<short explanation of the root cause>", "fixed_code": "<the complete corrected program>"}
Rules: return the full program, not a diff. Fix the bug in the code, never edit assertions
or tests to make them pass. Keep changes minimal. Use only the standard library."""


def get_model() -> str:
    return _secret("PATCHPILOT_MODEL") or DEFAULT_MODEL


def get_api_key() -> str | None:
    return _secret("OPENROUTER_API_KEY")


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
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
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


class LLMError(Exception):
    """Friendly, user-displayable LLM failure."""


def diagnose_and_fix(code: str, run_output: str, history: list[dict] | None = None) -> dict:
    """Return {"diagnosis": str, "fixed_code": str}. Raises LLMError with a friendly message."""
    import openai

    client = openai.OpenAI(api_key=get_api_key(), base_url=BASE_URL, timeout=90, max_retries=1)
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
    try:
        resp = client.chat.completions.create(
            model=get_model(),
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
        )
    except openai.AuthenticationError:
        raise LLMError("OpenRouter rejected the API key. Check OPENROUTER_API_KEY.") from None
    except openai.RateLimitError:
        raise LLMError("OpenRouter rate limit hit. Wait a moment and try again.") from None
    except openai.NotFoundError:
        raise LLMError(f"Model `{get_model()}` not found on OpenRouter. Check PATCHPILOT_MODEL.") from None
    except openai.APIConnectionError:
        raise LLMError("Could not reach OpenRouter. Check your network and try again.") from None
    except openai.APIError as e:
        raise LLMError(f"OpenRouter error: {getattr(e, 'message', e)}") from None
    text = (resp.choices[0].message.content or "") if resp.choices else ""
    try:
        return parse_response(text)
    except ValueError:
        raise LLMError("The model returned a response that was not valid JSON.") from None
