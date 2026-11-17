"""Read one post for the Worker: a link in, one JSON object and files out.

    post.py check                    which tools are missing, and how to install them
    post.py read [<link>] [--language <code>] [--login <browser>]   the link comes on stdin when left out
    post.py clean <folder>           delete a work folder that read made
    post.py pause [--login]          wait a random 6 to 12 seconds, between Instagram posts,
                                     or 30 to 90 seconds before a login read
    post.py upload <image> <upload-url> --header "<name>: <value>" ...
                                     send an image that read made to a Notion upload URL
    post.py notify [<title> <line>]  show a desktop notification: a title, then one line, on stdin
                                     when left out

A read is logged out, unless --login names a browser on this computer that is signed in
to Instagram: then it is a login read of an Instagram post (ADR 0001, #13).

Calls yt-dlp, gallery-dl, ffmpeg, ffprobe, Parakeet and Whisper as outside
programs found on PATH. When Windows Smart App Control blocks a tool that uv
installed, it runs the tool through the Python of its uv tool environment
instead (see run). Standard library only.

The caption choice, the keyframe sampling, the work-folder clean-up and the
update-and-retry on a 403 follow claude-video's /watch skill (MIT,
https://github.com/bradautomates/claude-video). No code is copied from it.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from platform import machine, system
from typing import Any, TypeVar
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from link import TIKTOK_SHORT_HOSTS
from link import parse as parse_link

T = TypeVar("T")

MARKER = ".graveyard-killer-work"
PLATFORMS = ("instagram", "tiktok", "youtube")  # the only links read downloads
WEB_LINK = re.compile(r"^https?://\S+$", re.IGNORECASE)
# No config file, so no cookies or login a user may have set up for yt-dlp elsewhere.
ANONYMOUS = ("--ignore-config", "--no-cookies")
# On 2026-11-14 a read sat at 0% CPU for 1 h 46 min and blocked a whole Worker run. A stalled
# connection now fails after this many seconds of silence, and every tool has a time limit.
NETWORK_TIMEOUT = "30"  # yt-dlp --socket-timeout, gallery-dl --http-timeout
YT_DLP = (*ANONYMOUS, "--socket-timeout", NETWORK_TIMEOUT)
GALLERY_DL = ("--config-ignore", "--http-timeout", NETWORK_TIMEOUT)
# Login reads. The browsers whose cookies both yt-dlp and gallery-dl can read (their cookies.py,
# yt-dlp 2026.10.21 and gallery-dl 1.32.17, checked 2026-11-16).
BROWSERS = ("brave", "chrome", "chromium", "edge", "firefox", "opera", "safari", "vivaldi")
# A browser, then optionally ":" and a profile name of letters, digits, spaces, dots, dashes and
# underscores that starts with a letter or digit. So no path, keyring, container or tool option.
BROWSER_VALUE = re.compile(r"(?P<browser>[A-Za-z]+)(?::(?P<profile>[^\W_][\w .-]{0,63}))?")
# A tool's warning that it could not use the browser's login: gallery-dl's "cookies: ..." lines,
# and yt-dlp's from cookies.py and its Instagram extractor (2026.10.21). Both tools then go on
# logged out, so a gated post looks hidden even from the login, or the login page looks like a
# challenge to the account. A login read with such a warning is a browser problem instead.
COOKIE_WARNING = re.compile(
    r"\]\[warning\] cookies:|^WARNING: .*(find-generic-password|cannot decrypt v1\d cookies|failed to decrypt cookie"
    r"|unknown cookie version|without sqlite3 support|cookies database version|networkwallet|kwallet"
    r"|account cookies are no longer valid)", re.IGNORECASE)
MINUTE = 60
TIME_LIMITS = {"yt-dlp": 20 * MINUTE, "gallery-dl": 10 * MINUTE, "uv": 5 * MINUTE,
               "ffmpeg": 15 * MINUTE, "ffprobe": 2 * MINUTE}
SPEECH_TIME_LIMIT = 60 * MINUTE  # Parakeet or Whisper, on a long video and a slow computer
NOTIFY_TIME_LIMIT = 30  # seconds for osascript, notify-send or PowerShell to show one notification
# Seconds between Instagram posts, as gallery-dl waits between Instagram requests (ADR 0001).
PAUSE = (6.0, 12.0)
# Seconds before a login read, on top of PAUSE. A choice, not a measurement: no safe rate is known.
LOGIN_PAUSE = (30.0, 90.0)
AT_MOST_720P = "bv*[height<=720]+ba/b[height<=720]/bv*+ba/b"
NOTION_UPLOAD_LIMIT = 5 * 1024 * 1024  # bytes, on Notion's Free plan
NOTION_UPLOAD_HOST = "api.notion.com"  # where the Notion connector's file uploads are sent
UPLOAD_TIMEOUT = 120  # seconds
UPLOAD_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}  # what read writes
NOTION_TEXT_BLOCK = 1800  # characters per page-body block, under Notion's 2,000 limit
# Matched, in this order and ignoring case, against the tool's last error line.
# A post Instagram hides from logged-out visitors, such as one with an age limit: yt-dlp finds
# no media for them (if_not_gated_logged_out). An Instagram change once gave it for public
# posts too (yt-dlp #17074), so the Worker stops Instagram after two new ones in a row.
LOGIN_ONLY = ("instagram sent an empty media response",)
NEEDS_LOGIN = ("rate-limit reached", "login required", "requiring login", "redirect to login",
               "/accounts/login", "only available for registered users", "sign in to confirm",
               "checkpoint_required", "challenge_required", "authorizationerror")
UNAVAILABLE = ("video unavailable", "video is unavailable", "private video", "this video is private", "removed by",
               "http error 404", "404 not found", "does not exist", "this post is unavailable")
NO_VIDEO = ("no video", "unsupported url")
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_TYPES = {".mp4", ".mov", ".m4v", ".webm"}
MAX_IMAGES = 10
MAX_KEYFRAMES = 8
MAX_CANDIDATES = 24  # frames looked at before near-duplicates are dropped
FRAME_SIZE = 1024  # px: frames fit in a square this size
SCENE_THRESHOLD = 0.3
# Mean difference per colour channel (0-255) below which two 16x16 thumbnails count as the same frame.
DUPLICATE_DIFFERENCE = 10
# Windows error ERROR_SYSTEM_INTEGRITY_POLICY_VIOLATION: Smart App Control refused to start a program.
BLOCKED_BY_APP_CONTROL = 4551
# Runs a console script by name inside its own Python, the way its launcher would.
# `python -c` puts the working folder first on sys.path and a launcher does not: the empty
# entry goes first, so a .py file in that folder cannot replace a module the tool imports.
CONSOLE_SCRIPT = ("import sys; sys.path[:] = [p for p in sys.path if p]; "
                  "from importlib.metadata import entry_points; sys.argv = sys.argv[1:]; "
                  "sys.exit(entry_points(group='console_scripts')[sys.argv[0]].load()())")


class BlockedTool(Exception):
    """Windows Smart App Control refused a tool, and post.py found no other way to run it."""


class ToolTimedOut(Exception):
    """A tool ran past its time limit, and post.py stopped it."""


def time_limit(program: str) -> float:
    """Seconds program may run. GK_TIME_LIMIT, in seconds, replaces every limit (for the tests)."""
    if os.environ.get("GK_TIME_LIMIT"):
        return float(os.environ["GK_TIME_LIMIT"])
    name = Path(program).name.lower().removesuffix(".exe")
    return TIME_LIMITS.get(name, SPEECH_TIME_LIMIT)


def run(command: list[str], **options: Any) -> subprocess.CompletedProcess[Any]:
    """Run a tool within its time limit. ToolTimedOut names a tool that ran past it."""
    program = command[0]
    options.setdefault("timeout", time_limit(program))
    try:
        return run_unblocked(command, **options)
    except subprocess.TimeoutExpired as slow:
        limit = float(options["timeout"])
        took = f"{limit / MINUTE:g} minutes" if limit >= MINUTE else f"{limit:g} seconds"
        raise ToolTimedOut(f"{Path(program).name} ran for more than {took} and was stopped") from slow


def run_unblocked(command: list[str], **options: Any) -> subprocess.CompletedProcess[Any]:
    """subprocess.run, except for a tool that Windows Smart App Control blocks.

    Once Smart App Control is on, it blocks the unsigned launchers that uv puts on PATH
    (yt-dlp.exe, gallery-dl.exe, whisper-ctranslate2.exe), while the Python inside each
    tool's environment still runs. So a blocked tool is run again through that Python.
    BlockedTool, which names the tool, means that this failed too or was not possible.
    """
    program = command[0]
    try:
        return subprocess.run(command, **options)
    except OSError as refused:
        if not blocked_by_app_control(refused):
            raise
        python = tool_python(program)
        if python is None:
            raise BlockedTool(f"Windows Smart App Control blocked {program}, and no uv tool environment "
                              "provides it, so it could not run through Python instead") from refused
        try:
            return subprocess.run([str(python), "-c", CONSOLE_SCRIPT, *command], **options)
        except OSError as again:
            if not blocked_by_app_control(again):
                raise
            raise BlockedTool(f"Windows Smart App Control blocked {program}, and also the Python of its "
                              f"uv tool environment, {python}") from again


def blocked_by_app_control(error: OSError) -> bool:
    return getattr(error, "winerror", None) == BLOCKED_BY_APP_CONTROL


def tool_python(program: str) -> Path | None:
    """The Python of the uv tool environment that provides program, when there is one.

    The environment named after the program comes first: a tool that depends on the
    program, such as one installed with --with yt-dlp, has its own copy, perhaps older.
    """
    for tools in tool_dirs():
        if not tools.is_dir():
            continue
        for environment in [tools / program, *sorted(tools.iterdir())]:
            scripts = environment / "Scripts"
            if (scripts / f"{program}.exe").is_file() and (scripts / "python.exe").is_file():
                return scripts / "python.exe"
    return None


def tool_dirs() -> list[Path]:
    """Where uv may keep its tool environments on Windows.

    UV_TOOL_DIR when it is set. Otherwise uv's storage reference names %APPDATA%\\uv\\data\\tools,
    and %APPDATA%\\uv\\tools, where the Smart App Control fallback was first tested, is tried too.
    """
    if os.environ.get("UV_TOOL_DIR"):
        return [Path(os.environ["UV_TOOL_DIR"])]
    appdata = Path(os.environ.get("APPDATA", ""))
    return [appdata / "uv" / "data" / "tools", appdata / "uv" / "tools"]


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


def missing_tools() -> str:
    """The tools that read needs and cannot find, for the error message.

    Windows leaves FileNotFoundError.filename empty, so the name comes from a lookup.
    It only looks for .exe files, the only kind post.py starts on Windows, and runs nothing.
    """
    names = ["yt-dlp", "gallery-dl", "ffmpeg", "ffprobe", *(engine.program for engine in engines())]
    suffix = ".exe" if system() == "Windows" else ""
    gone = [name for name in names if not shutil.which(name + suffix)]
    return ", ".join(gone) or "a tool"


@dataclass(frozen=True)
class Access:
    """How the tools reach the platform: logged out, or with a browser's cookies for a login read."""

    yt_dlp: tuple[str, ...]
    gallery_dl: tuple[str, ...]
    login: bool
    # yt-dlp's warnings stay on for a login read, to tell a browser problem from a gated post.
    quiet: tuple[str, ...] = ("--no-warnings",)


