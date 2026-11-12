"""Windows Smart App Control: a blocked uv tool runs again through its own Python."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts"))
import post  # noqa: E402


class Blocked(OSError):
    """What subprocess raises on Windows when Smart App Control refuses a program."""

    winerror = post.BLOCKED_BY_APP_CONTROL


def tool_environment(tools: Path, name: str) -> Path:
    scripts = tools / name / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / f"{name}.exe").write_bytes(b"")
    (scripts / "python.exe").write_bytes(b"")
    return scripts / "python.exe"


def refusing(blocked: str, calls: list[list[str]]) -> Any:
    def fake_run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == blocked:
            raise Blocked("Smart App Control blocked the file")
        return subprocess.CompletedProcess(command, 0, "", "")
    return fake_run


def test_a_blocked_tool_runs_through_the_python_of_its_uv_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    python = tool_environment(tmp_path, "yt-dlp")
    calls: list[list[str]] = []
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing("yt-dlp", calls))

    done = post.run(["yt-dlp", "--version"], capture_output=True, text=True)

    assert done.returncode == 0
    assert calls == [["yt-dlp", "--version"], [str(python), "-c", post.CONSOLE_SCRIPT, "yt-dlp", "--version"]]


def test_a_blocked_tool_without_a_uv_environment_is_still_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing("ffmpeg", []))

    with pytest.raises(Blocked):
        post.run(["ffmpeg", "-version"])


def test_a_missing_tool_is_not_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tool_environment(tmp_path, "yt-dlp")
    calls: list[list[str]] = []

    def missing(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        raise FileNotFoundError(command[0])

    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(FileNotFoundError):
        post.run(["yt-dlp", "--version"])
    assert len(calls) == 1


def test_the_console_script_runner_starts_a_real_entry_point() -> None:
    # pytest's own console script, run by name the way the fallback runs yt-dlp.
    done = subprocess.run([sys.executable, "-c", post.CONSOLE_SCRIPT, "pytest", "--version"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert "pytest" in (done.stdout + done.stderr)
