# File Management — Change Log

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
