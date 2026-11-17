Built for 0.9.0. The spec the Obsidian Library was built from, kept as a record; the skill files and ADR 0007 describe current behaviour. Settled while building (2026-11-16):

- **Phone saves.** Every share is appended to one "Share here" note. On Android that is one step and carries the post's caption (tested on a Pixel); a new note per share takes an extra step there. On an iPhone, a Share Sheet Location of the kind *Bookmarked note* appends to the same note (untested). The Worker moves each share's exact text to an "Already read" note.
- **Sync.** Setup asks how the vault reaches the phone, and says that the Worker reads only what has synced.
- **No phone chat.** Accepted: Recall, answering a Ping and chat Capture work only in the Code tab on the computer (ADR 0007). The Ping email still arrives.
- **The pointer.** The Library folder's absolute path, a new row in library.md's table. It goes in `~/.claude/CLAUDE.md` only.
- **Covers.** Copied from the post script's thumbnail into an Attachments folder, for every platform, and shown by the Base's cards view.
- **Writes.** Through a new stdlib script, `scripts/vault.py`, not by the agent editing YAML.
- **Evals.** `evals/obsidian.json`, against a test vault: a folder with an empty `.obsidian` folder.

# Spec: a Library on Obsidian

Issue #14.

Requested after the 0.7.0 release: keep the Library in an Obsidian vault.

An Obsidian Library is a third Library app ([ADR-0005](https://github.com/andreadorizza/graveyard-killer/blob/main/docs/adr/0005-a-library-in-more-than-one-app.md)): `library-obsidian.md` and `setup-obsidian.md`. The Worker runs on the computer, so it reads and writes the vault's files directly, with no connector.

## Shape

- One note per Entry in an `Entries` folder, its fields as Obsidian properties (YAML frontmatter), its long text as the note body.
- A `Settings` note laid out like the Notion Settings page.
- A Base over `Entries` for the table and a cards view. Bases have table, list, cards, Kanban and map layouts, and cards make "gallery-like views with images" ([Obsidian help](https://obsidian.md/help/bases/views), checked 2026-11-16). Whether a card's image can come from a property is not stated.
- Operations: "Find an Entry by its link" and "Query the Entries" read the frontmatter of the files; no query allowance.

## To settle before a PR

- **Phone saves.** On iPhone, Obsidian 1.13 and iOS 18 have a native share sheet whose Locations can make a new note in a folder from a template ([Obsidian help](https://obsidian.md/help/ios), checked 2026-11-16). On Android the official help says nothing; forum reports say Share inserts into the open note, a chosen file or the daily note only. So "List the shared saves" may need to read links out of a daily note or one "Share here" note.
- **Sync.** The phone's notes reach the computer only through Obsidian Sync, iCloud (Apple only) or a third-party sync. Setup must check that the vault on the computer is the one the phone writes to.
- **No phone chat.** No Claude chat on the phone can read a local vault. So Recall and answering a Ping work only on the computer, which undoes 0.7.0's "answer from any chat" ([ADR-0003](https://github.com/andreadorizza/graveyard-killer/blob/main/docs/adr/0003-every-exchange-is-a-chat.md)) for these users. The Ping email still arrives.
- **The pointer.** `library.md` tells the Library app by the host of the pointer's link. A vault has a folder path or an `obsidian://open?vault=…` link instead, so the pointer rule needs a new row.
- **Covers.** Store the image in the vault (an attachments folder) so it never expires.
- **Evals.** A test vault, like the Drive test Library.

