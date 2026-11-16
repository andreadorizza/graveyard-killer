# The Library in Google Drive

How a Google Drive Library does each operation in [library.md](library.md#operations), and Drive's own rules. Use your Google Sheets connector for the Sheet, and your Google Drive connector for files and folders.

## Layout

The Library is one Google Sheet, in a Drive folder with the Library's name. The pointer links to the Sheet. The Sheet has two tabs:

- the **Entries** tab, titled "Entries" in the Settings language. Row 1 holds the Library's field names, and each row below it holds one Entry. If the user renamed it, it is the tab other than `Settings` whose row 1 holds the Library's name for Link;
- the `Settings` tab, with the sections of [library.md](library.md#the-settings) in their order. Each section is a heading row with the section's name in column A, then its value, or its table with the table's own header row, then a blank row. After library.md's sections comes a **Folders** section, for Drive only:

  | Folder | Name in this Library | Link |
  | --- | --- | --- |
  | Library | Graveyard Killer | `https://drive.google.com/drive/folders/<id>` |
  | Share here | Condividi qui | `https://drive.google.com/drive/folders/<id>` |
  | Already read | Già letti | `https://drive.google.com/drive/folders/<id>` |

The Library's folder holds the Sheet and the other two folders. The phone shares posts into "Share here", and the Worker moves each shared file to "Already read" once read.

| Kind in library.md | On Drive |
| --- | --- |
| text | a text cell |
| link | a text cell holding the link |
| one label | a text cell with a dropdown of the labels from the Settings |
| labels | one text cell, with the Tags separated by a comma and a space |
| date | a date cell, written as `=DATE(y,m,d)` and shown as `2026-11-12` |

Category fields are extra columns. An Entry's long text is three columns, each named in the Settings' Fields table: **Captures**, with one line per extra Capture and the "Shared as" line; **Transcript**; and **On-screen text**. They come last, after Caption, since these four can be long. Sheets shows no covers, so an Entry has none.

The shared saves are the files in "Share here".

**Rows and columns move.** The user sorts, filters and moves rows and columns, so a row or a column has no fixed place:

- Find each column by its header in row 1, in every job.
- Find an Entry's row by its Link, and write to it only as [Writing to a row](#writing-to-a-row) says.
- Two rows hold the same Link only when one of them is a duplicate, and the duplicate is the row whose Note says "Duplicate of".

## Reading the Sheet

One read returns at most about 40,000 characters, and a larger read is refused (measured 2026-11-13). So:

- Once per job, read the tabs' titles and ids with `get_spreadsheet`, asking only for the field `sheets.properties`.
- Read cells with `get_values`, one column per read, in pages of 200 rows: `'Entries'!C1:C200`, then `'Entries'!C201:C400`, and so on. The n-th value of the page that starts at row 201 is row 200 + n. A cell that is empty comes back empty, or is left out at the end of a page.
- Every Entry has a Link, so the Link column shows where the Entries end: read it until a page comes back empty, or until the tab's last row, its `rowCount` in `sheets.properties`. Read the other columns down to the last row with a Link.
- If a read is refused as too large, read the same range again in two halves.
- Read Caption, Captures, Transcript and On-screen text one cell at a time, only for the rows you need.
- Put the tab's name in quotes in every range, as above. R1C1 ranges work too, such as `'Entries'!R12C5`.

Dates read back as `2026-11-12`.

## Writing to Drive

- **Typed cells.** Write every cell with `update_spreadsheet`: `appendCells` for new rows and `updateCells` for existing cells, with `fields` set to `userEnteredValue`. Send text as `stringValue`, and the Sheet keeps it exactly as written: a caption that starts with `=`, `+39 333`, `3/4` or `007` stays text, with no escaping. These two are the only way to write cells: the connector's `update_values` and `append_values` read each value as if the user typed it, so they turn such text into formulas, dates and numbers.
- **Dates.** Send a date as `formulaValue`, such as `=DATE(2026,11,12)`, with `userEnteredFormat` `{"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}}`, and add `userEnteredFormat.numberFormat` to `fields`. Then the date reads back as `2026-11-12` on any row.
- **Empty cells.** An empty cell, `{}`, clears the cell it lands on. Send it only to clear a cell, such as the Note, and never as a filler between cells you change.
- **Many Entries at once.** To change many Entries, such as for an Amnesty, read the Link column right before, and send all their cells in one call, each as its own request, as below.
- **Labels.** A dropdown accepts any value written through the connector, so it never catches a wrong label.
- **Tags.** Reuse the Tags in the Tags column, spelled the same.
- **Long text.** A cell holds at most 50,000 characters, and a read returns about 40,000. So for a value longer than 30,000 characters, in practice only a long transcript, create a Google Doc in the Library's folder, from the Settings' Folders section, titled "<Entry title> · <column name>". Put the whole value in it, and the Doc's link in the cell.
- **Drive links.** Write the links of Drive's own files and folders without a query string or a `#` part, such as the `?usp=drivesdk` that Drive adds. A post's Link stays exactly as the link script gives it.

## Writing to a row

`updateCells` counts rows and columns from 0, while a row's number, as `get_values` and the Sheet show it, counts from 1 with the header as row 1. Mixing the two writes into the row above. So write to an Entry's row in these steps, every time:

1. **Its number.** Take the row number n where the Link column shows the Entry's Link, and the column number c of each field from row 1, both counting from 1.
2. **Check it.** Read the Link cell of row n alone, such as `'Entries'!B6`. If it no longer holds the Entry's Link, find the Entry again and start over.
3. **Write.** In one `update_spreadsheet` call, send one `updateCells` request per changed cell, each with a single cell, at `rowIndex` n − 1 and `columnIndex` c − 1. Row 6, column C is `rowIndex` 5, `columnIndex` 2.

## Operations

### Read the Settings

Read the `Settings` tab with `get_values`, as `'Settings'!A:D`.

### Write the Settings

Find the cell by reading the `Settings` tab. Write every Settings value as text, dates too, such as `2026-11-10`.

- **A value:** `updateCells` on its cell. A value with several lines, such as "Open offers", stays in one cell, with a line break (`\n`) between its lines.
- **A new row in a table,** such as a Preference: in one `update_spreadsheet` call, insert one row just below the table's last row, then write into it. When `get_values` shows that last row as row r, that is `insertDimension` with `startIndex` r, `endIndex` r + 1 and `inheritFromBefore`, then `updateCells` at `rowIndex` r.
- **A missing section:** insert its heading row, its value or table, and a blank row, where library.md's order puts it.

### Find an Entry by its link

Read the Link column, in pages, and find the cell that equals the canonical link exactly. When you know the post's id, also look for a Link that contains it. That cell's row is the Entry's row, until something moves it.

### Query the Entries

Read the columns the question needs, in pages, and filter what you hold: Status for the Inbox, a date column for a range, the Link column for every Link. Read each column once per job.

### Search the Entries

Read Title, Summary, Next action, Tags and Author, in pages, and look for the words. Then read Caption, Transcript and On-screen text one cell at a time, only for the rows whose other columns come close, such as a fitting Category or Tag.

### Create an Entry

Read the header row, then `appendCells` on the Entries tab: one row per Entry, with one cell per column in the header's order, holding the field's value or `{}`. Send many Entries in batches of up to 100 rows. A blank row between Entries does no harm.

### Update an Entry

Write the changed cells as [Writing to a row](#writing-to-a-row) says. To add to the long text, read that cell first and write its old text with the new text after it, on a new line:

- a "Captured again" line goes at the end of Captures;
- the transcript goes in Transcript, one paragraph per block, with a blank line between paragraphs;
- the on-screen text goes in On-screen text.

The cover has no place on Drive: skip it.

### Add a Category

Do each step in one `update_spreadsheet` call, and read the header row again before the next step, since an inserted column moves the columns after it.

1. In the `Settings` tab, add a row at the end of the Categories table for each new Category, as [Write the Settings](#write-the-settings) says.
2. For each new Category field, `insertDimension` a column just before Caption, and write the field's name in its row 1.
3. Reset the Category column's dropdown: `setDataValidation` on the column from row 2 down, with a `ONE_OF_LIST` rule that holds every Category in the Settings, and `strict` and `showCustomUi` both true.

### Add a Tag

Nothing to add: a Tag is free text. Reuse the spelling already in the Tags column.

### List the shared saves

Take the "Share here" folder's id from its link in the Settings' Folders section, and list the files in it with the Drive connector's `search_files`: query `parentId = '<id>' and trashed = false`, with `excludeContentSnippets` true. Pass each answer's `nextPageToken` to get the next page, until a page comes back empty, and count a file that comes back twice once. For each file:

- its link may sit in its text, which `read_file_content` reads, else in its name;
- it was shared on the day of its `createdTime`, in local time;
- the text it was shared with is its text, and its name too when the name is more than the start of the link, as when YouTube names the file after the video.

### Adopt a shared save

[Create an Entry](#create-an-entry) with the fields the Worker gives, with the "Shared as" line in Captures. First [find an Entry by](#find-an-entry-by-its-link) the Worker's Link: if one exists, create the new row with its Note already set to "Duplicate of <[that Entry](#link-to-an-entry)>", so that the two rows can be told apart. Then move the file to "Already read": `update_file` with `parentId` set to that folder's id, from the Settings' Folders section.

### Set a shared save aside

Move the file to "Already read", as for an adopted file. The Ping names it.

### Remove a duplicate

Read the Link and Note cells of its row n to check it is the duplicate, then delete the row: `deleteDimension` with the dimension `ROWS`, `startIndex` n − 1 and `endIndex` n. Delete one row per call, and find the next duplicate again before deleting it, since a deleted row moves every row below it up. When you ask the user, and when you tell them it is done, say that the row is deleted, and that only the Sheet's version history can bring it back.

### Link to an Entry

A Sheet has no link to one row that survives a sort. So name the Entry by its Title and give its Link, every time, such as «Pasta alla Norma» (https://it.wikipedia.org/wiki/Pasta_alla_Norma).

### Create the Library

See [setup-google-drive.md](setup-google-drive.md#create-the-library).
