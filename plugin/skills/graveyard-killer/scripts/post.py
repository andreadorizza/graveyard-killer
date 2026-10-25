"""Read one post for the Worker: a link in, one JSON object and files out.

    post.py check                    which tools are missing, and how to install them
    post.py read [<link>] [--language <code>]   the link comes on stdin when left out
    post.py clean <folder>           delete a work folder that read made

Calls yt-dlp, gallery-dl, ffmpeg, ffprobe, Parakeet and Whisper as outside
programs found on PATH. Standard library only.

The caption choice, the keyframe sampling, the work-folder clean-up and the
update-and-retry on a 403 follow claude-video's /watch skill (MIT,
https://github.com/bradautomates/claude-video). No code is copied from it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from platform import machine, system
from typing import Any, TypeVar

from link import parse as parse_link

T = TypeVar("T")

MARKER = ".graveyard-killer-work"
WEB_LINK = re.compile(r"^https?://\S+$", re.IGNORECASE)
# No config file, so no cookies or login a user may have set up for yt-dlp elsewhere.
ANONYMOUS = ("--ignore-config", "--no-cookies")
AT_MOST_720P = "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b"
NOTION_UPLOAD_LIMIT = 5 * 1024 * 1024  # bytes, on Notion's Free plan
NOTION_TEXT_BLOCK = 1800  # characters per page-body block, under Notion's 2,000 limit
# Matched, in this order and ignoring case, against the tool's last error line.
NEEDS_LOGIN = ("rate-limit reached", "login required", "sign in to confirm",
               "checkpoint_required", "challenge_required", "authorizationerror")
UNAVAILABLE = ("video unavailable", "private video", "this video is private", "removed by",
               "http error 404", "404 not found", "does not exist", "this post is unavailable")
NO_VIDEO = ("no video", "unsupported url")
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
MAX_IMAGES = 10
MAX_KEYFRAMES = 8
MAX_CANDIDATES = 24  # frames looked at before near-duplicates are dropped
FRAME_SIZE = 1024  # px: frames fit in a square this size
SCENE_THRESHOLD = 0.3
# Mean difference per colour channel (0-255) below which two 16x16 thumbnails count as the same frame.
DUPLICATE_DIFFERENCE = 10


def check() -> dict[str, Any]:
    """Which tools are missing, each with the command that installs it on this computer.

    Also says whether the first-choice speech model is downloaded yet: it is over 1 GB.
    """
    ffmpeg_install = {"Darwin": "brew install ffmpeg",
                      "Windows": "winget install --id Gyan.FFmpeg --exact"}.get(system(), "sudo apt install ffmpeg")
    uv_install = ('powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
                  if system() == "Windows" else "curl -LsSf https://astral.sh/uv/install.sh | sh")
    needed = [  # (program, name shown to the user, install command)
        ("uv", "uv", uv_install),  # installs the tools below
        ("yt-dlp", "yt-dlp", "uv tool install yt-dlp"),
        ("gallery-dl", "gallery-dl", "uv tool install gallery-dl"),
        ("ffmpeg", "ffmpeg", ffmpeg_install),
        ("ffprobe", "ffmpeg", ffmpeg_install),  # ffprobe ships with ffmpeg
        *((engine.program, engine.name, f"uv tool install {engine.package}") for engine in engines()),
    ]
    missing: list[dict[str, str]] = []
    for program, name, install in needed:
        if not shutil.which(program) and all(m["tool"] != name for m in missing):
            missing.append({"tool": name, "install": install})
    return {"ok": not missing, "missing": missing, "speech_model": speech_model(engines()[0])}


def clean(folder: Path) -> dict[str, Any]:
    """Delete a work folder, but only one that read made: it holds the marker file."""
    if not (folder / MARKER).is_file():
        return {"error": f"{folder} is not a Graveyard Killer work folder, so it was left alone"}
    shutil.rmtree(folder)
    return {"cleaned": str(folder)}


@dataclass(frozen=True)
class Engine:
    """One speech-to-text program: how results name it, how to run it, and how to install it."""

    name: str  # "parakeet" or "whisper", as transcript_source reports it
    program: str
    package: str
    options: tuple[str, ...]  # model and JSON output; the output folder comes last
    model_cache: str | None  # Hugging Face cache folder of its model, when known


PARAKEET = Engine("parakeet", "parakeet-mlx", "parakeet-mlx",
                  ("--model", "mlx-community/parakeet-tdt-0.6b-v3", "--output-format", "json", "--output-dir"),
                  "models--mlx-community--parakeet-tdt-0.6b-v3")
MLX_WHISPER = Engine("whisper", "mlx_whisper", "mlx-whisper",
                     ("--model", "mlx-community/whisper-large-v3-turbo", "--output-format", "json",
                      "--output-dir"),
                     "models--mlx-community--whisper-large-v3-turbo")
CT2_WHISPER = Engine("whisper", "whisper-ctranslate2", "whisper-ctranslate2",
                     ("--model", "large-v3-turbo", "--output_format", "json", "--output_dir"),
                     None)
# Parakeet-TDT v3's 25 European languages, as ISO 639-1 codes.
PARAKEET_LANGUAGES = {"bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr", "hr", "hu", "it",
                      "lt", "lv", "mt", "nl", "pl", "pt", "ro", "ru", "sk", "sl", "sv", "uk"}


def engines() -> list[Engine]:
    """The engines this computer needs, first choice first.

    On Apple Silicon, Parakeet: faster than Whisper and much less prone to writing
    words over music or silence. Whisper turbo covers the languages Parakeet lacks.
    Elsewhere, Whisper turbo alone.
    """
    if system() == "Darwin" and machine() == "arm64":
        return [PARAKEET, MLX_WHISPER]
    return [CT2_WHISPER]


def engine_for(language: str | None) -> Engine:
    """Parakeet for its own languages and for an unknown one; Whisper for any other."""
    first = engines()[0]
    if first is PARAKEET and (language is None or language.split("-")[0].lower() in PARAKEET_LANGUAGES):
        return PARAKEET
    return engines()[-1]


def speech_model(engine: Engine) -> str:
    if engine.model_cache is None:
        return "unknown"
    cache = os.environ.get("HF_HUB_CACHE") or Path(
        os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub"
    return "downloaded" if (Path(cache) / engine.model_cache).is_dir() else "not downloaded"


def read(link: str, language: str | None = None) -> dict[str, Any]:
    if not WEB_LINK.match(link):
        # Refused before any tool runs: a "link" such as "--exec=..." would be read as an option.
        return {"status": "error", "reason": "not a web link", "link": link, "work": None}
    folder = new_work_folder()
    try:
        return read_post(link, folder, language)
    except FileNotFoundError as missing:
        return not_ok(link, folder, f"{missing.filename} is not installed")
    except subprocess.CalledProcessError as broken:
        output = broken.stderr
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return not_ok(link, folder, output or str(broken))
    except Exception as unexpected:  # odd tool output must still end in JSON, never a traceback
        return not_ok(link, folder, f"{type(unexpected).__name__}: {unexpected}")


def read_post(link: str, folder: Path, language: str | None) -> dict[str, Any]:
    downloaded = download(link, folder)
    if downloaded.returncode != 0 and "http error 403" in last_error(downloaded.stderr).lower():
        # Sites often break older yt-dlp releases: update once, then retry once.
        subprocess.run(["uv", "tool", "upgrade", "yt-dlp"], capture_output=True)
        downloaded = download(link, folder)
    if downloaded.returncode != 0:
        if matches(last_error(downloaded.stderr), NO_VIDEO):
            return read_photos(link, folder)
        return not_ok(link, folder, downloaded.stderr)
    info = json.loads(downloaded.stdout)
    if info.get("_type") in ("playlist", "multi_video"):
        return read_photos(info.get("webpage_url") or link, folder)
    return read_video(link, info, folder, language)


def read_video(link: str, info: dict[str, Any], folder: Path, hint: str | None) -> dict[str, Any]:
    canonical = parse_link(info.get("webpage_url") or link)
    media = Path(info["requested_downloads"][0]["filepath"])
    transcript, source, language = None, "none", None
    track = caption_track(info)
    if track:
        key, source = track
        transcript, language = captions(info["webpage_url"], key, source, folder), info["language"]
    elif has_audio(media):
        transcript, language, source = transcribe(media, folder / "transcript", hint or info.get("language"))
    frames = keyframes(media, folder / "frames")
    return ok(
        canonical, folder, "video", frames, thumbnail(folder / "media.jpg", frames, folder / "thumbnail.jpg"),
        author=author_of(info, canonical["platform"]),
        title=info.get("title"),
        caption=info.get("description") or "",
        duration=info.get("duration"),
        transcript=transcript,
        transcript_source=source,
        transcript_language=language,
    )


def read_photos(link: str, folder: Path) -> dict[str, Any]:
    """Photo posts and carousels: yt-dlp downloads video only, so gallery-dl takes over."""
    images_dir = folder / "images"
    fetched = subprocess.run(
        ["gallery-dl", "--config-ignore", "--write-metadata", "-D", str(images_dir), "--", link],
        capture_output=True, text=True,
    )
    if fetched.returncode != 0:
        return not_ok(link, folder, fetched.stderr)
    images = sorted(f for f in images_dir.glob("*") if f.suffix.lower() in IMAGE_TYPES)[:MAX_IMAGES]
    if not images:
        return not_ok(link, folder, "gallery-dl found no images in the post")
    metadata_file = Path(f"{images[0]}.json")
    metadata: dict[str, Any] = json.loads(metadata_file.read_text()) if metadata_file.exists() else {}
    frames_dir = folder / "frames"
    frames_dir.mkdir()
    frames = []
    for i, image in enumerate(images, start=1):
        frame = frames_dir / f"{i:02d}.jpg"
        save_jpeg(image, frame, FRAME_SIZE)
        frames.append(frame)
    return ok(
        parse_link(link), folder, "photos", frames, thumbnail(images[0], frames, folder / "thumbnail.jpg"),
        author=first_text(metadata, "username", "uploader", "author", "user"),
        title=None,
        caption=first_text(metadata, "description", "desc", "content", "caption") or "",
        duration=None,
        transcript=None,
        transcript_source="none",
        transcript_language=None,
    )


def ok(canonical: dict[str, Any], folder: Path, kind: str, frames: list[Path], thumb: Path,
       **post: Any) -> dict[str, Any]:
    """The result for a post that was read: what every kind shares, plus the post's own fields."""
    return {
        "status": "ok",
        "platform": canonical["platform"],
        "link": canonical["link"],
        "id": canonical["id"],
        "kind": kind,
        **post,
        "transcript_blocks": blocks(post.get("transcript") or ""),
        "keyframes": [str(f) for f in frames],
        "thumbnail": str(thumb),
        "cover_url": cover_url(canonical),
        "work": str(folder),
    }


