"""Run untrusted Python in a subprocess. Demo-grade isolation only."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 8000


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        parts = []
        if self.stdout.strip():
            parts.append(self.stdout.rstrip())
        if self.stderr.strip():
            parts.append(self.stderr.rstrip())
        if self.timed_out:
            parts.append(f"[timed out after {TIMEOUT_SECONDS}s]")
        return "\n".join(parts)


def _clip(text: str) -> str:
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + "\n...[truncated]"
    return text


def run_code(code: str, timeout: int = TIMEOUT_SECONDS) -> RunResult:
    """Execute code in a fresh temp dir with a minimal environment."""
    with tempfile.TemporaryDirectory(prefix="patchpilot_") as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": tmp,
            "TMPDIR": tmp,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        try:
            proc = subprocess.run(
                [sys.executable, "-I", path],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
            )
            return RunResult(_clip(proc.stdout), _clip(proc.stderr), proc.returncode)
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return RunResult(_clip(out), _clip(err), -1, timed_out=True)
