# zoseza

**A feature-rich Python clone of the `eza` (modern ls) utility specifically tailored for IBM z/OS UNIX System Services (USS).**

> **Note on Naming:** This repository and the default script are named `zoseza`. If you prefer a shorter command, you are welcome to rename the script or set up a shell alias (e.g., `alias zeza='/path/to/zoseza.py'`).

## Description

`zoseza` provides robust colorized terminal output, native EBCDIC/ASCII tag support (`chtag`), extended attribute inspection (`extattr`), zFS dataset resolution, and Git status integration.

It features both a standard CLI format and an interactive full-screen Text User Interface (TUI) for navigating, sorting, filtering, customizing columns, inspecting, editing, modifying z/OS attributes (`chtag`, `extattr`, `chmod`), and managing files directly on the mainframe.

## Sample Output

Running `zoseza.py -laTgD` inside a z/OS USS Git repository (note how `-D` only prints the dataset on the first entry or when a file/directory crosses into a different zFS dataset):

```text
. [ZOWE.ZFS.USERS] on  main:
Permissions Ln User     Group     Size Modified     Git Tag Info      Name  [Dataset]
drwxr-xr-x  39 LBDYCK   ZOWEDEV   8.0K Nov 16 16:00 --                ..  [ZOWE.ZFS.USERS]
drwxr-xr-x   7 LBDYCK   ZOWEDEV   8.0K Nov 17 08:15 --                .git
-rw-r--r--   1 LBDYCK   ZOWEDEV   1.0K Nov 16 16:00 --  t UTF-8       LICENSE
-rw-r--r--   1 LBDYCK   ZOWEDEV   7.4K Nov 18 13:15  M  t ISO8859-1   README.md
-rw-r--r--   1 LBDYCK   ZOWEDEV   6.1K Nov 18 13:15 --  t ISO8859-1   zoseza.1
-rwxr-xr-x   1 LBDYCK   ZOWEDEV  64.8K Nov 18 13:15 --  t ISO8859-1   zoseza.py
```

## Prerequisites