def cover_url(canonical: dict[str, Any]) -> str | None:
    """A cover image link that will not expire, for platforms that have one.

    Notion's connector sets a cover only from an external link. YouTube's image
    host is stable; Instagram's and TikTok's links are signed and expire.
    """
    if canonical["platform"] == "youtube" and canonical["id"]:
        return f"https://i.ytimg.com/vi/{canonical['id']}/hqdefault.jpg"
    return None


def blocks(text: str) -> list[str]:
    """The text in pieces of at most NOTION_TEXT_BLOCK characters, split between sentences."""
    pieces: list[str] = []
    current = ""
    for sentence in re.split(r"(?<=[.!?…])\s+", text.strip()):
        while len(sentence) > NOTION_TEXT_BLOCK:  # one sentence too long for a block: cut at a space
            cut = sentence.rfind(" ", 0, NOTION_TEXT_BLOCK)
            if cut <= 0:
                cut = NOTION_TEXT_BLOCK
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:cut])
            sentence = sentence[cut:].lstrip()
        if current and len(current) + 1 + len(sentence) > NOTION_TEXT_BLOCK:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
    if current:
        pieces.append(current)
    return pieces


def first_text(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, dict):
            value = value.get("unique_id") or value.get("uniqueId") or value.get("name")
        if value:
            return str(value)
    return None


