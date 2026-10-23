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
| Summary | text | One or two sentences in the Settings language |
| Next action | text | The one thing the user could do with it |
| Tags | multi-select | Free labels |
| Status | select | One Status (see below) |
| Captured | date | The date of the first Capture |
| Note | text | A message to the user about a problem with this Entry |

Each Category can add its own fields. They are named in the Settings and exist as extra properties in the Entries database.

The Entry's page body holds what does not fit a field: one dated line for each extra Capture of the same post, and the full caption when it is too long for the Caption field.

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
