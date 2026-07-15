#!/opt/homebrew/opt/python@3.12/libexec/bin/python3
#
# Filename: fm.py
# Project: File Management
# Version: 1.38
# Description: File Manager — a unified interactive + CLI tool that combines
#              the compare, display, eject, find, monitor, remove, sync, zip,
#              and clean-up file-management scripts into a single CB9Lib-based
#              program.
# Maintainer: Cloud Box 9 Inc.
# Last Modified Date: 2026-07-15
#
# Combines the functionality of:
#   compareFilesRecursive.sh, compareSubFolders.sh, folderSizes.sh,
#   findLargeFiles.sh, findDuplicates.sh, findDuplicatesExt.sh,
#   removeFiles.sh, zipSubFolders.sh, zipView.py
#
# Usage (interactive):
#   fm.py
#
# Usage (CLI):
#   fm.py compare-2files   FILE_A FILE_B
#   fm.py convert FILE csv|json|xlsx|sql   (convert a .csv/.json/.xlsx data file;
#                                           output written beside it, same name,
#                                           new extension, collision-safe)
#   fm.py uuid [N]                         (generate N random UUIDs, one per line)
#   fm.py compare-contents A B [--recursive] [--by name|size|both]
#   fm.py sizes [FOLDER] [--sort alpha|size]
#   fm.py drives                          (size and free space of all mounted drives)
#   fm.py find folder PATTERN [ROOT]
#   fm.py find name   PATTERN [ROOT]
#   fm.py find ext    EXT     [ROOT]
#   fm.py find over   N       [ROOT]      (N = megabytes)
#   fm.py find under  N       [ROOT]      (N = megabytes)
#   fm.py find-files [ROOT] [--name PAT] [--ext E] [--over N] [--under N]   (combined AND)
#   fm.py find-dups   FOLDER...           (duplicate filenames, size table per folder)
#   fm.py find-fuzzy-dups FOLDER...       (close-name + close-size duplicates,
#                                          grouped with KEEP/DELETE markers)
#   fm.py find-missing A B [--in first|second|either] [--size]   (filenames in only one
#                                          folder; --size also matches the file size)
#   fm.py find-replace ROOT SEARCH REPLACE [--ext E] [--apply] [--bak] [--yes]
#                                          (find & replace text in files; dry run
#                                           unless --apply)
#   fm.py find-rename ROOT (--prepend TEXT | --append TEXT | --replace FIND NEW)
#                     [--ext E] [--apply] [--yes]
#                                          (find files and rename them; dry run
#                                           unless --apply)
#   fm.py remove folder      PATH        [--delete] [--yes]
#   fm.py remove name        PATTERN ROOT [--delete] [--yes]   (files by name)
#   fm.py remove folder-name PATTERN ROOT [--delete] [--yes]   (folders by name)
#   fm.py remove dup-name    FOLDER...    [--delete] [--yes]
#   fm.py remove dup-hash    FOLDER...    [--delete] [--yes]
#   fm.py remove dup-fuzzy   FOLDER...    [--delete] [--yes]   (close name + close size)
#   fm.py remove zero-size   FOLDER...    [--delete] [--yes]   (empty 0-byte files)
#   fm.py eject [--list] [--force] [--yes]   (eject all external drives — macOS)
#   fm.py monitor FOLDER [--no-recursive] [--ext jpg,png] [--csv]   (Ctrl-C stops)
#   fm.py monitor --profile NAME          (run a monitorProfiles entry from fmConfig.json)
#   fm.py sync FOLDER_A FOLDER_B [--to b|a|both] [--conflict newest|largest]
#              [--no-recursive] [--include-hidden] [--copy] [--yes]
#   fm.py sync --profile NAME             (run a syncProfiles entry from fmConfig.json)
#   fm.py zip-subfolders  TARGET [DEST] [-r]
#   fm.py zip-view [ZIP|FOLDER]
#   fm.py zip-log  TARGET                 (log .zip/.tar to CB9Inventory)
#   fm.py cleanup junk ROOT [--delete] [--yes]        (.DS_Store / desktop.ini)
#   fm.py cleanup logs [FOLDER] [--days N] [--delete] [--yes]   (purge old log entries)
#
# NOTE: All Remove actions default to a DRY RUN (nothing is deleted). Deletion
#       only happens when explicitly opted-in (interactive confirm, or the
#       --delete flag on the CLI). Sync is the same: it previews and only
#       copies after explicit opt-in (interactive confirm, or --copy).
#
# -----------------------------------------------------------------------------
# Revision History:
# -----------------------------------------------------------------------------
# v1.38 (2026-07-15)
#   • Remove menu: two new options. 3rd option "Duplicates by Fuzzy Name"
#     (grouped with the other Duplicates removals) — same close-name +
#     close-size grouping as Find Duplicates by Fuzzy Name (shared
#     _fuzzy_dup_groups() helper, extracted from _find_fuzzy_dups_screen);
#     keeps the shortest/cleanest name per group, removes the rest. Typed
#     YES required to delete. 6th (last) option "Files of 0 Size" — lists
#     every empty (0-byte) file under the entered folders for removal;
#     hidden files/folders skipped (protects .gitkeep-style markers);
#     standard dry-run + confirm. By File Name / By Folder Name renumbered
#     to 4/5. New remove_duplicates_by_fuzzy_name(),
#     remove_zero_size_files(). CLI: fm.py remove dup-fuzzy FOLDER... and
#     fm.py remove zero-size FOLDER... [--delete] [--yes].
# -----------------------------------------------------------------------------
# v1.37 (2026-07-15)
#   • Find menu: new 4th option "Find Duplicates by Fuzzy Name" (after Find
#     Duplicates by Filename) — finds files whose names are CLOSE (not
#     necessarily identical) AND whose sizes are close (within 1%). Example:
#     videofile1.mov and videofile.mov at the same size are duplicates.
#     Close names = same stem after stripping duplicate-style endings
#     (trailing digits, "(1)", "[2]", "copy", "copy 2") or 85%+ difflib
#     similarity; extensions must match. Matches are clustered into groups;
#     each group marks the shortest/cleanest name KEEP and the rest DELETE
#     (candidates only — read-only, nothing is deleted). Groups sort largest
#     file first; summary shows group/candidate counts + reclaimable bytes.
#     New find_duplicates_by_fuzzy_name(), _find_fuzzy_dups_screen(),
#     _fuzzy_stem(), _names_close(), _sizes_close(). Later Find options
#     renumbered (Missing 5/6, Find & Replace 7, Find & Rename 8).
#     CLI: fm.py find-fuzzy-dups FOLDER...
# -----------------------------------------------------------------------------
# v1.36 (2026-07-15)
#   • Sync: new two-way direction (A ↔ B) — both folders push to each other in
#     one run. Files only in A are copied to B, files only in B are copied to
#     A, and when a file exists on both sides the copy that wins the conflict
#     rule (newest/largest) replaces the other; ties are skipped. Still a DRY
#     RUN preview first (grouped A → B and B → A sections) and nothing is ever
#     deleted. Interactive: third Direction option "Two-way sync A ↔ B".
#     Profiles: direction accepts Both (also 2way/twoway). CLI: --to both.
#     Added _parse_sync_direction(); _sync_screen now plans/copies in passes.
# -----------------------------------------------------------------------------
# v1.35 (2026-07-15)
#   • Sync: zero-byte source files are never copied (_sync_plan skips them and
#     reports a "Skipped N zero-byte file(s)" note instead). Prevents
#     incomplete/placeholder 0-byte files from overwriting good files on the
#     destination side.
# -----------------------------------------------------------------------------
# v1.34 (2026-07-14)
#   • Main Menu labels: capitalized the first letter after the em-dash on all
#     11 options (e.g. "Compare  — compare 2 files…" → "Compare  — Compare 2
#     files…"). README overview block matched. Cosmetic only.
# -----------------------------------------------------------------------------
# v1.33 (2026-07-14)
#   • Main Menu reordered (per spec — no longer alphabetical): 1. Compare
#     2. Convert  3. Display  4. Find  5. Eject  6. Monitor  7. Sync  8. Zip
#     9. Remove  10. Create Random UID  11. Clean Up. Dispatch, [H] Help
#     order, and the menu intro line updated to match; no feature changes.
# -----------------------------------------------------------------------------
# v1.32 (2026-07-14)
#   • Find menu: new 7th (last) option "Find & Rename" — find files, then
#     rename them. Enter a folder, an optional file extension, and a mode:
#     Prepend (text.mov -> api_text.mov; files already starting with the
#     text are skipped), Append (inserted before the extension:
#     text.mov -> text_api.mov; files already ending with it are skipped),
#     or Replace (literal case-insensitive replacement inside the filename;
#     blank replacement removes the text; only matching files are listed).
#     ALWAYS dry-runs first, listing every rename old -> new; renames that
#     would overwrite an existing file (or another rename in the same run)
#     are skipped and reported. Hidden/excluded files are never touched.
#     New find_and_rename()/_find_rename_screen(); results screens log to
#     fm.log and offer [R] Run Again. CLI: fm.py find-rename ROOT
#     (--prepend TEXT | --append TEXT | --replace FIND NEW) [--ext E]
#     [--apply] [--yes].
# -----------------------------------------------------------------------------
# v1.31 (2026-07-14)
#   • Main Menu: new "Create Random UID" option (3rd, keeping the menu
#     alphabetical; Clean Up stays last) — enter a number N and get N random
#     (version 4) UUIDs displayed one per line (capped at 10,000). The list
#     logs to fm.log; [R] Run Again regenerates a fresh batch with the same
#     count. New generate_uuids()/_uuid_screen()/create_random_uid_menu().
#     CLI: fm.py uuid [N] (default 1).
# -----------------------------------------------------------------------------
# v1.30 (2026-07-14)
#   • Main Menu: new "Convert" option (2nd, keeping the menu alphabetical;
#     Clean Up stays last) — convert a data file between formats. Input:
#     .csv (delimiter sniffed, BOM tolerated), .json (array of objects or
#     array of arrays), .xlsx (first sheet; via openpyxl). Output: CSV,
#     JSON (pretty-printed array of objects), XLSX (openpyxl — only format
#     needing a package; a clear message says pip3 install openpyxl if
#     missing), or SQL (CREATE TABLE named after the file with column types
#     guessed per column — TINYINT(1)/INT/BIGINT/DECIMAL/DATE/DATETIME/
#     VARCHAR(n)/TEXT — plus multi-row INSERTs in 500-row batches; empty
#     cells become NULL, identifiers sanitized + de-duplicated). Output is
#     written beside the source with the same name and new extension,
#     collision-safe (name-2.ext, …) — never overwrites. Results screens log
#     to fm.log and offer [R] Run Again. New convert_menu()/convert_file()/
#     _read_table()/writers/_unique_path(). CLI: fm.py convert FILE
#     csv|json|xlsx|sql.
# -----------------------------------------------------------------------------
# v1.29 (2026-07-14)
#   • Find menu: new 6th (last) option "Find & Replace" — enter a folder, the
#     text to find, the replacement text, and an optional file extension.
#     Scans recursively (hidden/binary/excluded files skipped); matching is
#     literal and case-insensitive. ALWAYS dry-runs first, listing every
#     match as file + line number + line with the matched text highlighted,
#     then a [y/N] confirm performs the replacement (with a follow-up prompt
#     offering .bak backups of each modified file) — No exits unchanged.
#     .bak files are skipped by the scan (so reruns never clobber fresh
#     backups) unless --ext bak is asked for explicitly.
#     Round-trips file bytes and line endings via surrogateescape +
#     newline="". New find_and_replace()/_find_replace_screen(); results
#     screens log to fm.log and offer [R] Run Again. CLI: fm.py find-replace
#     ROOT SEARCH REPLACE [--ext E] [--apply] [--bak] [--yes].
# -----------------------------------------------------------------------------
# v1.28 (2026-07-14)
#   • Main Menu: new "Clean Up" option (9th — last, per spec). Submenu:
#     1. Remove Junk Files — find and delete every .DS_Store / desktop.ini
#     under a root folder (hidden folders included; reuses the Remove
#     preview/confirm machinery). 2. Purge Old Log Files — trim entries older
#     than N days (default 90) from every .log file in ~/Documents/log
#     (folder and days promptable), ported from purgeLog.sh but block-aware:
#     untimestamped body lines follow their [YYYY-MM-DD HH:MM:SS] header's
#     keep/purge decision, so whole entries purge together. Per-file
#     purge/keep table preview; .bak backup before each rewrite. Both are
#     DRY RUN until confirmed. CLI: fm.py cleanup junk ROOT [--delete]
#     [--yes] and fm.py cleanup logs [FOLDER] [--days N] [--delete] [--yes].
# -----------------------------------------------------------------------------
# v1.27 (2026-07-14)
#   • Display menu is now: 1. All Drives  2. Subfolders Alphabetically
#     3. Subfolders by Size (largest first). New display_all_drives() lists
#     the boot volume plus every mount under /Volumes (deduplicated by
#     device) with Size / Used / Free / Use% and the mount point — Free comes
#     from shutil.disk_usage so it matches Finder's Available; Use% colors
#     yellow at 75% and red at 90%. CLI: fm.py drives.
# -----------------------------------------------------------------------------
# v1.26 (2026-07-14)
#   • Main Menu: new "Monitor" option (5th, keeping the menu alphabetical) —
#     Monitor File Activity. Watches a folder (or a fmConfig.json
#     monitorProfiles entry: name, folder, recursive, extensions, output) and
#     reports every created/modified/deleted file in real time, on screen and
#     to the chosen log: fm.log (plain timestamped lines) or
#     ~/Documents/log/fmMonitor.csv (Timestamp,Filename,Folder,Event rows).
#     Options: recursive (default Yes) and a file-extension filter. Stdlib
#     polling (1s snapshot diffs — no watchdog dependency); events flush
#     immediately so tail -f tracks the screen. [Q/ESC] stops and returns to
#     the menu (Ctrl-C on the CLI). Ported from the standalone
#     fileActivity.py idea. CLI: fm.py monitor FOLDER [--no-recursive]
#     [--ext jpg,png] [--csv], or fm.py monitor --profile NAME.
#   • Refactored profile loading into _load_config_profiles(key), shared by
#     syncProfiles and monitorProfiles.
# -----------------------------------------------------------------------------
# v1.25 (2026-07-14)
#   • Main Menu: new "Eject" option (3rd, keeping the menu alphabetical) —
#     Eject All External Drives (macOS). Lists the mounted external drives
#     (name, size, mount point), confirms, then ejects each with a per-drive
#     Success/Failed status and offers a force eject for failures. Detection
#     and eject logic ported from ejectDrives.py (diskutil info scan of
#     /Volumes; diskutil eject with Finder/AppleScript fallback; force =
#     diskutil unmountDisk force). Results are logged to fm.log. CLI:
#     fm.py eject [--list] [--force] [--yes].
# -----------------------------------------------------------------------------
# v1.24 (2026-07-14)
#   • Main Menu: new "Sync" option (before Zip) — one-way folder sync pushing
#     new/updated files A → B or B → A. Interactive flow asks for the two
#     folders, the direction, the both-sides conflict rule (newest wins
#     default / largest wins), recursive (default Yes), and exclude hidden
#     files (default Yes). Saved profiles from fmConfig.json (syncProfiles
#     list: name, folderA, folderB, direction, recursive, conflict,
#     excludeHidden) appear as Sync menu options; the [H] Help documents the
#     profile format. Every run previews (DRY RUN) and only copies after an
#     explicit confirm; nothing is ever deleted; copies use shutil.copy2 so
#     timestamps survive for future 'newest' runs. Results screens are logged
#     to ~/Documents/log/fm.log. CLI: fm.py sync A B [--to b|a] [--conflict
#     newest|largest] [--no-recursive] [--include-hidden] [--copy] [--yes],
#     or fm.py sync --profile NAME.
# -----------------------------------------------------------------------------
# v1.23 (2026-07-14)
#   • Main Menu [H] Help: new unnumbered "Logging" section explaining that
#     commands and their results screens are appended (timestamped, colors
#     stripped) to the activity log ~/Documents/log/fm.log, which actions log
#     there, and that Log Zip File records to CB9Inventory instead.
#   • render_menu()/_render_menu_lines() gained a help_note parameter and
#     show_menu_help() a note parameter for such extra Help sections; the
#     description wrapper was factored out into _print_help_desc().
# -----------------------------------------------------------------------------
# v1.22 (2026-07-13)
#   • Find menu: new 5th option "Find Missing by Filename & Size" — same flow
#     as Find Missing by Filename, but files match only when BOTH the name AND
#     the size agree, so same-named files with different sizes are also
#     reported (size shown in both columns). CLI: find-missing --size.
# -----------------------------------------------------------------------------
# v1.21 (2026-07-13)
#   • Compare & Find results screens now end with "[R] Run Again  [Q/ESC]
#     Quit/Back" instead of the plain Enter pause — R reruns the same action
#     with the same inputs (fresh scan; Find Dup/Missing reruns re-log to
#     fm.log). R/Q/ESC react instantly; Enter also goes back. New pause_rerun();
#     CLI one-shot runs are unchanged. Remove/Zip keep the plain pause.
# -----------------------------------------------------------------------------
# v1.20 (2026-07-13)
#   • .DS_Store and desktop.ini files (case-insensitive) are now also ignored
#     by all searches and compares — every Find feature and Compare Folder
#     Contents. Added EXCLUDED_FILE_NAMES + is_excluded_file(). Remove → By
#     File Name still targets them intentionally (junk-file cleanup).
# -----------------------------------------------------------------------------
# v1.19 (2026-07-13)
#   • The Windows Recycle Bin folder ($RECYCLE.BIN, case-insensitive) is now
#     excluded from all searches and compares: every Find feature (Files,
#     Folders, Duplicates/Missing by Filename) and Compare Folder Contents
#     (recursive and top-level). Added EXCLUDED_DIR_NAMES + prune_dirs().
# -----------------------------------------------------------------------------
# v1.18 (2026-07-13)
#   • Find Duplicates/Missing by Filename: the results screen is now also
#     appended (ANSI-stripped, timestamped) to ~/Documents/log/fm.log via the
#     new _ActivityLog stdout tee.
#   • Find Missing modes "In 1st/2nd folder only": added a last 'Folder'
#     column showing the directory containing each file (_scan_filenames now
#     records (size, dir) per occurrence).
#   • Find Missing: the Folder 1/2 list is repeated after the results table.
# -----------------------------------------------------------------------------
# v1.17 (2026-07-13)
#   • Find Missing by Filename — Show menu: the two entered folders are now
#     displayed below the options as "Folder 1 - …" / "Folder 2 - …".
#   • render_menu()/_render_menu_lines() gained an `outro` parameter (context
#     line(s) below the options), shared via _print_menu_outro().
# -----------------------------------------------------------------------------
# v1.16 (2026-07-13)
#   • Find menu: new 4th option "Find Missing by Filename" — enter two folders,
#     then choose In 1st folder only / In 2nd folder only / In either folder
#     (only once). Filenames present in only one folder are shown in the same
#     size table as Find Duplicates by Filename (blank column = missing there).
#   • Refactored the folder scan + table renderer into _scan_filenames() /
#     _print_filename_size_table() shared by both features; CLI: find-missing.
# -----------------------------------------------------------------------------
# v1.15 (2026-07-13)
#   • Find menu: new 3rd option "Find Duplicates by Filename" — enter one or
#     more folders (comma-separated); files sharing the same name are shown in
#     a table with a numbered header per folder and one size column per folder
#     (multiple occurrences within one folder list each size). Read-only.
#   • Added find_duplicates_by_filename(), fmt_size_short(); CLI: find-dups.
# -----------------------------------------------------------------------------
# v1.14 (2026-07-11)
#   • Log Zip File now sends zipFileFolder (the archive's containing folder)
#     so CB9Inventory records where each zip lives.
# -----------------------------------------------------------------------------
# v1.13 (2026-07-11)
#   • Zip menu: new 2nd option "Log Zip File" — logs a .zip/.tar archive (or
#     every archive in a folder, top level only) to the CB9Inventory database
#     on BPA5 via the DocInfo Manager API (api/zipFileLog.php). zipFile rows
#     are matched by name+size (insert or update); zipFileContent is synced
#     (update by path, insert new, soft-delete missing). .gz files are ignored.
#   • New fmConfig.json (logZip: apiUrl, serverSecretKey) + CLI: fm.py zip-log.
# -----------------------------------------------------------------------------
# v1.12 (2026-07-09)
#   • Remove → Duplicates (by Name / by Hash): deleting now requires typing the
#     word YES (any other input cancels) — a stronger gate than the y/n used by
#     the other removals. Added confirm_yes_word() + _finish_removal(require_yes).
# -----------------------------------------------------------------------------
# v1.11 (2026-07-09)
#   • Fixed: after selecting a menu option, a follow-up input prompt (e.g.
#     "Folder to measure:") was printed on the same line as "Option:". The menu
#     now emits a newline on selection so each new input request starts fresh.
# -----------------------------------------------------------------------------
# v1.10 (2026-07-09)
#   • Zip menu: "View Zip" is now the first option, "Zip SubFolders" second.
# -----------------------------------------------------------------------------
# v1.9 (2026-07-09)
#   • Expanded the [H] Help descriptions for every menu (Main, Compare, Compare-
#     By, Display, Find, Remove, Zip) into full explanations with inputs, tips,
#     and examples.
#   • show_menu_help() now word-wraps descriptions to the terminal width and
#     supports multi-line / bulleted text with hanging indents.
# -----------------------------------------------------------------------------
# v1.8 (2026-07-09)
#   • Remove menu reordered/renamed: 1) Duplicates by Name, 2) Duplicates by
#     Hash, 3) By File Name, 4) By Folder Name.
#   • New "By Folder Name": deletes folders whose name matches a wildcard under a
#     search root (recursively); only top-most matches are removed. Dry-run by
#     default. Added remove_folders_by_name() + CLI 'remove folder-name'.
# -----------------------------------------------------------------------------
# v1.7 (2026-07-09)
#   • Find: reworked into "Find Files" (multi-criteria) + "Find Folders".
#     Find Files lets you multi-select any of Filename pattern / Extension /
#     Size over N / Size under N (Space toggles), then prompts for each value and
#     runs one combined AND search — e.g. .mov files under 5 MB.
#   • Added render_multiselect() (checkbox menu: ↑↓ move, Space toggle, Enter
#     confirm) and find_files_combined(); new CLI: find-files [--name/--ext/
#     --over/--under]. The old single-criterion `find` subcommand still works.
# -----------------------------------------------------------------------------
# v1.6 (2026-07-09)
#   • All menus now support Up/Down arrow navigation with a highlighted row;
#     Enter selects the highlighted option (read_key + arrow loop in render_menu).
#   • Typing a number still selects (moves the highlight); H = Help, Q/ESC = Back/
#     Exit — all instant. Non-TTY (piped/automation) keeps line-based selection.
#   • Zip-file browser reuses the same arrow-navigable menu.
# -----------------------------------------------------------------------------
# v1.5 (2026-07-09)
#   • Display (Folder Sizes): the Folder name is now the first column (was last),
#     with a computed column width so rows, header, and TOTAL stay aligned.
# -----------------------------------------------------------------------------
# v1.4 (2026-07-09)
#   • Removed the copyright line from menu/result screens; it now appears only
#     on the exit screen. Menu footers show just the separator bars + legend.
# -----------------------------------------------------------------------------
# v1.3 (2026-07-09)
#   • Replaced [B] Back with [Q/ESC] on every menu: on a submenu Q/ESC go back;
#     on the Main Menu they exit.
#   • ESC now reacts INSTANTLY (no Enter needed) via a hybrid raw-mode reader
#     (menu_read); digits/letters still buffer until Enter for multi-digit input.
#   • All submenus now default to option 1 — pressing Enter selects it.
# -----------------------------------------------------------------------------
# v1.2 (2026-07-09)
#   • Fixed: pasting a folder/file path that was wrapped in single or double
#     quotes, or drag-and-dropped (backslash-escaped spaces), no longer errors.
#   • Added clean_path() which strips surrounding quotes and undoes backslash
#     escapes; applied to every interactive prompt and CLI path argument.
# -----------------------------------------------------------------------------
# v1.1 (2026-07-09)
#   • Every menu/result screen now ends with the standard CB9 footer whose last
#     line is the copyright notice.
#   • Submenus use a custom renderer: [H] Help shows a description of each
#     option, and [Q/B] both return to the parent menu.
#   • Reworked the Compare submenu:
#       - "Compare 2 Files" — side-by-side, line-by-line file comparison.
#       - "Compare Folder Contents" — options Recursive (Y/N) and
#         Compare By Name / Size / Both (both directions always reported).
#   • CLI: replaced compare-files/compare-folders with compare-2files and
#     compare-contents [--recursive] [--by].
# -----------------------------------------------------------------------------
# v1.0 (2026-07-09)
#   • Initial version. Merges 9 legacy file-management scripts into one tool.
#   • Menu: Compare / Display / Find / Remove / Zip (with submenus).
#   • Built on CB9Lib (header, footer, menu, confirm, exit_screen, colors,
#     project sounds).
#   • Remove actions are dry-run by default; deletion is explicit opt-in.
#   • Supports both an interactive menu and direct CLI subcommands.
# -----------------------------------------------------------------------------

import sys
import os
import argparse
import csv
import time
import zipfile
import tarfile
import hashlib
import fnmatch
import subprocess
import shutil
import difflib
import re
import textwrap
import json
import uuid
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict

