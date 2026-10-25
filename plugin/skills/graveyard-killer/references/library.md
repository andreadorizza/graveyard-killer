# The Library contract

Every Graveyard Killer job reads and writes the Library the same way. This file is the single description of that shape.

## Layout

The **Library** is one Notion page. It holds two things:

- the **Entries** database, with one row per Entry. It is the only database on the Library page;
- a child page titled `Settings`.

The memory line points to the Library page.

## Names

The Library uses the user's own names for fields and Statuses, in their language. This file uses the canonical English names. The Settings map each canonical name to the Library's name. Write to the Library with the Library's names, and use them in replies too.

## Entry fields

| Field | Notion type | Holds |
| --- | --- | --- |
| Title | title | A short title in the Settings language |
| Link | URL | The canonical link, which is also the duplicate key |
| Platform | select | `Instagram`, `TikTok`, `YouTube` or `Other`. These labels are fixed |
| Author | text | The account that posted it |
| Caption | text | The post's own text, in its original language |
| Category | select | One Category from the Settings |
| Summary | text | In the Settings language: one or two sentences at Capture, two or three after the Worker |
| Next action | text | The one thing the user could do with it |
| Tags | multi-select | Free labels in the Settings language, at most 5 per Entry (see [Writing to Notion](#writing-to-notion)) |
| Status | select | One Status (see below) |
| Captured | date | The date of the first Capture |
| Note | text | Something about this Entry that needs attention, in the Settings language. It is empty when nothing does |

Each Category can add its own fields. They are named in the Settings and exist as extra properties in the Entries database.

The Entry's page body holds what does not fit a field:

- one dated line for each extra Capture of the same post;
- the full caption, when it is longer than 2,000 characters, Notion's limit for one text value;
- a Transcript section and an On-screen text section, written by the Worker. Their headings are "Transcript" and "On-screen text" in the Settings language. Use the same words on every Entry, so look at a Processed Entry for the words already in use (in Italian: "Trascrizione", "Testo a schermo").

## After Capture

The Worker knows more about a post than Capture did, and the user may have edited the Entry in between. So the Worker changes an Entry's fields by these rules:

| Field | The Worker |
| --- | --- |
| Title | Replaces it only if it is empty, a bare link, or a title that only names the platform and maybe the author, as Capture writes with no preview ("Post Instagram", "Post TikTok di ia_dori", "Post Instagram (solo link)") |
| Category | Replaces it only if it is the fallback Category |
| Summary, Next action | Rewrites them from the full post |
| Tags | Adds Tags and never removes one |
| Category fields | Fills only empty ones |
| Author, Caption | Sets them from the post |
| Link | Replaces a short link with the post's canonical link |

When a resolved link shows that two Entries hold the same post, the older Entry stays and gains a "Captured again on <date>" line. The newer one gets the Note "Duplicate of <link to the older Entry>" and goes to the Notion trash once the user agrees, since Notion's connector trashes a page only on the user's say-so.

## Writing to Notion

- **Tags.** A multi-select only accepts values that are already among its options. Reuse an existing Tag wherever one fits. To add a new Tag, add it to the Tag property's options first. The connector's update replaces the whole option list, so read the current options and send every one of them along with the new ones. Leaving one out deletes it from every Entry.
- **Markdown.** The connector reads text values as Markdown. In text that comes from the post, such as Caption, Author and transcripts, put a backslash before `*`, `_`, `` ` ``, `[` and `]`, so the text stays as the creator wrote it.
- **Long text.** One text value or page-body block holds at most 2,000 characters. Split longer text into blocks, between sentences.

## Statuses

| Status | Meaning |
| --- | --- |
| Inbox | Captured, not processed yet |
| Processed | The Worker finished it |
| Used | The user did its Next action |
| Dismissed | The user chose not to act on it |
| Unavailable | The post was deleted or made private before the Worker could download it |
| Buried | Imported from the Graveyard, waiting to be dug up |

## The Settings page

It has these sections, in this order. Here is an example for an Italian Library:

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
| Note | Nota |

## Statuses
| Status | Label in this Library |
| --- | --- |
| Inbox | In arrivo |
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
Domenica
```

Exactly one Category is the fallback. The Category options in the Entries database are the Category names from this table.

## Finding an Entry by its link

Query the Entries database for a row whose Link field equals the canonical link exactly.