LOGGED_OUT = Access(YT_DLP, GALLERY_DL, login=False)


def login_access(value: str) -> Access | None:
    """The tools with the cookies of the browser profile that value names, or None for a bad value.

    Both tools still ignore their config files. gallery-dl loads only Instagram's cookies, and for
    Firefox it reads every container, as yt-dlp does by default, so both tools see the same login.
    yt-dlp loads every cookie of the browser, so it may use only its Instagram extractor.
    Neither gets --cookies <file>, so no cookie file is written: yt-dlp reads a copy of the
    browser's cookie database in a temporary folder that it deletes itself.
    """
    found = BROWSER_VALUE.fullmatch(value)
    if not found or found["browser"].lower() not in BROWSERS:
        return None
    browser, profile = found["browser"].lower(), found["profile"]
    in_profile = f":{profile}" if profile else ""
    every_container = "::all" if browser == "firefox" else ""
    return Access(
        ("--ignore-config", "--use-extractors", "Instagram", "--cookies-from-browser", browser + in_profile,
         "--socket-timeout", NETWORK_TIMEOUT),
        ("--config-ignore", "--cookies-from-browser", f"{browser}/.instagram.com{in_profile}{every_container}",
         "--http-timeout", NETWORK_TIMEOUT),
        login=True,
        quiet=(),
    )