* **Base z/OS USS Utilities:** Uses standard built-in z/OS commands (`ls`, `df`, `extattr`, `chtag`, `getfacl`) for metadata, file tagging, ACLs, and zFS mount resolution.
* **Python 3:** Requires `python3` (such as IBM Open Enterprise SDK for Python or the [zopen community](https://zopen.community/) Python port).
* **Optional Dependencies:**
  * `git` (via zopen community or Rocket) for `-g` / `--git` repository status and branch display.
  * `zotman` / `man-db` (via zopen community) for viewing and indexing the `ISO8859-1` `zoseza.1` manpage natively.
  * A [Nerd Font](https://www.nerdfonts.com/) installed on your local terminal emulator (e.g., Windows Terminal, iTerm2, WezTerm) if using `-i` / `--icons`.

## Usage & Recommended Aliases

You can run the utility directly from the shell or with Python 3:

```bash
./zoseza.py [OPTIONS] [PATHS...]
```

For daily use, add `zoseza.py` to your `PATH` (or symlink it) and add these convenient shortcuts to your `~/.bashrc` or `~/.zshrc`:

```bash
# Base command aliases
alias zoseza='/path/to/zoseza/zoseza.py'
alias zeza='/path/to/zoseza/zoseza.py'

# Common workflow shortcuts
alias ll='zoseza -l --group-directories-first' # Long listing with dirs first
alias la='zoseza -la'                          # Long listing including hidden files
alias lt='zoseza -laT'                         # Long listing with z/OS file tags
alias lg='zoseza -laTg'                        # Long listing with file tags and Git status
alias lzd='zoseza -lD'                         # Show underlying zFS datasets when they change
alias lx='zoseza -lx'                          # Show z/OS extended attributes (APF, ProgCtl)
alias ltree='zoseza --tree -L 2'               # Recursive tree view (2 levels deep)
alias ztui='zoseza --tui'                      # Launch interactive full-screen TUI
```

## Manpage Installation (`zotman` / `man-db`)

The included `zoseza.1` manpage is maintained in ASCII (`ISO8859-1`) and is designed to work seamlessly with `zotman` (`man-db`) from the [zopen community](https://zopen.community/) project.

To preview the manpage directly from the repository directory:

```bash
zotman ./zoseza.1
```

To install the manpage system-wide (or into your zopen environment) so `man zoseza` works from anywhere:

1. **Copy `zoseza.1` to your `man1` directory** (typically `$ZOPEN_ROOTFS/usr/local/share/man/man1/` or `/usr/local/share/man/man1/`, or a directory listed in your `$MANPATH`):
   ```bash
   mkdir -p "${ZOPEN_ROOTFS}/usr/local/share/man/man1"
   cp zoseza.1 "${ZOPEN_ROOTFS}/usr/local/share/man/man1/zoseza.1"
   chtag -tc ISO8859-1 "${ZOPEN_ROOTFS}/usr/local/share/man/man1/zoseza.1"
   ```
2. **Update the `man-db` index** (do not forget this step so `man` and `apropos` can locate the new page):
   ```bash
   mandb
   ```

Once `mandb` finishes, you can view the documentation anytime by running `man zoseza` (or `zotman zoseza`).

## CLI Options

| Flag | Description |
| :--- | :--- |
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
| `-L`, `--level DEPTH` | Limit the recursion depth of the `--tree` display. |
| `--group-directories-first` | List directories before regular files across any sort order. |
| `-d`, `--directory` | List directories themselves, not their contents. |
| `-S`, `--sort-size` | Sort files by size (largest first). |
| `-r`, `--reverse` | Reverse the current sort order. |
| `-1`, `--oneline` | Display one entry per line. |
| `-D`, `--dsn` | Show underlying zFS dataset names (displayed on the first entry and whenever the dataset changes). |
| `--color WHEN` | When to use terminal colors: `auto`, `always`, `never` (default: `auto`). |
| `--no-color` | Disable all terminal colors (alias for `--color=never`). Also respects the `NO_COLOR` environment variable. |
| `--tui` | Launch the interactive fullscreen Text User Interface. |
| `-v`, `--version` | Show program's version number and exit. |
| `-h`, `--help` | Show the CLI help message and exit. |

## TUI Hotkeys (Single-Column Reference)

* **`UP / DOWN`** : Navigate cursor up or down line by line
* **`PgUp / PgDn`** : Scroll the directory listing or file viewer by page
* **`Home / End`** : Jump to the first or last entry in the directory or file viewer
* **`ENTER`** : Open directory or view file in the built-in pager (supports live ASCII, EBCDIC `IBM-1047`, and Hex dump modes)
* **`ESC`** : Go up one directory or close active modal/view (25ms fast response)
* **`.`** : Toggle display of hidden dotfiles (`-a`)
* **`d`** : Toggle grouping directories before regular files (`[Dirs1st]`)
* **`i`** : Inspect full file metadata (permissions, ACLs, `chtag`, `extattr`, zFS dataset/mount, timestamps, and Git status)
* **`e`** : Edit selected file in configured editor (`$EDITOR` or `vi`)
* **`m`** : Create a new directory (`mkdir` popup dialog)
* **`A`** : Create a new empty file (popup dialog)
* **`p`** : Change file permissions (`chmod` octal popup dialog)
* **`u`** : Change z/OS file tag (`chtag` popup menu for `ISO8859-1`, `IBM-1047`, `UTF-8`, custom codeset, binary, mixed, or untagged)
* **`x`** : Modify z/OS extended attributes (`extattr` checklist popup for `+a`/`-a`, `+p`/`-p`, `+s`/`-s`, `+l`/`-l`)
* **`C`** : Copy selected file or directory (opens centered popup input modal)
* **`R`** : Rename selected file or directory (opens centered popup input modal)
* **`D`** : Delete selected file or directory (opens centered confirmation popup modal)
* **`s`** : Sort by file size (largest first)
* **`t`** : Sort by modification time (`mtime`)
* **`a`** : Sort by last access time (`atime`)
* **`z`** : Sort by status change time (`ctime`)
* **`n`** : Sort by filename
* **`r`** : Reverse current sort order
* **`f`** or **`/`** : Filter files in the current directory by substring
* **`c`** : Clear active filter (or cycle `AUTO` -> `ISO8859-1` -> `IBM-1047` -> `HEX` inside the File Viewer)
* **`h`** : Toggle side-by-side Hex / ASCII / EBCDIC (`IBM-1047`) dump inside the File Viewer
* **`v`** : Open interactive **TUI Columns Menu** to add or remove any column (`SPACE`/`ENTER` or shortcut key to toggle, `a` for all, `d` for default, and `s` to save when `Save Columns` is enabled in `o` Settings)
* **`I`** : Toggle Inode column visibility
* **`O`** : Toggle Octal permissions column
* **`N`** : Toggle Numeric UID and GID display
* **`G`** : Toggle Git status column
* **`T`** : Toggle z/OS File Tags (`chtag`) column
* **`X`** : Toggle z/OS Extended Attributes (`[apsl]`) column
* **`M`** : Toggle zFS Dataset column
* **`B`** : Toggle 512-byte Blocks size display
* **`W`** : Toggle Nerd Font Icons display
* **`o`** : Open colorized Settings menu (configure default editor, toggle `Save Columns` ON/OFF, and preview/save colors)
* **`F1`** : Show colorized Help tutorial
* **`q`** : Quit current view or exit TUI

## Configuration & Environment Variables

When you save settings inside the TUI (by pressing `o` then `s`), preferences are stored in `~/.pyeza.json` and confirmed via a popup message. By default, `"save_columns"` is set to `false` (`< OFF >`), meaning column changes in the `v` Columns Menu apply only to the current TUI session. If you toggle `Save Columns` to `< ON >` in the `o` Settings menu, pressing `s` inside the `v` Columns Menu will persist your active column layout to `~/.pyeza.json`:

```json
{
  "editor": "vim",
  "save_columns": false,
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

```python
#!/usr/bin/env python3
"exec" "python3" "$0" "$@"
```

If you clone or transfer `zoseza.py` to a new z/OS system, ensure its file tag and execute permissions are set properly:

```bash
chtag -tc ISO8859-1 zoseza.py zoseza.1 README.md
chmod 755 zoseza.py
```

## Change History

* **2026-11-18**: Added `Save Columns` option (`save_columns`, default: `OFF`) in the `o` Settings menu to optionally enable `s: Save` in the `v` Columns Menu; fixed line 2 background bleed in TUI popups using `curses.ACS_HLINE`; added interactive TUI modals for `chtag` (`u`), `chmod` (`p`), `extattr` (`x`), `mkdir` (`m`), and new file creation (`A`); added live `ISO8859-1`/`IBM-1047`/Hex dump switching (`c`, `h`) in the TUI file viewer; added `PgUp`/`PgDn`/`Home`/`End`, `.` dotfile toggle, and `d` group-directories-first in TUI; added CLI `--group-directories-first` and `-L`/`--level` tree depth options (v1.7.0).
* **2026-11-18**: Fixed `C` Copy hotkey collision in TUI (moved `ctime` sort to `z`), reduced `ESC` key delay to 25ms for instant response, added popup confirmation when saving TUI Settings and after Copy/Rename/Delete, updated `-D` to display the zFS dataset only when it changes, and formatted TUI hotkeys in a single-column layout across code, README, and manpage (v1.6.0).
* **2026-11-18**: Added interactive TUI Columns Menu (`v`) and direct hotkeys (`G`, `T`, `X`, `M`, `B`, `W`, `I`, `O`, `N`) to dynamically add or remove any display column, plus colorized the TUI Settings menu (`o`) with live color previews (v1.5.0).
* **2026-11-18**: Colorized TUI `F1` help tutorials and added centered, bordered popup modal dialogs for Copy (`C`), Rename (`R`), and Delete (`D`) operations (v1.4.0).
* **2026-11-17**: Added `zoseza.1` manpage documentation with `zotman` (`man-db`) installation and `mandb` indexing instructions.
* **2026-11-17**: Added `i` hotkey in TUI to display a scrollable full-screen inspector with complete file metadata, ACLs, `chtag` info, `extattr` flags, zFS dataset/mount point, timestamps, and Git status (v1.3.0).
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