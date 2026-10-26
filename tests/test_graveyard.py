"""The Graveyard parser, run the way the agent runs it: export folders or zips in, JSON out.

The exports here are small copies built like the real ones. Labels in Instagram's
export follow the account's language, so some tests use Italian labels on purpose.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts/graveyard.py"


def parse(*paths: Path) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)], capture_output=True, text=True, check=True
    )
    result: dict[str, Any] = json.loads(done.stdout)
    return result


def write(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) if not isinstance(data, str) else data)
    return path


def test_instagram_saved_posts_become_posts_with_link_date_and_author(tmp_path: Path) -> None:
    write(tmp_path / "your_instagram_activity/saved/saved_posts.json", {
        "saved_saved_media": [
            {"title": "some.creator",
             "string_map_data": {"Saved on": {"href": "https://www.instagram.com/reel/DAbc123xyz/",
                                              "timestamp": 1717243200}}},
        ]
    })

    result = parse(tmp_path)

    assert result["posts"] == [{
        "platform": "instagram",
        "link": "https://www.instagram.com/p/DAbc123xyz/",
        "id": "DAbc123xyz",
        "resolved": True,
        "saved": "2024-06-01",
        "author": "some.creator",
        "collection": None,
    }]


def instagram_export(root: Path) -> None:
    """Two saved posts; one is also in the collection "Ricette". Labels are Italian."""
    write(root / "your_instagram_activity/saved/saved_posts.json", {
        "saved_saved_media": [
            {"title": "chef.anna",
             "string_map_data": {"Salvato il": {"href": "https://www.instagram.com/p/Pasta00001/",
                                                "timestamp": 1704110400}}},
            {"title": "travel.ben",
             "string_map_data": {"Salvato il": {"href": "https://www.instagram.com/p/Lisbon0001/",
                                                "timestamp": 1717243200}}},
        ]
    })
    write(root / "your_instagram_activity/saved/saved_collections.json", {
        "saved_saved_collections": [
            {"title": "Raccolta",
             "string_map_data": {"Nome": {"value": "Ricette"},
                                 "Ora di creazione": {"timestamp": 1704000000}}},
            {"title": "chef.anna",
             "string_map_data": {"Nome": {"href": "https://www.instagram.com/p/Pasta00001/", "value": "chef.anna"},
                                 "Ora di aggiunta": {"timestamp": 1704110400}}},
        ]
    })


def test_instagram_collections_are_read_by_structure_whatever_the_language(tmp_path: Path) -> None:
    instagram_export(tmp_path)

    result = parse(tmp_path)

    by_link = {p["link"]: p for p in result["posts"]}
    assert len(result["posts"]) == 2
    assert by_link["https://www.instagram.com/p/Pasta00001/"]["collection"] == "Ricette"
    assert by_link["https://www.instagram.com/p/Lisbon0001/"]["collection"] is None
    assert result["collections"] == ["Ricette"]


def test_posts_come_newest_first(tmp_path: Path) -> None:
    instagram_export(tmp_path)

    saved = [p["saved"] for p in parse(tmp_path)["posts"]]

    assert saved == ["2024-06-01", "2024-01-01"]


def test_tiktok_favorites_are_read_and_likes_are_not(tmp_path: Path) -> None:
    write(tmp_path / "TikTok_Data/user_data_tiktok.json", {
        "Likes and Favorites": {
            "Favorite Videos": {"FavoriteVideoList": [
                {"Date": "2024-03-05 18:20:00", "Link": "https://www.tiktokv.com/share/video/7340000000000000001/"},
            ]},
            "Like List": {"ItemFavoriteList": [
                {"date": "2024-03-06 09:00:00", "link": "https://www.tiktokv.com/share/video/7340000000000000002/"},
            ]},
        }
    })

    assert parse(tmp_path)["posts"] == [{
        "platform": "tiktok",
        "link": "https://www.tiktokv.com/share/video/7340000000000000001/",
        "id": "7340000000000000001",
        "resolved": False,
        "saved": "2024-03-05",
        "author": None,
        "collection": None,
    }]


def test_youtube_playlists_from_takeout_are_read_in_both_csv_layouts(tmp_path: Path) -> None:
    playlists = tmp_path / "Takeout/YouTube and YouTube Music/playlists"
    write(playlists / "Ricette veloci-videos.csv",
          "Video ID,Playlist Video Creation Timestamp\n"
          "aaaaaaaaaaa,2024-02-01T10:00:00+00:00\n")
    write(playlists / "Liked videos.csv",  # the older layout: a playlist block, then the videos
          "Playlist Id,Channel Id,Time Created,Time Updated,Title,Description,Visibility\n"
          "LL,UC123,2020-01-01 00:00:00 UTC,2024-01-01 00:00:00 UTC,Liked videos,,Private\n"
          "\n"
          "Video Id,Time Added\n"
          "bbbbbbbbbbb,2023-05-06 07:08:09 UTC\n")
    write(tmp_path / "Takeout/YouTube and YouTube Music/history/watch-history.json",
          [{"titleUrl": "https://www.youtube.com/watch?v=ccccccccccc", "time": "2024-01-01T00:00:00Z"}])

    posts = parse(tmp_path)["posts"]

    assert posts == [
        {"platform": "youtube", "link": "https://www.youtube.com/watch?v=aaaaaaaaaaa", "id": "aaaaaaaaaaa",
         "resolved": True, "saved": "2024-02-01", "author": None, "collection": "Ricette veloci"},
        {"platform": "youtube", "link": "https://www.youtube.com/watch?v=bbbbbbbbbbb", "id": "bbbbbbbbbbb",
         "resolved": True, "saved": "2023-05-06", "author": None, "collection": "Liked videos"},
    ]


def test_zipped_exports_are_read_without_unpacking_and_together(tmp_path: Path) -> None:
    instagram = tmp_path / "instagram"
    instagram_export(instagram)
    archive = tmp_path / "instagram-export.zip"
    with zipfile.ZipFile(archive, "w") as z:
        for file in instagram.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(instagram))
    tiktok = write(tmp_path / "tiktok/user_data_tiktok.json", {"Activity": {"Favorite Videos": {
        "FavoriteVideoList": [{"Date": "2024-07-01 10:00:00",
                               "Link": "https://www.tiktokv.com/share/video/7340000000000000003/"}]}}})

    posts = parse(archive, tiktok.parent)["posts"]

    assert [p["platform"] for p in posts] == ["tiktok", "instagram", "instagram"]


def test_a_collection_post_with_no_save_date_is_kept_and_listed_last(tmp_path: Path) -> None:
    write(tmp_path / "saved_collections.json", {"saved_saved_collections": [
        {"title": "Collection", "string_map_data": {"Name": {"value": "Viaggi"}}},
        {"title": "travel.ben", "string_map_data": {"Name": {"href": "https://www.instagram.com/p/Porto00001/"}}},
    ]})
    instagram_export(tmp_path / "more")

    posts = parse(tmp_path)["posts"]

    assert posts[-1]["link"] == "https://www.instagram.com/p/Porto00001/"
    assert posts[-1]["saved"] is None and posts[-1]["collection"] == "Viaggi"


def test_an_html_export_says_to_request_json_instead(tmp_path: Path) -> None:
    write(tmp_path / "your_instagram_activity/saved/saved_posts.html", "<html>...</html>")

    result = parse(tmp_path)

    assert result["posts"] == []
    assert any("JSON" in w for w in result["warnings"])


def test_a_clean_export_has_no_warnings(tmp_path: Path) -> None:
    instagram_export(tmp_path)

    assert parse(tmp_path)["warnings"] == []
