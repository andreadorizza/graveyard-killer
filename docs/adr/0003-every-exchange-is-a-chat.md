# Every exchange with the user is a chat

Users will not open a recap page in Notion, so v1's weekly Digest pages would go unread. So the agent talks to the user only in a chat. A Worker run that has something for the user sends a **Ping**: it alerts the user and ends its own chat with what it found. It also saves its numbered offers in the Library's Settings, so the user answers in that chat or in any other chat, on the phone too. A run pings only for Proposals on the Entries it just read (a grocery list for a recipe, a calendar event for a dated one; at most 5, the most urgent first) or for something only the user can fix. Otherwise it stays silent, except that after 7 days with no Ping it sends the Digest. The first time a kind of Proposal comes up, the agent asks for a **Preference** (always, ask me, never) and records it in the Settings. "Always" counts as a yes only for the user's own apps. Anything that reaches other people or costs money asks every time.

## Considered Options

- **Digest pages in the Library, with Proposals as checkboxes.** Each run wrote a dated page. Rejected: the user never looks there. Pages already written stay.
- **A recurring calendar event as the weekly reminder.** No tokens, but it only sends the user to go and look. Rejected.
- **Answering a Ping in any chat,** with each open offer written on its Entry. It works across devices, but it adds state to every Entry. Rejected: one list in the Settings does the same.
- **Answering only in the run's chat,** as until 0.6.0. Scheduled runs have no Remote Control, so the user could answer only on the computer, and an offer they missed there was lost. Replaced in 0.7.0 ([#2](https://github.com/andreadorizza/graveyard-killer/issues/2)).
- **A server that keeps one conversation alive** and carries it to the phone, as OpenClaw's Gateway does through WhatsApp, Telegram or Signal, and Rakazo through its own phone apps. The agent then remembers its offers in its own conversation. [ADR-0001](0001-no-server-no-api-keys.md) rules out a server, so the Library holds that memory instead.
- **No Ping.** The Library becomes one more graveyard. Rejected.

OpenClaw, xAI's Grok Bot and Claude Duet work the same way: they wake on a schedule, stay silent unless something clears a bar, and keep an approval gate that a stored preference does not remove (their docs, 2026-11-11).

## Consequences

- A scheduled run asks nothing while it works. At its end it waits in its chat for the user's replies.
- The Ping needs a way to reach the user, chosen at Setup: a push notification or an email to themselves. Both a Gmail email and a Notion mention went through from a scheduled run in Auto mode on 2026-11-11: the email arrived, but Notion sent no notification for a mention made through the user's own connector, so that option was dropped in 0.4.2. Tested on 2026-11-11: scheduled runs are never connected to Remote Control, and the tool that would connect one refuses unattended sessions. So a push from a run reaches only the computer, and the run's chat does not show on the phone. Since 0.7.0 the email carries the whole Ping, and any chat can answer it ([#2](https://github.com/andreadorizza/graveyard-killer/issues/2)).
- The Settings gain a Pings section (how to reach the user, Last Ping, Last Digest, Open offers) and a Preferences table. Open offers keeps each Ping's numbered offers for 7 days. Every chat reads it before it acts on an answer and removes the offer it answered, so an offer is never done twice.
- Each Proposal is offered once, in the Ping of the run that reads its Entry. A Digest offers only Proposals about the Library itself, such as tidying or the Graveyard. In any chat the user can still ask for any action.
- A Proposal's result comes in the chat, or goes to another app on the user's yes.