def matches(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in patterns)


def caption_track(info: dict[str, Any]) -> tuple[str, str] | None:
    """One caption track in the video's own language: the creator's, else the automatic one.

    At most one track, as claude-video chooses. Returns the track's key and its source, "captions" or "auto_captions".
    """
    language = info.get("language")
    if not language:
        return None
    for field, source in (("subtitles", "captions"), ("automatic_captions", "auto_captions")):
        for key in info.get(field) or {}:
            # Automatic captions in the original language end in "-orig"; others are translations.
            if key == language or key.startswith(f"{language}-"):
                return str(key), source
    return None


def captions(link: str, track: str, source: str, folder: Path) -> str:
    which = "--write-subs" if source == "captions" else "--write-auto-subs"
    subprocess.run(
        ["yt-dlp", *ANONYMOUS, "--skip-download", which, "--sub-langs", track, "--sub-format", "vtt",
         "--no-warnings", "-o", str(folder / "subs.%(ext)s"), "--", link],
        capture_output=True, text=True, check=True,
    )
    return vtt_text((folder / f"subs.{track}.vtt").read_text())


def vtt_text(vtt: str) -> str:
    """Caption text without timings, tags, or the lines automatic captions repeat."""
    lines: list[str] = []
    for line in vtt.splitlines():
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        if line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if not lines or lines[-1] != line:
            lines.append(line)
    return " ".join(lines)


