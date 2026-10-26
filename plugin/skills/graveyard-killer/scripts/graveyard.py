"""Read the user's Graveyard from the platforms' official exports.

    graveyard.py <export folder or zip> [...]

Prints one JSON object: every saved post found, newest first, as
{platform, link, id, resolved, saved, author, collection}; the collection names;
and warnings about exports it cannot read.

Reads Instagram's saved posts and collections, TikTok's Favorites, and YouTube's
playlists from Google Takeout. Liked TikToks and watch history are not saves.
Standard library only, no network.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from link import parse as parse_link


def read_exports(paths: list[Path]) -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    warnings: list[str] = []
    for name, data in files(paths):
        if Path(name).name.startswith("saved_") and name.endswith(".html"):
            warnings.append(f"{name} is HTML: request the Instagram export again in JSON format")
        elif name.endswith(".json"):
            content = json.loads(data)
            found += instagram_posts(content) + tiktok_favorites(content)
        elif name.endswith(".csv") and "/playlists/" in f"/{name}":
            found += youtube_playlist(Path(name).name, data.decode("utf-8-sig"))
    posts = merge(found)
    collections = sorted({p["collection"] for p in posts if p["collection"]})
    return {"posts": posts, "collections": collections, "warnings": sorted(set(warnings))}


def merge(found: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One post per link, newest first. A post in several lists keeps its collection and earliest date."""
    by_link: dict[str, dict[str, Any]] = {}
    for post in found:
        known = by_link.setdefault(post["link"], post)
        if known is post:
            continue
        known["collection"] = known["collection"] or post["collection"]
        known["author"] = known["author"] or post["author"]
        dates = [d for d in (known["saved"], post["saved"]) if d]
        known["saved"] = min(dates) if dates else None
    return sorted(by_link.values(), key=lambda p: p["saved"] or "", reverse=True)


def files(paths: list[Path]) -> Iterator[tuple[str, bytes]]:
    """Every file in the given folders and zips, as (path inside it, content). Zips stay packed."""
    for path in paths:
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for member in sorted(archive.namelist()):
                    if not member.endswith("/"):
                        yield member, archive.read(member)
        elif path.is_dir():
            for file in sorted(p for p in path.rglob("*") if p.is_file()):
                yield file.relative_to(path).as_posix(), file.read_bytes()


def instagram_posts(data: Any) -> list[dict[str, Any]]:
    """Saved posts in an Instagram export file. Labels follow the account language, so read by structure."""
    posts = []
    for entries in lists_of_entries(data):
        collection = None
        for entry in entries:
            values = [v for v in entry.get("string_map_data", {}).values() if isinstance(v, dict)]
            href = next((v["href"] for v in values if "href" in v), None)
            if not href:
                # A collection's own row: its name, with no link. The posts after it belong to it.
                collection = next((v["value"] for v in values if v.get("value")), collection)
                continue
            timestamp = next((v["timestamp"] for v in values if v.get("timestamp")), None)
            canonical = parse_link(href)
            posts.append({
                "platform": canonical["platform"],
                "link": canonical["link"],
                "id": canonical["id"],
                "resolved": canonical["resolved"],
                "saved": day(timestamp),
                "author": entry.get("title") or None,
                "collection": collection,
            })
    return posts


def tiktok_favorites(data: Any) -> list[dict[str, Any]]:
    """Favorites in TikTok's export: the only list of saved videos. Liked videos are not saves."""
    posts = []
    for item in found_under(data, "FavoriteVideoList"):
        fields = {k.lower(): v for k, v in item.items()}
        if not fields.get("link"):
            continue
        canonical = parse_link(str(fields["link"]))
        posts.append({
            "platform": canonical["platform"],
            "link": canonical["link"],
            "id": canonical["id"],
            "resolved": canonical["resolved"],
            "saved": str(fields.get("date") or "")[:10] or None,
            "author": None,
            "collection": None,
        })
    return posts


def youtube_playlist(filename: str, text: str) -> list[dict[str, Any]]:
    """One playlist from Google Takeout. The playlist's name, from its file, is the collection.

    Two layouts exist: "<name>-videos.csv" with only video rows, and an older
    "<name>.csv" where a block about the playlist comes before the video rows.
    """
    name = filename.removesuffix(".csv").removesuffix("-videos")
    rows = list(csv.reader(io.StringIO(text)))
    header = next((i for i, row in enumerate(rows) if row and row[0].strip().lower() == "video id"), None)
    if header is None:
        return []
    timestamp_column = next(
        (i for i, cell in enumerate(rows[header]) if "time" in cell.lower() or "timestamp" in cell.lower()), None)
    posts = []
    for row in rows[header + 1:]:
        if not row or not row[0].strip():
            continue
        canonical = parse_link(f"https://www.youtube.com/watch?v={row[0].strip()}")
        saved = row[timestamp_column].strip()[:10] if timestamp_column is not None and len(row) > timestamp_column else ""
        posts.append({
            "platform": canonical["platform"],
            "link": canonical["link"],
            "id": canonical["id"],
            "resolved": canonical["resolved"],
            "saved": saved or None,
            "author": None,
            "collection": name,
        })
    return posts


def found_under(data: Any, key: str) -> Iterator[dict[str, Any]]:
    """Every dict in a list stored under `key`, anywhere in the JSON."""
    if isinstance(data, dict):
        for k, value in data.items():
            if k == key and isinstance(value, list):
                yield from (item for item in value if isinstance(item, dict))
            else:
                yield from found_under(value, key)
    elif isinstance(data, list):
        for value in data:
            yield from found_under(value, key)


def lists_of_entries(data: Any) -> Iterator[list[dict[str, Any]]]:
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and all(isinstance(e, dict) for e in value):
                if any("string_map_data" in e for e in value):
                    yield value


def day(timestamp: int | None) -> str | None:
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()


def main() -> None:
    print(json.dumps(read_exports([Path(p) for p in sys.argv[1:]])))


if __name__ == "__main__":
    main()
