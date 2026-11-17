"""Run the Graveyard Killer evals headless, one fresh agent session each.

Usage:
    python3 evals/run_evals.py [--agent claude|opencode] [--model <provider/model>] <app> <capture|worker|drive> <id> [<id> ...]
    python3 evals/run_evals.py [--agent ...] [--model ...] <app> resume <run> "<reply>"
    python3 evals/run_evals.py [--agent ...] [--model ...] <app> prompt <run> "<prompt>"

<app> is `notion` or `google-drive`. `resume` answers a finished run in its own
session. `prompt` runs any message against the test Library, for example to seed it.

The agent is `claude` (`claude -p`, the default) or `opencode` (`opencode run`, Notion only),
which needs `--model`, such as `opencode/glm-5.3-flash-free`. `--opencode-bin`, or OPENCODE_BIN,
names another OpenCode command.

Each run writes <temp folder>/gk-evals/<app>/<run>/, or gk-evals/opencode/<model>/<app>/<run>/:
out.jsonl (the session's stream), result.txt (its final message), session.txt,
expectations.md (what to grade) and, for OpenCode, stats.json (time, steps, tokens).
evals/local.json, which is not committed, holds each app's test Library link and
the placeholders' values; see evals/README.md.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import IO, Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "plugin/skills/graveyard-killer/scripts"))
import schedule  # noqa: E402  The scheduled run folder's opencode.json, which the OpenCode evals reuse.

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
HOME = pathlib.Path.home()
# Outside the repo, so the eval sessions load none of its CLAUDE.md or AGENTS.md.
RUNS = pathlib.Path(tempfile.gettempdir()) / "gk-evals"

APPS: dict[str, dict[str, Any]] = {
    "notion": {"name": "Notion", "tools": ["mcp__claude_ai_Notion"], "servers": ["claude.ai Notion"]},
    "google-drive": {
        "name": "Google Drive",
        "tools": ["mcp__claude_ai_Google_Drive", "mcp__claude_ai_Google_Sheets"],
        "servers": ["claude.ai Google Drive", "claude.ai Google Sheets"],
    },
}
# A session whose app connectors are still pending, or missing, when it starts fails to reach the Library
# (seen on 2026-11-13). The runner stops such a session at once and starts it again, this many times in all.
ATTEMPTS = 3
NO_MEMORY = {("capture", 12)}
SETTINGS = json.dumps(
    {"claudeMdExcludes": [str(HOME / ".claude" / "CLAUDE.md"), str(HOME / ".claude" / "projects") + "/**"]}
)
# Posts are untrusted input, so the sessions may run the skill's own scripts only, not any python3.
SCRIPTS = REPO / "plugin" / "skills" / "graveyard-killer" / "scripts"
ALLOWED = ["Skill", "ToolSearch", "Read", "Glob", "Grep", "WebFetch", "Bash(sleep:*)", "Bash(ls:*)",
           *(f"Bash(python3 {path}:*)" for name in ("link.py", "post.py", "graveyard.py")
             for path in (f"scripts/{name}", str(SCRIPTS / name)))]
# ~/.claude holds the user's own CLAUDE.md, with the pointer to their real Library. claudeMdExcludes keeps
# it out of the context, but an agent that finds no pointer will search for one, so it must not read there.
DISALLOWED = ["mcp__claude_ai_Gmail", "mcp__claude_ai_Google_Calendar", "PushNotification", "Write", "Edit",
              f"Read(/{HOME}/.claude/**)"]  # A Read rule covers Grep and Glob too.

# OpenCode: the free route is Notion only (ADR-0007).
OPENCODE_APPS = {"notion"}
OPENCODE_TIMEOUT = 7200  # A free model is slow: the #17 prototype took 42 minutes for 4 Entries.


def load_local() -> dict[str, Any]:
    path = HERE / "local.json"
    if not path.exists():
        sys.exit(f"Missing {path}: see evals/README.md")
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def fill(text: str, app: str, placeholders: dict[str, str]) -> str:
    text = text.replace("{{LIBRARY_APP}}", str(APPS[app]["name"]))
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


# --- Claude Code ---------------------------------------------------------------------------------

def command(app: str, prompt: str) -> list[str]:
    allowed = [*ALLOWED, *APPS[app]["tools"]]
    disallowed = [*DISALLOWED, *(t for other, spec in APPS.items() if other != app for t in spec["tools"])]
    return ["claude", "-p", prompt, "--plugin-dir", str(REPO / "plugin"), "--settings", SETTINGS,
            "--output-format", "stream-json", "--verbose",
            "--allowedTools", *allowed, "--disallowedTools", *disallowed]


def connectors_ready(event: dict[str, Any], app: str) -> bool:
    """Whether a session's init event shows every connector of the app as connected."""
    status = {server.get("name"): server.get("status") for server in event.get("mcp_servers", [])}
    return all(status.get(name) == "connected" for name in APPS[app]["servers"])


