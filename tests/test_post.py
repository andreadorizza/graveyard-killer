"""The post script, run the way the agent runs it: a link in, JSON and files out."""

from __future__ import annotations

import platform
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import Run

REEL = "https://www.instagram.com/p/Rk3elTest01/"
REEL_INFO = {
    "extractor_key": "Instagram",
    "id": "Rk3elTest01",
    "webpage_url": "https://www.instagram.com/p/Rk3elTest01/",
    "uploader": "Some Creator | Recipes | Travel | Tips",
    "channel": "some.creator",
    "title": "Video by some.creator",
    "description": "Three ways to cook chickpeas, and why the third one wins",
    "duration": 6,
}


def whisper_calls(run: Run) -> list[list[str]]:
    """Calls to either Whisper build; which one runs depends on the computer."""
    return run.called("mlx_whisper") + run.called("whisper-ctranslate2")


def speech_calls(run: Run) -> list[list[str]]:
    return run.called("parakeet-mlx") + whisper_calls(run)


apple_silicon = pytest.mark.skipif(
    not (platform.system() == "Darwin" and platform.machine() == "arm64"),
    reason="Parakeet runs only on Apple Silicon",
)
elsewhere = pytest.mark.skipif(
    platform.system() == "Darwin" and platform.machine() == "arm64",
    reason="off Apple Silicon, Whisper is the only engine",
)


def reel(media: dict[str, Path], **extra: Any) -> dict[str, Any]:
    return {
        "yt-dlp": [{"json": REEL_INFO, "media": str(media["scenes"]), "thumbnail": str(media["thumb"])}],
        "parakeet-mlx": [{"text": "Three ways to cook chickpeas."}],
        "mlx_whisper": [{"text": "Five things I would still do today.", "language": "en"}],
        "whisper-ctranslate2": [{"text": "Five things I would still do today.", "language": "en"}],
        **extra,
    }


