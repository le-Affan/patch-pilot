"""The repair loop: run -> diagnose -> patch -> re-run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator

from .sandbox import RunResult, run_code

MAX_ATTEMPTS = 4

Fixer = Callable[[str, str, list], dict]


@dataclass
class Event:
    kind: str  # initial_run | attempt | done
    attempt: int = 0
    code: str = ""
    output: str = ""
    diagnosis: str = ""
    passed: bool = False
    original: str = ""
    error: str = ""
    extra: dict = field(default_factory=dict)


def repair(code: str, fixer: Fixer, max_attempts: int = MAX_ATTEMPTS) -> Iterator[Event]:
    """Yield step events. `fixer(code, output, history)` -> {diagnosis, fixed_code}."""
    max_attempts = max(1, min(MAX_ATTEMPTS, max_attempts))
    original = code
    result: RunResult = run_code(code)
    yield Event("initial_run", code=code, output=result.output, passed=result.ok)
    if result.ok:
        yield Event("done", code=code, output=result.output, passed=True, original=original)
        return

    history: list[dict] = []
    for n in range(1, max_attempts + 1):
        try:
            fix = fixer(code, result.output, history)
        except Exception as e:  # LLM/network/parse failure
            yield Event("attempt", attempt=n, code=code, output=result.output, error=str(e) if type(e).__name__ == "LLMError" else f"{type(e).__name__}: {e}")
            break
        new_code = fix["fixed_code"]
        new_result = run_code(new_code)
        history.append({"attempt": n, "diagnosis": fix["diagnosis"], "output": new_result.output})
        yield Event(
            "attempt",
            attempt=n,
            code=new_code,
            output=new_result.output,
            diagnosis=fix["diagnosis"],
            passed=new_result.ok,
            extra={"error_before": result.output},
        )
        code, result = new_code, new_result
        if result.ok:
            break

    yield Event("done", code=code, output=result.output, passed=result.ok, original=original)
