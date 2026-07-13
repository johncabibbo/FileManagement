# File Management (`fm.py`)

A single, unified command‑line tool for the everyday file‑management chores that
used to live in nine separate scripts. **File Management** gives you an interactive
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
11. [Full Option Reference](#full-option-reference)
12. [Worked Examples](#worked-examples)
13. [Troubleshooting](#troubleshooting)
14. [License / Copyright](#license--copyright)

---

## Overview

`fm.py` is a **CB9Lib**‑based Python program. Run it with **no arguments** to get
a full‑screen interactive menu:

```
Compare  →  Compare 2 Files (side by side), Compare Folder Contents
                (Recursive Y/N · By Name / Size / Both)
Display  →  Folder Sizes
Find     →  Find Files (name · ext · size over/under, combined) · Find Folders
                · Find Duplicates by Filename · Find Missing by Filename
                · Find Missing by Filename & Size (all show a size table per folder)
Remove   →  duplicates (by name / by hash) · by file name · by folder name
Zip      →  View Zip · Zip SubFolders
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

`fm.py` needs **no config file** — folders and options are supplied
interactively or as CLI arguments. There are two configurable behaviors:

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
project name **`File Management`**:

```json
{
  "projectPreferences": [
    {
      "projectName": "File Management",
      "successAudio": "~/Documents/sounds/done.mp3",
      "failureAudio": "~/Documents/sounds/error.wav"
    }
  ]
}
```

Lookup is safe: if the profile is missing, the project has no entry, or the file
does not exist, `fm.py` silently falls back to the bundled defaults (and if those
are missing too, it simply plays nothing).

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
| 2 | **Display** | List subfolder sizes |
| 3 | **Find** | Locate folders/files by name, extension, or size; find duplicate or missing filenames |
| 4 | **Remove** | Delete folders, files, or duplicates (dry‑run first) |
| 5 | **Zip** | Zip each subfolder, or view a zip’s contents |
| Q | **Quit** | Exit with the standard CB9 exit screen |

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

### 2 · Display (Folder Sizes)

1. Enter the folder to measure (defaults to the current directory).
2. Choose **Alphabetical** or **By Size (largest first)**.

Output columns (in order): **Folder** (always first), **Size (human‑readable)**,
**Bytes (comma‑formatted)**, **File Count** — with a **TOTAL** row.

### 3 · Find

The Find submenu has five options. All Find searches (and folder Compares)
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
  1 - /Volumes/DriveA/lostMedia
  2 - /Volumes/DriveA/UncategorizedImages

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

### 4 · Remove  *(dry‑run by default)*

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

### 5 · Zip

- **View Zip** — enter a **zip file** to list its contents, or a **folder** to
  pick from the zips inside it. Shows uncompressed/compressed sizes, per‑file
  compression ratio, modified date, and totals — without extracting.
- **Zip SubFolders** — enter a **target** folder (whose subfolders get zipped)
  and a **zip destination** (defaults to the current directory). You’ll be asked
  whether to **remove source folders after a successful zip**. `.DS_Store` and
  `desktop.ini` are cleaned first; name collisions become `name-2.zip`, etc.

---

## Usage — CLI Mode

Any subcommand runs non‑interactively and prints results without pausing. See
`fm.py --help` (or `fm.py <subcommand> --help`) for built‑in help.

```
fm.py compare-2files   FILE_A FILE_B
fm.py compare-contents A B [--recursive] [--by name|size|both]
fm.py sizes [FOLDER] [--sort alpha|size]
fm.py find folder PATTERN [ROOT]
fm.py find name   PATTERN [ROOT]
fm.py find ext    EXT     [ROOT]
fm.py find over   N       [ROOT]      # N = megabytes
fm.py find under  N       [ROOT]      # N = megabytes
fm.py find-files [ROOT] [--name PAT] [--ext E] [--over N] [--under N]   # combined AND
fm.py find-dups  FOLDER...            # duplicate filenames, size table per folder
fm.py find-missing A B [--in first|second|either] [--size]   # filenames in only one folder
                                                              # --size: match name AND size
fm.py remove folder      PATH        [--delete] [--yes]
fm.py remove name        PATTERN ROOT [--delete] [--yes]   # files by name
fm.py remove folder-name PATTERN ROOT [--delete] [--yes]   # folders by name
fm.py remove dup-name    FOLDER...    [--delete] [--yes]
fm.py remove dup-hash    FOLDER...    [--delete] [--yes]
fm.py zip-subfolders  TARGET [DEST] [-r|--remove]
fm.py zip-view [ZIP|FOLDER]
```

Default argument values:

| Subcommand | Argument | Default |
|------------|----------|---------|
| `compare-contents` | `--recursive` / `--by` | off (top level) / `both` |
| `sizes` | `FOLDER` / `--sort` | `.` (current dir) / `alpha` |
| `find *` | `ROOT` | `.` (current dir) |
| `zip-subfolders` | `DEST` | current directory |

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

> 💡 **Tip:** Run any removal once with no flags (or in the menu) to inspect the
> preview, then re‑run with `--delete` once you’re satisfied.

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

### Display — `--sort`

| Value | Meaning |
|-------|---------|
| `alpha` *(default)* | Alphabetical by folder name |
| `size` | Largest total size first |

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
fm.py find-dups /Volumes/DriveA/lostMedia /Volumes/DriveA/UncategorizedImages
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
fm.py find-missing /Volumes/DriveA/lostMedia /Volumes/DriveA/UncategorizedImages --in first
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

### Zip — options

| Option | Effect |
|--------|--------|
| `TARGET` | Folder whose immediate subfolders are zipped |
| `DEST` | Where `.zip` files are written (default: current directory) |
| `-r`, `--remove` | Remove each source folder after a **successful** zip (asks to confirm) |

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
**Script:** `fm.py` — File Management
**Version:** 1.22
**Maintainer / Owner:** Cloud Box 9 Inc.
**Last Updated:** Jul 13, 2026

Copyright © 2026 Cloud Box 9 Inc. All rights reserved.
