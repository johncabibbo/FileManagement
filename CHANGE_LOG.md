# File Management — Change Log

---

## v2.00 — Aug 12, 2026

- **Convert Video to MP4**: the per-file `[i/N] filename` line now also shows the source file's size, e.g. `(123.4 MB)`, so you can see how big a file is before the spinner starts ticking.

---

## v1.99 — Aug 12, 2026

- **Convert Video to MP4**: added a spinner + elapsed-time indicator while each file encodes, so a slow/large conversion no longer looks frozen — moviepy's `write_videofile()` prints nothing on its own (`logger=None`) and can run for minutes with zero visible output. The encode now runs in a background thread while the main thread animates `| / - \` next to the elapsed seconds; clears cleanly before the OK/FAILED result. Shared with the AWS S3 wizard's Optimize Video step (same underlying `_convert_video_files_core()`).

---

## v1.98 — Aug 12, 2026

- **Main Menu reordered**: Display, Find, Compare, Monitor, Eject, Zip, Convert, Optimize Media, Sync, Remove, Clean Up, Mount Shares, Permissions, Environment Vars, Create Random UID, AWS S3, Local Scripts, Admin. Purely cosmetic — each option's `[N]` key and dispatch target were renumbered to match its new position; no functional change.

---

## v1.91 — Aug 1, 2026

- **Remove (Remove Folder / Remove Folders by Name / Remove Duplicates by Name/Hash/Fuzzy) and Sync**: the dry-run preview listing is no longer forced every time in interactive mode — a new upfront **"Dry run first?"** question (default Yes) lets you skip straight past the itemized preview. The final "Actually delete/copy these N item(s)?" confirm still always happens either way — nothing is ever deleted or copied without that explicit go-ahead, dry run or not.
- CLI (`--delete`/`--move-to`/`--copy`, or the dry-run-only default) is unaffected — those already choose dry-run vs. live explicitly via flags, so there's nothing to ask.
- Verified live: both the "skip dry run → decline final confirm → nothing touched" and "show dry run → confirm → deletes/copies correctly" paths, for both Remove and Sync.

---

## v1.90 — Aug 1, 2026

