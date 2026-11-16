# zoseza

**A feature-rich Python clone of the eza (modern ls) utility specifically tailored for IBM z/OS UNIX System Services (USS).**

Note on Naming: This repository and the default script are named zoseza. If you prefer a shorter command, you are welcome to rename the executable to zeza after installation, or simply set up a shell alias (e.g., alias zeza='zoseza'). 

## Description
It provides robust colorized terminal output, native EBCDIC/ASCII tag support (chtag), extended attribute inspection (extattr), zFS dataset resolution, and Git status integration. 

It features both a standard CLI format and an interactive full-screen Text User Interface (TUI) for navigating, sorting, filtering, editing, and managing files on the mainframe.

## Installation

The repository includes an install.sh script that automatically copies the executable and the manual page to the correct directories.

### 1. System-Wide Installation (Requires elevated privileges)
This will install the script to /usr/local/bin and the manpage to /usr/local/man/man1.
git clone github_com/lbdyck/zoseza.git
cd zoseza
chmod +x install.sh
./install.sh

### 2. Personal Installation (No special privileges required)
To install the tool into your personal home directory (~/bin and ~/man/man1), override the installation prefix:
git clone github_com/lbdyck/zoseza.git
cd zoseza
chmod +x install.sh
PREFIX=$HOME ./install.sh

### 3. Update Your Environment
Ensure your shell knows where to find the installed executable and manpage. Add the following to your ~/.profile, ~/.bashrc, or ~/.zshrc:
# If installed system-wide:
export PATH="/usr/local/bin:$PATH"
export MANPATH="/usr/local/man:$MANPATH"

# If installed personally:
export PATH="$HOME/bin:$PATH"
export MANPATH="$HOME/man:$MANPATH"

## CLI Options

| Flag | Description |
| :--- | :--- |
| paths | Files or directories to list (default: current directory). |
| -a, --all | Show hidden files (starting with .). |
| -l, --long | Display extended metadata (perms, links, owner, group, size, time). |
| -g, --git | Show Git status badges and the current branch. |
| -t, --time | Sort by modification time (newest first). |
| -u, --access | Sort/display by last access time (atime). |
| -c, --ctime | Sort/display by status change time (ctime). |
| -i, --icons | Display Nerd Font icons next to filenames. |
| --inode | Display the file serial number (inode). |
| -O, --octal | Display file permissions in octal format. |
| -n, --numeric | List numeric UIDs and GIDs instead of names. |
| -b, --blocks | Display file sizes in 512-byte blocks instead of bytes. |
| -J, --json FILE | Export directory listing data to a specified JSON file. |
| -e, --ext EXT | Filter by comma-separated file extensions (e.g., txt,rex,c). |
| -R, --regex PATTERN | Filter files matching a regular expression. |
| -T, --tags | Display z/OS file tags (state, codeset). |
| -x, --extattr | Display z/OS extended attributes (APF, program control, etc.). |
| --tree | Display output in a recursive tree topology. |
| -d, --directory | List directories themselves, not their contents. |
| -S, --sort-size | Sort files by size (largest first). |
| -r, --reverse | Reverse the current sort order. |
| -1, --oneline | Display one entry per line. |
| -D, --dsn | Show underlying zFS dataset names for directories and symlinks. |
| --tui | Launch the interactive fullscreen Text User Interface. |

## TUI Hotkeys

**Navigation & System**
* UP/DOWN : Navigate
* ENTER : Open Dir/File
* ESC : Go up one dir
* o : Open settings (colors/editor)
* F1 : Show help tutorial
* q : Quit

**Sorting & Filtering**
* s/t/a/C/n/r : Sort (Size / MTime / ATime / CTime / Name / Reverse)
* f or / : Filter by string
* c : Clear filter

**View Toggles (New)**
* I : Toggle Inode visibility
* O : Toggle Octal permissions
* N : Toggle Numeric UIDs/GIDs

**File Operations**
* e : Edit file
* D/R/C : Delete / Rename / Copy

## Change History
* 2026-11-16: Added standard UNIX ls extensions: --inode, -O (octal), -n (numeric IDs).
* 2026-11-16: Added alternate timestamp sorting: -u (access time) and -c (change time).
* 2026-11-16: Implemented dynamic ACL (+) detection by parsing background ls output.
* 2026-11-16: Added TUI runtime toggles for Inode (I), Octal (O), and Numeric (N) views.
* 2026-11-16: Added clean KeyboardInterrupt exit to suppress Ctrl+C tracebacks.
* 2026-11-16: Fixed -D (dataset) display for files and implemented zFS mount point caching.
* 2026-11-16: Added dynamic column headers (CLI/TUI) and TUI horizontal separator.
* 2026-11-16: Added TUI support for shell globbing (e.g., zeza.py --tui z*).
* 2026-11-16: Removed . from lists; explicitly pinned .. to the top of all sorts.
* 2026-11-16: Fixed column alignment drift for tagless directories.
* 2026-11-16: Added universal F1 Help overlays; added MIT License SPDX identifier.
* 2026-11-16: Added interactive file ops (D/R/C) and TUI settings (~/.pyeza.json).
* 2026-11-15: Initial TUI integration with colorized views and basic navigation.
* 2026-11-14: Initial CLI layout, z/OS specific integrations, and sorting capabilities.

