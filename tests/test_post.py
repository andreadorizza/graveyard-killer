"""The post script, run the way the agent runs it: a link in, JSON and files out."""

from __future__ import annotations

import platform
import subprocess
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


def reel(media: dict[str, Path], **extra: Any) -> dict[str, Any]:
    return {
        "yt-dlp": [{"json": REEL_INFO, "media": str(media["scenes"]), "thumbnail": str(media["thumb"])}],
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


def test_speech_without_captions_is_transcribed_by_whisper(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    run = post("read", REEL, scenario=reel(media))

    assert run.output["transcript"] == "Five things I would still do today."
    assert run.output["transcript_source"] == "whisper"
    assert run.output["transcript_language"] == "en"


def test_a_video_without_sound_has_no_transcript_and_skips_whisper(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    scenario = reel(media)
    scenario["yt-dlp"][0]["media"] = str(media["silent"])

    run = post("read", REEL, scenario=scenario)

    assert run.output["transcript"] is None
    assert run.output["transcript_source"] == "none"
    assert whisper_calls(run) == []


VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
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
    assert whisper_calls(run) == []


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
    assert whisper_calls(run) == []


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
    ],
)
def test_a_login_challenge_needs_login_and_is_not_retried(
    post: Callable[..., Run], link: str, error: str
) -> None:
    run = post("read", link, scenario={"yt-dlp": [{"exit": 1, "stderr": error}], "uv": [{}]})

    assert run.output["status"] == "needs_login"
    assert len(run.called("yt-dlp")) == 1
    assert run.called("uv") == []


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


CAROUSEL = "https://www.instagram.com/p/DAbc123xyz/?img_index=1"


def slides(media: dict[str, Path]) -> dict[str, Any]:
    return {
        "images": [str(media["slide1"]), str(media["slide2"]), str(media["slide3"])],
        "metadata": {"username": "some.creator", "fullname": "Some Creator",
                     "description": "Three slides on pasta", "post_shortcode": "DAbc123xyz"},
    }


@pytest.mark.parametrize(
    "yt_dlp",
    [
        {"exit": 1, "stderr": "ERROR: [Instagram] DAbc123xyz: There is no video in this post"},
        {"json": {"_type": "multi_video", "id": "DAbc123xyz", "entries": [{}]}},
    ],
)
def test_photos_and_carousels_are_read_with_gallery_dl(
    post: Callable[..., Run], media: dict[str, Path], yt_dlp: dict[str, Any]
) -> None:
    run = post("read", CAROUSEL, scenario={"yt-dlp": [yt_dlp], "gallery-dl": [slides(media)]})

    assert run.output["status"] == "ok"
    assert run.output["kind"] == "photos"
    assert run.output["link"] == "https://www.instagram.com/p/DAbc123xyz/"
    assert run.output["author"] == "some.creator"
    assert run.output["caption"] == "Three slides on pasta"
    assert run.output["transcript"] is None and run.output["transcript_source"] == "none"
    assert len(run.output["keyframes"]) == 3
    assert all(width(f) <= 1024 for f in run.output["keyframes"])
    assert is_jpeg(run.output["thumbnail"])


def test_gallery_dl_login_challenge_needs_login(post: Callable[..., Run]) -> None:
    scenario = {
        "yt-dlp": [{"exit": 1, "stderr": "ERROR: [Instagram] DAbc123xyz: There is no video in this post"}],
        "gallery-dl": [{"exit": 1, "stderr": "[instagram][error] AuthorizationError: Login required"}],
    }

    run = post("read", CAROUSEL, scenario=scenario)

    assert run.output["status"] == "needs_login"


@pytest.mark.parametrize(
    ("missing", "named"),
    [(("yt-dlp",), "yt-dlp"), (("mlx_whisper", "whisper-ctranslate2"), "whisper")],
)
def test_a_missing_tool_is_an_error_that_names_it(
    post: Callable[..., Run], media: dict[str, Path], missing: tuple[str, ...], named: str
) -> None:
    run = post("read", REEL, scenario=reel(media), without=missing)

    assert run.output["status"] == "error"
    assert named in run.output["reason"]


def test_a_tool_that_fails_midway_is_an_error(post: Callable[..., Run], media: dict[str, Path]) -> None:
    scenario = reel(media)
    scenario["mlx_whisper"] = scenario["whisper-ctranslate2"] = [{"exit": 1, "stderr": "Error: model load failed"}]

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


apple_silicon = pytest.mark.skipif(
    not (platform.system() == "Darwin" and platform.machine() == "arm64"),
    reason="the MLX Whisper model cache is only checked on Apple Silicon",
)


@apple_silicon
def test_check_says_whether_the_speech_model_is_downloaded(post: Callable[..., Run], tmp_path: Path) -> None:
    hf_home = tmp_path / "hf"
    assert post("check", env={"HF_HOME": str(hf_home)}).output["speech_model"] == "not downloaded"

    (hf_home / "hub" / "models--mlx-community--whisper-large-v3-turbo").mkdir(parents=True)
    assert post("check", env={"HF_HOME": str(hf_home)}).output["speech_model"] == "downloaded"


def test_check_lists_each_missing_tool_with_its_install_command(post: Callable[..., Run]) -> None:
    run = post("check", without=("gallery-dl", "ffmpeg", "mlx_whisper", "whisper-ctranslate2"))

    assert run.output["ok"] is False
    missing = {m["tool"]: m["install"] for m in run.output["missing"]}
    assert missing.keys() == {"gallery-dl", "ffmpeg", "whisper"}
    assert missing["gallery-dl"] == "uv tool install gallery-dl"
    assert "whisper" in missing["whisper"] and missing["whisper"].startswith("uv tool install")
    assert "ffmpeg" in missing["ffmpeg"]


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


def test_a_language_hint_reaches_whisper(post: Callable[..., Run], media: dict[str, Path]) -> None:
    run = post("read", REEL, "--language", "it", scenario=reel(media))

    calls = whisper_calls(run)
    assert len(calls) == 1
    argv = calls[0]
    assert argv[argv.index("--language") + 1] == "it"


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


def test_downloads_are_anonymous_and_at_most_720p(post: Callable[..., Run], media: dict[str, Path]) -> None:
    # Config files can hold cookies or a login; ignoring them keeps every read anonymous.
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    run = post("read", REEL, scenario={"yt-dlp": [photo_error], "gallery-dl": [slides(media)]})

    yt_dlp = run.called("yt-dlp")[0]
    assert "--ignore-config" in yt_dlp and "--no-cookies" in yt_dlp
    assert "height<=720" in yt_dlp[yt_dlp.index("-f") + 1]
    assert yt_dlp[-2:] == ["--", REEL]
    gallery_dl = run.called("gallery-dl")[0]
    assert "--config-ignore" in gallery_dl
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
    photo_error = {"exit": 1, "stderr": "ERROR: [Instagram] Rk3elTest01: There is no video in this post"}
    run = post("read", CAROUSEL, scenario={"yt-dlp": [photo_error], "gallery-dl": [slides(media)]})

    assert all(max(size(f)) <= 1024 for f in run.output["keyframes"])  # the slides are 1080x1350


def test_a_photo_post_behind_a_short_link_gets_its_canonical_link(
    post: Callable[..., Run], media: dict[str, Path]
) -> None:
    resolved = {"_type": "multi_video", "id": "7400000000000000002", "entries": [{}],
                "webpage_url": "https://www.tiktok.com/@another.creator/photo/7400000000000000002?_r=1"}
    scenario = {"yt-dlp": [{"json": resolved}], "gallery-dl": [slides(media)]}

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
