# The Library contract

Every Graveyard Killer job reads and writes the Library the same way, whatever app it lives in. This file describes what every Library app shares: the Entries, the Settings and the [operations](#operations) the jobs use. How an app does each operation, and its own rules, are in that app's file.

## Library apps

A Library lives in one **Library app**. The host of the link in the pointer line, `Graveyard Killer Library: <link>`, tells which:

| Link | Library app | Its file |
| --- | --- | --- |
| A host that is, or ends in, `notion.so`, `notion.com` or `notion.site`, such as `app.notion.com` or `www.notion.so` | Notion | [library-notion.md](library-notion.md) |
| A Google Sheet: the host `docs.google.com`, with a path that starts with `/spreadsheets/` | Google Drive | [library-google-drive.md](library-google-drive.md) |

Read your Library app's file before the first operation of a job, and follow it for every operation below. Never read another app's file: it does not apply. If the link matches no row above, it is not a Library link: tell the user so in one line, and stop.

A Library holds:

- the **Entries**, one per captured post;
- the **Settings**;
- the **shared saves**, when the app has a share route: posts the phone shared into the Library with no agent, which the Worker adopts.

## Names

The Library uses the user's own names for fields and Statuses, in their language. This file uses the canonical English names. The Settings map each canonical name to the Library's name. Write to the Library with the Library's names, and use them in replies too.

## Entry fields

| Field | Kind | Holds |
| --- | --- | --- |
| Title | text | A short title in the Settings language. It starts with "⏳ " while the Entry waits for the Worker (Inbox or Buried) |
| Link | link | The canonical link, which is also the duplicate key |
| Platform | one label | `Instagram`, `TikTok`, `YouTube` or `Other`. These labels are fixed. The scripts' lowercase `platform` values map to them |
| Author | text | The account that posted it |
| Caption | text | The post's own text, word for word, in its original language |
| Category | one label | One Category from the Settings |
| Summary | text | In the Settings language: one or two sentences at Capture, two or three after the Worker |
| Next action | text | The one thing the user could do with it. When the post gives a date for it (an event, a deadline, an offer that ends), the Next action names that date in full, such as "Book the Roma concert for 14 November 2026", so a Ping or the Digest can bring it up in time |
| Tags | labels | Free labels in the Settings language, at most 5 per Entry. Reuse an existing Tag wherever one fits, and [add a Tag](#add-a-tag) before using a new one |
| Status | one label | One Status (see below) |
| Captured | date | The date of the first Capture. Empty for an Entry imported from the Graveyard |
| Saved | date | The date the user saved the post on the platform, from the Graveyard import. Empty for a Captured Entry |
| Processed | date | The date the Worker finished it, as Processed or Unavailable. The Worker's limits and the Digest use it |
| Note | text | Something about this Entry that needs attention, in the Settings language. It is empty when nothing does |

Each Category can add its own fields. They are named in the Settings and are extra text fields on the Entries.

An Entry's **long text** holds what does not fit a field:

- one dated line for each extra Capture of the same post;
- the full caption, when it is longer than one text value holds in the Library app;
- a Transcript section and an On-screen text section, written by the Worker. Their headings are "Transcript" and "On-screen text" in the Settings language. Use the same words on every Entry, so look at a Processed Entry for the words already in use (in Italian: "Trascrizione", "Testo a schermo").

An Entry may also have a **cover**: the post's image, where the Library app shows one.

## Writing to the Library

These rules hold in every Library app. Your app's file adds its own.

- **Song lyrics.** Leave song lyrics out of every field and of the long text, in captions and descriptions as in transcripts.
- **Labels.** Write Statuses and Categories exactly as the Settings name them, never from memory.

## Statuses

| Status | Meaning |
| --- | --- |
| Inbox | Captured, waiting for the Worker to read it: a placeholder |
| Processed | The Worker finished it |
| Used | The user did its Next action |
| Dismissed | The user chose not to act on it |
| Unavailable | The post was deleted or made private before the Worker could download it, or 3 reads failed ([worker.md](worker.md#failed-tries)) |
| Buried | Imported from the Graveyard, waiting to be dug up |

A shared save counts as Inbox. The Worker adopts it ([worker.md](worker.md#adopt-the-shared-saves)).

## Duplicates

When a resolved link shows that two Entries hold the same post, the older Entry stays and gains a "Captured again on <date>" line in its long text. The newer one gets the Note "Duplicate of <[link to the older Entry](#link-to-an-entry)>", and is [removed](#remove-a-duplicate) once the user agrees.

## The Settings

They have these sections, in this order. Here is an example for an Italian Library:

```markdown
## Language
Italiano

## Fields
| Field | Name in this Library |
| --- | --- |
| Title | Titolo |
| Link | Link |
| Platform | Piattaforma |
| Author | Autore |
| Caption | Didascalia |
| Category | Categoria |
| Summary | Riassunto |
| Next action | Prossima azione |
| Tags | Tag |
| Status | Stato |
| Captured | Catturato il |
| Saved | Salvato il |
| Processed | Elaborato il |
| Note | Nota |

## Statuses
| Status | Label in this Library |
| --- | --- |
| Inbox | Da leggere |
| Processed | Elaborato |
| Used | Usato |
| Dismissed | Scartato |
| Unavailable | Non disponibile |
| Buried | Sepolto |

## Categories
| Category | What goes in it | Its own fields | Fallback |
| --- | --- | --- | --- |
| Ricette | Recipes and cooking | Ingredienti | |
| Viaggi | Places to visit | Luogo | |
| Altro | Everything else | | yes |

## Schedule
Ogni giorno 13:00

## Limits
| Setting | Value |
| --- | --- |
| Downloads per day | 20 |
| Downloads per week | 100 |

## Pings
| Setting | Value |
| --- | --- |
| Ping by | push |
| Last Ping | 2026-11-10 |
| Last Digest | 2026-11-03 |
| Open offers | 4 · 2026-11-10 · Ricette · lista della spesa · La lista della spesa per la carbonara · https://app.notion.com/p/418f4b208c40812fb8e0c2a4d1e5f6a7 |

## Preferences
| Kind | Answer |
| --- | --- |
| Ricette · lista della spesa | sempre |
| Eventi · calendario | chiedimi |

## Graveyard
| Setting | Value |
| --- | --- |
| Dig up next | Ricette |
| Last import | 2026-10-26 |

## Version
0.8.0
```

- **Categories.** Exactly one is the fallback. The Category field's choices are the Category names from this table.
- **Schedule.** When the Worker runs, in local time: every day by default, or the weekdays the user chose.
- **Limits.** How many posts the Worker may download, counted from the Processed dates ([worker.md](worker.md#steps), step 2).
- **Pings.** "Ping by" is how a Ping reaches the user: `push`, `email` or `none` ([ping.md](ping.md#send-it)). "Last Ping" and "Last Digest" are dates, or empty. "Open offers" holds the numbered offers of the last 7 days' Pings that the user has not answered yet, one per line: the number, the Ping's date, the kind, the offer in a few words and the link to its Entry, separated by " · ". It is empty when none is open ([ping.md](ping.md#send-it)).
- **Preferences.** One row per kind of Proposal: its Category and action, and the user's answer (always, ask me or never, in the Settings language). It starts empty ([ping.md](ping.md)).
- **Graveyard.** "Dig up next" is a Category the user asked to see first, or empty. "Last import" is the date of the last Graveyard import, or empty.
- **Version.** The Library's format: the newest step of [upgrade.md](upgrade.md) that it has had. Only Setup and an upgrade write it.

A new Library starts with the Limits above, Version at the newest heading in [upgrade.md](upgrade.md#steps), and every other new setting empty. An older Library may lack a section or a row, or hold one that a later version replaced: [upgrade.md](upgrade.md) says how to read it, and how a Worker run brings it up to date.

## Operations

The jobs name these operations. Your Library app's file says how to do each one, under the same heading.

### Read the Settings

Read every section of the Settings.

### Write the Settings

Set a value in a section, or add or update a row in a table section, such as a Preference.

### Find an Entry by its link

Find the Entry whose Link equals the canonical link exactly. A link that only a redirect can resolve, such as a TikTok link from an export, may sit in the Library under its full form: when you know the post's id, also look for a Link that contains it, unless the job asks for an exact match only.

### Query the Entries

Find the Entries with a Status, or with a date in a range, or read one field of many Entries, such as every Link for a Graveyard import. Ask each question once per job and work from the answer. Never query once per post in a loop.

### Search the Entries

Find the Entries whose Title, Summary, Next action, Tags, Author or Caption hold some words, and whose long text does when the app can search it.

### Create an Entry

Add one Entry, or many in batches, with the fields the job gives.

### Update an Entry

Change some of an Entry's fields, add to the end of its long text, or set its cover.

### Add a Category

Add one or more Categories, all in one go: rows in the Settings' Categories table, and choices for the Category field.

### Add a Tag

Make a new Tag available, before the first Entry uses it.

### List the shared saves

Find the shared saves, each with the places its link may sit, in order, and the day it was shared.

### Adopt a shared save

Turn a shared save into an Entry with the fields the Worker gives it, and with the "Shared as" line at the start of its long text when the Worker gives one.

### Set a shared save aside

Put a shared save that holds no link out of the Worker's way, when the app has a place for it. The Ping names each one moved.

### Remove a duplicate

Remove an Entry whose Note says it is a duplicate, once the user agrees.

### Link to an Entry

Point the user to one Entry in a reply.

### Create the Library

Setup creates the Library as the app's setup file says.
