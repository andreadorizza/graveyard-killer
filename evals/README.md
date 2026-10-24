# Evals

Evals for the `graveyard-killer` skill, in [skill-creator](https://github.com/anthropics/skills)'s `evals.json` format. They live outside `plugin/`, so they are not installed with the plugin.

## Capture (`capture.json`)

These evals run on the Mac in Claude Code with the Notion connector, against a test Library that exists only for evals. Build the test Library from [the Library contract](../plugin/skills/graveyard-killer/references/library.md).

**Memory.** Every eval except 12 runs with the memory line in place. In Claude Code, memory is a `CLAUDE.md` in the folder the eval runs in:

```
Graveyard Killer Library: <test Library link>
```

Keep this line out of the prompt. The skill reads the first link in the user's message, so a Library link in the prompt would be filed as the post. Run eval 12 in a folder without this file.

**Placeholders.** Before a run, replace these:

| Placeholder | Value |
| --- | --- |
| `{{INSTAGRAM_REEL_URL}}` | A public reel, as `https://www.instagram.com/reel/<code>/` |
| `{{INSTAGRAM_REEL_URL_AS_P}}` | The same reel, as `https://www.instagram.com/p/<code>/` |
| `{{INSTAGRAM_CAROUSEL_URL}}` | A public carousel, as `https://www.instagram.com/p/<code>/` |
| `{{TIKTOK_SHORT_URL}}` | A `vm.tiktok.com` link copied from TikTok's share menu |

**Order.** Empty the test Library's Entries before a run. Evals 6 and 8 test duplicates: run each one right after the eval it repeats (5 and 1), without emptying the Library in between. Every other eval stands alone.

These evals cannot cover what only the phone shows: whether the skill loads in the Claude Android app, whether each app's share menu delivers the link, and whether the phone's web fetch tool accepts the preview URLs. Check those by hand on the Pixel, using the list in the [Capture spec](../.scratch/capture/spec.md#testing-decisions).

## Worker (`worker.json`)

These evals also run in Claude Code on the Mac, with the memory line in place, against the same test Library. Every prompt is "process my inbox". What differs is the Library's state before the run, which each eval's `expected_output` describes as its seed. Seed the Entries by sharing from the phone, or write them into the Entries database by hand, then run the eval.

The Worker downloads and transcribes, so the tools from `post.py check` must be installed first.

**Order:**
- Evals 1 to 3 can share one run: seed all three Entries, run once, then check each eval's expectations.
- Eval 4 needs a processed TikTok Entry, so run it after eval 2.
- Eval 8 (an article) stands alone. Eval 9 checks after any run.

The post script itself is tested in `tests/test_post.py` with fake tools and no network, and in `tests/test_post_live.py` against the real tools (`uv run pytest -m live`).
