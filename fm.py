#!/opt/homebrew/opt/python@3.12/libexec/bin/python3
#
# Filename: fm.py
# Project: File Management
# Version: 1.22
# Description: File Management — a unified interactive + CLI tool that combines
#              the compare, display, find, remove, and zip file-management
#              scripts into a single CB9Lib-based program.
# Maintainer: Cloud Box 9 Inc.
# Last Modified Date: 2026-07-13
#
# Usage (interactive):
#   fm.py
#
# Usage (CLI):
#   fm.py compare-2files   FILE_A FILE_B
#   fm.py compare-contents A B [--recursive] [--by name|size|both]
#   fm.py sizes [FOLDER] [--sort alpha|size]
#   fm.py find folder PATTERN [ROOT]
#   fm.py find name   PATTERN [ROOT]
#   fm.py find ext    EXT     [ROOT]
#   fm.py find over   N       [ROOT]      (N = megabytes)
#   fm.py find under  N       [ROOT]      (N = megabytes)
#   fm.py find-files [ROOT] [--name PAT] [--ext E] [--over N] [--under N]   (combined AND)
#   fm.py find-dups   FOLDER...           (duplicate filenames, size table per folder)
#   fm.py find-missing A B [--in first|second|either] [--size]   (filenames in only one
#                                          folder; --size also matches the file size)
#   fm.py remove folder      PATH        [--delete] [--yes]
#   fm.py remove name        PATTERN ROOT [--delete] [--yes]   (files by name)
#   fm.py remove folder-name PATTERN ROOT [--delete] [--yes]   (folders by name)
#   fm.py remove dup-name    FOLDER...    [--delete] [--yes]
#   fm.py remove dup-hash    FOLDER...    [--delete] [--yes]
#   fm.py zip-subfolders  TARGET [DEST] [-r]
#   fm.py zip-view [ZIP|FOLDER]
#   fm.py zip-log  TARGET                 (log .zip/.tar to CB9Inventory)
#
# NOTE: All Remove actions default to a DRY RUN (nothing is deleted). Deletion
#       only happens when explicitly opted-in (interactive confirm, or the
#       --delete flag on the CLI).
#
# -----------------------------------------------------------------------------
# Revision History: see CHANGE_LOG.md
# -----------------------------------------------------------------------------

import sys
import os
import argparse
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
SCRIPT_NAME = "File Management"
VERSION     = "1.22"
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


def render_menu(subtitle, options, is_main=False, intro=None, outro=None):
    """Render a CB9 menu and return the user's choice.

    Navigation (interactive TTY):
      • ↑/↓ arrows move the highlighted option; Enter selects it.
      • Typing a number also selects that option (multi-digit buffered).
      • H shows Help; Q or ESC go Back (submenu) / Exit (main) — instant.

    options : list of (label, description) tuples. Description is shown by [H].
    intro   : optional context line shown above the options.
    outro   : optional context line(s) — str or list of str — shown below the
              options (e.g. the folders already entered).
    Returns str(number) for a selection, or 'back' (submenu) / 'quit' (main).
    Falls back to line input when stdin is not an interactive TTY (piped/CLI).
    """
    n = len(options)
    if n == 0:
        return "back"
    if not sys.stdin.isatty():
        return _render_menu_lines(subtitle, options, is_main, intro, outro)

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
            show_menu_help(subtitle, options)
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


def _render_menu_lines(subtitle, options, is_main, intro, outro=None):
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
            show_menu_help(subtitle, options)


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


