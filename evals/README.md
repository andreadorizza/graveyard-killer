# Evals

Evals for the `graveyard-killer` and `graveyard-killer-worker` skills, in [skill-creator](https://github.com/anthropics/skills)'s `evals.json` format. They live outside `plugin/`, so they are not installed with the plugin.

- `capture.json` and `worker.json` run once per Library app, against a test Library in that app.
- `drive.json` holds the evals for a Google Drive Library alone.

## Library apps

Every eval runs against a test Library that exists only for evals, never the user's own. Build one per app with Setup's step 2, as [setup-notion.md](../plugin/skills/graveyard-killer/references/setup-notion.md) and [setup-google-drive.md](../plugin/skills/graveyard-killer/references/setup-google-drive.md) say, in a "Development" page or folder.

**The Library-app placeholder.** `{{LIBRARY_APP}}` in an eval stands for the app of the test Library the run uses: Notion or Google Drive. Grade each eval with that app's file: "long text" is the page body on Notion and the Captures, Transcript and On-screen text columns on Drive, and "removed" is the trash on Notion and a deleted row on Drive.

## Running them

`run_evals.py` runs each eval in a fresh headless `claude -p` session, with the plugin loaded from this repo, in a folder outside the repo whose `CLAUDE.md` holds only the test Library's pointer. It keeps your own `~/.claude/CLAUDE.md`, which may point to your real Library, out of the session, and denies reading anything under `~/.claude`: an agent that finds no pointer searches for one, and on 2026-11-13 eval 12 found the real pointer that way and filed into the real Library. It allows only the connectors of the app under test, and only the skill's own scripts.

```
python3 evals/run_evals.py <notion|google-drive> <capture|worker|drive> <id> [<id> ...]
python3 evals/run_evals.py <notion|google-drive> resume <run> "<reply>"
python3 evals/run_evals.py <notion|google-drive> prompt <run> "<message>"
```

`resume` answers a run in its own session, such as "sì" to a Ping. `prompt` sends any message with the test Library's pointer in place. Each run leaves its stream, its final message and the expectations to grade in `gk-evals/<app>/<run>/` in the system temp folder. Grade by reading the test Library.

It reads `evals/local.json`, which is not committed:

```json
{
  "libraries": {
    "notion": "<the Notion test Library's link>",
    "google-drive": "<the Drive test Library's Sheet link>"
  },
  "placeholders": {
    "{{INSTAGRAM_REEL_URL}}": "https://www.instagram.com/reel/<code>/",
    "{{INSTAGRAM_REEL_URL_AS_P}}": "https://www.instagram.com/p/<code>/",
    "{{INSTAGRAM_CAROUSEL_URL}}": "https://www.instagram.com/p/<code>/",
    "{{TIKTOK_SHORT_URL}}": "<a vm.tiktok.com or vt.tiktok.com link from TikTok's share menu>",
    "{{INSTAGRAM_GATED_URL}}": "https://www.instagram.com/p/<code>/"
  }
}
```

The reel and the carousel are public posts; the reel's two links are the same post. The gated post is one that Instagram shows only to signed-in users, such as a post from an account with an age limit: a logged-out browser shows a notice instead of the post, and `post.py read` gives `login_only`.

About 15 sessions use up Notion's hourly query allowance on plans below Business: run the Notion evals in batches.

## Capture (`capture.json`)

**Memory.** Every eval except 12 runs with the pointer in place. Keep the pointer out of the prompt: the skill reads the first link in the user's message, so a Library link in the prompt would be filed as the post. The runner runs eval 12 with no pointer.

**Order.** Evals 6 and 8 test duplicates: run each one right after the eval it repeats (5 and 1). Every other eval stands alone, so the set can run in one go on an empty Library: check each eval's new Entries only.

These evals cannot cover what only the phone shows: whether the skill loads in the Claude Android app, whether each app's share menu delivers the link, and whether the phone's web fetch tool accepts the preview URLs. Check those by hand on the Pixel, using the list in the [Capture spec](../docs/specs/capture.md#testing-decisions).

## Worker (`worker.json`)

Every prompt is "run the Graveyard Killer worker". What differs is the Library's state before the run, which each eval's `expected_output` describes as its seed. Seed it by sharing from the phone, by a Capture eval, or by writing the Entries into the test Library by hand.

The Worker downloads and transcribes, so the tools from `post.py check` must be installed first.

**Upgrades.** Eval 18 starts from a Library made by an older version: replace the test Library's Settings with [fixtures/settings-0.3.0.md](fixtures/settings-0.3.0.md) (on Drive, write it into the `Settings` tab as library-google-drive.md's Layout says, keeping the Folders section). The fixture is frozen: never update it to the current Settings. A release that adds an upgrade step runs eval 18 ([ADR-0006](../docs/adr/0006-libraries-upgrade-themselves.md)).

**Order:**
- Evals 1 to 3 can share one run, after Capture evals 1, 4 and 5: then check each eval's expectations.
- Eval 4 needs a processed TikTok Entry, so run it after eval 2.
- Eval 8 (an article) stands alone. Eval 9 checks after any run.
- Eval 11 needs a shared save made through the app's share route, of a reel that is not in the Library yet. Eval 12 needs "Ping by" set to `none` and an empty Preferences table in the test Library's Settings.
- Eval 14 runs right after eval 13. Evals 15 and 16 seed a Note with a try count by hand; eval 16 needs no other YouTube Entry waiting.
- Evals 13, 14 and 19 test gated posts. No eval uses a real login: keep the test Library's Instagram login Browser empty, except for eval 19's seed, which is not a browser. Login reads themselves are checked by hand on the maintainer's computer, with each browser that [login.md](../plugin/skills/graveyard-killer/references/login.md#browsers) offers, before each release that changes them.

## Google Drive alone (`drive.json`)

These run only against the Drive test Library. Each `expected_output` gives its seed: write rows with the Sheets connector's `update_spreadsheet` (`appendCells`, text as `stringValue`), and put shared files in "Share here" with the Drive connector.

The post script itself is tested in `tests/test_post.py` with fake tools and no network, and in `tests/test_post_live.py` against the real tools (`uv run pytest -m live`).

On Windows with Smart App Control on, `uv run pytest` cannot start: Smart App Control blocks the unsigned `pytest.exe` in `.venv`. Run `uv run python -m pytest` instead. Smart App Control can also block the fake tools' launchers, and then the tests that use them fail with "Windows Smart App Control blocked".
