# Evals

Evals for the `graveyard-killer` skill, in [skill-creator](https://github.com/anthropics/skills)'s `evals.json` format. They live outside `plugin/`, so they are not installed with the plugin.

## Capture (`capture.json`)

These evals run on the Mac in Claude Code with the Notion connector, against a test Library that exists only for evals. Build the test Library from [the Library contract](../plugin/skills/graveyard-killer/references/library.md).

**Memory.** Every eval except 12 runs with the memory line in place. In Claude Code, memory is a `CLAUDE.md` in the folder the eval runs in:

```
When I share a social link without text, file it in my graveyard-killer Library at <test Library link>, following the Settings there.
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