def show_menu_help(subtitle, options):
    """Show a Help screen describing every option in the current menu.

    Descriptions are word-wrapped to the terminal width. A description may
    contain explicit newlines to force line breaks (e.g. for bullet lists);
    a line starting with a bullet keeps its hanging indent when it wraps.
    """
    screen(f"{subtitle} — Help")
    print()
    width = max(get_width() - 6, 40)
    for i, (label, desc) in enumerate(options, 1):
        print(f"  {color_text(f'{i}. {label}', fg=WHITE, style=BOLD)}")
        if desc:
            for para in desc.split("\n"):
                hang = "       " if para.lstrip().startswith(("•", "-")) else "     "
                wrapped = textwrap.fill(para.strip(), width=width,
                                        initial_indent="     ", subsequent_indent=hang)
                print(f"{DIM}{wrapped}{RESET}")
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
        ("Alphabetical",
         "List the subfolders sorted A→Z by name. Each row shows the folder, its "
         "size (human-readable), the exact byte count, and how many files it "
         "contains; a TOTAL row sums them. Best when you know the folder name "
         "you're looking for."),
        ("By Size (largest first)",
         "Same columns, but sorted by total size with the biggest folder first — "
         "the quickest way to see what is using the most space."),
    ]
    while True:
        ch = render_menu("Display — Folder Sizes", options,
                         intro="Shows each subfolder's size, byte count, and file count.")
        if ch == "back":
            return
        folder = ask_folder("Folder to measure", default=os.getcwd())
        if not folder:
            pause_return(); continue
        display_folder_sizes(folder, "size" if ch == "2" else "alpha")


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
        if ch == "3":
            folders = _ask_folders_multi()
            if folders:
                find_duplicates_by_filename(folders)
            else:
                pause_return()
            continue
        if ch in ("4", "5"):
            match_size = (ch == "5")
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
            root = ask_folder("Search root", default=os.getcwd())
            if not root:
                pause_return(); continue
            print(f"  {DIM}Tip: use '.DS_Store' or 'desktop.ini' to clean junk files.{RESET}")
            pat = ask("File name/pattern to remove (wildcards ok)")
            if pat:
                remove_by_name(root, pat, live_requested=None)
        elif ch == "4":
            root = ask_folder("Search root", default=os.getcwd())
            if not root:
                pause_return(); continue
            pat = ask("Folder name/pattern to remove (wildcards ok)")
            if pat:
                remove_folders_by_name(root, pat, live_requested=None)


