# No server and no API keys: the user's computer downloads, the user's agent thinks

Graveyard Killer is for people who will not manage API keys or a server. So it has neither. The user's own agent, on their subscription, does all analysis, and it reads and writes the Library only through that agent's connectors. Downloads happen on the user's own computer, in a weekly Worker run. Only that machine has the user's Instagram login and a home connection that Instagram does not throttle.

## Considered Options

- **A hosted service that downloads for everyone.** It would need our own Instagram accounts and datacenter IPs, which Instagram blocks or rate-limits. It would also mean accounts, billing and running a server. Rejected.
- **The phone's chat agent does everything.** Chat agents run code in a cloud sandbox. Gemini's has no internet, ChatGPT's blocks the open web, and none has the user's login. Uploading Instagram cookies to a sandbox would hand over the account. Rejected. The phone still captures. For TikTok, YouTube and other links it reads a preview from public pages. For Instagram it files the link only (Pixel run, 2026-10-24).
- **The Worker calls an LLM API itself.** Fully automatic, but it needs a key the target users cannot set up. Rejected.
- **The Worker runs on a cloud instance by default.** This covers Claude Code on the web, a scheduled cloud agent, Cowork's cloud, and a rented server. It would run while the computer sleeps. But a cloud machine has a datacenter IP, and sites block yt-dlp from those networks. The claude-video project reports that its local engine "can't fetch most URLs" in Cowork's cloud for this reason (README, checked 2026-10-24). Its one cloud path that works needs a Gemini API key. A rented server is also a server to manage. Rejected.

## Consequences

- An Entry captured on the phone stays a preview until the Worker's next weekly run. An Instagram Entry holds only its link until then. This makes Stories (gone in 24 hours) impossible in v1.
- Phone-only users never get transcripts.
- The Worker runs only while the Claude Desktop app is open and the computer is awake. A missed run catches up once.
- Downloading with the user's login puts their real Instagram account at risk. Instagram has flagged sessions for "suspected scraping" after a few dozen downloads, and no safe rate is known. So the Worker tries every Instagram post without the login first. It uses the login only as a fallback, for a few posts per run with long random pauses, and stops the run at the first challenge. It digs up only 10 Buried Entries per run by default. Setup states this risk to the user.
- Meta Muse (Oct 2026) does not remove the download: it is chat-only, unavailable in the EU, and its terms forbid automating it. Its model's API needs the video file.
