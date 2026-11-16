# Graveyard Killer

Saved posts go to a folder nobody opens again. This system takes a post you send it, pulls out what it says and files it where you will find and use it.

## Language

### Getting posts in

**Capture**:
The act of sending one post's URL into the system, by any route.
_Avoid_: Save, forward, share

**IG Save**:
Instagram's own bookmark button, which puts a post in the Saved collection inside Instagram. It is not a Capture.
_Avoid_: Save (alone)

**Inbox**:
The Captures the Worker has not read yet. No agent has watched their posts, so the user sees them as placeholders.
_Avoid_: Queue, pending

**Worker**:
The agent on the user's own computer that turns Captures in the Inbox into finished Entries, because only that computer can download with the user's login.
_Avoid_: Server, daemon, bot

**Graveyard**:
The posts a user saved inside the platforms before using Graveyard Killer: the Instagram Saved collection, TikTok Favorites, YouTube Watch Later.
_Avoid_: Backlog, old saves, archive

**Buried**:
An Entry imported from the Graveyard that holds only its link, date saved and author, and waits to be dug up.
_Avoid_: Imported, pending, backlog item

**Dig up**:
To turn a Buried Entry into a full Entry. Each Worker run digs up a few, within its download limits.
_Avoid_: Exhume, process, restore

**Amnesty**:
The user's choice to Dismiss every Buried Entry older than a date without digging it up.
_Avoid_: Bankruptcy, purge, clear

### The Library

**Library**:
The one place that holds every Entry and the Settings, in the user's Library app.
_Avoid_: Database, archive, collection

**Library app**:
The app the Library lives in, such as Notion or Google Drive. A Library lives in exactly one.
_Avoid_: Backend, provider, host, store

**Entry**:
One captured post in the Library, with its text, analysis and category.
_Avoid_: Item, record, post, save

**Category**:
The one bucket an Entry belongs to, from a list the user owns. A Category can add its own fields to the Entries in it.
_Avoid_: Type, folder, collection

**Tag**:
A free label on an Entry. An Entry has any number of Tags.
_Avoid_: Keyword, label

**Next action**:
The one thing the user could do with an Entry, such as "try this prompt" or "book this place".
_Avoid_: To-do, task

**Used**:
An Entry whose Next action the user did.

**Dismissed**:
An Entry the user decided not to act on. It stays in the Library.
_Avoid_: Deleted, archived

**Unavailable**:
An Entry whose post was deleted or made private before the Worker could download it, or whose post the Worker failed to read 3 times. It keeps the preview taken at Capture.
_Avoid_: Failed, broken, dead

**Settings**:
The part of the Library that holds the user's Categories, field names, language, schedule, limits and Preferences. Every agent reads it from there.
_Avoid_: Config, memory

**Upgrade**:
Bringing a Library made by an older version of Graveyard Killer up to date, one idempotent step per version, at the start of a Worker run. The Settings' Version names the newest step the Library has had.
_Avoid_: Migration, update (an update is a new plugin version)

### Using the Library

**Digest**:
A short review of recent Entries that the agent gives the user in a chat: when the user asks, or in a Ping when a week has passed with no other Ping.
_Avoid_: Summary, report, newsletter, recap page

**Ping**:
A message a Worker run sends the user on its own, because it has a Proposal to make or something only the user can fix. The user answers it in that same chat.
_Avoid_: Notification, alert, push

**Proposal**:
An action the agent offers for an Entry, such as a grocery list for a saved recipe or a calendar event for a dated one. Nothing happens without the user's yes.
_Avoid_: Suggestion, automation

**Preference**:
The user's standing answer to one kind of Proposal, such as "always offer a grocery list for recipes" or "never ping me about AI tools". The agent asks for it the first time that kind of Proposal comes up.
_Avoid_: Rule, setting, habit

**Recall**:
An agent looking in the Library for what the user saved: when the user asks about it, or when a conversation touches something the Library holds.
_Avoid_: Search, memory
