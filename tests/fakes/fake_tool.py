#!/usr/bin/env python3
"""Stand-in for yt-dlp, gallery-dl, Parakeet, Whisper and uv in the post script's tests.

The tool is named by the file it runs as. Each call appends its argv to the
log in $GK_FAKE_LOG and plays the next response for that tool from the
scenario in $GK_FAKE_SCENARIO:

    {"yt-dlp": [{"exit": 1, "stderr": "..."}, {"json": {...}, "media": "...", "thumbnail": "..."}]}

A response may hold: exit, stderr, json (printed; a string is printed as is),
media and thumbnail (files copied to where yt-dlp would write them), subs
(a VTT text), images (yt-dlp photo posts, gallery-dl), metadata (gallery-dl), text and
language (Parakeet and Whisper).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

tool = Path(sys.argv[0]).name
argv = sys.argv[1:]

log = Path(os.environ["GK_FAKE_LOG"])
with log.open("a") as f:
    f.write(json.dumps({"tool": tool, "argv": argv}) + "\n")

calls = [json.loads(line) for line in log.read_text().splitlines()]
index = sum(1 for c in calls if c["tool"] == tool) - 1
responses: list[dict[str, Any]] = json.loads(Path(os.environ["GK_FAKE_SCENARIO"]).read_text()).get(tool, [])
if not responses:
    sys.exit(f"fake {tool}: no response in the scenario")
response = responses[min(index, len(responses) - 1)]


def option(name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv else None


if response.get("exit", 0):
    sys.stderr.write(response.get("stderr", "") + "\n")
    sys.exit(response["exit"])

if tool == "yt-dlp":
    template = option("-o")
    assert template is not None and template.endswith(".%(ext)s"), template
    base = template[: -len(".%(ext)s")]
    raw = response.get("json", {})
    if isinstance(raw, str):  # deliberately broken output
        print(raw)
        sys.exit(0)
    info = dict(raw)
    # Like the real yt-dlp: --dump-single-json simulates, writing no files, unless --no-simulate.
    simulating = "--dump-single-json" in argv and "--no-simulate" not in argv
    if simulating:
        pass
    elif "--ignore-no-formats-error" in argv:  # a photo post: save each entry's image
        folder = Path(template).parent
        folder.mkdir(parents=True, exist_ok=True)
        for i, image in enumerate(response.get("images", []), start=1):
            shutil.copy(image, folder / f"{i:02d}{Path(image).suffix}")
    elif "--skip-download" in argv:
        langs = option("--sub-langs")
        Path(f"{base}.{langs}.vtt").write_text(response["subs"])
    else:
        if "media" in response:
            target = f"{base}{Path(response['media']).suffix}"
            shutil.copy(response["media"], target)
            info["requested_downloads"] = [{"filepath": target}]
        if "thumbnail" in response and "--write-thumbnail" in argv:
            shutil.copy(response["thumbnail"], f"{base}.jpg")
    print(json.dumps(info))

elif tool == "gallery-dl":
    folder = Path(option("-D") or ".")
    folder.mkdir(parents=True, exist_ok=True)
    for i, image in enumerate(response.get("images", []), start=1):
        image_file = folder / f"{i:02d}{Path(image).suffix}"
        shutil.copy(image, image_file)
        if "--write-metadata" in argv:
            Path(f"{image_file}.json").write_text(json.dumps(response.get("metadata", {})))

elif tool in ("mlx_whisper", "whisper-ctranslate2", "parakeet-mlx"):
    out_dir = Path(option("--output-dir") or option("--output_dir") or ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(argv[0]).stem
    result: dict[str, Any] = {"text": response.get("text", "")}
    if tool != "parakeet-mlx":  # Parakeet's JSON names no language; Whisper's does
        result.update(language=response.get("language", "en"), segments=[])
    else:
        result.update(sentences=[])
    (out_dir / f"{stem}.json").write_text(json.dumps(result))
