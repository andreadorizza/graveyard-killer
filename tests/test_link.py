"""The link script, called the way the agent calls it: shared text in, JSON out."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts/link.py"


def run_link_script(shared_text: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=shared_text,
        capture_output=True,
        text=True,
        check=True,
    )
    parsed: dict[str, Any] = json.loads(result.stdout)
    return parsed


def test_instagram_reel_becomes_a_canonical_post_link_with_no_preview() -> None:
    # Instagram refuses agent fetches and its embed page no longer carries the
    # caption, so Capture files the link only and the Worker reads the post.
    shared = "https://www.instagram.com/reel/DAbc123xyz/?igsh=MWQ1ZGUxMzBkMA=="

    assert run_link_script(shared) == {
        "platform": "instagram",
        "link": "https://www.instagram.com/p/DAbc123xyz/",
        "id": "DAbc123xyz",
        "resolved": True,
        "preview_urls": [],
    }


@pytest.mark.parametrize(
    "shared",
    [
        "https://www.instagram.com/p/DAbc123xyz/?img_index=3&igsh=abc",
        "https://instagram.com/p/DAbc123xyz",
        "https://www.instagram.com/reels/DAbc123xyz/",
        "https://www.instagram.com/tv/DAbc123xyz/",
        "https://www.instagram.com/some.creator/p/DAbc123xyz/",
        "https://www.instagram.com/some.creator/reel/DAbc123xyz/?igsh=abc",
        "https://m.instagram.com/reel/DAbc123xyz/",
    ],
)
def test_every_instagram_post_form_is_the_same_post(shared: str) -> None:
    result = run_link_script(shared)

    assert result["link"] == "https://www.instagram.com/p/DAbc123xyz/"
    assert result["id"] == "DAbc123xyz"


def test_instagram_share_link_needs_a_redirect() -> None:
    shared = "https://www.instagram.com/share/reel/BAGjK2x1Yz/?igsh=abc"

    assert run_link_script(shared) == {
        "platform": "instagram",
        "link": "https://www.instagram.com/share/reel/BAGjK2x1Yz/",
        "id": None,
        "resolved": False,
        "preview_urls": [],
    }


def test_instagram_story_is_unsupported() -> None:
    shared = "https://www.instagram.com/stories/some.creator/3456789012345678901?igsh=abc"

    assert run_link_script(shared) == {"unsupported": "story"}


def test_tiktok_video_keeps_its_path_without_the_query() -> None:
    shared = "https://www.tiktok.com/@scout2015/video/6718335390845095173?is_from_webapp=1&sender_device=pc"

    assert run_link_script(shared) == {
        "platform": "tiktok",
        "link": "https://www.tiktok.com/@scout2015/video/6718335390845095173",
        "id": "6718335390845095173",
        "resolved": True,
        "preview_urls": [shared],
    }


def test_tiktok_photo_post_is_a_post_too() -> None:
    result = run_link_script("https://www.tiktok.com/@some.creator/photo/7401234567890123456?lang=it")

    assert result["link"] == "https://www.tiktok.com/@some.creator/photo/7401234567890123456"
    assert result["id"] == "7401234567890123456"


@pytest.mark.parametrize(
    "shared",
    [
        "https://vm.tiktok.com/ZMabcDEF1/",
        "https://vt.tiktok.com/ZSabcDEF2/",
        "https://www.tiktok.com/t/ZTabcDEF3/",
    ],
)
def test_tiktok_short_link_needs_a_redirect(shared: str) -> None:
    assert run_link_script(shared) == {
        "platform": "tiktok",
        "link": shared,
        "id": None,
        "resolved": False,
        "preview_urls": [shared],
    }


def test_short_link_is_cleaned_like_any_other_link() -> None:
    result = run_link_script("https://VM.TikTok.com/ZMabcDEF1/?k=1&utm_source=x#top")

    assert result["link"] == "https://vm.tiktok.com/ZMabcDEF1/?k=1"
    assert result["resolved"] is False


def test_youtube_watch_link_drops_the_timestamp() -> None:
    shared = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"

    assert run_link_script(shared) == {
        "platform": "youtube",
        "link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "id": "dQw4w9WgXcQ",
        "resolved": True,
        "preview_urls": [
            "https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ&format=json",
            shared,
        ],
    }


@pytest.mark.parametrize(
    "shared",
    [
        "https://youtu.be/dQw4w9WgXcQ?si=AbCdEfGh123",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ?si=AbCdEfGh123",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ?feature=share",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ&si=AbCdEfGh123",
        "https://www.youtube.com/watch?feature=shared&v=dQw4w9WgXcQ",
    ],
)
def test_every_youtube_form_is_the_same_video(shared: str) -> None:
    result = run_link_script(shared)

    assert result["link"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result["id"] == "dQw4w9WgXcQ"


def test_other_link_loses_only_tracking_parameters_and_fragment() -> None:
    shared = "https://Example.COM/Recipes/Carbonara?id=7&utm_source=ig&utm_medium=social&fbclid=xyz&gclid=abc&si=q&igsh=r#comments"

    assert run_link_script(shared) == {
        "platform": "other",
        "link": "https://example.com/Recipes/Carbonara?id=7",
        "id": None,
        "resolved": True,
        "preview_urls": [shared],
    }


@pytest.mark.parametrize(
    ("shared", "platform", "canonical"),
    [
        (
            "https://www.youtube.com/@SomeChannel?si=abc",
            "youtube",
            "https://www.youtube.com/@SomeChannel",
        ),
        (
            "https://www.youtube.com/playlist?list=PL123&si=abc",
            "youtube",
            "https://www.youtube.com/playlist?list=PL123",
        ),
        (
            "https://www.tiktok.com/@some.creator?lang=it&_t=abc",
            "tiktok",
            "https://www.tiktok.com/@some.creator?lang=it&_t=abc",
        ),
    ],
)
def test_platform_link_that_is_no_post_is_a_plain_link(
    shared: str, platform: str, canonical: str
) -> None:
    assert run_link_script(shared) == {
        "platform": platform,
        "link": canonical,
        "id": None,
        "resolved": True,
        "preview_urls": [shared],
    }


@pytest.mark.parametrize(
    ("shared", "canonical"),
    [
        ("https://www.instagram.com/some.creator/?igsh=abc", "https://www.instagram.com/some.creator/"),
        (
            "https://www.instagram.com/reels/audio/1234567890/",
            "https://www.instagram.com/reels/audio/1234567890/",
        ),
    ],
)
def test_instagram_link_that_is_no_post_is_a_plain_link_with_no_preview(
    shared: str, canonical: str
) -> None:
    assert run_link_script(shared) == {
        "platform": "instagram",
        "link": canonical,
        "id": None,
        "resolved": True,
        "preview_urls": [],
    }


def test_share_text_and_trailing_punctuation_are_ignored() -> None:
    result = run_link_script("Guarda questo reel (https://www.instagram.com/reel/DAbc123xyz/?igsh=abc).")

    assert result["link"] == "https://www.instagram.com/p/DAbc123xyz/"


def test_preview_uses_the_shared_url_without_trailing_punctuation() -> None:
    result = run_link_script("Leggi qui (https://example.com/ricetta?id=7).")

    assert result["preview_urls"] == ["https://example.com/ricetta?id=7"]


def test_trailing_ellipsis_is_not_part_of_the_link() -> None:
    result = run_link_script("Guarda https://youtu.be/dQw4w9WgXcQ…")

    assert result["id"] == "dQw4w9WgXcQ"


def test_closing_parenthesis_that_belongs_to_the_url_is_kept() -> None:
    result = run_link_script("see (https://en.wikipedia.org/wiki/Carbonara_(dish)).")

    assert result["link"] == "https://en.wikipedia.org/wiki/Carbonara_(dish)"


def test_autocapitalised_link_is_still_a_link() -> None:
    result = run_link_script("Https://WWW.Instagram.com/reel/DAbc123xyz/")

    assert result["link"] == "https://www.instagram.com/p/DAbc123xyz/"


def test_first_of_two_links_wins() -> None:
    result = run_link_script(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ via https://www.instagram.com/p/DAbc123xyz/"
    )

    assert result["platform"] == "youtube"


def test_shared_text_can_come_as_arguments() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "Guarda", "https://youtu.be/dQw4w9WgXcQ"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )

    assert json.loads(result.stdout)["id"] == "dQw4w9WgXcQ"


def test_text_without_a_link_is_not_a_capture() -> None:
    assert run_link_script("what should I cook tonight?") == {"error": "no link"}
