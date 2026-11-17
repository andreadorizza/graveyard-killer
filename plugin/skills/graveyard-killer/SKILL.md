---
name: graveyard-killer
description: Capture a shared post into the user's Graveyard Killer Library, and recall what the user saved there. Use whenever a message is a link (Instagram, TikTok, YouTube or any web page) with no request, such as a bare link, a link inside an app's share text, or a link with a short "save this"; whenever the user asks about a post they saved; and whenever the user names Graveyard Killer or answers one of its messages, for example to set it up, import old saves, get its Digest or reply to its offers.
---

# Graveyard Killer

Graveyard Killer files the posts a user sends you into their own **Library**, which lives in an app they own, Notion or Google Drive: their **Library app**. Each post becomes one **Entry**. You do the work through the user's own connectors: there is no server and no API key.

The scripts in this skill run with `python3`. On Windows, `python3` can be the Microsoft Store's placeholder, which prints "Python was not found" and exits with code 49. Then use `py -3` in its place for every script.

Talk to the user in the language set in their Library's **Settings**. Keep this skill's own words (field and Status names) for your thinking, and write the Library's names into the Library.

With the user, use plain words in their language instead of this skill's terms, and recognise those words when they write them:

| This skill says | Say | In Italian |
| --- | --- | --- |
| Library | your Library | la tua Libreria |
| Entry | card | scheda |
| Inbox Entry | a placeholder | un segnaposto |
| Worker run | the tidy-up | il riordino |
| Digest | the recap | il riepilogo |
| Proposal | an offer | una proposta |
| Graveyard | old saves | vecchi salvataggi |
| dig up | bring back | ripescare |
| Amnesty | set aside old saves | scartare i vecchi salvataggi |

## 1. Choose the job

A **Capture** is the user sending you one post's URL to keep it. It arrives as a link on its own, a link inside an app's share text ("Check out this reel!"), or a link with a short "save this". The user is usually on their phone and wants to send the next post in seconds. So finish a Capture in one turn and ask nothing.

A link that comes with a question or a task ("summarise this", "is this true?") is a request, and a message with no link is ordinary chat. Answer those as usual, without this skill, unless they ask about the user's saves.

Done when you know the job:

- **Capture**: follow the steps below, then [references/capture.md](references/capture.md).
- **Recall**: the user asks about something they saved ("that carbonara recipe I saved?", "what did I save this week?"). Follow the steps below, then [references/recall.md](references/recall.md).
- **Worker run**: the user asks to run the Graveyard Killer worker or its tidy-up, by name. A request that does not name either, such as "process my inbox", is not a Worker run: answer it without this skill. Use the `graveyard-killer-worker` skill and pass it the user's whole message: it runs on its own, on the model it needs. When it returns, give its final message to the user as it is. If you have no shell, as in a phone app, tell the user the Worker runs on their computer, in the Claude Desktop Code tab, in Codex or in OpenCode, and stop.
- **Ping answer**: the user answers a Graveyard Killer Ping, in the chat where it arrived or in any other chat by naming Graveyard Killer, such as "yes to 1", "Graveyard Killer, yes to 4", "always for recipes" or "remove the duplicate", or asks what Graveyard Killer offered. Follow the steps below, then [references/ping.md](references/ping.md#when-the-user-answers).
- **Schedule the Worker**: the user asks Graveyard Killer to run its Worker on a schedule, or to change its time, for example "schedule the Graveyard Killer worker". Follow the steps below, then [references/schedule.md](references/schedule.md).
- **Setup**: the user asks to set up Graveyard Killer, or has no Library yet. On a phone, tell them Setup runs on their computer, in the Claude Desktop Code tab, in Codex in the ChatGPT desktop app, or in OpenCode with no paid plan, and stop. Otherwise go straight to [references/setup.md](references/setup.md), which creates the Library.
- **Graveyard**: the user asks Graveyard Killer to import their old saves, to dig up a Category next, or for an Amnesty. Follow the steps below, then [references/graveyard.md](references/graveyard.md).
- **Digest**: the user asks for their Graveyard Killer Digest, or what is new in their Library. Follow the steps below, then [references/digest.md](references/digest.md).
- **Update**: the user asks to update Graveyard Killer. In OpenCode, follow [references/opencode.md](references/opencode.md#update); in Codex, [references/codex.md](references/codex.md#update). Elsewhere, tell them to open *Customize → Plugins* in the Claude app and choose *Check for updates* on the Graveyard Killer marketplace.
- **Views**: the user asks Graveyard Killer for the gallery or the other views of their Library, or to add them again. Follow the steps below, then [add the views](references/library.md#add-the-views), and say in one line where to find them.
- **Preference**: the user tells Graveyard Killer to always, never, or ask before making a kind of offer, such as "stop offering grocery lists". Follow the steps below, then [references/ping.md](references/ping.md#when-the-user-answers).
- **Instagram login**: the user asks to turn Graveyard Killer's Instagram login on or off, or says yes to a Ping's offer to read gated posts with it. Follow the steps below, then [references/login.md](references/login.md).

## 2. Find the Library

Look in your instructions and memory for the Library's location, one line: `Graveyard Killer Library: <link>`. Done when you hold the Library link.

- If the line is missing, ask the user once for the link to their Graveyard Killer Library, such as its Notion page's or Google Sheet's link. If they have no Library yet: on a computer, offer Setup ([references/setup.md](references/setup.md)); on a phone, tell them Setup runs on their computer, in the Claude Desktop Code tab, in Codex or in OpenCode, and stop.
- When you had to ask for the link, give the user the pointer text from [setup.md](references/setup.md#the-pointer) once, ready to paste into the Instructions in their Claude settings, so that you need not ask again.

## 3. Read the Settings

Read [references/library.md](references/library.md), then the file of the Library app that the Library link's host names there. Every job reads and writes the Library through the operations those two files describe. Then [read the Settings](references/library.md#read-the-settings). Done when you know the language, every field name, every Status label, every Category and the fallback Category.

Then compare the Settings' Version with [references/upgrade.md](references/upgrade.md). When the Library is older or newer than this skill, or has no Version, follow upgrade.md: a Worker run, or Setup for a Library made elsewhere, brings an older Library up to date first, and every other job only reads it as upgrade.md describes. Done when you know which.

If the Library or its Settings cannot be read, tell the user which one failed and that their connector for the Library app, such as Notion's or Google Sheets', may need reconnecting, and stop.