# CB9Lib imports
sys.path.insert(0, os.path.expanduser("~/Documents/script/CB9Lib"))
from CB9Lib import (
    header, exit_screen, confirm, pause, clear_screen,
    get_width, color_text, get_project_sound, play_sound,
    RED, GREEN, YELLOW, CYAN, MAGENTA, WHITE, BOLD, DIM, RESET,
    BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_RED,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
SCRIPT_NAME = "File Manager"
VERSION     = "1.38"
VER         = f"v{VERSION}"

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
SOUND_SUCCESS = os.path.join(SCRIPT_DIR, "audio", "success.mp3")
SOUND_FAILURE = os.path.join(SCRIPT_DIR, "audio", "failure.wav")

# True when driven by the interactive menu; False for one-shot CLI subcommands.
# Controls whether end-of-task screens pause for a keypress.
INTERACTIVE = True


# -----------------------------------------------------------------------------
# Small display helpers
# -----------------------------------------------------------------------------
def bar(char="="):
    return char * get_width()


def screen(subtitle=""):
    """Clear + standard CB9 header for a full-screen action view."""
    header(SCRIPT_NAME, VER, subtitle)


def standard_footer(legend=""):
    """Draw the standard footer.

    Layout:
        =====================================
         <legend>                       (only if a legend was supplied)
        =====================================

    The copyright notice is intentionally NOT shown on menus/result screens —
    it appears only on the exit screen (see exit_screen()).
    """
    print(bar("="))
    if legend:
        print(color_text(" " + legend, fg=BRIGHT_YELLOW))
        print(bar("="))


def pause_return():
    """Standard end-of-task footer + pause (returns to the calling menu).
    In one-shot CLI mode there is no menu to return to, so draw the footer
    and continue without blocking on a keypress."""
    print()
    standard_footer()
    if not INTERACTIVE:
        return
    try:
        pause("Press Enter to return to the menu...")
    except EOFError:
        pass


def pause_rerun():
    """End-of-task footer for Compare/Find screens offering to rerun the same
    action with the same inputs.

    Returns True when the user chooses [R] Run Again, False to go back.
    [R], [Q], and ESC react instantly; Enter also goes back. In one-shot CLI
    mode there is no menu/rerun loop — draw the plain footer and return False.
    """
    print()
    if not INTERACTIVE:
        standard_footer()
        return False
    standard_footer("[R] Run Again   [Q/ESC] Quit/Back")
    sys.stdout.write(color_text(" Option: ", fg=CYAN, style=BOLD))
    sys.stdout.flush()
    if sys.stdin.isatty():
        while True:
            key = read_key()
            if key in ("r", "R"):
                print()
                return True
            if key in ("q", "Q", "ESC", "ENTER"):
                print()
                return False
            # anything else: ignore
    # Non-TTY (piped) fallback — line-based
    try:
        resp = sys.stdin.readline()
    except Exception:
        return False
    return resp.strip().lower() == "r"


ACTIVITY_LOG = os.path.expanduser("~/Documents/log/fm.log")


class _ActivityLog:
    """Context manager that mirrors everything printed to stdout into the FM
    activity log (~/Documents/log/fm.log). The screen keeps its colors; the
    log entry is written with all ANSI escape codes stripped, prefixed with a
    timestamp line. Logging failures never interrupt the on-screen output."""

    def __init__(self):
        self._buf = []
        self._stdout = None

    # file-like proxy -------------------------------------------------------
    def write(self, s):
        self._stdout.write(s)
        self._buf.append(s)

    def flush(self):
        self._stdout.flush()

    def isatty(self):
        return self._stdout.isatty()

    # context manager -------------------------------------------------------
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.stdout = self._stdout
        text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", "".join(self._buf))
        try:
            os.makedirs(os.path.dirname(ACTIVITY_LOG), exist_ok=True)
            with open(ACTIVITY_LOG, "a") as fh:
                fh.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                fh.write(text.lstrip("\n"))
                if not text.endswith("\n"):
                    fh.write("\n")
                fh.write("\n")
        except OSError:
            pass
        return False


def safe_confirm(prompt, default=False):
    """confirm() that treats a closed stdin (EOF) as the default answer,
    so a piped/non-interactive delete never blocks or crashes."""
    try:
        return confirm(prompt, default=default)
    except EOFError:
        return default


def report_result(ok, ok_msg, fail_msg=""):
    """Show a success/failure line and play the matching project sound."""
    if ok:
        print(color_text(f"  ✓ {ok_msg}", fg=BRIGHT_GREEN, style=BOLD))
        play_sound(get_project_sound(SCRIPT_NAME, "successAudio", SOUND_SUCCESS))
    else:
        print(color_text(f"  ✗ {fail_msg or ok_msg}", fg=BRIGHT_RED, style=BOLD))
        play_sound(get_project_sound(SCRIPT_NAME, "failureAudio", SOUND_FAILURE))


def fmt_size(n):
    """Human-readable byte size."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{int(n):,} B" if unit == "B" else f"{n:,.1f} {unit}"
        n /= 1024


def fmt_size_short(n):
    """Compact byte size for tight table cells (e.g. 512B, 1.1K, 2.2M)."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{int(n)}B" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


def fmt_commas(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def fmt_date(dt):
    try:
        return dt.strftime("%b %-d, %Y %-I:%M %p").replace("AM", "am").replace("PM", "pm")
    except Exception:
        return "—"


def ask(label, default=""):
    """Prompt for a line of input with an optional default."""
    suffix = f" {DIM}[{default}]{RESET}" if default else ""
    val = input(color_text(f"  {label}", fg=CYAN) + suffix + ": ").strip()
    return val if val else default


def clean_path(raw):
    """Normalize a path the user typed or pasted, then expand ~.

    Handles the common ways a path arrives with extra characters:
      • wrapped in matching single/double quotes  →  '/My Drive/x'  "…"
      • drag-and-dropped from the terminal, which backslash-escapes spaces
        and other characters  →  /My\\ Drive/x
    A plain path (even one containing spaces) is left untouched. Backslash
    escapes are only undone if doing so points at something that exists, so a
    legitimate backslash in a name is preserved.
    """
    if raw is None:
        return ""
    s = raw.strip()
    # Strip one layer of surrounding matching quotes (copy/paste)
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1]
    expanded = os.path.expanduser(s)
    if os.path.exists(expanded):
        return expanded
    # Undo shell-style backslash escapes (terminal drag-and-drop) and retry
    unescaped = os.path.expanduser(re.sub(r"\\(.)", r"\1", s))
    if os.path.exists(unescaped):
        return unescaped
    # Nothing resolved — return the quote-stripped, expanded form for the error
    return expanded


def ask_folder(label="Folder", default="", must_exist=True):
    """Prompt for a folder path (cleans quotes/escapes, expands ~)."""
    raw = ask(label, default)
    if not raw:
        print(color_text("  No path entered.", fg=YELLOW))
        return None
    path = clean_path(raw)
    if must_exist and not os.path.isdir(path):
        print(color_text(f"  Not a directory: {path}", fg=RED))
        return None
    return path


def ask_file(label="File", default=""):
    """Prompt for a file path (cleans quotes/escapes, expands ~)."""
    raw = ask(label, default)
    if not raw:
        print(color_text("  No path entered.", fg=YELLOW))
        return None
    path = clean_path(raw)
    if not os.path.isfile(path):
        print(color_text(f"  Not a file: {path}", fg=RED))
        return None
    return path


def is_hidden(rel):
    """True if any path component starts with '.'"""
    return any(part.startswith(".") for part in rel.replace("\\", "/").split("/") if part)


# Folder/file names always excluded from searches and compares (case-insensitive).
EXCLUDED_DIR_NAMES  = {"$recycle.bin"}
EXCLUDED_FILE_NAMES = {".ds_store", "desktop.ini"}


def prune_dirs(dns):
    """In-place filter for an os.walk() dir list: drop excluded folders
    (e.g. the Windows $RECYCLE.BIN on external drives) so they are neither
    matched nor descended into."""
    dns[:] = [d for d in dns if d.lower() not in EXCLUDED_DIR_NAMES]
    return dns


def is_excluded_file(fn):
    """True for junk files ignored by searches and compares (.DS_Store,
    desktop.ini)."""
    return fn.lower() in EXCLUDED_FILE_NAMES


# -----------------------------------------------------------------------------
# Filesystem scanning helpers
# -----------------------------------------------------------------------------
def rel_files(root):
    """Set of relative file paths under root, excluding hidden files/folders
    and excluded names ($RECYCLE.BIN, .DS_Store, desktop.ini)."""
    out = set()
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".") and d.lower() not in EXCLUDED_DIR_NAMES]
        for fn in fns:
            if fn.startswith(".") or is_excluded_file(fn):
                continue
            out.add(os.path.relpath(os.path.join(dp, fn), root))
    return out


def immediate_subfolders(root):
    """Sorted list of immediate, non-hidden subfolder names."""
    try:
        return sorted(
            d for d in os.listdir(root)
            if not d.startswith(".") and os.path.isdir(os.path.join(root, d))
        )
    except OSError:
        return []


def folder_stats(path):
    """Return (total_bytes, file_count) for everything under path."""
    total = 0
    count = 0
    for dp, dns, fns in os.walk(path):
        for fn in fns:
            try:
                total += os.path.getsize(os.path.join(dp, fn))
                count += 1
            except OSError:
                pass
    return total, count


def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


# =============================================================================
# COMPARE
# =============================================================================
def _read_lines(path):
    """Read a text file into a list of lines (best-effort, never raises)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError as e:
        print(color_text(f"  Cannot read {path}: {e}", fg=RED))
        return None


def _sbs_row(num, left, right, mark, col, color):
    """Print one side-by-side row: line# | left | mark | right."""
    l = left[:col].ljust(col)
    r = right[:col]
    n = f"{num:>4}" if num else "    "
    print(f"{DIM}{n}{RESET} {color}{l}{RESET} {color}{mark}{RESET} {color}{r}{RESET}")


