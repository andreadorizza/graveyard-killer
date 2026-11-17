"""Run the Worker every day from this computer's own scheduler, for an agent with no scheduler.

    schedule.py install --time 13:00 [--days mon,wed] --model opencode/<model>
                        [--fallback-model opencode/<model>] --folder <run folder> --library <link>
                        [--name graveyard-killer-worker] [--title <text>] [--alert <text>]
    schedule.py show [--name …]      the job's time, days, model, Library and last run
    schedule.py remove [--name …]    unload and delete the job; the run folder stays
    schedule.py run --folder <run folder>    what the job starts: one Worker run in OpenCode

The job starts `run` with the Python that installed it. `run` starts `opencode run` in the
run folder, which holds its opencode.json and AGENTS.md, with schedule.md's prompt as one
argument and no shell between them, and logs the run in the run folder.
If the model fails, it tries the fallback model once. If that fails too, post.py notify shows
a desktop notification, since the run's own Ping cannot say so.

macOS: a launchd agent in ~/Library/LaunchAgents with StartCalendarInterval. A job missed
  while the computer slept starts when it wakes, once however many were missed
  (man launchd.plist).
Windows: a Task Scheduler task with StartWhenAvailable. A missed start runs as soon as it
  can, after a delay, 10 minutes by default.
Linux: a systemd user service and timer with Persistent=true. A user timer runs only while
  the user's systemd instance does: from their first login, unless lingering is on.

Standard library only.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import IO, Any
from xml.sax.saxutils import escape

DEFAULT_NAME = "graveyard-killer-worker"
DEFAULT_TITLE = "Graveyard Killer: tidy-up"
DEFAULT_ALERT = "Graveyard Killer could not run today's tidy-up."
SETTINGS = "schedule.json"
LOG = "worker.log"
LAST_RUN = "last-run.json"
LOG_LIMIT = 1_000_000  # bytes: past this the log moves to worker.log.1, and the older one goes
RUN_TIME_LIMIT = 5 * 60 * 60  # seconds for one model's run; 4 Entries took 42 minutes on 2026-11-16
# Seconds with no output before a model's run counts as stuck: longer than post.py's longest tool
# (an hour of speech recognition), since OpenCode reports a tool only when it ends.
SILENCE_LIMIT = 75 * 60
# OpenCode 1.19 shows a model's error, such as "Free usage limit reached", only in its log, and then
# waits with no output and never exits (2026-11-16). At ERROR level, the log comes with the events.
LOG_FLAGS = ["--print-logs", "--log-level", "ERROR"]
MODEL_ERROR = re.compile(r'message="stream error".*?error\.error="([^"]*)"')
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
# schedule.md's scheduled prompt, word for word: a test checks that the two agree.
PROMPT = (
    "Run the Graveyard Killer worker with the graveyard-killer-worker skill, and pass it this whole message.\n"
    "\n"
    "Graveyard Killer Library: {library}\n"
    "\n"
    "This is a scheduled run. When the skill returns, give its final message to the user as it is: it is the "
    "Ping. Then answer the user's replies in this chat with the graveyard-killer skill.\n"
)
# setup.md's pointer, in English. Setup may write the run folder's AGENTS.md in the user's
# language first: install never replaces one.
POINTER = (
    "Graveyard Killer Library: {library}\n"
    "It holds the posts I saved. Look there when I ask about something I saved, or when we talk about a topic "
    "it may hold.\n"
)
NOTION_MCP = "https://mcp.notion.com/mcp"
SCRIPTS = ("post.py", "link.py")
WORK_PREFIX = "graveyard-killer-"  # post.py read makes its work folders in the temporary folder with this name


@dataclass
class Job:
    name: str
    time: str  # HH:MM, local time
    days: list[str]  # from DAYS; empty for every day
    model: str
    fallback_model: str | None
    folder: str
    library: str
    title: str = DEFAULT_TITLE
    alert: str = DEFAULT_ALERT
    python: str = sys.executable
    script: str = str(Path(__file__).resolve())
    opencode: list[str] = field(default_factory=lambda: ["opencode"])  # the command, before its arguments
    path: str = ""  # PATH at install: a launchd job gets a bare one, with no Homebrew tools
    # The temporary folder at install. A scheduler may start the job with another TMPDIR, or
    # none, and post.py would then make its work folders where opencode.json lets nothing be read.
    temp: str = field(default_factory=tempfile.gettempdir)
    log_flags: list[str] = field(default_factory=list)  # LOG_FLAGS, when this OpenCode has them

    @property
    def hour(self) -> int:
        return int(self.time.split(":")[0])

    @property
    def minute(self) -> int:
        return int(self.time.split(":")[1])

    def command(self) -> list[str]:
        """What the scheduler starts."""
        return [self.python, self.script, "run", "--folder", self.folder]


class Refused(Exception):
    """Something the user or Setup must fix; its text says what."""


def current_system() -> str:
    return platform.system()


# ---------------------------------------------------------------- the run folder

def opencode_worktree(folder: Path) -> Path | None:
    """The git repository that holds the run folder, or None for a folder in none."""
    for parent in (folder, *folder.parents):
        if (parent / ".git").exists():
            return parent
    return None


def worker_folders(job: Job) -> list[str]:
    """What the Worker may read: the skills, the run folder and post.py's work folders."""
    skills = Path(job.script).resolve().parents[2]
    temps = dict.fromkeys((job.temp, str(Path(job.temp).resolve())))
    return list(dict.fromkeys([str(skills), job.folder, *(str(Path(t) / f"{WORK_PREFIX}*") for t in temps)]))


