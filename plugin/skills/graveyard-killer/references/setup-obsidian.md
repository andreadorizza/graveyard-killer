# Setup in Obsidian

The Obsidian steps of [setup.md](setup.md). Read [library-obsidian.md](library-obsidian.md) first. Run each `vault.py` command as that file says.

## Create the Library

1. **Find the vault.** Ask in one question which Obsidian vault the Library goes in, and where its folder is on this computer. In Obsidian, the vault switcher's *Manage vaults* shows each vault, and a vault's menu there can reveal its folder. A vault that iCloud syncs sits on a Mac in `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`. Run `vault.py check "<the vault's folder>"`. Done when its `vault` is not null: then that is the vault's folder, and `vault_name` its name. If it is null, the folder holds no `.obsidian` folder, so it is not a vault Obsidian has opened: ask again.

2. **Check that the phone reaches it.** Ask how this vault reaches the phone: Obsidian Sync, iCloud (iPhone and Mac only), Syncthing (free, Android and computers), or another way. Obsidian supports Obsidian Sync, a paid add-on, on every device, and iCloud between Apple devices; it does not officially support Google Drive, OneDrive or Dropbox on an iPhone; on Android its help points to Syncthing through the community app Syncthing-Fork (Obsidian's help, checked 2026-11-16). Tell the user that a post shared on the phone reaches the Library only once the phone's vault syncs to this computer, and that the Worker reads only what has arrived. Obsidian Sync runs inside the Obsidian app, so with Sync, Obsidian must be open on this computer for shares to arrive; iCloud and Syncthing sync with Obsidian closed, and Syncthing only while the phone and this computer are both on and connected. Done when you know, or the user saves only on this computer.

3. **Name it.** Ask in one question what to call the Library, suggesting "Graveyard Killer". The Library is the folder `<vault>/<name>`. Done when you hold the name and `vault.py check "<vault>/<name>"` says it does not exist yet.

4. **Create the files.** Pick the names, in the Settings language, of the Entries folder, the Share here and Already read notes, the Attachments folder and the Cards view (in Italian: "Schede", "Condividi qui", "Già letti", "Allegati" and "Copertine"). Done when every file below exists.
   - `vault.py new-folder` for `<Library>`, `<Library>/<Entries>` and `<Library>/<Attachments>`.
   - `vault.py new-file "<Library>/<Share here>.md"` and `vault.py new-file "<Library>/<Already read>.md"`, with no input: each starts empty.
   - `vault.py new-file "<Library>/<name>.base"` with an input file holding `{"text": "..."}`, the [Base](#the-base) below.

5. **Write the Settings.** `vault.py create "<Library>" "Settings"` with an input file holding `{"body": "..."}`: every section of [library.md](library.md#the-settings) in order, as Markdown headings and tables, then the Files section of [library-obsidian.md](library-obsidian.md#layout). Done when `vault.py read "<Library>/Settings.md"` gives them back, and the note is named exactly `Settings`.
   - The Fields table also names Cover, with a name of one word, such as "Copertina", and names Tags `tags`.
   - The Limits start at 20 per day and 100 per week, the Instagram login with "Browser" empty and "Reads per run" at 3, and the Version is the newest heading in [upgrade.md](upgrade.md#steps).
   - The Schedule and "Ping by" stay empty until Setup's steps 3 and 9, and the Preferences table holds only its header row.

The Library link, for the pointer, is the Library folder's absolute path, as `vault.py check "<Library>"` prints it in `path`.

Tell the user to open the `.base` file in Obsidian: it shows the Entries as a table, and as cards with their covers. If the cards show no image, they open the cards view's settings and set *Image property* to Cover.

## The Base

Write it with the Library's names, as the Settings hold them. `<folder>` is the Entries folder's path from the vault's root, such as `Graveyard Killer/Schede`, and every name goes in double quotes:

```yaml
filters:
  and:
    - 'file.inFolder("<folder>")'
views:
  - type: table
    name: "<Entries>"
    order:
      - "<Title>"
      - "<Category>"
      - "<Status>"
      - "<Next action>"
      - "<Summary>"
      - tags
      - "<Platform>"
      - "<Captured>"
      - "<Processed>"
      - "<Note>"
      - "<Link>"
  - type: cards
    name: "<the Cards view's name>"
    image: note.<Cover>
    order:
      - "<Title>"
      - "<Category>"
      - "<Next action>"
```

A base file is YAML, and a property's name with no prefix is a note property ([Obsidian's help](https://obsidian.md/help/bases/syntax), checked 2026-11-16). The cards view's `image` key is not in Obsidian's help: forum users report `image: note.<property>` working, and the user can set it in the view's settings instead.

## Save from the phone

**Save through Obsidian.** This is the main way to save, with no tokens and with the computer off. Every share goes to the end of the Library's Share here note. The Worker reads the note, files each share, and moves its text to Already read. Then check on this computer, once the vault has synced, that the share arrived: `vault.py read "<Library>/<Share here>.md"`.

- **Android.** In Instagram, TikTok or YouTube, the user taps Share, picks Obsidian, chooses to add to an existing note, picks the Share here note, and saves. Obsidian adds the shared text on a new line at the end of the note: the link alone, or, for some Instagram reels, the caption and then the link. Tested on a Pixel. Obsidian's help does not document Android's share menu, so ask the user to tell you what their phone shows if it differs.
- **iPhone.** Obsidian's Share Sheet needs Obsidian 1.13 or later and iOS 18 or later. Once, in Obsidian, the user bookmarks the Share here note. Then, in the Share Sheet, they add a Location of the kind *Bookmarked note* that points to that note, adds to its end, and saves a shared link as *URL*, not *Full Text*. After that, they tap Share in Instagram, TikTok or YouTube, pick Obsidian, choose that Location and save. (Obsidian's help, checked 2026-11-16.) Untested: if Obsidian is missing from the share sheet, or nothing arrives, the user saves on this computer instead.

There is no second way through Claude on the phone: a Claude chat on the phone cannot reach the vault.