def compare_two_files(file_a, file_b):
    """Compare two files and display them side by side, line by line.

    Markers:  =  equal    ≠  changed    <  only in A    >  only in B
    """
    screen("Compare 2 Files")
    print()
    if not (os.path.isfile(file_a) and os.path.isfile(file_b)):
        print(color_text("  Both paths must be existing files.", fg=RED))
        pause_return()
        return

    a_lines = _read_lines(file_a)
    b_lines = _read_lines(file_b)
    if a_lines is None or b_lines is None:
        pause_return()
        return

    w = get_width()
    col = max((w - 9) // 2, 20)   # two columns + line#(4) + marker gutters

    print(f"  {YELLOW}A{RESET}: {file_a}  {DIM}({len(a_lines)} lines, {fmt_size(file_size(file_a))}){RESET}")
    print(f"  {YELLOW}B{RESET}: {file_b}  {DIM}({len(b_lines)} lines, {fmt_size(file_size(file_b))}){RESET}")
    print()
    print(color_text(f"  {'#':>3} {os.path.basename(file_a)[:col]:<{col}}   {os.path.basename(file_b)[:col]}",
                     fg=WHITE, style=BOLD))
    print(f"  {DIM}{'-' * min(col * 2 + 8, w - 2)}{RESET}")

    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    same = changed = only_a = only_b = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                _sbs_row(i1 + k + 1, a_lines[i1 + k], b_lines[j1 + k], "=", col, WHITE)
                same += 1
        elif tag == "replace":
            la, lb = a_lines[i1:i2], b_lines[j1:j2]
            for k in range(max(len(la), len(lb))):
                left = la[k] if k < len(la) else ""
                right = lb[k] if k < len(lb) else ""
                _sbs_row((i1 + k + 1) if k < len(la) else 0, left, right, "≠", col, YELLOW)
                changed += 1
        elif tag == "delete":
            for k in range(i1, i2):
                _sbs_row(k + 1, a_lines[k], "", "<", col, RED)
                only_a += 1
        elif tag == "insert":
            for k in range(j1, j2):
                _sbs_row(0, "", b_lines[k], ">", col, GREEN)
                only_b += 1

    print(f"  {DIM}{'-' * min(col * 2 + 8, w - 2)}{RESET}")
    if changed == only_a == only_b == 0:
        report_result(True, "Files are identical.")
    else:
        print(color_text(
            f"  {same} equal · {changed} changed · {only_a} only in A · {only_b} only in B",
            fg=BRIGHT_CYAN, style=BOLD))
        report_result(False, "", "Files differ.")
    if pause_rerun():
        compare_two_files(file_a, file_b)


def compare_folder_contents(folder_a, folder_b, recursive=True, by="both"):
    """Compare the contents of two folders.

    recursive: True  -> every file beneath each folder (relative paths)
               False -> only the immediate entries (files AND subfolders)
    by:        name -> entries present in one folder but not the other
               size -> entries in both whose size differs
               both -> both reports
    Hidden files/folders (leading '.') are ignored.
    """
    screen("Compare Folder Contents")
    print()
    print(f"  {YELLOW}A{RESET}: {folder_a}")
    print(f"  {YELLOW}B{RESET}: {folder_b}")
    print(f"  {YELLOW}Recursive{RESET}: {'Yes' if recursive else 'No'}    {YELLOW}Compare by{RESET}: {by}")
    print()

    if not (os.path.isdir(folder_a) and os.path.isdir(folder_b)):
        print(color_text("  Both paths must be directories.", fg=RED))
        pause_return()
        return

    if recursive:
        set_a, set_b = rel_files(folder_a), rel_files(folder_b)
    else:
        def entries(root):
            try:
                return {e for e in os.listdir(root)
                        if not e.startswith(".") and e.lower() not in EXCLUDED_DIR_NAMES
                        and not is_excluded_file(e)}
            except OSError:
                return set()
        set_a, set_b = entries(folder_a), entries(folder_b)

    def size_of(root, rel):
        p = os.path.join(root, rel)
        if os.path.isdir(p):
            total, _ = folder_stats(p)
            return total
        return file_size(p)

    if by in ("name", "both"):
        only_a = sorted(set_a - set_b)
        print(color_text(f"  In A but not in B ({len(only_a)}):", fg=BRIGHT_CYAN, style=BOLD))
        for rel in only_a:
            print(f"    {rel}")
        if not only_a:
            print(f"    {DIM}(none){RESET}")
        print()
        only_b = sorted(set_b - set_a)
        print(color_text(f"  In B but not in A ({len(only_b)}):", fg=BRIGHT_CYAN, style=BOLD))
        for rel in only_b:
            print(f"    {rel}")
        if not only_b:
            print(f"    {DIM}(none){RESET}")
        print()

    if by in ("size", "both"):
        common = sorted(set_a & set_b)
        diffs = []
        for rel in common:
            sa = size_of(folder_a, rel)
            sb = size_of(folder_b, rel)
            if sa != sb:
                diffs.append((rel, sa, sb))
        print(color_text(f"  In both but differing in size ({len(diffs)}):", fg=BRIGHT_CYAN, style=BOLD))
        for rel, sa, sb in diffs:
            print(f"    {rel}  {DIM}(A: {fmt_size(sa)}, B: {fmt_size(sb)}){RESET}")
        if not diffs:
            print(f"    {DIM}(none){RESET}")

    if pause_rerun():
        compare_folder_contents(folder_a, folder_b, recursive, by)


# =============================================================================
# DISPLAY — Folder Sizes
# =============================================================================
def display_folder_sizes(folder, sort_mode="alpha"):
    screen("Folder Sizes")
    print()
    print(f"  {YELLOW}Folder{RESET}: {folder}")
    print(f"  {YELLOW}Sort{RESET}: {'By Size (largest first)' if sort_mode == 'size' else 'Alphabetical'}")
    print()

    if not os.path.isdir(folder):
        print(color_text(f"  Not a directory: {folder}", fg=RED))
        pause_return()
        return

    subs = immediate_subfolders(folder)
    rows = []
    for name in subs:
        total, count = folder_stats(os.path.join(folder, name))
        rows.append((total, count, name))

    if sort_mode == "size":
        rows.sort(key=lambda r: r[0], reverse=True)
    else:
        rows.sort(key=lambda r: r[2].lower())

    # Folder is always the first column. Size it to the longest name (capped),
    # also accounting for the header and the TOTAL label so everything aligns.
    total_label = f"TOTAL ({len(rows)} folders)"
    name_w = max([len(n) for (_, _, n) in rows] + [len("Folder"), len(total_label)])
    name_w = min(name_w, 50)

    print(color_text(f"  {'Folder':<{name_w}}  {'Size':>10}  {'Bytes':>18}  {'Files':>9}", fg=YELLOW, style=BOLD))
    print(f"  {DIM}{'-'*name_w}  {'-'*10}  {'-'*18}  {'-'*9}{RESET}")

    grand_bytes = 0
    grand_files = 0
    for total, count, name in rows:
        grand_bytes += total
        grand_files += count
        disp = name[:name_w].ljust(name_w)
        print(f"  {WHITE}{disp}{RESET}  {GREEN}{fmt_size(total):>10}{RESET}  {fmt_commas(total):>18}  {count:>9,}")

    if not rows:
        print(f"    {DIM}(no subfolders){RESET}")
    else:
        print(f"  {DIM}{'-'*name_w}  {'-'*10}  {'-'*18}  {'-'*9}{RESET}")
        print(f"  {BOLD}{total_label[:name_w].ljust(name_w)}  {fmt_size(grand_bytes):>10}  {fmt_commas(grand_bytes):>18}  {grand_files:>9,}{RESET}")

    pause_return()


def display_all_drives():
    """List every mounted drive — the boot volume plus each drive under
    /Volumes — with its total size, used and free space, and use%. Free is
    what shutil.disk_usage reports as available to the user, so it matches
    Finder's Available figure. Duplicate mounts of the same device are
    listed once."""
    screen("All Drives")
    print()

    candidates = ["/"]
    volumes = "/Volumes"
    if os.path.isdir(volumes):
        for name in sorted(os.listdir(volumes), key=str.lower):
            path = os.path.join(volumes, name)
            if os.path.ismount(path):
                candidates.append(path)

    rows = []
    seen_devices = set()
    for path in candidates:
        try:
            dev = os.stat(path).st_dev
            usage = shutil.disk_usage(path)
        except OSError:
            continue
        if dev in seen_devices:
            continue
        seen_devices.add(dev)
        name = "/" if path == "/" else os.path.basename(path)
        pct = (usage.used / usage.total * 100) if usage.total else 0
        rows.append((name, path, usage.total, usage.used, usage.free, pct))

    if not rows:
        print(color_text("  No drives found.", fg=YELLOW))
        pause_return()
        return

    name_w = max([len(r[0]) for r in rows] + [len("Drive")])
    name_w = min(name_w, 40)
    print(color_text(f"  {'Drive':<{name_w}}  {'Size':>10}  {'Used':>10}  "
                     f"{'Free':>10}  {'Use%':>5}  Mount Point",
                     fg=YELLOW, style=BOLD))
    print(f"  {DIM}{'-' * name_w}  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 5}  {'-' * 20}{RESET}")
    for name, path, total, used, free, pct in rows:
        pct_color = RED if pct >= 90 else (YELLOW if pct >= 75 else GREEN)
        disp = name[:name_w].ljust(name_w)
        print(f"  {WHITE}{disp}{RESET}  {fmt_size(total):>10}  {fmt_size(used):>10}  "
              f"{GREEN}{fmt_size(free):>10}{RESET}  "
              f"{color_text(f'{pct:>4.0f}%', fg=pct_color)}  {DIM}{path}{RESET}")
    print()
    print(f"  {DIM}{len(rows)} drive(s). Free = space available to you (matches "
          f"Finder's Available).{RESET}")

    pause_return()


# =============================================================================
# CONVERT  (CSV / JSON / XLSX / SQL)
# =============================================================================
CONVERT_IN_FORMATS  = ("csv", "json", "xlsx")
CONVERT_OUT_FORMATS = ("csv", "json", "xlsx", "sql")


def _unique_path(path):
    """Collision-safe output path: name.ext, name-2.ext, name-3.ext, …
    (same convention as Zip SubFolders). Never overwrites."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f"{base}-{n}{ext}"):
        n += 1
    return f"{base}-{n}{ext}"


def _require_openpyxl():
    """Import openpyxl on demand. XLSX is the only format that needs a
    third-party package; everything else is stdlib."""
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        raise ValueError("XLSX support requires the openpyxl package — "
                         "install it with: pip3 install openpyxl")


def _json_cell(value):
    """Flatten a JSON value to a table cell (nested dict/list → JSON text)."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else value


def _read_table(path):
    """Read a .csv / .json / .xlsx file into (headers, rows).

    csv  : first row = header (delimiter sniffed: , ; tab |; BOM tolerated)
    json : array of objects (headers = union of keys, first-seen order) or
           array of arrays (first array = header); a single object = one row
    xlsx : first sheet, first row = header (needs openpyxl)

    Raises ValueError with a user-friendly message on anything invalid.
    """
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "csv":
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            data = list(csv.reader(fh, dialect))
        if not data:
            raise ValueError("The CSV file is empty.")
        return [str(h) for h in data[0]], data[1:]

    if ext == "json":
        with open(path, encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not data:
            raise ValueError("JSON must be a non-empty array of objects "
                             "(or an array of arrays with a header row).")
        if isinstance(data[0], dict):
            headers = []
            for rec in data:
                if not isinstance(rec, dict):
                    raise ValueError("JSON array mixes objects with non-objects.")
                for k in rec:
                    if k not in headers:
                        headers.append(k)
            rows = [[_json_cell(rec.get(h)) for h in headers] for rec in data]
            return headers, rows
        if isinstance(data[0], list):
            return [str(h) for h in data[0]], [list(r) for r in data[1:]]
        raise ValueError("Unsupported JSON structure — expected an array of "
                         "objects or an array of arrays.")

    if ext == "xlsx":
        opx = _require_openpyxl()
        wb = opx.load_workbook(path, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        data = [["" if c is None else c for c in row]
                for row in ws.iter_rows(values_only=True)]
        wb.close()
        if not data:
            raise ValueError("The XLSX file has no rows on its first sheet.")
        return [str(h) for h in data[0]], data[1:]

    raise ValueError(f"Unsupported input type .{ext} — "
                     "supported inputs: .csv, .json, .xlsx")


def _write_csv_out(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerows(rows)


def _write_json_out(path, headers, rows):
    records = []
    for r in rows:
        r = list(r) + [""] * (len(headers) - len(r))
        records.append(dict(zip(headers, r)))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False, default=str)
        fh.write("\n")


def _write_xlsx_out(path, headers, rows):
    opx = _require_openpyxl()
    wb = opx.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append([str(h) for h in headers])
    for r in rows:
        ws.append([c if isinstance(c, (int, float, bool, datetime)) or c is None
                   else str(c) for c in r])
    wb.save(path)


# --- SQL output ---------------------------------------------------------------
_SQL_INT_RE  = re.compile(r"^-?\d+$")
_SQL_DEC_RE  = re.compile(r"^-?\d+\.\d+$")
_SQL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SQL_DT_RE   = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$")


def _sql_ident(name):
    """Sanitize a name into a safe SQL identifier (backtick-quoted later)."""
    ident = re.sub(r"[^A-Za-z0-9_]", "_", str(name).strip()) or "col"
    if ident[0].isdigit():
        ident = "_" + ident
    return ident


def _sql_guess_type(values):
    """Guess a MySQL column type from a column's non-empty values:
    INT/BIGINT → DECIMAL → DATE → DATETIME → VARCHAR(n) → TEXT."""
    vals = [v for v in values if v is not None and str(v).strip() != ""]
    if not vals:
        return "VARCHAR(255)"
    strs = [str(v) for v in vals]
    if all(isinstance(v, bool) for v in vals):
        return "TINYINT(1)"
    if all(_SQL_INT_RE.match(s) for s in strs):
        return "BIGINT" if any(abs(int(s)) > 2147483647 for s in strs) else "INT"
    if all(_SQL_INT_RE.match(s) or _SQL_DEC_RE.match(s) for s in strs):
        whole = max(len(s.split(".")[0].lstrip("-")) for s in strs)
        frac  = max((len(s.split(".")[1]) if "." in s else 0) for s in strs)
        return f"DECIMAL({min(whole + frac, 65)},{min(frac, 30)})"
    if all(_SQL_DATE_RE.match(s) for s in strs):
        return "DATE"
    if all(_SQL_DT_RE.match(s) or _SQL_DATE_RE.match(s) for s in strs):
        return "DATETIME"
    longest = max(len(s) for s in strs)
    if longest > 255:
        return "TEXT"
    # round up to the next 25 so similar columns get tidy consistent widths
    return f"VARCHAR({max(25, ((longest + 24) // 25) * 25)})"


def _sql_value(value, col_type):
    """Render one value for an INSERT: NULL for empty, bare numbers for
    numeric columns, otherwise a quoted + escaped string literal."""
    if value is None or str(value).strip() == "":
        return "NULL"
    s = str(value)
    if col_type.startswith(("INT", "BIGINT", "DECIMAL", "TINYINT")):
        if isinstance(value, bool):
            return "1" if value else "0"
        if _SQL_INT_RE.match(s) or _SQL_DEC_RE.match(s):
            return s
    return "'" + s.replace("\\", "\\\\").replace("'", "''") + "'"


def _write_sql_out(path, headers, rows, table):
    """CREATE TABLE (guessed column types) + multi-row INSERTs (500/batch)."""
    table = _sql_ident(table)
    cols = []
    seen = set()
    for h in headers:                       # de-duplicate sanitized names
        c = base = _sql_ident(h)
        n = 2
        while c in seen:
            c = f"{base}_{n}"; n += 1
        seen.add(c)
        cols.append(c)
    types = [_sql_guess_type([r[i] if i < len(r) else "" for r in rows])
             for i in range(len(headers))]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"-- Generated by File Manager v{VERSION} on "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        fh.write(f"-- Source rows: {len(rows)}\n\n")
        fh.write(f"CREATE TABLE `{table}` (\n")
        fh.write(",\n".join(f"    `{c}` {t}" for c, t in zip(cols, types)))
        fh.write("\n);\n\n")
        col_list = ", ".join(f"`{c}`" for c in cols)
        for start in range(0, len(rows), 500):
            batch = rows[start:start + 500]
            fh.write(f"INSERT INTO `{table}` ({col_list}) VALUES\n")
            lines = []
            for r in batch:
                r = list(r) + [""] * (len(cols) - len(r))
                lines.append("(" + ", ".join(
                    _sql_value(r[i], types[i]) for i in range(len(cols))) + ")")
            fh.write(",\n".join(lines) + ";\n\n")


_CONVERT_WRITERS = {
    "csv":  _write_csv_out,
    "json": _write_json_out,
    "xlsx": _write_xlsx_out,
}


def convert_file(path, out_format):
    """Convert a CSV/JSON/XLSX data file to CSV, JSON, XLSX, or SQL.

    The output file is written next to the source with the same name and the
    new extension — collision-safe (name-2.ext, …), never overwriting. SQL
    output is a CREATE TABLE (types guessed per column) plus multi-row
    INSERTs, with the table named after the file. The results screen is
    appended to ~/Documents/log/fm.log and offers [R] Run Again.
    """
    while True:
        with _ActivityLog():
            _convert_screen(path, out_format)
        if not pause_rerun():
            return


def _convert_screen(path, out_format):
    screen("Convert")
    print()
    out_format = str(out_format).lower().lstrip(".")
    in_ext = os.path.splitext(path)[1].lower().lstrip(".")
    print(f"  {YELLOW}File{RESET}  : {path}")
    print(f"  {YELLOW}From{RESET}  : .{in_ext}    {YELLOW}To{RESET}: .{out_format}\n")
    if not os.path.isfile(path):
        print(color_text(f"  Not a file: {path}", fg=RED))
        return
    if out_format not in CONVERT_OUT_FORMATS:
        print(color_text(f"  Unsupported output format .{out_format} — "
                         f"choose one of: {', '.join(CONVERT_OUT_FORMATS)}", fg=RED))
        return

    out_path = _unique_path(os.path.splitext(path)[0] + "." + out_format)
    try:
        headers, rows = _read_table(path)
        # The header row defines the columns: pad short rows, drop extras.
        width = len(headers)
        rows = [(list(r) + [""] * width)[:width] for r in rows]
        if out_format == "sql":
            table = os.path.splitext(os.path.basename(path))[0]
            _write_sql_out(out_path, headers, rows, table)
        else:
            _CONVERT_WRITERS[out_format](out_path, headers, rows)
    except ValueError as e:
        report_result(False, "", str(e))
        return
    except OSError as e:
        report_result(False, "", f"File error: {e}")
        return

    print(f"  {YELLOW}Output{RESET}: {out_path}")
    print(f"  {YELLOW}Size{RESET}  : {fmt_size(file_size(out_path))}\n")
    report_result(True,
                  f"Converted {len(rows):,} row(s) × {len(headers)} column(s) "
                  f"to .{out_format}.")


def convert_menu():
    """Convert flow: pick the file, pick the output format, convert."""
    path = ask_file("File to convert (.csv, .json, .xlsx)")
    if not path:
        pause_return()
        return
    in_ext = os.path.splitext(path)[1].lower().lstrip(".")
    if in_ext not in CONVERT_IN_FORMATS:
        print(color_text(f"  Unsupported input type .{in_ext} — "
                         "supported: .csv, .json, .xlsx", fg=RED))
        pause_return()
        return
    options = [
        ("CSV",
         "Comma-separated values with a header row — opens anywhere "
         "(Excel, Numbers, imports)."),
        ("JSON",
         "An array of objects, one per row, pretty-printed (2-space indent) — "
         "for APIs, scripts, and config-style data."),
        ("XLSX",
         "An Excel workbook with the data on a single sheet (header row "
         "first). Requires the openpyxl package (pip3 install openpyxl) — "
         "the other formats work without it."),
        ("SQL",
         "A MySQL script: CREATE TABLE named after the file with column types "
         "guessed from the data (INT, DECIMAL, DATE, DATETIME, VARCHAR, "
         "TEXT), then multi-row INSERT statements (500 rows per batch). "
         "Empty cells become NULL."),
    ]
    ch = render_menu("Convert — Output Format", options,
                     outro=[f"File - {path}"])
    if ch == "back":
        return
    convert_file(path, CONVERT_OUT_FORMATS[int(ch) - 1])


# =============================================================================
# CREATE RANDOM UID
# =============================================================================
UUID_MAX = 10000


def generate_uuids(count):
    """Generate `count` random (version 4) UUIDs and show them one per line.
    The list is also appended to ~/Documents/log/fm.log; [R] reruns with the
    same count (new UUIDs each time)."""
    while True:
        with _ActivityLog():
            _uuid_screen(count)
        if not pause_rerun():
            return


def _uuid_screen(count):
    screen("Create Random UID")
    print()
    try:
        count = int(count)
    except (TypeError, ValueError):
        print(color_text("  Invalid number.", fg=RED))
        return
    if count < 1:
        print(color_text("  Enter a number of 1 or more.", fg=RED))
        return
    if count > UUID_MAX:
        print(color_text(f"  Capped at {UUID_MAX:,}.", fg=YELLOW))
        count = UUID_MAX
    print(f"  {YELLOW}Count{RESET}: {count:,}\n")
    for _ in range(count):
        print(f"  {uuid.uuid4()}")
    print()
    print(color_text(f"  {count:,} UUID(s) generated.", fg=BRIGHT_CYAN, style=BOLD))


def create_random_uid_menu():
    raw = ask("How many UUIDs to generate?", "1")
    try:
        count = int(raw)
    except ValueError:
        print(color_text("  Invalid number.", fg=RED))
        pause_return()
        return
    generate_uuids(count)


# =============================================================================
# FIND
# =============================================================================
def _print_find_results(results, kind, extra=None):
    if not results:
        print(color_text(f"  No matching {kind} found.", fg=YELLOW))
        return
    print(color_text(f"  {len(results)} {kind} found:", fg=BRIGHT_CYAN, style=BOLD))
    for path in results:
        if extra and path in extra:
            print(f"    {path}  {DIM}({extra[path]}){RESET}")
        else:
            print(f"    {path}")


def find_folders(root, pattern):
    screen("Find Folders")
    print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    results = []
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for d in sorted(dns):
            if fnmatch.fnmatch(d, pattern):
                results.append(os.path.join(dp, d))
    _print_find_results(sorted(results), "folders")
    if pause_rerun():
        find_folders(root, pattern)


def find_files_by_name(root, pattern):
    screen("Find Files by Name")
    print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    results = []
    extra = {}
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for fn in sorted(fns):
            if is_excluded_file(fn):
                continue
            if fnmatch.fnmatch(fn, pattern):
                p = os.path.join(dp, fn)
                results.append(p)
                extra[p] = fmt_size(file_size(p))
    _print_find_results(sorted(results), "files", extra)
    if pause_rerun():
        find_files_by_name(root, pattern)


def find_files_by_ext(root, ext):
    ext = ext.lstrip(".").lower()
    screen("Find Files by Extension")
    print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Extension{RESET}: .{ext}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    results = []
    extra = {}
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for fn in sorted(fns):
            if is_excluded_file(fn):
                continue
            if fn.lower().endswith("." + ext):
                p = os.path.join(dp, fn)
                results.append(p)
                extra[p] = fmt_size(file_size(p))
    _print_find_results(sorted(results), f".{ext} files", extra)
    if pause_rerun():
        find_files_by_ext(root, ext)


def find_by_size(root, megabytes, over=True):
    threshold = int(megabytes * 1024 * 1024)
    label = "over" if over else "under"
    screen(f"Find Files {label.capitalize()} {megabytes} MB")
    print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Size {label}{RESET}: {megabytes} MB\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    results = []
    extra = {}
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for fn in fns:
            if is_excluded_file(fn):
                continue
            p = os.path.join(dp, fn)
            sz = file_size(p)
            if (over and sz > threshold) or (not over and sz < threshold):
                results.append(p)
                extra[p] = fmt_size(sz)
    results.sort(key=lambda p: file_size(p), reverse=over)
    _print_find_results(results, f"files {label} {megabytes} MB", extra)
    if pause_rerun():
        find_by_size(root, megabytes, over)


def find_files_combined(root, pattern=None, ext=None, over_mb=None, under_mb=None):
    """Find files matching ALL supplied criteria (logical AND).

    pattern  : filename wildcard (e.g. "IMG_*.jpg")   — None to skip
    ext      : extension without dot (e.g. "mov")      — None to skip
    over_mb  : only files strictly larger than N MB    — None to skip
    under_mb : only files strictly smaller than N MB   — None to skip

    Example: ext="mov", under_mb=5  ->  .mov files under 5 MB.
    """
    ext_l = ext.lstrip(".").lower() if ext else None
    over_b = int(over_mb * 1024 * 1024) if over_mb is not None else None
    under_b = int(under_mb * 1024 * 1024) if under_mb is not None else None

    # Human-readable summary of the active criteria
    crit = []
    if pattern:
        crit.append(f"name matches '{pattern}'")
    if ext_l:
        crit.append(f"extension .{ext_l}")
    if over_mb is not None:
        crit.append(f"over {over_mb} MB")
    if under_mb is not None:
        crit.append(f"under {under_mb} MB")

    screen("Find Files")
    print()
    print(f"  {YELLOW}Root{RESET}: {root}")
    print(f"  {YELLOW}Criteria{RESET}: {' AND '.join(crit) if crit else '(all files)'}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return

    results = []
    extra = {}
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for fn in fns:
            if is_excluded_file(fn):
                continue
            if pattern and not fnmatch.fnmatch(fn, pattern):
                continue
            if ext_l and not fn.lower().endswith("." + ext_l):
                continue
            p = os.path.join(dp, fn)
            sz = file_size(p)
            if over_b is not None and not sz > over_b:
                continue
            if under_b is not None and not sz < under_b:
                continue
            results.append(p)
            extra[p] = fmt_size(sz)

    # Largest-first when a size criterion is in play; otherwise alphabetical.
    if over_b is not None or under_b is not None:
        results.sort(key=lambda p: file_size(p), reverse=True)
    else:
        results.sort()
    _print_find_results(results, "files", extra)
    if pause_rerun():
        find_files_combined(root, pattern, ext, over_mb, under_mb)


def _scan_filenames(folders):
    """Scan each folder recursively (hidden files/folders skipped) and return
    a list parallel to `folders`: one dict per folder of
    filename -> [(size, containing_dir), ...]."""
    per_folder = []
    for folder in folders:
        occ = defaultdict(list)
        for dp, dns, fns in os.walk(folder):
            dns[:] = [d for d in dns if not d.startswith(".") and d.lower() not in EXCLUDED_DIR_NAMES]
            for fn in fns:
                if fn.startswith(".") or is_excluded_file(fn):
                    continue
                occ[fn].append((file_size(os.path.join(dp, fn)), dp))
        per_folder.append(occ)
    return per_folder


def _print_filename_size_table(names, per_folder, folder_col_idx=None):
    """Print the filename/size-per-folder table: one row per name, one size
    column per folder (blank when the name isn't in that folder; multiple
    occurrences within one folder are listed comma-separated).

    folder_col_idx: when set (0-based folder index), append a last 'Folder'
    column showing the directory containing each occurrence in that folder.
    """
    rows = []
    for name in names:
        cells = [", ".join(fmt_size_short(s) for (s, _) in occ[name]) if name in occ else ""
                 for occ in per_folder]
        if folder_col_idx is not None:
            dirs = []
            for (_, dp) in per_folder[folder_col_idx].get(name, ()):
                if dp not in dirs:
                    dirs.append(dp)
            cells.append(", ".join(dirs))
        rows.append((name, cells))

    headers = [str(i + 1) for i in range(len(per_folder))]
    if folder_col_idx is not None:
        headers.append("Folder")

    name_w = max([len(n) for (n, _) in rows] + [len("Filename")])
    name_w = min(name_w, 50)
    col_ws = [max([len(cells[i]) for (_, cells) in rows] + [len(h), 8])
              for i, h in enumerate(headers)]

    last = len(headers) - 1
    if folder_col_idx is not None:
        # Keep the header/separator inside the terminal; the path cells
        # themselves are printed unpadded (no trailing spaces).
        used = 2 + name_w + sum(cw + 2 for cw in col_ws[:-1]) + 2
        col_ws[-1] = max(min(col_ws[-1], get_width() - used), len("Folder"))

    hdr = f"  {'Filename':<{name_w}}"
    sep = f"  {'-' * name_w}"
    for i, (h, cw) in enumerate(zip(headers, col_ws)):
        # The 'Folder' path column is left-aligned; size columns right-aligned.
        hdr += f"  {h}" if (folder_col_idx is not None and i == last) else f"  {h:>{cw}}"
        sep += f"  {'-' * cw}"
    print(color_text(hdr, fg=YELLOW, style=BOLD))
    print(f"{DIM}{sep}{RESET}")

    for name, cells in rows:
        line = f"  {WHITE}{name[:name_w]:<{name_w}}{RESET}"
        for i, (cw, cell) in enumerate(zip(col_ws, cells)):
            if folder_col_idx is not None and i == last:
                line += f"  {DIM}{cell}{RESET}"
            elif cell:
                line += f"  {GREEN}{cell:>{cw}}{RESET}"
            else:
                line += f"  {'':>{cw}}"
        print(line)
    print(f"{DIM}{sep}{RESET}")


def find_duplicates_by_filename(folders):
    """Find files that share the same filename across (or within) the given
    folders — read-only, nothing is changed.

    Each folder is scanned recursively (hidden files/folders skipped). A
    filename counts as a duplicate when it appears 2+ times in total. Results
    are shown as a table: a numbered header line per folder, then one row per
    duplicated filename with a size column per folder. If a name occurs more
    than once within a single folder, each size is listed comma-separated.
    The screen output is also appended to ~/Documents/log/fm.log.
    """
    while True:
        with _ActivityLog():
            _find_duplicates_screen(folders)
        if not pause_rerun():
            return


def _find_duplicates_screen(folders):
    screen("Find Duplicates by Filename")
    print()

    folders = [clean_path(f) for f in folders if f]
    valid = [f for f in folders if os.path.isdir(f)]
    for f in folders:
        if f not in valid:
            print(color_text(f"  Skipping (not a directory): {f}", fg=YELLOW))
    if not valid:
        print(color_text("  No valid folders to scan.", fg=RED))
        return

    # Numbered folder header
    for i, folder in enumerate(valid, 1):
        print(f"  {YELLOW}{i}{RESET} - {folder}")
    print()

    per_folder = _scan_filenames(valid)
    all_names = set()
    for occ in per_folder:
        all_names.update(occ)
    dups = sorted(
        (name for name in all_names
         if sum(len(occ.get(name, ())) for occ in per_folder) > 1),
        key=str.lower)

    if not dups:
        print(color_text("  No duplicate filenames found.", fg=YELLOW))
        return

    _print_filename_size_table(dups, per_folder)
    print(color_text(f"  {len(dups)} duplicated filename(s) found.", fg=BRIGHT_CYAN, style=BOLD))


FUZZY_NAME_RATIO     = 0.85   # difflib similarity threshold for "close" names
FUZZY_SIZE_TOLERANCE = 0.01   # sizes within 1% of each other count as "close"

# Duplicate-style name endings stripped before stems are compared:
# "video1", "video (1)", "video[2]", "video copy", "video copy 2", "video - Copy"
_FUZZY_SUFFIX_RE = re.compile(
    r"[ _\-.]*(?:\(\d+\)|\[\d+\]|copy(?:[ _\-]*\d+)?|\d+)$", re.IGNORECASE)


def _fuzzy_stem(stem):
    """Comparison key for a filename stem: lowercased, duplicate-style endings
    stripped, runs of separators collapsed to a single space."""
    s = _FUZZY_SUFFIX_RE.sub("", stem.lower())
    return re.sub(r"[ _\-.]+", " ", s).strip()


def _sizes_close(a, b):
    return abs(a - b) <= max(a, b) * FUZZY_SIZE_TOLERANCE


def _names_close(stem_a, stem_b):
    ka, kb = _fuzzy_stem(stem_a), _fuzzy_stem(stem_b)
    if ka and ka == kb:
        return True
    return difflib.SequenceMatcher(
        None, stem_a.lower(), stem_b.lower()).ratio() >= FUZZY_NAME_RATIO


def find_duplicates_by_fuzzy_name(folders):
    """Find files whose names are CLOSE (not necessarily identical) and whose
    sizes are close — read-only, nothing is changed.

    Each folder is scanned recursively (hidden files/folders skipped). Two
    files count as fuzzy duplicates when their extension matches, their sizes
    are within FUZZY_SIZE_TOLERANCE of each other, and their name stems either
    match after duplicate-style endings are stripped (videofile1 ~ videofile,
    photo (2) ~ photo, doc copy ~ doc) or are FUZZY_NAME_RATIO similar.
    Matches are clustered into groups; in each group the shortest/cleanest
    name is marked KEEP and the rest DELETE — candidates only, nothing is
    deleted. The screen output is also appended to ~/Documents/log/fm.log.
    """
    while True:
        with _ActivityLog():
            _find_fuzzy_dups_screen(folders)
        if not pause_rerun():
            return


def _fuzzy_dup_groups(folders):
    """Cluster every file under the given folders into fuzzy-duplicate groups:
    close name (_names_close) + same extension + size within
    FUZZY_SIZE_TOLERANCE. Returns a list of groups of (name, stem, ext, size,
    dir) tuples — each group sorted with the KEEP candidate (shortest/cleanest
    name) first, groups sorted largest file first. Groups have 2+ members."""
    # Flatten every occurrence across all folders: (name, stem, ext, size, dir)
    files = []
    for occ in _scan_filenames(folders):
        for name, entries in occ.items():
            stem, ext = os.path.splitext(name)
            for (size, dp) in entries:
                files.append((name, stem, ext.lower(), size, dp))

    # Sort by extension then size so only a nearby window needs pairwise name
    # comparison — once the size gap exceeds the tolerance it only grows, so
    # the inner scan can stop there.
    files.sort(key=lambda f: (f[2], f[3]))

    parent = list(range(len(files)))

    def _root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            if files[j][2] != files[i][2] or not _sizes_close(files[i][3], files[j][3]):
                break
            if _names_close(files[i][1], files[j][1]):
                parent[_root(j)] = _root(i)

    groups = defaultdict(list)
    for i in range(len(files)):
        groups[_root(i)].append(files[i])
    dup_groups = [g for g in groups.values() if len(g) > 1]

    # KEEP the shortest (cleanest) name; largest files first overall.
    for g in dup_groups:
        g.sort(key=lambda f: (len(f[0]), f[0].lower(), f[4]))
    dup_groups.sort(key=lambda g: -max(f[3] for f in g))
    return dup_groups


def _find_fuzzy_dups_screen(folders):
    screen("Find Duplicates by Fuzzy Name")
    print()

    folders = [clean_path(f) for f in folders if f]
    valid = [f for f in folders if os.path.isdir(f)]
    for f in folders:
        if f not in valid:
            print(color_text(f"  Skipping (not a directory): {f}", fg=YELLOW))
    if not valid:
        print(color_text("  No valid folders to scan.", fg=RED))
        return

    # Numbered folder header
    for i, folder in enumerate(valid, 1):
        print(f"  {YELLOW}{i}{RESET} - {folder}")
    print()

    dup_groups = _fuzzy_dup_groups(valid)
    if not dup_groups:
        print(color_text("  No fuzzy-duplicate files found.", fg=YELLOW))
        return

    name_w = min(max(len(f[0]) for g in dup_groups for f in g), 50)
    del_count = del_bytes = 0
    for n, group in enumerate(dup_groups, 1):
        print(color_text(f"  {n}) {group[0][0]}", style=BOLD))
        for k, (name, _stem, _ext, size, dp) in enumerate(group):
            tag = (color_text("KEEP  ", fg=BRIGHT_CYAN, style=BOLD) if k == 0
                   else color_text("DELETE", fg=BRIGHT_YELLOW, style=BOLD))
            print(f"     {tag}  {name:<{name_w}}  {fmt_size_short(size):>8}  {dp}")
            if k:
                del_count += 1
                del_bytes += size
        print()

    print(color_text(
        f"  {len(dup_groups)} fuzzy-duplicate group(s) — {del_count} DELETE "
        f"candidate(s), {fmt_size(del_bytes)} reclaimable. Nothing was deleted.",
        fg=BRIGHT_CYAN, style=BOLD))


def find_missing_by_filename(folder_a, folder_b, mode="either", match_size=False):
    """Compare two folders by filename and list files present in only ONE of
    them (missing from the other) — read-only, nothing is changed.

    mode: first  -> filenames in folder 1 but not in folder 2
          second -> filenames in folder 2 but not in folder 1
          either -> filenames in either folder but not in both

    match_size: when True, files match only when BOTH the filename AND the
    size agree — so a same-named file whose size differs between the folders
    is also reported (its size shows in both columns, revealing the mismatch).

    Both folders are scanned recursively (hidden files/folders skipped).
    Results use the same table as Find Duplicates by Filename: a numbered
    header per folder, one row per filename, and a size column per folder —
    the blank column shows which folder the file is missing from. In the
    first/second modes a last 'Folder' column shows the directory containing
    each file. The folder list is repeated after the results, and the screen
    output is also appended to ~/Documents/log/fm.log.
    """
    while True:
        with _ActivityLog():
            _find_missing_screen(folder_a, folder_b, mode, match_size)
        if not pause_rerun():
            return


def _find_missing_screen(folder_a, folder_b, mode, match_size=False):
    screen("Find Missing by Filename & Size" if match_size else "Find Missing by Filename")
    print()

    folders = [clean_path(folder_a), clean_path(folder_b)]
    ok = True
    for f in folders:
        if not os.path.isdir(f):
            print(color_text(f"  Not a directory: {f}", fg=RED))
            ok = False
    if not ok:
        return

    mode_labels = {
        "first":  "In 1st folder only",
        "second": "In 2nd folder only",
        "either": "In either folder (only once)",
    }
    print(f"  {YELLOW}Show{RESET}: {mode_labels.get(mode, mode)}\n")

    def folder_list():
        for i, folder in enumerate(folders, 1):
            print(f"  {YELLOW}{i}{RESET} - {folder}")

    folder_list()
    print()

    per_folder = _scan_filenames(folders)
    if match_size:
        # Match on (filename, size): a same-named file whose size differs on
        # the other side is treated as missing there.
        set_a = {(n, s) for n, occ in per_folder[0].items() for (s, _) in occ}
        set_b = {(n, s) for n, occ in per_folder[1].items() for (s, _) in occ}
    else:
        set_a, set_b = set(per_folder[0]), set(per_folder[1])
    if mode == "first":
        found = set_a - set_b
    elif mode == "second":
        found = set_b - set_a
    else:
        found = set_a ^ set_b
    names = {n for (n, _) in found} if match_size else found
    missing = sorted(names, key=str.lower)

    if not missing:
        print(color_text("  No missing files found for the selected option.", fg=YELLOW))
        return

    # In the single-folder modes every file lives in one known folder, so a
    # last column shows the directory actually containing each file.
    folder_col_idx = {"first": 0, "second": 1}.get(mode)
    _print_filename_size_table(missing, per_folder, folder_col_idx)
    what = "missing or differing in size" if match_size else "found in only one folder"
    print(color_text(f"  {len(missing)} filename(s) {what}.", fg=BRIGHT_CYAN, style=BOLD))
    print()
    folder_list()


def find_and_replace(root, search, replace, ext=None, live_requested=None,
                     assume_yes=False, backup=False):
    """Find a text string in files under a folder and replace it.

    ALWAYS a dry run first: every match is listed (file, line number, line
    with the match highlighted) before anything is touched. Matching is
    literal and case-insensitive; the replacement is inserted exactly as
    typed. Hidden files/folders, excluded names, and binary files are never
    scanned or modified. `ext` limits the scan to one file extension.

    live_requested: None  -> interactive (confirm Y/N, then ask about .bak)
                    True  -> CLI --apply (confirm unless assume_yes)
                    False -> CLI dry run (report only)
    The screen output is also appended to ~/Documents/log/fm.log.
    """
    while True:
        with _ActivityLog():
            _find_replace_screen(root, search, replace, ext,
                                 live_requested, assume_yes, backup)
        if not pause_rerun():
            return


def _find_replace_screen(root, search, replace, ext, live_requested,
                         assume_yes, backup):
    screen("Find & Replace")
    print()
    ext_l = ext.lstrip(".").lower() if ext else None
    print(f"  {YELLOW}Folder{RESET} : {root}")
    print(f"  {YELLOW}Find{RESET}   : {search}  {DIM}(case-insensitive){RESET}")
    print(f"  {YELLOW}Replace{RESET}: "
          f"{replace if replace else DIM + '(remove the text)' + RESET}")
    if ext_l:
        print(f"  {YELLOW}Ext{RESET}    : .{ext_l}")
    print()
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED))
        return
    if not search:
        print(color_text("  Search text required.", fg=RED))
        return

    pattern = re.compile(re.escape(search), re.IGNORECASE)

    plans = []                    # (path, text, match_count, [(line_no, line)])
    scanned = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".")
                  and d.lower() not in EXCLUDED_DIR_NAMES]
        for fn in sorted(fns):
            if fn.startswith(".") or is_excluded_file(fn):
                continue
            # Never touch .bak backups (this feature creates them) unless
            # .bak files were explicitly requested via the extension filter.
            if ext_l != "bak" and fn.lower().endswith(".bak"):
                continue
            if ext_l and not fn.lower().endswith("." + ext_l):
                continue
            path = os.path.join(dp, fn)
            try:
                with open(path, "rb") as fh:
                    if b"\x00" in fh.read(8192):
                        continue              # binary — never touched
                # surrogateescape + newline="" round-trips any byte sequence
                # and line-ending style unchanged apart from the replacement.
                with open(path, "r", encoding="utf-8",
                          errors="surrogateescape", newline="") as fh:
                    text = fh.read()
            except OSError:
                continue
            scanned += 1
            if not pattern.search(text):
                continue
            hits = [(no, line) for no, line in enumerate(text.splitlines(), 1)
                    if pattern.search(line)]
            plans.append((path, text, len(pattern.findall(text)), hits))

    if not plans:
        print(color_text(f"  No matches found ({scanned:,} file(s) scanned).",
                         fg=YELLOW))
        return

    # ---- Dry-run report: file, then line number + line per match ----------
    width = get_width()
    total = line_total = 0
    for path, _text, count, hits in plans:
        total += count
        line_total += len(hits)
        print(color_text(
            f"  {path}  ({count} match{'es' if count != 1 else ''})",
            fg=BRIGHT_CYAN, style=BOLD))
        for no, line in hits:
            plain = line.rstrip()
            prefix = f"    {no:>6}: "
            avail = max(20, width - len(prefix) - 1)
            if len(plain) > avail:
                plain = plain[:avail - 1] + "…"
            shown = pattern.sub(
                lambda m: f"{BRIGHT_RED}{BOLD}{m.group(0)}{RESET}", plain)
            print(f"{DIM}{prefix}{RESET}{shown}")
        print()

    print(color_text(
        f"  DRY RUN — {total:,} match(es) on {line_total:,} line(s) in "
        f"{len(plans)} file(s). Nothing has been changed.",
        fg=YELLOW, style=BOLD))

    do_replace = False
    make_bak = backup
    if live_requested is None:                # interactive
        do_replace = safe_confirm(
            f"  Replace all {total:,} occurrence(s) in {len(plans)} file(s)?",
            default=False)
        if do_replace:
            make_bak = safe_confirm(
                "  Create a .bak backup of each file before replacing?",
                default=True)
    elif live_requested is True:              # CLI --apply
        do_replace = True if assume_yes else safe_confirm(
            f"  Replace all {total:,} occurrence(s) in {len(plans)} file(s)?",
            default=False)
    else:                                     # CLI dry run
        print(color_text("  Re-run with --apply to perform the replacement.",
                         fg=YELLOW))
        return
    if not do_replace:
        print(color_text("  Cancelled — nothing changed.", fg=YELLOW))
        return

    ok = fail = 0
    for path, text, _count, _hits in plans:
        try:
            if make_bak:
                shutil.copy2(path, path + ".bak")
            with open(path, "w", encoding="utf-8",
                      errors="surrogateescape", newline="") as fh:
                fh.write(pattern.sub(lambda m: replace, text))
            ok += 1
        except OSError as e:
            fail += 1
            print(color_text(f"  ✗ {path}: {e}", fg=RED))
    print()
    report_result(
        fail == 0,
        f"Replaced {total:,} occurrence(s) in {ok} file(s)."
        + (" Backups saved with a .bak extension." if make_bak else ""),
        f"Replaced in {ok} file(s), {fail} failed.")