def absolute_patterns(folders: list[str]) -> list[str]:
    """Each folder and everything in it. OpenCode compares paths with / for \\, and asks
    external_directory for "<the folder>/*" whenever a tool looks outside the run folder."""
    patterns: list[str] = []
    for folder in folders:
        posix = folder.replace("\\", "/")
        patterns += [posix, f"{posix}/**"]
    return list(dict.fromkeys(patterns))


def read_patterns(folders: list[str], worktree: Path | None) -> list[str]:
    """OpenCode 1.x checks a read against the path relative to its worktree: the git
    repository, or the root for a folder in none, so "/Users/a/x" is checked as "Users/a/x".
    Absolute forms are kept too, for an agent that checks those."""
    patterns = absolute_patterns(folders)
    for folder in folders:
        relative = [folder[len(Path(folder).anchor):]]
        if worktree is not None:
            try:
                relative.append(os.path.relpath(folder, worktree))
            except ValueError:  # another drive
                pass
        for path in relative:
            posix = path.replace("\\", "/")
            patterns += [posix, f"{posix}/**"]
    return list(dict.fromkeys(patterns))


def script_calls(job: Job) -> list[str]:
    """The skill's script calls, as worker.md writes them and with the scripts' full path.

    Never a bare `python3 *`, which would let a post run `python3 -c`.
    """
    scripts = Path(job.script).resolve().parent
    pythons = ["python3", "python"] + (["py -3", "py"] if os.name == "nt" else [])
    calls = [f"cd {where}" for where in dict.fromkeys((str(scripts.parent), scripts.parent.as_posix()))]
    for python in pythons:
        for script in SCRIPTS:
            for where in dict.fromkeys((f"scripts/{script}", str(scripts / script), (scripts / script).as_posix())):
                calls += [f"{python} {where}", f"{python} {where} *"]
    return calls


def opencode_config(job: Job) -> dict[str, Any]:
    """The run folder's opencode.json, in OpenCode 1.x's format, which 2.x also reads.

    `opencode run --auto` approves every permission that is not denied, and a post is untrusted
    input that could ask the Worker to read a file and send it to a web page. So every rule
    denies first and then allows only what a Worker run needs: its own folders, the skill's
    scripts, web fetch and Notion. OpenCode applies the last rule that matches.
    """
    folders = worker_folders(job)
    reads = {"*": "deny", **{p: "allow" for p in read_patterns(folders, opencode_worktree(Path(job.folder)))}}
    elsewhere = {"*": "deny", **{p: "allow" for p in absolute_patterns(folders)}}
    return {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {"notion": {"type": "remote", "url": NOTION_MCP}},
        "permission": {
            "read": reads, "list": reads,
            # Any tool that looks outside the run folder asks this first, glob and grep included.
            "external_directory": elsewhere,
            # Glob and grep are checked against what they search for, not where, so a folder
            # rule cannot fence them: external_directory does.
            "glob": "allow", "grep": "allow",
            "edit": "deny",
            "bash": {"*": "deny", **{c: "allow" for c in script_calls(job)}},
            "webfetch": "allow",  # articles may be on any site
            "websearch": "deny",
            "question": "deny",  # nobody is there to answer: a question would hang the run
            "task": "deny",
            "doom_loop": "deny",  # the same call over and over stops instead of going on
        },
    }


