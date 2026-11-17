"""post.py notify: a Ping's alert as a desktop notification, when the agent has no push tool."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import Run

sys.path.insert(0, str(Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts"))
import post  # noqa: E402

TITLE = "Graveyard Killer"
# Shell, PowerShell, cmd and AppleScript would each expand or break on something here.
MESSAGE = """- The Roma concert is "on" Saturday: $HOME `id` $(id) %PATH% & 'quote' \\ end"""
NOTIFIERS = ("osascript", "notify-send", "powershell")
ALL_NOTIFIERS_WORK: dict[str, list[dict[str, Any]]] = {name: [{}] for name in NOTIFIERS}


def notifier_calls(run: Run) -> list[dict[str, Any]]:
    return [c for c in run.calls if c["tool"] in NOTIFIERS]


def test_notify_shows_the_title_and_line_unexpanded(post: Callable[..., Run]) -> None:
    run = post("notify", stdin=f"{TITLE}\n{MESSAGE}\n", scenario=ALL_NOTIFIERS_WORK)
    assert run.output == {"notified": True}
    [call] = notifier_calls(run)
    if platform.system() == "Windows":
        assert call["env"] == {"GK_NOTIFY_TITLE": TITLE, "GK_NOTIFY_MESSAGE": MESSAGE}
        assert MESSAGE not in " ".join(call["argv"])
    else:
        assert call["argv"][-2:] == [TITLE, MESSAGE]


def test_notify_needs_a_title_and_a_message(post: Callable[..., Run]) -> None:
    run = post("notify", stdin="Graveyard Killer\n", scenario=ALL_NOTIFIERS_WORK)
    assert run.exit_code == 2
    assert run.output["notified"] is False
    assert notifier_calls(run) == []


def test_notify_says_why_when_the_computer_has_no_notifier(post: Callable[..., Run]) -> None:
    run = post("notify", stdin=f"{TITLE}\n{MESSAGE}\n", without=NOTIFIERS)
    assert run.exit_code == 0
    assert run.output["notified"] is False
    assert "is not on this computer" in run.output["reason"]


def test_notify_passes_on_the_notifiers_error(post: Callable[..., Run]) -> None:
    failing = {name: [{"exit": 1, "stderr": "Could not connect to the notification server"}] for name in NOTIFIERS}
    run = post("notify", stdin=f"{TITLE}\n{MESSAGE}\n", scenario=failing)
    assert run.output == {"notified": False, "reason": "Could not connect to the notification server"}


def test_notify_joins_extra_lines_into_one(post: Callable[..., Run]) -> None:
    run = post("notify", stdin=f"{TITLE}\nfirst part\n\nsecond part\n", scenario=ALL_NOTIFIERS_WORK)
    [call] = notifier_calls(run)
    text = call["env"]["GK_NOTIFY_MESSAGE"] if platform.system() == "Windows" else call["argv"][-1]
    assert text == "first part second part"


@pytest.fixture
def commands(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], list[tuple[list[str], dict[str, Any]]]]:
    """Run notify as if on another system, recording what it would start."""
    def on(system_name: str) -> list[tuple[list[str], dict[str, Any]]]:
        started: list[tuple[list[str], dict[str, Any]]] = []

        def fake_run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
            started.append((command, options))
            return subprocess.CompletedProcess(command, 0, "", "")

        monkeypatch.setattr(post, "system", lambda: system_name)
        monkeypatch.setattr(shutil, "which", lambda name: f"/found/{name}")
        monkeypatch.setattr(subprocess, "run", fake_run)
        assert post.notify(TITLE, MESSAGE) == {"notified": True}
        return started
    return on


def test_on_macos_the_text_is_the_scripts_arguments(commands: Callable[[str], Any]) -> None:
    [(command, options)] = commands("Darwin")
    assert command[0] == "/found/osascript"
    assert command[-2:] == [TITLE, MESSAGE]
    script = " ".join(command[1:-2])
    assert MESSAGE not in script and "display notification" in script
    assert options["timeout"] == post.NOTIFY_TIME_LIMIT


def test_on_linux_notify_send_ends_its_options_before_the_text(commands: Callable[[str], Any]) -> None:
    [(command, _)] = commands("Linux")
    assert command[0] == "/found/notify-send"
    assert command[-3:] == ["--", TITLE, MESSAGE]


def test_on_windows_the_text_goes_in_the_environment_not_the_script(commands: Callable[[str], Any]) -> None:
    [(command, options)] = commands("Windows")
    assert command[0] == "/found/powershell.exe"
    assert "-NoProfile" in command and command[-1] == post.WINDOWS_TOAST
    assert options["env"]["GK_NOTIFY_TITLE"] == TITLE
    assert options["env"]["GK_NOTIFY_MESSAGE"] == MESSAGE
    assert "$env:GK_NOTIFY_MESSAGE" in post.WINDOWS_TOAST
