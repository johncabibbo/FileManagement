# File Management — Change Log

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

- Zip menu: new 2nd option "Log Zip File" — logs a .zip/.tar archive (or every archive in a folder, top level only) to the CB9Inventory database on a remote server via the DocInfo Manager API (api/zipFileLog.php). zipFile rows are matched by name+size (insert or update); zipFileContent is synced (update by path, insert new, soft-delete missing). .gz files are ignored.
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
