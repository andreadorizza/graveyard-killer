Status: ready-for-agent

# Spec: Capture a post from the phone into a Notion Library

## Problem Statement

I save posts on Instagram, TikTok and YouTube, and I never open them again. The IG Save button and the platforms' own bookmarks put them in a folder that nobody looks at. I want to send a post to my agent from the phone's share menu, in two taps. I also want it to land in my own Library at once, filed in a Category, with a short summary and a Next action. Then it is not lost while I wait for the Worker, which does not exist yet.

I am not technical, and the people I want to give this to are not technical either. We will not manage API keys, tokens, a server or a terminal. Capture must work through the agent app and its connectors only.

## Solution

I share a post from Instagram, TikTok or YouTube (or any other link) to the Claude app on my Pixel. The graveyard-killer skill sees a Capture. It finds my Library from one line in memory and reads the Library's Settings. It then makes the shared link canonical, reads a preview of the post (author and caption or title) from public pages, and creates one Entry with Status Inbox. The Entry has a first Category, a Title, a Summary, a Next action and a few Tags, all in my language. The caption stays in its original language.

If the same post comes in twice, the Library keeps one Entry, notes the second Capture and tells me. If no preview can be read, the Entry is still created with the link, and a note says the Worker will fill it in. The agent replies in one or two short lines, so the phone screen stays clean.

This spec also delivers the parts that every later job depends on: the plugin marketplace with one plugin and one skill, and the Library contract (the Entry fields, the Statuses and the Settings format) that the Worker, the Digest and Setup will reuse.

## User Stories

### Capture on the phone

1. As a phone user, I want to share an Instagram reel from Instagram's share menu to the Claude app, so that it becomes an Entry without me typing anything.
2. As a phone user, I want to share an Instagram photo post or carousel the same way, so that every post type is handled alike.
3. As a phone user, I want to share a TikTok video from TikTok's share menu, so that my TikTok saves land in the same Library.
4. As a phone user, I want to share a TikTok photo post, so that it is not lost because it is not a video.
5. As a phone user, I want to share a YouTube video or Short from the YouTube app, so that my YouTube saves land in the same Library.
6. As a phone user, I want to share any other link, such as an article, so that it is filed with whatever the page shows.
7. As a phone user, I want the share text that apps add around the link (such as "Check out this reel") to be ignored, so that only the post counts.
8. As a phone user, I want tracking parameters such as `igsh`, `si`, `utm_*` and `img_index` removed from the stored link, so that the Library holds a clean link.
9. As a phone user, I want a reply of one or two short lines that names the Category, the Title and the Next action, so that I know the Capture worked without reading a wall of text.
10. As a phone user, I want the reply to link to the new Entry, so that I can open it in Notion with one tap.
11. As a phone user, I want the reply in my own language, so that the tool feels like mine.
12. As a phone user, I want Capture to finish in one turn without questions, so that I can share several posts in a row quickly.

### The Entry

13. As a Library owner, I want each Entry to start with Status Inbox, so that I can see what the Worker has not processed yet.
14. As a Library owner, I want each Entry to store the canonical link, so that I can open the post from the Library and duplicates can be found.
15. As a Library owner, I want each Entry to record its Platform (Instagram, TikTok, YouTube or Other), so that I can filter by source.
16. As a Library owner, I want the author stored, so that I remember who made the post.
17. As a Library owner, I want the caption stored in its original language, so that nothing is lost in translation.
18. As a Library owner, I want a short Title written in my language, so that the Library reads well in a list.
19. As a Library owner, I want a Summary in my language based on the preview, so that I know what the post says before the Worker runs.
20. As a Library owner, I want one Next action, such as "try this recipe" or "book this place", so that every Entry points to something I could do.
21. As a Library owner, I want the agent to pick one Category from the Categories in my Settings, so that the Library stays organised my way.
22. As a Library owner, I want an Entry that fits no Category to go to my fallback Category, so that the agent never invents Categories behind my back.
23. As a Library owner, I want a few Tags on each Entry, reusing Tags already in my Library where they fit, so that Tags do not multiply.
24. As a Library owner, I want the Category's own fields filled in only when the preview states the value, so that the agent does not guess.
25. As a Library owner, I want the date of the Capture stored, so that the Digest can show what is new.

### Duplicates

26. As a phone user, I want sharing the same post twice to keep one Entry, so that the Library has no duplicates.
27. As a phone user, I want the reply to tell me the post is already in my Library, since when, and in which Category, so that I am not confused.
28. As a Library owner, I want a second Capture noted on the Entry with its date, so that I can see that I came back to this post.
29. As a phone user, I want a reel shared as `/reel/` and the same post shared as `/p/` to count as one post, so that the URL form does not create duplicates.
30. As a phone user, I want a YouTube video shared as a Short, as `youtu.be` and as `watch?v=` to count as one video, so that the URL form does not create duplicates.