def find_and_rename(root, mode, text, replace_with=None, ext=None,
                    live_requested=None, assume_yes=False):
    """Find files under a folder and rename them.

    mode: 'prepend' — new name = text + filename (files already starting
                      with the text are skipped)
          'append'  — text is inserted at the end of the name, BEFORE the
                      extension (files already ending with it are skipped)
          'replace' — occurrences of `text` inside the filename are replaced
                      with `replace_with` (matching is literal and
                      case-insensitive; only matching files are listed)

    ALWAYS a dry run first: every planned rename is listed old → new before
    anything is touched. Renames that would collide with an existing file
    (or with another rename in the same run) are skipped and reported.
    `ext` limits the scan to one file extension.

    live_requested: None  -> interactive (confirm Y/N after the preview)
                    True  -> CLI --apply (confirm unless assume_yes)
                    False -> CLI dry run (report only)
    The screen output is also appended to ~/Documents/log/fm.log.
    """
    while True:
        with _ActivityLog():
            _find_rename_screen(root, mode, text, replace_with, ext,
                                live_requested, assume_yes)
        if not pause_rerun():
            return


def _find_rename_screen(root, mode, text, replace_with, ext,
                        live_requested, assume_yes):
    screen("Find & Rename")
    print()
    ext_l = ext.lstrip(".").lower() if ext else None
    mode_disp = {"prepend": "Prepend (text + filename)",
                 "append":  "Append (before the extension)",
                 "replace": "Replace (inside the filename)"}[mode]
    print(f"  {YELLOW}Folder{RESET} : {root}")
    print(f"  {YELLOW}Mode{RESET}   : {mode_disp}")
    if mode == "replace":
        print(f"  {YELLOW}Find{RESET}   : {text}  {DIM}(case-insensitive){RESET}")
        print(f"  {YELLOW}Replace{RESET}: "
              f"{replace_with if replace_with else DIM + '(remove the text)' + RESET}")
    else:
        print(f"  {YELLOW}Text{RESET}   : {text}")
    if ext_l:
        print(f"  {YELLOW}Ext{RESET}    : .{ext_l}")
    print()
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED))
        return
    if not text:
        print(color_text("  Text required.", fg=RED))
        return

    pattern = (re.compile(re.escape(text), re.IGNORECASE)
               if mode == "replace" else None)

    plans = []                    # (dirpath, old_name, new_name)
    collisions = []               # (dirpath, old_name, new_name)
    taken = set()                 # target paths already claimed this run
    scanned = already = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".")
                  and d.lower() not in EXCLUDED_DIR_NAMES]
        for fn in sorted(fns):
            if fn.startswith(".") or is_excluded_file(fn):
                continue
            if ext_l and not fn.lower().endswith("." + ext_l):
                continue
            scanned += 1
            stem, dot_ext = os.path.splitext(fn)
            if mode == "prepend":
                if fn.lower().startswith(text.lower()):
                    already += 1              # already has the prefix
                    continue
                new_name = text + fn
            elif mode == "append":
                if stem.lower().endswith(text.lower()):
                    already += 1              # already has the suffix
                    continue
                new_name = stem + text + dot_ext
            else:                             # replace
                if not pattern.search(fn):
                    continue                  # filename doesn't contain it
                new_name = pattern.sub(lambda m: replace_with, fn)
            # A rename must produce a real, different, visible filename.
            if new_name == fn or not new_name or new_name.startswith("."):
                already += 1
                continue
            target = os.path.join(dp, new_name)
            if os.path.exists(target) or target in taken:
                collisions.append((dp, fn, new_name))
                continue
            taken.add(target)
            plans.append((dp, fn, new_name))

    if not plans and not collisions:
        print(color_text(
            f"  Nothing to rename ({scanned:,} file(s) scanned"
            + (f", {already:,} already named that way" if already else "")
            + ").", fg=YELLOW))
        return

    # ---- Dry-run report: old → new, path shown relative to the root -------
    for dp, fn, new_name in plans:
        rel = os.path.relpath(os.path.join(dp, fn), root)
        print(f"  {WHITE}{rel}{RESET}  {DIM}->{RESET}  "
              f"{BRIGHT_CYAN}{new_name}{RESET}")
    for dp, fn, new_name in collisions:
        rel = os.path.relpath(os.path.join(dp, fn), root)
        print(f"  {YELLOW}SKIP{RESET} {WHITE}{rel}{RESET}  {DIM}->{RESET}  "
              f"{new_name}  {YELLOW}(target already exists){RESET}")
    print()

    summary = f"  DRY RUN — {len(plans):,} file(s) would be renamed"
    extras = []
    if already:
        extras.append(f"{already:,} already named that way")
    if collisions:
        extras.append(f"{len(collisions):,} skipped — target exists")
    if extras:
        summary += f" ({', '.join(extras)})"
    summary += ". Nothing has been changed."
    print(color_text(summary, fg=YELLOW, style=BOLD))

    if not plans:
        return

    do_rename = False
    if live_requested is None:                # interactive
        do_rename = safe_confirm(
            f"  Rename these {len(plans):,} file(s)?", default=False)
    elif live_requested is True:              # CLI --apply
        do_rename = True if assume_yes else safe_confirm(
            f"  Rename these {len(plans):,} file(s)?", default=False)
    else:                                     # CLI dry run
        print(color_text("  Re-run with --apply to perform the rename.",
                         fg=YELLOW))
        return
    if not do_rename:
        print(color_text("  Cancelled — nothing renamed.", fg=YELLOW))
        return

    ok = fail = 0
    for dp, fn, new_name in plans:
        try:
            os.rename(os.path.join(dp, fn), os.path.join(dp, new_name))
            ok += 1
        except OSError as e:
            fail += 1
            print(color_text(f"  ✗ {os.path.join(dp, fn)}: {e}", fg=RED))
    print()
    report_result(fail == 0,
                  f"Renamed {ok} file(s).",
                  f"Renamed {ok} file(s), {fail} failed.")


# =============================================================================
# REMOVE  (dry-run by default)
# =============================================================================
def _preview_removal(items):
    """items: list of (path, size, is_dir). Prints a numbered preview.
    Returns total size in bytes."""
    total = 0
    print(color_text(f"  {len(items)} item(s) matched:", fg=BRIGHT_CYAN, style=BOLD))
    for i, (path, size, is_dir) in enumerate(items, 1):
        total += size
        tag = f"{YELLOW}[DIR]{RESET} " if is_dir else ""
        print(f"    {i:>3}. {tag}{path}  {DIM}({fmt_size(size)}){RESET}")
    if not items:
        print(f"    {DIM}(nothing to remove){RESET}")
    else:
        print(f"  {DIM}Total: {fmt_size(total)}{RESET}")
    return total


def _perform_removal(items):
    """Actually delete. Returns (ok_count, fail_count)."""
    ok = 0
    fail = 0
    for path, size, is_dir in items:
        try:
            if is_dir:
                shutil.rmtree(path)
            else:
                os.remove(path)
            ok += 1
        except OSError as e:
            print(color_text(f"    Failed: {path} ({e})", fg=RED))
            fail += 1
    return ok, fail


def confirm_yes_word(prompt):
    """Require the user to type the word YES (case-insensitive) to proceed.
    ANY other input — including a bare 'y' — is treated as no."""
    try:
        resp = input(color_text(prompt, fg=YELLOW)).strip()
    except EOFError:
        return False
    return resp.upper() == "YES"


def _finish_removal(items, live_requested, assume_yes=False, require_yes=False):
    """Common tail: preview, then delete only on explicit opt-in.

    live_requested:
        None  -> interactive mode: ask after preview whether to delete
        True  -> CLI --delete: delete after confirm (or assume_yes)
        False -> CLI default: dry run only
    require_yes:
        True  -> the confirmation requires typing the word YES (any other
                 input cancels). Used for the higher-stakes Duplicates removals.
    """
    _preview_removal(items)
    if not items:
        print()
        print(color_text("  DRY RUN — nothing to delete.", fg=YELLOW, style=BOLD))
        return

    do_delete = False
    if live_requested is None:            # interactive
        print()
        print(color_text("  This was a DRY RUN — nothing has been deleted yet.", fg=YELLOW, style=BOLD))
        if require_yes:
            do_delete = confirm_yes_word(f"  Type YES to delete these {len(items)} item(s) (anything else cancels): ")
        else:
            do_delete = safe_confirm(f"  Actually delete these {len(items)} item(s)?", default=False)
    elif live_requested is True:          # CLI --delete
        if assume_yes:
            do_delete = True
        elif require_yes:
            do_delete = confirm_yes_word(f"  Type YES to delete these {len(items)} item(s) (anything else cancels): ")
        else:
            do_delete = safe_confirm(f"  Delete these {len(items)} item(s)?", default=False)
    else:                                 # CLI dry run
        print()
        print(color_text("  DRY RUN — nothing deleted. Re-run with --delete to remove.", fg=YELLOW, style=BOLD))
        return

    if not do_delete:
        print(color_text("  Cancelled — nothing deleted.", fg=YELLOW))
        return

    ok, fail = _perform_removal(items)
    print()
    report_result(fail == 0,
                  f"Removed {ok} item(s)." + (f" {fail} failed." if fail else ""),
                  f"Removed {ok} item(s), {fail} failed.")


def remove_folder(path, live_requested=None):
    screen("Remove Folder")
    print()
    path = clean_path(path)
    print(f"  {YELLOW}Target{RESET}: {path}\n")
    if not os.path.isdir(path):
        print(color_text(f"  Not a directory: {path}", fg=RED)); pause_return(); return
    total, count = folder_stats(path)
    items = [(path, total, True)]
    print(color_text(f"  Contains {count:,} file(s), {fmt_size(total)}.", fg=DIM))
    _finish_removal(items, live_requested)
    pause_return()


def remove_by_name(root, pattern, live_requested=None):
    screen("Remove Files by Name")
    print()
    root = clean_path(root)
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    items = []
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            if fnmatch.fnmatch(fn, pattern):
                p = os.path.join(dp, fn)
                items.append((p, file_size(p), False))
    items.sort(key=lambda t: t[0])
    _finish_removal(items, live_requested)
    pause_return()


def _topmost(paths):
    """Drop any path that is nested inside another path in the list, so a parent
    and its descendant aren't both scheduled for deletion (which would error)."""
    paths = sorted(set(paths))
    return [p for p in paths if not any(o != p and p.startswith(o + os.sep) for o in paths)]


def remove_folders_by_name(root, pattern, live_requested=None):
    screen("Remove Folders by Name")
    print()
    root = clean_path(root)
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); pause_return(); return
    matches = []
    for dp, dns, fns in os.walk(root):
        for d in dns:
            if fnmatch.fnmatch(d, pattern):
                matches.append(os.path.join(dp, d))
    # Only delete top-most matches (a matched parent already covers matched children).
    items = [(m, folder_stats(m)[0], True) for m in _topmost(matches)]
    _finish_removal(items, live_requested)
    pause_return()


def _gather_files(folders, ext=None):
    """All files under the given folders, optionally filtered by extension."""
    files = []
    for folder in folders:
        folder = clean_path(folder)
        if not os.path.isdir(folder):
            continue
        for dp, dns, fns in os.walk(folder):
            for fn in fns:
                if ext and not fn.lower().endswith("." + ext.lstrip(".").lower()):
                    continue
                files.append(os.path.join(dp, fn))
    return files


def remove_duplicates_by_name(folders, live_requested=None, ext=None):
    screen("Remove Duplicates (by Name)")
    print()
    print(f"  {YELLOW}Folders{RESET}: {', '.join(folders)}")
    if ext:
        print(f"  {YELLOW}Extension{RESET}: .{ext.lstrip('.')}")
    print(f"  {DIM}Keeps the first occurrence of each name; removes the rest.{RESET}\n")

    files = _gather_files(folders, ext)
    groups = defaultdict(list)
    for p in files:
        groups[os.path.basename(p)].append(p)

    dups = {name: sorted(paths) for name, paths in groups.items() if len(paths) > 1}
    if not dups:
        print(color_text("  No duplicate filenames found.", fg=YELLOW))
        pause_return(); return

    print(color_text(f"  {len(dups)} duplicated name(s):", fg=BRIGHT_CYAN, style=BOLD))
    items = []
    for name in sorted(dups):
        paths = dups[name]
        print(f"    {WHITE}{name}{RESET}")
        print(f"      {GREEN}keep{RESET}   {paths[0]}")
        for p in paths[1:]:
            print(f"      {RED}remove{RESET} {p}")
            items.append((p, file_size(p), False))
    print()
    _finish_removal(items, live_requested, require_yes=True)
    pause_return()


def remove_duplicates_by_hash(folders, live_requested=None):
    screen("Remove Duplicates (by Hash)")
    print()
    print(f"  {YELLOW}Folders{RESET}: {', '.join(folders)}")
    print(f"  {DIM}Groups by SHA-256 content hash; keeps the first, removes the rest.{RESET}\n")

    files = _gather_files(folders)
    # Pre-group by size to avoid hashing unique-size files
    by_size = defaultdict(list)
    for p in files:
        by_size[file_size(p)].append(p)

    groups = defaultdict(list)
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for p in paths:
            h = _hash_file(p)
            if h:
                groups[h].append(p)

    dups = {h: sorted(paths) for h, paths in groups.items() if len(paths) > 1}
    if not dups:
        print(color_text("  No duplicate content found.", fg=YELLOW))
        pause_return(); return

    print(color_text(f"  {len(dups)} set(s) of identical files:", fg=BRIGHT_CYAN, style=BOLD))
    items = []
    for h in sorted(dups):
        paths = dups[h]
        print(f"    {DIM}{h[:16]}…  ({fmt_size(file_size(paths[0]))}){RESET}")
        print(f"      {GREEN}keep{RESET}   {paths[0]}")
        for p in paths[1:]:
            print(f"      {RED}remove{RESET} {p}")
            items.append((p, file_size(p), False))
    print()
    _finish_removal(items, live_requested, require_yes=True)
    pause_return()


def remove_duplicates_by_fuzzy_name(folders, live_requested=None, assume_yes=False):
    """Remove fuzzy duplicates: same grouping as Find Duplicates by Fuzzy Name
    (close name — dup-style endings stripped or 85%+ similar, same extension —
    plus sizes within 1%). Keeps the shortest/cleanest name in each group;
    the rest are listed for removal. Dry run + typed YES to delete."""
    screen("Remove Duplicates (by Fuzzy Name)")
    print()
    folders = [clean_path(f) for f in folders if f]
    valid = [f for f in folders if os.path.isdir(f)]
    for f in folders:
        if f not in valid:
            print(color_text(f"  Skipping (not a directory): {f}", fg=YELLOW))
    if not valid:
        print(color_text("  No valid folders to scan.", fg=RED)); pause_return(); return
    print(f"  {YELLOW}Folders{RESET}: {', '.join(valid)}")
    print(f"  {DIM}Close names (duplicate-style endings stripped or 85%+ similar, same "
          f"extension) with sizes within 1%. Keeps the shortest/cleanest name; "
          f"removes the rest. Hidden files/folders are skipped.{RESET}\n")

    dup_groups = _fuzzy_dup_groups(valid)
    if not dup_groups:
        print(color_text("  No fuzzy-duplicate files found.", fg=YELLOW))
        pause_return(); return

    print(color_text(f"  {len(dup_groups)} fuzzy-duplicate group(s):", fg=BRIGHT_CYAN, style=BOLD))
    items = []
    for group in dup_groups:
        print(f"    {WHITE}{group[0][0]}{RESET}")
        (name, _stem, _ext, size, dp) = group[0]
        print(f"      {BRIGHT_CYAN}keep{RESET}   {os.path.join(dp, name)}  {DIM}({fmt_size(size)}){RESET}")
        for (name, _stem, _ext, size, dp) in group[1:]:
            p = os.path.join(dp, name)
            print(f"      {BRIGHT_YELLOW}remove{RESET} {p}  {DIM}({fmt_size(size)}){RESET}")
            items.append((p, size, False))
    print()
    _finish_removal(items, live_requested, assume_yes=assume_yes, require_yes=True)
    pause_return()


def remove_zero_size_files(folders, live_requested=None, assume_yes=False):
    """Remove empty (0-byte) files under the given folders. Hidden
    files/folders are skipped — so intentional placeholders like .gitkeep are
    never touched. Dry run + confirm before anything is deleted."""
    screen("Remove Files of 0 Size")
    print()
    folders = [clean_path(f) for f in folders if f]
    valid = [f for f in folders if os.path.isdir(f)]
    for f in folders:
        if f not in valid:
            print(color_text(f"  Skipping (not a directory): {f}", fg=YELLOW))
    if not valid:
        print(color_text("  No valid folders to scan.", fg=RED)); pause_return(); return
    print(f"  {YELLOW}Folders{RESET}: {', '.join(valid)}")
    print(f"  {DIM}Removes empty (0-byte) files. Hidden files/folders are skipped.{RESET}\n")

    items = []
    for folder in valid:
        for dp, dns, fns in os.walk(folder):
            dns[:] = [d for d in dns if not d.startswith(".") and d.lower() not in EXCLUDED_DIR_NAMES]
            for fn in fns:
                if fn.startswith(".") or is_excluded_file(fn):
                    continue
                p = os.path.join(dp, fn)
                try:
                    if os.path.getsize(p) == 0 and os.path.isfile(p):
                        items.append((p, 0, False))
                except OSError:
                    continue
    items.sort(key=lambda t: t[0])

    if not items:
        print(color_text("  No 0-byte files found.", fg=YELLOW))
        pause_return(); return

    _finish_removal(items, live_requested, assume_yes=assume_yes)
    pause_return()


def _hash_file(path, chunk=1 << 20):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                b = f.read(chunk)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


# =============================================================================
# CLEAN UP  (junk files, old log entries; dry-run by default)
# =============================================================================
LOG_PURGE_DIR   = os.path.expanduser("~/Documents/log")
LOG_PURGE_DAYS  = 90
_LOG_TS_RE      = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")


def cleanup_junk_files(root, live_requested=None, assume_yes=False):
    """Find every .DS_Store / desktop.ini under root (recursively, hidden
    folders included) and remove them — DRY RUN preview + confirm, exactly
    like the Remove actions."""
    screen("Clean Up — Remove Junk Files")
    print()
    root = clean_path(root)
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Targets{RESET}: .DS_Store, desktop.ini\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED))
        return
    items = []
    for dp, dns, fns in os.walk(root):
        prune_dirs(dns)
        for fn in fns:
            if is_excluded_file(fn):
                full = os.path.join(dp, fn)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                items.append((full, size, False))
    items.sort(key=lambda i: i[0])
    _finish_removal(items, live_requested, assume_yes=assume_yes)


def _purge_scan_file(path, cutoff):
    """Read one log file and split it at cutoff. Returns (kept_lines,
    purge_count).

    Block-aware: a line with a [YYYY-MM-DD HH:MM:SS] timestamp decides
    keep/purge for itself AND every untimestamped line that follows it (an
    entry's body and trailing blank line belong to its header). Lines before
    any timestamp are kept."""
    kept = []
    purged = 0
    keep_current = True
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            m = _LOG_TS_RE.search(line)
            if m:
                try:
                    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    keep_current = ts >= cutoff
                except ValueError:
                    keep_current = True
            if keep_current:
                kept.append(line)
            else:
                purged += 1
    return kept, purged


def cleanup_purge_logs(folder=LOG_PURGE_DIR, days=LOG_PURGE_DAYS,
                       live_requested=None, assume_yes=False):
    """Purge entries older than N days from every .log file in folder.
    DRY RUN preview + confirm; a .bak backup of each changed file is written
    before it is rewritten. Empty files after purging are preserved."""
    screen("Clean Up — Purge Old Log Files")
    print()
    folder = clean_path(folder)
    try:
        days = max(0, int(days))
    except (TypeError, ValueError):
        days = LOG_PURGE_DAYS
    cutoff = datetime.fromtimestamp(time.time() - days * 86400)
    print(f"  {YELLOW}Log folder{RESET}  : {folder}")
    print(f"  {YELLOW}Days to keep{RESET}: {days}")
    print(f"  {YELLOW}Cutoff{RESET}      : entries before "
          f"{cutoff.strftime('%-m/%-d/%y %-I:%M ') + cutoff.strftime('%p').lower()} are purged")
    print()
    if not os.path.isdir(folder):
        print(color_text(f"  Not a directory: {folder}", fg=RED))
        return

    log_files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".log"))
    if not log_files:
        print(color_text(f"  No .log files found in {folder}.", fg=YELLOW))
        return

    plans = []                       # (path, kept_lines, purge_count)
    for fn in log_files:
        path = os.path.join(folder, fn)
        try:
            kept, purge_count = _purge_scan_file(path, cutoff)
        except OSError as e:
            print(color_text(f"  ⚠ {fn}: {e}", fg=YELLOW))
            continue
        plans.append((path, kept, purge_count))

    name_w = max([len(os.path.basename(p)) for p, _, _ in plans] + [len("Log File")])
    name_w = min(name_w, 40)
    print(color_text(f"  {'Log File':<{name_w}}  {'Purge':>8}  {'Keep':>8}  {'Size':>10}",
                     fg=YELLOW, style=BOLD))
    print(f"  {DIM}{'-' * name_w}  {'-' * 8}  {'-' * 8}  {'-' * 10}{RESET}")
    total_purge = 0
    for path, kept, purge_count in plans:
        total_purge += purge_count
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        purge_disp = (color_text(f"{purge_count:>8,}", fg=RED, style=BOLD)
                      if purge_count else f"{purge_count:>8,}")
        print(f"  {WHITE}{os.path.basename(path)[:name_w].ljust(name_w)}{RESET}  "
              f"{purge_disp}  {len(kept):>8,}  {fmt_size(size):>10}")

    print()
    if total_purge == 0:
        print(color_text(f"  Nothing to purge — no entries older than {days} days.",
                         fg=GREEN, style=BOLD))
        return

    do_purge = False
    if live_requested is None:                # interactive
        print(color_text("  This was a DRY RUN — nothing has been purged yet.",
                         fg=YELLOW, style=BOLD))
        do_purge = safe_confirm(f"  Actually purge {total_purge:,} old line(s) "
                                f"from {len(plans)} file(s)?", default=False)
    elif live_requested is True:              # CLI --delete
        do_purge = True if assume_yes else safe_confirm(
            f"  Purge {total_purge:,} old line(s) from {len(plans)} file(s)?", default=False)
    else:                                     # CLI dry run
        print(color_text("  DRY RUN — nothing purged. Re-run with --delete to purge.",
                         fg=YELLOW, style=BOLD))
        return
    if not do_purge:
        print(color_text("  Cancelled — nothing purged.", fg=YELLOW))
        return

    ok = fail = 0
    for path, kept, purge_count in plans:
        if purge_count == 0:
            continue
        try:
            shutil.copy2(path, path + ".bak")
            with open(path, "w") as fh:
                fh.writelines(kept)
            ok += 1
        except OSError as e:
            fail += 1
            print(color_text(f"  ✗ {os.path.basename(path)}: {e}", fg=RED))
    print()
    report_result(fail == 0,
                  f"Purged {total_purge:,} line(s) from {ok} file(s). "
                  "Backups saved with a .bak extension.",
                  f"Purged {ok} file(s), {fail} failed.")


