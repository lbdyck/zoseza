# zoseza
```
zeza.py (Python eza clone for z/OS)

Description:
  A feature-rich Python clone of the `eza` (modern ls) utility specifically tailored 
  for IBM z/OS UNIX System Services (USS). It provides robust colorized terminal output, 
  native EBCDIC/ASCII tag support (chtag), extended attribute inspection (extattr), 
  zFS dataset resolution, and Git status integration. 

  It features both a standard CLI format and an interactive full-screen Text User Interface 
  (TUI) for navigating, sorting, filtering, editing, and managing files on the mainframe.

CLI Options:
  paths                 Files or directories to list (default: current directory).
  -a, --all             Show hidden files (starting with .).
  -l, --long            Display extended metadata (perms, links, owner, group, size, time).
  -g, --git             Show Git status badges and the current branch.
  -t, --time            Sort by modification time (newest first).
  -i, --icons           Display Nerd Font icons next to filenames.
  -b, --blocks          Display file sizes in 512-byte blocks instead of bytes.
  -J, --json FILE       Export directory listing data to a specified JSON file.
  -e, --ext EXT         Filter by comma-separated file extensions (e.g., txt,rex,c).
  -R, --regex PATTERN   Filter files matching a regular expression.
  -T, --tags            Display z/OS file tags (state, codeset).
  -x, --extattr         Display z/OS extended attributes (APF, program control, etc.).
  --tree                Display output in a recursive tree topology.
  -d, --directory       List directories themselves, not their contents.
  -S, --sort-size       Sort files by size (largest first).
  -r, --reverse         Reverse the current sort order.
  -1, --oneline         Display one entry per line.
  -D, --dsn             Show underlying zFS dataset names for directories and symlinks.
  --tui                 Launch the interactive fullscreen Text User Interface.

TUI Hotkeys:
  UP/DOWN : Navigate              s/t/n/r : Sort (Size/Time/Name/Reverse)
  ENTER   : Open Dir/File         f or /  : Filter by string
  ESC     : Go up one dir         c       : Clear filter
  e       : Edit file             o       : Open settings (colors/editor)
  D/R/C   : Delete/Rename/Copy    F1      : Show help tutorial
  q       : Quit

Change History:
  2026-11-16: Fixed -D (dataset) display for files and implemented zFS mount point caching.
  2026-11-16: Added dynamic column headers (CLI/TUI) and TUI horizontal separator.
  2026-11-16: Added TUI support for shell globbing (e.g., zeza.py --tui z*).
  2026-11-16: Removed '.' from lists; explicitly pinned '..' to the top of all sorts.
  2026-11-16: Fixed column alignment drift for tagless directories.
  2026-11-16: Added universal F1 Help overlays; added MIT License SPDX identifier.
  2026-11-16: Added interactive file ops (D/R/C) and TUI settings (~/.pyeza.json).
  2026-11-15: Initial TUI integration with colorized views and basic navigation.
  2026-11-14: Initial CLI layout, z/OS specific integrations, and sorting capabilities.
```

Help for --tui (via F1):

<img width="864" height="723" alt="image" src="https://github.com/user-attachments/assets/32c76f40-7a20-41f9-9888-d0a60f8f7e2b" />

When `F`` is used in the `o` (settings:

<img width="862" height="238" alt="image" src="https://github.com/user-attachments/assets/64c3a501-f834-4800-a3dd-752ac279a235" />

Google Gemini was used for this project
