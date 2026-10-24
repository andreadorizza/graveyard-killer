---
name: graveyard-killer
description: Capture a shared post into the user's Graveyard Killer Library. Use whenever a message is a link (Instagram, TikTok, YouTube or any web page) with no request, such as a bare link, a link inside an app's share text, or a link with a short "save this". Also use when the user names Graveyard Killer.
---

# Graveyard Killer

Graveyard Killer files the posts a user sends you into their own **Library**, a Notion page they own. Each post becomes one **Entry**. You do the work through the user's own connectors: there is no server and no API key.

Talk to the user in the language set in their Library's **Settings**. Keep this skill's own words (field and Status names) for your thinking, and write the Library's names into the Library.

## 1. Choose the job

A **Capture** is the user sending you one post's URL to keep it. It arrives as a link on its own, a link inside an app's share text ("Check out this reel!"), or a link with a short "save this". The user is usually on their phone and wants to send the next post in seconds. So finish a Capture in one turn and ask nothing.

A link that comes with a question or a task ("summarise this", "is this true?") is a request, and a message with no link is ordinary chat. Answer those as usual, without this skill.

Done when you know the job:

- **Capture**: follow the steps below, then [references/capture.md](references/capture.md).

## 2. Find the Library

Look in your memory for the Library's location, saved as one line: `Graveyard Killer Library: <link>`. Done when you hold the Library link.

- If the line is missing, ask the user once for the link to their Graveyard Killer Library page in Notion. If they have no Library yet, tell them a Library is created during Setup on their computer, and stop.
- With the link in hand, save that line to your memory if you can. If you cannot, give the user the exact line and ask them to add it to your memory or custom instructions.

## 3. Read the Settings

Read the Settings page inside the Library through your Notion connector, as described in [references/library.md](references/library.md). Done when you know the language, every field name, every Status label, every Category and the fallback Category.

If the Library or its Settings cannot be read, tell the user which one failed and that the Notion connector may need reconnecting, and stop.
