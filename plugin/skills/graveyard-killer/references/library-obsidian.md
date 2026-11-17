# The Library in Obsidian

How an Obsidian Library does each operation in [library.md](library.md#operations), and Obsidian's own rules. The Library is a folder of Markdown files in the user's Obsidian vault, on their computer. You read and write it through this skill's `scripts/vault.py`, with no connector and with no need for Obsidian to be open.

## Only on this computer

The vault is a folder on the user's computer. Only an agent that runs this skill's scripts on that computer reaches it: the Claude Desktop Code tab, or a Worker run. A phone app, a chat with no shell, or a sandbox in the cloud cannot. So before the first operation of a job, run `vault.py check "<Library>"`. If you cannot run it, or it says the folder does not exist, tell the user in one line, in their language, that their Library is in Obsidian on their computer: they save a post from the phone by sharing it to Obsidian's "Share here" note, and they ask about their saves or answer a Ping in the Claude Desktop Code tab on the computer. If this is that computer, add that the Library's folder may have moved. Then stop.

The pointer's link is the Library folder's absolute path on this computer. Another computer has its own path to the same synced vault, in its own pointer.

## Layout

The Library is one folder inside a vault: the folder the pointer names. It holds:

- `Settings.md`, a note whose body holds the sections of [library.md](library.md#the-settings) as headings and tables, in their order. After library.md's sections comes a **Files** section, for Obsidian only:

  ```markdown
  ## Files
  | File | Name in this Library |
  | --- | --- |
  | Entries | Schede |
  | Share here | Condividi qui |
  | Already read | Già letti |
  | Attachments | Allegati |
  ```

- the **Entries** folder, with one note per Entry, named in the Settings language;
- the **Share here** note, where the phone shares posts, and the **Already read** note, where the Worker moves each share once read, both named in the Settings language;
- the **Attachments** folder, for the covers;
- a Base, `<Library name>.base`, which shows the Entries as a table and as cards with their covers. The user opens it in Obsidian. Agents never read or write it.

Each name in the Files section is a name inside the Library folder: `<Library>/<Entries>/` and `<Library>/<Attachments>/` are folders, and `<Library>/<Share here>.md` and `<Library>/<Already read>.md` are notes.

An Entry is a note in the Entries folder. Its fields are the note's properties (its YAML frontmatter), with the Library's field names:

| Kind in library.md | In Obsidian |
| --- | --- |
| text | a text property, on one line |
| link | a text property holding the link |
| one label | a text property holding the label |
| labels | Obsidian's own `tags` property, a list |
| date | a date property, such as `2026-11-16` |

Category fields are extra text properties. An Entry also has a **Cover** property, for Obsidian only and named in the Settings' Fields table, which holds a link to the cover image in the Attachments folder. An Entry's long text is the note's body.

**Tags** are Obsidian tags, so the Fields table names the Tags field `tags`, whatever the Settings language. A tag holds no spaces and not only digits: vault.py writes a Tag's spaces and marks as hyphens, such as `pasta-veloce`, and keeps its letters and accents.

**Note names.** Name a new Entry's note after its post: `<Platform> <id>`, such as `Instagram DQx1abc`, with the `id` from the link script, or with the Title without "⏳ " when the script gives no `id`. `vault.py` makes the name safe and unique. A note is never renamed: the Base shows the Title, and a note's name only has to stay the same, since links to it name it.

The shared saves are the shares in the Share here note's body.

## vault.py

Run every read and write of the Library with this skill's `scripts/vault.py`, and never edit the vault's files any other way. It writes properties as valid YAML whatever a caption holds, changes only the properties you name, never leaves a note half written, and escapes text from a post. Every command prints JSON. A command that fails prints `{"error": "..."}`: say what failed, and do not write around it.

Run it the way you run this skill's other scripts, `python3 scripts/vault.py` or with the script's full path, such as `python3 /path/to/graveyard-killer/scripts/vault.py list "<folder>"`, one command per call, with no shell variables. Put the paths you pass it in double quotes, not the script's own path: an approval to run the script matches the command as written. A command that writes takes its JSON from a file, never from the command itself: Claude Code holds back a command whose text has a brace beside a quote, and text from a post can hold anything. So for each write:

1. Write the JSON with your file-writing tool to a new file in your scratchpad folder, or else in the system's temporary folder, with a new name each time, such as `gk-12.json`: a file tool may refuse to overwrite a file it has not read.
2. Run the command with `--input "<that file>"`:

   ```
   python3 scripts/vault.py update "<the note's path>" --input "<scratchpad>/gk-12.json"
   ```

   where the file holds, for example:

   ```json
   {"set": {"Stato": "Elaborato", "Elaborato il": {"date": "2026-11-16"}, "Nota": null},
    "sections": [{"heading": "Trascrizione", "parts": [{"post": "The first paragraph, word for word."}]}]}
   ```

- **`set`** sets properties and leaves every other one as it was. A text is a string; `tags` is a list of strings; a date is `{"date": "YYYY-MM-DD"}`; `null` clears a property. **`unset`** removes properties.
- **`append`** adds parts at the end of the body, and **`prepend`** at its start. A part is `{"post": "..."}` for text from the post, such as a caption, a transcript paragraph or on-screen text; `{"markdown": "..."}` for your own words, such as a "Captured again" line; or `{"heading": "..."}` for a heading. **`sections`** puts parts under a `## ` heading: it replaces that section where the note has one, else adds it at the end, so writing it twice never doubles it. **`body`** replaces the whole body.
- **`list`** prints a first line `{"count": N}`, then one note per line, with its `name` and its properties: all of them, or one `--field` each. `--where` keeps only the notes that meet a condition: `NAME=VALUE`, `NAME!=VALUE`, `NAME~TEXT` (holds the text, in any case), `NAME>=VALUE` or `NAME<=VALUE` (dates compare as dates), and `NAME=` for an empty value. Several `--where` must all hold. `--extra path` and `--extra uri` add each note's path, for writes, and its link. A note's path is `<folder>/<name>.md`.
- A `list` or `search` answer longer than about 25,000 characters is refused, since the shell would cut it. Ask for fewer fields, add a `--where`, or add `--out "<scratchpad>/gk-list.jsonl"` and read that file in parts with your file-reading tool.

## Writing to Obsidian

- **Text from the post** goes in the body only as a `{"post": ...}` part. Obsidian reads the body as Markdown, so a caption's `#hashtags` would become tags in the user's vault, and `[[...]]` links. vault.py escapes them. In properties it needs nothing: Obsidian shows no Markdown in text properties, and a hashtag there makes no tag (Obsidian's help, checked 2026-11-16).
- **One line.** A text property holds one line, and vault.py writes a line break as a space. So a caption on one line goes whole in Caption. For a caption of more than one line, put its first line in Caption and the whole caption in the body, under a heading with the Library's name for Caption.
- **Tags.** Reuse the tags already on Entries, spelled the same: read them with `list`, asking for `tags`.
- **Labels and links.** Write Statuses and Categories exactly as the Settings name them. Write a post's Link exactly as the link script gives it.

## Operations

`<Library>` is the pointer's path, and `<Entries>`, `<Share here>`, `<Already read>` and `<Attachments>` are the names in the Settings' Files section.

### Read the Settings

`vault.py read "<Library>/Settings.md"`, and read its `body`.

### Write the Settings

Read the Settings note, change its body, and write the whole body back at once with `vault.py update "<Library>/Settings.md"` and an input file holding `{"body": "..."}`: change the value under a section's heading, or add or update a row in its table. A value with several lines, such as "Open offers", stays in one table cell, with `<br>` between its lines. Write right after you read, with no other write in between, and keep every other line of the body as it was.

### Find an Entry by its link

`vault.py list "<Library>/<Entries>" --field "<Link>" --where "<Link>=<the canonical link>" --extra path --extra uri`. When you know the post's id, also look for a Link that contains it, with `--where "<Link>~<id>"`. Keep the note's `path` for the writes that follow.

### Query the Entries

`vault.py list "<Library>/<Entries>"`, with one `--field` for each field the question needs, such as Status, Captured and Note, and a `--where` for the question, such as `--where "<Status>=<Inbox label>"` or `--where "<Processed>>=2026-11-10"`. For every Link of the Library, as for a Graveyard import, ask for `--field "<Link>"` alone, with `--out` when the Library is large. Ask once per job and work from the answer. A note gives no time of creation: order Entries with the same date by name.

### Search the Entries

`vault.py search "<Library>/<Entries>" <word> [<word> ...]`: the notes whose properties or body hold every word, in any case, each with its properties and `uri`. Search for one or two telling words, then other forms of them (singular, plural, the Settings language and English) when nothing comes back.

### Create an Entry

`vault.py create "<Library>/<Entries>" "<note name>"`, with every field in `set` under the Library's names, and the long text as [Update an Entry](#update-an-entry) lays it out: a multi-line caption in `sections`, under the Library's name for Caption. For many Entries at once, such as a Graveyard import, use `vault.py create-many "<Library>/<Entries>"` with an input file holding `{"notes": [{"name": "...", "set": {...}}, ...]}`, up to 100 notes a call.

### Update an Entry

`vault.py update "<the note's path>"`. For many Entries at once, such as an Amnesty, use `vault.py update-many` with an input file holding `{"notes": [{"path": "...", "set": {...}}, ...]}`. The long text:

- a "Captured again" line goes at the end, as a `markdown` part in `append`;
- the full caption, when it has more than one line, goes in `sections`, under the Library's name for Caption;
- the Transcript and the On-screen text go in `sections`, each under its heading, with one `post` part per paragraph.

A section replaces the one already there, such as the caption that Capture wrote from a preview, so a caption is never in the body twice.

**The cover.** From the post script's `thumbnail` file, before its `clean`: `vault.py attach "<thumbnail>" "<Library>/<Attachments>" "<the note's name>"`, then set the Cover property to the `link` it prints, such as `[[Graveyard Killer/Allegati/Instagram DQx1abc.jpg]]`. With no `thumbnail`, set Cover to the `cover_url` when there is one. With neither, the Entry has no cover.

### Add a Category

Add the rows to the Settings' Categories table, as [Write the Settings](#write-the-settings) says. Category is a text property, so there is no list of choices to change. Its new fields appear on each Entry that has them; the user can add them as columns in the Base.

### Add a Tag

Nothing to add: a tag is free text. Reuse the spelling already on the Entries.

### List the shared saves

`vault.py shares "<Library>/<Share here>.md" "<Library>/<Already read>.md"`. The phone adds each share at the end of the note, on a new line: a link alone, or the post's caption and then its link, as Instagram shares a reel. The script splits the note into `shares` the same way every time: a share ends at a line that holds a link, and the lines before it, back to the share before, are its caption. Text after the last link is a share with no link. Use its shares as they are.

When the phone and this computer changed the note at the same time, a sync app such as Syncthing keeps one version as a conflict copy next to it. `shares` takes in the copies' shares that are not yet filed, drops from the note the shares already in Already read, and moves the copies to the vault's `.trash` folder; its `merged` names them. There is nothing more to do. For each share:

- its link is its `link`: the link on its last line, or none;
- it was shared on the day the Share here note last changed, the `modified` of this run's first `shares` call: keep that date for the whole run, since each move changes the note;
- the text it was shared with is its `text`, exactly as the note holds it: [Adopt a shared save](#adopt-a-shared-save) moves that exact text.

### Adopt a shared save

In one command, which creates the Entry and moves the share's text from Share here to Already read, so that the share is never filed twice:

`vault.py adopt "<Library>/<Share here>.md" "<Library>/<Already read>.md" "<Library>/<Entries>" "<note name>" --input "<file>"`

The input file holds what [Create an Entry](#create-an-entry) would, plus `"share"`: the share's `text`, exactly as `shares` gave it. Put the "Shared as" line, when there is one, as a `post` part in `prepend`. If it says the text is not in the note, run `shares` again and use the share's new text: the phone may have added to the note meanwhile. It writes nothing then. Already read keeps the text escaped, so its hashtags make no tags.

### Set a shared save aside

`vault.py move-text "<Library>/<Share here>.md" "<Library>/<Already read>.md"` with an input file holding `{"text": "<the share's text>"}`. The Ping names it.

### Remove a duplicate

`vault.py trash "<the note's path>"`: it moves the note to the vault's `.trash` folder, where Obsidian's own trash keeps deleted files. Obsidian does not list that folder, so when you ask the user, and when you tell them it is done, say that the note moves to the vault's `.trash` folder, from where they can move it back in Finder or File Explorer.

### Link to an Entry

Name the Entry by its Title, with its `uri` as the link, such as [Pasta alla Norma](obsidian://open?vault=My%20Vault&file=Graveyard%20Killer%2FSchede%2FInstagram%20DQx1abc). The link opens the note in Obsidian, on the phone too when the phone's vault has the same name.

### Create the Library

See [setup-obsidian.md](setup-obsidian.md#create-the-library).
