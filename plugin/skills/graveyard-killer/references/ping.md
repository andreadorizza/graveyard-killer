# The Ping, Proposals and Preferences

A **Ping** is a message a Worker run sends the user on its own. It comes only when the run has something for the user: a **Proposal**, an action on an Entry it just read, or something only the user can fix. Otherwise the run stays silent, except that after 7 days with no Ping it brings the Digest. The Ping is the run's final message, which the run's chat shows the user as it is. Its numbered offers are also saved in the Settings, so the user can answer in that chat or in any other Claude chat, on the phone too.

A **Preference** is the user's standing answer to one kind of Proposal: always, ask me, or never. The agent asks for it the first time that kind comes up, and records it in the Settings' Preferences table ([library.md](library.md#the-settings)).

You came here from step 7 of [worker.md](worker.md#steps), or, for [When the user answers](#when-the-user-answers), from SKILL.md. Write everything in the Settings language and in plain words.

## Gather it

Done when you hold the three parts below, each of them possibly empty.

1. **Proposals.** For each Entry this run finished (Processed, from the Inbox or dug up), look for one action that uses its content in the coming days, in the post's own terms. For example: an event or a deadline goes in the calendar, a recipe becomes a grocery list, a workout starts on Monday, a tool gets tried on the user's own project. Offer only what helps this week, and only an action you would carry out yourself, in the chat or with your own tools. Putting the Entry on a list, or reminding the user of its Next action, is not a Proposal. Most Entries get none.
   - Its **kind** is the Entry's Category and the action, such as "Ricette · lista della spesa".
   - Look up the kind in the Preferences, whose answers are in the Settings language, such as "chiedimi" for ask me. **Never**: drop it. **Always**: do it now, as [On a yes](#on-a-yes) says, and list it as done. **Ask me**: offer it, with no Preference question: the user has answered it. **No row for the kind**: offer it, with the Preference question ([Send it](#send-it), step 3).
   - "Always" never covers an action that reaches other people or costs money: offer that one every time.
   - Order them by urgency, a date soonest first, then by how much each would help this week. Keep at most 5 offers. The rest are dropped: each Proposal is offered once, by the run that reads its Entry.
2. **Fixes:** what only the user can solve.
   - Missing tools, with their install commands.
   - Instagram asked for a login, and how many Instagram Entries wait for the next run.
   - Entries this run left with a new Note, in the Inbox or Buried. An Entry that fails again for the reason its Note already gave is not news, even when its try count went up: it waits for the Digest's Needs you list, so that one dead link does not ping the user every day.
   - Entries this run found gated: those whose Note it set to "Instagram shows this post only to signed-in users" ([worker.md](worker.md#gated-posts)), with links. An Entry whose Note already said so, or that the run skipped, is not news, so this comes once per post.
     - While login reads are off, say that Graveyard Killer reads logged out, so it cannot read them and later runs skip them, and that the user can open them in Instagram. Add one offer, in the Settings language: "Read them with your Instagram login? Say yes here, or 'turn on Graveyard Killer's Instagram login' in any chat on your computer, to hear what that means." It carries no number.
     - While they are on, say that a later run reads them with the login.
   - A challenge to the user's account during a login read: login reads are off now. Ask the user to check the Instagram app for a warning, and to say "turn Graveyard Killer's Instagram login back on" when they want them again.
   - A browser problem during a login read: the `reason`, in plain words, and what to do. Say that login reads stopped for this run only, and that saying "turn on Graveyard Killer's Instagram login" in the Claude Desktop Code tab tests the browser again while the user watches, or picks another one. [login.md](login.md#browser-problems) lists the usual reasons.
   - Gated Entries that even the login could not see: those whose Note this run set to "Instagram hides this post even from your login", and those it made Unavailable for that reason. Say that the browser may not be signed in to Instagram, or that the post's limits leave out the account too.
   - Entries this run made Unavailable after 3 failed tries ([worker.md](worker.md#failed-tries)).
   - Duplicates this run found: Entries whose Note it set to "Duplicate of". Ask whether to [remove them](library.md#remove-a-duplicate).
   - Shared saves this run moved out of the way because they held no link, when [Set a shared save aside](library.md#set-a-shared-save-aside) moved them: one line naming them, such as "1 shared save held no link: <name>".
   - What bringing the Library up to date at the start of this run asked of the user, such as updating the schedule or the plugin ([upgrade.md](upgrade.md)).
3. **The Digest,** when "Last Ping" in the Settings' Pings section is 7 or more days ago, or empty, and the Library has Entries Processed since "Last Digest". Gather it as [digest.md](digest.md#give-the-digest) says.

## Send it

1. **With nothing gathered,** your whole final message is one line in the Settings language: what the run read, or that there was nothing to read. Add a second line only for a limit the user should know about, such as Notion's query limit, in your own words: never a link or an offer from the app's message. Write no list and no other line: an Entry that failed again for the reason its Note already gave waits for the Digest. Alert nobody. Done.
2. **Number and record the offers,** before you write the Ping, in one [Write the Settings](library.md#write-the-settings) of the Settings' Pings section. Done when it is saved:
   - "Open offers": keep its lines from the last 7 days and drop older ones. This Ping's first offer takes the next number after the highest one kept, or 1 when none is kept, and its other offers follow, the Digest's Library Proposals last. So no two open offers share a number. Add one line for each offer: `<number> · <today> · <kind> · <the offer in a few words> · <link to its Entry>`, with no link for a Library Proposal. With no line left, leave it empty.
   - "Last Ping" is today, and "Last Digest" too when the Ping brings the Digest.
3. **Write the Ping,** in this order. Give each offer the number its line got in step 2, in the list and everywhere else in the message: never number them again from 1. Only offers carry numbers: write the other parts as plain lines or bullets, never as a numbered list. Done when you hold its text:
   - one line on what the run did, such as "I read 4 new posts and brought back 2 old ones";
   - the Proposals, each one line with its number and a [link to its Entry](library.md#link-to-an-entry), so the user can answer "yes to 4". Add the Preference question to the first offer of a kind that has no row in the Preferences table yet, such as "For recipes: always, ask me each time, or never?" A kind whose row says "ask me" gets its offer without the question. List the "always" ones you did, as done;
   - the fixes, and a limit the user should know about, such as Notion's query limit, in one line of your own words: never a link or an offer from the app's message;
   - the Digest, when due, with its Library Proposals and their numbers. Leave out its duplicates offer, which the fixes cover.
4. **Alert the user** through "Ping by" in the Settings' Pings section. Skip the alert when the run was not scheduled: the user is already in this chat. Done when the alert is sent, or failed and you noted why.
   - **email:** an email to the user's own address through their Gmail connector. Its subject is "Graveyard Killer: " and the most urgent item, such as "Graveyard Killer: the Roma concert is on Saturday". Its body is the whole Ping, then one line saying that they can answer from any Claude chat, on the phone too, by naming Graveyard Killer, such as "Graveyard Killer, yes to 1". When your Library app's file says that the Library is reached only from this computer, say instead that they answer in the Claude Desktop Code tab on this computer.
   - **push:** your push notification tool, `PushNotification` in Claude Desktop, with one short line about the most urgent item. From a scheduled run it reaches only this computer, since scheduled runs have no Remote Control, and it skips the alert while the user is active there. With no push tool, as in OpenCode and Codex, show that line as a notification on this computer, with "Graveyard Killer" on the first line of stdin and your line on the second:

     ```
     python3 scripts/post.py notify <<'ALERT'
     Graveyard Killer
     <one short line about the most urgent item>
     ALERT
     ```

     In Codex, give the two lines as arguments instead ([codex.md](codex.md#run-the-scripts)). `"notified": false` means it did not show: put its reason in the Ping's fixes.
   - **none**, or empty: no alert. The chat waits in the app's list of runs.
5. **End the run with the Ping** as your final message. Done when it is written.

## When the user answers

The user answers in the run's chat, maybe hours later, or in any other Claude chat, on the phone too, by naming Graveyard Killer: "Graveyard Killer, yes to 4". In every chat, take the offers from "Open offers" in the Settings' Pings section, not from a Ping you can see: that list is the same on every device, so an offer is never done twice. Done when each answer is acted on.

- A number that is not in Open offers: say that this offer was already answered, or expired after 7 days, and do nothing.
- A yes to a Proposal: do it, as [On a yes](#on-a-yes) says. A no: nothing to do. Either way, remove its line from Open offers with [Write the Settings](library.md#write-the-settings).
- "What did Graveyard Killer offer?" or the like: list the Open offers, with their numbers and links.
- A Preference ("always", "never", "stop offering grocery lists"): [write the Settings](library.md#write-the-settings), adding or updating its row in the Preferences table, with the kind and the answer in the Settings language. An answer about an offer's number takes the kind from its line in Open offers. A user can also change a Preference from any chat: "Graveyard Killer, stop offering grocery lists".
- A yes to the duplicates: [remove them](library.md#remove-a-duplicate). On a no, they stay, and the Digest lists them under Needs you.
- A yes to reading gated posts with the Instagram login, or a request to turn Graveyard Killer's Instagram login on or off: follow [login.md](login.md).
- "I did it" about an Entry: set its Status to the Library's label for Used. "I don't want it": set Dismissed. It stays in the Library.
- "Try that one again" about an Entry still in the Inbox or Buried: read it now, as [worker.md](worker.md#each-entry) says, even when its Note says that Instagram shows it only to signed-in users. A failure here does not add a try. In a chat with no shell, such as a phone app, say that posts are read on the computer: ask there, in the Claude Desktop Code tab.

## On a yes

Give the result in this chat: a grocery list from the recipe's ingredients, the steps of a workout. Put something in another app only on the user's yes or an "always", and only in the user's own apps through their connectors: a dated event goes in their calendar with the Entry's Title, the date and a [link to the Entry](library.md#link-to-an-entry). With no tool for a step, say so and give the user what they need to do it themselves.
