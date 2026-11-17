# Setup in Google Drive

The Google Drive steps of [setup.md](setup.md). Read [library-google-drive.md](library-google-drive.md) first.

## Create the Library

1. **Check the connectors.** A Drive Library needs two connectors: Google Drive for the folders and Google Sheets for the Sheet. Check that Google Drive works, for example by searching the user's Drive for a folder, and that you have the Google Sheets tools `get_spreadsheet`, `get_values` and `update_spreadsheet`. If a connector is missing, ask the user to connect it in *Customize → Connectors*, and wait. Done when both are there.

2. **Name it.** Ask in one question what to call the Library, suggesting "Graveyard Killer". Done when you hold the name.

3. **Create the files** with the Drive connector's `create_file`, in this order. Done when all four exist.
   - A folder with that name in the user's My Drive (`contentMimeType` `application/vnd.google-apps.folder`).
   - Inside it, the Sheet with the same name (`contentMimeType` `application/vnd.google-apps.spreadsheet`, no content).
   - Inside it, the two folders "Share here" and "Already read", named in the Settings language (in Italian, "Condividi qui" and "Già letti").

4. **Lay out the Sheet** in one `update_spreadsheet` call, with the first tab's id from `get_spreadsheet`. Done when the call succeeds.
   - Rename the first tab to "Entries" in the Settings language, freeze its row 1, and set the whole tab to clip text (`wrapStrategy` `CLIP`), so each Entry stays one line high.
   - Add a tab titled `Settings`.
   - In row 1 of the Entries tab, in bold, write the Library's field names: every field in library.md's order except Caption, then each Category's own fields, then Caption, Captures, Transcript and On-screen text. A new Sheet has 26 columns: add more first with `appendDimension` if the header needs them.
   - Format the Captured, Saved and Processed columns, from row 2 down, as dates shown `yyyy-mm-dd`: `repeatCell` with `numberFormat` `{"type": "DATE", "pattern": "yyyy-mm-dd"}`.
   - Add the dropdowns, from row 2 down: `setDataValidation` with a `ONE_OF_LIST` rule, `strict` and `showCustomUi` both true. Platform holds `Instagram`, `TikTok`, `YouTube` and `Other`; Status the six Status labels; Category the Category names.

5. **Write the Settings** in the `Settings` tab with `updateCells`, laid out as library-google-drive.md's [Layout](library-google-drive.md#layout) says: every section of library.md in order, then Folders with the three folders' names and links. Done when you can read the Settings back with `get_values`.
   - The Fields table also names Captures, Transcript and On-screen text.
   - The Limits start at 20 per day and 100 per week, the Instagram login with "Browser" empty and "Reads per run" at 3, and the Version is the newest heading in [upgrade.md](upgrade.md#steps).
   - The Schedule and "Ping by" stay empty until Setup's steps 3 and 9, and the Preferences table holds only its header row.

The Library link, for the pointer, is the Sheet's link without a query string or a `#` part: `https://docs.google.com/spreadsheets/d/<id>/edit`.

## Save from the phone

**Save through Drive.** This is the main way to save, with no tokens and with the computer off. In Instagram, TikTok or YouTube, the user taps Share, picks Drive, chooses the Library's "Share here" folder as the destination, and saves. Drive saves a small file holding the post's link, which the Worker reads and then moves to "Already read". Then check that the file arrived in "Share here". This was tested on Android. On an iPhone it is untested: if Drive is missing from the share sheet, or no file arrives, use the next route.