### When the preview fails

31. As a phone user, I want an Entry created even when no preview can be read, so that the link is never lost.
32. As a Library owner, I want such an Entry to carry a note that says the Worker will fill it in, so that I know why it is thin.
33. As a phone user, I want the reply to say plainly that only the link was saved, so that I am not misled.
34. As a phone user, I want an Instagram Story link refused with a short reason, so that I know Stories are not supported and why.
35. As a phone user, I want a message that holds no link to be treated as a normal chat, so that the skill does not get in my way.
36. As a phone user, I want a link that comes with a real request, such as "summarise this", to be answered as that request and not filed, so that Capture only happens when I mean it.

### Finding the Library

37. As a phone user, I want the agent to find my Library from one line in memory, so that I never paste the link again.
38. As a phone user, I want the agent to ask me for the Library link once when the memory line is missing, so that a fresh surface still works.
39. As a phone user, I want the agent to save the memory line itself where it can, or tell me the exact line to add where it cannot, so that I only answer once.
40. As a phone user, I want the skill to start on its own when I share a link, so that I never type an instruction.
41. As a Library owner, I want the agent to read my Settings before it writes, so that field names, Status names and Categories match my Library exactly.
42. As a Library owner, I want a clear message when the Library or its Settings cannot be read, so that I can fix the connector or the link.

### Library contract (for the jobs that come later)

43. As the Worker (later), I want every Entry in the Inbox to hold a canonical link and a Platform, so that I know what to download.
44. As the Worker (later), I want a note field on the Entry, so that I can tell the user what went wrong, such as "log in to Instagram in Chrome".
45. As Setup (later), I want one written description of the Library's fields, Statuses and Settings format, so that I create Libraries that every job can read.
46. As a Library owner, I want field names and Status names in my language, so that my Notion looks like mine, while the agents still agree on what each one means.
47. As a Library owner, I want to edit my Categories in the Settings page, not in the skill, so that changes reach every agent at once.

### Plugin and install

48. As a Claude user, I want to add the repo as a plugin marketplace from Customize → Plugins → Add marketplace, so that the skill reaches my phone and my Mac.
49. As a non-Claude agent user, I want the skill to be a standard Agent Skill, so that I can install it with `npx skills add` later.
50. As a maintainer, I want SKILL.md to be a short router that sends each job to its own reference file, so that later jobs (Worker, Digest, Setup, Graveyard) slot in without making Capture heavier.
51. As a maintainer, I want the skill written for any agent, naming capabilities ("your web fetch tool", "your Notion connector") and not one vendor's tool names, so that other agents can follow it.
52. As a maintainer, I want the public plugin to hold nothing specific to my own projects, so that it stays generic.

### Development

53. As a maintainer, I want link parsing in one small script with tests, so that the URL edge cases are pinned down and do not drift.
54. As a maintainer, I want the script to need only the Python standard library, so that it runs in the phone app's sandbox with no network and no install.
55. As a maintainer, I want skill evals that run Capture against a test Library on the Mac, so that I can change the skill without a phone in hand.
56. As a maintainer, I want a short manual checklist for the Pixel, so that the things only a real phone can show are checked before release.

## Implementation Decisions

### Plugin layout

- The repo root becomes a Claude plugin marketplace that lists one plugin, `graveyard-killer`. The plugin holds one standard Agent Skill, also named `graveyard-killer`.
- SKILL.md is a short router. Its description must trigger on two things: a message that is only a social link (or a link with share boilerplate), and requests that name Graveyard Killer. Its body tells the agent to find the Library and read the Settings, then go to the reference file for the job. This spec adds two reference files: one for Capture, and one for the Library contract that all jobs share.
- The skill, the docs and the code are in English. The agent talks to the user, and writes Title, Summary, Next action and Tags, in the language set in the Settings.
- The skill names capabilities, not vendor tool names: "your web fetch tool", "your Notion connector", "your code tool".

### The link script

- This is a single command-line script that uses only the Python standard library and runs with plain `python3`. It needs no uv, because uv is for the Worker's dependencies. It does no network calls.
- **Input:** the whole shared text, on stdin or as arguments.
- **Output:** one JSON object with these keys:
  - `platform`: `instagram`, `tiktok`, `youtube` or `other`.
  - `link`: the canonical link.
  - `id`: the post code or video id, or null.
  - `resolved`: false when the link is a short or share link that only a redirect can resolve.
  - `preview_urls`: the URLs to try for a preview, in order.
- **Other results:**
  - `{"error": "no link"}` when the text holds no URL.
  - `{"unsupported": "story"}` for Instagram Stories.
