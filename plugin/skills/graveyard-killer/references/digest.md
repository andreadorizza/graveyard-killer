# Digest

A **Digest** is a short weekly review of the Library, written for the user. It is a child page of the Library, titled `Digest YYYY-MM-DD` with the day it was written, so the user can read it on the phone and every agent can find the newest one. Each Worker run writes one as its last step. The user can also ask for a Digest in any chat.

You have chosen this job, found the Library and read its Settings (see SKILL.md).

## Write the Digest

This is the last step of every Worker run. A "Show a Digest" request can also lead here.

1. **Find the period.** It runs from the date of the newest Digest page in the Library (its title says it), or from 7 days ago when there is none, to today. Both days are in the period. Done when you hold both dates.

2. **Gather the lists.** Each Entry goes in one list only: an Entry in Needs you appears nowhere else. Done when you hold all five:
   - **Coming up:** Entries whose Status is Processed and whose Next action names a calendar date (a day, or a day and a month) from today to 14 days after today. A date without a year is the next one to come. Words such as "this weekend" are not a date;
   - **New:** Entries whose Processed date is in the period and whose Status is not Dismissed, grouped by Category, leaving out the Entries in Coming up or Dug up and those the newest Digest already lists;
   - **Dug up:** Entries whose Processed date is in the period and that came from the Graveyard (they have a Saved date), leaving out the Entries in Coming up and those the newest Digest already lists;
   - **Needs you:** every Entry in the Inbox, every Buried Entry with a Note, and every Entry whose Note says it is a duplicate;
   - **Re-import:** a reminder to export the Graveyard again and import it, only when "Last import" in the Settings' Graveyard section is more than 3 months ago, or empty while Buried Entries exist.

   If all five are empty, write no page. Say there is nothing new this week, and stop.

3. **Create the page** under the Library page, titled `Digest <today as YYYY-MM-DD>`. Done when the page exists. Its layout:
   - one level-2 heading for each list that is not empty, in the order above, in the Settings language. In Italian they are "In programma", "Nuovi", "Ripescati", "Ha bisogno di te" and "Da reimportare". In another language, translate them once and reuse the previous Digest's words;
   - under New, one level-3 heading per Category, in the Settings' order;
   - one line per Entry: a mention of the Entry's page, then " — " and its Next action without a closing full stop. Under Needs you, put its Note instead. In the other lists, when the Next action names no calendar date, end the line with the day the post reached the user, from Saved (saved on the platform) or else Captured (sent to Graveyard Killer), such as " (saved 14 June 2023)" in the Settings language, in Italian " (salvato il 14 giugno 2023)".

4. **Report it.** In a Worker run, add the Digest's link to the run's closing summary. Done when the link is in it.

## Show a Digest

The user asks to see their Digest, in any chat, for example "show my Graveyard Killer digest".

1. **Find the newest Digest page** by its title. If it is more than 7 days old, or there is none, write one first ([Write the Digest](#write-the-digest), steps 1 to 3). Done when you hold its content, or know there is nothing new.
2. **Show it** in the Settings language, with the link to the Digest page: one line per list, giving its count and naming each Entry in Coming up. Done when you have sent it.
3. **Offer Proposals.** A **Proposal** is an action you offer while showing the Digest. Nothing happens unless the user accepts it. Offer at most 3, one line each, the most useful this week first: an Entry the user can use now beats tidying the Library. Done when you have offered them.

## Proposals

Act on a Proposal only after the user says yes. A Proposal may draw on any Entry in the Library, not only this Digest's. A relative time in a Next action, such as "this weekend", means the next one to come. Each one, and what to do on a yes:

- **Use an Entry now,** when its content fits the coming days: an event or a deadline in Coming up, a recipe for the weekend, a workout to start on Monday. Offer the step that uses it, in the post's own terms ("The Roma concert is on 14 November: shall I add it to your calendar?"). On a yes, do it with your own tools: for a dated event, create it in the user's calendar with the Entry's Title, the date and the Entry's link; for a recipe, write the shopping list from its ingredients. If you have no tool for the step, say so and give the user what they need to do it themselves.
- **Mark an Entry Used,** when the user says they did its Next action: set its Status to the Library's label for Used.
- **Dismiss an Entry** the user no longer wants: set its Status to the Library's label for Dismissed. It stays in the Library.
- **Move an Entry to another Category,** when it sits in the fallback Category and another fits: set its Category. When three or more Entries in the fallback Category share a theme that no Category covers, offer a new Category named after it, for example after the Tags they share. On a yes, add it to the Settings' Categories table and to the Category property's options, as [library.md](library.md#writing-to-notion) explains for options. Then move the Entries.
- **Move the duplicates to the trash:** the Entries whose Note says they are duplicates. Your Notion connector trashes a page only on the user's say-so, and this yes is it.
- **Dig up a Category next,** or **an Amnesty** when many Buried Entries are older than a year: follow [graveyard.md](graveyard.md).
