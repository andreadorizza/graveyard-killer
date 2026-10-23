"""Turn the text of a shared post into its canonical link.

Reads the shared text from its arguments, or from stdin when there are none,
and prints one JSON object.
Standard library only, no network.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

URL = re.compile(r"https?://\S+", re.IGNORECASE)
# Punctuation that ends a sentence, not a URL.
TRAILING = ".,;:!?)]}>\"'»”’…"
# /p/, /reel/, /reels/ and /tv/ all name the same post, with or without a username in front.
# /reels/audio/ is a sound's page, not a post.
INSTAGRAM_POST = re.compile(r"/(?:p|reels?|tv)/(?!audio/)([\w-]+)")
TIKTOK_POST = re.compile(r"/@[\w.-]+/(?:video|photo)/(\d+)")
TIKTOK_SHORT_HOSTS = {"vm.tiktok.com", "vt.tiktok.com"}
YOUTUBE_PATH = re.compile(r"/(?:shorts|live)/([\w-]+)")
# Dropped from every link we do not rebuild, together with every utm_* parameter.
TRACKING = {"fbclid", "gclid", "igsh", "si"}


def parse(text: str) -> dict[str, Any]:
    found = URL.findall(text)
    if not found:
        return {"error": "no link"}
    shared = trim(found[0])
    host = urlsplit(shared).hostname or ""
    if on_site(host, "instagram.com"):
        return instagram(shared)
    if host == "youtu.be" or on_site(host, "youtube.com"):
        return youtube(shared)
    if on_site(host, "tiktok.com"):
        return tiktok(shared)
    return result("other", clean(shared), None, [shared])


def trim(url: str) -> str:
    while url and url[-1] in TRAILING:
        # Keep a ")" that closes a "(" inside the URL, as in Wikipedia links.
        if url[-1] == ")" and url.count("(") >= url.count(")"):
            break
        url = url[:-1]
    return url


def on_site(host: str, site: str) -> bool:
    return host == site or host.endswith("." + site)


def instagram(shared: str) -> dict[str, Any]:
    path = urlsplit(shared).path
    if path.startswith("/stories/"):
        return {"unsupported": "story"}
    if path.startswith("/share/"):
        return result("instagram", clean(shared), None, [shared], resolved=False)
    post = INSTAGRAM_POST.search(path)
    if not post:
        return result("instagram", clean(shared), None, [shared])
    code = post.group(1)
    link = f"https://www.instagram.com/p/{code}/"
    return result("instagram", link, code, [f"{link}embed/captioned/", shared])


def tiktok(shared: str) -> dict[str, Any]:
    parts = urlsplit(shared)
    if parts.hostname in TIKTOK_SHORT_HOSTS or parts.path.startswith("/t/"):
        return result("tiktok", clean(shared), None, [shared], resolved=False)
    post = TIKTOK_POST.match(parts.path)
    if not post:
        return result("tiktok", clean(shared), None, [shared])
    link = f"https://www.tiktok.com{post.group(0)}"
    return result("tiktok", link, post.group(1), [shared])


def youtube(shared: str) -> dict[str, Any]:
    parts = urlsplit(shared)
    in_path = YOUTUBE_PATH.match(parts.path)
    if parts.hostname == "youtu.be":
        video_id = parts.path.strip("/").split("/")[0]
    elif in_path:
        video_id = in_path.group(1)
    else:
        video_id = parse_qs(parts.query).get("v", [""])[0]
    if not video_id:
        return result("youtube", clean(shared), None, [shared])
    link = f"https://www.youtube.com/watch?v={video_id}"
    oembed = "https://www.youtube.com/oembed?" + urlencode({"url": link, "format": "json"})
    return result("youtube", link, video_id, [oembed, shared])


def clean(shared: str) -> str:
    """The shared URL with a lowercase host and no fragment or tracking parameters."""
    parts = urlsplit(shared)
    # Filter the raw query so the parameters we keep stay byte for byte as shared.
    kept = [p for p in parts.query.split("&") if p and not is_tracking(p.split("=", 1)[0])]
    return urlunsplit(parts._replace(netloc=parts.netloc.lower(), query="&".join(kept), fragment=""))


def is_tracking(key: str) -> bool:
    return key.startswith("utm_") or key in TRACKING


def result(
    platform: str,
    link: str,
    post_id: str | None,
    preview_urls: list[str],
    resolved: bool = True,
) -> dict[str, Any]:
    """resolved is False for a short or share link: only a redirect knows its post."""
    return {
        "platform": platform,
        "link": link,
        "id": post_id,
        "resolved": resolved,
        "preview_urls": preview_urls,
    }


def main() -> None:
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(parse(text)))


if __name__ == "__main__":
    main()
