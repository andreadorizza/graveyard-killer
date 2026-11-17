"""The schedule script: each system's job file, written with fakes, and one run with a fake OpenCode."""

from __future__ import annotations

import json
import os
import plistlib
import re
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