def keep_cookie_copies_in(folder: Path) -> None:
    """Make the tools put their copy of the browser's cookie database inside the work folder.

    yt-dlp and gallery-dl copy it to a temporary folder and delete it when they finish, but not
    when post.py stops them at their time limit. Inside the work folder, clean deletes it then too.
    """
    temporary = folder / "tmp"
    temporary.mkdir()
    for name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[name] = str(temporary)


# A post's own link, one form per platform, with nothing but the post's id and, on TikTok, its author.
OWN_LINK = re.compile(r"https://www\.instagram\.com/p/[\w-]+/"
                      r"|https://www\.youtube\.com/watch\?v=[\w-]+"
                      r"|https://www\.tiktok\.com/(?:@[\w.-]+/(?:video|photo)|share/video)/\d+")


def own_link(post: dict[str, Any]) -> str | None:
    """The post's link rebuilt from its id, or None when it fits none of the forms in OWN_LINK."""
    link = str(post.get("link") or "")
    if post.get("platform") == "tiktok" and urlsplit(link).path.startswith("/share/video/"):
        link = f"https://www.tiktok.com/share/video/{post['id']}"  # an export's link keeps no query
    return link if OWN_LINK.fullmatch(link) else None


def platform_share_link(link: str) -> bool:
    """A link with no post id that the platform itself turns into a post's link: TikTok's short
    links and Instagram's /share/ links. Never Instagram's link shim, l.instagram.com, which leads
    off the platform."""
    parts = urlsplit(link)
    host = (parts.hostname or "").lower()
    if host in TIKTOK_SHORT_HOSTS:
        return True
    return host in ("instagram.com", "www.instagram.com") and parts.path.startswith("/share/")