def attempt(cmd: list[str], cwd: pathlib.Path, out: IO[str], app: str) -> str:
    """Stream one session into out. Return "done", "timeout", or "not ready" after stopping it at its start."""
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    timer = threading.Timer(3600, proc.kill)
    timer.start()
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            out.write(line)
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init" and not connectors_ready(event, app):
                proc.kill()
                proc.wait()
                return "not ready"
        proc.wait()
        return "done" if timer.is_alive() else "timeout"
    finally:
        timer.cancel()


def run(folder: pathlib.Path, cmd: list[str], app: str, resume: bool = False) -> None:
    """Run one session. A resumed session adds to the run's stream; a new run starts it again."""
    cwd = folder / "cwd"
    with open(folder / "out.jsonl", "a" if resume else "w", encoding="utf-8") as out:
        for number in range(1, ATTEMPTS + 1):
            start = out.tell()
            outcome = attempt(cmd, cwd, out, app)
            if outcome != "not ready":
                break
            out.truncate(start)
            out.seek(start)
            print(f"--- {folder.name}: connectors not ready at start, try {number} of {ATTEMPTS}", flush=True)
            time.sleep(15)
        if outcome != "done":
            print(f"=== {folder.name}: {outcome}", flush=True)
            return
    result, session = "", ""
    for line in (folder / "out.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        session = event.get("session_id", session)
        if event.get("type") == "result":
            result = event.get("result", "")
    (folder / "result.txt").write_text(result, encoding="utf-8")
    (folder / "session.txt").write_text(session, encoding="utf-8")
    print(f"=== {folder.name} (session {session})\n{result}\n", flush=True)


def prepare(app: str, name: str, library: str, memory: bool) -> pathlib.Path:
    folder = RUNS / app / name
    cwd = folder / "cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    pointer = cwd / "CLAUDE.md"
    if memory:
        pointer.write_text(f"Graveyard Killer Library: {library}\n", encoding="utf-8")
    else:
        pointer.unlink(missing_ok=True)
    return folder


# --- OpenCode ------------------------------------------------------------------------------------

def opencode_base(model: str) -> pathlib.Path:
    return RUNS / "opencode" / re.sub(r"[^A-Za-z0-9.-]+", "-", model)


def opencode_env() -> dict[str, str]:
    """Keep the user's own OpenCode setup out: its global config, its sessions and every skill outside the run folder.

    OPENCODE_DISABLE_CLAUDE_CODE keeps ~/.claude/CLAUDE.md, with the real Library pointer, out of the
    context. OPENCODE_DISABLE_EXTERNAL_SKILLS skips ~/.claude/skills and ~/.agents/skills, so a skill
    installed by Setup never mixes with this branch's. XDG_CONFIG_HOME moves the global config, where
    Setup puts its AGENTS.md pointer, to an empty folder. OPENCODE_DB keeps the eval sessions in their
    own database: OpenCode runs that share one fail with "database is locked". The data folder, which
    holds the Notion sign-in from `opencode mcp auth notion`, stays the user's own.
    """
    shared = RUNS / "opencode"
    config = shared / "config"
    pointer = config / "opencode" / "AGENTS.md"
    if pointer.exists():
        sys.exit(f"{pointer} must not exist: the eval sessions' only pointer is the run folder's AGENTS.md")
    config.mkdir(parents=True, exist_ok=True)
    return {**os.environ, "OPENCODE_DISABLE_CLAUDE_CODE": "1", "OPENCODE_DISABLE_EXTERNAL_SKILLS": "1",
            "OPENCODE_DISABLE_AUTOUPDATE": "1", "XDG_CONFIG_HOME": str(config),
            "OPENCODE_DB": str(shared / "opencode.db")}


def opencode_config(cwd: pathlib.Path, skills: pathlib.Path, model: str, library: str) -> dict[str, Any]:
    """The run folder's opencode.json: the one schedule.py writes for a scheduled run, so the evals test the
    rules users get, plus `skills.paths` for this branch's skills.

    `opencode run --auto` approves every permission that is not denied, and a post is untrusted input.
    schedule.py's rules deny first and then allow only the run folder, the skills and post.py's work
    folders for reading, the skill's exact script calls in Bash, web fetch and Notion.
    """
    job = schedule.Job(name="gk-eval", time="13:00", days=[], model=model, fallback_model=None,
                       folder=str(cwd.resolve()), library=library,
                       script=str(skills.resolve() / "graveyard-killer" / "scripts" / "schedule.py"),
                       temp=tempfile.gettempdir())
    config: dict[str, Any] = schedule.opencode_config(job)
    config["skills"] = {"paths": [str(skills.resolve())]}
    return config


def opencode_prepare(model: str, app: str, name: str, library: str, memory: bool) -> pathlib.Path:
    """A fresh run folder, cwd/, with the pointer in AGENTS.md and opencode.json, and this branch's skills
    next to it in skills/, outside the run folder as a user's installed skills are.

    With the skills inside the run folder, schedule.py's rules denied reading them (OpenCode 1.19.5,
    2026-11-16). The skills folder is not hidden: OpenCode 1.19's glob finds nothing under `.agents`.
    """
    folder = opencode_base(model) / app / name
    cwd, skills = folder / "cwd", folder / "skills"
    cwd.mkdir(parents=True, exist_ok=True)
    for old in (skills, cwd / "skills"):  # cwd/skills: where the skills went before
        shutil.rmtree(old, ignore_errors=True)
    shutil.copytree(REPO / "plugin" / "skills", skills, ignore=shutil.ignore_patterns("__pycache__"))
    pointer = cwd / "AGENTS.md"
    if memory:
        pointer.write_text(f"Graveyard Killer Library: {library}\n", encoding="utf-8")
    else:
        pointer.unlink(missing_ok=True)
    config = opencode_config(cwd, skills, model, library)
    (cwd / "opencode.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return folder


def opencode_command(binary: str, model: str, prompt: str, session: str = "") -> list[str]:
    # The run folder is the process's working folder, not `--dir`, which OpenCode 2.x may not have.
    # --print-logs at ERROR puts the model's errors, such as "Free usage limit reached", in the stream:
    # `opencode run` shows them nowhere else, and after one it waits with no output and does not exit.
    return [binary, "run", "--auto", "--format", "json", "--print-logs", "--log-level", "ERROR", "-m", model,
            *(["-s", session] if session else []), prompt]


def here(env: dict[str, str], cwd: pathlib.Path) -> dict[str, str]:
    """The environment for a process in cwd. OpenCode 1.19 takes its project folder from PWD, not from the
    process's working folder: with the runner's own PWD, a session ran in the repo and never saw AGENTS.md."""
    return {**env, "PWD": str(cwd)}


def opencode_ready(binary: str, cwd: pathlib.Path, env: dict[str, str]) -> bool:
    """Whether `opencode mcp list` shows the Notion server as connected in the run folder."""
    listing = subprocess.run([binary, "mcp", "list"], cwd=cwd, env=here(env, cwd), capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=120)
    text = re.sub(r"\x1b\[[0-9;]*m", "", listing.stdout + listing.stderr).lower()
    lines = [line for line in text.splitlines() if "notion" in line and "http" not in line]
    return any("connected" in line and not any(bad in line for bad in ("not connected", "disconnected", "failed", "needs"))
               for line in lines)


def opencode_attempt(cmd: list[str], cwd: pathlib.Path, env: dict[str, str], out: IO[str]) -> str:
    """Stream one session into out. Return "done", "timeout", "exit <code>", "locked", or the model's error.

    "locked" and a model error before the first step can be tried again; a model error later cannot,
    since the run has already changed the Library.
    """
    proc = subprocess.Popen(cmd, cwd=cwd, env=here(env, cwd), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    timer = threading.Timer(OPENCODE_TIMEOUT, proc.kill)
    timer.start()
    locked, steps, error = False, 0, ""
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            out.write(line)
            out.flush()
            locked = locked or "database is locked" in line
            steps += '"type":"step_finish"' in line
            if "stream error" in line and "level=ERROR" in line:
                found = re.search(r'error\.error="([^"]*)"', line)
                error = found.group(1) if found else "stream error"
                proc.kill()
                break
        proc.wait()
        if not timer.is_alive():
            return "timeout"
        if error:
            return f"model error{'' if steps else ' at start'}: {error}"
        if locked and proc.returncode:
            return "locked"
        return f"exit {proc.returncode}" if proc.returncode else "done"
    finally:
        timer.cancel()


def opencode_stats(lines: list[str]) -> tuple[str, str, dict[str, Any]]:
    """The session, its final message and its counts, from `opencode run --format json` events."""
    session, last_message = "", ""
    texts: dict[str, list[str]] = {}
    stats: dict[str, Any] = {"steps": 0, "tool_calls": 0, "tool_errors": 0, "errors": [],
                             "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache_read": 0}, "last_input": 0}
    first = last = 0
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        session = event.get("sessionID", session)
        stamp = event.get("timestamp")
        if isinstance(stamp, int):
            first, last = first or stamp, stamp
        part = event.get("part") or {}
        kind = event.get("type")
        if kind == "text":
            message = part.get("messageID", "")
            texts.setdefault(message, []).append(part.get("text", ""))
            last_message = message
        elif kind == "tool_use":
            stats["tool_calls"] += 1
            stats["tool_errors"] += (part.get("state") or {}).get("status") == "error"
        elif kind == "step_finish":
            stats["steps"] += 1
            tokens = part.get("tokens") or {}
            for key in ("input", "output", "reasoning"):
                stats["tokens"][key] += int(tokens.get(key) or 0)
            stats["tokens"]["cache_read"] += int((tokens.get("cache") or {}).get("read") or 0)
            stats["last_input"] = int(tokens.get("input") or 0)
        elif kind == "error":
            stats["errors"].append(event.get("error") or part)
    stats["minutes"] = round((last - first) / 60000, 1) if first else 0
    return session, "\n".join(texts.get(last_message, [])).strip(), stats


def opencode_run(folder: pathlib.Path, cmd: list[str], env: dict[str, str], binary: str, model: str,
                 resume: bool = False) -> None:
    """Run one session in OpenCode. A resumed session adds to the run's stream; a new run starts it again."""
    cwd = folder / "cwd"
    for number in range(1, ATTEMPTS + 1):
        if opencode_ready(binary, cwd, env):
            break
        print(f"--- {folder.name}: Notion not connected, try {number} of {ATTEMPTS}", flush=True)
        time.sleep(15)
    else:
        print(f"=== {folder.name}: Notion is not connected. Run `opencode mcp auth notion` once.", flush=True)
        return
    started = time.monotonic()
    with open(folder / "out.jsonl", "a" if resume else "w", encoding="utf-8") as out:
        for number in range(1, ATTEMPTS + 1):
            start = out.tell()
            outcome = opencode_attempt(cmd, cwd, env, out)
            if outcome != "locked" and not outcome.startswith("model error at start"):
                break
            out.truncate(start)
            out.seek(start)
            print(f"--- {folder.name}: {outcome}, try {number} of {ATTEMPTS}", flush=True)
            time.sleep(15 if outcome == "locked" else 120)
    lines = (folder / "out.jsonl").read_text(encoding="utf-8").splitlines()
    session, result, stats = opencode_stats(lines)
    stats.update({"agent": "opencode", "model": model, "session": session, "outcome": outcome,
                  "wall_minutes": round((time.monotonic() - started) / 60, 1)})
    (folder / "result.txt").write_text(result, encoding="utf-8")
    (folder / "session.txt").write_text(session, encoding="utf-8")
    (folder / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    tokens = stats["tokens"]
    print(f"=== {folder.name} on {model} (session {session}): {outcome}, {stats['wall_minutes']} min, "
          f"{stats['steps']} steps, {tokens['input']} input and {tokens['output']} output tokens, "
          f"{stats['tool_errors']} of {stats['tool_calls']} tool calls failed\n{result}\n", flush=True)


# --- Both ----------------------------------------------------------------------------------------

def options(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    """Split the --agent, --model and --opencode-bin options from the positional arguments."""
    found = {"agent": "claude", "model": "", "opencode-bin": os.environ.get("OPENCODE_BIN", "opencode")}
    rest: list[str] = []
    args = iter(argv)
    for arg in args:
        name, _, value = arg.partition("=")
        if name.startswith("--") and name[2:] in found:
            found[name[2:]] = value or next(args, "")
        else:
            rest.append(arg)
    return found, rest


def main() -> None:
    opts, args = options(sys.argv[1:])
    agent, model, binary = opts["agent"], opts["model"], opts["opencode-bin"]
    if len(args) < 3 or args[0] not in APPS or (args[1] in ("resume", "prompt") and len(args) != 4):
        sys.exit(__doc__)
    if agent not in ("claude", "opencode"):
        sys.exit(f"Unknown agent {agent!r}: use claude or opencode.")
    app, kind = args[0], args[1]
    if kind == "drive" and app != "google-drive":
        sys.exit("drive.json runs against the Google Drive test Library only.")
    if agent == "opencode" and app not in OPENCODE_APPS:
        sys.exit("OpenCode runs against the Notion test Library only: the free route is Notion only (ADR-0007).")
    if agent == "opencode" and "/" not in model:
        sys.exit("OpenCode needs --model <provider/model>, such as opencode/glm-5.3-flash-free.")
    local = load_local()
    library: str = local["libraries"][app]
    placeholders: dict[str, str] = local.get("placeholders", {})
    env = opencode_env() if agent == "opencode" else {}

    def start(name: str, memory: bool, prompt: str) -> pathlib.Path:
        if agent == "opencode":
            folder = opencode_prepare(model, app, name, library, memory)
            opencode_run(folder, opencode_command(binary, model, prompt), env, binary, model)
        else:
            folder = prepare(app, name, library, memory)
            run(folder, command(app, prompt), app)
        return folder

    if kind == "resume":
        folder = (opencode_base(model) if agent == "opencode" else RUNS) / app / args[2]
        session = (folder / "session.txt").read_text(encoding="utf-8").strip()
        if agent == "opencode":
            opencode_run(folder, opencode_command(binary, model, args[3], session), env, binary, model, resume=True)
        else:
            run(folder, [*command(app, args[3]), "--resume", session], app, resume=True)
        return
    if kind == "prompt":
        start(args[2], True, fill(args[3], app, placeholders))
        return

    evals = {e["id"]: e for e in json.loads((HERE / f"{kind}.json").read_text(encoding="utf-8"))["evals"]}
    for eval_id in map(int, args[2:]):
        spec = evals[eval_id]
        name = f"{kind}-{eval_id}"
        base = opencode_base(model) if agent == "opencode" else RUNS
        folder = base / app / name
        folder.mkdir(parents=True, exist_ok=True)
        on = f" in OpenCode on {model}" if agent == "opencode" else ""
        lines = [f"# {kind} {eval_id} on {APPS[app]['name']}{on}", "", fill(spec["expected_output"], app, placeholders), ""]
        lines += [f"- {fill(x, app, placeholders)}" for x in spec["expectations"]]
        (folder / "expectations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        start(name, (kind, eval_id) not in NO_MEMORY, fill(spec["prompt"], app, placeholders))


if __name__ == "__main__":
    main()
