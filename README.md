# zoseza

**A feature-rich Python clone of the `eza` (modern ls) utility specifically tailored for IBM z/OS UNIX System Services (USS).**

> **Note on Naming:** This repository and the default script are named `zoseza`. If you prefer a shorter command, you are welcome to rename the script or set up a shell alias (e.g., `alias zeza='/path/to/zoseza.py'`).

## Description

`zoseza` provides robust colorized terminal output, native EBCDIC/ASCII tag support (`chtag`), extended attribute inspection (`extattr`), zFS dataset resolution, and Git status integration.

It features both a standard CLI format and an interactive full-screen Text User Interface (TUI) for navigating, sorting, filtering, inspecting, editing, and managing files directly on the mainframe.

## Sample Output

Running `zoseza.py -laTgD` inside a z/OS USS Git repository:

```
. [ZOWE.ZFS.USERS] on  main:
Permissions Ln User     Group     Size Modified     Git Tag Info      Name  [Dataset]
drwxr-xr-x  39 LBDYCK   ZOWEDEV   8.0K Nov 16 16:00 --                ..  [ZOWE.ZFS.USERS]
drwxr-xr-x   7 LBDYCK   ZOWEDEV   8.0K Nov 17 08:15 --                .git  [ZOWE.ZFS.USERS]
-rw-r--r--   1 LBDYCK   ZOWEDEV   1.0K Nov 16 16:00 --  t UTF-8       LICENSE  [ZOWE.ZFS.USERS]
-rw-r--r--   1 LBDYCK   ZOWEDEV   6.2K Nov 17 09:10  M  t ISO8859-1   README.md  [ZOWE.ZFS.USERS]
-rwxr-xr-x   1 LBDYCK   ZOWEDEV  46.4K Nov 17 09:05 --  t ISO8859-1   zoseza.py  [ZOWE.ZFS.USERS]
```

## Prerequisites