def download(link: str, folder: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["yt-dlp", *ANONYMOUS, "--no-simulate", "--dump-single-json", "--no-warnings", "--no-progress",
         "-f", AT_MOST_720P, "--write-thumbnail", "--convert-thumbnails", "jpg", "--playlist-items", "1",
         "-o", str(folder / "media.%(ext)s"), "--", link],
        capture_output=True, text=True,
    )


def not_ok(link: str, folder: Path, tool_output: str) -> dict[str, Any]:
    """The result for a post that could not be read: unavailable, needs_login or error."""
    reason = last_error(tool_output)
    if matches(reason, NEEDS_LOGIN):
        status = "needs_login"
    elif matches(reason, UNAVAILABLE):
        status = "unavailable"
    else:
        status = "error"
    canonical = parse_link(link)
    return {
        "status": status,
        "reason": reason,
        "platform": canonical.get("platform"),
        "link": canonical.get("link", link),
        "id": canonical.get("id"),
        "work": str(folder),
    }


def last_error(tool_output: str) -> str:
    lines = [line.strip() for line in tool_output.splitlines() if line.strip()]
    errors = [line for line in lines if "ERROR" in line or "error" in line] or lines or ["unknown error"]
    return errors[-1][:300]


def thumbnail(written: Path, frames: list[Path], out: Path) -> Path:
    """A JPEG under Notion's 5 MiB upload limit, from the post's thumbnail or its first keyframe."""
    source = written if written.exists() else frames[0]
    for box in (1280, 640):
        save_jpeg(source, out, box, quality=4)
        if out.stat().st_size < NOTION_UPLOAD_LIMIT:
            break
    return out


def keyframes(media: Path, out_dir: Path) -> list[Path]:
    """The first frame and one frame per scene, near-duplicates dropped, then at most MAX_KEYFRAMES.

    A clip with fewer than three scenes is sampled evenly instead. Dropping duplicates
    before the cap keeps the cap for frames that differ (as claude-video does).
    """
    out_dir.mkdir()
    times = [0.0, *scene_changes(media)]
    if len(times) < 3:
        length = duration_of(media)
        times = [length * i / MAX_KEYFRAMES for i in range(MAX_KEYFRAMES)]
    kept: list[Path] = []
    last: bytes | None = None
    for i, time in enumerate(evenly(times, MAX_CANDIDATES), start=1):
        frame = out_dir / f"{i:02d}.jpg"
        save_jpeg(media, frame, FRAME_SIZE, at=time)
        if not frame.exists():
            continue
        thumb = tiny(frame)
        if last is not None and difference(thumb, last) < DUPLICATE_DIFFERENCE:
            frame.unlink()
            continue
        kept.append(frame)
        last = thumb
    chosen = evenly(kept, MAX_KEYFRAMES)
    for frame in set(kept) - set(chosen):
        frame.unlink()
    return chosen