- **Remove → Duplicates by Name/Hash/Fuzzy Name, and Find Duplicates → [D] Delete Duplicates**: added a "move to a folder" alternative to deleting. Interactively, after the usual dry-run preview you now choose **[D] Delete / [M] Move to Folder / [C] Cancel** instead of a plain Y/N; moving asks for a destination folder (created if it doesn't exist) and only needs a normal confirm — it's reversible, unlike delete, which still requires typing YES.
- **CLI**: `fm.py remove dup-name|dup-hash|dup-fuzzy ... --move-to FOLDER` moves instead of deleting (mutually exclusive with `--delete`; `--yes` skips the confirm). Rejected with an error for the non-duplicate remove types (`folder`, `name`, `folder-name`, `zero-size`).
- Moved files are never overwritten: a name collision at the destination gets an auto `" (1)"`, `" (2)"`, ... suffix. New `_unique_dest_path()`, `_perform_move()`; `_finish_removal()` gained `allow_move`/`move_to` params, shared by all four duplicate-removal call sites.

---

## v1.89 — Jul 29, 2026

- **AWS S3 credentials simplified**: Admin Menu now only asks for Access Key ID, Secret Access Key, and Region. Bucket and folder/prefix are no longer stored there — they're entered per task instead: Zip SubFolders' "Push files to AWS S3?" prompt now asks for a bucket (+ optional folder) when you say Yes, and the AWS S3 wizard's step 8 (already per-task) no longer pre-fills from a saved bucket. Lets one set of credentials push to different buckets on different runs.
- `is_aws_configured()` no longer requires a bucket — just Access Key ID + Secret Access Key. `_s3_push_file()`/`_s3_push_zip()` no longer fall back to an Admin-configured bucket; it's now a required argument from every caller.

---

## v1.88 — Jul 29, 2026

- Main Menu: **Admin is the last option again** ([18], after AWS S3 at [17]) — the v1.86 AWS S3 addition had appended it after Admin, breaking the "Admin is always last" convention from v1.65.
- **AWS S3** is now grayed out on the Main Menu, with the reason shown inline, until it's actually usable: `boto3 not installed`, or `AWS credentials not configured — see Admin Menu`. Recomputed fresh on every Main Menu redraw (`main_menu()` now builds its trailing AWS S3 + Admin options inside the render loop instead of once outside it), so setting credentials in Admin Menu and backing out immediately un-grays it — no restart needed. Admin itself is never gated, since it's where those credentials get set.

---

## v1.87 — Jul 29, 2026

- **Centralized activity logging** for FM and DocInfo Manager: `api/zipFileLog.php` and `api/fileLog.php` (doc_cloudbox9_com) now write to `docInfo.activityLog` via `standardModel::activityLogAdd()` instead of a separate `CB9Inventory.activityLog` via `cb9InventoryModel::activityLogAdd()` (now removed — those two endpoints were its only callers). `CB9Inventory.activityLog` is frozen going forward; its ~600 existing rows stay for history.
- `docInfo.activityLog` gained two new nullable columns, `docProjectId`/`serverId`, identifying the **source system** that logged each entry (not what got changed). `fmConfig.json`'s `logZip` block gained matching `serverId`/`docProjectId` keys (`1`/`87` — Ash Mac / File Management) sent on every `zipFileLog.php`/`fileLog.php` call; both are optional, and existing DocInfo Manager call sites elsewhere in the app are unaffected (they simply don't pass these new fields, matching their optional/nullable nature).
- Added `activityLogTypeId` **102** ("Zip Log") to `docInfo.activityLogType`, matching the row that already existed in `CB9Inventory.activityLogType` — needed since `api/zipFileLog.php` now logs into `docInfo.activityLog` under that type. (`api/fileLog.php` continues logging under type **6** "AWS S3", which already existed in both databases' `activityLogType`.)
- `standardModel::activityLogAdd()` gained two new optional trailing parameters, `$docProjectId`/`$serverId` (default `NULL`) — its 27 existing call sites across the app are unaffected. DocInfo Manager's own reference values (`14`/`2`) are now available as `DOC_PROJECT_ID_DOCINFO`/`SERVER_ID_DOCINFO` in `setting.php`.

---

## v1.86 — Jul 29, 2026

- New Main Menu option **[18] AWS S3**, with four submenu options:
  - **Display Buckets & Sizes** — every bucket the saved credentials can see, with object count and total size. S3 has no cheap per-bucket size API, so this lists every object in every bucket directly — can be slow on large buckets.
  - **Optimize Media, Zip, Log & Upload to AWS S3** — a guided wizard (`aws_s3_optimize_menu()`): Folder or File → Optimize Video files (convert to MP4, + delete originals) → Resize Images (Height/Width, default 1200×1200 — fit within the box, preserve aspect ratio, never upscale — filename gets a `_HEIGHT-WIDTH` suffix using the *actual* resulting size, + delete originals) → Create Media Thumbnails (80×80, `_tmb` suffix) → Zip to 1 File / Zip Subfolders / neither → Log Contents to DocInfo Manager → AWS S3 Bucket (+ optional folder/prefix) → **Review screen** → 3…2…1 countdown. **ESC/Q during the countdown returns to the Review screen with the same answers** (not re-asked, not aborted) — only ESC/Q on one of the 8 questions themselves cancels the whole wizard, same as every other multi-question flow in FM. Zipped output logs through the existing zip-log path (now also carrying its S3 location); files uploaded without zipping log individually through the new fileLog path.
  - **Search AWS S3** — filename **prefix** match across every object in every bucket (S3 has no server-side wildcard/glob support — this is `startswith()`, not a full pattern match).
  - **Search DocInfo Manager Records** — full wildcard filename search (`*`, `?`) merging results from zipFileContent (files inside logged zips) and the new fileLog (individual files logged without zipping) into one table.
- **New DocInfo Manager server-side support** (`doc_cloudbox9_com`): `CB9Inventory.fileLog` already existed (unused) — wired it up with new `cb9InventoryModel::fileLog()`/`fileLogSearch()` methods and new `api/fileLog.php`/`api/fileLogSearch.php` outpost endpoints (same dual-auth pattern — `serverSecretKey` + DocInfo Manager user token — as `api/zipFileLog.php`). Added a `fileLogBeforeUpdateArchive` trigger (`fileLog` → `fileLogArchive`), matching the existing `zipFile`/`zipFileContent` archive-on-update pattern. `zipFileLog()`/`api/zipFileLog.php` also gained optional `s3Bucket`/`s3Key`/`uploadConfirmed` passthrough (columns already existed on `zipFile`, previously always NULL/0).
- Refactored `convert_videos_to_mp4()` and `convert_images_to_format()` into thin UI wrappers over new no-I/O core loops (`_convert_video_files_core()`, `_convert_image_files_core()`) so the AWS S3 wizard can drive the same conversion engine directly without nested screens/prompts/double-logging. `_convert_image_files_core()` gained an optional `resize_to=(w, h)` parameter, also usable stand-alone. Added `_create_thumbnails()` and `zip_folder_to_one_file()` (no existing FM feature previously zipped an entire folder to a single archive).
- Generalized `_s3_push_zip()` into `_s3_push_file(local_path, bucket, folder)` so a caller can target a different bucket/folder per run than the Admin-configured default; `_s3_push_zip()` kept as a thin backward-compatible wrapper for Zip SubFolders.

---

## v1.85 — Jul 29, 2026

- Main Menu: shortened the **Environment Vars — Display All** label to just **Environment Vars** (the option's `[H]` Help description still explains it lists every environment variable)
- Fixed the `VERSION` constant (was stuck at `"1.62"` since 2026-07-22 while the Revision History kept advancing to v1.84 — the app's exit/About screens were showing a version 22 releases stale; see the Documentation entry below, which is what surfaced this)

---

## Documentation — Jul 29, 2026

- Added `TECHNICAL_REFERENCE.md`: architecture-level companion to `README.md` — the full menu structure diagram (read directly from `main_menu()` and every submenu function, including dynamic profile entries and gray-out logic), a section map of where each feature lives in `fm.py`, the complete `fmConfig.json` key reference (including `mountProfiles`, `commonFolders`, and `serverJobs`/`serverJobLog`, none of which were documented anywhere before), the CLI↔menu command map, and a Known Issues note
- `README.md`: documented **Mount Shares** and **Server Jobs** (entire Main Menu items, previously undocumented despite existing in the code) plus their `fmConfig.json` sections; added the previously-missing **Drives in Use** (Display), **Find Files in Zip** and **Search Zip File Contents by Name** (Zip), and **Manage Common Folders** (Admin) menu options; fixed the Main Menu table/overview (was missing 2 of 17 items and mis-numbered from Permissions onward); corrected a stale "seven options" count on the Find submenu (actually eight); added `drives-in-use` and `find-zip` to the CLI reference
- No code changes to `fm.py` in this pass — see `TECHNICAL_REFERENCE.md`'s Known Issues for the separate, pre-existing `VERSION` constant / revision-history mismatch (code stuck at 1.62, header docs at v1.84) noticed while writing this

---

## v1.80 — Jul 26, 2026

- Display → new **Drives in Use** option: lists every mounted external drive and whether it's currently being read from or written to. Detection samples each drive's underlying physical disk with `iostat` for ~1 second and checks for actual transfers, rather than checking for open file handles (`lsof`) — so a drive with an idle-but-open file doesn't falsely show as in use. macOS only (uses the same `diskutil`-based external-drive detection as Eject). Also added as CLI command `fm.py drives-in-use`

---

## v1.67 — Jul 23, 2026

- Zip → **Log Zip File Contents** now remembers the last file/folder you entered (`LAST_PATHS["zip_log_target"]`, persisted to `fmLastPaths.json` like every other keyed prompt) — Enter reuses it, typing a new path overrides it. Applies to both the interactive prompt and the `fm.py zip-log` CLI path
- README.md: documented the previously-undocumented "remembers the last path" behavior (Features list + the Zip section's Log Zip File Contents bullet) — this pattern already existed for Compare/Sync/Zip SubFolders/etc., not just the new Log Zip File Contents case

---

## v1.66 — Jul 23, 2026

- Zip menu's **Log Zip File Contents** `[H]` Help now spells out what "matched by name + size" and "updated" actually mean for `zipFileContent`: inserted (new file) / updated + reactivated (changed file) / left alone (unchanged) / soft-deleted, `deleted=1` (file no longer in the archive) — and that every `zipFileContent`/`zipFile` `UPDATE`, including the soft-delete, is archived pre-change via the `BEFORE UPDATE` triggers into `zipFileContentArchive`/`zipFileArchive`
- Same detail added to `README.md`'s "8 · Zip" section

---

## v1.65 — Jul 23, 2026

- Main Menu: **Admin** is now the last option ([15], after **Environment Vars** at [14]) — previously Admin was [14] and Environment Vars was [15]

---

## v1.64 — Jul 23, 2026

- Help screens are easier to read: `_print_help_desc()` now inserts a blank line between paragraphs, while bullet lines stay tight against each other (no blank line between one bullet and the next)
- Rewrote the densest option descriptions across every menu — Compare, Find, Remove, Zip, Optimize Media, Clean Up, Permissions, and the Main Menu's Logging help note — as short paragraphs and bullet lists instead of one run-on block of text

---

## v1.63 — Jul 23, 2026

- Log Zip File Contents now computes an MD5 hash of the whole archive (`_file_md5()`, same block-read approach as vlcmenu's duplicate finder) and sends it to the DocInfo Manager API as `zipFileHash`, stored on the new `zipFile.zipFileHash` column (indexed) in CB9Inventory
- Stored only for now — matching an existing zip row to update-vs-insert is still by `zipFileName` + `zipFileSizeBytes`; the hash sets up a future duplicate finder against `CB9Inventory.zipFile`

---

## v1.62 — Jul 22, 2026

- Added a new Main Menu option, **Permissions**, with three submenu options: **Set Apache Permissions** (a one-shot chown/chmod fix for `/var/www` — directories 755, files 644, owned by the Apache user/group, via `sudo` — FM's first use of `sudo`; grayed out when `/var/www` doesn't exist), **Run a Profile** (apply a saved permission profile — scans for matching files, previews every permission change, applies only after confirming), and **Set a Profile** (create or edit a saved permission profile)
- New `fmConfig.json` key **`permissionProfiles`**: `name`, `folder`, `pattern` (exact filename, bare extension, or wildcard), `permission` (chmod octal), `recursive` — documented with a worked example in `fmConfig.sample.json`
- Permission-matching scans **include hidden files/dotfiles** (unlike Sync/Compare/Find's usual exclusion) since permission fixes commonly target `.htaccess` and similar; the universal junk-name exclusions (`.DS_Store`, `desktop.ini`, `$RECYCLE.BIN`) still apply
- Permissions is menu-only — no CLI subcommand, matching Admin Menu and Environment Vars

---

## v1.61 — Jul 22, 2026

- Added a new Main Menu option, **Environment Vars**, with one submenu option, **Display All**: lists every environment variable (`os.environ`), name and value, sorted alphabetically. Read-only
- Deliberately **not** written to `fm.log` — environment variables commonly hold secrets (API keys, tokens, credentials), matching the same caution the app already takes with Admin Menu's password/AWS key handling

---

## v1.60 — Jul 22, 2026

- Compare → Compare Folder Contents → Interactive: **Compare By** is no longer a separate full-screen menu — it's now a plain inline prompt, same style as the Recursive/Case-sensitive questions, so Folder A/B, Recursive, Case-sensitive, and Compare By are all gathered in one continuous sequence with zero screen changes in between
- `ESC` during the Compare By prompt now cancels the wizard the same way every other question in it already does

---

## v1.59 — Jul 22, 2026

- Clean Up → Remove Junk Files now also targets **`*.bak`** files, alongside `.DS_Store` and `desktop.ini`. This is independent of the unrelated Compare/Find exclusion list — `.bak` files are only added to this cleanup, not silently excluded elsewhere
- Choosing Remove Junk Files now first shows a checklist of the three file types (all checked by default) — `↑/↓` move, `Space` toggles, `Enter` confirms — so you can unselect any of them before entering the root folder. The CLI (`fm.py cleanup junk ROOT`) has no interactive checklist and keeps removing all three by default

---

## v1.58 — Jul 22, 2026

- `ESC` now cancels **any** question prompt instantly and returns to the menu it was asked from, everywhere in the app — previously only menus and "press any key" screens reacted to `ESC`; free-text prompts and Y/N confirmations used plain input, where `ESC` just typed an invisible character and did nothing
- New raw-mode line reader powers this; every top-level menu (Compare, Display, Find, Remove, Monitor, Sync, Zip, Optimize Media, Clean Up, Admin, Main) now catches the cancellation, so pressing `ESC` anywhere inside a multi-question wizard (e.g. Folder A entered, `ESC` on Folder B) abandons that action and instantly redraws the menu it came from
- Known limitation: the DocInfo Manager password (Admin Menu → Login) and the AWS Secret Access Key still use Python's masked `getpass` input, which can't detect a bare `ESC` mid-keystroke without a from-scratch rewrite — left as-is. Every other prompt in the app, including the Login username and the other AWS credential fields, is `ESC`-aware

---

## v1.57 — Jul 22, 2026

- Compare → Compare Folder Contents now asks **Interactive** (default) or **Run Profile** first: Run Profile lists saved entries from `fmConfig.json`'s new `compareProfiles` array (folderA/folderB/recursive/compareBy/caseSensitive) and runs the chosen one immediately
- Interactive's end-of-run footer is now **`[R]` Run Again / `[S]` Save as Profile / `[Q/ESC]` Quit/Back** — `[S]` prompts for a name and appends the folders/options just used to `compareProfiles`, preserving every other setting already in the file
- `fmConfig.json` / `fmConfig.sample.json`: added the `compareProfiles` key, with a worked example and a `_help` entry in the sample

---

## v1.56 — Jul 21, 2026

- Closed every remaining gap in `fm.log` coverage. File-mutating actions (Sync, Zip, Optimize Media, Remove, Clean Up) now log every individual file created/updated/deleted/uploaded; every other menu action now logs its start, the options chosen, any errors, and its end
- Admin Menu (DocInfo Manager login/logout, AWS S3 credential set/update/clear) previously logged nothing — now logs a start/finish for each action (username, or region/bucket/folder), never the password or AWS secret/access keys
- Zip → Log Zip File Contents previously only wrote to the CB9Inventory DB — now also logs a start/finish plus one line per archive (logged/failed/recorded-as-Failed) to `fm.log`
- Zip SubFolders' pre-zip `.DS_Store`/`desktop.ini` cleanup deleted files with no record anywhere — each deletion is now individually logged
- Monitor File Activity logged nothing to `fm.log` when CSV output was chosen (events went to `fmMonitor.csv` only) — now always logs a start/options/end summary to `fm.log` regardless of output mode; the "not a directory" error is now logged too
- Compare 2 Files, Display All Drives, Display Folder Sizes, Find Folders, Find Files (combined, by name, by extension, over/under N MB) previously had no logging at all — each now logs its start (with options), errors, and a finish summary
- Failed file removals/purges (`_perform_removal()`, Purge Old Log Files) previously vanished silently — failures are now logged individually alongside successes

---

## v1.49 — Jul 20, 2026

- Main Menu: new "Optimize Media" option (9th, right after Zip — Remove, Create Random UID, Clean Up, and Admin each shifted down one)
- New submenu option "Convert Video to MP4": converts `.mov`/`.avi`/`.mkv`/`.wmv`/`.flv`/`.m4v` files to `.mp4` (H.264 + AAC) via `moviepy`. Asks for a source folder, an optional destination (defaults to source), whether to include subfolders, and a Clean Up option to delete each original after a successful conversion (off by default, re-confirmed right before it happens — same pattern as Zip SubFolders' `remove_after`). Collision-safe naming (`name.mp4`, `name-2.mp4`, …) never overwrites
- Grayed out in the menu (like "Log Zip File Contents"' login gate) when `moviepy` isn't installed, showing a "pip install moviepy" hint
- New CLI: `fm.py convert-video SOURCE [DEST] [-r] [--delete]`
- Clean Up's delete-original step now validates the new `.mp4` first — `_validate_converted_mp4()` reopens the output with `moviepy` and checks it's non-empty with a duration within 2% (min 1s slack) of the source's. The original is only removed when validation passes; otherwise it's kept and flagged "— *reason*, original KEPT" in the output, with the run summary reporting how many originals were kept
- Fixed: Convert Video to MP4 could crash the whole script with an uncaught traceback if a per-file filesystem call (`os.makedirs(out_dir)`, the output collision check) hit an error — both sat outside the per-file `try`/`except`. Seen when an external destination drive was unmounted mid-batch: one file's ffmpeg write failed cleanly (caught), but the next file's `os.makedirs()` raised `PermissionError` uncaught and killed the process. Both calls now live inside the `try` block (bad file → reported FAILED, batch continues), and each loop iteration now checks that the destination folder still exists — if it's gone, the batch stops early with a clear message instead of failing once per remaining file
- Convert Video to MP4: new "Pause between files" prompt (seconds, default 5, `0` disables) to ease sustained I/O on an external drive during a long batch — suspected cause of a drive dropping mid-run. Sleeps between conversions (never after the last file), with a live "Pausing Ns (drive cooldown)…" line. New CLI flag: `fm.py convert-video ... --pause SECONDS` (default 0)

---

## v1.48 — Jul 20, 2026

- Renamed Zip menu option "Log Zip File" to "Log Zip File Contents" (label, screen title, and related help text)
- An archive that can't be read (e.g. "File is not a zip file") is no longer skipped — it's still logged with empty contents and a new `loadFailed` flag; server-side, `zipFileLog.php` (v1.4) / `cb9InventoryModel::zipFileLog()` (v2.1) set `zipFileStatusId = 3` (Failed) instead of 1 (Active) so the row still gets recorded with its size, just flagged. Reported distinctly in the summary as "recorded as Failed (unreadable)"

---

## v1.47 — Jul 20, 2026

- Zip menu: added a 4th option "Zip SubFolders & Log" — same as Zip SubFolders, then logs every zip created to CB9Inventory via `log_zip_files()`. Grayed out under the same "login required" reason as Log Zip File
- Zip SubFolders (and Zip SubFolders & Log) now also ask "Push files to AWS S3?" — new `_s3_push_zip()` uploads each successfully created zip via `boto3`, using credentials saved in Admin Menu; skips gracefully (no failure) if `boto3` is missing or AWS isn't configured
- Admin Menu: added Set/Update/Clear AWS S3 Credentials (Access Key ID, Secret Access Key, region, bucket) — stored encrypted via `CB9Lib.secureAuth` under a new `authKey` (`"fmAwsS3"`), same secure store as the DocInfo Manager login but a separate namespace
- FM remains fully usable with no DocInfo Manager login — only Log Zip File and Zip SubFolders & Log require it; Zip SubFolders (without Log) and its optional S3 push do not

---

## v1.46 — Jul 20, 2026

- Menu options can now be conditionally grayed out: `render_menu()` accepts a `(label, description, reason)` triple — a truthy `reason` grays the option out and blocks selection, showing the reason instead of running it (existing 2-tuple options unaffected)
- Zip menu's "Log Zip File" uses this — shown grayed out with "login required — see Admin Menu" whenever not authenticated, instead of letting you select it and only then prompting for credentials (the CLI path `fm.py zip-log`, which has no menu, still prompts inline via `ensure_authenticated()`)
- `_post_zip_log()` now sends the DocInfo Manager token as an `X-API-Token` header; server-side, `zipFileLog.php` (v1.3) now validates it via `_auth.php`'s new `requireUserAuth()`, alongside the existing `serverSecretKey` check — Log Zip File now records which user ran it, not just which machine

---

## v1.45 — Jul 20, 2026

- Added an Admin Menu (Show Aliases-style DocInfo Manager login) to the main menu: `[L]` Login to DocInfo Manager / Logout, showing current auth status. Uses `CB9Lib.secureAuth` with its own `authKey` (`"fm"`) — an independent session from Show Aliases' login, even though both hit the same DocInfo Manager account
- Zip → Log Zip File now requires being logged in before it will run; prompts inline for credentials if not already authenticated, same pattern as Show Aliases' DB actions
- New `fmConfig.json` `auth` block (`baseUrl`, `loginEndpoint`, `secureAuthFile`, `authKey`) — all optional, defaults hardcoded in `fm.py`

---

## v1.44 — Jul 20, 2026

- `pause_return()` (the standard end-of-task "return to menu" screen used throughout the app) now reacts instantly to `[Q]` and `[ESC]`, same as `[Enter]` — previously Q/ESC had no effect there and only a literal Enter press would return to the calling menu
- Fixed `VERSION` variable drift (was still `"1.42"` while the header/revision history had already moved to 1.43)

---

## v1.40 — Jul 16, 2026

- **Sync** (`fm.py sync`): while copying, a periodic milestone line is now written straight to `fm.log` every 15 seconds (`MILESTONE_INTERVAL_SECONDS`), e.g. `2026-07-16 15:22:41 - Copied 728/2103 files, 8.3 GB of 10.4 GB`. New `_log_milestone()` helper writes immediately, unlike the existing `_ActivityLog` mirror which only flushes its buffered copy of the on-screen output once the whole operation finishes — so an interrupted long-running sync now leaves a trail of how far it actually got, not just a "started" marker and then silence.

---

## v1.39 — Jul 16, 2026

- **Monitor** (`fm.py monitor`): the header (Profile/Folder/Recursive/Extensions/Logging) and footer (`[Q/ESC] Stop` + live event counts) are now stationary at the top/bottom of the window in an interactive terminal — only the event feed scrolls between them, using an ANSI scroll region (DECSTBM), the same technique as `backup42.py`'s execution screen (CB9 Static Header/Footer permanent rule).
- Footer event counts (created/modified/deleted) update in place as events occur, without disturbing the scroll region or cursor position.
- The frame redraws correctly on terminal resize (SIGWINCH); a terminal shorter than 13 rows shows a "too small" message instead of drawing a broken frame.
- Non-interactive runs (piped output, cron, `--profile` from a script) are unchanged — plain scrolling text, no ANSI codes.
- Verified with a pty-driven functional test: scroll region set to the correct rows, header/footer content correct, a live file-create event appears in the scroll region, footer counts update in place, and the scroll region/cursor are restored cleanly on quit.
- **Sync** (`fm.py sync`) gets the same stationary-frame treatment: the header keeps Folder A/B, Direction, Options, and the "N new, M updated — size to copy" summary pinned at the top; the footer shows phase status and live `Copying... N/total file(s)` progress, updated in place per file. Only the file plan / confirm prompt / copy output scrolls between them. The frame only kicks in once there's an actual plan to show — folder-not-found and "nothing to copy" stay as short one-shot messages (no frame needed).
- Refactored the ANSI scroll-region/cursor helpers (`_mon_*` → `_frm_*`) to be shared between Monitor and Sync instead of duplicated, and added a common `_frm_cleanup()`.
- Verified the Sync frame with a pty-driven functional test end to end: header shows the real folders/direction/options/summary, the NEW/UPDATE file table and confirm prompt scroll correctly, the footer's live copy progress updates through `0/3` → `3/3`, the files are actually copied to disk, and the frame tears down cleanly afterward.
- **Fixed:** the header could still scroll because both frames measured the terminal with `shutil.get_terminal_size()`, which prefers the `COLUMNS`/`LINES` environment variables when they're set — and those go stale the moment the real terminal window is resized, since nothing re-exports them for a running child process. That stale size fed directly into the frame's row math, misaligning the scroll region against the real screen. Added `_frm_term_size()`, which queries the real size via `os.get_terminal_size()` (a direct ioctl on stdout, bypassing `COLUMNS`/`LINES` entirely); both Monitor's and Sync's frame-drawing functions now use it. Confirmed with a pty test that a real resize is picked up correctly even while `COLUMNS`/`LINES` still hold the old, stale values.
- **Fixed a crash:** running Sync (or any screen wrapped in `with _ActivityLog():`, e.g. Eject) raised `AttributeError: '_ActivityLog' object has no attribute 'fileno'` from `_frm_term_size()`. `_ActivityLog` temporarily swaps `sys.stdout` for a tee proxy that only implements `write()`/`flush()`/`isatty()` — it has no `fileno()` at all. `_frm_term_size()` now queries the real stdout file descriptor (`1`) directly instead of `sys.stdout.fileno()`, which sidesteps that (and any future) Python-level stdout wrapper entirely. Verified with a pty test that reproduces the exact failing call path (`sync_folders()` → `with _ActivityLog(): _sync_screen()`) — no crash, the frame renders correctly, and the activity log still receives the mirrored output as before.
- Sync's footer now shows `Copying N/total: filename (size)...` *before* each file starts, not just the completed count afterward. A single large file — video footage between two external USB drives, for example — can take a long time to physically copy, and the footer used to just sit at the previous count the whole time with no indication anything was happening, easily mistaken for a hang even though the copy was genuinely progressing (confirmed live against a real in-progress sync: the process was correctly blocked in the kernel on real disk I/O, `lsof` showed the exact file being copied, and the destination file's size was actively growing).
- **Compare Folder Contents → Compare By** submenu: relabeled the three options to spell out exactly what each one does instead of the terse `By Name` / `By Size` / `Both`:
  - `Match Name, Display Missing Files`
  - `Match Name, Compare Size, Display Files with Size Differences`
  - `Display Missing Files & Existing Files with Size Differences`
- Sync footer's copy progress now shows percent complete and the total bytes to copy instead of just bytes copied so far — e.g. `Copying... 201/322 file(s)  (85% complete, 28.4 GB/78.2 GB complete)` instead of `(28.4 GB so far)`.
- **Fixed:** `fm.log` entries for Monitor/Sync (anything drawn via the stationary frame) contained raw control-code junk like `^[[?25l`. `_ActivityLog`'s ANSI-stripping regex only matched plain SGR color codes and missed private-mode codes (`\x1b[?25l`/`h` — the `?` isn't a digit or `;`) and non-CSI codes (`\x1b7`/`\x1b8`, DEC save/restore cursor, used around the live footer updates). New `_strip_screen_codes()` strips every CSI sequence generically, converts the frame's absolute row-jumps and save-cursor markers to newlines first so lines land properly instead of being mashed together, and normalizes stray `\r`. Retroactively re-cleaned the existing `fm.log` with it — confirmed zero escape bytes remain anywhere in the file. Entries logged before this fix still show the frame header as one run-on line in a couple of spots (the old code had already destroyed the row-jump codes without converting them to newlines, before this fix existed to do that) — that specific formatting can't be recovered after the fact, but every entry logged from now on is fully clean.
- **Compare Folder Contents** and **Sync** now log a concise "started" entry to `fm.log` the moment the operation begins — activity type plus its folders/options (Direction, Recursive, Conflict, Hidden Files for Sync; Recursive, Compare By for Compare). This is independent of Sync's existing full-output mirror (which only writes once the run finishes) — a long-running or interrupted sync now leaves a record that it was started even if it's killed partway through. Compare had no activity logging at all before this. Also de-duplicated the sync direction description string (previously hand-built in two separate places) into a shared `_sync_direction_desc()` helper.

---

## v1.38 — Jul 15, 2026

- Remove menu: two new options.
  - 3rd option **"Duplicates by Fuzzy Name"** (grouped with the other Duplicates removals) — same close-name + close-size grouping as Find Duplicates by Fuzzy Name (shared `_fuzzy_dup_groups()` helper). The shortest/cleanest name in each group is kept; the rest are listed for removal. Hidden files skipped. Dry run + typed **YES** required to delete. CLI: `fm.py remove dup-fuzzy FOLDER... [--delete] [--yes]`.
  - 6th (last) option **"Files of 0 Size"** — lists every empty (0-byte) file under the entered folders for removal (incomplete downloads, placeholders, failed copies). Hidden files/folders skipped, so markers like `.gitkeep` are never touched. Standard dry-run + confirm. CLI: `fm.py remove zero-size FOLDER... [--delete] [--yes]`.
  - By File Name / By Folder Name renumbered to 4/5.
- README updated (overview, Remove menu table + notes, CLI usage/reference).

---

## v1.37 — Jul 15, 2026

- Find menu: new 4th option **"Find Duplicates by Fuzzy Name"** (right after Find Duplicates by Filename) — finds files whose **names are close** (not necessarily identical) **and whose sizes are close** (within 1%). Example: `videofile1.mov` and `videofile.mov` at the same size are duplicates, and `videofile1.mov` is the one flagged to delete.
  - Close names = same stem after stripping duplicate-style endings (trailing digits, `(1)`, `[2]`, `copy`, `copy 2`, `- Copy`) or 85%+ difflib similarity; the extension must match.
  - Matches are clustered into groups (largest files first). Each group marks the shortest/cleanest name **KEEP** and the rest **DELETE** — candidates only; read-only, nothing is deleted.
  - Summary line: group count, DELETE-candidate count, and total reclaimable bytes. Results log to `~/Documents/log/fm.log`; [R] Run Again supported.
  - Later Find options renumbered (Missing by Filename 5, Missing by Filename & Size 6, Find & Replace 7, Find & Rename 8).
  - CLI: `fm.py find-fuzzy-dups FOLDER...`
- README updated (overview, Find section with example output, activity-log table, CLI usage/reference).

---

## v1.36 — Jul 15, 2026

- Sync: new **two-way direction (A ↔ B)** — both folders push to each other in one run. Files only in A are copied to B, files only in B are copied to A, and when a file exists on both sides the copy that wins the conflict rule (newest/largest) replaces the other; ties are skipped. Still a DRY RUN preview first (grouped A → B and B → A sections) and nothing is ever deleted.
  - Interactive Sync: third Direction option "Two-way sync A ↔ B".
  - Profiles: `direction` now accepts `Both` (also `2way`/`twoway`); shown as "A ↔ B" in the Sync menu.
  - CLI: `fm.py sync A B --to both`.
- README updated (overview, profiles table, Sync section, CLI usage/options).

---

## v1.35 — Jul 15, 2026

- Sync: zero-byte source files are never copied (skipped with a "Skipped N zero-byte file(s)" note) so incomplete/placeholder 0-byte files can't overwrite good files on the destination side.

---

## v1.34 — Jul 14, 2026

- Main Menu labels: capitalized the first letter after the em-dash on all 11 options (e.g. "Compare  — compare 2 files…" → "Compare  — Compare 2 files…"). README overview block matched. Cosmetic only.

---

## v1.33 — Jul 14, 2026

- Main Menu reordered (per spec — no longer alphabetical): 1. Compare  2. Convert  3. Display  4. Find  5. Eject  6. Monitor  7. Sync  8. Zip  9. Remove  10. Create Random UID  11. Clean Up. Dispatch, [H] Help order, and the menu intro line updated to match; README overview block and usage sections reordered/renumbered the same way. No feature changes.

---

## v1.32 — Jul 14, 2026

- Find menu: new 7th (last) option "Find & Rename" — find files, then rename them. Enter a folder, an optional file extension, and a mode:
  - Prepend — text added to the start of the filename (text.mov -> api_text.mov); files already starting with the text are skipped, so reruns are safe.
  - Append — text inserted at the end of the name, before the extension (text.mov -> text_api.mov); files already ending with it are skipped.
  - Replace — literal, case-insensitive replacement inside the filename (draft_intro.mov -> final_intro.mov); blank replacement removes the text; only matching files are listed.
- ALWAYS a dry run first — every planned rename is listed old -> new before anything is touched. Renames that would overwrite an existing file (or collide with another rename in the same run) are skipped and reported; hidden/junk files are never touched. Results screens log to fm.log and offer [R] Run Again.
- New find_and_rename()/_find_rename_screen(). CLI: fm.py find-rename ROOT (--prepend TEXT | --append TEXT | --replace FIND NEW) [--ext E] [--apply] [--yes].

---

## v1.31 — Jul 14, 2026

- Main Menu: new "Create Random UID" option (3rd, keeping the menu alphabetical; Clean Up stays last) — enter a number N and get N random (version 4) UUIDs displayed one per line, capped at 10,000 per run. The list is appended to fm.log; [R] Run Again regenerates a fresh batch with the same count.
- New generate_uuids()/_uuid_screen()/create_random_uid_menu(). CLI: fm.py uuid [N] (default 1).

---

## v1.30 — Jul 14, 2026

- Main Menu: new "Convert" option (2nd, keeping the menu alphabetical; Clean Up stays last) — convert a data file between formats. Input: .csv (delimiter sniffed: , ; tab |; UTF-8 BOM tolerated), .json (array of objects → keys become headers in first-seen order, array of arrays with a header row, or a single object), or .xlsx (first sheet, first row = header; via openpyxl). Output: CSV (RFC-4180), JSON (pretty-printed array of objects), XLSX (openpyxl — the only format needing a package; if missing, a clear message says pip3 install openpyxl and everything else still works), or SQL.
- SQL output: CREATE TABLE named after the file with column types guessed per column (TINYINT(1) / INT / BIGINT / DECIMAL(m,d) / DATE / DATETIME / VARCHAR(n) / TEXT), then multi-row INSERTs in 500-row batches; empty cells become NULL, values escaped, identifiers sanitized and de-duplicated.
- The output file is written beside the source with the same name and new extension, collision-safe (name-2.ext, name-3.ext, …) — never overwrites. Short rows are padded and extra cells dropped (the header row defines the columns). Results screens log to fm.log and offer [R] Run Again.
- New convert_menu()/convert_file()/_read_table()/format writers/_unique_path(). CLI: fm.py convert FILE csv|json|xlsx|sql.

---

## v1.29 — Jul 14, 2026

- Find menu: new 6th (last) option "Find & Replace" — enter a folder, the text to find, the replacement text, and an optional file extension. Scans recursively (hidden/binary/excluded files skipped); matching is literal and case-insensitive. ALWAYS dry-runs first, listing every match as file + line number + line with the matched text highlighted, then a [y/N] confirm performs the replacement (with a follow-up prompt offering .bak backups of each modified file) — No exits unchanged. .bak files are skipped by the scan (so reruns never clobber fresh backups) unless --ext bak is asked for explicitly. Round-trips file bytes and line endings via surrogateescape + newline="".
- New find_and_replace()/_find_replace_screen(); results screens log to fm.log and offer [R] Run Again. CLI: fm.py find-replace ROOT SEARCH REPLACE [--ext E] [--apply] [--bak] [--yes].

---

## v1.28 — Jul 14, 2026

- Main Menu: new "Clean Up" option (9th — last, per spec). Submenu:
  1. Remove Junk Files — find and delete every .DS_Store / desktop.ini under a root folder (hidden folders included; reuses the Remove preview/confirm machinery).
  2. Purge Old Log Files — trim entries older than N days (default 90) from every .log file in ~/Documents/log (folder and days promptable), ported from purgeLog.sh but block-aware: untimestamped body lines follow their [YYYY-MM-DD HH:MM:SS] header's keep/purge decision, so whole entries purge together. Per-file purge/keep table preview; .bak backup before each rewrite.
- Both are DRY RUN until confirmed. CLI: fm.py cleanup junk ROOT [--delete] [--yes] and fm.py cleanup logs [FOLDER] [--days N] [--delete] [--yes].

---

## v1.27 — Jul 14, 2026

- Display menu is now: 1. All Drives  2. Subfolders Alphabetically  3. Subfolders by Size (largest first). New display_all_drives() lists the boot volume plus every mount under /Volumes (deduplicated by device) with Size / Used / Free / Use% and the mount point — Free comes from shutil.disk_usage so it matches Finder's Available; Use% colors yellow at 75% and red at 90%. CLI: fm.py drives.

---

## v1.26 — Jul 14, 2026

- Main Menu: new "Monitor" option (5th, keeping the menu alphabetical) — Monitor File Activity. Watches a folder (or a fmConfig.json monitorProfiles entry: name, folder, recursive, extensions, output) and reports every created/modified/deleted file in real time, on screen and to the chosen log: fm.log (plain timestamped lines) or ~/Documents/log/fmMonitor.csv (Timestamp,Filename,Folder,Event rows). Options: recursive (default Yes) and a file-extension filter. Stdlib polling (1s snapshot diffs — no watchdog dependency); events flush immediately so tail -f tracks the screen. [Q/ESC] stops and returns to the menu (Ctrl-C on the CLI). Ported from the standalone fileActivity.py idea. CLI: fm.py monitor FOLDER [--no-recursive] [--ext jpg,png] [--csv], or fm.py monitor --profile NAME.
- Refactored profile loading into _load_config_profiles(key), shared by syncProfiles and monitorProfiles.

---

## v1.25 — Jul 14, 2026

- Main Menu: new "Eject" option (3rd, keeping the menu alphabetical) — Eject All External Drives (macOS). Lists the mounted external drives (name, size, mount point), confirms, then ejects each with a per-drive Success/Failed status and offers a force eject for failures. Detection and eject logic ported from ejectDrives.py (diskutil info scan of /Volumes; diskutil eject with Finder/AppleScript fallback; force = diskutil unmountDisk force). Results are logged to fm.log. CLI: fm.py eject [--list] [--force] [--yes].

---

## v1.24 — Jul 14, 2026

- Main Menu: new "Sync" option (before Zip) — one-way folder sync pushing new/updated files A → B or B → A. Interactive flow asks for the two folders, the direction, the both-sides conflict rule (newest wins default / largest wins), recursive (default Yes), and exclude hidden files (default Yes). Saved profiles from fmConfig.json (syncProfiles list: name, folderA, folderB, direction, recursive, conflict, excludeHidden) appear as Sync menu options; the [H] Help documents the profile format.
- Every run previews (DRY RUN) and only copies after an explicit confirm; nothing is ever deleted; copies use shutil.copy2 so timestamps survive for future 'newest' runs. Results screens are logged to ~/Documents/log/fm.log. CLI: fm.py sync A B [--to b|a] [--conflict newest|largest] [--no-recursive] [--include-hidden] [--copy] [--yes], or fm.py sync --profile NAME.

---

## v1.23 — Jul 14, 2026

- Main Menu [H] Help: new unnumbered "Logging" section explaining that commands and their results screens are appended (timestamped, colors stripped) to the activity log ~/Documents/log/fm.log, which actions log there, and that Log Zip File records to CB9Inventory instead.
- render_menu()/_render_menu_lines() gained a help_note parameter and show_menu_help() a note parameter for such extra Help sections; the description wrapper was factored out into _print_help_desc().

---

## v1.22 — Jul 13, 2026

- Find menu: new 5th option "Find Missing by Filename & Size" — same flow as Find Missing by Filename, but files match only when BOTH the name AND the size agree, so same-named files with different sizes are also reported (size shown in both columns). CLI: find-missing --size.

---

## v1.21 — Jul 13, 2026

- Compare & Find results screens now end with "[R] Run Again  [Q/ESC] Quit/Back" instead of the plain Enter pause — R reruns the same action with the same inputs (fresh scan; Find Dup/Missing reruns re-log to fm.log). R/Q/ESC react instantly; Enter also goes back. New pause_rerun(); CLI one-shot runs are unchanged. Remove/Zip keep the plain pause.

---

## v1.20 — Jul 13, 2026

- .DS_Store and desktop.ini files (case-insensitive) are now also ignored by all searches and compares — every Find feature and Compare Folder Contents. Added EXCLUDED_FILE_NAMES + is_excluded_file(). Remove → By File Name still targets them intentionally (junk-file cleanup).

---

## v1.19 — Jul 13, 2026

- The Windows Recycle Bin folder ($RECYCLE.BIN, case-insensitive) is now excluded from all searches and compares: every Find feature (Files, Folders, Duplicates/Missing by Filename) and Compare Folder Contents (recursive and top-level). Added EXCLUDED_DIR_NAMES + prune_dirs().

---

## v1.18 — Jul 13, 2026

- Find Duplicates/Missing by Filename: the results screen is now also appended (ANSI-stripped, timestamped) to ~/Documents/log/fm.log via the new _ActivityLog stdout tee.
- Find Missing modes "In 1st/2nd folder only": added a last 'Folder' column showing the directory containing each file (_scan_filenames now records (size, dir) per occurrence).
- Find Missing: the Folder 1/2 list is repeated after the results table.

---

## v1.17 — Jul 13, 2026

- Find Missing by Filename — Show menu: the two entered folders are now displayed below the options as "Folder 1 - …" / "Folder 2 - …".
- render_menu()/_render_menu_lines() gained an `outro` parameter (context line(s) below the options), shared via _print_menu_outro().

---

## v1.16 — Jul 13, 2026

- Find menu: new 4th option "Find Missing by Filename" — enter two folders, then choose In 1st folder only / In 2nd folder only / In either folder (only once). Filenames present in only one folder are shown in the same size table as Find Duplicates by Filename (blank column = missing there).
- Refactored the folder scan + table renderer into _scan_filenames() / _print_filename_size_table() shared by both features; CLI: find-missing.

---

## v1.15 — Jul 13, 2026

- Find menu: new 3rd option "Find Duplicates by Filename" — enter one or more folders (comma-separated); files sharing the same name are shown in a table with a numbered header per folder and one size column per folder (multiple occurrences within one folder list each size). Read-only.
- Added find_duplicates_by_filename(), fmt_size_short(); CLI: find-dups.

---

## v1.14 — Jul 11, 2026

- Log Zip File now sends zipFileFolder (the archive's containing folder) so CB9Inventory records where each zip lives.

---

## v1.13 — Jul 11, 2026

- Zip menu: new 2nd option "Log Zip File" — logs a .zip/.tar archive (or every archive in a folder, top level only) to the CB9Inventory database on BPA5 via the DocInfo Manager API (api/zipFileLog.php). zipFile rows are matched by name+size (insert or update); zipFileContent is synced (update by path, insert new, soft-delete missing). .gz files are ignored.
- New fmConfig.json (logZip: apiUrl, serverSecretKey) + CLI: fm.py zip-log.

---

## v1.12 — Jul 9, 2026

- Remove → Duplicates (by Name / by Hash): deleting now requires typing the word YES (any other input cancels) — a stronger gate than the y/n used by the other removals. Added confirm_yes_word() + _finish_removal(require_yes).

---

## v1.11 — Jul 9, 2026

- Fixed: after selecting a menu option, a follow-up input prompt (e.g. "Folder to measure:") was printed on the same line as "Option:". The menu now emits a newline on selection so each new input request starts fresh.

---

## v1.10 — Jul 9, 2026

- Zip menu: "View Zip" is now the first option, "Zip SubFolders" second.

---

## v1.9 — Jul 9, 2026

- Expanded the [H] Help descriptions for every menu (Main, Compare, Compare-By, Display, Find, Remove, Zip) into full explanations with inputs, tips, and examples.
- show_menu_help() now word-wraps descriptions to the terminal width and supports multi-line / bulleted text with hanging indents.

---

## v1.8 — Jul 9, 2026

- Remove menu reordered/renamed: 1) Duplicates by Name, 2) Duplicates by Hash, 3) By File Name, 4) By Folder Name.
- New "By Folder Name": deletes folders whose name matches a wildcard under a search root (recursively); only top-most matches are removed. Dry-run by default. Added remove_folders_by_name() + CLI 'remove folder-name'.

---

## v1.7 — Jul 9, 2026

- Find: reworked into "Find Files" (multi-criteria) + "Find Folders". Find Files lets you multi-select any of Filename pattern / Extension / Size over N / Size under N (Space toggles), then prompts for each value and runs one combined AND search — e.g. .mov files under 5 MB.
- Added render_multiselect() (checkbox menu: ↑↓ move, Space toggle, Enter confirm) and find_files_combined(); new CLI: find-files [--name/--ext/--over/--under]. The old single-criterion `find` subcommand still works.

---

## v1.6 — Jul 9, 2026

- All menus now support Up/Down arrow navigation with a highlighted row; Enter selects the highlighted option (read_key + arrow loop in render_menu).
- Typing a number still selects (moves the highlight); H = Help, Q/ESC = Back/Exit — all instant. Non-TTY (piped/automation) keeps line-based selection.
- Zip-file browser reuses the same arrow-navigable menu.

---

## v1.5 — Jul 9, 2026

- Display (Folder Sizes): the Folder name is now the first column (was last), with a computed column width so rows, header, and TOTAL stay aligned.

---

## v1.4 — Jul 9, 2026

- Removed the copyright line from menu/result screens; it now appears only on the exit screen. Menu footers show just the separator bars + legend.

---

## v1.3 — Jul 9, 2026

- Replaced [B] Back with [Q/ESC] on every menu: on a submenu Q/ESC go back; on the Main Menu they exit.
- ESC now reacts INSTANTLY (no Enter needed) via a hybrid raw-mode reader (menu_read); digits/letters still buffer until Enter for multi-digit input.
- All submenus now default to option 1 — pressing Enter selects it.

---

## v1.2 — Jul 9, 2026

- Fixed: pasting a folder/file path that was wrapped in single or double quotes, or drag-and-dropped (backslash-escaped spaces), no longer errors.
- Added clean_path() which strips surrounding quotes and undoes backslash escapes; applied to every interactive prompt and CLI path argument.

---

## v1.1 — Jul 9, 2026

- Every menu/result screen now ends with the standard CB9 footer whose last line is the copyright notice.
- Submenus use a custom renderer: [H] Help shows a description of each option, and [Q/B] both return to the parent menu.
- Reworked the Compare submenu: "Compare 2 Files" — side-by-side, line-by-line file comparison; "Compare Folder Contents" — options Recursive (Y/N) and Compare By Name / Size / Both (both directions always reported).
- CLI: replaced compare-files/compare-folders with compare-2files and compare-contents [--recursive] [--by].

---

## v1.0 — Jul 9, 2026

- Initial version. Merges 9 legacy file-management scripts into one tool.
- Menu: Compare / Display / Find / Remove / Zip (with submenus).
- Built on CB9Lib (header, footer, menu, confirm, exit_screen, colors, project sounds).
- Remove actions are dry-run by default; deletion is explicit opt-in.
- Supports both an interactive menu and direct CLI subcommands.

---

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