def zip_menu():
    options = [
        ("View Zip",
         "Inspect a zip WITHOUT extracting it: each entry's uncompressed and "
         "compressed size, compression ratio, and modified date, plus totals. "
         "Give a single .zip file to view it directly, or give a folder to pick "
         "from the zips inside it."),
        ("Log Zip File",
         "Log a .zip or .tar archive — or every archive in a folder (top level "
         "only) — to the CB9Inventory database on a remote server via the DocInfo Manager "
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


def main_menu():
    options = [
        ("Compare  — compare 2 files, or folder contents",
         "Two tools. 'Compare 2 Files' shows two text files side by side with a "
         "line-by-line diff. 'Compare Folder Contents' compares what's inside two "
         "folders by name and/or size, top-level or recursively — handy for "
         "checking a backup against the original."),
        ("Display  — folder sizes",
         "List every immediate subfolder of a chosen folder with its total size "
         "(human-readable and exact bytes) and file count, sorted alphabetically "
         "or largest-first, ending with a grand total. Good for finding what's "
         "eating disk space."),
        ("Find     — files by combined criteria, folders by name, duplicates",
         "'Find Files' searches for files matching one or more criteria AND-ed "
         "together (filename pattern, extension, size over N MB, size under N MB) "
         "— e.g. .mov files under 5 MB. 'Find Folders' finds directories by name "
         "pattern. 'Find Duplicates by Filename' scans one or more folders and "
         "tables files sharing the same name with a size column per folder. "
         "'Find Missing by Filename' compares two folders and tables the files "
         "present in only one of them. Nothing is changed; results are just "
         "listed."),
        ("Remove   — duplicates, files/folders by name",
         "Delete duplicate files (by name or by exact content), files by name "
         "pattern, or folders by name pattern. Every removal shows a preview and "
         "is a DRY RUN until you confirm — nothing is deleted by accident."),
        ("Zip      — view zip, log zip file, zip subfolders",
         "'View Zip' lists a zip's contents (sizes, ratios, dates) without "
         "extracting it. 'Log Zip File' records a .zip/.tar (or a folder of "
         "them) to the CB9Inventory database. 'Zip SubFolders' compresses each "
         "subfolder of a target into its own .zip."),
    ]
    while True:
        ch = render_menu("Main Menu", options, is_main=True,
                         intro="Compare · Display · Find · Remove · Zip")
        if ch == "quit":
            exit_screen(SCRIPT_NAME, VER)
            return
        elif ch == "1":
            compare_menu()
        elif ch == "2":
            display_menu()
        elif ch == "3":
            find_menu()
        elif ch == "4":
            remove_menu()
        elif ch == "5":
            zip_menu()


# =============================================================================
# CLI
# =============================================================================
def build_parser():
    p = argparse.ArgumentParser(
        prog="fm.py", add_help=True,
        description="File Management — compare, display, find, remove, zip. "
                    "Run with no arguments for the interactive menu.")
    sub = p.add_subparsers(dest="cmd")

    c2 = sub.add_parser("compare-2files", help="Compare two files side by side")
    c2.add_argument("a"); c2.add_argument("b")

    cc = sub.add_parser("compare-contents", help="Compare the contents of two folders")
    cc.add_argument("a"); cc.add_argument("b")
    cc.add_argument("--recursive", action="store_true", help="Descend into subfolders (default: top level only)")
    cc.add_argument("--by", choices=["name", "size", "both"], default="both")

    sz = sub.add_parser("sizes", help="Display subfolder sizes")
    sz.add_argument("folder", nargs="?", default=".")
    sz.add_argument("--sort", choices=["alpha", "size"], default="alpha")

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

    fmis = sub.add_parser("find-missing", help="Find filenames present in only one of two folders (size table)")
    fmis.add_argument("a"); fmis.add_argument("b")
    fmis.add_argument("--in", dest="mode", choices=["first", "second", "either"], default="either",
                      help="show names in the 1st folder only, the 2nd only, or either (default)")
    fmis.add_argument("--size", action="store_true",
                      help="match by filename AND size (same name with a different size = missing)")

    rm = sub.add_parser("remove", help="Remove items (dry-run unless --delete)")
    rm.add_argument("type", choices=["folder", "name", "folder-name", "dup-name", "dup-hash"])
    rm.add_argument("args", nargs="+")
    rm.add_argument("--delete", action="store_true", help="Actually delete (default: dry run)")
    rm.add_argument("--yes", action="store_true", help="Skip confirmation when deleting")

    zs = sub.add_parser("zip-subfolders", help="Zip each subfolder")
    zs.add_argument("target"); zs.add_argument("dest", nargs="?", default=None)
    zs.add_argument("-r", "--remove", action="store_true", help="Remove source folders after zip")

    zv = sub.add_parser("zip-view", help="View a zip file or browse a folder of zips")
    zv.add_argument("path", nargs="?", default=None)

    zl = sub.add_parser("zip-log", help="Log a .zip/.tar (or a folder of them) to CB9Inventory")
    zl.add_argument("target")

    return p


def run_cli(ns):
    cmd = ns.cmd
    if cmd == "compare-2files":
        compare_two_files(clean_path(ns.a), clean_path(ns.b))
    elif cmd == "compare-contents":
        compare_folder_contents(clean_path(ns.a), clean_path(ns.b),
                                ns.recursive, ns.by)
    elif cmd == "sizes":
        display_folder_sizes(clean_path(ns.folder), ns.sort)
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
    elif cmd == "find-missing":
        find_missing_by_filename(ns.a, ns.b, ns.mode, ns.size)
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
    elif cmd == "zip-subfolders":
        zip_subfolders(ns.target, ns.dest, ns.remove)
    elif cmd == "zip-view":
        zip_view(ns.path)
    elif cmd == "zip-log":
        log_zip_files(ns.target)


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