# =============================================================================
# EJECT EXTERNAL DRIVES  (macOS)
# =============================================================================
def _external_drives():
    """Scan /Volumes and return the mounted external drives as a list of
    {identifier, name, size, mount_point} dicts (deduplicated by disk).

    A volume counts as external when `diskutil info` reports Internal: No,
    a Protocol of USB/Thunderbolt/SATA/FireWire, or Removable Media. Same
    detection logic as the standalone ejectDrives.py script."""
    drives = []
    volumes_path = "/Volumes"
    if not os.path.isdir(volumes_path):
        return drives
    for volume_name in sorted(os.listdir(volumes_path)):
        volume_path = os.path.join(volumes_path, volume_name)
        if not os.path.ismount(volume_path):
            continue
        try:
            info_result = subprocess.run(["diskutil", "info", volume_path],
                                         capture_output=True, text=True)
        except OSError:
            return drives                    # diskutil unavailable (not macOS)
        if info_result.returncode != 0:
            continue

        is_external = False
        disk_identifier = None
        size = "—"
        for line in info_result.stdout.split("\n"):
            if "Protocol:" in line:
                if line.split(":")[1].strip().lower() in ("usb", "thunderbolt",
                                                          "sata", "firewire"):
                    is_external = True
            elif "Removable Media:" in line:
                if "Removable" in line or "Yes" in line:
                    is_external = True
            elif "Internal:" in line:
                if "No" in line:
                    is_external = True
            elif "Part of Whole:" in line:
                disk_identifier = line.split(":")[1].strip()
            elif "Device Identifier:" in line and not disk_identifier:
                m = re.match(r"(disk\d+)", line.split(":")[1].strip())
                if m:
                    disk_identifier = m.group(1)
            elif ("Disk Size:" in line or "Container Total Space:" in line
                  or "Volume Total Space:" in line):
                m = re.search(r"\((\d[\d,]*)\s*Bytes\)", line)
                if m:
                    size = fmt_size(int(m.group(1).replace(",", "")))

        if is_external and disk_identifier:
            drives.append({"identifier": disk_identifier, "name": volume_name,
                           "size": size, "mount_point": volume_path})

    # One entry per physical disk (a disk may mount several volumes)
    seen = set()
    unique = []
    for d in drives:
        if d["identifier"] not in seen:
            seen.add(d["identifier"])
            unique.append(d)
    return unique


def _eject_via_finder(volume_name):
    """AppleScript fallback — same as clicking the eject button in Finder."""
    script = f'tell application "Finder"\n    eject disk "{volume_name}"\nend tell'
    try:
        result = subprocess.run(["osascript", "-e", script],
                                capture_output=True, text=True)
    except OSError as e:
        return False, str(e)
    if result.returncode == 0:
        return True, "Ejected via Finder"
    return False, result.stderr.strip()


def _eject_drive(drive, force=False):
    """Eject one drive dict. force=True force-unmounts the whole disk first.
    Returns (success, message)."""
    identifier = drive["identifier"]
    try:
        if force:
            unmount = subprocess.run(["diskutil", "unmountDisk", "force", identifier],
                                     capture_output=True, text=True)
            if unmount.returncode != 0:
                return False, f"Force unmount failed: {unmount.stderr.strip()}"
        result = subprocess.run(["diskutil", "eject", identifier],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        if not force:                         # Finder fallback (non-force only)
            ok, msg = _eject_via_finder(drive["name"])
            if ok:
                return True, msg
        return False, result.stderr.strip()
    except OSError as e:
        return False, str(e)


def _print_drive_list(drives):
    name_w = max([len(d["name"]) for d in drives] + [4])
    size_w = max([len(d["size"]) for d in drives] + [4])
    print(color_text(f"  {'#':>2}  {'Name':<{name_w}}  {'Size':>{size_w}}  Mount Point",
                     fg=WHITE, style=BOLD))
    print(f"  {'-' * 2}  {'-' * name_w}  {'-' * size_w}  {'-' * 20}")
    for i, d in enumerate(drives, 1):
        print(f"  {i:>2}  {d['name']:<{name_w}}  {d['size']:>{size_w}}  "
              f"{DIM}{d['mount_point']}{RESET}")


def _eject_loop(drives, force=False):
    """Eject each drive with a per-drive status line.
    Returns (ok_count, failed_drives)."""
    ok = 0
    failed = []
    for d in drives:
        verb = "Force ejecting" if force else "Ejecting"
        sys.stdout.write(color_text(f"  {verb} {d['name']}... ", fg=CYAN))
        sys.stdout.flush()
        success, msg = _eject_drive(d, force=force)
        if success:
            print(color_text("Success", fg=BRIGHT_GREEN, style=BOLD))
            ok += 1
        else:
            print(color_text("Failed", fg=BRIGHT_RED, style=BOLD))
            if msg:
                print(color_text(f"    {msg}", fg=RED))
            failed.append(d)
    return ok, failed


def _eject_screen(live_requested, assume_yes, force):
    screen("Eject All External Drives")
    print()
    if sys.platform != "darwin":
        print(color_text("  Eject uses diskutil and is only available on macOS.", fg=RED))
        return

    drives = _external_drives()
    if not drives:
        print(color_text("  No external drives found.", fg=YELLOW, style=BOLD))
        return

    _print_drive_list(drives)
    print()

    do_eject = False
    if live_requested is None or (live_requested is True and not assume_yes):
        do_eject = safe_confirm(f"  Eject all {len(drives)} drive(s)?", default=False)
    else:
        do_eject = True                       # CLI --yes
    if not do_eject:
        print(color_text("  Cancelled — nothing ejected.", fg=YELLOW))
        return

    print()
    ok, failed = _eject_loop(drives, force=force)

    # Offer to force-eject anything that would not let go (Spotlight, etc.)
    if failed and not force:
        print()
        force_it = (True if assume_yes and live_requested is True
                    else safe_confirm(f"  Force eject the {len(failed)} failed drive(s)?",
                                      default=False))
        if force_it:
            print()
            ok2, failed = _eject_loop(failed, force=True)
            ok += ok2

    print()
    report_result(not failed,
                  f"Ejected {ok} drive(s).",
                  f"Ejected {ok} drive(s), {len(failed)} failed — "
                  "close any apps using the drive(s) and try again.")


def eject_external_drives(live_requested=None, assume_yes=False, force=False):
    """List the mounted external drives and eject them all after a confirm
    (macOS). Failures offer a force eject. The screen output is also appended
    to ~/Documents/log/fm.log."""
    with _ActivityLog():
        _eject_screen(live_requested, assume_yes, force)


# =============================================================================
# MONITOR FILE ACTIVITY  (real-time, stdlib polling)
# =============================================================================
MONITOR_CSV          = os.path.expanduser("~/Documents/log/fmMonitor.csv")
MONITOR_POLL_SECONDS = 1.0


def _parse_ext_filter(raw):
    """Normalize an extension filter ('jpg, .PNG' or ['jpg','png']) to a
    lowercase set without dots. Empty/blank input -> empty set (= all files)."""
    if not raw:
        return set()
    parts = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    return {str(p).strip().lstrip(".").lower() for p in parts if str(p).strip()}


def _monitor_snapshot(root, recursive, exts):
    """One poll of the watched folder: {relative path: (mtime, size)}.

    Hidden files/folders ARE included (their activity is often the point);
    junk files (.DS_Store, desktop.ini) and $RECYCLE.BIN are skipped.
    exts: set of extensions to watch (empty = every file)."""
    snap = {}

    def want(fn):
        if is_excluded_file(fn):
            return False
        return not exts or os.path.splitext(fn)[1][1:].lower() in exts

    if recursive:
        for dp, dns, fns in os.walk(root):
            prune_dirs(dns)
            for fn in fns:
                if not want(fn):
                    continue
                full = os.path.join(dp, fn)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                snap[os.path.relpath(full, root)] = (st.st_mtime, st.st_size)
    else:
        try:
            names = os.listdir(root)
        except OSError:
            return snap
        for fn in names:
            full = os.path.join(root, fn)
            if not want(fn) or not os.path.isfile(full):
                continue
            try:
                st = os.stat(full)
            except OSError:
                continue
            snap[fn] = (st.st_mtime, st.st_size)
    return snap


def _diff_snapshots(old, new):
    """Compare two snapshots. Returns [(event, relpath, size)] sorted by
    path; event is CREATED / MODIFIED / DELETED."""
    events = []
    for rel, meta in new.items():
        if rel not in old:
            events.append(("CREATED", rel, meta[1]))
        elif meta != old[rel]:
            events.append(("MODIFIED", rel, meta[1]))
    for rel in old:
        if rel not in new:
            events.append(("DELETED", rel, None))
    return sorted(events, key=lambda e: e[1])


def _monitor_ts():
    """Event timestamp in the display format m/d/yy h:mm:ss am."""
    now = datetime.now()
    return now.strftime("%-m/%-d/%y %-I:%M:%S ") + now.strftime("%p").lower()


class _MonitorLog:
    """Real-time event writer. output='log' appends lines to the FM activity
    log (~/Documents/log/fm.log); output='csv' appends rows to fmMonitor.csv
    in the same folder (header written when the file is new). Every event is
    flushed immediately so `tail -f` tracks the screen live. Write failures
    never interrupt monitoring."""

    def __init__(self, output, folder, recursive, exts):
        self.output = output
        self.path = MONITOR_CSV if output == "csv" else ACTIVITY_LOG
        self._fh = None
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            is_new = not os.path.exists(self.path) or os.path.getsize(self.path) == 0
            self._fh = open(self.path, "a", newline="" if output == "csv" else None)
            if output == "csv":
                self._csv = csv.writer(self._fh)
                if is_new:
                    self._csv.writerow(["Timestamp", "Filename", "Folder", "Event"])
            else:
                ext_disp = ", ".join(sorted(exts)) if exts else "all"
                self._fh.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                self._fh.write(f"Monitor File Activity — {folder}\n")
                self._fh.write(f"Recursive: {'Yes' if recursive else 'No'}   "
                               f"Extensions: {ext_disp}\n")
            self._fh.flush()
        except OSError:
            self._fh = None
        self.opened = self._fh is not None

    def event(self, ts, event, rel, folder):
        if not self._fh:
            return
        try:
            if self.output == "csv":
                self._csv.writerow([ts, os.path.basename(rel),
                                    os.path.join(folder, os.path.dirname(rel)).rstrip("/"),
                                    event.lower()])
            else:
                self._fh.write(f"{ts}  {event:<9} {rel}\n")
            self._fh.flush()
        except OSError:
            pass

    def close(self, summary=""):
        if not self._fh:
            return
        try:
            if self.output == "log":
                if summary:
                    self._fh.write(summary + "\n")
                self._fh.write("\n")
            self._fh.flush()
            self._fh.close()
        except OSError:
            pass
        self._fh = None


_MONITOR_EVENT_COLORS = {"CREATED": GREEN, "MODIFIED": YELLOW, "DELETED": RED}


def monitor_activity(folder, recursive=True, exts=None, output="log",
                     profile_name=None):
    """Watch a folder for file activity (created / modified / deleted) and
    report each event in real time — on screen and to fm.log (or
    fmMonitor.csv). Polls once a second using snapshot diffs (no third-party
    packages). [Q/ESC] stops and returns to the menu (Ctrl-C non-TTY)."""
    exts = _parse_ext_filter(exts)
    screen("Monitor File Activity")
    print()
    if profile_name:
        print(f"  {YELLOW}Profile{RESET}   : {profile_name}")
    print(f"  {YELLOW}Folder{RESET}    : {folder}")
    print(f"  {YELLOW}Recursive{RESET} : {'Yes' if recursive else 'No'}")
    print(f"  {YELLOW}Extensions{RESET}: {', '.join(sorted(exts)) if exts else 'all files'}")
    log_disp = MONITOR_CSV.replace(os.path.expanduser('~'), '~') if output == "csv" \
        else ACTIVITY_LOG.replace(os.path.expanduser('~'), '~')
    print(f"  {YELLOW}Logging to{RESET}: {log_disp}")
    print()

    if not os.path.isdir(folder):
        print(color_text(f"  Not a directory: {folder}", fg=RED))
        return

    is_tty = sys.stdin.isatty()
    stop_hint = "[Q/ESC] Stop" if is_tty else "Ctrl-C to stop"
    print(color_text(f"  Monitoring... {stop_hint}. Events appear below as they happen.",
                     fg=CYAN, style=BOLD))
    print()

    counts = {"CREATED": 0, "MODIFIED": 0, "DELETED": 0}
    mlog = _MonitorLog(output, folder, recursive, exts)
    if mlog._fh is None:
        print(color_text(f"  ⚠ Could not open {log_disp} — events will show on screen only.",
                         fg=YELLOW))
        print()
    baseline = _monitor_snapshot(folder, recursive, exts)

    def poll_once():
        nonlocal baseline
        snap = _monitor_snapshot(folder, recursive, exts)
        for event, rel, size in _diff_snapshots(baseline, snap):
            ts = _monitor_ts()
            counts[event] += 1
            colored = color_text(f"{event:<9}", fg=_MONITOR_EVENT_COLORS[event], style=BOLD)
            size_disp = f"  {DIM}({fmt_size(size)}){RESET}" if size is not None else ""
            print(f"  {DIM}{ts}{RESET}  {colored} {rel}{size_disp}")
            mlog.event(ts, event, rel, folder)
        baseline = snap

    try:
        if is_tty:
            import termios, tty, select
            fd = sys.stdin.fileno()
            old_attr = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while True:
                    r, _, _ = select.select([fd], [], [], MONITOR_POLL_SECONDS)
                    if r:
                        ch = os.read(fd, 1)
                        if ch in (b"q", b"Q", b"\x1b"):
                            break
                    poll_once()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_attr)
        else:
            while True:
                time.sleep(MONITOR_POLL_SECONDS)
                poll_once()
    except KeyboardInterrupt:
        pass
    finally:
        total = sum(counts.values())
        summary = (f"Stopped — {total} event(s): {counts['CREATED']} created, "
                   f"{counts['MODIFIED']} modified, {counts['DELETED']} deleted.")
        mlog.close(summary)

    print()
    print(color_text(f"  {summary}", fg=WHITE, style=BOLD))
    if mlog.opened:
        print(f"  {DIM}Activity logged to {log_disp}{RESET}")


# =============================================================================
# SYNC  (one-way push; dry-run by default)
# =============================================================================
def _load_config_profiles(key):
    """Return (profiles, error) — a profile list (e.g. syncProfiles,
    monitorProfiles) from fmConfig.json. A missing config file or a missing
    key simply means no profiles (empty list, no error); a broken file
    returns an error string."""
    try:
        with open(CONFIG_FILE, "r") as fh:
            cfg = json.load(fh)
    except OSError:
        return [], ""
    except ValueError as e:
        return [], f"fmConfig.json is not valid JSON: {e}"
    profs = cfg.get(key, [])
    if not isinstance(profs, list):
        return [], f"fmConfig.json: {key} must be a list"
    return [p for p in profs if isinstance(p, dict)], ""


def _load_sync_profiles():
    return _load_config_profiles("syncProfiles")


def _load_monitor_profiles():
    return _load_config_profiles("monitorProfiles")


def _scan_sync_side(root, recursive, exclude_hidden):
    """Scan one side of a sync: {relative path: (size, mtime)}.

    Junk files (.DS_Store, desktop.ini) and excluded folders ($RECYCLE.BIN)
    are always skipped; hidden files/folders only when exclude_hidden."""
    out = {}
    if recursive:
        for dp, dns, fns in os.walk(root):
            prune_dirs(dns)
            if exclude_hidden:
                dns[:] = [d for d in dns if not d.startswith(".")]
            for fn in fns:
                if is_excluded_file(fn):
                    continue
                if exclude_hidden and fn.startswith("."):
                    continue
                full = os.path.join(dp, fn)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                out[os.path.relpath(full, root)] = (st.st_size, st.st_mtime)
    else:
        try:
            names = os.listdir(root)
        except OSError:
            return out
        for fn in names:
            full = os.path.join(root, fn)
            if not os.path.isfile(full) or is_excluded_file(fn):
                continue
            if exclude_hidden and fn.startswith("."):
                continue
            try:
                st = os.stat(full)
            except OSError:
                continue
            out[fn] = (st.st_size, st.st_mtime)
    return out


def _sync_plan(src_map, dst_map, conflict):
    """Decide what to push src → dst. Returns (new_rels, upd_rels, skipped_zero).

    A file that exists on both sides is only copied when the source wins the
    conflict rule: 'newest' = source modified time is newer (1s tolerance for
    coarse filesystem timestamps), 'largest' = source is bigger.

    Zero-byte source files are never copied (usually incomplete/placeholder
    files) and are counted in skipped_zero instead."""
    new_rels, upd_rels = [], []
    skipped_zero = 0
    for rel in sorted(src_map):
        s_size, s_mtime = src_map[rel]
        if s_size == 0:
            skipped_zero += 1
            continue
        if rel not in dst_map:
            new_rels.append(rel)
            continue
        d_size, d_mtime = dst_map[rel]
        if conflict == "largest":
            if s_size > d_size:
                upd_rels.append(rel)
        else:                                   # newest (default)
            if s_mtime > d_mtime + 1:
                upd_rels.append(rel)
    return new_rels, upd_rels, skipped_zero


def _fmt_mtime(ts):
    """Modified time in the display format m/d/yy h:mm am."""
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%-m/%-d/%y %-I:%M ") + dt.strftime("%p").lower()
    except (OSError, OverflowError, ValueError):
        return "—"


def _sync_screen(folder_a, folder_b, direction, recursive, conflict,
                 exclude_hidden, live_requested, assume_yes, profile_name):
    screen("Sync Folders")
    print()
    if profile_name:
        print(f"  {YELLOW}Profile{RESET}  : {profile_name}")
    print(f"  {YELLOW}Folder A{RESET} : {folder_a}")
    print(f"  {YELLOW}Folder B{RESET} : {folder_b}")
    if direction == "both":
        print(f"  {YELLOW}Direction{RESET}: A ↔ B  (two-way: each side receives the other's new/updated files)")
    else:
        src_lbl, dst_lbl = ("B", "A") if direction == "b2a" else ("A", "B")
        print(f"  {YELLOW}Direction{RESET}: {src_lbl} → {dst_lbl}  (push new/updated files from {src_lbl} to {dst_lbl})")
    print(f"  {YELLOW}Options{RESET}  : Recursive: {'Yes' if recursive else 'No'}   "
          f"Conflict: {'Newest' if conflict == 'newest' else 'Largest'} wins   "
          f"Hidden files: {'Excluded' if exclude_hidden else 'Included'}")
    print()

    for path, lbl in ((folder_a, "A"), (folder_b, "B")):
        if not os.path.isdir(path):
            print(color_text(f"  Folder {lbl} is not a directory: {path}", fg=RED))
            return

    a_map = _scan_sync_side(folder_a, recursive, exclude_hidden)
    b_map = _scan_sync_side(folder_b, recursive, exclude_hidden)

    # Each pass is one push: (src, dst, src_lbl, dst_lbl, src_map, dst_map,
    # new_rels, upd_rels, skipped_zero). Two-way = both passes; a file on both
    # sides can only win the conflict rule in one direction, so the two passes
    # never fight over the same file.
    passes = []
    if direction in ("a2b", "both"):
        new_r, upd_r, sk = _sync_plan(a_map, b_map, conflict)
        passes.append((folder_a, folder_b, "A", "B", a_map, b_map, new_r, upd_r, sk))
    if direction in ("b2a", "both"):
        new_r, upd_r, sk = _sync_plan(b_map, a_map, conflict)
        passes.append((folder_b, folder_a, "B", "A", b_map, a_map, new_r, upd_r, sk))

    total = sum(len(p[6]) + len(p[7]) for p in passes)
    copy_desc = ("between A and B" if direction == "both"
                 else f"from {passes[0][2]} to {passes[0][3]}")

    if total == 0:
        if direction == "both":
            print(color_text("  Nothing to copy — A and B already have each "
                             "other's new/updated files.", fg=GREEN, style=BOLD))
        else:
            print(color_text(f"  Nothing to copy — {passes[0][3]} already has every "
                             f"new/updated file from {passes[0][2]}.", fg=GREEN, style=BOLD))
        print(f"  {DIM}Scanned {len(a_map):,} file(s) in A, "
              f"{len(b_map):,} in B.{RESET}")
        for p in passes:
            if p[8]:
                print(f"  {DIM}Skipped {p[8]:,} zero-byte file(s) in {p[2]} "
                      f"(never copied).{RESET}")
        return

    total_new = sum(len(p[6]) for p in passes)
    total_upd = sum(len(p[7]) for p in passes)
    total_bytes = sum(p[4][r][0] for p in passes for r in p[6] + p[7])
    print(color_text(f"  {total_new} new, {total_upd} updated — "
                     f"{fmt_size(total_bytes)} to copy {copy_desc}:",
                     fg=WHITE, style=BOLD))
    for p in passes:
        if p[8]:
            print(f"  {DIM}Skipped {p[8]:,} zero-byte file(s) in {p[2]} "
                  f"(never copied).{RESET}")

    for src, dst, src_lbl, dst_lbl, src_map, dst_map, new_rels, upd_rels, _sk in passes:
        if not new_rels and not upd_rels:
            if direction == "both":
                print()
                print(color_text(f"  {src_lbl} → {dst_lbl}: nothing to copy.", fg=GREEN))
            continue
        print()
        if direction == "both":
            print(color_text(f"  {src_lbl} → {dst_lbl}:", fg=CYAN, style=BOLD))
        print(color_text(f"  {'Action':<7} {'Size':>10}  {'Modified':<17} File",
                         fg=WHITE, style=BOLD))
        print(f"  {'-' * 7} {'-' * 10}  {'-' * 17} {'-' * 30}")
        upd_set = set(upd_rels)
        for rel in sorted(new_rels + upd_rels):
            s_size, s_mtime = src_map[rel]
            if rel in upd_set:
                act = color_text(f"{'UPDATE':<7}", fg=YELLOW)
                d_size, d_mtime = dst_map[rel]
                tail = f"  {DIM}(replaces {fmt_size(d_size)}, {_fmt_mtime(d_mtime)}){RESET}"
            else:
                act = color_text(f"{'NEW':<7}", fg=GREEN)
                tail = ""
            print(f"  {act} {fmt_size(s_size):>10}  {_fmt_mtime(s_mtime):<17} {rel}{tail}")

    # Copy only on explicit opt-in — same safety model as Remove.
    print()
    do_copy = False
    if live_requested is None:                # interactive
        print(color_text("  This was a DRY RUN — nothing has been copied yet.",
                         fg=YELLOW, style=BOLD))
        do_copy = safe_confirm(f"  Actually copy these {total} file(s) "
                               f"{copy_desc}?", default=False)
    elif live_requested is True:              # CLI --copy
        do_copy = True if assume_yes else safe_confirm(
            f"  Copy these {total} file(s) {copy_desc}?", default=False)
    else:                                     # CLI dry run
        print(color_text("  DRY RUN — nothing copied. Re-run with --copy to sync.",
                         fg=YELLOW, style=BOLD))
        return

    if not do_copy:
        print(color_text("  Cancelled — nothing copied.", fg=YELLOW))
        return

    ok = fail = 0
    copied_bytes = 0
    for src, dst, src_lbl, dst_lbl, src_map, dst_map, new_rels, upd_rels, _sk in passes:
        for rel in new_rels + upd_rels:
            s_path = os.path.join(src, rel)
            d_path = os.path.join(dst, rel)
            try:
                os.makedirs(os.path.dirname(d_path), exist_ok=True)
                shutil.copy2(s_path, d_path)  # copy2 preserves mtime for future 'newest' runs
                ok += 1
                copied_bytes += src_map[rel][0]
            except OSError as e:
                fail += 1
                print(color_text(f"  ✗ {src_lbl} → {dst_lbl} {rel}: {e}", fg=RED))
    print()
    report_result(fail == 0,
                  f"Copied {ok} file(s) ({fmt_size(copied_bytes)}) {copy_desc}.",
                  f"Copied {ok} file(s) ({fmt_size(copied_bytes)}) {copy_desc}, {fail} failed.")


def sync_folders(folder_a, folder_b, direction, recursive=True,
                 conflict="newest", exclude_hidden=True, live_requested=None,
                 assume_yes=False, profile_name=None):
    """Folder sync: push new/updated files from one folder into the other
    (A → B or B → A), or both ways at once (direction 'both' — each side
    receives the other's new/updated files; the conflict rule decides which
    copy wins when a file exists on both sides). Nothing is ever deleted,
    and nothing is copied until explicitly confirmed (interactive y, or
    --copy on the CLI) — the preview is a DRY RUN. The screen output is
    also appended to ~/Documents/log/fm.log."""
    with _ActivityLog():
        _sync_screen(folder_a, folder_b, direction, recursive, conflict,
                     exclude_hidden, live_requested, assume_yes, profile_name)


def _parse_sync_direction(raw):
    """Normalize a profile/CLI direction value to a2b, b2a, or both."""
    d = str(raw).lower()
    if d in ("both", "2way", "twoway", "two-way", "ab", "a2b+b2a"):
        return "both"
    if d in ("btoa", "b2a"):
        return "b2a"
    return "a2b"


