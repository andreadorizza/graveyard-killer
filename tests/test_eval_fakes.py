"""The evals' fake posts: post.py reads every recorded post through the stand-ins, and nothing else."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "evals"))
import run_evals  # noqa: E402

SCRIPT = REPO / "plugin/skills/graveyard-killer/scripts/post.py"

pytestmark = pytest.mark.skipif(os.name == "nt", reason="post.py starts only .exe tools on Windows")

Read = Callable[[str], tuple[dict[str, Any], list[dict[str, Any]]]]


@pytest.fixture
def read(tmp_path: Path) -> Read:
    """post.py read with the stand-ins first on PATH, as an eval session runs it."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("post.py needs the real ffmpeg and ffprobe")
    folder = tmp_path / "run"
    bin_dir = run_evals.install_fakes(folder)
    temp = tmp_path / "temp"
    temp.mkdir()
    path = os.pathsep.join([str(bin_dir), str(Path(shutil.which("ffmpeg") or "").parent),
                            str(Path(shutil.which("ffprobe") or "").parent), str(Path(sys.executable).parent)])

    def run(link: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        done = subprocess.run([sys.executable, str(SCRIPT), "read", link], capture_output=True, text=True,
                              env={**os.environ, "PATH": path, "TMPDIR": str(temp)})
        assert done.stdout, done.stderr
        return json.loads(done.stdout), run_evals.fake_calls(folder)

    return run


def recorded(name: str) -> dict[str, Any]:
    post: dict[str, Any] = json.loads((run_evals.FIXTURES / name / "post.json").read_text(encoding="utf-8"))
    return post


@pytest.mark.parametrize("name", ["instagram-DPDm7KmjQMq", "youtube-jNQXAC9IVRw"])
def test_a_video_is_read_from_its_recording(read: Read, name: str) -> None:
    post = recorded(name)
    result, calls = read(post["link"])
    assert result["status"] == "ok" and result["kind"] == "video"
    assert result["author"] == (post["info"]["channel"] if name.startswith("instagram") else post["info"]["uploader"])
    assert result["caption"] == post["info"]["description"]
    assert result["transcript"] == post["speech"]["text"]
    assert result["transcript_source"] in ("parakeet", "whisper")
    assert result["keyframes"] and all(Path(frame).is_file() for frame in result["keyframes"])
    assert Path(result["thumbnail"]).is_file()
    assert {call["post"] for call in calls} == {name}
    shutil.rmtree(result["work"])


def test_captions_come_from_the_recorded_track(read: Read) -> None:
    result, calls = read("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result["status"] == "ok"
    assert result["transcript_source"] == "captions" and result["transcript_language"] == "en"
    assert "upbeat pop song plays" in result["transcript"]
    assert [call["tool"] for call in calls] == ["yt-dlp", "yt-dlp"]  # the video, then its captions
    shutil.rmtree(result["work"])


def test_a_carousel_is_read_from_its_recorded_slides(read: Read) -> None:
    post = recorded("instagram-De3Y-5XmtD6")
    result, _ = read("https://www.instagram.com/p/De3Y-5XmtD6/?img_index=2&igsh=abc")
    assert result["status"] == "ok" and result["kind"] == "photos"
    assert result["author"] == "intelligenza_artificiale_dori"
    assert result["caption"] == post["info"]["description"]
    assert len(result["keyframes"]) == len(post["images"])
    shutil.rmtree(result["work"])


def test_a_reel_link_finds_the_same_post(read: Read) -> None:
    result, calls = read("https://www.instagram.com/reel/DPDm7KmjQMq/?igsh=MWQ1ZGUxMzBkMA==")
    assert result["status"] == "ok" and result["link"] == "https://www.instagram.com/p/DPDm7KmjQMq/"
    assert calls[0]["post"] == "instagram-DPDm7KmjQMq"
    shutil.rmtree(result["work"])


def test_a_recorded_failure_fails_as_it_did(read: Read) -> None:
    result, _ = read("https://www.youtube.com/watch?v=aaaa")
    assert result["status"] == "error"
    assert result["reason"] == recorded("youtube-aaaa")["error"]


def test_any_other_link_fails_without_a_download(read: Read) -> None:
    result, calls = read("https://www.instagram.com/p/NotRecorded1/")
    assert result["status"] == "error"
    assert "no recorded post" in result["reason"] and "--live-posts" in result["reason"]
    assert calls and all(call["post"] is None for call in calls)


def test_every_recorded_post_names_files_that_exist() -> None:
    for path in run_evals.FIXTURES.glob("*/post.json"):
        post = json.loads(path.read_text(encoding="utf-8"))
        for name in [post.get("media"), post.get("thumbnail"), *post.get("images", [])]:
            assert name is None or (path.parent / name).is_file(), f"{path}: {name}"


def test_the_flags_choose_the_posts(tmp_path: Path) -> None:
    opts, flags, rest = run_evals.options(["--live-posts", "notion", "worker", "1"])
    assert flags == {"fake-posts": False, "live-posts": True} and rest == ["notion", "worker", "1"]
    _, none, _ = run_evals.options(["notion", "worker", "1"])
    assert not run_evals.live_posts(none, tmp_path, ("worker", 1))
    assert run_evals.live_posts(none, tmp_path, ("worker", 13))
    assert run_evals.live_posts(none, tmp_path, ("worker", 19))
    assert not run_evals.live_posts({"fake-posts": True, "live-posts": False}, tmp_path, ("worker", 13))
    with pytest.raises(SystemExit):
        run_evals.options(["--fake-posts", "--live-posts", "notion", "worker", "1"])


def test_a_resumed_run_keeps_its_posts(tmp_path: Path) -> None:
    _, none, _ = run_evals.options(["notion", "resume", "worker-13", "sì"])
    with run_evals.posts(tmp_path, live=True):
        pass
    assert run_evals.live_posts(none, tmp_path, None)
    with run_evals.posts(tmp_path, live=False):
        pass
    assert not run_evals.live_posts(none, tmp_path, None)


def test_the_stand_ins_are_first_on_path_only_during_the_run(tmp_path: Path) -> None:
    before = os.environ.get("PATH")
    with run_evals.posts(tmp_path, live=False):
        assert shutil.which("yt-dlp") == str(tmp_path / "fakes" / "bin" / "yt-dlp")
    assert os.environ.get("PATH") == before
    assert (tmp_path / "posts.txt").read_text(encoding="utf-8") == "fake\n"


def test_an_opencode_session_gets_the_stand_ins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_evals, "RUNS", tmp_path / "gk-evals")
    with run_evals.posts(tmp_path / "run", live=False):
        env = run_evals.opencode_env()
    assert env["PATH"].split(os.pathsep)[0] == str(tmp_path / "run" / "fakes" / "bin")