def prepare_folder(job: Job) -> list[str]:
    """Write the job's settings, and the OpenCode files the folder lacks. Returns what was written."""
    folder = Path(job.folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = [str(folder / SETTINGS)]
    (folder / SETTINGS).write_text(json.dumps(asdict(job), indent=2) + "\n", encoding="utf-8")
    # Always rewritten: its rules name this job's folders.
    config = folder / "opencode.json"
    config.write_text(json.dumps(opencode_config(job), indent=2) + "\n", encoding="utf-8")
    written.append(str(config))
    agents = folder / "AGENTS.md"
    if not agents.exists():
        agents.write_text(POINTER.format(library=job.library), encoding="utf-8")
        written.append(str(agents))
    return written


def load_job(folder: Path) -> Job:
    data = json.loads((folder / SETTINGS).read_text(encoding="utf-8"))
    return Job(**data)


# ---------------------------------------------------------------- macOS: launchd

def launch_agent(name: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{name}.plist"


def launchd_plist(job: Job) -> bytes:
    if job.days:
        # launchd counts Sunday as 0 (or 7) and Monday as 1.
        interval: Any = [{"Weekday": (DAYS.index(d) + 1) % 7, "Hour": job.hour, "Minute": job.minute} for d in job.days]
    else:
        interval = {"Hour": job.hour, "Minute": job.minute}
    scheduler_log = str(Path(job.folder) / "scheduler.log")
    return plistlib.dumps({
        "Label": job.name,
        "ProgramArguments": job.command(),
        "WorkingDirectory": job.folder,
        "StartCalendarInterval": interval,
        "EnvironmentVariables": {"PATH": job.path},
        "StandardOutPath": scheduler_log,
        "StandardErrorPath": scheduler_log,
        "RunAtLoad": False,
    })


def launchd_domain() -> str:
    return f"gui/{os.getuid()}"  # type: ignore[attr-defined,unused-ignore]


def install_launchd(job: Job) -> list[str]:
    plist = launch_agent(job.name)
    plist.parent.mkdir(parents=True, exist_ok=True)
    unload_launchd(job.name)
    plist.write_bytes(launchd_plist(job))
    loaded = subprocess.run(["launchctl", "bootstrap", launchd_domain(), str(plist)], capture_output=True, text=True)
    if loaded.returncode != 0:
        raise Refused(f"launchctl could not load {plist}: {loaded.stderr.strip()}")
    return [str(plist)]


def unload_launchd(name: str) -> None:
    subprocess.run(["launchctl", "bootout", f"{launchd_domain()}/{name}"], capture_output=True, text=True)


def remove_launchd(name: str) -> list[str]:
    plist = launch_agent(name)
    unload_launchd(name)
    if plist.exists():
        plist.unlink()
        return [str(plist)]
    return []


def launchd_folder(name: str) -> Path | None:
    plist = launch_agent(name)
    if not plist.exists():
        return None
    return Path(plistlib.loads(plist.read_bytes())["ProgramArguments"][-1])


def launchd_loaded(name: str) -> bool:
    found = subprocess.run(["launchctl", "print", f"{launchd_domain()}/{name}"], capture_output=True, text=True)
    return found.returncode == 0


# ---------------------------------------------------------------- Windows: Task Scheduler

WINDOWS_DAYS = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
                "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}


def windowless(python: str) -> str:
    """pythonw.exe next to python.exe, so no console window opens when the task runs."""
    candidate = Path(python).with_name("pythonw.exe")
    return str(candidate) if candidate.exists() else python


def task_xml(job: Job, today: date) -> str:
    if job.days:
        days = "".join(f"<{WINDOWS_DAYS[d]} />" for d in job.days)
        schedule = f"<ScheduleByWeek><WeeksInterval>1</WeeksInterval><DaysOfWeek>{days}</DaysOfWeek></ScheduleByWeek>"
    else:
        schedule = "<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>"
    domain, user = os.environ.get("USERDOMAIN"), os.environ.get("USERNAME")
    account = f"{domain}\\{user}" if domain and user else None
    user_id = f"<UserId>{escape(account)}</UserId>" if account else ""
    command, *arguments = job.command()
    start = f"{today.isoformat()}T{job.hour:02d}:{job.minute:02d}:00"
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        f"  <RegistrationInfo><Description>{escape(job.title)}</Description></RegistrationInfo>\n"
        "  <Triggers>\n"
        f"    <CalendarTrigger><StartBoundary>{start}</StartBoundary><Enabled>true</Enabled>{schedule}</CalendarTrigger>\n"
        "  </Triggers>\n"
        # Run as the signed-in user, in their session, so that a notification shows.
        f'  <Principals><Principal id="Author">{user_id}<LogonType>InteractiveToken</LogonType>'
        "<RunLevel>LeastPrivilege</RunLevel></Principal></Principals>\n"
        "  <Settings>\n"
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n"
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n"
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n"
        "    <StartWhenAvailable>true</StartWhenAvailable>\n"
        "    <ExecutionTimeLimit>PT12H</ExecutionTimeLimit>\n"
        "    <Enabled>true</Enabled>\n"
        "  </Settings>\n"
        '  <Actions Context="Author">\n'
        f"    <Exec><Command>{escape(windowless(command))}</Command>"
        f"<Arguments>{escape(subprocess.list2cmdline(arguments))}</Arguments>"
        f"<WorkingDirectory>{escape(job.folder)}</WorkingDirectory></Exec>\n"
        "  </Actions>\n"
        "</Task>\n"
    )


def install_task(job: Job) -> list[str]:
    xml = Path(job.folder) / f"{job.name}.xml"
    xml.write_text(task_xml(job, date.today()), encoding="utf-16")  # schtasks reads UTF-16 with its BOM
    created = subprocess.run(["schtasks", "/Create", "/TN", job.name, "/XML", str(xml), "/F"],
                             capture_output=True, text=True)
    if created.returncode != 0:
        raise Refused(f"schtasks could not create the task: {(created.stderr or created.stdout).strip()}")
    return [str(xml)]


def remove_task(name: str) -> list[str]:
    deleted = subprocess.run(["schtasks", "/Delete", "/TN", name, "/F"], capture_output=True, text=True)
    return [f"task {name}"] if deleted.returncode == 0 else []


def task_folder(name: str) -> Path | None:
    found = subprocess.run(["schtasks", "/Query", "/TN", name, "/XML", "ONE"], capture_output=True, text=True)
    if found.returncode != 0:
        return None
    match = re.search(r"<WorkingDirectory>(.*?)</WorkingDirectory>", found.stdout, re.DOTALL)
    if not match:
        return None
    return Path(html.unescape(match.group(1).strip()))


# ---------------------------------------------------------------- Linux: systemd

def systemd_units_folder() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "systemd" / "user"


def systemd_value(text: str) -> str:
    """Text for a unit file, where % starts a specifier and $ a variable."""
    return text.replace("%", "%%").replace("$", "$$")


def systemd_argument(text: str) -> str:
    return '"' + systemd_value(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def systemd_units(job: Job) -> tuple[str, str]:
    service = (
        "[Unit]\n"
        f"Description={systemd_value(job.title)}\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"WorkingDirectory={systemd_value(job.folder)}\n"
        f"ExecStart={' '.join(systemd_argument(a) for a in job.command())}\n"
        "TimeoutStartSec=12h\n"
    )
    days = ",".join(d.capitalize() for d in job.days)
    calendar = f"{days + ' ' if days else ''}*-*-* {job.hour:02d}:{job.minute:02d}:00"
    timer = (
        "[Unit]\n"
        f"Description={systemd_value(job.title)}\n"
        "\n"
        "[Timer]\n"
        f"OnCalendar={calendar}\n"
        "Persistent=true\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )
    return service, timer


def systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True)


def install_systemd(job: Job) -> list[str]:
    folder = systemd_units_folder()
    folder.mkdir(parents=True, exist_ok=True)
    service, timer = systemd_units(job)
    (folder / f"{job.name}.service").write_text(service, encoding="utf-8")
    (folder / f"{job.name}.timer").write_text(timer, encoding="utf-8")
    systemctl("daemon-reload")
    enabled = systemctl("enable", "--now", f"{job.name}.timer")
    if enabled.returncode != 0:
        raise Refused(f"systemctl could not start the timer: {enabled.stderr.strip()}")
    return [str(folder / f"{job.name}.service"), str(folder / f"{job.name}.timer")]


def remove_systemd(name: str) -> list[str]:
    systemctl("disable", "--now", f"{name}.timer")
    removed = []
    for suffix in (".timer", ".service"):
        unit = systemd_units_folder() / f"{name}{suffix}"
        if unit.exists():
            unit.unlink()
            removed.append(str(unit))
    systemctl("daemon-reload")
    return removed


def systemd_folder(name: str) -> Path | None:
    service = systemd_units_folder() / f"{name}.service"
    if not service.exists():
        return None
    for line in service.read_text(encoding="utf-8").splitlines():
        if line.startswith("WorkingDirectory="):
            return Path(line.split("=", 1)[1].replace("%%", "%").replace("$$", "$"))
    return None


def systemd_loaded(name: str) -> bool:
    return systemctl("is-enabled", f"{name}.timer").returncode == 0


# ---------------------------------------------------------------- the commands

def system_or_refuse() -> str:
    system = current_system()
    if system not in ("Darwin", "Windows", "Linux"):
        raise Refused(f"No scheduler for {system or 'this system'}: the Worker can be scheduled on macOS, "
                      "Windows and Linux.")
    return system


def parse_days(text: str | None) -> list[str]:
    if not text:
        return []
    days = [d.strip().lower()[:3] for d in text.split(",") if d.strip()]
    unknown = [d for d in days if d not in DAYS]
    if unknown:
        raise Refused(f"Unknown days {', '.join(unknown)}: use {','.join(DAYS)}.")
    return sorted(set(days), key=DAYS.index)


def supported_log_flags(opencode: list[str]) -> list[str]:
    """LOG_FLAGS if `opencode run` lists them. OpenCode 2.x's docs do not name them, and an
    option it does not know could stop every run."""
    try:
        listing = subprocess.run([*opencode, "run", "--help"], capture_output=True, text=True,
                                 stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return LOG_FLAGS if "--print-logs" in f"{listing.stdout}{listing.stderr}" else []


def install(args: argparse.Namespace) -> dict[str, Any]:
    system = system_or_refuse()
    match = TIME.match(args.time)
    if not match:
        raise Refused(f"The time {args.time!r} is not HH:MM, such as 13:00.")
    for model in filter(None, (args.model, args.fallback_model)):
        if "/" not in model:
            raise Refused(f"The model {model!r} needs its provider, such as opencode/glm-5.3-flash-free.")
    if not re.match(r"^https?://\S+$", args.library):
        raise Refused(f"The Library link {args.library!r} is not a web link.")
    opencode = shutil.which("opencode")
    if not opencode:
        raise Refused("OpenCode is not installed, or not on PATH: install it first.")
    job = Job(
        name=args.name,
        time=f"{int(match.group(1)):02d}:{match.group(2)}",
        days=parse_days(args.days),
        model=args.model,
        fallback_model=args.fallback_model,
        folder=str(Path(args.folder).expanduser().resolve()),
        library=args.library,
        title=args.title,
        alert=args.alert,
        opencode=[opencode],
        path=os.environ.get("PATH", ""),
        log_flags=supported_log_flags([opencode]),
    )
    written = prepare_folder(job)
    if system == "Darwin":
        written += install_launchd(job)
    elif system == "Windows":
        written += install_task(job)
    else:
        written += install_systemd(job)
    return {"installed": job.name, "system": system, "time": job.time, "days": job.days or "every day",
            "model": job.model, "fallback_model": job.fallback_model, "folder": job.folder,
            "library": job.library, "written": written}


def find_folder(system: str, name: str) -> Path | None:
    if system == "Darwin":
        return launchd_folder(name)
    if system == "Windows":
        return task_folder(name)
    return systemd_folder(name)


def show(args: argparse.Namespace) -> dict[str, Any]:
    system = system_or_refuse()
    folder = find_folder(system, args.name)
    if folder is None:
        return {"job": None, "name": args.name, "system": system}
    result: dict[str, Any] = {"job": args.name, "system": system, "folder": str(folder)}
    if system == "Darwin":
        result["loaded"] = launchd_loaded(args.name)
    elif system == "Linux":
        result["loaded"] = systemd_loaded(args.name)
    try:
        job = load_job(folder)
    except (OSError, ValueError, TypeError) as e:
        result["error"] = f"cannot read {folder / SETTINGS}: {e}"
        return result
    result.update(time=job.time, days=job.days or "every day", model=job.model,
                  fallback_model=job.fallback_model, library=job.library, log=str(folder / LOG))
    last = folder / LAST_RUN
    if last.exists():
        result["last_run"] = json.loads(last.read_text(encoding="utf-8"))
    return result


def remove(args: argparse.Namespace) -> dict[str, Any]:
    system = system_or_refuse()
    if system == "Darwin":
        removed = remove_launchd(args.name)
    elif system == "Windows":
        removed = remove_task(args.name)
    else:
        removed = remove_systemd(args.name)
    return {"removed": args.name if removed else None, "deleted": removed}


# ---------------------------------------------------------------- one run

class Log:
    """The run folder's log: one timestamped line per event, kept under LOG_LIMIT."""

    def __init__(self, folder: Path) -> None:
        path = folder / LOG
        if path.exists() and path.stat().st_size > LOG_LIMIT:
            path.replace(folder / f"{LOG}.1")
        self.file: IO[str] = path.open("a", encoding="utf-8")

    def write(self, kind: str, text: str = "") -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        first, *rest = (text or "").splitlines() or [""]
        self.file.write(f"{stamp}  {kind:<8} {first}\n")
        for line in rest:
            self.file.write(f"{'':<19}  {'':<8} {line}\n")
        self.file.flush()

    def close(self) -> None:
        self.file.close()


@dataclass
class Outcome:
    ok: bool
    reason: str = ""
    ping: str | None = None
    session: str | None = None
    timed_out: bool = False


def describe_tool(part: dict[str, Any]) -> str:
    """One line: the tool, what it worked on, and how it went."""
    state = part.get("state") or {}
    given = state.get("input") or {}
    target = next((str(given[k]) for k in ("command", "filePath", "url", "name", "pattern") if given.get(k)), "")
    target = target.splitlines()[0][:160] if target else ""
    line = " ".join(filter(None, (str(part.get("tool")), target, f"({state.get('status', '')})")))
    if state.get("status") == "error":
        line += f": {str(state.get('error', ''))[:300]}"
    return line


def prompt_argument(opencode: list[str], library: str) -> str:
    """The prompt as one argument. A Windows .cmd shim, such as npm's, runs through cmd.exe,
    which ends a command at a line break, so there the paragraphs become one line."""
    prompt = PROMPT.format(library=library)
    if opencode[0].lower().endswith((".cmd", ".bat")):
        prompt = " ".join(line for line in prompt.splitlines() if line)
    return prompt


def run_model(job: Job, model: str, env: dict[str, str], log: Log) -> Outcome:
    # OpenCode 1.x and 2.x both take the run folder as the working folder, and read its
    # opencode.json and AGENTS.md there; 1.x's --dir may not exist in 2.x.
    command = [*job.opencode, "run", "--auto", "--format", "json", *job.log_flags, "-m", model,
               prompt_argument(job.opencode, job.library)]
    log.write("start", f"{model} in {job.folder}")
    # OpenCode 1.19 takes its project folder from PWD, not from the working folder: started from a
    # shell, it would run in the shell's folder, without the run folder's opencode.json.
    env = {**env, "PWD": job.folder}
    try:
        process = subprocess.Popen(
            command, cwd=job.folder, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as e:
        log.write("error", f"cannot start OpenCode: {e}")
        return Outcome(False, f"cannot start OpenCode: {e}")
    timed_out, silent, done = threading.Event(), threading.Event(), threading.Event()
    heard = [time.monotonic()]

    def stop() -> None:
        timed_out.set()
        process.kill()

    def watch() -> None:
        while not done.wait(min(30.0, SILENCE_LIMIT / 4)):
            if time.monotonic() - heard[0] > SILENCE_LIMIT:
                silent.set()
                process.kill()
                return

    timer = threading.Timer(RUN_TIME_LIMIT, stop)
    timer.start()
    threading.Thread(target=watch, daemon=True).start()
    outcome = Outcome(False)
    error: str | None = None
    assert process.stdout is not None
    try:
        for line in process.stdout:
            heard[0] = time.monotonic()
            try:
                event = json.loads(line)
            except ValueError:
                if line.strip():
                    log.write("output", line.rstrip())
                found = MODEL_ERROR.search(line)
                if found:  # the model refused: OpenCode would wait forever, so stop it
                    error = found.group(1)
                    process.kill()
                continue
            if not isinstance(event, dict):
                continue
            outcome.session = outcome.session or event.get("sessionID")
            part = event.get("part") or {}
            if event.get("type") == "text" and part.get("text"):
                outcome.ping, error = part["text"], None
                log.write("text", part["text"])
            elif event.get("type") == "tool_use":
                log.write("tool", describe_tool(part))
            elif event.get("type") == "error":
                details = event.get("error") or {}
                error = f"{details.get('name', 'error')}: {(details.get('data') or {}).get('message', '')}".strip()
                log.write("error", error)
        process.wait()
    finally:
        timer.cancel()
        done.set()
    if timed_out.is_set():
        outcome.reason, outcome.timed_out = f"stopped after {RUN_TIME_LIMIT // 60} minutes", True
    elif silent.is_set():
        outcome.reason = error or f"OpenCode said nothing for {SILENCE_LIMIT // 60} minutes and was stopped"
    elif process.returncode != 0:
        outcome.reason = error or f"OpenCode exited with {process.returncode}"
    elif error or outcome.ping is None:
        outcome.reason = error or "the run ended with no final message"
    else:
        outcome.ok = True
    log.write("end", f"{model}: {'done' if outcome.ok else outcome.reason}"
              + (f" (session {outcome.session})" if outcome.session else ""))
    return outcome


def alert(job: Job, reason: str) -> None:
    """A desktop notification through post.py notify, which sits next to this script."""
    post = str(Path(job.script).with_name("post.py"))
    message = f"{job.alert} {reason}. Log: {Path(job.folder) / LOG}"
    subprocess.run([job.python, post, "notify"], input=f"{job.title}\n{message}\n", capture_output=True, text=True)


def run(folder: Path) -> Outcome:
    folder = folder.resolve()
    job = load_job(folder)
    env = {**os.environ, "OPENCODE_DISABLE_CLAUDE_CODE": "1"}  # ~/.claude stays out of the run
    if job.path:
        env["PATH"] = job.path
    env["TMPDIR"] = job.temp  # post.py's work folders go where opencode.json lets the Worker read
    log = Log(folder)
    started = datetime.now().isoformat(timespec="seconds")
    outcome = Outcome(False, "no model")
    tried: list[str] = []
    try:
        for model in filter(None, (job.model, job.fallback_model)):
            tried.append(model)
            outcome = run_model(job, model, env, log)
            if outcome.ok or outcome.timed_out:
                break
    finally:
        log.close()
    (folder / LAST_RUN).write_text(json.dumps({
        "started": started, "finished": datetime.now().isoformat(timespec="seconds"), "models": tried,
        "ok": outcome.ok, "reason": outcome.reason or None, "session": outcome.session, "ping": outcome.ping,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not outcome.ok:
        alert(job, outcome.reason)
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser(prog="schedule.py")
    commands = parser.add_subparsers(dest="command", required=True)
    install_parser = commands.add_parser("install")
    install_parser.add_argument("--time", required=True, help="HH:MM, local time")
    install_parser.add_argument("--days", help="such as mon,wed; every day when left out")
    install_parser.add_argument("--model", required=True, help="provider/model, such as opencode/glm-5.3-flash-free")
    install_parser.add_argument("--fallback-model", help="tried once when the model fails")
    install_parser.add_argument("--folder", required=True, help="the run folder")
    install_parser.add_argument("--library", required=True, help="the Library link")
    install_parser.add_argument("--title", default=DEFAULT_TITLE, help="the job's name, in the Settings language")
    install_parser.add_argument("--alert", default=DEFAULT_ALERT, help="the notification's text when a run "
                                "fails, in the Settings language")
    for other in (commands.add_parser("show"), commands.add_parser("remove")):
        other.add_argument("--name", default=DEFAULT_NAME, help="the job's name")
    install_parser.add_argument("--name", default=DEFAULT_NAME, help="the job's name")
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--folder", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            sys.exit(0 if run(args.folder).ok else 1)
        result = {"install": install, "show": show, "remove": remove}[args.command](args)
    except Refused as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