def _run_sync_profile(pr, live_requested=None, assume_yes=False):
    """Run one syncProfiles entry from fmConfig.json (defaults: AtoB,
    recursive, newest wins, hidden excluded). Still previews + confirms."""
    folder_a = clean_path(str(pr.get("folderA", "")))
    folder_b = clean_path(str(pr.get("folderB", "")))
    direction = _parse_sync_direction(pr.get("direction", "AtoB"))
    conflict = "largest" if str(pr.get("conflict", "newest")).lower() == "largest" else "newest"
    sync_folders(folder_a, folder_b, direction,
                 recursive=bool(pr.get("recursive", True)),
                 conflict=conflict,
                 exclude_hidden=bool(pr.get("excludeHidden", True)),
                 live_requested=live_requested, assume_yes=assume_yes,
                 profile_name=pr.get("name") or "(unnamed profile)")
    pause_return()


# =============================================================================
# ZIP
# =============================================================================
def zip_subfolders(target, dest=None, remove_after=False):
    screen("Zip SubFolders")
    print()
    target = clean_path(target)
    dest = clean_path(dest) if dest else os.getcwd()
    print(f"  {YELLOW}Source{RESET}: {target}")
    print(f"  {YELLOW}Dest{RESET}  : {dest}")
    print(f"  {YELLOW}Remove source after zip{RESET}: {'Yes' if remove_after else 'No'}\n")

    if not os.path.isdir(target):
        print(color_text(f"  Not a directory: {target}", fg=RED)); pause_return(); return

    os.makedirs(dest, exist_ok=True)

    # Cleanup .DS_Store / desktop.ini
    junk = 0
    for dp, dns, fns in os.walk(target):
        for fn in fns:
            if fn == ".DS_Store" or fn.lower() == "desktop.ini":
                try:
                    os.remove(os.path.join(dp, fn)); junk += 1
                except OSError:
                    pass
    print(color_text(f"  Cleaned {junk} .DS_Store/desktop.ini file(s).", fg=DIM))

    subs = immediate_subfolders(target)
    if not subs:
        print(color_text("  No subfolders to zip.", fg=YELLOW)); pause_return(); return

    if remove_after:
        remove_after = safe_confirm(color_text("  Remove each source folder after a successful zip?", fg=YELLOW), default=False)

    print(color_text(f"\n  Zipping {len(subs)} folder(s)…", fg=BRIGHT_CYAN, style=BOLD))
    ok = 0
    fail = 0
    removed = 0
    for i, name in enumerate(subs, 1):
        zip_path = os.path.join(dest, name + ".zip")
        suffix = 2
        while os.path.exists(zip_path):
            zip_path = os.path.join(dest, f"{name}-{suffix}.zip")
            suffix += 1
        base = os.path.basename(zip_path)
        print(f"    {CYAN}[{i}/{len(subs)}]{RESET} {WHITE}{name:<40}{RESET}", end="", flush=True)
        rc = subprocess.run(
            ["zip", "-r", zip_path, name],
            cwd=target, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode
        if rc == 0:
            note = f" [{base}]" if base != name + ".zip" else ""
            print(f" {BRIGHT_GREEN}OK{RESET} {DIM}({fmt_size(file_size(zip_path))}){note}{RESET}")
            ok += 1
            if remove_after:
                try:
                    shutil.rmtree(os.path.join(target, name)); removed += 1
                except OSError:
                    pass
        else:
            print(f" {BRIGHT_RED}FAILED{RESET}")
            fail += 1

    print()
    report_result(fail == 0,
                  f"Zipped {ok} folder(s)." + (f" Removed {removed} source(s)." if remove_after else ""),
                  f"Zipped {ok}, {fail} failed.")
    pause_return()


# ---- Zip viewing (ported from zipView.py) -----------------------------------
def zip_view(target):
    target = clean_path(target) if target else None
    if not target:
        screen("View Zip")
        print()
        target = ask("Zip file or folder path")
        if target:
            target = clean_path(target)
    if not target:
        return
    if os.path.isdir(target):
        _browse_zip_folder(target)
    else:
        screen("View Zip")
        print()
        _view_zip_file(target)
        pause_return()


def _browse_zip_folder(folder):
    while True:
        try:
            zips = sorted(
                f for f in os.listdir(folder)
                if not f.startswith(".") and f.lower().endswith(".zip")
                and os.path.isfile(os.path.join(folder, f))
            )
        except OSError as e:
            screen("View Zip"); print(color_text(f"\n  Cannot read folder: {e}", fg=RED)); pause_return(); return

        if not zips:
            screen(f"Select Zip — {os.path.basename(os.path.abspath(folder))}")
            print(color_text("\n  No zip files found here.", fg=YELLOW)); pause_return(); return

        # Reuse the standard arrow-navigable menu to pick a zip.
        options = [(f"{z}  ({fmt_size(file_size(os.path.join(folder, z)))})", "") for z in zips]
        choice = render_menu(
            f"Select Zip — {os.path.basename(os.path.abspath(folder))}", options,
            intro=f"Folder: {folder}   ({len(zips)} zip file(s))")
        if choice == "back":
            return
        screen("View Zip"); print()
        _view_zip_file(os.path.join(folder, zips[int(choice) - 1]))
        pause_return()


def _view_zip_file(path):
    if not os.path.isfile(path):
        print(color_text(f"  File not found: {path}", fg=RED)); return
    if not zipfile.is_zipfile(path):
        print(color_text(f"  Not a valid zip file: {path}", fg=RED)); return

    w = get_width()
    print(f"  {BOLD}{WHITE}{os.path.basename(path)}{RESET}   {DIM}{path}{RESET}\n")
    with zipfile.ZipFile(path, "r") as zf:
        entries = [e for e in zf.infolist() if not is_hidden(e.filename)]
        files = [e for e in entries if not e.is_dir()]
        dirs = [e for e in entries if e.is_dir()]

        name_w = max((len(e.filename) for e in entries), default=20)
        name_w = min(max(name_w, 20), max(w - 55, 20))
        hdr = f"  {'Name':<{name_w}}  {'Uncompressed':>13}  {'Compressed':>11}  {'Ratio':>6}  Modified"
        print(color_text(hdr, fg=WHITE, style=BOLD))
        print(f"  {DIM}{'-' * min(len(hdr), w)}{RESET}")

        tu = tc = 0
        for e in sorted(entries, key=lambda x: x.filename):
            name = e.filename[:name_w]
            try:
                mod = fmt_date(datetime(*e.date_time)) if e.date_time and e.date_time[0] >= 1980 else "—"
            except Exception:
                mod = "—"
            if e.is_dir():
                print(f"  {DIM}{YELLOW}{name:<{name_w}}{RESET}  {DIM}{'<DIR>':>13}  {'':>11}  {'':>6}  {mod}{RESET}")
                continue
            uncomp, comp = e.file_size, e.compress_size
            ratio = (1 - comp / uncomp) * 100 if uncomp > 0 else 0.0
            tu += uncomp; tc += comp
            col = GREEN if ratio > 20 else (CYAN if ratio > 0 else DIM)
            print(f"  {WHITE}{name:<{name_w}}{RESET}  {fmt_size(uncomp):>13}  "
                  f"{col}{fmt_size(comp):>11}{RESET}  {col}{ratio:5.1f}%{RESET}  {DIM}{mod}{RESET}")

        print(f"  {DIM}{'-' * min(len(hdr), w)}{RESET}")
        tr = (1 - tc / tu) * 100 if tu > 0 else 0.0
        print(f"  {BOLD}{'TOTAL (' + str(len(files)) + ' files, ' + str(len(dirs)) + ' dirs)':<{name_w}}"
              f"  {fmt_size(tu):>13}  {fmt_size(tc):>11}  {tr:5.1f}%{RESET}")
        print(f"\n  {DIM}Zip size on disk: {RESET}{BOLD}{fmt_size(file_size(path))}{RESET}")


# ---- Log Zip File (CB9Inventory via DocInfo Manager API) --------------------
LOGZIP_EXTS = (".zip", ".tar")   # .gz is intentionally not supported
CONFIG_FILE = os.path.join(SCRIPT_DIR, "fmConfig.json")


def _load_logzip_config():
    """Load fmConfig.json and return the logZip settings, or (None, error)."""
    try:
        with open(CONFIG_FILE, "r") as fh:
            cfg = json.load(fh)
    except OSError:
        return None, f"Config file not found: {CONFIG_FILE}"
    except ValueError as e:
        return None, f"Config file is not valid JSON: {e}"
    logzip = cfg.get("logZip", {})
    if not logzip.get("apiUrl") or not logzip.get("serverSecretKey"):
        return None, "fmConfig.json is missing logZip.apiUrl or logZip.serverSecretKey"
    return logzip, ""


def _sql_datetime(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _archive_contents(path):
    """Return the file listing of a .zip or .tar archive as a list of dicts
    matching the zipFileContent columns. Directories are skipped."""
    contents = []
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path, "r") as zf:
            for e in zf.infolist():
                if e.is_dir():
                    continue
                try:
                    mod = (datetime(*e.date_time).strftime("%Y-%m-%d %H:%M:%S")
                           if e.date_time and e.date_time[0] >= 1980 else "")
                except Exception:
                    mod = ""
                name = os.path.basename(e.filename.rstrip("/"))
                contents.append({
                    "fileName":         name[:255],
                    "filePath":         e.filename[:500],
                    "fileSizeBytes":    e.file_size,
                    "fileModifiedDate": mod,
                    "fileExtension":    os.path.splitext(name)[1].lstrip(".").lower()[:20],
                })
    else:  # .tar
        with tarfile.open(path, "r") as tf:
            for m in tf.getmembers():
                if not m.isfile():
                    continue
                name = os.path.basename(m.name.rstrip("/"))
                contents.append({
                    "fileName":         name[:255],
                    "filePath":         m.name[:500],
                    "fileSizeBytes":    m.size,
                    "fileModifiedDate": _sql_datetime(m.mtime) if m.mtime else "",
                    "fileExtension":    os.path.splitext(name)[1].lstrip(".").lower()[:20],
                })
    return contents


def _post_zip_log(logzip, path, contents):
    """POST one archive's info + contents to the DocInfo Manager API."""
    st = os.stat(path)
    created = getattr(st, "st_birthtime", st.st_mtime)
    fields = {
        "serverSecretKey":         logzip["serverSecretKey"],
        "zipFileName":             os.path.basename(path),
        "zipFileFolder":           os.path.dirname(os.path.abspath(path))[:300],
        "zipFileSizeBytes":        st.st_size,
        "zipFileCount":            len(contents),
        "zipFileCreatedDate":      _sql_datetime(created),
        "zipFileLastModifiedDate": _sql_datetime(st.st_mtime),
        "zipDate":                 _sql_datetime(st.st_mtime),
        "contents":                json.dumps(contents),
    }
    req = urllib.request.Request(
        logzip["apiUrl"],
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def log_zip_files(target):
    """Log a .zip/.tar file — or every one in a folder (top level only) — to
    the CB9Inventory database via the DocInfo Manager API."""
    screen("Log Zip File")
    print()

    logzip, err = _load_logzip_config()
    if not logzip:
        print(color_text(f"  {err}", fg=RED))
        pause_return(); return

    target = clean_path(target) if target else ""
    if not target:
        print(color_text("  No path entered.", fg=YELLOW))
        pause_return(); return

    if os.path.isfile(target):
        if not target.lower().endswith(LOGZIP_EXTS):
            print(color_text(f"  Not a .zip or .tar file: {target}", fg=RED))
            pause_return(); return
        archives = [target]
    elif os.path.isdir(target):
        archives = sorted(
            os.path.join(target, f) for f in os.listdir(target)
            if not f.startswith(".") and f.lower().endswith(LOGZIP_EXTS)
            and os.path.isfile(os.path.join(target, f))
        )
        if not archives:
            print(color_text("  No .zip or .tar files found (top level).", fg=YELLOW))
            pause_return(); return
    else:
        print(color_text(f"  Path not found: {target}", fg=RED))
        pause_return(); return

    print(f"  {YELLOW}Target{RESET}: {target}")
    print(f"  {YELLOW}Archives to log{RESET}: {len(archives)}\n")

    ok = fail = 0
    for path in archives:
        base = os.path.basename(path)
        print(f"  {WHITE}{base}{RESET} {DIM}({fmt_size(file_size(path))}){RESET} ... ", end="", flush=True)
        try:
            contents = _archive_contents(path)
            result = _post_zip_log(logzip, path, contents)
        except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError) as e:
            print(f"{BRIGHT_RED}FAILED{RESET} {DIM}{e}{RESET}")
            fail += 1
            continue

        if str(result.get("success", "0")) == "1":
            counts = (f"{len(contents)} files: "
                      f"+{result.get('contentInserted', 0)} "
                      f"~{result.get('contentUpdated', 0)} "
                      f"-{result.get('contentDeleted', 0)} "
                      f"={result.get('contentUnchanged', 0)}")
            print(f"{BRIGHT_GREEN}{result.get('action', 'logged').upper()}{RESET} "
                  f"{DIM}[zipFileId {result.get('zipFileId', 0)}] ({counts}){RESET}")
            ok += 1
        else:
            print(f"{BRIGHT_RED}FAILED{RESET} {DIM}{result.get('msg', 'Unknown error')}{RESET}")
            fail += 1

    print()
    report_result(fail == 0,
                  f"Logged {ok} archive(s) to CB9Inventory.",
                  f"Logged {ok}, {fail} failed.")
    pause_return()


# =============================================================================
# INTERACTIVE MENUS
# =============================================================================
def menu_read(prompt="", default=""):
    """Read a menu selection with a hybrid input model.

    • ESC acts IMMEDIATELY — it does not require the user to press Enter.
    • Enter submits the current buffer; on an empty buffer it returns `default`.
    • All other keys (digits, letters) buffer until Enter is pressed, so
      multi-digit choices still work.

    Returns 'ESC', or the typed text (lower-cased, stripped / or `default`).
    Falls back to a normal line read when stdin is not an interactive TTY
    (e.g. piped input), where ESC cannot be detected instantly.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    # Non-TTY (piped) — behave like a normal line read.
    if not sys.stdin.isatty():
        try:
            line = sys.stdin.readline()
        except Exception:
            return "ESC"
        if line == "":                       # EOF
            return "ESC"
        val = line.strip().lower()
        return val if val else default

    try:
        import termios, tty, select
    except ImportError:                      # non-POSIX fallback
        val = input().strip().lower()
        return val if val else default

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = ""
    try:
        tty.setraw(fd)
        while True:
            ch = os.read(fd, 1)
            if not ch:
                return "ESC"
            if ch == b"\x1b":                # ESC — could be a bare ESC or an arrow seq
                r, _, _ = select.select([fd], [], [], 0.03)
                if r:
                    os.read(fd, 2)           # swallow the arrow sequence, ignore
                    continue
                sys.stdout.write("\n"); sys.stdout.flush()
                return "ESC"
            if ch in (b"\r", b"\n"):         # Enter — submit
                sys.stdout.write("\n"); sys.stdout.flush()
                val = buf.strip().lower()
                return val if val else default
            if ch == b"\x03":                # Ctrl-C
                raise KeyboardInterrupt
            if ch in (b"\x7f", b"\x08"):     # Backspace
                if buf:
                    buf = buf[:-1]
                    sys.stdout.write("\b \b"); sys.stdout.flush()
                continue
            c = ch.decode("utf-8", "ignore")
            if c and c.isprintable():        # buffer printable chars (echo manually)
                buf += c
                sys.stdout.write(c); sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def read_key():
    """Read ONE keypress in raw mode (TTY only), reacting instantly.

    Returns one of: 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'ESC',
    'BACKSPACE', or the typed character.
    """
    import termios, tty, select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if not ch:
            return "ESC"
        if ch == b"\x1b":                    # ESC alone, or an arrow-key sequence
            r, _, _ = select.select([fd], [], [], 0.03)
            if not r:
                return "ESC"
            seq = os.read(fd, 2)
            return {b"[A": "UP", b"[B": "DOWN", b"[C": "RIGHT", b"[D": "LEFT"}.get(seq, "ESC")
        if ch in (b"\r", b"\n"):
            return "ENTER"
        if ch == b"\x03":                    # Ctrl-C
            raise KeyboardInterrupt
        if ch in (b"\x7f", b"\x08"):
            return "BACKSPACE"
        return ch.decode("utf-8", "ignore")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_menu(subtitle, options, is_main=False, intro=None, outro=None,
                help_note=None):
    """Render a CB9 menu and return the user's choice.

    Navigation (interactive TTY):
      • ↑/↓ arrows move the highlighted option; Enter selects it.
      • Typing a number also selects that option (multi-digit buffered).
      • H shows Help; Q or ESC go Back (submenu) / Exit (main) — instant.

    options   : list of (label, description) tuples. Description is shown by [H].
    intro     : optional context line shown above the options.
    outro     : optional context line(s) — str or list of str — shown below the
                options (e.g. the folders already entered).
    help_note : optional (label, description) tuple shown at the bottom of the
                [H] Help screen after the option descriptions (e.g. logging info).
    Returns str(number) for a selection, or 'back' (submenu) / 'quit' (main).
    Falls back to line input when stdin is not an interactive TTY (piped/CLI).
    """
    n = len(options)
    if n == 0:
        return "back"
    if not sys.stdin.isatty():
        return _render_menu_lines(subtitle, options, is_main, intro, outro,
                                  help_note)

    back_word = "Exit" if is_main else "Back"
    selected = 0        # highlighted row (starts on option 1, the default)
    buf = ""            # numeric typing buffer (for multi-digit menus)
    while True:
        screen(subtitle)
        if intro:
            print(f"  {DIM}{intro}{RESET}")
        print()
        for i, (label, _desc) in enumerate(options):
            if i == selected:
                print(color_text(f"  ▶ {i + 1}. {label}", fg=BRIGHT_CYAN, style=BOLD))
            else:
                print(f"    {color_text(str(i + 1), fg=YELLOW)}. {label}")
        print()
        _print_menu_outro(outro)
        standard_footer(f"[↑↓] Move   [Enter] Select   [H] Help   [Q/ESC] {back_word}")
        sys.stdout.write(color_text(" Option: ", fg=CYAN, style=BOLD) + buf)
        sys.stdout.flush()

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % n; buf = ""
        elif key == "DOWN":
            selected = (selected + 1) % n; buf = ""
        elif key == "ENTER":
            print()   # leave the prompt line so any follow-up prompt starts fresh
            if buf.isdigit() and 1 <= int(buf) <= n:
                return str(int(buf))
            return str(selected + 1)          # select the highlighted option
        elif key == "ESC" or key in ("q", "Q"):
            return "quit" if is_main else "back"
        elif key in ("h", "H"):
            show_menu_help(subtitle, options, help_note)
        elif key == "BACKSPACE":
            buf = buf[:-1]
        elif key and key.isdigit():
            buf += key
            if 1 <= int(buf) <= n:            # move highlight to the typed number
                selected = int(buf) - 1
        # anything else: ignore and redraw


def _print_menu_outro(outro):
    """Print the optional context line(s) shown below a menu's options."""
    if not outro:
        return
    lines = [outro] if isinstance(outro, str) else outro
    for line in lines:
        print(f"  {DIM}{line}{RESET}")
    print()


def _render_menu_lines(subtitle, options, is_main, intro, outro=None,
                       help_note=None):
    """Line-based menu fallback for non-TTY stdin (piped input / automation).
    Preserves numbered selection, Enter=default option 1, H help, Q/ESC back."""
    default = "" if is_main else "1"
    while True:
        screen(subtitle)
        if intro:
            print(f"  {DIM}{intro}{RESET}")
        print()
        for i, (label, _desc) in enumerate(options, 1):
            tag = f" {DIM}(default){RESET}" if (i == 1 and not is_main) else ""
            print(f"  {color_text(str(i), fg=YELLOW, style=BOLD)}. {label}{tag}")
        print()
        _print_menu_outro(outro)
        back_word = "Exit" if is_main else "Back"
        standard_footer(f"[↑↓] Move   [Enter] Select   [H] Help   [Q/ESC] {back_word}")
        prompt = " Option: " if is_main else " Option [1]: "
        choice = menu_read(color_text(prompt, fg=CYAN, style=BOLD), default=default)
        if choice == "ESC":
            return "quit" if is_main else "back"
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return choice
        if choice == "q":
            return "quit" if is_main else "back"
        if choice == "h":
            show_menu_help(subtitle, options, help_note)


def render_multiselect(subtitle, options, intro=None):
    """Multi-select menu — the user can toggle several options on.

    Interactive TTY: ↑/↓ move, Space toggles the highlighted item, Enter
    confirms, Q/ESC cancels.
    Non-TTY: enter comma-separated numbers (or 'all'); blank cancels.

    Returns a list of selected indices (possibly empty), or None if cancelled.
    """
    n = len(options)
    if n == 0:
        return None

    if not sys.stdin.isatty():
        screen(subtitle)
        if intro:
            print(f"  {DIM}{intro}{RESET}")
        print()
        for i, (label, _d) in enumerate(options, 1):
            print(f"  {color_text(str(i), fg=YELLOW, style=BOLD)}. {label}")
        print()
        standard_footer("Enter numbers (comma-separated) or 'all'; blank cancels")
        raw = menu_read(color_text(" Select: ", fg=CYAN, style=BOLD))
        if raw in ("ESC", "", "q"):
            return None
        if raw == "all":
            return list(range(n))
        picks = [int(t) - 1 for t in raw.split(",") if t.strip().isdigit() and 1 <= int(t) <= n]
        return sorted(set(picks))

    selected = set()
    cursor = 0
    while True:
        screen(subtitle)
        if intro:
            print(f"  {DIM}{intro}{RESET}")
        print()
        for i, (label, _d) in enumerate(options):
            box = "☑" if i in selected else "☐"
            if i == cursor:
                print(color_text(f"  ▶ {box} {label}", fg=BRIGHT_CYAN, style=BOLD))
            else:
                mark = color_text(box, fg=GREEN) if i in selected else box
                print(f"    {mark} {label}")
        print()
        standard_footer("[↑↓] Move   [Space] Toggle   [Enter] Confirm   [Q/ESC] Cancel")
        sys.stdout.write(color_text(f" Selected: {len(selected)} ", fg=CYAN, style=BOLD))
        sys.stdout.flush()

        key = read_key()
        if key == "UP":
            cursor = (cursor - 1) % n
        elif key == "DOWN":
            cursor = (cursor + 1) % n
        elif key == " ":
            selected.discard(cursor) if cursor in selected else selected.add(cursor)
        elif key == "ENTER":
            print()   # leave the prompt line so any follow-up prompt starts fresh
            return sorted(selected)
        elif key == "ESC" or key in ("q", "Q"):
            return None
        # anything else: ignore and redraw


def _print_help_desc(desc, width):
    """Word-wrap and print one Help description block (dim, indented)."""
    for para in desc.split("\n"):
        hang = "       " if para.lstrip().startswith(("•", "-")) else "     "
        wrapped = textwrap.fill(para.strip(), width=width,
                                initial_indent="     ", subsequent_indent=hang)
        print(f"{DIM}{wrapped}{RESET}")


def show_menu_help(subtitle, options, note=None):
    """Show a Help screen describing every option in the current menu.

    Descriptions are word-wrapped to the terminal width. A description may
    contain explicit newlines to force line breaks (e.g. for bullet lists);
    a line starting with a bullet keeps its hanging indent when it wraps.
    note : optional (label, description) tuple printed after the options —
           an unnumbered extra section (e.g. where activity is logged).
    """
    screen(f"{subtitle} — Help")
    print()
    width = max(get_width() - 6, 40)
    for i, (label, desc) in enumerate(options, 1):
        print(f"  {color_text(f'{i}. {label}', fg=WHITE, style=BOLD)}")
        if desc:
            _print_help_desc(desc, width)
        print()
    if note:
        note_label, note_desc = note
        print(f"  {color_text(note_label, fg=WHITE, style=BOLD)}")
        if note_desc:
            _print_help_desc(note_desc, width)
        print()
    standard_footer("[Any key] Back to menu")
    sys.stdout.write(color_text(" Option: ", fg=CYAN, style=BOLD)); sys.stdout.flush()
    if sys.stdin.isatty():
        read_key()          # any key dismisses
    else:
        menu_read("")


def _pick_compare_by():
    """Sub-selection for the comparison basis. Returns name|size|both or None."""
    options = [
        ("By Name",
         "List the entries that exist in one folder but not the other — reported "
         "in both directions (in A but not B, and in B but not A). Use this to see "
         "what's missing on either side."),
        ("By Size",
         "For entries that exist in BOTH folders, report only the ones whose size "
         "differs, showing A's size vs B's size. Use this to spot files that "
         "changed even though the name is the same."),
        ("Both",
         "Run the By Name report and the By Size report together — the full "
         "picture of what's missing and what changed."),
    ]
    ch = render_menu("Compare Folder Contents — Compare By", options)
    return {"1": "name", "2": "size", "3": "both"}.get(ch) if ch != "back" else None


def compare_menu():
    options = [
        ("Compare 2 Files",
         "Pick two text files; they are shown side by side, line by line, aligned "
         "by a diff. Each row is marked: = the lines are identical, ≠ the line "
         "changed, < the line exists only in file A, > the line exists only in "
         "file B. A summary counts equal / changed / only-in-A / only-in-B lines, "
         "or reports that the files are identical."),
        ("Compare Folder Contents",
         "Compare what is inside two folders. You'll choose two things:\n"
         "• Recursive? — Yes compares every file beneath each folder; No compares "
         "only the immediate top-level files and subfolders.\n"
         "• Compare By — Name (entries in one folder only, both directions), Size "
         "(entries in both whose size differs), or Both.\n"
         "Hidden files and folders (names starting with a dot) are ignored."),
    ]
    while True:
        ch = render_menu("Compare", options)
        if ch == "back":
            return
        if ch == "1":
            fa = ask_file("File A")
            if not fa:
                pause_return(); continue
            fb = ask_file("File B")
            if not fb:
                pause_return(); continue
            compare_two_files(fa, fb)
        elif ch == "2":
            a = ask_folder("Folder A")
            if not a:
                pause_return(); continue
            b = ask_folder("Folder B")
            if not b:
                pause_return(); continue
            recursive = safe_confirm("  Recursive (descend into subfolders)?", default=True)
            by = _pick_compare_by()
            if by is None:
                continue
            compare_folder_contents(a, b, recursive, by)


def display_menu():
    options = [
        ("All Drives",
         "Size and free space of every mounted drive — the boot volume plus "
         "each drive under /Volumes. Shows Size, Used, Free, and Use% per "
         "drive (Use% turns yellow at 75% and red at 90%). Free is the space "
         "actually available to you, matching Finder's Available figure."),
        ("Subfolders Alphabetically",
         "Enter a folder; its subfolders are listed sorted A→Z by name. Each "
         "row shows the folder, its size (human-readable), the exact byte "
         "count, and how many files it contains; a TOTAL row sums them. Best "
         "when you know the folder name you're looking for."),
        ("Subfolders by Size (largest first)",
         "Same columns, but sorted by total size with the biggest folder first — "
         "the quickest way to see what is using the most space."),
    ]
    while True:
        ch = render_menu("Display", options,
                         intro="Drive space · subfolder sizes, byte counts, and file counts.")
        if ch == "back":
            return
        if ch == "1":
            display_all_drives()
            continue
        folder = ask_folder("Folder to measure", default=os.getcwd())
        if not folder:
            pause_return(); continue
        display_folder_sizes(folder, "size" if ch == "3" else "alpha")


def _pick_missing_mode(folder_a, folder_b, subtitle="Find Missing by Filename — Show"):
    """Sub-selection for the Find Missing features — shows the two entered
    folders below the options. Returns first|second|either, or None if
    cancelled."""
    options = [
        ("In 1st folder only",
         "List filenames that exist in the 1st folder but NOT in the 2nd — the "
         "files the 2nd folder is missing."),
        ("In 2nd folder only",
         "List filenames that exist in the 2nd folder but NOT in the 1st — the "
         "files the 1st folder is missing."),
        ("In either folder (only once)",
         "List filenames that exist in one folder but not the other, in both "
         "directions — the full picture of what doesn't match."),
    ]
    ch = render_menu(subtitle, options,
                     outro=[f"Folder 1 - {folder_a}", f"Folder 2 - {folder_b}"])
    return {"1": "first", "2": "second", "3": "either"}.get(ch) if ch != "back" else None


def find_menu():
    options = [
        ("Find Files   (one or more criteria)",
         "Search for files that match one or more criteria combined with AND. On "
         "the next screen, use Space to toggle any of:\n"
         "• Filename pattern — a wildcard like IMG_*.jpg\n"
         "• File extension — e.g. mov, jpg\n"
         "• Size over N MB — larger than N\n"
         "• Size under N MB — smaller than N\n"
         "You then enter a value for each toggled criterion and a search root. "
         "Example: extension = mov and size under 5 finds .mov files under 5 MB. "
         "Each result shows its size (largest first when a size filter is on)."),
        ("Find Folders (by name/pattern)",
         "Find directories whose name matches a wildcard pattern, searched "
         "recursively under a chosen root. Example pattern: *_backup. Results are "
         "just listed — nothing is changed."),
        ("Find Duplicates by Filename",
         "Enter one or more folders (comma-separated). Each folder is scanned "
         "recursively and files sharing the same filename are reported in a "
         "table: a numbered header lists the folders, then one row per "
         "duplicated filename with a size column per folder — so you can see "
         "at a glance where each copy lives and whether the sizes match. If a "
         "name occurs more than once inside a single folder, every size is "
         "listed in that column. Matching is by filename only — contents are "
         "not compared. Nothing is changed; results are just listed."),
        ("Find Duplicates by Fuzzy Name",
         "Enter one or more folders (comma-separated). Each folder is scanned "
         "recursively and files are grouped as duplicates when their names "
         "are CLOSE — not necessarily identical — AND their sizes are close "
         "(within 1%). Example: videofile1.mov and videofile.mov at the same "
         "size are duplicates. Names are close when the stems match after "
         "duplicate-style endings are stripped (trailing digits, \"(1)\", "
         "\"[2]\", \"copy\", \"copy 2\") or are 85%+ similar; extensions "
         "must match. Each group marks the shortest/cleanest name KEEP and "
         "the rest DELETE — so videofile1.mov is the one flagged to delete. "
         "Nothing is deleted; results are just listed, largest files first, "
         "with a reclaimable-space total."),
        ("Find Missing by Filename",
         "Enter two folders, then choose what to show:\n"
         "• In 1st folder only — files the 2nd folder is missing.\n"
         "• In 2nd folder only — files the 1st folder is missing.\n"
         "• In either folder (only once) — both directions together.\n"
         "Each folder is scanned recursively and files are matched by filename "
         "only — contents are not compared. Results use the same table as Find "
         "Duplicates by Filename: a numbered header lists the folders, then one "
         "row per filename with a size column per folder — the blank column "
         "shows where the file is missing. Nothing is changed; results are "
         "just listed."),
        ("Find Missing by Filename & Size",
         "Same as Find Missing by Filename, but files only count as a match "
         "when BOTH the filename AND the file size agree. That means a "
         "same-named file whose size differs between the two folders is also "
         "reported — with its size shown in both columns so the mismatch is "
         "obvious. Enter two folders, then choose In 1st folder only / In 2nd "
         "folder only / In either folder. Nothing is changed; results are "
         "just listed."),
        ("Find & Replace",
         "Enter a folder, the text to find, the replacement text, and an "
         "optional file extension. Every text file under the folder is "
         "scanned recursively (hidden files/folders and binary files are "
         "skipped); matching is literal and case-insensitive. ALWAYS a dry "
         "run first — every match is listed with its file, line number, and "
         "the line with the matched text highlighted, and nothing is "
         "touched. Then confirm [y/N] to replace every occurrence (you are "
         "also asked whether to save a .bak backup of each file first), or "
         "answer No to exit with nothing changed."),
        ("Find & Rename",
         "Find files, then rename them. Enter a folder, an optional file "
         "extension, and choose how the text is applied:\n"
         "• Prepend — add the text to the START of the filename "
         "(text.mov -> api_text.mov). Files already starting with it are "
         "skipped.\n"
         "• Append — add the text to the END of the name, before the "
         "extension (text.mov -> text_api.mov). Files already ending with "
         "it are skipped.\n"
         "• Replace — replace text inside the filename (draft_a.mov -> "
         "final_a.mov); matching is literal and case-insensitive, and a "
         "blank replacement removes the text.\n"
         "ALWAYS a dry run first — every rename is listed old -> new, and "
         "nothing is touched until you confirm [y/N]. Renames that would "
         "overwrite an existing file are skipped and reported."),
    ]
    while True:
        ch = render_menu("Find", options)
        if ch == "back":
            return
        if ch == "2":
            root = ask_folder("Search root", default=os.getcwd())
            if not root:
                pause_return(); continue
            pat = ask("Folder name/pattern (wildcards ok)", "*")
            find_folders(root, pat or "*")
            continue
        if ch in ("3", "4"):
            folders = _ask_folders_multi()
            if folders:
                if ch == "3":
                    find_duplicates_by_filename(folders)
                else:
                    find_duplicates_by_fuzzy_name(folders)
            else:
                pause_return()
            continue
        if ch in ("5", "6"):
            match_size = (ch == "6")
            a = ask_folder("Folder 1")
            if not a:
                pause_return(); continue
            b = ask_folder("Folder 2")
            if not b:
                pause_return(); continue
            subtitle = ("Find Missing by Filename & Size — Show" if match_size
                        else "Find Missing by Filename — Show")
            mode = _pick_missing_mode(a, b, subtitle)
            if mode is None:
                continue
            find_missing_by_filename(a, b, mode, match_size)
            continue
        if ch == "7":
            root = ask_folder("Folder to search")
            if not root:
                pause_return(); continue
            search = ask("Text to find")
            if not search:
                print(color_text("  Search text required — cancelled.", fg=YELLOW))
                pause_return(); continue
            replace = ask("Replace with (blank = remove the text)")
            ext = ask("File extension (optional, e.g. php)")
            find_and_replace(root, search, replace, ext or None)
            continue
        if ch == "8":
            root = ask_folder("Folder to search")
            if not root:
                pause_return(); continue
            mode_opts = [
                ("Prepend — add text to the start of the filename",
                 "The text is added to the front of every found filename: "
                 "text.mov -> api_text.mov. Files whose name already starts "
                 "with the text are skipped, so reruns are safe."),
                ("Append  — add text to the end, before the extension",
                 "The text is inserted between the name and its extension: "
                 "text.mov -> text_api.mov. Files whose name already ends "
                 "with the text are skipped, so reruns are safe."),
                ("Replace — replace text within the filename",
                 "Enter the text to find in the filename and its replacement "
                 "(blank = remove the text): draft_a.mov -> final_a.mov. "
                 "Matching is literal and case-insensitive; only files whose "
                 "name contains the text are listed."),
            ]
            mch = render_menu("Find & Rename — Mode", mode_opts,
                              outro=[f"Folder - {root}"])
            if mch == "back":
                continue
            replace_with = None
            if mch == "1":
                mode = "prepend"
                text = ask("Text to prepend")
            elif mch == "2":
                mode = "append"
                text = ask("Text to append (before the extension)")
            else:
                mode = "replace"
                text = ask("Text to find in the filename")
                if text:
                    replace_with = ask("Replacement text (blank = remove the text)")
            if not text:
                print(color_text("  Text required — cancelled.", fg=YELLOW))
                pause_return(); continue
            ext = ask("File extension (optional, e.g. mov)")
            find_and_rename(root, mode, text, replace_with, ext or None)
            continue

        # Find Files — pick one or more criteria, then prompt for each value.
        crit_opts = [
            ("Filename pattern", "Match file names against a wildcard (e.g. IMG_*.jpg)."),
            ("File extension",   "Match a file extension (e.g. mov, jpg)."),
            ("Size over N MB",   "Only files larger than N megabytes."),
            ("Size under N MB",  "Only files smaller than N megabytes."),
        ]
        picks = render_multiselect(
            "Find Files — Select Criteria", crit_opts,
            intro="Toggle any criteria to combine (e.g. extension + size under). They are AND-ed together.")
        if picks is None:
            continue                       # cancelled — back to Find menu
        if not picks:
            print(color_text("  No criteria selected.", fg=YELLOW)); pause_return(); continue

        pattern = ext = over_mb = under_mb = None
        if 0 in picks:
            pattern = ask("Filename pattern (wildcards ok)", "*") or "*"
        if 1 in picks:
            ext = ask("Extension (e.g. mov)")
            if not ext:
                print(color_text("  Extension required — cancelled.", fg=YELLOW)); pause_return(); continue
        if 2 in picks:
            try:
                over_mb = float(ask("Size OVER how many MB?", "5"))
            except ValueError:
                print(color_text("  Invalid number.", fg=RED)); pause_return(); continue
        if 3 in picks:
            try:
                under_mb = float(ask("Size UNDER how many MB?", "5"))
            except ValueError:
                print(color_text("  Invalid number.", fg=RED)); pause_return(); continue

        root = ask_folder("Search root", default=os.getcwd())
        if not root:
            pause_return(); continue
        find_files_combined(root, pattern, ext, over_mb, under_mb)


def _ask_folders_multi():
    raw = ask("Folder(s) — comma-separated for multiple")
    if not raw:
        return None
    folders = [clean_path(f) for f in raw.split(",") if f.strip()]
    valid = [f for f in folders if os.path.isdir(f)]
    for f in folders:
        if f not in valid:
            print(color_text(f"  Skipping (not a directory): {f}", fg=YELLOW))
    return valid or None


def remove_menu():
    options = [
        ("Duplicates by Name",
         "Scan one or more folders (enter several comma-separated) and group files "
         "that share the same file name. The first occurrence of each name is "
         "kept; the rest are listed for removal. You can optionally limit the scan "
         "to a single extension. Matches by name only — the contents are not "
         "checked. Previewed and dry-run; to actually delete you must type the "
         "word YES (anything else cancels)."),
        ("Duplicates by Hash",
         "Scan one or more folders and group files with identical CONTENT using a "
         "SHA-256 hash. Files are pre-grouped by size first, so files of different "
         "sizes are never hashed (fast). The first of each identical set is kept; "
         "the rest are listed for removal. This catches duplicates even when they "
         "have different names. Previewed and dry-run; to actually delete you must "
         "type the word YES (anything else cancels)."),
        ("Duplicates by Fuzzy Name",
         "Scan one or more folders and group files whose names are CLOSE — not "
         "necessarily identical — AND whose sizes are close (within 1%). Example: "
         "videofile1.mov and videofile.mov at the same size are duplicates, and "
         "videofile1.mov is the one removed. Names are close when the stems match "
         "after duplicate-style endings are stripped (trailing digits, \"(1)\", "
         "\"[2]\", \"copy\") or are 85%+ similar; extensions must match. The "
         "shortest/cleanest name in each group is kept; the rest are listed for "
         "removal. Hidden files are skipped. Previewed and dry-run; to actually "
         "delete you must type the word YES (anything else cancels)."),
        ("By File Name",
         "Delete files whose name matches a wildcard pattern, searched recursively "
         "under a chosen root. Every match is previewed with its size before "
         "anything is deleted.\n"
         "• Tip: enter '.DS_Store' or 'desktop.ini' to clean macOS/Windows junk "
         "files. Wildcards work too, e.g. *.tmp."),
        ("By Folder Name",
         "Delete folders whose name matches a wildcard pattern, searched "
         "recursively under a chosen root; each matching folder tree is removed. "
         "When a matched folder sits inside another matched folder, only the "
         "top-most one is removed (it already contains the child). Previewed and "
         "dry-run until you confirm. Example pattern: *_tmp."),
        ("Files of 0 Size",
         "Scan one or more folders (enter several comma-separated) and list every "
         "empty (0-byte) file for removal — incomplete downloads, placeholder "
         "files, failed copies. Hidden files/folders are skipped, so intentional "
         "markers like .gitkeep are never touched. Previewed and dry-run until "
         "you confirm."),
    ]
    while True:
        ch = render_menu("Remove", options,
                         intro="DRY RUN by default — you always confirm before anything is deleted.")
        if ch == "back":
            return
        if ch == "1":
            folders = _ask_folders_multi()
            if folders:
                ext = ask("Limit to extension (blank = all)")
                remove_duplicates_by_name(folders, live_requested=None, ext=ext or None)
        elif ch == "2":
            folders = _ask_folders_multi()
            if folders:
                remove_duplicates_by_hash(folders, live_requested=None)
        elif ch == "3":
            folders = _ask_folders_multi()
            if folders:
                remove_duplicates_by_fuzzy_name(folders, live_requested=None)
        elif ch == "4":
            root = ask_folder("Search root", default=os.getcwd())
            if not root:
                pause_return(); continue
            print(f"  {DIM}Tip: use '.DS_Store' or 'desktop.ini' to clean junk files.{RESET}")
            pat = ask("File name/pattern to remove (wildcards ok)")
            if pat:
                remove_by_name(root, pat, live_requested=None)
        elif ch == "5":
            root = ask_folder("Search root", default=os.getcwd())
            if not root:
                pause_return(); continue
            pat = ask("Folder name/pattern to remove (wildcards ok)")
            if pat:
                remove_folders_by_name(root, pat, live_requested=None)
        elif ch == "6":
            folders = _ask_folders_multi()
            if folders:
                remove_zero_size_files(folders, live_requested=None)


def _monitor_output_choice():
    """Ask where monitor events should be logged. Returns 'log' | 'csv' | None."""
    log_disp = ACTIVITY_LOG.replace(os.path.expanduser("~"), "~")
    csv_disp = MONITOR_CSV.replace(os.path.expanduser("~"), "~")
    options = [
        (f"FM activity log — {log_disp}",
         "Each event is appended to the shared FM activity log as a plain "
         "timestamped line, right below the session header. Everything FM "
         "does stays in one log."),
        (f"CSV file — {csv_disp}",
         "Each event is appended as a CSV row (Timestamp, Filename, Folder, "
         "Event) — easy to open in a spreadsheet or parse. The header row is "
         "written when the file is first created; sessions append."),
    ]
    ch = render_menu("Monitor — Log Destination", options)
    if ch == "back":
        return None
    return "log" if ch == "1" else "csv"


def _monitor_interactive():
    """Interactive Monitor — ask for the folder and options, then watch it."""
    screen("Monitor File Activity")
    print()
    folder = ask_folder("Folder to monitor")
    if not folder:
        pause_return(); return
    recursive = safe_confirm("  Include subfolders (recursive)?", default=True)
    ext_raw = ask("File extensions to watch (comma-separated, blank = all)")
    output = _monitor_output_choice()
    if output is None:
        return
    monitor_activity(folder, recursive, ext_raw, output)
    pause_return()


def _run_monitor_profile(pr):
    """Run one monitorProfiles entry from fmConfig.json (defaults: recursive,
    all extensions, log output)."""
    folder = clean_path(str(pr.get("folder", "")))
    output = "csv" if str(pr.get("output", "log")).lower() == "csv" else "log"
    monitor_activity(folder,
                     recursive=bool(pr.get("recursive", True)),
                     exts=pr.get("extensions", ""),
                     output=output,
                     profile_name=pr.get("name") or "(unnamed profile)")
    pause_return()


def monitor_menu():
    profile_note = (
        "Monitor Profiles (fmConfig.json)",
        "Saved monitor setups appear as options above Interactive Monitor. Add "
        "them to fmConfig.json as a monitorProfiles list; each profile supports:\n"
        "• name — the label shown in this menu\n"
        "• folder — the folder to watch (~ is expanded)\n"
        "• recursive — true/false (default true)\n"
        "• extensions — extensions to watch, e.g. \"jpg,png\" or a list "
        "(default: all files)\n"
        "• output — log (fm.log) or csv (fmMonitor.csv); default log\n"
        "Monitoring runs until you press [Q/ESC].")
    while True:
        profiles, perr = _load_monitor_profiles()
        options = []
        for pr in profiles:
            name = pr.get("name") or "(unnamed profile)"
            exts = _parse_ext_filter(pr.get("extensions", ""))
            options.append((
                f"Profile: {name}",
                f"Watch this saved profile's folder for created/modified/deleted "
                f"files:\n"
                f"• Folder — {pr.get('folder', '?')}\n"
                f"• Recursive: {'Yes' if pr.get('recursive', True) else 'No'}   "
                f"Extensions: {', '.join(sorted(exts)) if exts else 'all'}   "
                f"Output: {'CSV' if str(pr.get('output', 'log')).lower() == 'csv' else 'fm.log'}\n"
                "Runs until you press [Q/ESC]."))
        options.append((
            "Interactive Monitor — enter a folder & options",
            "Enter the folder to watch, whether to include subfolders (default "
            "Yes), an optional extension filter (e.g. jpg, png — blank watches "
            "everything), and where to log (fm.log or fmMonitor.csv). Every "
            "created, modified, or deleted file then appears on screen and in "
            "the log in real time until you press [Q/ESC]."))
        ch = render_menu("Monitor File Activity", options,
                         outro=(f"⚠ {perr}" if perr else None),
                         help_note=profile_note)
        if ch == "back":
            return
        if int(ch) <= len(profiles):
            _run_monitor_profile(profiles[int(ch) - 1])
        else:
            _monitor_interactive()


def _sync_interactive():
    """Interactive Sync — ask for the two folders, the direction, and the
    options, then run the preview/confirm sync."""
    screen("Sync Folders")
    print()
    folder_a = ask_folder("Folder A")
    if not folder_a:
        pause_return(); return
    folder_b = ask_folder("Folder B")
    if not folder_b:
        pause_return(); return

    dir_options = [
        ("Push new/updated files from A → B",
         "Folder A is the source. Files that exist only in A are copied into B, "
         "and files existing on both sides are copied when A's copy wins the "
         "conflict rule you pick next. Folder B is never read from — nothing in "
         "A changes, and nothing is ever deleted."),
        ("Push new/updated files from B → A",
         "Folder B is the source. Files that exist only in B are copied into A, "
         "and files existing on both sides are copied when B's copy wins the "
         "conflict rule you pick next. Folder A is never read from — nothing in "
         "B changes, and nothing is ever deleted."),
        ("Two-way sync A ↔ B",
         "Both folders push to each other in one run. Files that exist only in "
         "A are copied into B, files that exist only in B are copied into A, "
         "and when a file exists on both sides the copy that wins the conflict "
         "rule you pick next replaces the other. Nothing is ever deleted."),
    ]
    ch = render_menu("Sync — Direction", dir_options,
                     outro=[f"Folder A - {folder_a}", f"Folder B - {folder_b}"])
    if ch == "back":
        return
    direction = {"1": "a2b", "2": "b2a", "3": "both"}[ch]

    conflict_options = [
        ("Choose the newest  — copy only when the source file is newer",
         "When a file exists in both folders, its modified times are compared "
         "and the source copy is pushed only if it is newer than the "
         "destination copy. The usual choice for keeping a backup current."),
        ("Choose the largest — copy only when the source file is larger",
         "When a file exists in both folders, their sizes are compared and the "
         "source copy is pushed only if it is larger than the destination "
         "copy. Useful when bigger means better (e.g. re-exported media)."),
    ]
    ch = render_menu("Sync — If a File Exists on Both Sides", conflict_options,
                     outro=[f"Folder A - {folder_a}", f"Folder B - {folder_b}"])
    if ch == "back":
        return
    conflict = "newest" if ch == "1" else "largest"

    recursive = safe_confirm("  Include subfolders (recursive)?", default=True)
    exclude_hidden = safe_confirm("  Exclude hidden files?", default=True)

    sync_folders(folder_a, folder_b, direction, recursive, conflict, exclude_hidden)
    pause_return()


def sync_menu():
    profile_note = (
        "Sync Profiles (fmConfig.json)",
        "Saved sync setups appear as options above Interactive Sync. Add them to "
        "fmConfig.json as a syncProfiles list; each profile supports:\n"
        "• name — the label shown in this menu\n"
        "• folderA / folderB — the two folders (~ is expanded)\n"
        "• direction — AtoB, BtoA, or Both (which side pushes its new/updated "
        "files; Both = two-way, each side receives the other's)\n"
        "• recursive — true/false (default true)\n"
        "• conflict — newest or largest: when a file exists on both sides, copy "
        "only when the source is newer / larger (default newest)\n"
        "• excludeHidden — true/false (default true)\n"
        "Profiles run exactly like Interactive Sync: a preview first, and "
        "nothing is copied until you confirm.")
    while True:
        profiles, perr = _load_sync_profiles()
        options = []
        for pr in profiles:
            name = pr.get("name") or "(unnamed profile)"
            pdir = _parse_sync_direction(pr.get("direction", "AtoB"))
            arrow = {"b2a": "B → A", "both": "A ↔ B"}.get(pdir, "A → B")
            conflict = ("Largest"
                        if str(pr.get("conflict", "newest")).lower() == "largest"
                        else "Newest")
            options.append((
                f"Profile: {name}  ({arrow})",
                f"Push new/updated files {arrow} using this saved profile:\n"
                f"• Folder A — {pr.get('folderA', '?')}\n"
                f"• Folder B — {pr.get('folderB', '?')}\n"
                f"• Recursive: {'Yes' if pr.get('recursive', True) else 'No'}   "
                f"Conflict: {conflict} wins   Hidden files: "
                f"{'Excluded' if pr.get('excludeHidden', True) else 'Included'}\n"
                "Previews first — nothing is copied until you confirm."))
        options.append((
            "Interactive Sync — enter folders, direction & options",
            "Enter Folder A and Folder B, choose the push direction (A → B, "
            "B → A, or two-way A ↔ B), what wins when a file exists on both "
            "sides (newest or largest), whether to include subfolders (default "
            "Yes), and whether to exclude hidden files (default Yes). A preview "
            "lists every file that would be copied — nothing is copied until "
            "you confirm."))
        ch = render_menu("Sync", options,
                         outro=(f"⚠ {perr}" if perr else None),
                         help_note=profile_note)
        if ch == "back":
            return
        if int(ch) <= len(profiles):
            _run_sync_profile(profiles[int(ch) - 1])
        else:
            _sync_interactive()


def zip_menu():
    options = [
        ("View Zip",
         "Inspect a zip WITHOUT extracting it: each entry's uncompressed and "
         "compressed size, compression ratio, and modified date, plus totals. "
         "Give a single .zip file to view it directly, or give a folder to pick "
         "from the zips inside it."),
        ("Log Zip File",
         "Log a .zip or .tar archive — or every archive in a folder (top level "
         "only) — to the CB9Inventory database on BPA5 via the DocInfo Manager "
         "API. Each archive is recorded in zipFile (matched by name + size: "
         "insert when new, update when seen before) and its file listing is "
         "synced to zipFileContent (existing rows updated, new rows inserted, "
         "files no longer in the archive soft-deleted). Prior row states are "
         "preserved automatically by database archive triggers. .gz files are "
         "ignored. Settings come from fmConfig.json (logZip: apiUrl, "
         "serverSecretKey)."),
        ("Zip SubFolders",
         "Zip each immediate subfolder of a target folder into its own .zip file "
         "in a destination folder (defaults to the current directory). Before "
         "zipping it removes .DS_Store and desktop.ini files, and it resolves name "
         "collisions automatically (name.zip, name-2.zip, …). You'll be asked "
         "whether to delete each source folder after it zips successfully — that "
         "removal only happens on a successful zip."),
    ]
    while True:
        ch = render_menu("Zip", options)
        if ch == "back":
            return
        if ch == "1":
            target = ask("Zip file or folder to view")
            if target:
                zip_view(target)
        elif ch == "2":
            target = ask("Zip/tar file or folder to log")
            if target:
                log_zip_files(target)
        elif ch == "3":
            target = ask_folder("Target folder (contains subfolders to zip)")
            if not target:
                pause_return(); continue
            dest = ask("Zip destination", default=os.getcwd())
            remove_after = safe_confirm("  Remove source folders after zipping?", default=False)
            zip_subfolders(target, dest, remove_after)


def cleanup_menu():
    options = [
        ("Remove Junk Files (.DS_Store / desktop.ini)",
         "Enter a root folder; every .DS_Store and desktop.ini beneath it "
         "(hidden folders included) is found and listed. A DRY RUN preview "
         "shows each file and its size — nothing is deleted until you "
         "confirm."),
        ("Purge Old Log Files",
         "Trim old entries out of every .log file in ~/Documents/log (or a "
         "folder you choose). You pick how many days to keep (default 90); "
         "entries with a [YYYY-MM-DD HH:MM:SS] timestamp older than that are "
         "removed — an entry's untimestamped body lines go with their header. "
         "A DRY RUN table shows purge/keep line counts per file first, and a "
         ".bak backup of each changed file is saved before it is rewritten."),
    ]
    while True:
        ch = render_menu("Clean Up", options,
                         intro="Junk-file cleanup · log purging — dry run first, always.")
        if ch == "back":
            return
        if ch == "1":
            root = ask_folder("Root folder to clean", default=os.path.expanduser("~"))
            if not root:
                pause_return(); continue
            cleanup_junk_files(root)
            pause_return()
        elif ch == "2":
            folder = ask_folder("Log folder", default=LOG_PURGE_DIR)
            if not folder:
                pause_return(); continue
            days = ask("Days to keep", default=str(LOG_PURGE_DAYS))
            cleanup_purge_logs(folder, days)
            pause_return()


def main_menu():
    options = [
        ("Compare  — Compare 2 files, or folder contents",
         "Two tools. 'Compare 2 Files' shows two text files side by side with a "
         "line-by-line diff. 'Compare Folder Contents' compares what's inside two "
         "folders by name and/or size, top-level or recursively — handy for "
         "checking a backup against the original."),
        ("Convert  — Data files between CSV / JSON / XLSX / SQL",
         "Convert a data file to another format. Input: .csv, .json, or .xlsx "
         "(first row / keys = column headers). Output: CSV, JSON (array of "
         "objects), XLSX (needs openpyxl), or SQL (CREATE TABLE with guessed "
         "column types + multi-row INSERTs, table named after the file). The "
         "new file is written next to the source with the same name and the "
         "new extension — collision-safe (name-2.ext, …), never overwrites."),
        ("Display  — All drives, folder sizes",
         "'All Drives' shows the size, used, and free space of every mounted "
         "drive (free matches Finder's Available). The Subfolders options list "
         "every immediate subfolder of a chosen folder with its total size "
         "(human-readable and exact bytes) and file count, sorted alphabetically "
         "or largest-first, ending with a grand total. Good for finding what's "
         "eating disk space."),
        ("Find     — Files by combined criteria, folders by name, duplicates",
         "'Find Files' searches for files matching one or more criteria AND-ed "
         "together (filename pattern, extension, size over N MB, size under N MB) "
         "— e.g. .mov files under 5 MB. 'Find Folders' finds directories by name "
         "pattern. 'Find Duplicates by Filename' scans one or more folders and "
         "tables files sharing the same name with a size column per folder. "
         "'Find Missing by Filename' compares two folders and tables the files "
         "present in only one of them. 'Find & Replace' edits text inside "
         "files; 'Find & Rename' renames the files themselves (prepend / "
         "append / replace text in the filename) — both dry-run first."),
        ("Eject    — Eject all external drives",
         "List the external drives currently mounted (name, size, mount point) "
         "and eject them all — the same as clicking each drive's eject button. "
         "Asks for confirmation first, shows a per-drive Success/Failed status, "
         "and offers a force eject for drives that won't let go (e.g. Spotlight "
         "or an app is still using them). macOS only (uses diskutil, with a "
         "Finder fallback)."),
        ("Monitor  — File activity in a folder, real-time",
         "Watch a folder (or a saved profile from fmConfig.json) and report "
         "every created, modified, and deleted file as it happens — on screen "
         "and to fm.log or a CSV. Options: recursive (default yes) and a file "
         "extension filter. Runs until you press [Q/ESC]."),
        ("Sync     — Push new/updated files between two folders",
         "Sync two folders: push new/updated files A → B, B → A, or two-way "
         "A ↔ B. Options: recursive (default yes), what wins when a file exists "
         "on both sides (newest or largest), and excluding hidden files. Saved "
         "profiles from fmConfig.json (syncProfiles) run the same way. Nothing "
         "is deleted, and every run previews first — a DRY RUN until you "
         "confirm."),
        ("Zip      — View zip, log zip file, zip subfolders",
         "'View Zip' lists a zip's contents (sizes, ratios, dates) without "
         "extracting it. 'Log Zip File' records a .zip/.tar (or a folder of "
         "them) to the CB9Inventory database. 'Zip SubFolders' compresses each "
         "subfolder of a target into its own .zip."),
        ("Remove   — Duplicates, files/folders by name",
         "Delete duplicate files (by name or by exact content), files by name "
         "pattern, or folders by name pattern. Every removal shows a preview and "
         "is a DRY RUN until you confirm — nothing is deleted by accident."),
        ("Create Random UID — Generate N random UUIDs",
         "Enter how many UUIDs you need and get that many random (version 4) "
         "UUIDs, one per line — e.g. 550e8400-e29b-41d4-a716-446655440000. "
         "Handy for database keys, API tokens, and test data. The list is "
         "also appended to the activity log (fm.log); [R] Run Again "
         "regenerates a fresh batch with the same count."),
        ("Clean Up — Junk files, purge old log entries",
         "'Remove Junk Files' finds and deletes every .DS_Store / desktop.ini "
         "under a root folder. 'Purge Old Log Files' trims entries older than "
         "N days (default 90) out of the .log files in ~/Documents/log, saving "
         "a .bak backup of each changed file. Both show a DRY RUN preview and "
         "change nothing until you confirm."),
    ]
    help_note = (
        "Logging",
        "Commands and their results screens are logged to the FM activity log:\n"
        "• ~/Documents/log/fm.log\n"
        "Each run is appended with a [YYYY-MM-DD HH:MM:SS] timestamp line, exactly "
        "as shown on screen but with colors stripped — including the folders "
        "entered and the full results table. Actions that log: Convert, Eject All "
        "External Drives, Find Duplicates by Filename, Find Missing by Filename, "
        "Find & Replace, Find & Rename, Create Random UID (reruns "
        "via [R] Run Again are logged again), Monitor File Activity (each event "
        "streams in real time — or to ~/Documents/log/fmMonitor.csv when CSV "
        "output is chosen), and Sync (the preview and what was copied). "
        "'Zip → Log Zip File' is different — it records archives to the "
        "CB9Inventory database on BPA5, not to fm.log.")
    while True:
        ch = render_menu("Main Menu", options, is_main=True,
                         intro="Compare · Convert · Display · Find · Eject · Monitor · Sync · Zip · Remove · Create Random UID · Clean Up",
                         help_note=help_note)
        if ch == "quit":
            exit_screen(SCRIPT_NAME, VER)
            return
        elif ch == "1":
            compare_menu()
        elif ch == "2":
            convert_menu()
        elif ch == "3":
            display_menu()
        elif ch == "4":
            find_menu()
        elif ch == "5":
            eject_external_drives()
            pause_return()
        elif ch == "6":
            monitor_menu()
        elif ch == "7":
            sync_menu()
        elif ch == "8":
            zip_menu()
        elif ch == "9":
            remove_menu()
        elif ch == "10":
            create_random_uid_menu()
        elif ch == "11":
            cleanup_menu()


# =============================================================================
# CLI
# =============================================================================
def build_parser():
    p = argparse.ArgumentParser(
        prog="fm.py", add_help=True,
        description="File Manager — compare, display, eject, find, monitor, remove, sync, zip, cleanup. "
                    "Run with no arguments for the interactive menu.")
    sub = p.add_subparsers(dest="cmd")

    c2 = sub.add_parser("compare-2files", help="Compare two files side by side")
    c2.add_argument("a"); c2.add_argument("b")

    cc = sub.add_parser("compare-contents", help="Compare the contents of two folders")
    cc.add_argument("a"); cc.add_argument("b")
    cc.add_argument("--recursive", action="store_true", help="Descend into subfolders (default: top level only)")
    cc.add_argument("--by", choices=["name", "size", "both"], default="both")

    cv = sub.add_parser("convert", help="Convert a data file (.csv/.json/.xlsx) to CSV, JSON, XLSX, or SQL")
    cv.add_argument("file", help="source file (.csv, .json, or .xlsx)")
    cv.add_argument("to", choices=["csv", "json", "xlsx", "sql"],
                    help="output format — written next to the source, same name, new extension")

    uu = sub.add_parser("uuid", help="Generate N random UUIDs, one per line")
    uu.add_argument("count", nargs="?", type=int, default=1,
                    help="how many UUIDs to generate (default 1)")

    sz = sub.add_parser("sizes", help="Display subfolder sizes")
    sz.add_argument("folder", nargs="?", default=".")
    sz.add_argument("--sort", choices=["alpha", "size"], default="alpha")

    sub.add_parser("drives", help="Display size and free space of all mounted drives")

    fd = sub.add_parser("find", help="Find folders/files (single criterion)")
    fd.add_argument("type", choices=["folder", "name", "ext", "over", "under"])
    fd.add_argument("value")
    fd.add_argument("root", nargs="?", default=".")

    ff = sub.add_parser("find-files", help="Find files by one or more combined criteria (AND)")
    ff.add_argument("root", nargs="?", default=".")
    ff.add_argument("--name", help="filename wildcard pattern (e.g. 'IMG_*.jpg')")
    ff.add_argument("--ext", help="file extension, e.g. mov")
    ff.add_argument("--over", type=float, help="only files larger than N MB")
    ff.add_argument("--under", type=float, help="only files smaller than N MB")

    fdup = sub.add_parser("find-dups", help="Find duplicate filenames across one or more folders (size table)")
    fdup.add_argument("folders", nargs="+")

    ffuz = sub.add_parser("find-fuzzy-dups",
                          help="Find close-name + close-size duplicates (grouped with KEEP/DELETE markers)")
    ffuz.add_argument("folders", nargs="+")

    fmis = sub.add_parser("find-missing", help="Find filenames present in only one of two folders (size table)")
    fmis.add_argument("a"); fmis.add_argument("b")
    fmis.add_argument("--in", dest="mode", choices=["first", "second", "either"], default="either",
                      help="show names in the 1st folder only, the 2nd only, or either (default)")
    fmis.add_argument("--size", action="store_true",
                      help="match by filename AND size (same name with a different size = missing)")

    frp = sub.add_parser("find-replace", help="Find text in files and replace it (dry-run unless --apply)")
    frp.add_argument("root"); frp.add_argument("search"); frp.add_argument("replace")
    frp.add_argument("--ext", help="only files with this extension, e.g. php")
    frp.add_argument("--apply", action="store_true", help="Actually replace (default: dry run)")
    frp.add_argument("--bak", action="store_true", help="save a .bak backup of each modified file")
    frp.add_argument("--yes", action="store_true", help="Skip confirmation when replacing")

    frn = sub.add_parser("find-rename", help="Find files and rename them (dry-run unless --apply)")
    frn.add_argument("root")
    frn_mode = frn.add_mutually_exclusive_group(required=True)
    frn_mode.add_argument("--prepend", metavar="TEXT",
                          help="add TEXT to the start of each filename (skips files already starting with it)")
    frn_mode.add_argument("--append", dest="append_text", metavar="TEXT",
                          help="add TEXT to the end of the name, before the extension (skips files already ending with it)")
    frn_mode.add_argument("--replace", nargs=2, metavar=("FIND", "NEW"),
                          help="replace FIND with NEW inside the filename (literal, case-insensitive; NEW may be '')")
    frn.add_argument("--ext", help="only files with this extension, e.g. mov")
    frn.add_argument("--apply", action="store_true", help="Actually rename (default: dry run)")
    frn.add_argument("--yes", action="store_true", help="Skip confirmation when renaming")

    rm = sub.add_parser("remove", help="Remove items (dry-run unless --delete)")
    rm.add_argument("type", choices=["folder", "name", "folder-name", "dup-name", "dup-hash",
                                     "dup-fuzzy", "zero-size"])
    rm.add_argument("args", nargs="+")
    rm.add_argument("--delete", action="store_true", help="Actually delete (default: dry run)")
    rm.add_argument("--yes", action="store_true", help="Skip confirmation when deleting")

    mo = sub.add_parser("monitor", help="Watch a folder for file activity in real time (Ctrl-C to stop)")
    mo.add_argument("folder", nargs="?", help="Folder to monitor")
    mo.add_argument("--profile", help="run a named monitorProfiles entry from fmConfig.json instead of giving a folder")
    mo.add_argument("--no-recursive", action="store_true", help="top-level files only (default: recursive)")
    mo.add_argument("--ext", help="comma-separated extensions to watch, e.g. jpg,png (default: all files)")
    mo.add_argument("--csv", action="store_true", help="log events to fmMonitor.csv instead of fm.log")

    ej = sub.add_parser("eject", help="Eject all external drives (macOS)")
    ej.add_argument("--list", action="store_true", help="list external drives and exit (no eject)")
    ej.add_argument("--force", action="store_true", help="force-unmount before ejecting (bypasses Spotlight etc.)")
    ej.add_argument("--yes", action="store_true", help="Skip confirmation and eject immediately")

    sy = sub.add_parser("sync", help="Sync: push new/updated files between two folders, one-way or two-way (dry-run unless --copy)")
    sy.add_argument("a", nargs="?", help="Folder A")
    sy.add_argument("b", nargs="?", help="Folder B")
    sy.add_argument("--to", choices=["b", "a", "both"], default="b",
                    help="push direction: 'b' = A→B (default), 'a' = B→A, 'both' = two-way A↔B")
    sy.add_argument("--profile", help="run a named syncProfiles entry from fmConfig.json instead of giving folders")
    sy.add_argument("--conflict", choices=["newest", "largest"], default="newest",
                    help="when a file exists on both sides, copy only if the source is newer (default) / larger")
    sy.add_argument("--no-recursive", action="store_true", help="top-level files only (default: recursive)")
    sy.add_argument("--include-hidden", action="store_true", help="include hidden files (default: excluded)")
    sy.add_argument("--copy", action="store_true", help="Actually copy (default: dry run)")
    sy.add_argument("--yes", action="store_true", help="Skip confirmation when copying")

    zs = sub.add_parser("zip-subfolders", help="Zip each subfolder")
    zs.add_argument("target"); zs.add_argument("dest", nargs="?", default=None)
    zs.add_argument("-r", "--remove", action="store_true", help="Remove source folders after zip")

    zv = sub.add_parser("zip-view", help="View a zip file or browse a folder of zips")
    zv.add_argument("path", nargs="?", default=None)

    zl = sub.add_parser("zip-log", help="Log a .zip/.tar (or a folder of them) to CB9Inventory")
    zl.add_argument("target")

    cu = sub.add_parser("cleanup", help="Remove junk files or purge old log entries (dry-run unless --delete)")
    cu.add_argument("what", choices=["junk", "logs"])
    cu.add_argument("path", nargs="?", help="junk: root folder (required); logs: log folder (default ~/Documents/log)")
    cu.add_argument("--days", type=int, default=LOG_PURGE_DAYS, help="logs: days of entries to keep (default 90)")
    cu.add_argument("--delete", action="store_true", help="Actually delete/purge (default: dry run)")
    cu.add_argument("--yes", action="store_true", help="Skip confirmation when deleting/purging")

    return p


def run_cli(ns):
    cmd = ns.cmd
    if cmd == "compare-2files":
        compare_two_files(clean_path(ns.a), clean_path(ns.b))
    elif cmd == "convert":
        convert_file(clean_path(ns.file), ns.to)
    elif cmd == "uuid":
        generate_uuids(ns.count)
    elif cmd == "compare-contents":
        compare_folder_contents(clean_path(ns.a), clean_path(ns.b),
                                ns.recursive, ns.by)
    elif cmd == "sizes":
        display_folder_sizes(clean_path(ns.folder), ns.sort)
    elif cmd == "drives":
        display_all_drives()
    elif cmd == "find":
        root = clean_path(ns.root)
        if ns.type == "folder":
            find_folders(root, ns.value)
        elif ns.type == "name":
            find_files_by_name(root, ns.value)
        elif ns.type == "ext":
            find_files_by_ext(root, ns.value)
        elif ns.type in ("over", "under"):
            find_by_size(root, float(ns.value), over=(ns.type == "over"))
    elif cmd == "find-files":
        find_files_combined(clean_path(ns.root), ns.name, ns.ext, ns.over, ns.under)
    elif cmd == "find-dups":
        find_duplicates_by_filename(ns.folders)
    elif cmd == "find-fuzzy-dups":
        find_duplicates_by_fuzzy_name(ns.folders)
    elif cmd == "find-missing":
        find_missing_by_filename(ns.a, ns.b, ns.mode, ns.size)
    elif cmd == "find-replace":
        find_and_replace(clean_path(ns.root), ns.search, ns.replace, ns.ext,
                         live_requested=ns.apply, assume_yes=ns.yes,
                         backup=ns.bak)
    elif cmd == "find-rename":
        if ns.prepend is not None:
            mode, text, repl = "prepend", ns.prepend, None
        elif ns.append_text is not None:
            mode, text, repl = "append", ns.append_text, None
        else:
            mode, text, repl = "replace", ns.replace[0], ns.replace[1]
        find_and_rename(clean_path(ns.root), mode, text, repl, ns.ext,
                        live_requested=ns.apply, assume_yes=ns.yes)
    elif cmd == "remove":
        live = True if ns.delete else False
        if ns.type == "folder":
            _cli_remove_folder(ns.args[0], live, ns.yes)
        elif ns.type == "name":
            _cli_remove_name(ns.args, live, ns.yes)
        elif ns.type == "folder-name":
            _cli_remove_folder_name(ns.args, live, ns.yes)
        elif ns.type == "dup-name":
            _cli_dupname(ns.args, live, ns.yes)
        elif ns.type == "dup-hash":
            _cli_duphash(ns.args, live, ns.yes)
        elif ns.type == "dup-fuzzy":
            remove_duplicates_by_fuzzy_name(ns.args, live, assume_yes=ns.yes)
        elif ns.type == "zero-size":
            remove_zero_size_files(ns.args, live, assume_yes=ns.yes)
    elif cmd == "monitor":
        if ns.profile:
            profiles, perr = _load_monitor_profiles()
            pr = next((p for p in profiles
                       if str(p.get("name", "")).lower() == ns.profile.lower()), None)
            if perr:
                print(color_text(f"  {perr}", fg=RED))
            elif pr is None:
                names = ", ".join(str(p.get("name", "?")) for p in profiles) or "(none defined)"
                print(color_text(f"  No monitor profile named '{ns.profile}'. Profiles: {names}", fg=RED))
            else:
                monitor_activity(clean_path(str(pr.get("folder", ""))),
                                 recursive=bool(pr.get("recursive", True)),
                                 exts=pr.get("extensions", ""),
                                 output="csv" if (ns.csv or str(pr.get("output", "log")).lower() == "csv") else "log",
                                 profile_name=pr.get("name") or "(unnamed profile)")
        elif not ns.folder:
            print(color_text("  usage: monitor FOLDER  (or: monitor --profile NAME)", fg=RED))
        else:
            monitor_activity(clean_path(ns.folder),
                             recursive=not ns.no_recursive,
                             exts=ns.ext or "",
                             output="csv" if ns.csv else "log")
    elif cmd == "eject":
        if ns.list:
            drives = _external_drives()
            if drives:
                print()
                _print_drive_list(drives)
            else:
                print(color_text("  No external drives found.", fg=YELLOW))
        else:
            eject_external_drives(live_requested=True, assume_yes=ns.yes,
                                  force=ns.force)
    elif cmd == "sync":
        live = True if ns.copy else False
        if ns.profile:
            profiles, perr = _load_sync_profiles()
            pr = next((p for p in profiles
                       if str(p.get("name", "")).lower() == ns.profile.lower()), None)
            if perr:
                print(color_text(f"  {perr}", fg=RED))
            elif pr is None:
                names = ", ".join(str(p.get("name", "?")) for p in profiles) or "(none defined)"
                print(color_text(f"  No sync profile named '{ns.profile}'. Profiles: {names}", fg=RED))
            else:
                _run_sync_profile(pr, live_requested=live, assume_yes=ns.yes)
        elif not ns.a or not ns.b:
            print(color_text("  usage: sync FOLDER_A FOLDER_B  (or: sync --profile NAME)", fg=RED))
        else:
            sync_folders(clean_path(ns.a), clean_path(ns.b),
                         {"b": "a2b", "a": "b2a", "both": "both"}[ns.to],
                         recursive=not ns.no_recursive,
                         conflict=ns.conflict,
                         exclude_hidden=not ns.include_hidden,
                         live_requested=live, assume_yes=ns.yes)
    elif cmd == "zip-subfolders":
        zip_subfolders(ns.target, ns.dest, ns.remove)
    elif cmd == "zip-view":
        zip_view(ns.path)
    elif cmd == "zip-log":
        log_zip_files(ns.target)
    elif cmd == "cleanup":
        live = True if ns.delete else False
        if ns.what == "junk":
            if not ns.path:
                print(color_text("  usage: cleanup junk ROOT [--delete] [--yes]", fg=RED))
            else:
                cleanup_junk_files(ns.path, live_requested=live, assume_yes=ns.yes)
        else:
            cleanup_purge_logs(ns.path or LOG_PURGE_DIR, ns.days,
                               live_requested=live, assume_yes=ns.yes)


# CLI remove wrappers reuse the screen functions but pass live_requested and
# assume_yes through the shared _finish_removal path.
def _cli_remove_folder(path, live, yes):
    screen("Remove Folder"); print()
    path = clean_path(path)
    print(f"  {YELLOW}Target{RESET}: {path}\n")
    if not os.path.isdir(path):
        print(color_text(f"  Not a directory: {path}", fg=RED)); return
    total, _ = folder_stats(path)
    _finish_removal([(path, total, True)], live, assume_yes=yes)


def _cli_remove_name(args, live, yes):
    if len(args) < 2:
        print(color_text("  usage: remove name PATTERN ROOT", fg=RED)); return
    pattern, root = args[0], clean_path(args[1])
    screen("Remove Files by Name"); print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); return
    items = []
    for dp, dns, fns in os.walk(root):
        for fn in fns:
            if fnmatch.fnmatch(fn, pattern):
                p = os.path.join(dp, fn)
                items.append((p, file_size(p), False))
    items.sort(key=lambda t: t[0])
    _finish_removal(items, live, assume_yes=yes)


