#!/usr/bin/env python3
"""Stand-in for `opencode run` in the schedule script's tests.

Each call appends its argv, its stdin, its working folder, OPENCODE_DISABLE_CLAUDE_CODE, PATH,
TMPDIR and PWD to the log in $GK_FAKE_OPENCODE_LOG, then plays the next response from the list in
$GK_FAKE_OPENCODE_SCENARIO: {"events": [...], "exit": 0, "sleep": 0}. Events are printed as
JSON lines, as `opencode run --format json` prints them; a string is printed as it is.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

log = Path(os.environ["GK_FAKE_OPENCODE_LOG"])
with log.open("a", encoding="utf-8") as f:
    f.write(json.dumps({
        "argv": sys.argv[1:],
        "stdin": sys.stdin.read(),
        "cwd": os.getcwd(),
        "disable_claude_code": os.environ.get("OPENCODE_DISABLE_CLAUDE_CODE"),
        "path": os.environ.get("PATH"),
        "tmpdir": os.environ.get("TMPDIR"),
        "pwd": os.environ.get("PWD"),
    }) + "\n")

index = len(log.read_text(encoding="utf-8").splitlines()) - 1
responses: list[dict[str, Any]] = json.loads(Path(os.environ["GK_FAKE_OPENCODE_SCENARIO"]).read_text())
response = responses[min(index, len(responses) - 1)]
for event in response.get("events", []):
    print(event if isinstance(event, str) else json.dumps(event), flush=True)
time.sleep(response.get("sleep", 0))
sys.exit(response.get("exit", 0))