def refused(link: str, reason: str) -> dict[str, Any]:
    """A read stopped before any tool ran."""
    return {"status": "error", "reason": reason, "link": link, "work": None}


def read(link: str, language: str | None = None, login: str | None = None) -> dict[str, Any]:
    if not WEB_LINK.match(link):
        # Refused before any tool runs: a "link" such as "--exec=..." would be read as an option.
        return refused(link, "not a web link")
    post = parse_link(link)
    if post.get("platform") not in PLATFORMS:
        # Refused before any tool runs. The Worker reads another page with its web fetch tool, and
        # where read runs outside an agent's sandbox (Codex) any other link could carry data out.
        return refused(link, "not an Instagram, TikTok or YouTube link: read the page with your web fetch tool")
    if post.get("id"):
        # The tools get the post's own link, rebuilt from its id: a link on the platform's host can
        # still redirect elsewhere, such as YouTube's /redirect or l.instagram.com.
        own = own_link(post)
        if own is None:
            return refused(link, "not a post's own link: read takes an Instagram, TikTok or YouTube post")
        link = own
    elif not platform_share_link(link):
        return refused(link, "not a post's own link: read takes an Instagram, TikTok or YouTube post, not a "
                             "profile, a search or a redirect to another site")
    access = LOGGED_OUT
    if login is not None:
        named = login_access(login)
        if named is None:
            return refused(link, "--login takes a browser that both yt-dlp and gallery-dl read, such as firefox "
                                 "or chrome:Profile 1, with a profile of letters, digits, spaces, dots, dashes "
                                 "and underscores")
        # yt-dlp loads every cookie of the browser, so a share or redirect link that led to another
        # site would read it with the user's login there: only a post's own link, read as canonical.
        post = parse_link(link)
        if post.get("platform") != "instagram" or not post.get("id"):
            return refused(link, "login reads are for an Instagram post's own link, with /p/, /reel/ or /tv/ "
                                 "in its path")
        link, access = post["link"], named
    folder = new_work_folder()
    if access.login:
        keep_cookie_copies_in(folder)
    try:
        return read_post(link, folder, language, access)
    except FileNotFoundError as missing:
        return not_ok(link, folder, f"{missing.filename or missing_tools()} is not installed")
    except subprocess.CalledProcessError as broken:
        output = broken.stderr
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return not_ok(link, folder, output or str(broken))
    except BlockedTool as blocked:
        return not_ok(link, folder, str(blocked))
    except ToolTimedOut as slow:
        return not_ok(link, folder, f"ERROR: {slow}")
    except Exception as unexpected:  # odd tool output must still end in JSON, never a traceback
        return not_ok(link, folder, f"{type(unexpected).__name__}: {unexpected}")


def read_post(link: str, folder: Path, language: str | None, access: Access) -> dict[str, Any]:
    downloaded = download(link, folder, access)
    # Sites often break older yt-dlp releases: update once, then retry once. Not on a login read,
    # where a 403 may be Instagram refusing the account: a second try would use the account again.
    if (downloaded.returncode != 0 and not access.login
            and "http error 403" in last_error(downloaded.stderr).lower()):
        try:  # the update is optional: without uv, or with uv blocked, the retry still runs
            subprocess.run(["uv", "tool", "upgrade", "yt-dlp"], capture_output=True, timeout=time_limit("uv"))
        except (OSError, subprocess.TimeoutExpired):
            pass
        downloaded = download(link, folder, access)
    if downloaded.returncode != 0:
        if matches(last_error(downloaded.stderr), NO_VIDEO):
            return read_photos(link, folder, access, language)
        result = failed(link, folder, downloaded.stderr, access)
        if access.login and result["status"] == "login_only":
            return read_gated(link, folder, language, access, downloaded.stderr)
        return result
    info = json.loads(downloaded.stdout)
    if info.get("_type") in ("playlist", "multi_video"):
        return read_photos(info.get("webpage_url") or link, folder, access, language)
    return read_video(link, info, folder, language, access)


