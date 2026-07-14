# File Manager (`fm.py`)

A single, unified command‑line tool for the everyday file‑management chores that
used to live in nine separate scripts. **File Manager** gives you an interactive
menu **and** scriptable CLI subcommands for comparing, measuring, finding,
removing, and zipping files and folders.

> Built on **CB9Lib** (headers, footers, menus, colors, confirmations, project
> sounds). Every destructive action is a **dry run by default** — nothing is
> deleted unless you explicitly opt in.

---

## Table of Contents

1. [Overview](#overview)
2. [What It Replaces](#what-it-replaces)
3. [Features](#features)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Alias Setup — Run From Anywhere](#alias-setup--run-from-anywhere)
7. [Configuration](#configuration)
8. [Usage — Interactive Mode](#usage--interactive-mode)
9. [Usage — CLI Mode](#usage--cli-mode)
10. [The Dry‑Run Safety Model](#the-dry-run-safety-model)
11. [Logging — The Activity Log](#logging--the-activity-log)
12. [Full Option Reference](#full-option-reference)
13. [Worked Examples](#worked-examples)
14. [Troubleshooting](#troubleshooting)
15. [License / Copyright](#license--copyright)

---

## Overview

`fm.py` is a **CB9Lib**‑based Python program. Run it with **no arguments** to get
a full‑screen interactive menu:

```
Compare  →  Compare 2 Files (side by side), Compare Folder Contents
                (Recursive Y/N · By Name / Size / Both)
Display  →  All Drives (size & free space) · Subfolder Sizes (alpha / largest first)
Eject    →  Eject All External Drives (macOS)
Find     →  Find Files (name · ext · size over/under, combined) · Find Folders
                · Find Duplicates by Filename · Find Missing by Filename
                · Find Missing by Filename & Size (all show a size table per folder)
                · Find & Replace (text in files — dry run, then confirm)
Monitor  →  watch a folder for created/modified/deleted files in real time
Remove   →  duplicates (by name / by hash) · by file name · by folder name
Sync     →  push new/updated files A → B or B → A (profiles or interactive)
Zip      →  View Zip · Log Zip File · Zip SubFolders
Clean Up →  Remove Junk Files (.DS_Store / desktop.ini) · Purge Old Log Files
```

Run it **with a subcommand** to do the same work non‑interactively (ideal for
automation, cron jobs, or piping):

```bash
fm.py sizes ~/Documents --sort size
fm.py find over 500 ~/Movies
fm.py remove name "*.tmp" ~/Downloads --delete --yes
```

---

## What It Replaces

| Legacy script | Folded into |
|---------------|-------------|
| `compareFilesRecursive.sh` | **Compare → Compare Folder Contents** (Recursive) / `fm.py compare-contents --recursive` |
| `compareSubFolders.sh` | **Compare → Compare Folder Contents** (top level) / `fm.py compare-contents` |
| `folderSizes.sh` | **Display → Folder Sizes** / `fm.py sizes` |
| `findLargeFiles.sh` | **Find → Size over N** / `fm.py find over` |
| `findDuplicates.sh` | **Remove → Duplicates by Name** / `fm.py remove dup-name` |
| `findDuplicatesExt.sh` | **Remove → Duplicates by Name** (with extension filter) |
| `removeFiles.sh` | **Remove → Filename** (use pattern `.DS_Store` / `desktop.ini`) |
| `zipSubFolders.sh` | **Zip → Zip SubFolders** / `fm.py zip-subfolders` |
| `zipView.py` | **Zip → View Zip** / `fm.py zip-view` |

Two capabilities were **added** beyond a literal merge:

- **Duplicates by hash** — SHA‑256 content comparison (size‑prefiltered for
  speed), in addition to the original by‑name matching.
- **Find → Size under N** — the mirror of the original “large files” search.

---

## Features

- **Interactive menu** with **↑/↓ arrow navigation** (Enter selects the
  highlighted option; number keys also work), CB9‑standard header/footer,
  colors, and sounds (the copyright notice is shown on the exit screen).
  Submenus offer **`[H]` Help** (a detailed description of each option) and
  **`[Q/ESC]` Back** — arrows and ESC react instantly.
- **Side‑by‑side file comparison** with change markers and a diff summary.
- **CLI subcommands** for every action — same engine, no prompts.
- **Dry‑run‑by‑default** removals — preview first, delete only on explicit
  opt‑in.
- **One‑way folder sync** — push new/updated files A → B or B → A, with
  newest/largest conflict rules, saved profiles in `fmConfig.json`, and the
  same preview‑first safety model (nothing is ever deleted).
- **Eject all external drives** (macOS) — lists the mounted external drives,
  confirms, ejects each with per‑drive status, and offers a force eject for
  drives that won't let go.
- **Real‑time file activity monitor** — watch a folder (recursive optional,
  extension filter) and see every created / modified / deleted file as it
  happens, on screen and in fm.log or a CSV. No third‑party packages —
  1‑second snapshot polling.
- **Find & Replace across a folder tree** — literal, case‑insensitive text
  replacement with an optional extension filter. Always a dry run first (every
  match shown with file, line number, and highlighted text), then an explicit
  confirm, with optional `.bak` backups of each modified file.
- **Clean Up** — find and delete every `.DS_Store` / `desktop.ini` under a
  root folder, and purge log entries older than N days from every `.log` file
  in a folder (block‑aware, `.bak` backup before each rewrite). Both dry‑run
  first.
- **Recursive**, hidden‑file‑aware scanning (files/folders beginning with `.`
  are ignored in compares and zip listings).
- **Human‑readable + exact byte** sizes everywhere.
- **Collision‑safe zipping** (`name.zip`, `name-2.zip`, `name-3.zip`, …) with
  automatic `.DS_Store` / `desktop.ini` cleanup.
- **Zip inspection** without extracting — per‑file compression ratios and totals.
- **Per‑project sound overrides** via `~/userProfile.json`.

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **Python ≥ 3.10** | The script shebang targets `/opt/homebrew/opt/python@3.12/libexec/bin/python3`. |
| **CB9Lib** | Expected at `~/Documents/script/CB9Lib` (added to `sys.path` automatically). |
| **`zip` command** | Used by **Zip SubFolders** (pre‑installed on macOS; `apt install zip` on Linux). |
| **`diskutil`** (macOS) | Used by **Eject All External Drives** — this feature is macOS‑only. |
| **macOS / Linux terminal** | ANSI colors and terminal‑width detection. Sounds use `afplay` (macOS). |

No third‑party Python packages are required — only the standard library and
CB9Lib.

---

## Installation

1. **Confirm CB9Lib is present** at `~/Documents/script/CB9Lib` (the script does
   `sys.path.insert(0, "~/Documents/script/CB9Lib")` and then `from CB9Lib import …`):

   ```bash
   ls ~/Documents/script/CB9Lib/CB9Lib/__init__.py
   ```

2. **Make the script executable** (already done if you cloned this folder):

   ```bash
   chmod +x ~/Documents/script/FM/fm.py
   ```

3. **Run it**:

   ```bash
   ~/Documents/script/FM/fm.py           # interactive menu
   ~/Documents/script/FM/fm.py --help    # CLI reference
   ```

> **Optional — custom sounds:** create an `audio/` folder next to `fm.py`
> containing `success.mp3` and `failure.wav` to hear a chime when a task
> finishes. Missing sound files are silently ignored.

---

## Alias Setup — Run From Anywhere

Create a short command so you can type `fm` from any directory.

### macOS / Linux (bash / zsh)

Add this to `~/.zshrc`, `~/.bashrc`, or `~/.bash_profile`:

```bash
alias fm='python3 ~/Documents/script/FM/fm.py'
```

Then reload your shell:

```bash
source ~/.zshrc     # or: source ~/.bashrc
```

Confirm it works:

```bash
fm --help
```

**Alternative (symlink onto your PATH):**

```bash
chmod +x ~/Documents/script/FM/fm.py
ln -s ~/Documents/script/FM/fm.py /usr/local/bin/fm
fm --help
```

### Windows

**PowerShell** — add a function to your `$PROFILE`:

```powershell
function fm { python "$HOME\Documents\script\FM\fm.py" @args }
```

Reload with `. $PROFILE`, then run `fm --help`.

**Batch wrapper** — save `fm.bat` somewhere on your `PATH`:

```bat
@echo off
python "%USERPROFILE%\Documents\script\FM\fm.py" %*
```

> **Note:** `fm.py` uses ANSI colors, terminal sizing, and `afplay`/`zip`, so it
> is designed for macOS/Linux. On Windows, run it under **WSL** or **Git Bash**
> for the best experience; the full path is
> `~/Documents/script/FM/fm.py`.

---

## Configuration

`fm.py` needs **no config file** for everyday use — folders and options are
supplied interactively or as CLI arguments. There are four configurable
behaviors:

### 1. CB9Lib location

The script adds CB9Lib to the path itself:

```python
sys.path.insert(0, os.path.expanduser("~/Documents/script/CB9Lib"))
from CB9Lib import (...)
```

If your CB9Lib lives elsewhere, edit that one line near the top of `fm.py`.

### 2. Sound preferences (`~/userProfile.json`)

Completion sounds default to `audio/success.mp3` and `audio/failure.wav` beside
`fm.py`. You can override them per project in `~/userProfile.json` using the
project name **`File Manager`**:

```json
{
  "projectPreferences": [
    {
      "projectName": "File Manager",
      "successAudio": "~/Documents/sounds/done.mp3",
      "failureAudio": "~/Documents/sounds/error.wav"
    }
  ]
}
```

Lookup is safe: if the profile is missing, the project has no entry, or the file
does not exist, `fm.py` silently falls back to the bundled defaults (and if those
are missing too, it simply plays nothing).

### 3. Sync profiles (`fmConfig.json`)

Saved sync setups live in `fmConfig.json` (beside `fm.py`) as a `syncProfiles`
list. Each profile appears as its own option at the top of the **Sync** menu
and can also be run from the CLI with `fm.py sync --profile NAME`:

```json
{
  "syncProfiles": [
    {
      "name": "Media to Backup",
      "folderA": "~/Media",
      "folderB": "/Volumes/CB9-2t/MediaBackup",
      "direction": "AtoB",
      "recursive": true,
      "conflict": "newest",
      "excludeHidden": true
    }
  ]
}
```

| Key | Values | Default | Meaning |
|-----|--------|---------|---------|
| `name` | string | *(unnamed profile)* | Label shown in the Sync menu / matched by `--profile` |
| `folderA` / `folderB` | paths (`~` ok) | — | The two folders |
| `direction` | `AtoB` / `BtoA` | `AtoB` | Which side pushes its new/updated files |
| `recursive` | `true` / `false` | `true` | Include subfolders |
| `conflict` | `newest` / `largest` | `newest` | When a file exists on both sides, copy only if the source is newer / larger |
| `excludeHidden` | `true` / `false` | `true` | Skip hidden files/folders (names starting with `.`) |

Profiles run exactly like an interactive sync: a **preview first**, and nothing
is copied until you confirm. The same reference is available in the app — press
**`H`** on the Sync menu.

### 4. Monitor profiles (`fmConfig.json`)

Saved monitor setups live in the same file as a `monitorProfiles` list. Each
profile appears at the top of the **Monitor** menu and can be run from the CLI
with `fm.py monitor --profile NAME`:

```json
{
  "monitorProfiles": [
    {
      "name": "Watch Downloads",
      "folder": "~/Downloads",
      "recursive": true,
      "extensions": "zip,dmg,pdf",
      "output": "log"
    }
  ]
}
```

| Key | Values | Default | Meaning |
|-----|--------|---------|---------|
| `name` | string | *(unnamed profile)* | Label shown in the Monitor menu / matched by `--profile` |
| `folder` | path (`~` ok) | — | The folder to watch |
| `recursive` | `true` / `false` | `true` | Include subfolders |
| `extensions` | `"jpg,png"` or a list | *(all files)* | Only report files with these extensions |
| `output` | `log` / `csv` | `log` | Log events to `fm.log` or to `~/Documents/log/fmMonitor.csv` |

The same reference is available in the app — press **`H`** on the Monitor menu.

---

## Usage — Interactive Mode

Launch with no arguments:

```bash
fm            # if the alias is set
# or
~/Documents/script/FM/fm.py
```

You’ll see the **Main Menu**. Use the **↑/↓ arrow keys** to move the highlighted
option and press **Enter** to select it — or type the option **number**.

**Every screen** shows the standard footer with a legend of the available keys
(the **copyright notice appears on the exit screen**, not on the menus):

| Key | On the Main Menu | On a submenu |
|-----|------------------|--------------|
| `↑` / `↓` | Move the highlight | Move the highlight |
| `Enter` | Select the highlighted option | Select the highlighted option |
| `#` (number) | Select that option | Select that option |
| `H` | Show Help (a description of every option) | Show Help |
| `Q` | **Exit** (exit screen) | **Back** to the parent menu |
| `ESC` | **Exit** — reacts instantly | **Back** — reacts instantly |

Key points:

- **↑/↓ move the highlight; Enter selects it.** The highlight starts on option 1.
- **Typing a number** also selects that option (multi‑digit is buffered).
- **`Q` and `ESC` both go back** on a submenu, and both **exit** on the Main Menu.
- **`ESC` and the arrows are instant** — they don't require pressing Enter.
- **`H`** prints a short description of each option, then returns you to the menu.
- When a **Compare** or **Find** finishes, the footer offers **[R] Run Again**
  (rerun the same action with the same inputs — a fresh scan) and
  **[Q/ESC] Quit/Back** (Enter also goes back).

### Main Menu

| # | Option | What it does |
|---|--------|--------------|
| 1 | **Compare** | Compare two files side by side, or compare folder contents |
| 2 | **Display** | All drives (size & free space), or subfolder sizes |
| 3 | **Eject** | Eject all external drives (macOS, confirms first) |
| 4 | **Find** | Locate folders/files by name, extension, or size; find duplicate or missing filenames |
| 5 | **Monitor** | Watch a folder for file activity in real time (profiles or interactive) |
| 6 | **Remove** | Delete folders, files, or duplicates (dry‑run first) |
| 7 | **Sync** | Push new/updated files between two folders (profiles or interactive, dry‑run first) |
| 8 | **Zip** | View a zip’s contents, log a zip to CB9Inventory, or zip each subfolder |
| 9 | **Clean Up** | Remove junk files, or purge old entries from log files (dry‑run first) |
| Q | **Quit** | Exit with the standard CB9 exit screen |

Press **`H`** on any menu for on‑screen descriptions of its options. The Main
Menu Help ends with a **Logging** section showing where commands and results
are logged (see [Logging — The Activity Log](#logging--the-activity-log)).

### 1 · Compare

The Compare submenu has two options (press **`H`** in the menu for these
descriptions on screen):

**1. Compare 2 Files** — compare two files **side by side**, line by line.

1. Enter **File A** and **File B**.
2. The two files are shown in parallel columns with a line number and a marker:

   | Marker | Meaning |
   |--------|---------|
   | `=` | Lines are identical |
   | `≠` | Line changed between A and B |
   | `<` | Line exists only in A |
   | `>` | Line exists only in B |

   A summary line reports counts (equal / changed / only‑A / only‑B), or
   “Files are identical.”

**2. Compare Folder Contents** — compare what’s inside two folders.

1. Enter **Folder A** and **Folder B**.
2. **Recursive?** — answer **Y** to compare every file beneath each folder, or
   **N** to compare only the immediate top‑level entries (files *and* subfolders).
3. **Compare By**:
   - **By Name** — entries present in one folder but not the other (both
     directions are always reported).
   - **By Size** — entries present in *both* whose size differs.
   - **Both** — runs the By Name report *and* the By Size report.

Hidden files/folders (names starting with `.`) are ignored throughout.

### 2 · Display

The Display menu has three options:

**1. All Drives** — size and free space of every mounted drive: the boot
volume plus each drive under `/Volumes` (each physical drive listed once).
Columns: **Drive**, **Size**, **Used**, **Free**, **Use%**, **Mount Point**.
Free is the space actually available to you, matching Finder's **Available**
figure, and Use% turns yellow at 75% and red at 90%.

**2. Subfolders Alphabetically / 3. Subfolders by Size (largest first)** —
enter the folder to measure (defaults to the current directory); its immediate
subfolders are listed A→Z or biggest‑first. Output columns (in order):
**Folder** (always first), **Size (human‑readable)**, **Bytes
(comma‑formatted)**, **File Count** — with a **TOTAL** row.

### 3 · Eject  *(macOS)*

**Eject All External Drives** — the equivalent of clicking every external
drive's eject button at once:

1. The mounted external drives are listed (name, size, mount point). External
   = `diskutil info` reports `Internal: No`, a USB / Thunderbolt / SATA /
   FireWire protocol, or removable media.
2. Confirm **Eject all N drive(s)?** — the default is **No**.
3. Each drive is ejected with a per‑drive **Success / Failed** status
   (`diskutil eject`, falling back to Finder's eject via AppleScript).
4. If any drive won't let go (Spotlight indexing, an app holding files open),
   you're offered a **force eject** (`diskutil unmountDisk force`) for just
   the failed drives.

The drive list and results are appended to the
[activity log](#logging--the-activity-log). Internal disks and the boot
volume are never touched.

### 4 · Find

The Find submenu has six options. All Find searches (and folder Compares)
skip the Windows Recycle Bin folder (`$RECYCLE.BIN`) found on external drives,
plus `.DS_Store` and `desktop.ini` junk files. (**Remove → By File Name** can
still target `.DS_Store` / `desktop.ini` intentionally for cleanup.)

**1. Find Files (one or more criteria)** — select **multiple** criteria and
combine them (logical **AND**). On the criteria screen, use **↑/↓** to move,
**Space** to toggle a criterion on/off, and **Enter** to confirm. Then you're
prompted for each selected criterion's value, and finally the **search root**.

| Criterion | Prompt | Keeps files that are… |
|-----------|--------|------------------------|
| **Filename pattern** | wildcard (e.g. `IMG_*.jpg`) | name matches the pattern |
| **File extension** | extension, e.g. `mov` | have that extension |
| **Size over N MB** | threshold in MB | larger than N MB |
| **Size under N MB** | threshold in MB | smaller than N MB |

> **Example — “`.mov` files under 5 MB”:** toggle **File extension** and **Size
> under N MB**, enter `mov` and `5`. Results are files matching *both* criteria.

**2. Find Folders (by name/pattern)** — find directories whose name matches a
wildcard pattern, recursively.

**3. Find Duplicates by Filename** — enter **one or more folders**
(comma‑separated). Each folder is scanned recursively (hidden files like
`.DS_Store` are skipped) and files sharing the **same filename** are reported
in a table: a numbered header lists the folders, then one row per duplicated
filename with a **size column per folder**, so you can see where each copy
lives and whether the sizes match. If a name occurs more than once inside a
single folder, every size is listed in that column. Matching is by filename
only — contents are not compared. Read‑only: nothing is changed.

```
  1 - /Volumes/CB9-2t/lostMedia
  2 - /Volumes/CB9-2t/UncategorizedImages

  Filename            1         2
  ---------  ----------  --------
  betty.jpg        1.1K      2.2M
  twice.txt  100B, 2.9K
```

The results screen is also appended (plain text, timestamped) to the activity
log at `~/Documents/log/fm.log`.

**4. Find Missing by Filename** — enter **two folders**, then choose what to
show:

| Option | Shows |
|--------|-------|
| **In 1st folder only** | filenames the 2nd folder is missing |
| **In 2nd folder only** | filenames the 1st folder is missing |
| **In either folder (only once)** | both directions together |

Each folder is scanned recursively (hidden files skipped) and files are
matched by **filename only** — contents are not compared. Results use the same
table as Find Duplicates by Filename: a numbered folder header, one row per
filename, one size column per folder — the **blank column** shows where the
file is missing. In the **1st/2nd folder only** modes, a last **Folder**
column shows the directory actually containing each file. The Folder 1/2 list
is repeated after the results, and the results screen is also appended to the
activity log at `~/Documents/log/fm.log`. Read‑only: nothing is changed.

**5. Find Missing by Filename & Size** — same flow as Find Missing by
Filename, but files only count as a match when **both the filename AND the
file size agree**. A same‑named file whose size differs between the two
folders is therefore also reported — with its size shown in **both** columns
so the mismatch is obvious:

```
  Filename            1         2
  ---------  ----------  --------
  betty.jpg        1.1K      2.2M   ← same name, different size
  solo.png         500B             ← only in folder 1
```

Patterns use shell‑style wildcards: `*` (any run of chars), `?` (one char),
`[abc]` (character set). When a size criterion is active, results are sorted
largest‑first; otherwise alphabetically.

**6. Find & Replace** — enter a **folder**, the **text to find**, the
**replacement text** (blank = remove the text), and an optional **file
extension**. The folder is scanned recursively; hidden files/folders, binary
files, and `.bak` files are skipped, and matching is **literal and
case‑insensitive**. It is **always a dry run first**: every match is listed
with its file, line number, and the line with the matched text highlighted —
nothing is touched. A `[y/N]` confirm then replaces every occurrence (a
follow‑up prompt offers a **`.bak` backup** of each modified file first);
answering No exits with nothing changed. File bytes and line endings
round‑trip unchanged apart from the replacement, and the results screen is
appended to the activity log.

### 5 · Monitor  *(real‑time)*

**Monitor File Activity** — watch a folder and see every file event as it
happens. The Monitor menu lists your saved **profiles** (see
[Configuration → Monitor profiles](#4-monitor-profiles-fmconfigjson)) followed
by **Interactive Monitor**, which asks for:

1. **Folder to monitor**.
2. **Include subfolders (recursive)?** — default **Yes**.
3. **File extensions to watch** — comma‑separated (e.g. `jpg, png`); leave
   blank to watch every file.
4. **Log destination** — the FM activity log (`~/Documents/log/fm.log`) or a
   CSV (`~/Documents/log/fmMonitor.csv`, rows of
   `Timestamp,Filename,Folder,Event`).

Every **created**, **modified**, and **deleted** file then appears on screen
*and* in the chosen log in real time (events are flushed immediately, so
`tail -f` works):

```
  Monitoring... [Q/ESC] Stop. Events appear below as they happen.

  7/14/26 10:26:27 am  CREATED   newfile.txt  (7 B)
  7/14/26 10:26:27 am  CREATED   sub/deep.log  (6 B)
  7/14/26 10:26:30 am  MODIFIED  existing.txt  (11 B)
  7/14/26 10:26:30 am  DELETED   newfile.txt

  Stopped — 4 event(s): 2 created, 1 modified, 1 deleted.
```

Press **`[Q/ESC]`** to stop and return to the menu (a summary line is written
to the log). Detection polls once a second with snapshot diffs — no
third‑party packages. Hidden files are included; `.DS_Store` / `desktop.ini`
junk and `$RECYCLE.BIN` are ignored. Read‑only: monitoring never changes the
watched folder.

### 6 · Remove  *(dry‑run by default)*

Pick what to remove, supply the target(s), and **review the preview**. Nothing is
deleted until you answer **Yes** to the confirmation.

The menu options (in order):

| # | Option | You provide | Behavior |
|---|--------|-------------|----------|
| 1 | **Duplicates by Name** | one or more folders (comma‑separated), optional extension | Groups files by name; **keeps the first**, lists the rest for removal |
| 2 | **Duplicates by Hash** | one or more folders | Groups files by SHA‑256 content; **keeps the first**, lists the rest |
| 3 | **By File Name** | search root + pattern | Previews every **file** whose name matches the wildcard, then deletes on confirm. Use `.DS_Store` or `desktop.ini` to clean junk files. |
| 4 | **By Folder Name** | search root + pattern | Previews every **folder** whose name matches the wildcard (recursively) and removes each matching tree. Only top‑most matches are deleted (a matched parent already covers matched children). |

After the preview you’ll see:

> *This was a DRY RUN — nothing has been deleted yet.*
> *Actually delete these N item(s)? [y/N]*

Answer **`n`** (the default) to cancel; **`y`** to delete.

### 7 · Sync  *(dry‑run by default)*

One‑way sync: **push new/updated files** from one folder into the other.
Nothing is ever deleted, and nothing is copied until you confirm the preview.

The Sync menu lists your saved **profiles** (see
[Configuration → Sync profiles](#3-sync-profiles-fmconfigjson)) followed by
**Interactive Sync**, which asks for:

1. **Folder A** and **Folder B**.
2. **Direction** — push new/updated files **A → B**, or **B → A**.
3. **If a file exists on both sides** — choose the **newest** (copy only when
   the source is newer — the default) or the **largest** (copy only when the
   source is larger).
4. **Include subfolders (recursive)?** — default **Yes**.
5. **Exclude hidden files?** — default **Yes**.

The preview then lists every file that would be copied — `NEW` (missing from
the destination) or `UPDATE` (exists on both sides and the source wins the
conflict rule), with size and modified date, and for updates what would be
replaced:

```
  2 new, 1 updated — 57 B to copy from A to B:

  Action        Size  Modified          File
  ------- ----------  ----------------- ------------------------------
  UPDATE        25 B  7/14/26 10:00 am  changed.txt  (replaces 10 B, 1/1/26 1:01 am)
  NEW           19 B  7/14/26 10:00 am  onlyA.txt
  NEW           13 B  7/14/26 10:00 am  sub/deep.txt

  This was a DRY RUN — nothing has been copied yet.
  Actually copy these 3 file(s) from A to B? [y/N]
```

Copies preserve the file's modified time (`shutil.copy2`), so future
**newest** runs keep working correctly. Destination subfolders are created as
needed. Junk files (`.DS_Store`, `desktop.ini`) and `$RECYCLE.BIN` are always
skipped. The preview and copy results are appended to the
[activity log](#logging--the-activity-log).

### 8 · Zip

- **View Zip** — enter a **zip file** to list its contents, or a **folder** to
  pick from the zips inside it. Shows uncompressed/compressed sizes, per‑file
  compression ratio, modified date, and totals — without extracting.
- **Log Zip File** — log a `.zip` / `.tar` archive (or every archive in a
  folder, top level only) to the **CB9Inventory database** on a remote server via the
  DocInfo Manager API. Archives are matched by name + size (insert or update)
  and their file lists are synced. Requires the `logZip` section of
  `fmConfig.json` (`apiUrl`, `serverSecretKey`). `.gz` files are ignored.
- **Zip SubFolders** — enter a **target** folder (whose subfolders get zipped)
  and a **zip destination** (defaults to the current directory). You’ll be asked
  whether to **remove source folders after a successful zip**. `.DS_Store` and
  `desktop.ini` are cleaned first; name collisions become `name-2.zip`, etc.

### 9 · Clean Up  *(dry‑run by default)*

Two housekeeping tools. Like Remove, both **always preview first** — nothing
is deleted or rewritten until you confirm.

**1. Remove Junk Files** — enter a **root folder** (defaults to your home
folder). Every `.DS_Store` and `desktop.ini` beneath it is found —
**recursively, hidden folders included** — and listed with its size, using the
same preview/confirm flow as the Remove menu:

> *This was a DRY RUN — nothing has been deleted yet.*
> *Actually delete these N item(s)? [y/N]*

**2. Purge Old Log Files** — trim old entries out of **every `.log` file** in
a folder:

1. **Log folder** — defaults to `~/Documents/log`.
2. **Days to keep** — defaults to **90**. Entries with a
   `[YYYY-MM-DD HH:MM:SS]` timestamp older than that are purged.
3. A per‑file **preview table** shows the purge/keep line counts and the file
   size before anything is touched:

   ```
     Log File               Purge      Keep        Size
     -------------------  --------  --------  ----------
     claudeCommands.log      1,204     3,310      612.4K
     fm.log                      0       188       22.1K

     This was a DRY RUN — nothing has been purged yet.
     Actually purge 1,204 old line(s) from 2 file(s)? [y/N]
   ```

4. On confirm, a **`.bak` backup** of each changed file is saved before the
   file is rewritten. Files with nothing to purge are left untouched.

The purge is **block‑aware**: untimestamped lines follow their
`[YYYY-MM-DD HH:MM:SS]` header's keep/purge decision, so a multi‑line log
entry (header + body + blank line) is always kept or purged **as a whole** —
ported from `purgeLog.sh`, with this improvement.

---

## Usage — CLI Mode

Any subcommand runs non‑interactively and prints results without pausing. See
`fm.py --help` (or `fm.py <subcommand> --help`) for built‑in help.

```
fm.py compare-2files   FILE_A FILE_B
fm.py compare-contents A B [--recursive] [--by name|size|both]
fm.py sizes [FOLDER] [--sort alpha|size]
fm.py drives                          # size and free space of all mounted drives
fm.py find folder PATTERN [ROOT]
fm.py find name   PATTERN [ROOT]
fm.py find ext    EXT     [ROOT]
fm.py find over   N       [ROOT]      # N = megabytes
fm.py find under  N       [ROOT]      # N = megabytes
fm.py find-files [ROOT] [--name PAT] [--ext E] [--over N] [--under N]   # combined AND
fm.py find-dups  FOLDER...            # duplicate filenames, size table per folder
fm.py find-missing A B [--in first|second|either] [--size]   # filenames in only one folder
                                                              # --size: match name AND size
fm.py find-replace ROOT SEARCH REPLACE [--ext E] [--apply] [--bak] [--yes]
                                      # find & replace text in files (dry run unless --apply)
fm.py remove folder      PATH        [--delete] [--yes]
fm.py remove name        PATTERN ROOT [--delete] [--yes]   # files by name
fm.py remove folder-name PATTERN ROOT [--delete] [--yes]   # folders by name
fm.py remove dup-name    FOLDER...    [--delete] [--yes]
fm.py remove dup-hash    FOLDER...    [--delete] [--yes]
fm.py eject [--list] [--force] [--yes]   # eject all external drives (macOS)
fm.py monitor FOLDER [--no-recursive] [--ext jpg,png] [--csv]   # Ctrl-C stops
fm.py monitor --profile NAME             # run a monitorProfiles entry from fmConfig.json
fm.py sync FOLDER_A FOLDER_B [--to b|a] [--conflict newest|largest]
           [--no-recursive] [--include-hidden] [--copy] [--yes]
fm.py sync --profile NAME             # run a syncProfiles entry from fmConfig.json
fm.py zip-subfolders  TARGET [DEST] [-r|--remove]
fm.py zip-view [ZIP|FOLDER]
fm.py zip-log  TARGET                 # log .zip/.tar archives to CB9Inventory
fm.py cleanup junk ROOT [--delete] [--yes]                  # .DS_Store / desktop.ini
fm.py cleanup logs [FOLDER] [--days N] [--delete] [--yes]   # purge old log entries
```

Default argument values:

| Subcommand | Argument | Default |
|------------|----------|---------|
| `compare-contents` | `--recursive` / `--by` | off (top level) / `both` |
| `sizes` | `FOLDER` / `--sort` | `.` (current dir) / `alpha` |
| `find *` | `ROOT` | `.` (current dir) |
| `sync` | `--to` / `--conflict` | `b` (A→B) / `newest` |
| `zip-subfolders` | `DEST` | current directory |
| `cleanup logs` | `FOLDER` / `--days` | `~/Documents/log` / `90` |

---

## The Dry‑Run Safety Model

**Every removal is a dry run unless you explicitly opt in.** This is by design —
you always see exactly what *would* be deleted before anything happens.

| Context | Default | How to actually delete |
|---------|---------|------------------------|
| **Interactive menu** | Preview only | Answer **`y`** to the “Actually delete…?” prompt (default is **No**) |
| **CLI (no flag)** | Preview only, then: *“Re‑run with `--delete` to remove.”* | Add `--delete` |
| **CLI `--delete`** | Preview, then **confirm** prompt | Confirm with `y`, or add `--yes` to skip the prompt |
| **CLI `--delete --yes`** | Preview, then **delete immediately** | — (use with care in scripts) |

Duplicate removals always **keep the first occurrence** of each group and only
propose the remaining copies for deletion. As an extra safeguard, the two
**Duplicates** actions (by Name and by Hash) require you to **type the word
`YES`** to confirm deletion — any other input cancels (the other removals use a
simple `y/n`).

**Sync follows the same model for copying:** the preview is a dry run, and
files are only copied after the interactive confirm — or, on the CLI, with
`--copy` (plus `--yes` to skip the confirmation). Sync never deletes anything.

**Clean Up follows the same model too:** Remove Junk Files uses the exact
Remove preview/confirm flow above, and Purge Old Log Files shows its per‑file
purge/keep table first, purges only after the confirm (CLI: `--delete`, plus
`--yes` to skip the prompt), and saves a `.bak` backup of every file it
rewrites.

**Find & Replace follows it for writing:** the match list is always shown
first, and files are only modified after the confirm — or, on the CLI, with
`--apply` (plus `--yes` to skip the confirmation, and `--bak` for backups).

> 💡 **Tip:** Run any removal once with no flags (or in the menu) to inspect the
> preview, then re‑run with `--delete` once you’re satisfied. The same applies
> to `sync` — inspect the preview, then re‑run with `--copy`.

---

## Logging — The Activity Log

Commands and their results screens are logged to the FM **activity log**:

```
~/Documents/log/fm.log
```

Each run is **appended** with a `[YYYY-MM-DD HH:MM:SS]` timestamp line,
followed by the screen output exactly as it appeared — colors stripped —
including the folders entered and the full results table. The file grows
indefinitely; it is plain text, so it can be viewed with `less`, `tail`, or
any editor.

**Actions that write to the activity log:**

| Action | What is logged |
|--------|----------------|
| **Eject All External Drives** | The drive list + per‑drive eject results |
| **Find → Find Duplicates by Filename** | Folder list + the duplicate‑filename size table |
| **Find → Find Missing by Filename** (and **& Size**) | Folder 1/2 list + the missing‑filename table |
| **Find → Find & Replace** | The settings header, the dry‑run match list (file · line number · line), and what was actually replaced |
| **Monitor File Activity** | The session header, then each created/modified/deleted event **in real time**, and a closing summary. (With CSV output the events go to `~/Documents/log/fmMonitor.csv` instead.) |
| **Sync** (profiles, interactive, and CLI) | The settings header, the NEW/UPDATE preview table, and what was actually copied |
| Reruns via **`[R]` Run Again** | Each rerun is logged as a fresh timestamped entry |

Notes:

- The log directory (`~/Documents/log/`) is created automatically if missing;
  a logging failure never interrupts the on‑screen output.
- **Zip → Log Zip File** is different — it records archives to the
  **CB9Inventory database** on a remote server (via the DocInfo Manager API), not to
  `fm.log`.
- This information is also shown in the app itself: press **`H`** on the Main
  Menu — the Help screen ends with a **Logging** section.

---

## Full Option Reference

### Compare 2 Files — markers

`fm.py compare-2files FILE_A FILE_B` (no options) shows the two files side by
side. Each row is marked:

| Marker | Meaning |
|--------|---------|
| `=` | Lines are identical |
| `≠` | Line changed between A and B |
| `<` | Line exists only in A |
| `>` | Line exists only in B |

### Compare Folder Contents — `--recursive`

| State | Meaning |
|-------|---------|
| *(omitted, default)* | Compare only the immediate top‑level entries (files **and** subfolders) |
| `--recursive` | Compare every file beneath each folder |

### Compare Folder Contents — `--by` (comparison basis)

| Value | Meaning |
|-------|---------|
| `name` | Presence differences (entries in one folder only — both directions reported) |
| `size` | For entries present in **both**, report those whose size differs |
| `both` *(default)* | Run both reports |

### Display — `--sort` and `drives`

`fm.py sizes [FOLDER] --sort …`:

| Value | Meaning |
|-------|---------|
| `alpha` *(default)* | Alphabetical by folder name |
| `size` | Largest total size first |

`fm.py drives` takes no options — it prints every mounted drive with Size,
Used, Free (matches Finder's Available), Use%, and mount point.

### Find — `type` (single criterion)

| Type | Value argument | Result |
|------|----------------|--------|
| `folder` | wildcard pattern | Matching directories |
| `name` | wildcard pattern | Matching files (with size) |
| `ext` | extension (`mp4`, `.mp4`) | Files with that extension (with size) |
| `over` | number of MB | Files larger than N MB (largest first) |
| `under` | number of MB | Files smaller than N MB |

### `find-files` — combined criteria (AND)

Combine any of these flags; a file must satisfy **all** supplied criteria.
Omit a flag to skip that criterion.

| Flag | Meaning |
|------|---------|
| `--name PAT` | filename matches wildcard `PAT` |
| `--ext E` | extension is `E` (e.g. `mov`) |
| `--over N` | larger than `N` MB |
| `--under N` | smaller than `N` MB |

```bash
fm.py find-files ~/Movies --ext mov --under 5      # .mov files under 5 MB
```

### `find-dups` — duplicate filenames across folders

Pass **one or more folders**; each is scanned recursively (hidden files
skipped). Files sharing the same filename (2+ occurrences in total, within or
across folders) are shown in a table with a numbered folder header and one
size column per folder. Read‑only — nothing is changed.

```bash
fm.py find-dups /Volumes/CB9-2t/lostMedia /Volumes/CB9-2t/UncategorizedImages
```

### `find-missing` — filenames in only one of two folders

Pass **exactly two folders**; each is scanned recursively (hidden files
skipped). Filenames present in only one folder are shown in the same size
table as `find-dups` — the blank column shows where the file is missing, and
the `first`/`second` modes add a last **Folder** column with the directory
containing each file. Output is also appended to `~/Documents/log/fm.log`.
Read‑only — nothing is changed.

| Flag | Meaning |
|------|---------|
| `--in first` | names in the 1st folder but not the 2nd |
| `--in second` | names in the 2nd folder but not the 1st |
| `--in either` | both directions together *(default)* |
| `--size` | match by filename **and** size — a same‑named file with a different size is also reported |

```bash
fm.py find-missing /Volumes/CB9-2t/lostMedia /Volumes/CB9-2t/UncategorizedImages --in first
```

### `find-replace` — find & replace text in files

`fm.py find-replace ROOT SEARCH REPLACE` scans ROOT recursively (hidden
files/folders, binary files, junk names, and `.bak` files are skipped) for
**literal, case‑insensitive** occurrences of SEARCH. Without `--apply` it is a
**dry run**: every match is listed as file · line number · line with the
matched text highlighted, and nothing is touched. Use `""` as REPLACE to
delete the text. File bytes and line endings round‑trip unchanged apart from
the replacement.

| Flag | Effect |
|------|--------|
| `--ext E` | Only scan files with extension `E` (e.g. `php`) |
| `--apply` | Actually replace (otherwise dry run) |
| `--bak` | Save a `.bak` backup of each modified file before writing |
| `--yes` | Skip the confirmation prompt (only meaningful with `--apply`) |

```bash
fm.py find-replace ~/Documents/sites/mysite "old-domain.com" "new-domain.com" --ext php           # dry run
fm.py find-replace ~/Documents/sites/mysite "old-domain.com" "new-domain.com" --ext php --apply --bak
```

### Remove — `type` and flags

| Type | Positional args | Notes |
|------|-----------------|-------|
| `folder` | `PATH` | Remove one directory tree (by exact path) |
| `name` | `PATTERN ROOT` | Remove **files** matching a wildcard under ROOT |
| `folder-name` | `PATTERN ROOT` | Remove **folders** matching a wildcard under ROOT (top‑most matches) |
| `dup-name` | `FOLDER...` | Duplicate **names** across one or more folders (type **`YES`** to delete) |
| `dup-hash` | `FOLDER...` | Duplicate **content** (SHA‑256) across folders (type **`YES`** to delete) |

| Flag | Effect |
|------|--------|
| `--delete` | Perform the deletion (otherwise dry run) |
| `--yes` | Skip the confirmation prompt (only meaningful with `--delete`) |

### Eject — options *(macOS)*

| Option | Effect |
|--------|--------|
| *(none)* | List the external drives, confirm, then eject them all |
| `--list` | List the external drives and exit — nothing is ejected |
| `--force` | Force‑unmount each disk before ejecting (bypasses Spotlight / open‑file holds) |
| `--yes` | Skip the confirmation and eject immediately (failures are force‑ejected too) |

```bash
fm.py eject --list          # see what's connected
fm.py eject                 # eject everything after confirming
fm.py eject --yes           # eject everything immediately (for scripts)
```

### Monitor — options

| Option | Effect |
|--------|--------|
| `FOLDER` | The folder to watch (omit when using `--profile`) |
| `--profile NAME` | Run a saved `monitorProfiles` entry from `fmConfig.json` (case‑insensitive) |
| `--no-recursive` | Top‑level files only (default: recursive) |
| `--ext jpg,png` | Only report files with these extensions (default: all files) |
| `--csv` | Log events to `~/Documents/log/fmMonitor.csv` instead of `fm.log` |

In the interactive menu, stop with **`[Q/ESC]`**; on the CLI, stop with
**Ctrl‑C**.

```bash
fm.py monitor ~/Downloads --ext zip,dmg        # watch downloads, log to fm.log
fm.py monitor ~/Documents/sites --csv          # everything, logged as CSV rows
```

### Sync — options

| Option | Effect |
|--------|--------|
| `FOLDER_A FOLDER_B` | The two folders (omit both when using `--profile`) |
| `--to b` | Push new/updated files **A → B** *(default)* |
| `--to a` | Push new/updated files **B → A** |
| `--profile NAME` | Run a saved `syncProfiles` entry from `fmConfig.json` (name match is case‑insensitive) |
| `--conflict newest` | Both‑sides rule: copy only when the source file is **newer** *(default)* |
| `--conflict largest` | Both‑sides rule: copy only when the source file is **larger** |
| `--no-recursive` | Top‑level files only (default: recursive) |
| `--include-hidden` | Include hidden files/folders (default: excluded) |
| `--copy` | Actually copy (otherwise dry run) |
| `--yes` | Skip the confirmation prompt (only meaningful with `--copy`) |

```bash
fm.py sync ~/Media /Volumes/CB9-2t/MediaBackup             # preview A→B (dry run)
fm.py sync ~/Media /Volumes/CB9-2t/MediaBackup --copy      # copy after confirming
fm.py sync --profile "Media to Backup" --copy --yes        # run a saved profile unattended
```

### Zip — options

| Option | Effect |
|--------|--------|
| `TARGET` | Folder whose immediate subfolders are zipped |
| `DEST` | Where `.zip` files are written (default: current directory) |
| `-r`, `--remove` | Remove each source folder after a **successful** zip (asks to confirm) |

`fm.py zip-log TARGET` — log one `.zip`/`.tar` archive (or every archive in a
folder, top level only) to the CB9Inventory database. No flags; requires the
`logZip` section of `fmConfig.json`.

### Cleanup — `what` and flags

| What | Positional arg | Behavior |
|------|----------------|----------|
| `junk` | `ROOT` (required) | Find every `.DS_Store` / `desktop.ini` under ROOT (hidden folders included) and delete on confirm |
| `logs` | `FOLDER` (default `~/Documents/log`) | Purge entries older than `--days` from every `.log` file; `.bak` backup before each rewrite |

| Flag | Effect |
|------|--------|
| `--days N` | `logs` only: days of entries to keep (default **90**) |
| `--delete` | Actually delete / purge (otherwise dry run) |
| `--yes` | Skip the confirmation prompt (only meaningful with `--delete`) |

```bash
fm.py cleanup junk ~/Documents                    # dry run — list the junk files
fm.py cleanup junk ~/Documents --delete           # delete after confirming
fm.py cleanup logs                                # dry run — purge/keep table, 90 days
fm.py cleanup logs ~/Documents/log --days 30 --delete --yes   # purge unattended
```

---

## Worked Examples

**Compare two backup copies of a project (missing files + size drift, recursive):**

```bash
fm.py compare-contents ~/Documents/sites/mysite /Volumes/Backup/mysite --recursive --by both
```

**Compare two config files side by side:**

```bash
fm.py compare-2files ~/app/config.old.json ~/app/config.new.json
```

**See which folders in a media library are biggest:**

```bash
fm.py sizes /Volumes/Media/2026 --sort size
```

Expected output (abridged):

```
        Size               Bytes      Files  Folder
  ----------  ------------------  ---------  --------------------
      12.4 GB      13,314,905,600      1,204  04_ContentHouse
       3.1 GB       3,328,599,040        512  02_Interviews
  ----------  ------------------  ---------  --------------------
      15.5 GB      16,643,504,640      1,716  TOTAL (2 folders)
```

**Find everything over 500 MB in Movies:**

```bash
fm.py find over 500 ~/Movies
```

**Find `.mov` files under 5 MB (combined criteria):**

```bash
fm.py find-files ~/Movies --ext mov --under 5
```

**Preview, then clean macOS junk files:**

```bash
fm.py remove name ".DS_Store" ~/Documents            # dry run — see what matches
fm.py remove name ".DS_Store" ~/Documents --delete   # delete after confirming
```

**Remove content‑duplicate files across two drives (keep the first copy):**

```bash
fm.py remove dup-hash /Volumes/DriveA/Media /Volumes/DriveB/Import          # preview
fm.py remove dup-hash /Volumes/DriveA/Media /Volumes/DriveB/Import --delete # delete
```

**Keep a backup drive current (push new/updated files, newest wins):**

```bash
fm.py sync ~/Media /Volumes/CB9-2t/MediaBackup             # dry run — review the preview
fm.py sync ~/Media /Volumes/CB9-2t/MediaBackup --copy      # copy (confirms first)
```

**Watch a hot folder for new PDFs while you work:**

```bash
fm.py monitor ~/Downloads --ext pdf            # each arrival prints + logs; Ctrl-C stops
```

**Rename a setting across a whole PHP site (preview, then apply with backups):**

```bash
fm.py find-replace ~/Documents/sites/mysite "oldFunctionName" "newFunctionName" --ext php
fm.py find-replace ~/Documents/sites/mysite "oldFunctionName" "newFunctionName" --ext php --apply --bak
```

**Monthly housekeeping — junk files gone, logs trimmed to 90 days:**

```bash
fm.py cleanup junk ~ --delete                  # confirm, then delete every .DS_Store/desktop.ini
fm.py cleanup logs --delete                    # confirm, then purge old fm/claude/etc. log entries
```

**Back up, then eject every external drive (end‑of‑day):**

```bash
fm.py sync ~/Media /Volumes/CB9-2t/MediaBackup --copy --yes
fm.py eject --yes
```

**Zip every subfolder of an import staging area into a temp folder:**

```bash
fm.py zip-subfolders /Volumes/Media/Import /Volumes/BigDrive/ZipTemp
fm.py zip-subfolders -r /Volumes/Media/Import /Volumes/BigDrive/ZipTemp   # + remove sources
```

**Inspect a zip without extracting it:**

```bash
fm.py zip-view /Volumes/BigDrive/ZipTemp/betty.zip
fm.py zip-view /Volumes/BigDrive/ZipTemp        # browse & pick a zip from the folder
```

---

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `ModuleNotFoundError: No module named 'CB9Lib'` | CB9Lib is not at `~/Documents/script/CB9Lib`. Fix the location or edit the `sys.path.insert(...)` line in `fm.py`. |
| Colors show as `\033[...]` gibberish | Terminal doesn’t support ANSI, or output is being captured. Run in a normal terminal. |
| `zip: command not found` (Zip SubFolders) | Install `zip` (`brew install zip` / `apt install zip`). |
| No completion sound | Optional. Add `audio/success.mp3` + `audio/failure.wav` beside `fm.py`, or configure `~/userProfile.json` (see [Configuration](#configuration)). |
| `EOFError` when piping input | The interactive menu needs a terminal. For scripting/piping, use the **CLI subcommands** instead. |
| A removal “did nothing” | That’s the safety default — it was a **dry run**. Add `--delete` (CLI) or confirm **`y`** (menu). |
| “Not a directory” when pasting a path with spaces | Fixed in v1.2 — paths wrapped in `'…'` / `"…"` quotes or drag‑and‑dropped (backslash‑escaped spaces) are now cleaned automatically. You can paste the path any of those ways. |

---

## License / Copyright

---
**Project:** File Management
**Script:** `fm.py` — File Manager
**Version:** 1.29
**Maintainer / Owner:** Cloud Box 9 Inc.
**Last Updated:** Jul 14, 2026

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
