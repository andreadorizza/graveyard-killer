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
The Captures that are not yet processed.
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
To turn a Buried Entry into a full Entry. Each Worker run digs up a few.
_Avoid_: Exhume, process, restore

**Amnesty**:
The user's choice to Dismiss every Buried Entry older than a date without digging it up.
_Avoid_: Bankruptcy, purge, clear

### The Library

**Library**:
The one database that holds every Entry.
_Avoid_: Database, archive, collection

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
An Entry whose post was deleted or made private before the Worker could download it. It keeps the preview taken at Capture.
_Avoid_: Failed, broken, dead

**Settings**:
The part of the Library that holds the user's Categories, field names, language and schedule. Every agent reads it from there.
_Avoid_: Config, memory, preferences

### Using the Library

**Digest**:
A short review of recent Entries, written by the agent for the user.
_Avoid_: Summary, report, newsletter

**Proposal**:
An action the agent offers while it shows a Digest. Nothing happens unless the user accepts it.
_Avoid_: Suggestion, push, automation
