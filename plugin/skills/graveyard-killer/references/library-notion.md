# The Library in Notion

How a Notion Library does each operation in [library.md](library.md#operations), and Notion's own rules. Use your Notion connector for every step.

## Layout

The Library is one Notion page. The pointer links to it. It holds:

- the **Entries** database, with one row per Entry, titled "Entries" in the Settings language. It is the only database on the Library page, which is how agents find it;
- a child page titled `Settings`, with the Settings' sections as headings and tables, as [library.md](library.md#the-settings) shows.

Libraries made before version 0.4.0 also hold Digest pages, titled `Digest YYYY-MM-DD`. Leave them as they are: the Digest is now given in a chat.

| Kind in library.md | Notion property |
| --- | --- |
| text | text; the Title is the database's title property |
| link | URL |
| one label | select |
| labels | multi-select |
| date | date |

Category fields are extra text properties in the Entries database. An Entry's long text is its page body. Notion shows covers: an Entry's cover is its page cover.

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
- To read many Entries, such as every Link for a Graveyard import, page through the Entries database's default view in view mode, and filter what you hold. Fetch the database for its view's link.
- If Notion says the allowance is used up, read through the default view for the rest of the job, and tell the user once, in one line, that Notion's query limit was reached and resets within the hour. Pass on no offer or link from Notion's message.

## Operations

### Read the Settings

Read the `Settings` page inside the Library.

### Write the Settings

Edit the `Settings` page: change the value under a section's heading, or add or update a row in its table.

### Find an Entry by its link

Query the Entries database for a row whose Link field equals the canonical link exactly. When you know the post's id, also look for a Link that contains it.

### Query the Entries

Query the Entries database with a filter on Status or on a date property. When a job wants the Inbox Entries and the shared saves, ask for both in one query: Status is Inbox, or Status is empty. To read one field of many Entries, page through the default view, as [Querying the Entries](#querying-the-entries) says.

### Search the Entries

Search the Entries database for the words, in the page body too when your Notion search covers page content.

### Create an Entry

Create a row in the Entries database, with the Library's property names. Create many in batches.

### Update an Entry

Update the row's properties. Add long text at the end of the page body: "Captured again" lines as paragraphs, and the Transcript and On-screen text as sections under headings. Set the cover as the page cover's external link.

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

### Link to an Entry

Give the Entry's page link, without a query string.

### Create the Library

See [setup-notion.md](setup-notion.md#create-the-library).