- If the text holds more than one URL, the script uses the first one.
- **Canonical forms:**
  - **Instagram:** `/p/`, `/reel/`, `/reels/` and `/tv/` paths, with or without a username in front, become `https://www.instagram.com/p/<code>/`. The script drops the query string, which removes `igsh` and `img_index`. `/share/` links are cleaned like other links and come back with `resolved: false`. `/reels/audio/` is a sound's page, not a post.
  - **TikTok:** `/@user/video/<id>` and `/@user/photo/<id>` keep their path. The script drops the query string. `vm.tiktok.com`, `vt.tiktok.com` and `/t/` short links are cleaned like other links and come back with `resolved: false`.
  - **YouTube:** `watch?v=`, `youtu.be/`, `/shorts/`, `/live/` and the `m.` and `music.` hosts all become `https://www.youtube.com/watch?v=<id>`. The script drops `si`, `t`, `feature` and every other parameter.
  - **Other:** the script lowercases the host, drops the fragment, and drops `utm_*`, `fbclid`, `gclid`, `igsh` and `si`. It keeps every other parameter.
  - **Platform links that are no post** (a profile, a channel, a playlist): the platform is kept, the link is cleaned like other links, and `id` is null.
- **Preview URLs, in order:**
  - Instagram: none. Capture files the link only, and the Worker reads the post (Pixel run, 2026-10-24: the phone refused every Instagram fetch, and the embed page no longer has the caption in its HTML).
  - TikTok: the shared link. TikTok's oEmbed no longer returns a caption (checked 2026-10-23).
  - YouTube: the oEmbed URL (title and author), then the shared link.
  - Other: the shared link.
- **Dedupe key:** the canonical link is the Entry's Link field and the dedupe key. When `resolved` is false, the agent tries to learn the canonical link from the fetched page. If it finds one, it runs the script again on that link and uses the new result.

### Capture flow (the agent's steps)

1. **Recognise a Capture.** A message is a Capture when it shares a link with no request, or with share boilerplate or a plain "save this". A link that comes with a real request is not a Capture. A message with no link is not a Capture.
2. **Find the Library.** The agent looks for the memory line. If it is missing, the agent asks for the Library link once. Then it saves the memory line where the surface lets it write memory. Where it cannot, it gives the user the exact line to add.
3. **Read the Settings** through the Notion connector.
4. **Run the link script** on the message text. If the script cannot run, the agent applies the same rules, which the Capture reference file restates in short prose. This is the ADR 0002 fallback.
   - On `no link`, the agent drops Capture and answers normally.
   - On `unsupported: story`, the agent says that Stories are not supported in v1 and files nothing.
5. **Read a preview.** The agent tries each preview URL in order with its web fetch tool and stops at the first one that yields an author and a caption or a title. A fetch error or an empty page moves it on to the next URL.
6. **Check for a duplicate.** The agent queries the Entries for the same Link. If one exists, it adds a dated "captured again" line to the Entry's page body, replies that the post is already in the Library (with its date and Category), and stops. This check comes after the preview, so an unresolved short link can first become canonical.
7. **Write the Entry.** The agent writes Title, Summary, Next action and up to 3 Tags in the Settings language, reusing existing Tags where they fit. It picks the Category from the Settings and uses the fallback Category when none fits. It fills a Category's own fields only when the preview states the value.
   - **With no preview:** the Title is "<Platform> post by <author>", or the link when the author is unknown. Summary and Next action stay empty. The Category is the fallback. The Note says the Worker will fill it in.
8. **Create the Entry** with Status Inbox and today's date as Captured.
9. **Reply** in one or two lines in the user's language, with the Category, the Title, the Next action and a link to the Entry. With no preview, the reply says that only the link was saved.

### Library contract (Notion)

- The Library is one Notion page. It holds the Entries database and a Settings child page. The memory line points to the Library page.
- **Entry fields.** These are canonical names. The Library uses the user's names for them, as mapped in the Settings.
  - Title (title)
  - Link (URL)
  - Platform (select: Instagram, TikTok, YouTube, Other)
  - Author (text)
  - Caption (text)
  - Category (select)
  - Summary (text)
  - Next action (text)
  - Tags (multi-select)
  - Status (select)
  - Captured (date)
  - Note (text)
  - Each Category's own fields
- **Statuses.** All six exist from the start: Inbox, Processed, Used, Dismissed, Unavailable, Buried. Capture only ever writes Inbox.
- **The Settings page** has fixed sections, in this order:
  - **Language:** one language name.
  - **Fields:** a two-column table that maps each canonical field to the Library's name for it.
  - **Statuses:** a two-column table that maps each canonical Status to the Library's label.
  - **Categories:** a table with four columns: name, what goes in it, its own fields, and Fallback, which is marked on exactly one row.
  - **Schedule:** the Worker's weekday. Capture does not read it.
