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
python3 evals/run_evals.py [--fake-posts|--live-posts] <notion|google-drive> <capture|worker|drive> <id> [<id> ...]
python3 evals/run_evals.py [--fake-posts|--live-posts] <notion|google-drive> resume <run> "<reply>"
python3 evals/run_evals.py [--fake-posts|--live-posts] <notion|google-drive> prompt <run> "<message>"
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

### Fake posts

Instagram flags an IP that reads the same post again and again: on 2026-11-17 one reel was downloaded about 10 times in a day of eval runs from one Mac. So the runner fakes the posts by default. Before each session it puts stand-ins for `yt-dlp`, `gallery-dl`, `parakeet-mlx`, `mlx_whisper` and `whisper-ctranslate2` first on PATH, in `<run>/fakes/bin`. The skill's `post.py` runs as it always does, with the real `ffmpeg` and `ffprobe`, and the stand-ins answer from the posts recorded in [fixtures/posts](fixtures/posts):

| Recorded post | Used by |
|---|---|
| `instagram-DPDm7KmjQMq`, the reel of `{{INSTAGRAM_REEL_URL}}` and `{{INSTAGRAM_REEL_URL_AS_P}}` | Worker 1, 11 |
| `instagram-De3Y-5XmtD6`, the carousel of `{{INSTAGRAM_CAROUSEL_URL}}` | a Worker run after Capture 2 |
| `youtube-dQw4w9WgXcQ` | Worker 3, 15; Drive 4 |
| `youtube-jNQXAC9IVRw` | Drive 1 |
| `youtube-aaaa`, the truncated link | Worker 15, 16 |

A post matches by platform and id, so `/reel/`, `/p/` and tracking parameters all find it. Any other link fails as a broken download does: `post.py read` gives `error`, and the runner names the link after the run. A `local.json` placeholder that points at another post needs a recording too.

