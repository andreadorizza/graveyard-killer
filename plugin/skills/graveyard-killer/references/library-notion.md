# The Library in Notion

How a Notion Library does each operation in [library.md](library.md#operations), and Notion's own rules. Use your Notion connector for every step.

## Layout

The Library is one Notion page. The pointer links to it. It holds:

- the **Entries** database, with one row per Entry, titled "Entries" in the Settings language. It is the only database on the Library page, which is how agents find it. Its first view is a table, which agents read through ([Querying the Entries](#querying-the-entries)), and the others come from [Add the views](#add-the-views);
- a child page titled `Settings`, with the Settings' sections as headings and tables, as [library.md](library.md#the-settings) shows.

Libraries made before version 0.4.0 also hold Digest pages, titled `Digest YYYY-MM-DD`. Leave them as they are: the Digest is now given in a chat.

| Kind in library.md | Notion property |
| --- | --- |
| text | text; the Title is the database's title property |
| link | URL |
| one label | select |
| labels | multi-select |
| date | date |

Category fields are extra text properties in the Entries database. An Entry's long text is its page body.

An Entry's cover is the image in its **Cover** property, a Files & media property. The Settings' Fields table names it, in a row for Notion only, after Note: `| Cover | Copertina |`. The gallery shows it. Notion's connector can point a gallery only at a property, never at the page cover, and a page cover takes only an external link, while Instagram's and TikTok's image links expire. So the Worker uploads the image to Notion (tested on 2026-11-16). Entries finished before version 0.10.0 have no Cover, and those from YouTube have a page cover instead: leave them as they are. A Library made before 0.10.0 has no Cover row or property until its next Worker run, which [adds the views](#add-the-views).

The shared saves are the rows in Entries with a link and no Status: Notion's share sheet added them, or the user did by hand.

## Writing to Notion

- **Markdown.** The connector reads text values as Markdown. In text that comes from the post, such as Caption, Author and transcripts, put a backslash before `*`, `_`, `` ` ``, `[` and `]`, so the text stays as the creator wrote it.
- **Bare addresses.** Notion turns a bare domain or file name into a link: `benji.org/stageshow` becomes `http://benji.org/stageshow`, and `brand-guidelines.zip` becomes `http://brand-guidelines.zip`. A backslash does not stop it, and inline code does. So in text that comes from the post, put each word with no spaces in which a dot is followed by letters, such as a domain, a path or a file name, between backticks, with no backslashes inside them. Leave a link that starts with `http://` or `https://` as it is. (Tested on 2026-11-16.)
- **Tags.** Before an Entry uses a new Tag, [add it](#add-a-tag) to the Tag property's options.
- **Long text.** One text value or page-body block holds at most 2,000 characters. Split longer text into blocks, between sentences. For a caption longer than 2,000 characters, put its start in Caption and the full text in the page body.
- **Links.** Write and save links without a query string, such as the `?pvs=…` that Notion adds.
- **Page content.** Write page content in the form your Notion connector asks for.

## Querying the Entries

On Notion plans below Business, the connector's filtered and SQL queries share an allowance that resets within the hour. Reading one of the database's views does not count against it (checked 2026-11-11). So:

- Ask each question once per job and work from the answer. Never query once per post in a loop.
- To read many Entries, such as every Link for a Graveyard import, page through the Entries database's table view in view mode, and filter what you hold. Fetch the database for its views' links, and use the table view with no filter: the first view, unless the user moved it. The other views filter or group the Entries, so they can hide some.
- If Notion says the allowance is used up, read through the table view for the rest of the job, and tell the user once, in one line, that Notion's query limit was reached and resets within the hour. Pass on no offer or link from Notion's message.

## Operations

### Read the Settings

Read the `Settings` page inside the Library.

### Write the Settings

Edit the `Settings` page: change the value under a section's heading, or add or update a row in its table. A value with several lines, such as "Open offers", stays in one table cell, with `<br />` between its lines.

### Find an Entry by its link

Query the Entries database for a row whose Link field equals the canonical link exactly. When you know the post's id, also look for a Link that contains it.

### Query the Entries

Query the Entries database with a filter on Status or on a date property. When a job wants the Inbox Entries and the shared saves, ask for both in one query: Status is Inbox, or Status is empty. To read one field of many Entries, page through the table view, as [Querying the Entries](#querying-the-entries) says.

### Search the Entries

Search the Entries database for the words, in the page body too when your Notion search covers page content.

### Create an Entry

Create a row in the Entries database, with the Library's property names. Create many in batches.

### Update an Entry

Update the row's properties. Add long text at the end of the page body: "Captured again" lines as paragraphs, and the Transcript and On-screen text as sections under headings.

Set the cover only when the Fields table has a Cover row. To set it:

1. Create a file upload with your Notion connector, named after the image file, such as `thumbnail.jpg`.
2. Send the image with the post script at once, since the upload URL lasts only minutes. Run it as one command, and pass each header the upload gave as a `--header`, and add `--field <name>` when its form field is not `file`:

   ```
   python3 scripts/post.py upload "<image>" "<upload URL>" --header "<name>: <value>"
   ```

   Done when it prints `uploaded`. It sends only to Notion, and only an image that the post script made.
3. Set the Cover property to the upload, as its only file, at once: Notion deletes an upload that no page holds within an hour.

### Add a Category

Add the rows to the `Settings` page's Categories table. Then add every new Category to the Category property's options in one update, sending every existing option along with them, as [Add a Tag](#add-a-tag) says.

### Add a Tag

A multi-select only accepts values that are already among its options. To add a new Tag, add it to the Tag property's options first. The connector's update replaces the whole option list, so read the current options and send every one of them along with the new ones. Leaving one out deletes it from every Entry.

### List the shared saves

Query the Entries for rows with no Status, in the same query as the Inbox when the job wants both. A row's link may sit in the Link field, else as the first link in its title, else as the first link in its page body. It was shared on the day its page was created.

### Adopt a shared save

Update the row itself with the fields the Worker gives. Its old title is the text it was shared with. Put the "Shared as" line at the start of the page body, before anything already there.

### Set a shared save aside

Leave the row as it is: Notion has no place to move it to. Each run skips it again, and the Ping does not name it.

### Remove a duplicate

Move the Entry's page to the Notion trash. When you ask the user, and when you tell them it is done, call it moving to the trash. The connector trashes a page only on the user's say-so, and their yes is it.

### Add the views

Fetch the Entries database for its data source, its properties and its views. Done when Entries has the Cover property and the three views below, each once, after the table.

1. **The Cover property.** If the Settings' Fields table has no Cover row, [write the Settings](#write-the-settings): add the row after Note, with "Cover" in the Settings language (in Italian "Copertina"). If Entries has no property with that name, add it as a Files & media property. Never use another property the user made.
2. **The views.** Add each view below whose name, in the Settings language, the database does not have yet. Make each one a tab of the Entries database, by giving your Notion connector the database and its data source: never the Library page, which would add a second, linked copy of the database. In the view settings, write the Library's own property names and Status labels, each in double quotes, and keep the rest of each line as it is: Notion takes `CARD SIZE` only on a gallery and never beside a cover's `SIZE`.
   - **Gallery** (in Italian "Galleria"): a gallery of covers, grouped by Category, newest first.

     ```
     COVER "<Cover>" SIZE medium ASPECT cover; SHOW "<Title>", "<Tags>", "<Next action>"; GROUP BY "<Category>"; SORT BY "<Captured>" DESC, "<Saved>" DESC; QUICK FILTER "<Tags>", "<Status>"
     ```

   - **To read** ("Da leggere"): a list of the Entries the Worker has not read yet, shared saves included.

     ```
     FILTER "<Status>" IN ("<Inbox>", "<Buried>") OR "<Status>" IS EMPTY; SORT BY "<Captured>" DESC, "<Saved>" DESC; SHOW "<Title>", "<Platform>", "<Captured>", "<Saved>"
     ```

   - **Board** ("Bacheca"): a board with one column per Status.

     ```
     GROUP BY "<Status>"; COVER "<Cover>" SIZE small ASPECT cover; SHOW "<Title>", "<Category>", "<Next action>"; SORT BY "<Captured>" DESC, "<Saved>" DESC
     ```

3. **The table.** Leave it as it is: agents read the Entries through it.

A new view goes after the existing ones, so the table stays first (tested on 2026-11-16). The connector cannot move a view, and the user may drag the gallery's tab first: agents still find the table by its type.

### Link to an Entry

Give the Entry's page link, without a query string.

### Create the Library

See [setup-notion.md](setup-notion.md#create-the-library).