- **The memory line** holds only the Library's location: `Graveyard Killer Library: <link>`. The Capture instructions live only in the skill (ADR 0002).
- Creating the Library is Setup's job and is out of scope here. For this slice, the agent creates one test Library on the Mac by hand from the contract. It is not a skill feature.

## Testing Decisions

- **A good test checks external behaviour only.** For the script, that means the JSON that comes out for a given shared text. For the skill, it means the Entry that appears in the Library and the reply the user sees. Tests never check how the agent got there.
- **Seam 1, the Capture behaviour (main seam).** It has two kinds of test:
  - **Skill evals**, in skill-creator's eval format. They run on the Mac in Claude Code with the Notion connector, against a dedicated test Library that is emptied before each run. The memory line lives in the eval folder's memory, not in the prompt. The two duplicate cases run right after the case they repeat. The cases are:
    - an Instagram reel with Android share boilerplate and `igsh`
    - an Instagram carousel with `img_index`
    - a TikTok full link
    - a TikTok short link
    - a YouTube Short with `si`
    - a YouTube watch link with `t`
    - an article link
    - the same reel shared as `/reel/` and then as `/p/`
    - a link with a real request
    - a message with no link
    - an Instagram Story link
    - a missing memory line

    The assertions are: the Link is canonical; Platform and Status are right; the Category is in the Settings (or is the fallback); the text fields are in the Settings language; there is one Entry per post; the reply is short; nothing is filed when nothing should be.
  - **A manual acceptance run on the Pixel** against the same test Library. It checks what only the phone can show:
    - The skill loads in the Claude Android app.
    - Each app's share menu delivers the link.
    - The phone's web fetch tool reads each preview URL. This covers whether it accepts the URLs the script builds.
    - The Notion connector creates and queries Entries.
    - The reply reads well on the phone screen.
- **Seam 2, the link script.** It is built test first with pytest, run with uv on the Mac. The tests call the script the way the agent does (shared text in, JSON out). They are table-driven with real shared strings for every canonical form above, plus: no URL, two URLs, trailing punctuation, uppercase hosts, and links wrapped in share text.
- **Prior art:** none. The repo has no code yet, so these tests set the pattern for the Worker's scripts (the export parser and Graveyard dedupe).

## Out of Scope

- The Worker: downloads, transcripts, keyframes, thumbnails, Processed and Unavailable, and the weekly task.
- The Digest and Proposals.
- The Setup conversation: creating Libraries, installing tools, scheduling, and writing memory on every surface.
- The Graveyard: export import, Buried Entries, Dig up and Amnesty.
- Google Sheets and markdown Libraries. The contract is written for Notion first.
- iOS share-sheet Capture and Instagram Stories.
- A script that fetches previews itself. The agent's web fetch tool does all fetching in this slice.
- Page covers or thumbnails at Capture. Instagram and TikTok CDN image links expire.
- Testing on agents other than Claude. The skill is written to be portable, but only Claude is tested.
- Directory submission and release notes.

## Further Notes

- **Result of the Pixel run (2026-10-24):** the skill started on its own, the share delivered the link, and a link-only Entry was created with Status Inbox. Every Instagram preview fetch was refused, so Instagram Captures are now link-only. TikTok and YouTube previews are not tested on the phone yet.
- **Biggest risk: building preview URLs.** Claude's web fetch tool documentation says the tool only fetches URLs that already appeared in the conversation: user messages, client-side tool results, and earlier search or fetch results. It does not fetch URLs found only in Claude's own output (checked 2026-10-23, docs.claude.com, web fetch tool, "URL validation"). The Instagram embed URL and the YouTube oEmbed URL are both built from the shared link. So the phone app may refuse them. It is unknown whether the script's output in the sandbox counts as a tool result. The preview order and the link-only Entry keep Capture useful either way. The Pixel run decides which sources work. If none works on the phone, two options exist: script-side fetching where the sandbox has network access, or leaving previews to the Worker.
- **TikTok previews:** the oEmbed endpoint returns only a player iframe, with no title or author (checked 2026-10-23). The caption sits in JSON embedded in the post page. It is unknown whether the web fetch tool's text output keeps it.
- **YouTube previews:** oEmbed returns the title and the author, with no description (checked 2026-10-23). The description sits in JSON embedded in the watch page.
- **Short links:** TikTok short links and Instagram `/share/` links cannot be made canonical without a redirect. If the fetched page does not reveal the canonical link, two Captures of the same post through different short links can create two Entries.
- **Skill triggering:** a bare link with no words may not trigger the skill. Memory holds no Capture rule to fall back on (ADR 0002), so the skill's description must do it alone. If the Pixel run shows weak triggering, sharpen the description.
- **Caption length:** Instagram captions run to 2,200 characters. Check that the Notion connector stores a caption that long in one text field.
- design.md's "To verify while building" list now includes these risks.
