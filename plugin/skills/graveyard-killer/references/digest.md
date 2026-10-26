# Digest

A **Digest** is a short weekly review of the Library, written for the user. It is a child page of the Library, titled `Digest YYYY-MM-DD` with the day it was written, so the user can read it on the phone and every agent can find the newest one. Each Worker run writes one as its last step. The user can also ask for a Digest in any chat.

You have chosen this job, found the Library and read its Settings (see SKILL.md).

## Write the Digest

This is the last step of every Worker run. A "Show a Digest" request can also lead here.

1. **Find the period.** It starts at the date of the newest Digest page in the Library (its title says it), or 7 days ago when there is none. It ends today. Done when you hold both dates.

2. **Gather the lists.** Done when you hold all five:
   - **Coming up:** Entries whose Status is Processed and whose Next action names a date from today to 14 days after today. A date without a year is the next one to come;
   - **New:** Entries whose Processed date is in the period and whose Status is not Dismissed, grouped by Category;
   - **Dug up:** among them, the Entries that came from the Graveyard (they have a Saved date);
   - **Needs you:** every Entry in the Inbox, every Buried Entry with a Note, and every Entry whose Note says it is a duplicate;
   - **Re-import:** a reminder to export the Graveyard again and import it, only when "Last import" in the Settings' Graveyard section is more than 3 months ago, or empty while Buried Entries exist.

   If all five are empty, write no page. Say there is nothing new this week, and stop.

3. **Create the page** under the Library page, titled `Digest <today as YYYY-MM-DD>`. Done when the page exists. Its layout:
   - one level-2 heading for each list that is not empty, in the order above. Translate "Coming up", "New", "Dug up", "Needs you" and "Re-import" into the Settings language once, and use the same words as the previous Digest;
   - under New, one level-3 heading per Category;
   - one line per Entry: a mention of the Entry's page, then " — " and its Next action. Under Needs you, put its Note instead.

4. **Report it.** In a Worker run, add the Digest's link to the run's closing summary. Done when the link is in it.

## Show a Digest

The user asks to see their Digest, in any chat, for example "show my Graveyard Killer digest".

1. **Find the newest Digest page** by its title. If there is none from the last 7 days, write one first ([Write the Digest](#write-the-digest), steps 1 to 3). Done when you hold its content, or know there is nothing new.
2. **Show it** in a few lines, in the Settings language, with the link to the page. Done when you have sent it.
3. **Offer Proposals.** A **Proposal** is an action you offer while showing the Digest. Nothing happens unless the user accepts it. Offer at most 3, one line each, the most useful this week first: an Entry the user can use now beats tidying the Library. Done when you have offered them.

## Proposals

Act on a Proposal only after the user says yes. Each one, and what to do on a yes:

- **Use an Entry now,** when its content fits the coming days: an event or a deadline in Coming up, a recipe for the weekend, a workout to start on Monday. Offer the step that uses it, in the post's own terms ("The Roma concert is on 14 November: shall I add it to your calendar?"). On a yes, do it with your own tools: for a dated event, create it in the user's calendar with the Entry's Title, the date and the Entry's link. If you have no tool for the step, say so and give the user what they need to do it themselves.
- **Mark an Entry Used,** when the user says they did its Next action: set its Status to the Library's label for Used.
- **Dismiss an Entry** the user no longer wants: set its Status to the Library's label for Dismissed. It stays in the Library.
- **Move an Entry to another Category,** when it sits in the fallback Category and another fits: set its Category. When no Category fits a group of Entries, offer a new Category. On a yes, add it to the Settings' Categories table and to the Category property's options, as [library.md](library.md#writing-to-notion) explains for options. Then move the Entries.
- **Move the duplicates to the trash:** the Entries whose Note says they are duplicates. Your Notion connector trashes a page only on the user's say-so, and this yes is it.
- **Dig up a Category next,** or **an Amnesty** when many Buried Entries are older than a year: follow [graveyard.md](graveyard.md).