def read_video(link: str, info: dict[str, Any], folder: Path, hint: str | None, access: Access) -> dict[str, Any]:
    canonical = parse_link(info.get("webpage_url") or link)
    media = Path(info["requested_downloads"][0]["filepath"])
    transcript, source, language = None, "none", None
    track = caption_track(info)
    if track:
        key, source = track
        transcript, language = captions(info["webpage_url"], key, source, folder, access), info["language"]
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


def read_photos(link: str, folder: Path, access: Access, language: str | None = None) -> dict[str, Any]:
    """Photo posts and carousels: yt-dlp downloads no video, but saves each slide's image.

    gallery-dl reads the posts yt-dlp returns no images for. Checked without a login
    on a real 7-slide Instagram carousel, 2026-10-25.
    """
    images_dir = folder / "images"
    asked = run(
        # --no-simulate: without it, --dump-single-json writes no files at all.
        ["yt-dlp", *access.yt_dlp, "--ignore-no-formats-error", "--skip-download", "--no-simulate",
         "--dump-single-json", *access.quiet, "--write-thumbnail", "--convert-thumbnails", "jpg",
         "-o", str(images_dir / "%(playlist_index)02d.%(ext)s"), "--", link],
        capture_output=True, text=True,
    )
    if asked.returncode != 0 and matches(last_error(asked.stderr), LOGIN_ONLY + NEEDS_LOGIN):
        result = failed(link, folder, asked.stderr, access)
        if access.login and result["status"] == "login_only":
            return read_gated(link, folder, language, access, asked.stderr)
        return result  # logged out, gallery-dl would only meet Instagram's login page
    info: dict[str, Any] = json.loads(asked.stdout) if asked.returncode == 0 and asked.stdout.strip() else {}
    images = images_in(images_dir)
    if images:
        canonical = parse_link(info.get("webpage_url") or link)
        return photos(canonical, folder, images, author_of(info, canonical["platform"]),
                      info.get("description") or "")
    fetched = run(
        ["gallery-dl", *access.gallery_dl, "--write-metadata", "-D", str(images_dir), "--", link],
        capture_output=True, text=True,
    )
    if fetched.returncode != 0:
        return failed(link, folder, fetched.stderr, access)
    images = images_in(images_dir)
    if not images:
        return not_ok(link, folder, "no images found in the post")
    metadata_file = Path(f"{images[0]}.json")
    metadata: dict[str, Any] = json.loads(metadata_file.read_text(encoding="utf-8")) if metadata_file.exists() else {}
    return photos(parse_link(info.get("webpage_url") or link), folder, images,
                  first_text(metadata, "username", "uploader", "author", "user"),
                  first_text(metadata, "description", "desc", "content", "caption") or "")


def read_gated(link: str, folder: Path, hint: str | None, access: Access, gated: str) -> dict[str, Any]:
    """A login read that yt-dlp still found hidden: gallery-dl reads the post with the same cookies.

    With a signed-in Chrome session, yt-dlp got an empty media response for an age-limited post
    that the account sees in the browser, and gallery-dl read it (checked 2026-11-16). gallery-dl
    is asked for the merged video file: for a DASH video it would otherwise call yt-dlp's module,
    which its own install lacks. With no media, the post stays login_only.
    """
    media_dir = folder / "gallery"
    fetched = run(
        ["gallery-dl", *access.gallery_dl, "-o", "extractor.instagram.videos=merged", "--write-metadata",
         "-D", str(media_dir), "--", link],
        capture_output=True, text=True,
    )
    if fetched.returncode != 0:
        return failed(link, folder, fetched.stderr, access)
    videos = sorted(f for f in media_dir.glob("*") if f.suffix.lower() in VIDEO_TYPES) if media_dir.is_dir() else []
    images = images_in(media_dir)
    if not videos and not images:  # login_only, or error after gallery-dl's own cookie warning
        return failed(link, folder, f"{fetched.stderr}\n{gated}", access)
    first = videos[0] if videos else images[0]
    metadata_file = Path(f"{first}.json")
    metadata: dict[str, Any] = json.loads(metadata_file.read_text(encoding="utf-8")) if metadata_file.exists() else {}
    canonical = parse_link(link)
    author = first_text(metadata, "username", "uploader", "author", "user")
    caption = first_text(metadata, "description", "desc", "content", "caption") or ""
    if not videos:
        return photos(canonical, folder, images, author, caption)
    media = videos[0]
    transcript, language, source = None, None, "none"
    if has_audio(media):
        transcript, language, source = transcribe(media, folder / "transcript", hint)
    frames = keyframes(media, folder / "frames")
    return ok(
        canonical, folder, "video", frames, thumbnail(folder / "media.jpg", frames, folder / "thumbnail.jpg"),
        author=author,
        title=None,
        caption=caption,
        duration=None,
        transcript=transcript,
        transcript_source=source,
        transcript_language=language,
    )


