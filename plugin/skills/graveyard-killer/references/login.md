# Login reads

A Worker run reads every post logged out. Instagram shows some posts only to signed-in users, such as the posts of an account with an age limit, so a logged-out read cannot see them: they wait with a gated Note ([worker.md](worker.md#gated-posts)). A **login read** reads such a post a second time with the user's own Instagram login, which yt-dlp and gallery-dl take from a browser on this computer where the user is signed in. Login reads are off until the user turns them on here.

You came here from SKILL.md, when the user asked to turn Graveyard Killer's Instagram login on or off, or from [ping.md](ping.md#when-the-user-answers), on a yes to a Ping's offer to read gated posts with it. You found the Library and read its Settings. Talk in the Settings language, in plain words.

- **On a phone,** or in any chat with no shell: say that login reads are turned on and off on the computer that runs the Worker, in the Claude Desktop Code tab, and stop.
- **A scheduled run** never does this. It only empties Browser at a challenge ([worker.md](worker.md#gated-posts)).

Run the scripts with `python3` from the `graveyard-killer` skill's folder.

## Turn them on

1. **Say the risk once,** and ask whether to go on. Done when the user answers. On a no, change nothing and stop.
   - Login reads use the user's real Instagram account.
   - Instagram's Terms of Use forbid "collecting information in an automated way without our express permission", even while logged in: https://help.instagram.com/581066165581870.
   - Instagram has flagged sessions after a few dozen downloads, and no safe rate is known.
   - So the Worker still reads every post logged out first, and uses the login only for the posts Instagram hides: at most 3 a run, with a pause of 30 to 90 seconds before each. At the first challenge to the account it stops reading Instagram and turns login reads off.
   - A second Instagram account, signed in to a browser profile of its own, keeps the main account out of it, provided that account also passes the creator's limits, such as an age limit.
   - Graveyard Killer saves no copy of the login: the tools read the browser's cookies at each login read, and the copy they make for it is deleted with the read's work folder.

2. **Ask which browser,** recommending one as [Browsers](#browsers) says for this computer's system. Done when you hold a Browser value that passes the check below.
   - Offer only the browsers the table offers. Firefox is the recommendation on macOS and Windows.
   - When the browser has more than one profile, ask which one is signed in to Instagram, and use its folder name, not the name the browser shows. Firefox shows it in `about:profiles` as the last folder of the profile's Root Directory, such as `a1b2c3d4.default-release`. Chrome and Edge show it in `chrome://version` and `edge://version` as the last folder of the Profile Path, such as `Default` or `Profile 1`. With a single profile, the browser name alone is enough.
   - The value is the browser name in lowercase (`brave`, `chrome`, `chromium`, `edge`, `firefox`, `opera`, `safari` or `vivaldi`), alone or followed by a colon and the profile's folder name, such as `firefox` or `chrome:Profile 1`. The folder name must be at most 64 characters, made only of letters, digits, spaces, dots, dashes and underscores, and start with a letter or digit. A profile that does not fit cannot be used: suggest another profile or browser.

3. **Say what this computer will ask,** from the same table, before the test. Done when you have told the user.

4. **Write the Settings,** in the Instagram login section, with [Write the Settings](library.md#write-the-settings): Browser, and "Reads per run" only if the user wants another number, a whole number from 1 up. Done when the Settings hold it.

5. **Test while the user watches,** so that any prompt comes up now and not in a scheduled run nobody watches. [Query the Entries](library.md#query-the-entries) in the Inbox or Buried with a [gated Note](worker.md#gated-posts) and a Link to an Instagram post's own page, with `/p/`, `/reel/` or `/tv/` in its path, and take the oldest by Captured, or by Saved for a Buried one. Make at most 2 test reads: the other gated Entries wait for scheduled runs. Done when the user knows whether login reads work.
   - **With no gated Entry:** say that the next scheduled run that meets a gated post reads it with the login, and that any prompt may first come up then. For a Chromium browser on macOS, add that a Keychain dialog nobody answers stops that read after 20 minutes, and the Ping then asks for a test. Stop here.
   - Say that the computer may show its prompt now, and which button to choose. Then read the Entry with the login, with the Browser value in single quotes and the Link in a quoted heredoc:

     ```
     python3 scripts/post.py read --login '<Browser>' <<'LINK'
     <the Entry's Link>
     LINK
     ```

   - Act on its `status`, then clean up its `work` as [worker.md](worker.md#instagram-tiktok-and-youtube) says in step 4:
     - `ok`: merge a duplicate or finish the Entry, as [worker.md](worker.md#instagram-tiktok-and-youtube) says in step 3. Say that scheduled runs will now read gated posts with the login, up to "Reads per run" each.
     - `unavailable`: set the Entry Unavailable as worker.md says. If this was the first test read, test again with the next gated Entry, after `python3 scripts/post.py pause --login`. After the second, say that the test could not tell, and that scheduled runs will try.
     - `login_only`: the browser profile showed Instagram no login, or the account cannot see the post either. Leave the Entry as it is. Ask the user to open Instagram in that browser profile and check that they are signed in and see the post, then offer to test again, to pick another browser, or to turn login reads off.
     - `needs_login`: Instagram challenged the account. Write Browser empty, which turns login reads off, and ask the user to check the Instagram app for a warning.
     - `error`: explain the `reason` with [Browser problems](#browser-problems), then offer another browser or turning login reads off.

## Turn them off

Write Browser empty in the Settings' Instagram login section with [Write the Settings](library.md#write-the-settings). Tell the user that login reads are off, that gated posts wait with their Note and later runs skip them, and that they can turn login reads on again by asking. Done when the Settings hold it.

## Browsers

Firefox is the only browser that works on both systems, and it needs no prompt or extra permission. Checked against the tools' own documents and issues on 2026-11-16, and with a real login read through Chrome on macOS that day. Before each release that changes login reads, a manual login read with each browser below keeps this table true.

| System | Browser | Works | What the computer asks | Offer it |
| --- | --- | --- | --- | --- |
| macOS | Firefox | Yes | Nothing: the tools read its cookie file directly | Recommended |
| macOS | Chrome, Edge, Brave, Opera, Vivaldi, Chromium | Yes | A Keychain dialog asking for "\<Browser\> Safe Storage", the key that unlocks the browser's cookies, with Deny, Allow Once and Always Allow. Scheduled runs need Always Allow, chosen during the test | Yes, after saying that Always Allow lets the `security` tool, which the download tools call, read that key from then on without asking, so any program on this Mac that runs `security` can read it too |
| macOS | Safari | Only with Full Disk Access for the app that runs the Worker | Full Disk Access, set by hand in System Settings, which lets that app read all files, other apps' data included | No: too broad. Mention it only if the user has no other browser signed in to Instagram |
| Windows | Firefox | Yes | Nothing | Recommended |
| Windows | Chrome | No | Chrome 127 and later lock its cookies to Chrome itself (App-Bound Encryption), and yt-dlp cannot read them. Chrome also locks its cookie file while it runs | No: suggest Firefox |
| Windows | Edge | Probably not | Edge locks its cookies to Edge by default, like Chrome | No, until a manual check says it works |
| Windows | Brave, Opera, Vivaldi | Unknown | Unknown | No, until a manual check says it works |

On Linux, login reads are not supported: say so, and leave them off.

## Browser problems

A login read's `error` names the problem in its `reason`. The usual ones:

| The reason says | It means | What to do |
| --- | --- | --- |
| "could not find … cookies database", or "Unable to find … cookies database" | That browser or profile has no cookies on this computer | Check the browser and the profile's folder name, or pick another browser |
| "find-generic-password failed" | On macOS, the Keychain dialog was denied, so the tools could not unlock the browser's cookies | Test again while watching, and choose Always Allow |
| "cannot decrypt … cookies", "failed to decrypt cookie" or "unknown cookie version" | The tools cannot unlock this browser's cookies, as with Chrome and Edge on Windows | Use Firefox |
| "account cookies are no longer valid" | The Instagram login in that browser has expired | Sign in to Instagram again in that browser profile |
| "Could not copy Chrome cookie database" | On Windows, Chrome locks its cookie file while it runs | Use Firefox |
| "Operation not permitted", about Safari's cookies | Safari's cookies need Full Disk Access | Use another browser |
| "ran for more than 20 minutes and was stopped" | Most likely a Keychain dialog that nobody answered in a scheduled run | Test again while watching, and choose Always Allow |
| "--login takes a browser …" | The Browser value in the Settings is not one the script accepts | Turn login reads on again, to write a new value |
