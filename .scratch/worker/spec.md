Status: ready-for-agent

# Spec: The Worker finishes the Inbox, run by hand

## Problem Statement

Capture works from my phone, but most Entries arrive thin. Instagram refuses agent fetches, so an Instagram Entry holds only its link, the fallback Category and a Note. A TikTok shared from Android is a `vm.tiktok.com` short link that Capture cannot resolve, so it is thin too, and two shares of the same TikTok can become two Entries. Even a YouTube Entry holds only a title, not what the video says. Until something reads the actual posts, my Library is a list of links, which is the graveyard again.

The only machine that can read the posts is my own computer. It has a home connection that the platforms do not throttle, and that is where yt-dlp works without a login (ADR 0001).

## Solution

On my Mac, in the Claude Desktop Code tab, I say "process my inbox". The Worker goes through every Entry with Status Inbox, oldest first. For each one, it does the following:

- It reads the post anonymously, with no login and no cookies.
- It resolves short links. If the result is a post that is already in the Library, it merges the two Entries.
- It gets what the post says: the full caption, the speech (from the creator's captions or from Whisper) and the text on screen.
- It finishes the Entry in my language. The Entry gets a real Title, Summary, Next action, Category and Tags, the transcript in its page body, and a thumbnail as its cover.
- It sets the Status to Processed and deletes the downloaded media.

Some posts can't be finished:
- A post that was deleted or made private becomes Unavailable and keeps its preview.
- If Instagram challenges the run, the Worker stops trying Instagram for that run. It leaves those Entries in the Inbox with a Note, and finishes everything else.

At the end it gives me a short report: what it finished, what is Unavailable, and what is still waiting and why.

This slice proves the Worker's hardest parts by hand: downloading, transcription, keyframes, the thumbnail upload and the Notion writes. The weekly schedule comes later, on top of the same steps.

## User Stories

### Starting a run

1. As a Library owner, I want to say "process my inbox" in the Code tab, so that my thin Entries get finished without me opening each post.
2. As a Library owner, I want the Worker to find my Library and read its Settings the same way Capture does, so that it writes the same field names, Status labels and Categories.
3. As a Library owner, I want the Worker to take only Entries with Status Inbox, so that it never touches Entries I have Used or Dismissed.
4. As a Library owner, I want the oldest Entries done first, so that nothing waits forever behind new Captures.
5. As a Library owner, I want a clear message when the Library has no Inbox Entries, so that I know the run did nothing on purpose.
6. As a phone user, I want "process my inbox" sent from the phone answered with "the Worker runs on your computer", so that I know where to ask.

### Tools

7. As a non-technical user, I want the Worker to check its tools before it starts, so that a missing tool does not fail halfway through my Inbox.
8. As a non-technical user, I want to be asked once before anything is installed, with what will be installed and roughly how big it is, so that nothing large lands on my computer by surprise.
9. As a Library owner, I want the first transcription to warn me that the speech model is downloaded once, so that a slow first run does not look broken.
10. As a Library owner, I want Apple Silicon Macs to use the fast Whisper build and other computers the portable one, so that transcription is as quick as my machine allows.

### Reading the post

11. As a Library owner, I want each post read without my login, so that my Instagram account is not put at risk.
12. As a Library owner, I want an Instagram reel's author and full caption read, so that the Entry says what the post says.
13. As a Library owner, I want a TikTok short link resolved to the post's full link, so that the Entry links to the real post.
14. As a Library owner, I want a resolved link that matches an older Entry merged into it, so that one post stays one Entry.
15. As a Library owner, I want the merged-away Entry moved to Notion's trash rather than deleted forever, so that a wrong merge can be undone.
16. As a Library owner, I want the older Entry to note "Captured again on <date>" after a merge, so that I can see that I shared the post twice.
17. As a Library owner, I want photo posts and carousels read too, so that posts with no video are not left behind.
18. As a Library owner, I want a YouTube video's description read, so that links and recipes in it are not lost.

### What the post says

19. As a Library owner, I want the speech in a video transcribed, so that I can search and read what was said.
20. As a Library owner, I want the creator's own YouTube captions used when they exist, so that the run is faster and the text is exact.
21. As a Library owner, I want transcripts kept in their original language, so that nothing is lost in translation.
22. As a Library owner, I want the text shown on screen read from a few keyframes, so that recipes, lists and prompts that are only on screen end up in the Entry.
23. As a Library owner, I want each carousel image read for its text, so that slide-based posts are captured in full.

### Finishing the Entry

24. As a Library owner, I want a Title, Summary and Next action rewritten from the full post in my language, so that the Entry is useful without opening the post.
25. As a Library owner, I want an Entry that sits in the fallback Category moved to the right Category, so that Capture's guess is fixed.
26. As a Library owner, I want a Category I chose myself kept, so that the Worker does not undo my sorting.
27. As a Library owner, I want a Title I wrote myself kept, so that my words stay.
28. As a Library owner, I want Tags added and never removed, so that my own Tags survive.
29. As a Library owner, I want a Category's own fields filled when the post states them, such as Ingredienti for a recipe, so that the Category's fields are useful.
30. As a Library owner, I want Author and Caption filled with the full caption, so that the preview gaps from Capture are closed.
31. As a Library owner, I want the transcript and the on-screen text in the Entry's page body under clear headings, so that the fields stay short and the detail is one click away.
32. As a Library owner, I want a thumbnail as the Entry's cover, so that I can recognise posts at a glance in Notion.
33. As a Library owner, I want the Note cleared once the Entry is finished, so that a Note always means "something needs attention".
34. As a Library owner, I want Status set to Processed only after every write succeeded, so that a half-finished Entry is never marked done.

### When a post can't be finished

35. As a Library owner, I want a deleted or private post marked Unavailable, with a Note that says why, so that I stop waiting for it.
36. As a Library owner, I want an Unavailable Entry to keep the preview it had, so that I still know what it was.
37. As an Instagram user, I want the run to stop trying Instagram at the first challenge, so that my IP is not flagged for "suspected scraping" (ADR 0001).
38. As an Instagram user, I want the Instagram Entries left waiting to carry a Note saying they will be retried, so that I know why they are still thin.
39. As an Instagram user, I want a few seconds of random pause between Instagram posts, so that the run does not look like a burst.
40. As a Library owner, I want any other failure to leave the Entry in the Inbox with a short Note, so that one bad post does not stop the whole run.

### Clean-up and report

41. As a Library owner, I want downloaded media deleted after each Entry, so that my disk does not fill up.
42. As a Library owner, I want the clean-up limited to the Worker's own work folder, so that nothing else on my computer can be deleted by mistake.
43. As a Library owner, I want a short report at the end that gives counts and lists what still waits and why, so that I know the state of my Inbox in one look.
44. As a Library owner, I want the report in my language, so that it reads like the rest of my Library.

### Development

45. As a maintainer, I want everything that touches media in one script with one interface (link in, JSON and files out), so that the agent's job stays reading, writing and judging.
46. As a maintainer, I want that script tested with fake tools on PATH, so that the tests run offline and never call Instagram.
47. As a maintainer, I want one optional live test on a public YouTube video, so that I can check the real tool chain when tools update.
48. As a maintainer, I want Worker evals against the test Library, so that I can change the instructions without a manual run each time.

## Implementation Decisions

### Skill

- **A new job.** SKILL.md gets a second job, **Worker run**, with its own reference file.
  - **Trigger:** the description gains one branch: the user asks to process their Inbox.
  - **Shared steps:** the job reuses "Find the Library" and "Read the Settings" as they are.
  - **Shell check:** the job needs a computer with a shell. On a surface without one, such as the phone app, the agent says that the Worker runs on the computer and stops.
- **Agent and script split the work.** The agent does the Notion reads and writes, the duplicate checks and all the writing and judging (Title, Summary, Next action, Category, Tags, reading keyframes). The post script does everything that touches media. The agent never runs yt-dlp, gallery-dl, ffmpeg or Whisper directly.

### Tools

- **The tools:**
  - yt-dlp and gallery-dl, as uv tools.
  - mlx-whisper on Apple Silicon, or whisper-ctranslate2 (built on faster-whisper) elsewhere, as uv tools.
  - ffmpeg from the system package manager.
- **Checking them:** the post script has a `check` command. It lists what is missing, with the install command for this platform.
- **Asking first:** the agent asks once before installing anything. It names each tool and says the speech model downloads on first use, about 1.6 GB for the turbo model.
- **The speech model** is Whisper turbo (large-v3-turbo) on both builds.

### The post script

- It is one command-line script in the skill, run with uv.
- It calls each tool as an outside program found on PATH, which is the seam the tests use. It imports the link script to make links canonical.
- **Commands:**
  - `check`: reports missing tools as JSON.
  - `read <link> --work <folder>`: reads one post into a fresh work folder and prints one JSON object.
  - `clean <folder>`: deletes a work folder. It refuses any folder that lacks the marker file that `read` creates.
- **`read` output.** All paths point inside the work folder. The JSON object has:
  - `status`: `ok`, `unavailable`, `needs_login` or `error`
  - `reason`: one short sentence when the status is not `ok`
  - `platform`, and `link`, which is canonical: the link script run on the tool's resolved `webpage_url`
  - `id`, `author`, `title`, `caption`
  - `kind`: `video` or `photos`
  - `duration`
  - `transcript`, plus `transcript_source` (`captions`, `whisper` or `none`) and `transcript_language`
  - `keyframes`: image paths
  - `thumbnail`: a JPEG path, kept under 5 MiB for Notion's Free plan
- **Reading a post:**
  - yt-dlp runs first, anonymously, with video at most 720p.
  - If yt-dlp reports a post with no video (an Instagram photo post or carousel, or a TikTok photo post), the script falls back to gallery-dl, also anonymously.
  - The output keeps the yt-dlp metadata and gallery-dl's images.
- **Transcript:**
  - The creator's YouTube captions are used when they exist, in the video's own language.
  - Otherwise Whisper runs on the audio, if there is audio.
  - Photos get no transcript.
- **Keyframes:**
  - For video: the first frame, plus scene-change frames, at most 8 in total, each scaled to at most 1024 px.
  - For photos: each image, at most 10, scaled the same way.
- **Thumbnail:** yt-dlp's thumbnail, or the first image for photos, converted to JPEG under 5 MiB.
- **Status rules,** from the tools' error text:
  - `unavailable`: the post was removed, is private, or does not exist.
  - `needs_login`: Instagram's "rate-limit reached or login required" and similar challenges.
  - `error`: any other failure, including a missing tool (named in the reason).

### Prior art to borrow: claude-video

[claude-video](https://github.com/bradautomates/claude-video) (the `/watch` skill, v0.3.2, MIT) already solves the video half of the post script. The post script borrows these decisions from it, credits the project in a comment where code is adapted, and keeps the MIT notice with any copied code:

- **Caption choice:** at most one track. Prefer creator captions in the video's own language, then the original-language automatic captions. Record where the captions came from.
- **Keyframes:** scene-change frames, with uniform sampling as the fallback on nearly static clips, and a small-thumbnail pass that drops near-duplicate frames before the cap applies.
- **Downloads:** each run gets a fresh work folder. A partial download or a leftover merge file never counts as media.
- **Clean-up:** delete only the work folder that this run created, never its parent.
- **On a 403 or login challenge from yt-dlp:** update yt-dlp once and retry once before reporting the status. Rotating clients or cookies is ruled out.
- **Non-English speech:** pass a spoken-language hint to Whisper when the Settings language or the caption suggests one. Report language detection as unverified otherwise.

### The run (the agent's steps)

1. **Prepare.** Find the Library, read the Settings and run `check`. If tools are missing, ask once to install them, install them, and check again.
2. **List the Inbox.** Query the Entries with the Inbox Status label, oldest Captured first. If there are none, say so and stop.
3. **For each Entry**, run `read` on its Link, then act on the status:
   - `needs_login`: leave the Entry in the Inbox and set the Note to say that Instagram asked for a login and the next run will retry. Skip every remaining Instagram Entry in this run, with the same Note.
   - `unavailable`: set Status Unavailable and set the Note to the reason. Change nothing else.
   - `error`: leave the Entry in the Inbox, set the Note to the reason, and go on.
   - `ok` with a `link` different from the Entry's Link: query for an Entry with the new link.
     - If one exists, add "Captured again on <this Entry's Captured date>" to the older Entry's page body, move this Entry to the trash, clean the work folder, and go on.
     - If none exists, update the Link.
   - `ok`: finish the Entry, as described in [Finishing an Entry](#finishing-an-entry).
4. **Clean up** the work folder with `clean` after each Entry, whatever its result.
5. **Pause** for a random 3 to 8 seconds before each Instagram Entry after the first.
6. **Report** in the Settings language:
   - counts of Processed, Unavailable, merged, and still in the Inbox;
   - each Entry still in the Inbox, with its reason.

### Finishing an Entry

- The agent reads the caption, the transcript and the keyframes. The keyframes are for on-screen text.
- **Kept or replaced:**
  - **Category:** replaced only when the Entry is in the fallback Category.
  - **Title:** replaced only when it is still Capture's no-preview title ("<Platform> post…") or empty.
  - **Summary and Next action:** always rewritten from the full post.
  - **Tags:** added, up to 5 in total, reusing existing Tags. None are removed.
  - **Category fields:** filled only when the post states the value and the field is empty.
  - **Author and Caption:** set from the post. A caption too long for its field overflows into the page body, as in the Library contract.
- **Page body:** the agent adds a Transcript section and an On-screen text section, with headings in the Settings language. It leaves out any section that would be empty.
- **Cover:** the agent uploads the thumbnail through the Notion connector's file upload and sets it as the page cover.
- **Last step:** the agent sets Status Processed and clears the Note. Status Processed is written only after every write above has succeeded.

### Library contract changes

- The Entry page body gains the Transcript and On-screen text sections.
- The contract states:
  - who may change which fields after Capture (the rules in [Finishing an Entry](#finishing-an-entry));
  - that a Note always means "something needs attention" and is cleared when nothing does;
  - that a merged duplicate goes to the trash.

## Testing Decisions

- **A good test checks external behaviour only.**
  - For the post script, that means the JSON and the files that `read` leaves for a given link and given tool behaviour, plus what `check` and `clean` do.
  - For the Worker, it means the Entries in the Library and the report after a run.
- **Seam 1, the Worker run (main seam).**
  - **Manual run:** in a Code tab session, against the test Library. The three Entries already there are an Instagram reel (link-only), a TikTok short link and a YouTube Short (already previewed).
  - **Worker evals,** in skill-creator's format, against the same test Library. The cases:
    - The Instagram reel ends Processed, with the full caption, a transcript, a Category that is not the fallback where one fits, and a cover.
    - The TikTok Entry's Link becomes `/@user/video/<id>`, and it ends Processed.
    - The YouTube Entry keeps its Title and gains the description in Caption and a transcript.
    - A second short link for an already-processed TikTok is merged: the older Entry gains a "Captured again" line, and the newer one is in the trash.
    - A non-existent YouTube video ends Unavailable, with a Note.
    - "Process my inbox" with no Inbox Entries reports that there is nothing to do.
    - An Entry with a Category set by hand keeps it.
    - No work folder is left on disk after the run.
- **Seam 2, the post script.**
  - It is built test first with pytest, and the tests call the script as the agent does.
  - Fake `yt-dlp`, `gallery-dl`, `ffmpeg`, `ffprobe` and Whisper commands are placed first on PATH. They print stored JSON and write small media files. No test needs the network.
  - The cases:
    - a video post with speech gives a Whisper transcript;
    - a YouTube video with creator captions gives `transcript_source: captions`, and Whisper is never called;
    - a short link's resolved `webpage_url` gives a canonical `link`;
    - a carousel falls back to gallery-dl, gives image keyframes and has no transcript;
    - removed or private posts give `unavailable`;
    - Instagram's login challenge gives `needs_login`;
    - a missing tool gives `error`, with the tool's name;
    - `check` lists the missing tools;
    - `clean` deletes a work folder and refuses a folder without the marker;
    - the thumbnail stays under 5 MiB.
  - **The live test** is opt-in, behind a pytest marker. It runs the real tool chain on the public YouTube test video, with no Instagram.
- **Prior art:**
  - The link script's tests already call a script as the agent does, with a subprocess, text in and JSON out.
  - `evals/capture.json` sets the eval format and the test Library practice.
  - claude-video's tests build their media with FFmpeg in the test itself, and they run yt-dlp offline. That is the same approach as the fake tools here.

## Out of Scope

- The weekly scheduled task and its catch-up run. Scheduled tasks are still unverified on the design checklist.
- The Instagram login fallback, browser cookies, and the Windows cookie notes.
- The Graveyard: export import, Buried Entries, Dig up and Amnesty.
- The Digest and Proposals.
- A Setting that keeps downloaded media.
- Google Sheets and markdown Libraries.
- The Setup conversation. The Worker installs only its own tools, after asking.
- Stories and iOS.

## Further Notes

- **Checked 2026-10-24**, with yt-dlp 2026.10.21, metadata only, no cookies, from this Mac:
  - The test Instagram reel gave its author, its full caption and 8 formats.
  - The test TikTok short link resolved to `@chase_ai_/video/7693602525081111821`, with its author and caption.
  - The link script turns that resolved URL into the canonical link.
- **The synced plugin loads in a new Code tab session** (checked 2026-10-24).
- **To verify while building:**
  - The Notion connector uploads a local file and sets it as a page cover.
  - Moving an Entry to the trash works through the connector.
  - gallery-dl reads Instagram carousels and photo posts anonymously. If it needs a login, those posts get `needs_login`.
  - yt-dlp or gallery-dl reads TikTok photo posts.
  - Whisper turbo handles Italian speech well enough for Summaries.
  - A 14-minute video transcribes in reasonable time on Apple Silicon.
- **Why claude-video is not a dependency** (checked 2026-10-24):
  - It is a second plugin for every user to install.
  - Its first-run setup recommends a Gemini API key, which conflicts with ADR 0001.
  - It rejects carousels, which yt-dlp reports as `multi_video`, and it has no photo support.
  - It prints a markdown report for an agent. It has no JSON output, and it does not separate "unavailable" from "needs a login".
- **No cloud Worker:** ADR 0001 rejects running the Worker on a cloud instance by default.
- **Account safety:** Instagram has flagged sessions after a few dozen downloads (ADR 0001). This slice uses no session at all. A challenge still stops Instagram for the run, to protect the IP.
- **Unattended runs:** the Code tab asks for approval of shell and Notion tool calls. This is fine by hand. The scheduled run will need "always allow" (Setup step 6).
- The four new checks above are on design.md's "To verify while building" list.
