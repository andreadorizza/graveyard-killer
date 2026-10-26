# The Graveyard

The **Graveyard** is what the user saved inside the platforms before Graveyard Killer: Instagram's saved posts and collections, TikTok's Favorites, and YouTube's playlists. It comes in through the platforms' official exports only. Graveyard Killer never unsaves or changes anything on the platforms.

Each post in the Graveyard becomes a **Buried** Entry: its link, the date it was saved, its author when known, and a Category. Each Worker run **digs up** a few of them, newest first, and finishes them like Inbox Entries. An **Amnesty** dismisses every Buried Entry saved before a date.

You have chosen one of the jobs below, found the Library and read its Settings (see SKILL.md). The Graveyard settings are in the Settings' Graveyard section.

## Import the Graveyard

The user asks Graveyard Killer to import their Graveyard. The import runs on the computer, where the export files are.

1. **Find the exports.** Ask where the export files are, unless the user said. They are zips or folders from:
   - Instagram: *Accounts Center → Your information and permissions → Download your information*, in **JSON** format;
   - TikTok: *Settings → Account → Download your data*, in **JSON** format;
   - YouTube: Google Takeout, with *YouTube and YouTube Music* selected.

   Done when you hold their paths.

2. **Read them.** Run `python3 scripts/graveyard.py "<path>" ["<path>" …]` from this skill's folder. It prints `posts` (newest first), `collections` and `warnings`. Done when you hold the result.
   - Tell the user about every warning. An HTML export must be requested again in JSON.

3. **Leave out what the Library already holds.** For each post, look for an Entry with the same Link, or with a Link that contains the post's `id` (see [library.md](library.md#finding-an-entry-by-its-link)). Done when you know the new posts.

4. **Match collections to Categories.** A post whose collection has the same name as a Category in the Settings, or an obvious match, gets that Category. Every other post gets the fallback Category. If some collections have no matching Category, list them and ask once whether to add them as Categories. On a yes, add them to the Settings' Categories table and to the Category property's options, as [library.md](library.md#writing-to-notion) explains for options. Done when every new post has a Category.

5. **Tell the user what will be imported:** the count per platform and per Category. Ask once to go ahead. Done when they answer.

6. **Create the Buried Entries**, in batches, with:
   - **Title:** "<Platform> post", or "<Platform> post by <author>", in the Settings language;
   - **Link, Platform, Author, Category:** from the post;
   - **Saved:** the post's `saved` date;
   - **Status:** the Library's label for Buried.

   Leave Captured and Note empty. Done when every new post has an Entry.

7. **Record the import.** Set "Last import" in the Settings' Graveyard section to today. Tell the user how many Entries were buried, and that each weekly run digs up the number in "Dig up per run". Done when you have sent it.

## Dig up (part of each Worker run)

After the Inbox, the Worker run digs up Buried Entries:

1. **Pick them.** Query the Entries whose Status is the Library's label for Buried. If "Dig up next" names a Category, take that Category's Entries first. Order them by Saved, newest first, with empty dates last. Take as many as "Dig up per run" says (10 if empty). Done when you hold the list.
2. **Finish each one exactly like an Inbox Entry** (see [worker.md](worker.md#each-entry)). A dug-up Entry ends Processed, Unavailable or merged, or stays Buried with a Note when it could not be read. The pause before Instagram Entries and the stop at an Instagram challenge cover dug-up Entries too.
3. **Note them for the Digest:** which Entries this run dug up. Done when the list is ready for the Digest.

When the user asks to dig up a Category next ("dig up my recipes next"), set "Dig up next" to that Category. When that Category has no Buried Entries left, clear it.

## Amnesty

The user asks for an Amnesty before a date, for example "Graveyard Killer amnesty for everything saved before 2023".

1. **Count them:** the Buried Entries whose Saved is before the date, and those with no Saved date. Done when you hold both counts.
2. **Ask once,** giving the count: dismiss these Entries? Say whether the ones with no Saved date are included; they are only when the user says so. Done when the user answers.
3. **On a yes,** set their Status to the Library's label for Dismissed. They stay in the Library. Tell the user how many were dismissed. Done when you have sent it.