* **Base z/OS USS Utilities:** Uses standard built-in z/OS commands (`ls`, `df`, `extattr`, `chtag`, `getfacl`) for metadata, file tagging, ACLs, and zFS mount resolution.
* **Python 3:** Requires `python3` (such as IBM Open Enterprise SDK for Python or the [zopen community](https://zopen.community/) Python port).
* **Optional Dependencies:**
  * `git` (via zopen community or Rocket) for `-g` / `--git` repository status and branch display.
  * A [Nerd Font](https://www.nerdfonts.com/) installed on your local terminal emulator (e.g., Windows Terminal, iTerm2, WezTerm) if using `-i` / `--icons`.

## Usage & Recommended Aliases

You can run the utility directly from the shell or with Python 3:

```
./zoseza.py [OPTIONS] [PATHS...]
```

For daily use, add `zoseza.py` to your `PATH` (or symlink it) and add these convenient shortcuts to your `~/.bashrc` or `~/.zshrc`:

```
# Base command aliases
alias zoseza='/path/to/zoseza/zoseza.py'
alias zeza='/path/to/zoseza/zoseza.py'

# Common workflow shortcuts
alias ll='zoseza -l'            # Standard long listing
alias la='zoseza -la'           # Long listing including hidden files
alias lt='zoseza -laT'          # Long listing with z/OS file tags
alias lg='zoseza -laTg'         # Long listing with file tags and Git status
alias lzd='zoseza -lD'          # Show underlying zFS datasets
alias lx='zoseza -lx'           # Show z/OS extended attributes (APF, ProgCtl)
alias ltree='zoseza --tree'     # Recursive tree view
alias ztui='zoseza --tui'       # Launch interactive full-screen TUI
```

## CLI Options

| Flag | Description | 
| ----- | ----- | 
| `paths` | Files or directories to list (default: current directory). | 
| `-a`, `--all` | Show hidden files (starting with `.`). | 
| `-l`, `--long` | Display extended metadata (perms, links, owner, group, size, time). | 
| `-g`, `--git` | Show Git status badges and the current branch. | 
| `-t`, `--time` | Sort by modification time (newest first). | 
| `-u`, `--access` | Sort/display by last access time (atime). | 
| `-c`, `--ctime` | Sort/display by status change time (ctime). | 
| `-i`, `--icons` | Display Nerd Font icons next to filenames. | 
| `--inode` | Display the file serial number (inode). | 
| `-O`, `--octal` | Display file permissions in octal format. | 
| `-n`, `--numeric` | List numeric UIDs and GIDs instead of names. | 
| `-b`, `--blocks` | Display file sizes in 512-byte blocks instead of bytes. | 
| `-J`, `--json FILE` | Export directory listing data to a specified JSON file. | 
| `-e`, `--ext EXT` | Filter by comma-separated file extensions (e.g., txt,rex,c). | 
| `-R`, `--regex PATTERN` | Filter files matching a regular expression. | 
| `-T`, `--tags` | Display z/OS file tags (state, codeset). | 
| `-x`, `--extattr` | Display z/OS extended attributes (APF, program control, etc.). | 
| `--tree` | Display output in a recursive tree topology. | 
| `-d`, `--directory` | List directories themselves, not their contents. | 
| `-S`, `--sort-size` | Sort files by size (largest first). | 
| `-r`, `--reverse` | Reverse the current sort order. | 
| `-1`, `--oneline` | Display one entry per line. | 
| `-D`, `--dsn` | Show underlying zFS dataset names for directories and symlinks. | 
| `--color WHEN` | When to use terminal colors: `auto`, `always`, `never` (default: `auto`). | 
| `--no-color` | Disable all terminal colors (alias for `--color=never`). Also respects the `NO_COLOR` environment variable. | 
| `--tui` | Launch the interactive fullscreen Text User Interface. | 
| `-v`, `--version` | Show program's version number and exit. | 
| `-h`, `--help` | Show the CLI help message and exit. | 

## TUI Hotkeys

**Navigation & System**

* **`UP/DOWN`** : Navigate
* **`ENTER`** : Open Dir/File
* **`ESC`** : Go up one dir
* **`o`** : Open settings (colors/editor)
* **`F1`** : Show help tutorial
* **`q`** : Quit

**Sorting & Filtering**

* **`s/t/a/C/n/r`** : Sort (Size / MTime / ATime / CTime / Name / Reverse)
* **`f`** or **`/`** : Filter by string
* **`c`** : Clear filter

**View Toggles**

* **`I`** : Toggle Inode visibility
* **`O`** : Toggle Octal permissions
* **`N`** : Toggle Numeric UIDs/GIDs

**File Operations & Inspection**

* **`i`** : Inspect full file metadata (permissions, ACLs, `chtag`, `extattr`, zFS dataset/mount, timestamps, and Git status)
* **`e`** : Edit file
* **`D/R/C`** : Delete / Rename / Copy

## Configuration & Environment Variables

When you save settings inside the TUI (by pressing `o` then `s`), preferences are stored in `~/.pyeza.json`. You can also create or edit this file manually:

```
{
  "editor": "vim",
  "color_dir": 4,
  "color_exe": 2,
  "color_sym": 6,
  "color_def": 7
}
```

*(Color codes follow standard curses/ANSI indices: `0`=Black, `1`=Red, `2`=Green, `3`=Yellow, `4`=Blue, `5`=Magenta, `6`=Cyan, `7`=White).*

**Environment Variables:**

* `EDITOR`: Default text editor for the TUI `e` hotkey if not overridden in `~/.pyeza.json` (defaults to `vi`).
* `LS_COLORS`: Standard UNIX color definitions (`di`, `ex`, `ln`, `fi`) are automatically respected in CLI output.
* `NO_COLOR`: If set in your environment, disables ANSI colors by default (per [no-color.org](https://no-color.org/)).

## z/OS USS Encoding & Polyglot Header Note

On z/OS USS, ASCII tools like zopen `vim` and `git` expect source files to be encoded and tagged as `ISO8859-1` or `UTF-8`, whereas the z/OS kernel requires `IBM-1047` (EBCDIC) to parse `#!` shebang lines during direct execution.

To allow `zoseza.py` to remain in `ISO8859-1` (so you can edit it cleanly in `vim`) while still executing directly from your shell (`./zoseza.py`), line 2 of the script uses a POSIX shell/Python polyglot header:

```
#!/usr/bin/env python3
"exec" "python3" "$0" "$@"
```

If you clone or transfer `zoseza.py` to a new z/OS system, ensure its file tag and execute permissions are set properly:

```
chtag -tc ISO8859-1 zoseza.py
chmod 755 zoseza.py
```

## Change History

* **2026-11-17**: Added `i` hotkey in TUI to display a scrollable full-screen inspector with complete file metadata, ACLs, `chtag` info, `extattr` flags, zFS dataset/mount point, timestamps, and Git status.
* **2026-11-17**: Added `-v` / `--version` flag and descriptive `--help` strings for all CLI options.
* **2026-11-17**: Added `--color` (`auto`, `always`, `never`), `--no-color`, and `NO_COLOR` environment variable support.
* **2026-11-16**: Added polyglot shell/Python `exec` header for direct execution while maintaining ASCII `vim` compatibility.
* **2026-11-16**: Streamlined documentation to focus on direct execution and shell aliases.
* **2026-11-16**: Restored missing `get_git_branch` function.
* **2026-11-16**: Added standard UNIX ls extensions: `--inode`, `-O` (octal), `-n` (numeric IDs).
* **2026-11-16**: Added alternate timestamp sorting: `-u` (access time) and `-c` (change time).
* **2026-11-16**: Implemented dynamic ACL (`+`) detection by parsing background `ls` output.
* **2026-11-16**: Added TUI runtime toggles for Inode (`I`), Octal (`O`), and Numeric (`N`) views.
* **2026-11-16**: Added clean KeyboardInterrupt exit to suppress Ctrl+C tracebacks.
* **2026-11-16**: Fixed `-D` (dataset) display for files and implemented zFS mount point caching.
* **2026-11-16**: Added dynamic column headers (CLI/TUI) and TUI horizontal separator.
* **2026-11-16**: Added TUI support for shell globbing (e.g., `zoseza --tui z*`).
* **2026-11-16**: Removed `.` from lists; explicitly pinned `..` to the top of all sorts.
* **2026-11-15**: Initial TUI integration with colorized views and basic navigation.
* **2026-11-14**: Initial CLI layout, z/OS specific integrations, and sorting capabilities.
