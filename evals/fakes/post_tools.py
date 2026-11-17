#!/usr/bin/env python3
"""Stand-in for yt-dlp, gallery-dl, Parakeet and Whisper when the evals run with fake posts.

run_evals.py copies this file into <run>/fakes/bin under each tool's name, writes fakes.json
next to the copies and puts that folder first on PATH, so post.py runs these instead of the
real tools and downloads nothing. The tool is named by the file it runs as.

Each call appends its argv, the post it matched and its working folder to the log that
fakes.json names. The answers come from the recorded posts in evals/fixtures/posts/<name>/post.json,
matched by link.py's platform and id. Any other link fails as a real download that went wrong
does: an ERROR line and exit code 1, which post.py reports as `error`. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, NoReturn

HERE = Path(__file__).parent
CONFIG: dict[str, str] = json.loads((HERE / "fakes.json").read_text(encoding="utf-8"))
sys.path.insert(0, CONFIG["scripts"])
from link import parse  # noqa: E402  The skill's own link.py, so a post matches however its link is written.

FIXTURES = Path(CONFIG["fixtures"])
TOOL = Path(sys.argv[0]).name
ARGV = sys.argv[1:]
SPEECH = ("parakeet-mlx", "mlx_whisper", "whisper-ctranslate2")


def log(post: str | None, link: str | None) -> None:
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "tool": TOOL, "argv": ARGV, "link": link,
             "post": post, "cwd": os.getcwd()}
    with open(CONFIG["log"], "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def fail(message: str, code: int = 1) -> NoReturn:
    sys.stderr.write(message + "\n")
    sys.exit(code)


def option(name: str) -> str | None:
    return ARGV[ARGV.index(name) + 1] if name in ARGV and ARGV.index(name) + 1 < len(ARGV) else None


def posts() -> list[tuple[Path, dict[str, Any]]]:
    found = []
    for path in sorted(FIXTURES.glob("*/post.json")):
        found.append((path.parent, json.loads(path.read_text(encoding="utf-8"))))
    return found


def key(link: str) -> tuple[Any, Any]:
    parsed = parse(link)
    return parsed.get("platform"), parsed.get("id") or parsed.get("link")


def post_for(link: str) -> tuple[Path, dict[str, Any]] | None:
    wanted = key(link)
    return next(((folder, post) for folder, post in posts() if key(post["link"]) == wanted), None)


def not_recorded(link: str) -> NoReturn:
    fail(f"ERROR: [fake-posts] {link}: no recorded post for this link. Add one to evals/fixtures/posts, "
         "or run the eval with --live-posts")


def yt_dlp() -> None:
    if len(ARGV) < 2 or ARGV[-2] != "--":
        log(None, None)
        fail("fake yt-dlp: post.py always ends its call with -- <link>", 2)
    link = ARGV[-1]
    found = post_for(link)
    log(found[0].name if found else None, link)
    if found is None:
        not_recorded(link)
    folder, post = found
    if "error" in post:
        fail(post["error"])
    template = option("-o")
    if template is None or not template.endswith(".%(ext)s"):
        fail(f"fake yt-dlp: unexpected -o {template}", 2)
    base = template[: -len(".%(ext)s")]
    info: dict[str, Any] = dict(post["info"])
    if "--ignore-no-formats-error" in ARGV:  # post.py's photo read: yt-dlp saves each slide's image
        target = Path(template).parent
        target.mkdir(parents=True, exist_ok=True)
        for i, image in enumerate(post.get("images", []), start=1):
            shutil.copy(folder / image, target / f"{i:02d}{Path(image).suffix}")
    elif post.get("images"):  # a photo post has no video, so the video download fails
        fail(f"ERROR: [{info.get('extractor_key', 'generic')}] {info.get('id')}: No video formats found!")
    elif "--skip-download" in ARGV:  # the caption track, written as yt-dlp names it
        track = option("--sub-langs") or ""
        text = post.get("subtitles", {}).get(track)
        if text is None:
            fail(f"ERROR: [fake-posts] {link}: no recorded caption track {track}")
        Path(f"{base}.{track}.vtt").write_text(text, encoding="utf-8")
    else:
        media = folder / post["media"]
        target_file = f"{base}{media.suffix}"
        shutil.copy(media, target_file)
        info["requested_downloads"] = [{"filepath": target_file}]
        if post.get("thumbnail") and "--write-thumbnail" in ARGV:
            shutil.copy(folder / post["thumbnail"], f"{base}.jpg")
    print(json.dumps(info))


def gallery_dl() -> None:
    link = ARGV[-1] if ARGV else ""
    found = post_for(link) if link.startswith("http") else None
    log(found[0].name if found else None, link)
    if found is None or not found[1].get("images"):
        not_recorded(link)
    folder, post = found
    target = Path(option("-D") or ".")
    target.mkdir(parents=True, exist_ok=True)
    info = post["info"]
    for i, image in enumerate(post["images"], start=1):
        saved = target / f"{i:02d}{Path(image).suffix}"
        shutil.copy(folder / image, saved)
        if "--write-metadata" in ARGV:
            metadata = {"username": info.get("channel"), "description": info.get("description", "")}
            Path(f"{saved}.json").write_text(json.dumps(metadata), encoding="utf-8")


def speech() -> None:
    """The recorded transcript of the post whose media file this is, found by its content."""
    media = Path(ARGV[0]) if ARGV else Path()
    digest = hashlib.sha256(media.read_bytes()).hexdigest() if media.is_file() else ""
    found = next(((folder, post) for folder, post in posts()
                  if post.get("media") and hashlib.sha256((folder / post["media"]).read_bytes()).hexdigest() == digest),
                 None)
    log(found[0].name if found else None, None)
    if found is None or "speech" not in found[1]:
        fail(f"fake {TOOL}: no recorded speech for {media}")
    recorded = found[1]["speech"]
    out_dir = Path(option("--output-dir") or option("--output_dir") or ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"text": recorded["text"]}
    if TOOL == "parakeet-mlx":  # Parakeet's JSON names no language; Whisper's does
        result["sentences"] = []
    else:
        result.update(language=recorded.get("language") or "en", segments=[])
    (out_dir / f"{media.stem}.json").write_text(json.dumps(result), encoding="utf-8")


def main() -> None:
    if TOOL == "yt-dlp":
        yt_dlp()
    elif TOOL == "gallery-dl":
        gallery_dl()
    elif TOOL in SPEECH:
        speech()
    else:
        log(None, None)
        fail(f"fake-posts has no stand-in for {TOOL}", 2)


if __name__ == "__main__":
    main()
