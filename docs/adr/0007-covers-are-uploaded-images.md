# A Notion cover is an uploaded image in a Cover property

Issue #16 asked for a Library that looks like Raindrop.io: cards with covers. Two Notion limits stand in the way. The Notion connector can point a gallery's cover only at a property, never at the page cover. And a page cover takes only an external link, while Instagram's and TikTok's image links are signed and expire within days, so until 0.10.0 only YouTube Entries had a cover. A gallery of page covers would show empty cards for most posts, and the user would have to switch its card preview to the page cover by hand.

So a Notion Library has a **Cover** property, a Files & media property, and a gallery whose cover is that property. Its name sits in the Settings' Fields table, in a row for Notion only, as Drive's Captures, Transcript and On-screen text columns do, so a Files & media property the user made is never taken for it. The Worker uploads the image that `post.py read` already makes for each post: the post's own image, or the first frame of its video. The connector's file upload gives a short-lived URL that one multipart POST must reach, and the user has already allowed the skill's own scripts for the scheduled run ([schedule.md](../../plugin/skills/graveyard-killer/references/schedule.md), step 3), so `post.py upload` sends it. It sends only to `api.notion.com`, and only an image inside a work folder that `read` made, so no text in a post can make it send another file or send one elsewhere. Setup makes the views, and the 0.10.0 upgrade adds them and the property to an older Library ([ADR-0006](0006-libraries-upgrade-themselves.md)). Tested on 2026-11-16 on a copy of the eval Library.

## Considered Options

- **Views only, with page covers.** The issue's first proposal. Only YouTube cards would show an image, and the user would set *Layout → Card preview → Page cover* once by hand.
- **A published Notion template.** One fixed language and fixed Categories, while Setup builds each Library in the user's language with their Categories.
- **`create-attachment` with the image's link.** Notion fetched a fresh Instagram image link and a YouTube one. But it needs a link the post script does not keep, and nothing tells whether TikTok's image host lets Notion in. The local image exists for every post.
- **`curl` for the upload.** A new command for the user to allow, and one that would send any file anywhere.

## Consequences

- Entries finished before 0.10.0 have no image in the gallery. Those from YouTube keep their page cover.
- The table stays the first view, and agents read the Entries through it, since reading a view does not count against Notion's query allowance. A new view goes after the existing ones; if the user drags the gallery first, agents still find the table by its type.
- A Drive Library is unchanged: Sheets shows no covers ([ADR-0005](0005-a-library-in-more-than-one-app.md)).
- A cover that fails to upload is left out: the Entry is still finished.
