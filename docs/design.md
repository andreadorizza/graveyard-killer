# Graveyard Killer: v1 design

Saved posts die in a folder nobody opens. Graveyard Killer takes a post you share from your phone, works out what it says, files it in your Library, and brings it back to you in a weekly Digest. It needs no server and no API keys. Terms are defined in [GLOSSARY.md](../GLOSSARY.md); the two load-bearing decisions are in [docs/adr/](adr/).

## Parts

- **Plugin.** A Claude plugin marketplace with one plugin. Inside it is a standard Agent Skill: `SKILL.md` plus Python scripts. The Worker's scripts run with uv. Capture's link script needs only `python3`, so it also runs in a phone app's sandbox. Everything is written in English, and the agent talks in the user's language.
- **Library.** Notion, Google Sheets or a markdown folder, chosen at setup. Field names are in the user's language. The Library holds its own **Settings**: Categories and their fields, language, schedule. Markdown works from the computer only.
- **Memory.** One line on each agent surface says where the Library is. In Claude the apps share one memory and the Code tab keeps its own, so setup writes both. If the line is missing, the skill asks for the link once.
- **Worker.** A local scheduled task in the Claude Desktop Code tab. It runs weekly by default (setup can change it), while the app is open and the computer is awake, and does one catch-up run after sleep. "Process my inbox" runs it on demand.

## Flow

1. **Capture, on the phone.** You share a link to the agent app. For TikTok, YouTube and other links, the agent reads a preview from public pages, then files an Entry in the Inbox with a first Category, summary and Next action. For Instagram it files the link only, because Instagram refuses agent fetches and its embed page no longer carries the caption. The Worker fills in the rest. The same link twice stays one Entry, and the second capture is noted.
2. **Worker run, weekly.**
   - Download: yt-dlp for video, gallery-dl for photos and carousels.
   - Extract: Whisper for speech (mlx-whisper on Apple Silicon, faster-whisper elsewhere), or YouTube's own captions when present. The agent reads on-screen text from keyframes.
   - Finish the Entry: the agent's analysis, a stored thumbnail (none in Sheets), then the media is deleted (a setting keeps it).
   - Dig up the run's quota of Buried Entries, newest first.
   - Last step: write the "Week of …" Digest.
3. **Digest.** Written weekly, or on request in any chat. When it is shown, the agent may offer Proposals, and it acts only on a yes. It also lists Entries the Worker could not finish, and reminds you every 3 months to re-import your Graveyard.

**Statuses:** Inbox → Processed → Used or Dismissed. Also Unavailable (the post is gone; the preview is kept) and Buried.

## Instagram account safety

Instagram has locked sessions for "suspected scraping" after a few dozen downloads, and no safe rate is known. So:
- Every Instagram post is tried without login first.
- The login is a fallback: a few posts per run, with long random pauses.
- The run stops at the first challenge, and the rest waits for next week.

Setup states the risk. TikTok and YouTube use the normal path. A login failure leaves the Entry in the Inbox with a note ("log in to Instagram in Chrome"). Windows reads cookies from Firefox or an exported `cookies.txt`, since Chrome's are encrypted there.

## The Graveyard

- **Source:** official exports only.
  - Instagram's "Download your information" gives saved posts (link, date, author) and collections with their names. Parse it by structure, because labels follow the account language.
  - TikTok's "Download your data" gives Favorites (link, date).
  - Google Takeout gives YouTube Liked videos and playlists. Watch Later is excluded; copy it into a playlist first.
- **Import:** every post becomes a Buried Entry. Instagram collections seed the Categories at setup, and each Buried Entry starts in its collection's Category.
- **Drip:** each run digs up 10 Buried Entries by default; you can steer it ("dig up my recipes next"). An Amnesty Dismisses every Buried Entry older than a date.
- **Never touch the platforms:** nothing is unsaved or changed on Instagram, TikTok or YouTube. Re-imports skip links already in the Library.

## Setup

Setup is a conversation on the computer, in the Code tab, after the plugin is added.

1. "What do you save?" plus any Instagram collections → Categories and their fields.
2. Pick the Library; the agent creates it with its Settings.
3. Pick the weekly day.
4. Pick the browser you are logged in with.
5. The agent installs the tools, asking first: uv, ffmpeg, yt-dlp, gallery-dl, Whisper.
6. Test one link end to end, and approve the Library tools with "always allow" so scheduled runs never stall.
7. The agent saves the Library link to memory and creates the weekly task.
8. On the phone: connect Notion or Sheets, and share a test link.
9. Optional: request the Graveyard exports. They arrive in hours to about 2 days. Then say "import my Graveyard".

## Scope of v1

- **In:**
  - Instagram (reels, carousels, photos), TikTok and YouTube. Other links are filed with whatever the page shows.
  - Tested with Claude on Android (Pixel) and Mac.
- **Out:**
  - iOS share-sheet capture, and Instagram Stories.
  - Terminal-agent scheduling.
  - Pushing into other apps.
  - Thumbnails in Sheets.

## Release

- MIT license, on a public GitHub repo that is a Claude plugin marketplace.
- Claude users add it from *Customize → Plugins → Add marketplace*. It reaches web, desktop, mobile and Claude Code, and updates sync automatically.
- Other agents install it with `npx skills add`. A ZIP upload is the fallback.
- Submit to Anthropic's directory once v1 works on the Pixel and the Mac.
- The README states the Instagram account risk.

## To verify while building

- [x] The plugin's skill loads in the Claude Android app, and Capture works from Instagram's share menu. (Pixel, 2026-10-24: the Entry was created with Status Inbox.)
- [ ] The synced plugin loads in the Desktop Code tab and inside its scheduled tasks.
- [ ] ✗ Claude's fetch tool reads the caption from the embed page. (2026-10-24: refused on the Pixel. From a home connection, the embed page is now a page that JavaScript fills in, with no caption in its HTML, even for public posts.)
- [ ] Claude's fetch tool on the phone accepts a preview URL that the agent built (the embed page, YouTube oEmbed). Its docs say it fetches only URLs already in the conversation. (2026-10-24 on the Pixel: every Instagram preview URL was refused. A YouTube Short got a full preview, with author, title, Summary and Next action. Which of its two preview URLs served it is not recorded.)
- [ ] ✗ The fetch tool's text keeps the TikTok caption and the YouTube description from the post page. Their oEmbed endpoints do not return them. (2026-10-24 on the Pixel: a shared TikTok gave no preview at all. YouTube gave the title but not the description.)
- [x] A shared link with no text triggers the skill in the Android app, through the skill's description alone. Memory holds no Capture rule to fall back on. (Pixel, 2026-10-24.)
- [ ] TikTok short links and Instagram `/share/` links resolve to one canonical link, so the same post shared twice stays one Entry. (2026-10-24: TikTok's Android share gives a `vm.tiktok.com` short link. Capture could not resolve it on the Pixel, so the Worker must.)
- [ ] The Notion connector stores a 2,200-character caption in one field.
- [ ] Claude's Sheets connector can append rows to an existing sheet.
- [ ] The Instagram export parser handles a real export, including collections with no save date.
- [ ] Anonymous yt-dlp works for public reels from a home connection.