def images_in(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(f for f in folder.glob("*") if f.suffix.lower() in IMAGE_TYPES)[:MAX_IMAGES]


def photos(canonical: dict[str, Any], folder: Path, images: list[Path], author: str | None,
           caption: str) -> dict[str, Any]:
    frames_dir = folder / "frames"
    frames_dir.mkdir()
    frames = []
    for i, image in enumerate(images, start=1):
        frame = frames_dir / f"{i:02d}.jpg"
        save_jpeg(image, frame, FRAME_SIZE)
        frames.append(frame)
    return ok(
        canonical, folder, "photos", frames, thumbnail(images[0], frames, folder / "thumbnail.jpg"),
        author=author,
        title=None,
        caption=caption,
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
        "work": str(folder),
    }


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


def captions(link: str, track: str, source: str, folder: Path, access: Access) -> str:
    which = "--write-subs" if source == "captions" else "--write-auto-subs"
    run(
        ["yt-dlp", *access.yt_dlp, "--skip-download", which, "--sub-langs", track, "--sub-format", "vtt",
         *access.quiet, "-o", str(folder / "subs.%(ext)s"), "--", link],
        capture_output=True, text=True, check=True,
    )
    # yt-dlp writes UTF-8; without the encoding, Windows would read it as its own code page.
    return vtt_text((folder / f"subs.{track}.vtt").read_text(encoding="utf-8"))


def vtt_text(vtt: str) -> str:
    """Caption text without timings, tags, or the lines automatic captions repeat."""
    lines: list[str] = []
    for line in vtt.splitlines():
        line = html.unescape(re.sub(r"<[^>]+>", "", line)).strip()  # captions keep entities such as &gt;
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit():
            continue
        if line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if not lines or lines[-1] != line:
            lines.append(line)
    return " ".join(lines)


def download(link: str, folder: Path, access: Access) -> subprocess.CompletedProcess[str]:
    return run(
        ["yt-dlp", *access.yt_dlp, "--no-simulate", "--dump-single-json", *access.quiet, "--no-progress",
         "-f", AT_MOST_720P, "--write-thumbnail", "--convert-thumbnails", "jpg", "--playlist-items", "1",
         "-o", str(folder / "media.%(ext)s"), "--", link],
        capture_output=True, text=True,
    )


def failed(link: str, folder: Path, tool_output: str, access: Access) -> dict[str, Any]:
    """not_ok for a tool that failed, except that on a login read, a gated post or a login page
    after a cookie warning is an error with that warning as its reason: the login was never used."""
    if access.login and status_of(last_error(tool_output)) in ("login_only", "needs_login"):
        warnings = [line.strip() for line in tool_output.splitlines() if COOKIE_WARNING.search(line.strip())]
        if warnings:
            return not_ok(link, folder, warnings[-1], status="error")
    return not_ok(link, folder, tool_output)


def not_ok(link: str, folder: Path, tool_output: str, status: str | None = None) -> dict[str, Any]:
    """The result for a post that could not be read: login_only, needs_login, unavailable or error.

    The status comes from the tool's last error line, unless the caller already knows it. Its work
    folder holds nothing the Worker uses, so it goes now, and `work` is null: a run that forgot to
    clean after a failed read left one behind (Codex, 2026-11-17).
    """
    shutil.rmtree(folder, ignore_errors=True)
    reason = last_error(tool_output)
    canonical = parse_link(link)
    return {
        "status": status or status_of(reason),
        "reason": reason,
        "platform": canonical.get("platform"),
        "link": canonical.get("link", link),
        "id": canonical.get("id"),
        "work": None,
    }


def status_of(reason: str) -> str:
    if matches(reason, LOGIN_ONLY):
        return "login_only"
    if matches(reason, NEEDS_LOGIN):
        return "needs_login"
    if matches(reason, UNAVAILABLE):
        return "unavailable"
    return "error"


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
    scan = run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(media), "-an",
         "-vf", f"scale=160:-2,select='gt(scene,{SCENE_THRESHOLD})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", scan.stderr)]


def duration_of(media: Path) -> float:
    probe = run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(media)],
        capture_output=True, text=True, check=True,
    )
    return float(probe.stdout.strip() or 0)


