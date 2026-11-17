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


def tool_environment(tools: Path, name: str, program: str | None = None) -> Path:
    """A uv tool environment called name whose Scripts holds program (name by default)."""
    scripts = tools / name / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / f"{program or name}.exe").write_bytes(b"")
    (scripts / "python.exe").write_bytes(b"")
    return scripts / "python.exe"


def refusing(blocked: set[str], calls: list[list[str]]) -> Any:
    def fake_run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] in blocked:
            raise Blocked("Smart App Control blocked the file")
        return subprocess.CompletedProcess(command, 0, "", "")
    return fake_run


def test_a_blocked_tool_runs_through_the_python_of_its_uv_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    python = tool_environment(tmp_path, "yt-dlp")
    calls: list[list[str]] = []
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing({"yt-dlp"}, calls))

    done = post.run(["yt-dlp", "--version"], capture_output=True, text=True)

    assert done.returncode == 0
    assert calls == [["yt-dlp", "--version"], [str(python), "-c", post.CONSOLE_SCRIPT, "yt-dlp", "--version"]]


def test_the_environment_named_after_the_tool_comes_before_one_that_bundles_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tool_environment(tmp_path, "a-downloader", program="yt-dlp")  # sorts first, holds its own yt-dlp
    python = tool_environment(tmp_path, "yt-dlp")
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))

    assert post.tool_python("yt-dlp") == python


@pytest.mark.parametrize("layout", [("uv", "data", "tools"), ("uv", "tools")])
def test_without_uv_tool_dir_the_tools_are_in_appdata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: tuple[str, ...]
) -> None:
    python = tool_environment(tmp_path.joinpath(*layout), "gallery-dl")
    monkeypatch.delenv("UV_TOOL_DIR", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert post.tool_python("gallery-dl") == python


def test_an_environment_without_its_python_is_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tool_environment(tmp_path, "yt-dlp").unlink()
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))

    assert post.tool_python("yt-dlp") is None


def test_a_blocked_tool_without_a_uv_environment_names_the_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing({"ffmpeg"}, []))

    with pytest.raises(post.BlockedTool, match="blocked ffmpeg, and no uv tool environment provides it"):
        post.run(["ffmpeg", "-version"])


def test_a_blocked_tool_whose_python_is_blocked_too_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    python = tool_environment(tmp_path, "yt-dlp")
    calls: list[list[str]] = []
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing({"yt-dlp", str(python)}, calls))

    with pytest.raises(post.BlockedTool, match="blocked yt-dlp, and also the Python of its uv tool environment"):
        post.run(["yt-dlp", "--version"])
    assert len(calls) == 2


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


def test_read_reports_a_blocked_tool_by_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", refusing({"yt-dlp"}, []))

    result = post.read("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result["work"] is None  # a failed read removes its own work folder

    assert result["status"] == "error"
    assert result["reason"].startswith("Windows Smart App Control blocked yt-dlp")


def test_a_403_still_retries_when_uv_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def forbidden(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == "uv":
            raise Blocked("Smart App Control blocked the file")
        return subprocess.CompletedProcess(command, 1, "", "ERROR: [youtube] x: HTTP Error 403: Forbidden")

    monkeypatch.setenv("UV_TOOL_DIR", str(tmp_path))
    monkeypatch.setattr(subprocess, "run", forbidden)

    result = post.read("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result["work"] is None  # a failed read removes its own work folder

    assert [command[0] for command in calls] == ["yt-dlp", "uv", "yt-dlp"]
    assert "403" in result["reason"]


def test_the_console_script_runner_starts_a_real_entry_point() -> None:
    # pytest's own console script, run by name the way the fallback runs yt-dlp.
    done = subprocess.run([sys.executable, "-c", post.CONSOLE_SCRIPT, "pytest", "--version"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert "pytest" in (done.stdout + done.stderr)


def test_the_console_script_runner_ignores_modules_in_the_working_folder(tmp_path: Path) -> None:
    # A launcher never imports from the working folder, so the fallback must not either.
    (tmp_path / "_pytest.py").write_text('raise SystemExit("imported from the working folder")\n')
    done = subprocess.run([sys.executable, "-c", post.CONSOLE_SCRIPT, "pytest", "--version"],
                          capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0, done.stderr