Each recording keeps what a real `post.py read` gave (the kind, the author, the duration, the transcript's source and language), with its own short caption and transcript and small made-up images and video in place of the creator's: the repository is public. A new recording is a folder named `<platform>-<id>` with a `post.json` in the same shape: `info` is what `yt-dlp --dump-single-json` prints, `speech` what the speech engine hears, `subtitles` a caption track's VTT, `images` a carousel's slides, and `error` the last line a failed read printed.

Each run writes `posts.txt` (fake or live) and `fakes/calls.jsonl`, one line per stand-in call with the post it matched. The runner prints a count after each session. A shell that rebuilds PATH can still reach the real tools: Codex runs commands in a login shell, whose profile put Homebrew's `yt-dlp` ahead of the stand-ins on 2026-11-17, so with fake posts the runner starts Codex with `allow_login_shell=false`. When a session's stream shows a post read that no stand-in answered, the runner warns that the real tools ran. A resumed run keeps the posts it started with. `expectations.md` says when posts were fake: grade the caption and the transcript against the recording, not the live post.

**Live posts.** The evals that test the platforms themselves read real posts: Worker 2 and 4 (TikTok's short links), 5 (how YouTube reports a missing video), 13, 14 and 19 (Instagram's posts for signed-in users). They are `LIVE_POSTS` in `run_evals.py`. `--live-posts` makes any run read real posts; `--fake-posts` fakes them in a live eval too. Capture runs no download, so the setting changes nothing there.

**The live stage, once per release.** Fake posts test what the agent does with a read, not the platforms: a change on Instagram, TikTok or YouTube that breaks `yt-dlp` or `gallery-dl`, the real speech engines, and real frames all need real posts. So on the `release-<version>` branch, after the evals pass with fake posts, run this once before the merge to `main`:

1. `uv run pytest -m live`: the real tools read one YouTube video. It never touches Instagram.
2. Seed the reel and the YouTube Entries with Capture evals 1 and 5, in a test Library that holds neither post yet. Then run `python3 evals/run_evals.py --live-posts notion worker 1` and grade Worker evals 1 and 3. That is two real reads, one on Instagram.
3. Run the live evals (Worker 2, 4, 5, 13, 14 and 19) only when the release changes what they test: TikTok links, posts for signed-in users, or how a failed read is reported.

If a live read differs from its recording in kind, author, duration or the transcript's source or language, update the recording's `post.json` to match. That is about three real reads per release, instead of one per eval run.

### On OpenCode's free models

The free route runs the Worker in OpenCode ([ADR-0007](../docs/adr/0007-a-free-worker-in-opencode.md)), so the runner can run any eval there instead of in `claude -p`, against the Notion test Library only:

```
python3 evals/run_evals.py --agent opencode --model opencode/glm-5.3-flash-free notion worker 1 3 12
python3 evals/run_evals.py --agent opencode --model opencode/glm-5.3-flash-free notion resume worker-12 "sì, sempre"
```

- **Before the first run,** sign OpenCode in to Notion once: `opencode mcp auth notion`. The sign-in lives in OpenCode's data folder, which the runner leaves as it is.
- **The model** is `provider/model`. `opencode models opencode` lists the Zen models; the free ones end in `-free`. The free route uses `opencode/glm-5.3-flash-free` and `opencode/deepseek-v4.1-flash-free`, the two that keep no data and train on nothing.
- **Another OpenCode,** such as a 2.x build, goes in `--opencode-bin` or `OPENCODE_BIN`. The runner is tested on OpenCode 1.19.5.

Each eval runs in a fresh `opencode run --auto --format json -m <model>`, in a run folder outside the repo that holds the test pointer in `AGENTS.md` and an `opencode.json`. This branch's skills sit next to the run folder, outside it as a user's installed skills are, registered with `skills.paths` in a folder that is not hidden: OpenCode 1.19's glob finds nothing under `.agents`.

The `opencode.json` is the one `schedule.py` writes for a scheduled run, so the evals test the rules users get. `--auto` approves every permission that is not denied, and a post is untrusted input, so every rule denies first and then allows only what a Worker run needs: reading the run folder, the skills and `post.py`'s work folders, the skill's exact script calls in Bash, web fetch and Notion. No edits, no subagents, no web search, no questions. If an eval fails on one of these rules, fix the rule in `schedule.py`, for users too.

The runner also keeps your own OpenCode setup out of the session:

- `OPENCODE_DISABLE_CLAUDE_CODE=1`: OpenCode does not load `~/.claude/CLAUDE.md`, with your real pointer.
- `OPENCODE_DISABLE_EXTERNAL_SKILLS=1`: it skips `~/.claude/skills` and `~/.agents/skills`, so an installed copy of the skills never mixes with this branch's.
- `XDG_CONFIG_HOME` points at an empty folder in `gk-evals/opencode/config`, so a global `AGENTS.md` pointer, which Setup on the free route writes, never loads. The runner stops if one appears there.
- `OPENCODE_DB` gives the eval sessions their own database. Two OpenCode processes on one database fail with "database is locked", for example an eval and a scheduled Worker run.
- `PWD` is the run folder. OpenCode 1.19 takes its project folder from `PWD`, not from the process's working folder.

Runs land in `gk-evals/opencode/<model>/notion/<run>/`, with a `stats.json` that holds the minutes, the model steps, the tokens and the failed tool calls. A free model is slow, and each step sends the whole conversation again, starting at about 70,000 input tokens for the instructions, the tools and Notion's tool list.

### On Codex

Codex runs the Worker as a scheduled task in the ChatGPT desktop app ([ADR-0008](../docs/adr/0008-a-worker-in-codex.md)). The runner runs any eval in `codex exec` instead, against the Notion test Library only:

```
python3 evals/run_evals.py --agent codex notion worker 1 3 12
python3 evals/run_evals.py --agent codex notion resume worker-12 "sì, sempre"
```

- **Before the first run,** sign Codex in to ChatGPT (the ChatGPT app does it), and to Notion once: `codex mcp add notion --url https://mcp.notion.com/mcp`. Both live in `~/.codex`, which the runner leaves as it is.
- **The model** defaults to the scheduled task's, `gpt-6-luna`; `--model` names another.
- **Codex** is `codex` on PATH, or else the one the ChatGPT app bundles on a Mac. `--codex-bin` or `CODEX_BIN` names another.

Each eval runs in a fresh `codex exec --json`, in a run folder outside the repo written by `schedule.py codex`, as a user's is: `AGENTS.md` with the test pointer and the scripts line, `.codex/config.toml` and `.codex/rules`. This branch's skills go in the folder's own `.agents/skills`. Commands in the run can read only the skills and the folder, with no network, and only the skills' scripts, by full path, run outside the sandbox. If an eval fails on one of these rules, fix it in `schedule.py`, for users too.

The runner also keeps your own setup out of the session:

- A copy of the skills installed in `~/.agents/skills`, which Codex reads in every folder, is switched off for the run (`-c skills.config=[…]`).
- It stops if `~/.codex/AGENTS.md` holds a Graveyard Killer pointer, which Setup on Codex writes there.
- `~/.claude` stays out: Codex does not read `CLAUDE.md`, and the sandbox cannot read `~/.claude`.

`schedule.py codex` marks each run folder as trusted in `~/.codex/config.toml`, one `[projects."…"]` table per eval name, since Codex ignores an untrusted folder's `.codex`. Runs land in `gk-evals/codex/<model>/notion/<run>/`, with a `stats.json` that holds the minutes, the commands and Notion calls with the failed ones, the tokens and the work folders left. `post.py`'s work folders go in the run folder's `work/`, not the system temp folder, so Worker eval 9 checks there (`work_folders_left`).

## Capture (`capture.json`)

**Memory.** Every eval except 12 runs with the pointer in place. Keep the pointer out of the prompt: the skill reads the first link in the user's message, so a Library link in the prompt would be filed as the post. The runner runs eval 12 with no pointer.

**Order.** Evals 6 and 8 test duplicates: run each one right after the eval it repeats (5 and 1). Every other eval stands alone, so the set can run in one go on an empty Library: check each eval's new Entries only.

These evals cannot cover what only the phone shows: whether the skill loads in the Claude Android app, whether each app's share menu delivers the link, and whether the phone's web fetch tool accepts the preview URLs. Check those by hand on the Pixel, using the list in the [Capture spec](../docs/specs/capture.md#testing-decisions).

## Worker (`worker.json`)

Every prompt is "run the Graveyard Killer worker". What differs is the Library's state before the run, which each eval's `expected_output` describes as its seed. Seed it by sharing from the phone, by a Capture eval, or by writing the Entries into the test Library by hand.

The Worker downloads and transcribes. With fake posts it needs only `ffmpeg`; the live evals need every tool from `post.py check`.

**Upgrades.** Eval 18 starts from a Library made by an older version: replace the test Library's Settings with [fixtures/settings-0.3.0.md](fixtures/settings-0.3.0.md) (on Drive, write it into the `Settings` tab as library-google-drive.md's Layout says, keeping the Folders section). The fixture is frozen: never update it to the current Settings. A release that adds an upgrade step runs eval 18 ([ADR-0006](../docs/adr/0006-libraries-upgrade-themselves.md)).

**Order:**
- Evals 1 to 3 can share one run, after Capture evals 1, 4 and 5: then check each eval's expectations.
- Eval 4 needs a processed TikTok Entry, so run it after eval 2.
- Eval 8 (an article) stands alone. Eval 9 checks after any run.
- Eval 11 needs a shared save made through the app's share route, of a reel that is not in the Library yet: with fake posts, the recorded reel. Eval 12 needs "Ping by" set to `none` and an empty Preferences table in the test Library's Settings.
- Eval 14 runs right after eval 13. Evals 15 and 16 seed a Note with a try count by hand; eval 16 needs no other YouTube Entry waiting.
- Evals 13, 14 and 19 test gated posts. No eval uses a real login: keep the test Library's Instagram login Browser empty, except for eval 19's seed, which is not a browser. Login reads themselves are checked by hand on the maintainer's computer, with each browser that [login.md](../plugin/skills/graveyard-killer/references/login.md#browsers) offers, before each release that changes them.

## Google Drive alone (`drive.json`)

These run only against the Drive test Library. Each `expected_output` gives its seed: write rows with the Sheets connector's `update_spreadsheet` (`appendCells`, text as `stringValue`), and put shared files in "Share here" with the Drive connector.

The post script itself is tested in `tests/test_post.py` with fake tools and no network, and in `tests/test_post_live.py` against the real tools (`uv run pytest -m live`).

On Windows with Smart App Control on, `uv run pytest` cannot start: Smart App Control blocks the unsigned `pytest.exe` in `.venv`. Run `uv run python -m pytest` instead. Smart App Control can also block the fake tools' launchers, and then the tests that use them fail with "Windows Smart App Control blocked".