def evenly(items: list[T], most: int) -> list[T]:
    """At most `most` items, spread evenly and always keeping the first."""
    if len(items) <= most:
        return items
    step = len(items) / most
    return [items[int(i * step)] for i in range(most)]


def scene_changes(media: Path) -> list[float]:
    scan = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(media), "-an",
         "-vf", f"scale=160:-2,select='gt(scene,{SCENE_THRESHOLD})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", scan.stderr)]


def duration_of(media: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(media)],
        capture_output=True, text=True, check=True,
    )
    return float(probe.stdout.strip() or 0)


def tiny(image: Path) -> bytes:
    """A 16x16 RGB thumbnail, for spotting near-duplicate frames."""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(image), "-vf", "scale=16:16", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout


def difference(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / max(len(a), 1)


def save_jpeg(source: Path, out: Path, box: int, quality: int = 3, at: float | None = None) -> None:
    """One frame of source (at a time in seconds, for video) as a JPEG that fits a box x box square."""
    seek = ["-ss", f"{at:.3f}"] if at is not None else []
    fit = (f"scale='min({box},iw)':'min({box},ih)'"
           ":force_original_aspect_ratio=decrease:force_divisible_by=2")
    run_ffmpeg(*seek, "-i", str(source), "-frames:v", "1", "-vf", fit, "-q:v", str(quality), str(out))


def run_ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, check=True)


def has_audio(media: Path) -> bool:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(media)],
        capture_output=True, text=True, check=True,
    )
    return bool(probe.stdout.strip())


def transcribe(media: Path, out_dir: Path, language: str | None) -> tuple[str, str | None, str]:
    """The speech in media, the language it is in when known, and the engine's name."""
    out_dir.mkdir()
    engine = engine_for(language)
    command = [engine.program, str(media), *engine.options, str(out_dir)]
    if language and engine.name == "whisper":  # Parakeet takes no language option
        command += ["--language", language]
    subprocess.run(command, capture_output=True, text=True, check=True)
    result = json.loads((out_dir / f"{media.stem}.json").read_text())
    return str(result.get("text", "")).strip(), result.get("language") or language, engine.name


def author_of(info: dict[str, Any], platform: str) -> str | None:
    # Instagram's uploader is the display name; its channel is the account handle.
    first, second = ("channel", "uploader") if platform == "instagram" else ("uploader", "channel")
    value = info.get(first) or info.get(second)
    return str(value) if value else None


def new_work_folder() -> Path:
    """A fresh temporary folder, marked so that clean will delete it and nothing else."""
    folder = Path(tempfile.mkdtemp(prefix="graveyard-killer-"))
    (folder / MARKER).write_text("")
    return folder.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(prog="post.py")
    commands = parser.add_subparsers(dest="command", required=True)
    read_parser = commands.add_parser("read")
    read_parser.add_argument("link", nargs="?", help="the Entry's Link; read from stdin when left out")
    read_parser.add_argument("--language", help="the spoken language when known, such as it")
    commands.add_parser("check")
    clean_parser = commands.add_parser("clean")
    clean_parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        print(json.dumps(check()))
    elif args.command == "clean":
        result = clean(args.folder)
        print(json.dumps(result))
        if "error" in result:
            sys.exit(2)
    else:
        link = args.link if args.link is not None else sys.stdin.read().strip()
        print(json.dumps(read(link, args.language)))


if __name__ == "__main__":
    main()