def test_reading_a_reel_gives_its_canonical_link_author_and_caption(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", REEL, scenario=reel(media))

    assert run.exit_code == 0
    assert run.output["status"] == "ok"
    assert run.output["platform"] == "instagram"
    assert run.output["link"] == "https://www.instagram.com/p/Rk3elTest01/"
    assert run.output["id"] == "Rk3elTest01"
    assert run.output["author"] == "some.creator"
    assert run.output["caption"] == REEL_INFO["description"]
    assert run.output["kind"] == "video"
    assert Path(run.output["work"]).is_dir()


@elsewhere
def test_speech_without_captions_is_transcribed_by_whisper(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", REEL, scenario=reel(media))

    assert run.output["transcript"] == "Five things I would still do today."
    assert run.output["transcript_source"] == "whisper"
    assert run.output["transcript_language"] == "en"


@apple_silicon
@pytest.mark.parametrize("hint", [None, "it", "en"])
def test_on_apple_silicon_parakeet_transcribes_its_own_languages(
    post: Callable[..., Run], media: dict[str, Path], hint: str | None
) -> None:
    args = ("read", REEL, "--language", hint) if hint else ("read", REEL)
    run = post(*args, scenario=reel(media))

    assert run.output["transcript"] == "Three ways to cook chickpeas."
    assert run.output["transcript_source"] == "parakeet"
    assert run.output["transcript_language"] == hint
    assert whisper_calls(run) == []


@apple_silicon
def test_on_apple_silicon_whisper_takes_languages_parakeet_lacks(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", REEL, "--language", "ja", scenario=reel(media))

    assert run.output["transcript_source"] == "whisper"
    assert run.called("parakeet-mlx") == []


def test_a_video_without_sound_has_no_transcript_and_skips_whisper(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    scenario = reel(media)
    scenario["yt-dlp"][0]["media"] = str(media["silent"])

    run = post("read", REEL, scenario=scenario)

    assert run.output["transcript"] is None
    assert run.output["transcript_source"] == "none"
    assert speech_calls(run) == []


VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TIKTOK = "https://www.tiktok.com/@someone/video/7400000000000000001"
VIDEO_INFO = {
    "extractor_key": "Youtube",
    "id": "dQw4w9WgXcQ",
    "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "uploader": "Some Channel",
    "channel": "Some Channel",
    "title": "Crispy chickpeas in 20 minutes",
    "description": "Ingredients and steps are below.",
    "duration": 6,
    "language": "en",
}
VTT = """WEBVTT

00:00:00.000 --> 00:00:02.000
Soak the chickpeas overnight

00:00:02.000 --> 00:00:04.000
then roast them <i>for twenty minutes</i>
"""


def youtube(media: dict[str, Path], **info: Any) -> dict[str, Any]:
    return {
        "yt-dlp": [
            {"json": {**VIDEO_INFO, **info}, "media": str(media["scenes"]), "thumbnail": str(media["thumb"])},
            {"subs": VTT},
        ],
        "parakeet-mlx": [{"text": "parakeet text"}],
        "mlx_whisper": [{"text": "whisper text", "language": "en"}],
        "whisper-ctranslate2": [{"text": "whisper text", "language": "en"}],
    }


def test_creator_captions_are_the_transcript_and_whisper_never_runs(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", VIDEO, scenario=youtube(media, subtitles={"en": [{"ext": "vtt"}]}))

    assert run.output["transcript"] == "Soak the chickpeas overnight then roast them for twenty minutes"
    assert run.output["transcript_source"] == "captions"
    assert run.output["transcript_language"] == "en"
    assert speech_calls(run) == []


AUTO_VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000
roast the chickpeas

00:00:01.000 --> 00:00:03.000
roast the chickpeas
until crisp
"""


def test_original_language_automatic_captions_come_before_whisper(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    scenario = youtube(media, automatic_captions={"en-orig": [{"ext": "vtt"}], "it": [{"ext": "vtt"}]})
    scenario["yt-dlp"][1] = {"subs": AUTO_VTT}

    run = post("read", VIDEO, scenario=scenario)

    assert run.output["transcript"] == "roast the chickpeas until crisp"
    assert run.output["transcript_source"] == "auto_captions"
    assert speech_calls(run) == []


ACCENTED_VTT = """WEBVTT
Kind: captions
Language: it

00:00:00.000 --> 00:00:02.000
le novità del campo legale &gt;&gt; [musica]
"""


def test_captions_are_read_as_utf8_and_their_entities_decoded(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    # yt-dlp writes UTF-8 and keeps HTML entities; Windows' default encoding is not UTF-8.
    scenario = youtube(media, subtitles={"en": [{"ext": "vtt"}]})
    scenario["yt-dlp"][1] = {"subs": ACCENTED_VTT}

    run = post("read", VIDEO, scenario=scenario)

    assert run.output["transcript"] == "le novità del campo legale >> [musica]"


def test_a_short_link_resolves_to_the_canonical_post_link(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    info = {
        "extractor_key": "TikTok",
        "id": "7400000000000000001",
        "webpage_url": "https://www.tiktok.com/@another.creator/video/7400000000000000001?_r=1&_t=ZN-9AoWJzi0byQ",
        "uploader": "another.creator",
        "channel": "Another Creator",
        "description": "one pan pasta",
    }
    scenario = reel(media)
    scenario["yt-dlp"] = [{"json": info, "media": str(media["silent"])}]

    run = post("read", "https://vm.tiktok.com/ZMtest001/", scenario=scenario)

    assert run.output["link"] == "https://www.tiktok.com/@another.creator/video/7400000000000000001"
    assert run.output["platform"] == "tiktok"
    assert run.output["author"] == "another.creator"


def width(image: str) -> int:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0", image],
        capture_output=True, text=True, check=True,
    )
    return int(probe.stdout.strip())


def test_keyframes_are_one_per_scene_and_at_most_1024_px_wide(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", REEL, scenario=reel(media))

    frames = run.output["keyframes"]
    assert len(frames) == 3  # the test video has a red, a green and a blue scene
    assert all(Path(f).is_relative_to(run.output["work"]) and Path(f).is_file() for f in frames)
    assert all(width(f) <= 1024 for f in frames)


def test_a_static_clip_keeps_a_single_keyframe(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = reel(media)
    scenario["yt-dlp"][0]["media"] = str(media["silent"])

    run = post("read", REEL, scenario=scenario)

    assert len(run.output["keyframes"]) == 1


FIVE_MIB = 5 * 1024 * 1024


def is_jpeg(image: str) -> bool:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "csv=p=0", image],
        capture_output=True, text=True, check=True,
    )
    return probe.stdout.strip() == "mjpeg"


def test_the_thumbnail_is_a_jpeg_under_5_mib(post: Callable[..., Run], media: dict[str, Path]) -> None:
    assert media["big_thumb"].stat().st_size > FIVE_MIB
    scenario = reel(media)
    scenario["yt-dlp"][0]["thumbnail"] = str(media["big_thumb"])

    run = post("read", REEL, scenario=scenario)

    thumbnail = Path(run.output["thumbnail"])
    assert thumbnail.is_relative_to(run.output["work"])
    assert 0 < thumbnail.stat().st_size < FIVE_MIB
    assert is_jpeg(str(thumbnail))


def test_without_a_thumbnail_the_first_keyframe_stands_in(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    scenario = reel(media)
    del scenario["yt-dlp"][0]["thumbnail"]

    run = post("read", REEL, scenario=scenario)

    assert Path(run.output["thumbnail"]).is_file()
    assert is_jpeg(run.output["thumbnail"])


@pytest.mark.parametrize(
    "error",
    [
        "ERROR: [youtube] aaaaaaaaaaa: Video unavailable",
        "ERROR: [youtube] aaaaaaaaaaa: This video is unavailable",
        "ERROR: [youtube] dQw4w9WgXcQ: Video unavailable. This video has been removed by the uploader",
        "ERROR: [youtube] dQw4w9WgXcQ: Private video. Sign in if you've been granted access to this video",
        "ERROR: [TikTok] 7400000000000000001: Unable to download webpage: HTTP Error 404: Not Found",
    ],
)
def test_a_removed_private_or_missing_post_is_unavailable(post: Callable[..., Run], error: str) -> None:
    run = post("read", VIDEO, scenario={"yt-dlp": [{"exit": 1, "stderr": error}]})

    assert run.output["status"] == "unavailable"
    assert run.output["reason"]
    assert run.output["link"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert Path(run.output["work"]).is_dir()


@pytest.mark.parametrize(
    ("link", "error"),
    [
        (REEL, "ERROR: [Instagram] Rk3elTest01: Requested content is not available, rate-limit reached "
               "or login required. Use --cookies, --cookies-from-browser, --username and --password"),
        (VIDEO, "ERROR: [youtube] dQw4w9WgXcQ: Sign in to confirm you're not a bot."),
        (TIKTOK, "ERROR: [TikTok] 7400000000000000001: TikTok is requiring login for access to this "
                 "content. Use --cookies-from-browser or --cookies for the authentication."),
        (VIDEO, "ERROR: [youtube] dQw4w9WgXcQ: This video is only available for registered users. "
                "Use --cookies-from-browser or --cookies for the authentication."),
    ],
)
def test_a_login_challenge_needs_login_and_is_not_retried(
    post: Callable[..., Run], link: str, error: str
) -> None:
    run = post("read", link, scenario={"yt-dlp": [{"exit": 1, "stderr": error}], "uv": [{}]})

    assert run.output["status"] == "needs_login"
    assert len(run.called("yt-dlp")) == 1
    assert run.called("uv") == []


# yt-dlp 2026.10.21 on an age-limited post, logged out, 2026-11-16. yt-dlp raises it when the
# page holds no media for logged-out visitors (if_not_gated_logged_out is empty).
GATED = ("ERROR: [Instagram] Rk3elTest01: Instagram sent an empty media response. Check if this post is "
         "accessible in your browser without being logged-in. If it is not, then use --cookies-from-browser "
         "or --cookies for the authentication. See  https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-"
         "cookies-to-yt-dlp  for how to manually pass cookies. Otherwise, if the post is accessible in "
         "browser without being logged-in, please report this issue on  https://github.com/yt-dlp/yt-dlp/"
         "issues?q= , filling out the appropriate issue template. Confirm you are on the latest version "
         "using  yt-dlp -U")


def test_a_post_hidden_from_logged_out_visitors_is_login_only(post: Callable[..., Run]) -> None:
    run = post("read", REEL, scenario={"yt-dlp": [{"exit": 1, "stderr": GATED}], "uv": [{}]})

    assert run.output["status"] == "login_only"
    assert "empty media response" in run.output["reason"]
    assert run.output["platform"] == "instagram"
    assert len(run.called("yt-dlp")) == 1
    assert run.called("uv") == []
    assert run.called("gallery-dl") == []


def test_a_link_with_shell_characters_reaches_the_tool_unchanged(post: Callable[..., Run]) -> None:
    # On Windows a .cmd or .bat tool would run through cmd.exe, where & and | start commands.
    link = VIDEO + "&t=1|whoami&echo=%20x"
    run = post("read", link, scenario={"yt-dlp": [{"exit": 1, "stderr": "ERROR: Video unavailable"}]})

    assert run.called("yt-dlp")[0][-1] == link


FORBIDDEN = "ERROR: [youtube] dQw4w9WgXcQ: Unable to download video data: HTTP Error 403: Forbidden"


def test_a_403_updates_yt_dlp_once_and_retries_once(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = youtube(media)
    scenario["yt-dlp"] = [{"exit": 1, "stderr": FORBIDDEN}, *scenario["yt-dlp"]]
    scenario["uv"] = [{}]

    run = post("read", VIDEO, scenario=scenario)

    assert run.output["status"] == "ok"
    assert run.called("uv") == [["tool", "upgrade", "yt-dlp"]]
    assert len(run.called("yt-dlp")) == 2


def test_a_403_that_survives_the_update_is_an_error(post: Callable[..., Run]) -> None:
    scenario = {"yt-dlp": [{"exit": 1, "stderr": FORBIDDEN}], "uv": [{}]}

    run = post("read", VIDEO, scenario=scenario)

    assert run.output["status"] == "error"
    assert "403" in run.output["reason"]
    assert len(run.called("yt-dlp")) == 2


def test_a_tool_that_hangs_is_stopped_with_an_error(post: Callable[..., Run]) -> None:
    # On 2026-11-14 a read sat at 0% CPU for 1 h 46 min and blocked a whole Worker run.
    started = time.monotonic()
    run = post("read", REEL, scenario={"yt-dlp": [{"sleep": 10}]}, env={"GK_TIME_LIMIT": "1"})

    assert time.monotonic() - started < 9
    assert run.output["status"] == "error"
    assert "yt-dlp" in run.output["reason"] and "stopped" in run.output["reason"]
    assert Path(run.output["work"]).is_dir()


CAROUSEL = "https://www.instagram.com/p/DAbc123xyz/?img_index=1"


def slides(media: dict[str, Path]) -> dict[str, Any]:
    return {
        "images": [str(media["slide1"]), str(media["slide2"]), str(media["slide3"])],
        "metadata": {"username": "some.creator", "fullname": "Some Creator",
                     "description": "Three slides on pasta", "post_shortcode": "DAbc123xyz"},
    }


NO_VIDEO = {"exit": 1, "stderr": "ERROR: [Instagram] DAbc123xyz: There is no video in this post"}
CAROUSEL_INFO = {
    "_type": "playlist", "id": "DAbc123xyz", "webpage_url": "https://www.instagram.com/p/DAbc123xyz/",
    "channel": "some.creator", "uploader": "Some Creator | Pasta every day",
    "description": "Three slides on pasta", "entries": [{}, {}, {}],
}


def carousel_images(media: dict[str, Path], **info: Any) -> dict[str, Any]:
    """yt-dlp's answer when asked for a photo post's images, without a login."""
    return {"json": {**CAROUSEL_INFO, **info},
            "images": [str(media["slide1"]), str(media["slide2"]), str(media["slide3"])]}


@pytest.mark.parametrize(
    "first_try",
    [NO_VIDEO, {"json": {"_type": "multi_video", "id": "DAbc123xyz", "entries": [{}]}}],
)
def test_photos_and_carousels_are_read_with_yt_dlp_alone(
    post: Callable[..., Run], media: dict[str, Path], first_try: dict[str, Any]
) -> None:
    # Checked on a real 7-slide carousel, 2026-10-25: caption, account and 720x900 images, no login.
    run = post("read", CAROUSEL, scenario={"yt-dlp": [first_try, carousel_images(media)]})

    assert run.output["status"] == "ok"
    assert run.output["kind"] == "photos"
    assert run.output["link"] == "https://www.instagram.com/p/DAbc123xyz/"
    assert run.output["author"] == "some.creator"
    assert run.output["caption"] == "Three slides on pasta"
    assert run.output["transcript"] is None and run.output["transcript_source"] == "none"
    assert len(run.output["keyframes"]) == 3
    assert all(width(f) <= 1024 for f in run.output["keyframes"])
    assert is_jpeg(run.output["thumbnail"])
    assert run.called("gallery-dl") == []


def test_gallery_dl_reads_the_photos_yt_dlp_cannot(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = {"yt-dlp": [NO_VIDEO, {"json": {"id": "DAbc123xyz"}}], "gallery-dl": [slides(media)]}

    run = post("read", CAROUSEL, scenario=scenario)

    assert run.output["status"] == "ok"
    assert run.output["kind"] == "photos"
    assert run.output["author"] == "some.creator"
    assert len(run.output["keyframes"]) == 3


@pytest.mark.parametrize(
    "gallery_error",
    [
        "[instagram][error] AuthorizationError: Login required",
        # Seen on the second Worker run, 2026-10-25, for a public photo post.
        "[instagram][error] HTTP redirect to login page (https://www.instagram.com/accounts/login/)",
    ],
)
def test_gallery_dl_login_challenge_needs_login(post: Callable[..., Run], gallery_error: str) -> None:
    scenario = {
        "yt-dlp": [NO_VIDEO, {"json": {"id": "DAbc123xyz"}}],
        "gallery-dl": [{"exit": 1, "stderr": gallery_error}],
    }

    run = post("read", CAROUSEL, scenario=scenario)

    assert run.output["status"] == "needs_login"


def test_a_photo_post_hidden_from_logged_out_visitors_is_login_only(post: Callable[..., Run]) -> None:
    # gallery-dl would only meet Instagram's login page, which a challenge also gives.
    scenario = {"yt-dlp": [NO_VIDEO, {"exit": 1, "stderr": GATED}], "gallery-dl": [{}]}

    run = post("read", CAROUSEL, scenario=scenario)

    assert run.output["status"] == "login_only"
    assert run.called("gallery-dl") == []


@pytest.mark.parametrize(
    ("missing", "named"),
    [(("yt-dlp",), "yt-dlp"), (("parakeet-mlx", "mlx_whisper", "whisper-ctranslate2"), "is not installed")],
)
def test_a_missing_tool_is_an_error_that_names_it(
    post: Callable[..., Run], media: dict[str, Path], missing: tuple[str, ...], named: str
) -> None:
    run = post("read", REEL, scenario=reel(media), without=missing)

    assert run.output["status"] == "error"
    assert named in run.output["reason"]


def test_a_tool_that_fails_midway_is_an_error(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = reel(media)
    failing = [{"exit": 1, "stderr": "Error: model load failed"}]
    scenario["parakeet-mlx"] = scenario["mlx_whisper"] = scenario["whisper-ctranslate2"] = failing

    run = post("read", REEL, scenario=scenario)

    assert run.output["status"] == "error"
    assert "model load failed" in run.output["reason"]


def test_check_passes_when_every_tool_is_there(post: Callable[..., Run]) -> None:
    run = post("check")

    assert run.output["ok"] is True
    assert run.output["missing"] == []


def test_check_asks_for_uv_which_installs_the_other_tools(post: Callable[..., Run]) -> None:
    run = post("check", without=("uv",))

    missing = {m["tool"]: m["install"] for m in run.output["missing"]}
    assert "astral.sh/uv" in missing["uv"]


@apple_silicon
def test_check_asks_for_parakeet_on_apple_silicon(post: Callable[..., Run]) -> None:
    run = post("check", without=("parakeet-mlx",))

    missing = {m["tool"]: m["install"] for m in run.output["missing"]}
    assert missing["parakeet"] == "uv tool install parakeet-mlx"


@apple_silicon
def test_check_says_whether_the_speech_model_is_downloaded(post: Callable[..., Run], tmp_path: Path) -> None:
    hf_home = tmp_path / "hf"
    assert post("check", env={"HF_HOME": str(hf_home)}).output["speech_model"] == "not downloaded"

    (hf_home / "hub" / "models--mlx-community--parakeet-tdt-0.6b-v3").mkdir(parents=True)
    assert post("check", env={"HF_HOME": str(hf_home)}).output["speech_model"] == "downloaded"


def test_check_lists_each_missing_tool_with_its_install_command(post: Callable[..., Run]) -> None:
    run = post("check", without=("gallery-dl", "ffmpeg", "mlx_whisper", "whisper-ctranslate2"))

    assert run.output["ok"] is False
    missing = {m["tool"]: m["install"] for m in run.output["missing"]}
    assert missing.keys() == {"gallery-dl", "ffmpeg", "whisper"}
    assert missing["gallery-dl"] == "uv tool install gallery-dl"
    assert "whisper" in missing["whisper"] and missing["whisper"].startswith("uv tool install")
    assert "ffmpeg" in missing["ffmpeg"].lower()  # winget's id is Gyan.FFmpeg


def test_clean_deletes_a_work_folder_that_read_made(post: Callable[..., Run], media: dict[str, Path]) -> None:
    work = post("read", REEL, scenario=reel(media)).output["work"]

    run = post("clean", work)

    assert run.exit_code == 0
    assert run.output == {"cleaned": work}
    assert not Path(work).exists()


def test_clean_refuses_a_folder_that_read_did_not_make(post: Callable[..., Run], tmp_path: Path) -> None:
    precious = tmp_path / "my documents"
    precious.mkdir()
    (precious / "notes.txt").write_text("keep me")

    run = post("clean", str(precious))

    assert run.exit_code != 0
    assert "error" in run.output
    assert (precious / "notes.txt").exists()


def test_a_language_hint_parakeet_lacks_reaches_whisper(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", REEL, "--language", "ja", scenario=reel(media))

    calls = whisper_calls(run)
    assert len(calls) == 1
    argv = calls[0]
    assert argv[argv.index("--language") + 1] == "ja"


def test_the_link_can_arrive_on_stdin(post: Callable[..., Run], media: dict[str, Path]) -> None:
    # The agent passes the Entry's Link through a quoted heredoc, so no shell ever expands it.
    run = post("read", scenario=reel(media), stdin=f"{REEL}\n")

    assert run.output["status"] == "ok"
    assert run.output["link"] == REEL


@pytest.mark.parametrize("not_a_link", ["--exec=touch pwned", "file:///etc/passwd", "-o /tmp/x"])
def test_anything_but_a_web_link_is_refused_before_any_tool_runs(
    post: Callable[..., Run], not_a_link: str
) -> None:
    run = post("read", scenario={"yt-dlp": [{}], "gallery-dl": [{}]}, stdin=not_a_link)

    assert run.output["status"] == "error"
    assert run.calls == []


def test_downloads_are_anonymous_at_most_720p_and_time_out(post: Callable[..., Run], media: dict[str, Path]) -> None:
    # Config files can hold cookies or a login; ignoring them keeps every read anonymous.
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    scenario = {"yt-dlp": [photo_error, {"json": {"id": "Rk3elTest01"}}], "gallery-dl": [slides(media)]}
    run = post("read", REEL, scenario=scenario)

    download, photos = run.called("yt-dlp")
    assert "height<=720" in download[download.index("-f") + 1]
    for yt_dlp in (download, photos):
        assert "--ignore-config" in yt_dlp and "--no-cookies" in yt_dlp
        assert yt_dlp[yt_dlp.index("--socket-timeout") + 1] == "30"  # a stalled connection fails fast
        assert yt_dlp[-2:] == ["--", REEL]
    gallery_dl = run.called("gallery-dl")[0]
    assert "--config-ignore" in gallery_dl
    assert gallery_dl[gallery_dl.index("--http-timeout") + 1] == "30"
    assert gallery_dl[-2:] == ["--", REEL]


@pytest.mark.parametrize("output", ["not json", "{}", '{"requested_downloads": []}'])
def test_unexpected_tool_output_is_an_error_not_a_crash(post: Callable[..., Run], output: str) -> None:
    run = post("read", REEL, scenario={"yt-dlp": [{"json": output}]})

    assert run.output["status"] == "error"
    assert run.output["reason"]


def size(image: str) -> tuple[int, int]:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", image],
        capture_output=True, text=True, check=True,
    )
    w, h = probe.stdout.strip().split(",")
    return int(w), int(h)


def test_tall_slides_fit_in_a_1024_px_square(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", CAROUSEL, scenario={"yt-dlp": [NO_VIDEO, carousel_images(media)]})

    assert all(max(size(f)) <= 1024 for f in run.output["keyframes"])  # the slides are 1080x1350


def test_a_photo_post_behind_a_short_link_gets_its_canonical_link(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    resolved = {"_type": "multi_video", "id": "7400000000000000002", "entries": [{}],
                "webpage_url": "https://www.tiktok.com/@another.creator/photo/7400000000000000002?_r=1"}
    scenario = {"yt-dlp": [{"json": resolved}, carousel_images(media, **resolved)]}

    run = post("read", "https://vm.tiktok.com/ZMphoto01/", scenario=scenario)

    assert run.output["link"] == "https://www.tiktok.com/@another.creator/photo/7400000000000000002"
    assert run.output["kind"] == "photos"


def test_many_scenes_give_at_most_8_distinct_keyframes(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = reel(media)
    scenario["yt-dlp"][0]["media"] = str(media["twelve_scenes"])

    run = post("read", REEL, scenario=scenario)

    frames = run.output["keyframes"]
    assert len(frames) == 8
    assert len({Path(f).read_bytes() for f in frames}) == 8


def test_youtube_gets_a_stable_cover_url(post: Callable[..., Run], media: dict[str, Path]) -> None:
    # Notion's connector takes only an external URL as a cover, and YouTube's image host is stable.
    run = post("read", VIDEO, scenario=youtube(media))

    assert run.output["cover_url"] == "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"


def test_instagram_and_tiktok_get_no_cover_url(post: Callable[..., Run], media: dict[str, Path]) -> None:
    # Their image links are signed and expire within days.
    run = post("read", REEL, scenario=reel(media))

    assert run.output["cover_url"] is None


def test_a_long_transcript_comes_in_blocks_that_fit_notion(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    sentence = "Soak the chickpeas overnight, then roast them until they are crisp. "
    scenario = reel(media)
    scenario["parakeet-mlx"] = scenario["mlx_whisper"] = scenario["whisper-ctranslate2"] = [
        {"text": sentence * 100, "language": "en"}
    ]

    run = post("read", REEL, scenario=scenario)

    blocks = run.output["transcript_blocks"]
    assert len(blocks) > 1
    assert all(0 < len(b) <= 1800 for b in blocks)
    assert all(b.endswith(".") for b in blocks)  # split between sentences
    assert " ".join(blocks) == run.output["transcript"]


def test_a_short_transcript_is_one_block(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", REEL, scenario=reel(media))

    assert run.output["transcript_blocks"] == [run.output["transcript"]]


def test_pause_waits_a_random_6_to_12_seconds(post: Callable[..., Run]) -> None:
    # The Worker's pause between Instagram posts. In the eval runner, which allows only the
    # skill's own scripts, `sleep $((RANDOM % 7 + 6))` and `python3 -c` needed approval (2026-11-16).
    started = time.monotonic()
    run = post("pause", env={"GK_PAUSE_SCALE": "0.01"})

    assert run.exit_code == 0
    assert 6 <= run.output["paused"] <= 12
    assert time.monotonic() - started < 5
    assert run.calls == []


def test_pause_before_a_login_read_waits_a_random_30_to_90_seconds(post: Callable[..., Run]) -> None:
    started = time.monotonic()
    run = post("pause", "--login", env={"GK_PAUSE_SCALE": "0.01"})

    assert run.exit_code == 0
    assert 30 <= run.output["paused"] <= 90
    assert time.monotonic() - started < 5
    assert run.calls == []


# Login reads (#13): a second read of a gated Instagram post with the cookies of a browser on this
# computer. No test reads a real browser's cookies: the fake tools only log what they were given.


def cookies_from_browser(argv: list[str]) -> str:
    return argv[argv.index("--cookies-from-browser") + 1]


def test_a_login_read_gives_both_tools_the_browser_and_never_a_cookie_file(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    scenario = {"yt-dlp": [photo_error, {"json": {"id": "Rk3elTest01"}}], "gallery-dl": [slides(media)]}

    run = post("read", REEL, "--login", "firefox", scenario=scenario)

    assert run.output["status"] == "ok"
    for yt_dlp in run.called("yt-dlp"):
        assert cookies_from_browser(yt_dlp) == "firefox"
        assert "--no-cookies" not in yt_dlp and "--cookies" not in yt_dlp
        assert "--ignore-config" in yt_dlp
        # It loads every cookie of the browser, so it may not follow the post to another site.
        assert yt_dlp[yt_dlp.index("--use-extractors") + 1] == "Instagram"
        assert "--no-warnings" not in yt_dlp  # its cookie warnings tell a browser problem from a gated post
        assert yt_dlp[-2:] == ["--", REEL]
    gallery_dl = run.called("gallery-dl")[0]
    # Only Instagram's cookies, from every Firefox container, as yt-dlp reads them by default.
    assert cookies_from_browser(gallery_dl) == "firefox/.instagram.com::all"
    assert "--cookies" not in gallery_dl
    assert "--config-ignore" in gallery_dl


@pytest.mark.parametrize(
    ("login", "yt_dlp_value", "gallery_dl_value"),
    [
        ("chrome:Profile 1", "chrome:Profile 1", "chrome/.instagram.com:Profile 1"),
        ("firefox:a1b2c3d4.default-release", "firefox:a1b2c3d4.default-release",
         "firefox/.instagram.com:a1b2c3d4.default-release::all"),
        ("Edge", "edge", "edge/.instagram.com"),
    ],
)
def test_a_profile_reaches_both_tools_after_the_domain_for_gallery_dl(
    post: Callable[..., Run], media: dict[str, Path], login: str, yt_dlp_value: str, gallery_dl_value: str
) -> None:
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    scenario = {"yt-dlp": [photo_error, {"json": {"id": "Rk3elTest01"}}], "gallery-dl": [slides(media)]}

    run = post("read", REEL, "--login", login, scenario=scenario)

    assert [cookies_from_browser(c) for c in run.called("yt-dlp")] == [yt_dlp_value, yt_dlp_value]
    assert cookies_from_browser(run.called("gallery-dl")[0]) == gallery_dl_value


def test_a_login_read_of_a_gated_reel_reads_it(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", REEL, "--login", "firefox", scenario=reel(media))

    assert run.output["status"] == "ok"
    assert run.output["author"] == "some.creator"


def test_a_login_read_reads_the_posts_canonical_link(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", "--login", "firefox", scenario=reel(media),
               stdin="https://www.instagram.com/reel/Rk3elTest01/?igsh=abc123")

    assert run.output["status"] == "ok"
    assert run.called("yt-dlp")[0][-2:] == ["--", REEL]


@pytest.mark.parametrize(
    "link",
    [VIDEO, TIKTOK, "https://example.com/article",
     # Instagram links that are not a post's own: a share link and the link shim redirect elsewhere.
     "https://www.instagram.com/share/reel/BAbCdEf123/",
     "https://l.instagram.com/?u=https%3A%2F%2Fexample.com%2F",
     "https://www.instagram.com/some.creator/"],
)
def test_a_login_read_of_anything_but_an_instagram_post_is_refused_before_any_tool_runs(
    post: Callable[..., Run], link: str
) -> None:
    run = post("read", "--login", "firefox", scenario={"yt-dlp": [{}], "gallery-dl": [{}]}, stdin=link)

    assert run.output["status"] == "error"
    assert "Instagram" in run.output["reason"]
    assert run.output["work"] is None
    assert run.calls == []


@pytest.mark.parametrize(
    "browser",
    ["firefox --exec x", "firefox;rm -rf ~", "../x", "firefox:../x", "firefox:..", "firefox:", "",
     "firefox+gnomekeyring", "firefox::Personal", "firefox:Profile\n1", "whale", "chrome:" + "a" * 65,
     "chrome:/Users/me/x"],
)
def test_a_browser_value_that_is_not_a_known_browser_and_plain_profile_is_refused(
    post: Callable[..., Run], browser: str
) -> None:
    run = post("read", REEL, "--login", browser, scenario={"yt-dlp": [{}], "gallery-dl": [{}]})

    assert run.output["status"] == "error"
    assert "--login" in run.output["reason"]
    assert run.calls == []


def test_a_browser_yt_dlp_cannot_read_is_an_error_with_its_reason(post: Callable[..., Run]) -> None:
    error = "ERROR: could not find firefox cookies database in /Users/someone/Library/Application Support/Firefox"
    run = post("read", REEL, "--login", "firefox", scenario={"yt-dlp": [{"exit": 1, "stderr": error}]})

    assert run.output["status"] == "error"
    assert "cookies database" in run.output["reason"]


def test_cookies_gallery_dl_cannot_load_are_an_error_not_a_challenge(post: Callable[..., Run]) -> None:
    # gallery-dl only warns when it cannot load the cookies, then meets the login page logged out.
    stderr = ("[instagram][warning] cookies: Unable to find Firefox cookies database\n"
              "[instagram][error] HTTP redirect to login page (https://www.instagram.com/accounts/login/)")
    scenario = {"yt-dlp": [NO_VIDEO, {"json": {"id": "DAbc123xyz"}}], "gallery-dl": [{"exit": 1, "stderr": stderr}]}

    run = post("read", CAROUSEL, "--login", "firefox", scenario=scenario)

    assert run.output["status"] == "error"
    assert "Unable to find Firefox cookies database" in run.output["reason"]


@pytest.mark.parametrize(
    "error",
    ["ERROR: [Instagram] Rk3elTest01: checkpoint_required",
     "ERROR: [Instagram] Rk3elTest01: Requested content is not available, rate-limit reached or login required."],
)
def test_a_challenge_during_a_login_read_needs_login(post: Callable[..., Run], error: str) -> None:
    run = post("read", REEL, "--login", "firefox", scenario={"yt-dlp": [{"exit": 1, "stderr": error}], "uv": [{}]})

    assert run.output["status"] == "needs_login"
    assert len(run.called("yt-dlp")) == 1


def test_a_post_hidden_even_with_the_login_is_still_login_only(post: Callable[..., Run]) -> None:
    # gallery-dl, asked with the same cookies, finds no media either.
    scenario = {"yt-dlp": [{"exit": 1, "stderr": GATED}], "gallery-dl": [{"images": []}]}
    run = post("read", REEL, "--login", "firefox", scenario=scenario)

    assert run.output["status"] == "login_only"
    assert "empty media response" in run.output["reason"]
    assert len(run.called("gallery-dl")) == 1


def test_a_gated_reel_that_yt_dlp_cannot_read_with_the_login_is_read_by_gallery_dl(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    # A signed-in Chrome session, 2026-11-16: yt-dlp still got an empty media response for an
    # age-limited reel the account sees in the browser, and gallery-dl read it with the same cookies.
    gallery = {"images": [str(media["scenes"])],
               "metadata": {"username": "some.creator", "description": "A reel for adults only"}}
    scenario = {**reel(media), "yt-dlp": [{"exit": 1, "stderr": GATED}], "gallery-dl": [gallery]}

    run = post("read", REEL, "--login", "chrome", scenario=scenario)

    assert run.output["status"] == "ok"
    assert run.output["kind"] == "video"
    assert run.output["link"] == REEL
    assert run.output["author"] == "some.creator"
    assert run.output["caption"] == "A reel for adults only"
    assert run.output["transcript"] == "Three ways to cook chickpeas."
    assert run.output["keyframes"]
    assert Path(run.output["thumbnail"]).exists()
    gallery_dl = run.called("gallery-dl")[0]
    assert cookies_from_browser(gallery_dl) == "chrome/.instagram.com"
    # The merged video file: for a DASH video gallery-dl would call yt-dlp's module, which its install lacks.
    assert "extractor.instagram.videos=merged" in gallery_dl
    assert gallery_dl[-2:] == ["--", REEL]


def test_a_gated_photo_post_that_yt_dlp_cannot_read_with_the_login_is_read_by_gallery_dl(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    scenario = {"yt-dlp": [{"exit": 1, "stderr": GATED}], "gallery-dl": [slides(media)]}

    run = post("read", REEL, "--login", "firefox", scenario=scenario)

    assert run.output["status"] == "ok"
    assert run.output["kind"] == "photos"
    assert run.output["author"] == "some.creator"
    assert len(run.output["keyframes"]) == 3


def test_gallery_dl_finding_nothing_after_its_cookie_warning_is_an_error(post: Callable[..., Run]) -> None:
    warning = "[instagram][warning] cookies: Unable to find Chrome cookies database at '/nowhere'"
    scenario = {"yt-dlp": [{"exit": 1, "stderr": GATED}], "gallery-dl": [{"images": [], "stderr": warning}]}

    run = post("read", REEL, "--login", "chrome", scenario=scenario)

    assert run.output["status"] == "error"
    assert "cookies" in run.output["reason"]


def test_a_login_page_from_gallery_dl_on_a_login_read_needs_login(post: Callable[..., Run]) -> None:
    login_page = {"exit": 1, "stderr": "[instagram][error] HTTP redirect to login page "
                                       "(https://www.instagram.com/accounts/login/)"}
    scenario = {"yt-dlp": [{"exit": 1, "stderr": GATED}], "gallery-dl": [login_page]}

    run = post("read", REEL, "--login", "firefox", scenario=scenario)

    assert run.output["status"] == "needs_login"


def test_a_403_on_a_login_read_is_an_error_and_not_retried(post: Callable[..., Run]) -> None:
    # A retry would use the account a second time, and the 403 may be Instagram refusing it.
    forbidden = "ERROR: [Instagram] Rk3elTest01: Unable to download webpage: HTTP Error 403: Forbidden"
    run = post("read", REEL, "--login", "firefox", scenario={"yt-dlp": [{"exit": 1, "stderr": forbidden}], "uv": [{}]})

    assert run.output["status"] == "error"
    assert len(run.called("yt-dlp")) == 1
    assert run.called("uv") == []


@pytest.mark.parametrize(
    "warning",
    ["WARNING: find-generic-password failed",  # a Keychain prompt denied, on macOS
     "WARNING: cannot decrypt v10 cookies: no key found",
     "WARNING: [Instagram] The provided Instagram account cookies are no longer valid"],
)
def test_a_gated_result_after_a_cookie_warning_is_a_browser_problem(post: Callable[..., Run], warning: str) -> None:
    # yt-dlp goes on logged out when it cannot use the cookies: the post only looks hidden from the login.
    run = post("read", REEL, "--login", "chrome", scenario={"yt-dlp": [{"exit": 1, "stderr": f"{warning}\n{GATED}"}]})

    assert run.output["status"] == "error"
    assert run.output["reason"] == warning


def test_a_logged_out_read_ignores_the_tools_warnings(post: Callable[..., Run]) -> None:
    stderr = f"WARNING: cannot decrypt v10 cookies: no key found\n{GATED}"
    run = post("read", REEL, scenario={"yt-dlp": [{"exit": 1, "stderr": stderr}]})

    assert run.output["status"] == "login_only"
    assert "--no-warnings" in run.called("yt-dlp")[0]


def test_the_cookie_copy_stays_in_the_work_folder_on_a_login_read(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    # The tools delete their copy of the cookie database, but not when post.py stops them at their
    # time limit. In the work folder, clean deletes it then too.
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    scenario = {"yt-dlp": [photo_error, {"json": {"id": "Rk3elTest01"}}], "gallery-dl": [slides(media)]}

    run = post("read", REEL, "--login", "firefox", scenario=scenario)

    work = Path(run.output["work"])
    for call in run.calls:
        assert Path(call["tmpdir"]).parent == work, call


def test_a_logged_out_read_keeps_the_usual_temporary_folder(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", REEL, scenario=reel(media))

    work = Path(run.output["work"])
    assert all(work not in Path(call["tmpdir"]).parents for call in run.calls)