def _cli_remove_folder_name(args, live, yes):
    if len(args) < 2:
        print(color_text("  usage: remove folder-name PATTERN ROOT", fg=RED)); return
    pattern, root = args[0], clean_path(args[1])
    screen("Remove Folders by Name"); print()
    print(f"  {YELLOW}Root{RESET}: {root}    {YELLOW}Pattern{RESET}: {pattern}\n")
    if not os.path.isdir(root):
        print(color_text(f"  Not a directory: {root}", fg=RED)); return
    matches = []
    for dp, dns, fns in os.walk(root):
        for d in dns:
            if fnmatch.fnmatch(d, pattern):
                matches.append(os.path.join(dp, d))
    items = [(m, folder_stats(m)[0], True) for m in _topmost(matches)]
    _finish_removal(items, live, assume_yes=yes)


def _cli_dupname(folders, live, yes):
    screen("Remove Duplicates (by Name)"); print()
    files = _gather_files(folders)
    groups = defaultdict(list)
    for p in files:
        groups[os.path.basename(p)].append(p)
    items = []
    for name, paths in sorted(groups.items()):
        if len(paths) > 1:
            for p in sorted(paths)[1:]:
                items.append((p, file_size(p), False))
    _finish_removal(items, live, assume_yes=yes, require_yes=True)


def _cli_duphash(folders, live, yes):
    screen("Remove Duplicates (by Hash)"); print()
    files = _gather_files(folders)
    by_size = defaultdict(list)
    for p in files:
        by_size[file_size(p)].append(p)
    groups = defaultdict(list)
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for p in paths:
            h = _hash_file(p)
            if h:
                groups[h].append(p)
    items = []
    for h, paths in groups.items():
        if len(paths) > 1:
            for p in sorted(paths)[1:]:
                items.append((p, file_size(p), False))
    _finish_removal(items, live, assume_yes=yes, require_yes=True)


# =============================================================================
# ENTRY POINT
# =============================================================================
def main():
    if len(sys.argv) > 1:
        global INTERACTIVE
        INTERACTIVE = False
        parser = build_parser()
        ns = parser.parse_args()
        if not ns.cmd:
            parser.print_help()
            return
        try:
            run_cli(ns)
        except KeyboardInterrupt:
            print()
        return

    try:
        main_menu()
    except KeyboardInterrupt:
        print()
        exit_screen(SCRIPT_NAME, VER)


if __name__ == "__main__":
    main()
