"""Opt-in: the real tool chain on a public YouTube video. Run with `uv run pytest -m live`.

Needs network and the real tools (see `post.py check`). Never touches Instagram.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import SCRIPT

VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def run_post(*args: str) -> dict[str, object]:
    done = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)
    result: dict[str, object] = json.loads(done.stdout)
    return result


@pytest.mark.live
def test_the_real_tools_read_a_public_youtube_video() -> None:
    tools = run_post("check")
    if not tools["ok"]:
        pytest.skip(f"missing tools: {tools['missing']}")

    result = run_post("read", VIDEO)
    try:
        assert result["status"] == "ok", result.get("reason")
        assert result["link"] == VIDEO
        assert result["author"] == "Rick Astley"
        assert result["transcript"]
        assert result["keyframes"]
        assert Path(str(result["thumbnail"])).is_file()
    finally:
        run_post("clean", str(result["work"]))