def tiny(image: Path) -> bytes:
    """A 16x16 RGB thumbnail, for spotting near-duplicate frames."""
    done: subprocess.CompletedProcess[bytes] = run(
        ["ffmpeg", "-v", "error", "-i", str(image), "-vf", "scale=16:16", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    )
    return done.stdout


def difference(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / max(len(a), 1)


def save_jpeg(source: Path, out: Path, box: int, quality: int = 3, at: float | None = None) -> None:
    """One frame of source (at a time in seconds, for video) as a JPEG that fits a box x box square."""
    seek = ["-ss", f"{at:.3f}"] if at is not None else []
    fit = (f"scale='min({box},iw)':'min({box},ih)'"
           ":force_original_aspect_ratio=decrease:force_divisible_by=2")
    run_ffmpeg(*seek, "-i", str(source), "-frames:v", "1", "-vf", fit, "-q:v", str(quality), str(out))


def run_ffmpeg(*args: str) -> None:
    run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, check=True)


def has_audio(media: Path) -> bool:
    probe = run(
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
    run(command, capture_output=True, text=True, check=True)
    result = json.loads((out_dir / f"{media.stem}.json").read_text(encoding="utf-8"))
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


# A toast from Windows PowerShell 5.1, which loads the WinRT types (PowerShell 7 does not). The
# text arrives in environment variables and goes in as XML text nodes, so PowerShell never parses
# it. A toast needs a registered app id; this one is Windows PowerShell's own.
WINDOWS_TOAST = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$texts = $xml.GetElementsByTagName('text')
$texts.Item(0).AppendChild($xml.CreateTextNode($env:GK_NOTIFY_TITLE)) > $null
$texts.Item(1).AppendChild($xml.CreateTextNode($env:GK_NOTIFY_MESSAGE)) > $null
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
"""
# macOS: the text is the script's arguments, never part of the script.
MAC_NOTIFICATION = ("on run argv", "display notification (item 2 of argv) with title (item 1 of argv)", "end run")
# In a sandbox, Codex's included, osascript cannot load `display notification`, so the script above
# fails to compile: "syntax error: Expected end of line but found identifier. (-2741)" (2026-11-17).
MAC_SANDBOXED = "(-2741)"
MAC_SANDBOXED_REASON = ("osascript could not read its notification command (-2741), as happens when it runs in a "
                        "sandbox such as Codex's: run post.py notify outside the sandbox")


def notify(title: str, message: str) -> dict[str, Any]:
    """Show a notification on this computer, for a Ping when the agent has no push tool.

    The text reaches the system as arguments or environment variables, never inside a script
    or a shell command, so nothing in it is expanded. A zero exit means the system took the
    notification, not that the user saw it: macOS may have notifications off for the app that
    shows it (Script Editor, for osascript).
    """
    env = None
    if system() == "Darwin":
        command = ["osascript", *(part for line in MAC_NOTIFICATION for part in ("-e", line)), title, message]
    elif system() == "Windows":
        command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_TOAST]
        env = {**os.environ, "GK_NOTIFY_TITLE": title, "GK_NOTIFY_MESSAGE": message}
    else:  # Linux and the other systems with a freedesktop notification server
        command = ["notify-send", "--app-name=Graveyard Killer", "--", title, message]
    program = shutil.which(command[0])
    if program is None:
        hint = " (on Debian or Ubuntu: sudo apt install libnotify-bin)" if command[0] == "notify-send" else ""
        return {"notified": False, "reason": f"{command[0]} is not on this computer{hint}"}
    try:
        result = run([program, *command[1:]], capture_output=True, text=True, timeout=NOTIFY_TIME_LIMIT, env=env)
    except (OSError, ToolTimedOut) as failed:
        return {"notified": False, "reason": str(failed)}
    if result.returncode != 0:
        lines = (result.stderr or "").strip().splitlines()
        if command[0] == "osascript" and lines and MAC_SANDBOXED in lines[-1]:
            return {"notified": False, "reason": MAC_SANDBOXED_REASON}
        return {"notified": False, "reason": lines[-1] if lines else f"{command[0]} exited with {result.returncode}"}
    return {"notified": True}


def pause(login: bool = False) -> dict[str, float]:
    """Wait a random PAUSE, or LOGIN_PAUSE before a login read. A shell sleep with $RANDOM, or
    python3 -c, needs approval where only the skill's own scripts may run. GK_PAUSE_SCALE shortens
    the wait (for the tests)."""
    seconds = random.uniform(*(LOGIN_PAUSE if login else PAUSE))
    time.sleep(seconds * float(os.environ.get("GK_PAUSE_SCALE", "1")))
    return {"paused": round(seconds, 1)}


def upload(image: Path, upload_url: str, headers: list[str], field: str = "file") -> dict[str, Any]:
    """Send one image that read made to an upload URL from the Notion connector's file upload:
    one multipart POST, with the headers the connector gave.

    It sends only to Notion, and only an image inside a work folder that read made, so that
    no text in a post can make it send another file, or send one somewhere else.
    """
    parts = urlsplit(upload_url)
    if parts.scheme != "https" or parts.hostname != NOTION_UPLOAD_HOST:
        return {"error": f"not a Notion upload URL: {upload_url}"}
    image = image.resolve()
    made_by_read = any((folder / MARKER).is_file() for folder in image.parents)
    content_type = UPLOAD_TYPES.get(image.suffix.lower())
    if not (image.is_file() and made_by_read and content_type):
        return {"error": f"not an image that read made: {image}"}
    if not re.fullmatch(r"[A-Za-z0-9_-]+", field):
        return {"error": f"not a form field name: {field}"}
    request_headers = {}
    for header in headers:
        name, colon, value = header.partition(":")
        if not colon or not name.strip():
            return {"error": f"not a header: {header}"}
        if name.strip().lower() != "content-type":  # the multipart body sets its own
            request_headers[name.strip()] = value.strip()
    boundary = uuid.uuid4().hex
    body = b"".join([
        f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{image.name}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        image.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    request_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    request = Request(upload_url, data=body, headers=request_headers, method="POST")
    try:
        with urlopen(request, timeout=UPLOAD_TIMEOUT) as response:
            answer = json.loads(response.read() or b"{}")
    except HTTPError as error:
        return {"error": f"HTTP {error.code}: {error.read().decode(errors='replace')[:300]}"}
    except (OSError, ValueError) as error:  # no connection, a time-out, or an answer that is not JSON
        return {"error": str(error)[:300] or type(error).__name__}
    if not isinstance(answer, dict) or answer.get("status") != "uploaded":
        return {"error": f"Notion did not take the upload: {json.dumps(answer)[:300]}"}
    return {"uploaded": answer.get("file_upload_id") or answer.get("id")}


def main() -> None:
    parser = argparse.ArgumentParser(prog="post.py")
    commands = parser.add_subparsers(dest="command", required=True)
    read_parser = commands.add_parser("read")
    read_parser.add_argument("link", nargs="?", help="the Entry's Link; read from stdin when left out")
    read_parser.add_argument("--language", help="the spoken language when known, such as it")
    read_parser.add_argument("--login", metavar="BROWSER",
                             help="read an Instagram post with this browser's login, such as firefox or "
                                  "'chrome:Profile 1'")
    commands.add_parser("check")
    pause_parser = commands.add_parser("pause")
    pause_parser.add_argument("--login", action="store_true", help="the longer pause before a login read")
    notify_parser = commands.add_parser("notify", help="a title on the first line of stdin, the message on the next")
    # As arguments too: Codex lets a script out of its sandbox only when the command has no heredoc.
    notify_parser.add_argument("text", nargs="*", help="the title, then the message; stdin when left out")
    clean_parser = commands.add_parser("clean")
    clean_parser.add_argument("folder", type=Path)
    upload_parser = commands.add_parser("upload")
    upload_parser.add_argument("image", type=Path, help="an image path from read's output, such as its thumbnail")
    upload_parser.add_argument("upload_url", help="the upload URL the Notion connector gave")
    upload_parser.add_argument("--header", action="append", default=[], help='one of its headers, as "name: value"')
    upload_parser.add_argument("--field", default="file", help="its form field, file unless it says otherwise")
    args = parser.parse_args()
    if args.command == "check":
        print(json.dumps(check()))
    elif args.command == "pause":
        print(json.dumps(pause(args.login)))
    elif args.command == "notify":
        given = args.text or sys.stdin.read().splitlines()
        lines = [line.strip() for line in given if line.strip()]
        if len(lines) < 2:
            print(json.dumps({"notified": False, "reason": "stdin needs a title line and a message line"}))
            sys.exit(2)
        print(json.dumps(notify(lines[0], " ".join(lines[1:]))))
    elif args.command in ("clean", "upload"):
        if args.command == "clean":
            result = clean(args.folder)
        else:
            result = upload(args.image, args.upload_url, args.header, args.field)
        print(json.dumps(result))
        if "error" in result:
            sys.exit(2)
    else:
        link = args.link if args.link is not None else sys.stdin.read().strip()
        print(json.dumps(read(link, args.language, args.login)))


if __name__ == "__main__":
    main()
