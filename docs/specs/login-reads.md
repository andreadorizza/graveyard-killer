Shipped in 0.6.0 (part 1) and 0.9.0 (part 2). The spec login reads were built from, kept as a record; the skill files and the ADRs describe current behaviour. [As built](#as-built) lists where the build differs.

# Spec: read Instagram posts that only signed-in users can see

This spec covers what the Worker spec left out of scope: "The Instagram login fallback, browser cookies, and the Windows cookie notes" (`docs/specs/worker.md`). ADR 0001 already sets the policy. This spec says how to build it.

## Problem Statement

Instagram shows some posts only to signed-in accounts. A creator can limit who sees their account by age, for example. A logged-out visitor then gets a notice that the account limits who can see its content, and no post.

The Worker reads every post logged out (ADR 0001), so it can never read these posts. I checked one age-limited post on 2026-11-16, logged out, from a home connection:

- yt-dlp 2026.10.21 says "Instagram sent an empty media response". In yt-dlp's `extractor/instagram.py`, this error comes when the page's `xig_polaris_media.if_not_gated_logged_out` is empty. The message's own advice: check the post in a logged-out browser, and if it is hidden there, pass cookies with `--cookies-from-browser` or `--cookies`. Otherwise, report a bug.
- The message alone does not prove a gate. In June 2026 an Instagram change made it appear for public posts too (yt-dlp #17074, fixed by updating yt-dlp). For this post, a logged-out browser showed the gate.
- gallery-dl 1.32.17 gets "HTTP redirect to login page".
- The post's `/embed/captioned/` page is Instagram's error page.

`post.py` matches that yt-dlp message to none of its patterns, so the post gets the status `error`. The Entry stays in the Inbox with yt-dlp's English text as its Note. Every run reads it again and spends one download each time (#6). It must not become `needs_login` either. That status stops Instagram for the whole run, and this Entry would stop it on every run.

## Solution

There are two parts, built in this order.

1. **Give these posts their own status.** `post.py` reports them as `login_only`. The Worker leaves such an Entry where it is, Inbox or Buried, with a Note that says Instagram shows the post only to signed-in users. While login reads are off, later runs do not read it again. The Ping lists it once and offers login reads.
2. **Login reads, only when I turn them on.** The Worker reads a `login_only` post a second time with my own Instagram login, which yt-dlp and gallery-dl take from a browser on this computer where I am signed in. Every post is still read logged out first. Login reads are Instagram only and capped per run, with a long pause before each. They turn themselves off at the first challenge to my account.

## User Stories

### Gated posts, with login reads off

1. As a Library owner, I want a post that Instagram shows only to signed-in users to say so in its Note, so that I know why it is still a placeholder.
2. As a Library owner, I want such a post not to be read again on every run, so that it does not spend a download each day.
3. As an Instagram user, I want one gated post not to stop the other Instagram posts in a run, because the gate is on that post, not on my connection.
4. As an Instagram user, I want two new gated results in a row to stop Instagram for the run, so that a block on my connection is never taken for gated posts.
5. As a Library owner, I want the Ping to list a gated post once and to offer login reads, so that I can choose to read it.

### Turning login reads on and off

6. As an Instagram user, I want login reads off until I turn them on, so that my account is used only when I say so.
7. As an Instagram user, I want to hear the risk before I turn them on: it is my real account, Instagram's terms forbid automated collection, and Instagram has flagged sessions after a few dozen downloads.
8. As a Library owner, I want to be asked which browser and profile on this computer is signed in to Instagram, with a recommendation for the browser that needs the fewest permissions.
9. As a non-technical user, I want to know beforehand which prompt my computer will show, and what it means to approve it for good.
10. As a Library owner, I want a test read while I watch, so that any prompt comes up now and not in a scheduled run that nobody watches.
11. As a careful Instagram user, I want to be told that a second Instagram account in its own browser profile works too, so that I can keep my main account out of this.
12. As a Library owner, I want to turn login reads off from any chat on my computer.

### Login reads

13. As an Instagram user, I want every post read logged out first, with my login used only for posts Instagram showed as `login_only`.
14. As a TikTok and YouTube user, I want my login never used for any platform but Instagram.
15. As an Instagram user, I want at most a few login reads per run, with a long random pause before each, so that the run does not look like scraping.
16. As a Library owner, I want each login read to count against the download budget, like any other read.
17. As an Instagram user, I want the Worker to stop at the first challenge to my account: no more Instagram in that run, and login reads turned off until I turn them on again.
18. As a non-technical user, I want a browser problem (a prompt I denied, a missing permission, cookies the tool cannot read) to stop login reads for the run, and to show up in the Ping with what to do.
19. As a Library owner, I want a post that even my login cannot see to become Unavailable after two tries, so that it is not retried forever.
20. As an Instagram user, I want no copy of my cookies saved by Graveyard Killer, so that nothing about my login is left on disk.

### Development

21. As a maintainer, I want `post.py`'s login reads tested with fake tools on PATH, so that no test ever reads a real browser's cookies or calls Instagram.
22. As a maintainer, I want one manual check of a real login read per browser and OS before release, so that the browser notes in this spec stay true.

## Implementation Decisions

### The post script

- **A new status, `login_only`.** It has its own pattern list, starting with yt-dlp's "empty media response". gallery-dl's "redirect to login page" stays `needs_login`, because a challenge gives it too. yt-dlp reports the gate before it knows whether the post is a video, so a gated carousel never reaches gallery-dl (to verify).
- **`read --login <browser>`** reads one post with the browser's cookies:
  - Instagram links only. Any other link is refused before any tool runs, as `error`.
  - `<browser>` is a browser name that both tools support, optionally followed by `:<profile>`, where the profile is letters, digits, spaces, dots, dashes and underscores, up to 64 characters. Anything else is refused before any tool runs. It is passed as one argument, never through a shell.
  - yt-dlp gets `--cookies-from-browser <browser>` in place of `--no-cookies`. gallery-dl gets `--cookies-from-browser <browser>/.instagram.com` (with the profile after the domain), so it loads only Instagram's cookies. Both tools still ignore their config files.
  - It never passes `--cookies <file>`, so no cookie file is written. yt-dlp reads a copy of the browser's cookie database in a temporary folder that it deletes itself (`cookies.py`, `tempfile.TemporaryDirectory`).
  - The status rules stay the same. `needs_login` from a login read now means a challenge to the account.
- **No new command.** The test read when turning login reads on is an ordinary `read --login` of a gated Entry.

### The Settings

A new section, **Instagram login**, after Limits:

| Setting | Value |
| --- | --- |
| Browser | (empty: login reads are off) |
| Reads per run | 3 |

- "Browser" holds a value such as `firefox` or `chrome:Profile 1`. It names a browser on the computer that runs the Worker. Setup already keeps the scheduled Worker on one computer only.
- A new Library starts with Browser empty. A Library without the section has login reads off.
- `library.md` gains the section and its line in the list of Settings. Both Library apps store it like Limits.

### The Worker run (`worker.md`)

- **The intro** changes from "with no login" to "logged out, and with the user's login only for posts that need it, when the user turned that on".
- **Listing the Inbox (step 3).** While Browser is empty, leave out the Entries whose Note says that Instagram shows the post only to signed-in users. Dig up does the same (`graveyard.md`).
- **Acting on `login_only`** (step 3 of Each Entry):
  - **Login reads are off, used up, or stopped for this run:** leave the Status as it is, and set the Note to "Instagram shows this post only to signed-in users", in the Settings language.
  - **Otherwise:** wait a random 30 to 90 seconds, then run `read --login <Browser>` on the same Link, through the same quoted heredoc. Act on its result:
    - `ok`: merge or finish as usual.
    - `unavailable`: as usual.
    - `login_only`: Instagram hides the post even with the login. Set the Note to say so. If the Note already said so, set Status Unavailable with that Note instead. Stop login reads for this run, since the browser may not be signed in to Instagram.
    - `needs_login`: a challenge to the account. Stop reading Instagram for the run, as for any challenge. Write Browser empty with [Write the Settings](library.md#write-the-settings), which turns login reads off. Leave the Note as the challenge Note says.
    - `error`: a browser or tool problem. Stop login reads for this run. Keep the gated Note, and give the `reason` in the Ping.
- **Two new gated results in a row,** with no other Instagram result between them, count as a challenge: treat the second as `needs_login`. A result is new when the Entry's Note did not already say it is gated. The same message came for public posts during an Instagram change (#17074), so without this rule a breakage could mark every Instagram Entry as gated.
- **Budget:** each login read uses one download, on top of the logged-out read.
- **Pauses:** the 30 to 90 seconds come on top of the 6 to 12 seconds before each Instagram Entry. Like the 3 reads per run, they are a choice, not a measurement: ADR 0001 says no safe rate is known. At one run a day, 3 reads per run means at most about 90 login reads a month.

### The Ping (`ping.md`)

The fixes gain:

- the Entries this run found gated, with links. While Browser is empty, they come with one offer: "Read them with your Instagram login? Say yes to hear what that means." The existing rule that a repeat Note is not news keeps the offer from coming every day;
- a challenge during a login read: login reads are off now. Check the Instagram app for a warning, and say "turn Graveyard Killer's Instagram login back on" to resume;
- a browser problem, with the `reason` and what to do;
- gated posts that even the login could not see.

Under "When the user answers": a yes to login reads follows `login.md`.

### Turning login reads on (a new reference, `login.md`)

It starts on a yes to the Ping's offer, or when the user asks any chat on the computer to turn Graveyard Killer's Instagram login on or off. On a phone, the agent says that this happens on the computer, and stops. A scheduled run never does it. `SKILL.md`'s job list gets one line that points here.

1. **Say the risk once,** in the Settings language. Login reads use the user's real account. Instagram's terms forbid collecting information in an automated way (quote the clause, with its link). Instagram has flagged sessions after a few dozen downloads. The Worker makes at most 3 login reads a run, with long pauses, and turns them off at the first challenge. A second Instagram account, signed in to its own browser profile, keeps the main account out of it, provided that account also passes the creator's limits. Ask whether to go on.
2. **Ask which browser,** and which profile when it has more than one. Recommend one as the table in [Browsers](#browsers) says, for this computer's OS. Done when you have a value that `read --login` accepts.
3. **Say what this computer will ask,** from the same table, before the test.
4. **Write the Settings:** Browser, and Reads per run only if the user wants another number.
5. **Test while the user watches.** Run a login read on the oldest gated Entry. On `ok`, finish it as a Worker run does, and say that scheduled runs will now read gated posts. On `error`, explain the `reason`, then offer another browser or turning login reads off. With no gated Entry, say that the next gated post will be read, and that any prompt may first come up then.

Turning off writes Browser empty, and says so.

### Browsers

Recommend Firefox on both systems. It is the only browser that works on both, and it needs no prompt or extra permission. The sources are in Further Notes.

| OS | Browser | Works | What the computer asks | Offer it |
| --- | --- | --- | --- | --- |
| macOS | Firefox | Yes | Nothing: the tools read its cookie database directly | Recommended |
| macOS | Chrome, Edge, Brave, other Chromium browsers | Yes | A Keychain dialog for "<Browser> Safe Storage", with Deny, Allow Once and Always Allow. Scheduled runs need Always Allow, given during the test read | Yes, after saying that Always Allow lets the `security` tool read that key from then on without asking |
| macOS | Safari | Only with Full Disk Access for the app that runs the Worker | Full Disk Access, set by hand in System Settings, which lets that app read all files, other apps' data included | No: too broad. Mention it only if the user has no other browser signed in |
| Windows | Firefox | Yes | Nothing | Recommended |
| Windows | Chrome | No | Chrome 127 and later encrypt cookies with App-Bound Encryption, which yt-dlp does not decrypt and does not plan to. Chrome also locks its cookie database while it runs | No: suggest Firefox |
| Windows | Edge | Probably not | Edge binds its encryption keys to Edge by default, like Chrome | No, until a manual check says it works |
| Windows | Brave, Opera, Vivaldi | Unknown | Unknown | No, until a manual check says it works |

`login.md` holds this table in plain words. The manual check before each release keeps it true.

### Considered options

- **Every Instagram post read with the login.** It would need fewer reads and fail less often, but it puts the account at risk on every post. ADR 0001 rejects it.
- **A cookie file exported once.** It leaves the login on disk in a file that, as yt-dlp's FAQ warns, can hold the cookies for every site. The user must also export it again each time the session expires. Rejected.
- **The agent's own signed-in browser** (Claude Desktop's browser pane). It gets the caption and screenshots but no audio, so no transcript. It also ties the Worker to one agent's tools, while the Worker should run in other agents too (#3). Rejected.
- **A tool that signs in with the user's password,** such as Instaloader. Graveyard Killer never asks for or stores a password. Rejected.

### Other files

- **ADR 0001:** its consequence on the login fallback gains this spec's choices: off by default, 3 reads per run, 30 to 90 second pauses, and off again at the first challenge. No new ADR is needed.
- **GLOSSARY.md:** a new term, **Login read**: a second read of a gated Instagram post with the user's browser login.
- **Setup** does not change. Login reads are offered when the first gated post shows up, so a user who never meets one never hears about them.

## Testing Decisions

- **The post script,** with fake tools on PATH, as today:
  - yt-dlp's "empty media response" gives `login_only`;
  - `read --login firefox` gives yt-dlp `--cookies-from-browser firefox` and gallery-dl `--cookies-from-browser firefox/.instagram.com`. yt-dlp no longer gets `--no-cookies`, and neither tool gets `--cookies`;
  - a profile ends up in both tools' values, after the domain for gallery-dl;
  - `read` without `--login` still passes `--no-cookies` (the existing test);
  - `--login` on a TikTok, YouTube or other link is refused before any tool runs;
  - a browser value that is not a known browser with a plain profile is refused before any tool runs, such as `firefox --exec x`, `firefox;rm -rf ~` or `../x`;
  - a tool's cookie error gives `error`, with the tool's reason;
  - a challenge during a login read gives `needs_login`.
- **Worker evals,** on the test Library only:
  - a gated Instagram Entry with Browser empty stays in the Inbox, with the gated Note in the Settings language and no other change. The Ping lists it and offers login reads;
  - a second run leaves that Entry out and spends no download on it;
  - a gated Entry does not stop the next, ungated Instagram Entry.
  - The gated post must be public and age-limited by its creator, such as a drinks brand's post, never a post from a user's own saves.
- **No eval uses a real login.** Login reads are checked by hand on the maintainer's computer, once per browser and OS in the table, before each release that changes them.

## Out of Scope

- Stories. A login read only retries a gated post, and a Story is gone within 24 hours.
- Logins for TikTok, YouTube or any other platform.
- Checking whether the browser is signed in to Instagram before a run.
- Retries of other failed posts (#6). This spec only stops retries of gated posts while login reads are off.
- Linux.

## Further Notes

- **Checked 2026-11-16,** from the maintainer's Mac, logged out, on one age-limited post: the tool messages in the Problem Statement.
- **Checked 2026-11-16 in the installed tools' source** (yt-dlp 2026.10.21, gallery-dl 1.32.17):
  - yt-dlp supports brave, chrome, chromium, edge, firefox, opera, safari, vivaldi and whale (`--cookies-from-browser BROWSER[+KEYRING][:PROFILE][::CONTAINER]`).
  - gallery-dl takes `BROWSER[/DOMAIN][+KEYRING][:PROFILE][::CONTAINER]`. A domain that starts with a dot also matches its subdomains.
  - On macOS, both tools get a Chromium browser's cookie key with `security find-generic-password -s "<Browser> Safe Storage"`. That key is in the user's login Keychain.
  - On macOS, Safari's cookies come from `~/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies`.
  - yt-dlp decrypts Windows Chromium cookies of version `v10` only.
  - yt-dlp copies the cookie database to a temporary folder that it deletes itself.
- **Checked 2026-11-16 in official sources:**
  - **yt-dlp README:** the `--cookies-from-browser` syntax and browser list above. The latest release is 2026.10.26.
  - **gallery-dl `docs/options.md`:** the syntax above. Its README covers Chromium-based browsers, Firefox and Safari. The latest release is 1.32.20.
  - **Windows Chrome:**
    - yt-dlp #10927 (open) says `--cookies-from-browser chrome` will likely stay broken on Windows because of App-Bound Encryption. Its workarounds are Firefox, an exported cookie file, or turning off a Chrome security policy.
    - yt-dlp #17443, asking to support it, was closed as not planned.
    - Google announced App-Bound Encryption for Chrome 127 on Windows: https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html
  - **Windows Chrome lock:** yt-dlp #7271 (open) is "Could not copy Chrome cookie database". The workaround is to close Chrome completely.
  - **Windows Edge:** Microsoft's `ApplicationBoundEncryptionEnabled` policy page (updated 2026-11-03) says Edge binds its encryption keys to Edge by default: https://learn.microsoft.com/en-us/deployedge/microsoft-edge-browser-policies/applicationboundencryptionenabled
  - **macOS Keychain:** Apple's Keychain Access guide says an app that wants a keychain password asks first, with Deny, Allow Once and Always Allow: https://support.apple.com/guide/mac-help/kychn002/mac. No yt-dlp document covers the prompt.
  - **macOS Safari:**
    - yt-dlp #7392 (open) is a `PermissionError` on `Cookies.binarycookies`. Users report that Full Disk Access fixes it.
    - Apple says Full Disk Access lets an app read all files, other apps' data included: https://support.apple.com/en-us/guide/mac-help/mchl211c911f/mac
  - **Instagram's Terms of Use** forbid "collecting information in an automated way without our express permission", even when logged in (https://help.instagram.com/581066165581870). The new terms that take effect on 20 January 2027 keep the rule.
  - **yt-dlp's wiki** warns, for YouTube only, that using an account with yt-dlp can get it banned, and suggests a throwaway account. Its FAQ warns that an exported cookie file holds the cookies for every site.
- **To verify while building:**
  - what else Always Allow on "<Browser> Safe Storage" lets read the key, since the access is granted to the `security` tool, not to yt-dlp;
  - that Firefox works on Windows. The only source is the workaround in #10927;
  - that Instagram cookies in a Firefox container are found: yt-dlp reads all containers by default, and gallery-dl reads none;
  - whether the two-in-a-row rule should also update yt-dlp once, as an HTTP 403 does, since #17074 was fixed by an update;
  - whether `check` should install yt-dlp's `curl-cffi` extra. In #17074 a maintainer said impersonation is now required for Instagram without cookies. On 2026-11-16, yt-dlp here had no impersonation targets (`curl_cffi` unavailable) and still read a public reel logged out;
  - whether posts from a private account the user follows give the same message, so that login reads cover them too;
  - that a gated carousel gives yt-dlp's message before gallery-dl runs;
  - a real login read with each browser in the table, in a scheduled run with nobody watching.

## As built

Choices made while building part 2, from the "To verify while building" list and a few gaps:

- **Firefox containers.** gallery-dl reads no container by default and yt-dlp reads them all (their `cookies.py`, checked 2026-11-16). So gallery-dl gets `::all` for Firefox, as `firefox/.instagram.com::all`, and both tools see the same login.
- **Cookie warnings.** When a tool cannot use the browser's cookies, it often only warns and goes on logged out: gallery-dl's `cookies: …`, and yt-dlp's `find-generic-password failed` (a denied Keychain dialog), `cannot decrypt v10 cookies` or `The provided Instagram account cookies are no longer valid`. A gated post then looks hidden even from the login, and the login page looks like a challenge. So yt-dlp keeps its warnings on a login read, and a `login_only` or `needs_login` that follows such a warning is `error`, with the warning as its `reason`.
- **The cookie copy.** Both tools copy the browser's cookie database to a temporary folder and delete it when they finish, but not when post.py stops them at their time limit, as after a Keychain dialog nobody answers. A login read runs them with their temporary folder inside its work folder, which `clean` deletes.
- **A post's own link only.** yt-dlp loads every cookie of the browser, not only Instagram's, so a share link or Instagram's link shim that led to another site would read it with the user's login there (found by the commit's security review). A login read refuses any link but a post's own (`/p/`, `/reel/`, `/tv/`), reads its canonical form, and lets yt-dlp use only its Instagram extractor (`--use-extractors Instagram`). The Worker skips a gated Entry with any other Link, so it keeps its Note and does not stop login reads for the run.
- **gallery-dl when yt-dlp finds the post hidden even with the login.** With a signed-in Chrome session, yt-dlp once got an empty media response for the age-limited test post, which the account sees in the browser, and read it fine on the next try; gallery-dl read it with the same cookies (2026-11-16). One such response would have given the post the second gated Note, and two would have made it Unavailable. So a login read that yt-dlp finds hidden reads the post again with gallery-dl, asking it for the merged video file: for a DASH video, gallery-dl would call yt-dlp's module, which its own install lacks. A video then gets keyframes and the local transcript, but no title, duration or creator's captions. The result is `login_only` only when gallery-dl finds no media either.
- **No 403 retry on a login read.** A 403 with the user's cookies may be Instagram refusing the account, and the update-and-retry would use the account a second time. It is `error`, which stops login reads for the run.
- **The 30 to 90 second pause** is `post.py pause --login`, a command of its own like the 6 to 12 second pause, since a shell sleep needs approval where only the skill's scripts may run.
- **The Browser value on the command line.** The Worker checks it against the same rule as the script before using it, and puts it in single quotes: any other value is a browser problem, with no read.
- **Login reads used up or stopped.** The rest of the run skips the Entries that hold a gated Note, without reading them logged out, so they spend no download that no login read can follow.
- **Two in a row.** Only logged-out reads count, and only the second Entry is treated as `needs_login`, as this spec says; the first keeps its gated Note. 0.6.0 rewrote both Notes, so two gated posts next to each other in the list stopped Instagram on every run. A login read between two results breaks the row.
- **The test read** when turning login reads on makes at most 2 reads, the second only when the first post turned out Unavailable.
- **Two gated Notes.** "Instagram shows this post only to signed-in users" after a logged-out read, and "Instagram hides this post even from your login" after a login read gave `login_only` too. The second one twice makes the Entry Unavailable. Both count as gated, for the Inbox list, Dig up and the two-in-a-row rule.
- **The Ping's offer** of login reads carries no number, like the duplicates question. It names both answers: yes in the run's chat, or "turn on Graveyard Killer's Instagram login" in any chat on the computer.
- **Checked by hand** on 2026-11-16: login reads with Chrome on macOS (the Default profile, through the Keychain dialog) read the age-limited test post, once through yt-dlp and once through the gallery-dl fallback. **Still to check by hand:** Firefox and the other browsers `login.md` offers, a login read in a scheduled run with nobody watching, Firefox on Windows, a gated carousel, and whether posts from a private account the user follows give the same message. Not done: updating yt-dlp on the two-in-a-row rule, and `curl-cffi` in `check`.
