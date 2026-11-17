# The Graveyard

The **Graveyard** is what the user saved inside the platforms before Graveyard Killer: Instagram's saved posts and collections, TikTok's Favorites, and YouTube's playlists. It comes in through the platforms' official exports only. Graveyard Killer never unsaves or changes anything on the platforms.

Each post in the Graveyard becomes a **Buried** Entry: its link, the date it was saved, its author when known, and a Category. Each Worker run **digs up** a few of them, newest first, and finishes them like Inbox Entries. An **Amnesty** dismisses every Buried Entry saved before a date.

You have chosen one of the jobs below, found the Library and read its Settings (see SKILL.md). The Graveyard settings are in the Settings' Graveyard section.

## Import the Graveyard

The user asks Graveyard Killer to import their Graveyard. The import runs on the computer, where the export files are.

1. **Find the exports.** Ask where the export files are, unless the user said. They are zips or folders from:
   - Instagram: *Accounts Center → Your information and permissions → Export your information → Create export*, choosing **JSON** as the format (in Italian: *Centro gestione account → Le tue informazioni e autorizzazioni → Esporta le tue informazioni → Crea esportazione*);
   - TikTok: *Settings → Account → Download your data*, in **JSON** format;
   - YouTube: Google Takeout, with *YouTube and YouTube Music* selected.

   An export can take up to 30 days on Instagram, a few days on TikTok, and minutes to days on Google Takeout. Its download link then expires, after 4 days on Instagram and TikTok and about 7 on Takeout, so the user should download it soon. Done when you hold their paths.

2. **Read them.** Run `python3 scripts/graveyard.py "<path>" ["<path>" …]` from this skill's folder. It prints `posts` (newest first), `collections` and `warnings`. Done when you hold the result.
   - Tell the user about every warning. An HTML export must be requested again in JSON.

3. **Leave out what the Library already holds.** Read every Link in the Library once, with [Query the Entries](library.md#query-the-entries). A post is already there when a Link equals its link or contains its `id`. Done when you know the new posts.

4. **Match collections to Categories.** A post whose collection has the same name as a Category in the Settings, or an obvious match, gets that Category. Every other post gets the fallback Category. If some collections have no matching Category, list them and ask once whether to add them as Categories. On a yes, [add them all as Categories](library.md#add-a-category) in one go. Done when every new post has a Category.

5. **Tell the user what will be imported:** the count per platform and per Category. Ask once to go ahead. Done when they answer.

6. **[Create the Buried Entries](library.md#create-an-entry)**, in batches, with:
   - **Title:** "⏳ <Platform> post", or "⏳ <Platform> post by <author>", in the Settings language;
   - **Link, Platform, Author, Category:** from the post;
   - **Saved:** the post's `saved` date;
   - **Status:** the Library's label for Buried.

   Leave Captured and Note empty. Done when every new post has an Entry.

7. **Record the import.** Set "Last import" in the Settings' Graveyard section to today. Tell the user how many Entries were buried, and that each tidy-up brings back a few, within the daily and weekly limits in the Settings. Done when you have sent it.

## Dig up (part of each Worker run)

After the Inbox, the Worker run digs up Buried Entries with what is left of its budget ([worker.md](worker.md#steps), step 2):

1. **Pick them.** [Query the Entries](library.md#query-the-entries) whose Status is the Library's label for Buried. If "Dig up next" names a Category, take that Category's Entries first. Order them by Saved, newest first, with empty dates last, and put the Entries with a Note, which a past run could not read, after all the others. While login reads are off, leave out the Entries with a [gated Note](worker.md#gated-posts). Take as many as the budget leaves. Done when you hold the list.
2. **Finish each one exactly like an Inbox Entry** (see [worker.md](worker.md#each-entry)). A dug-up Entry ends Processed, Unavailable or merged, or stays Buried with its ⏳ and a Note when it could not be read. The pause before Instagram Entries, the stop at an Instagram challenge, [gated posts](worker.md#gated-posts) with their login reads and the [failed tries](worker.md#failed-tries) cover dug-up Entries too. Done when each one has its result.

When the user asks to dig up a Category next ("dig up my recipes next"), set "Dig up next" to that Category. When that Category has no Buried Entries left, clear it.

## Amnesty

The user asks for an Amnesty before a date, for example "Graveyard Killer amnesty for everything saved before 2023".

1. **Count them:** the Buried Entries whose Saved is before the date, and those with no Saved date. Done when you hold both counts.
2. **Ask once,** giving the count: dismiss these Entries? Say whether the ones with no Saved date are included; they are only when the user says so. Done when the user answers.
3. **On a yes,** set their Status to the Library's label for Dismissed. They stay in the Library. Tell the user how many were dismissed. Done when you have sent it.
