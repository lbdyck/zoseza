#!/usr/bin/env python3
"exec" "python3" "$0" "$@"
# SPDX-License-Identifier: MIT
"""
zoseza.py (Python eza clone for z/OS)

Description:
  A feature-rich Python clone of the eza (modern ls) utility specifically tailored 
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
  -u, --access          Sort/display by last access time (atime).
  -c, --ctime           Sort/display by status change time (ctime).
  -i, --icons           Display Nerd Font icons next to filenames.
  --inode               Display the file serial number (inode).
  -O, --octal           Display file permissions in octal format.
  -n, --numeric         List numeric UIDs and GIDs instead of names.
  -b, --blocks          Display file sizes in 512-byte blocks instead of bytes.
  -J, --json FILE       Export directory listing data to a specified JSON file.
  -e, --ext EXT         Filter by comma-separated file extensions (e.g., txt,rex,c).
  -R, --regex PATTERN   Filter files matching a regular expression.
  -T, --tags            Display z/OS file tags (state, codeset).
  -x, --extattr         Display z/OS extended attributes (APF, program control, etc.).
  --tree                Display output in a recursive tree topology.
  -L, --level DEPTH     Limit the recursion depth of the tree display.
  --group-directories-first
                        List directories before regular files.
  -d, --directory       List directories themselves, not their contents.
  -S, --sort-size       Sort files by size (largest first).
  -r, --reverse         Reverse the current sort order.
  -1, --oneline         Display one entry per line.
  -D, --dsn             Show underlying zFS dataset names for directories and symlinks.
  --color WHEN          When to use terminal colors: auto, always, never (default: auto).
  --no-color            Disable all terminal colors (alias for --color=never).
  -v, --version         Show program's version number and exit.
  --tui                 Launch the interactive fullscreen Text User Interface.

TUI Hotkeys:
  UP/DOWN       : Navigate cursor up or down
  PgUp/PgDn     : Scroll directory list by page
  Home/End      : Jump to first or last entry
  ENTER         : Open directory or view file (with ASCII/EBCDIC/Hex toggle)
  ESC           : Go up one directory or close sub-view
  .             : Toggle hidden dotfiles (-a)
  d             : Toggle grouping directories first
  i             : Inspect full file details and z/OS metadata
  e             : Edit file in configured editor
  m             : Create new directory (mkdir popup)
  A             : Create new empty file (touch popup)
  p             : Change file permissions (chmod popup)
  u             : Change z/OS file tag (chtag popup)
  x             : Modify z/OS extended attributes (extattr popup)
  C             : Copy file or directory (popup dialog)
  R             : Rename file or directory (popup dialog)
  D             : Delete file or directory (popup dialog)
  v             : Open interactive Columns Menu (add/remove columns)
  s             : Sort by file size
  t             : Sort by modification time (mtime)
  a             : Sort by access time (atime)
  z             : Sort by status change time (ctime)
  n             : Sort by filename
  r             : Reverse active sort order
  f or /        : Filter entries by substring
  c             : Clear active filter
  I / O / N     : Toggle Inode / Octal permissions / Numeric UID & GID
  G / T / X / M : Toggle Git / z/OS Tags / ExtAttr / zFS Dataset
  B / W         : Toggle 512B Blocks / Nerd Font Icons
  o             : Open Settings menu (colors and editor)
  F1            : Show colorized help tutorial
  q             : Quit current view or exit TUI

Change History:
  2026-11-18: Made saving TUI column preferences an explicit setting (default: OFF) in Settings ('o') and Columns Menu ('v').
  2026-11-18: Fixed residual background text bleed on line 2 of TUI popup dialogs using win.hline(ACS_HLINE).
  2026-11-18: Added TUI popups for chtag ('u'), chmod ('p'), extattr ('x'), mkdir ('m'), and new file ('A').
  2026-11-18: Added ASCII/EBCDIC (cp1047) and Hex dump toggles ('c', 'h') inside the TUI file viewer.
  2026-11-18: Added PgUp/PgDn/Home/End navigation, '.' hidden file toggle, and 'd' group-dirs-first in TUI.
  2026-11-18: Added CLI --group-directories-first and -L/--level tree depth limit.
  2026-11-18: Added success confirmation popups after Copy ('C'), Delete ('D'), and Rename ('R') in TUI.
  2026-11-18: Fixed 'C' (Copy) hotkey collision with CTime sort (moved CTime sort to 'z').
  2026-11-18: Set ESCDELAY=25ms for instant ESC key response in TUI.
  2026-11-18: Added confirmation popup when saving TUI settings and deduplicated -D dataset display.
  2026-11-18: Added interactive TUI Columns Menu ('v') and hotkeys to add or remove any display column.
  2026-11-18: Colorized TUI F1 help screens and added centered popup modals for Copy, Rename, and Delete.
  2026-11-17: Added 'i' hotkey in TUI to display comprehensive file metadata and z/OS attributes.
  2026-11-17: Added -v / --version option, --color (auto/always/never), and --no-color CLI options.
  2026-11-16: Restored missing get_git_branch function.
  2026-11-16: Added standard UNIX ls extensions: --inode, -O (octal), -n (numeric IDs).
  2026-11-16: Added alternate timestamp sorting: -u (access time) and -c (change time).
  2026-11-16: Implemented dynamic ACL (+) detection by parsing background ls output.
  2026-11-16: Added TUI runtime toggles for Inode (I), Octal (O), and Numeric (N) views.
  2026-11-16: Added clean KeyboardInterrupt exit to suppress Ctrl+C tracebacks.
  2026-11-16: Fixed -D (dataset) display for files and implemented zFS mount point caching.
  2026-11-16: Added dynamic column headers (CLI/TUI) and TUI horizontal separator.
  2026-11-16: Added TUI support for shell globbing (e.g., zoseza --tui z*).
  2026-11-16: Removed '.' from lists; explicitly pinned '..' to the top of all sorts.
  2026-11-15: Initial TUI integration with colorized views and basic navigation.
  2026-11-14: Initial CLI layout, z/OS specific integrations, and sorting capabilities.
"""
import os
import sys
import stat
import argparse
import subprocess
import shutil
import json
import re
import curses
from datetime import datetime

VERSION = "1.7.0"
CMD_NAME = os.path.basename(sys.argv[0])

# ANSI Color Codes
COLORS = {
    'reset': '\033[0m', 'dir': '\033[1;34m', 'exe': '\033[1;32m',       
    'symlink': '\033[1;36m', 'file': '\033[0m', 'size': '\033[1;32m',      
    'time': '\033[34m', 'perms': '\033[33m', 'user': '\033[33m',        
    'group': '\033[33m', 'git_clean': '\033[90m', 'git_mod': '\033[33m',     
    'git_add': '\033[32m', 'git_untracked': '\033[31m',
    'branch': '\033[36m', 'tree_line': '\033[90m', 'tags': '\033[35m',
    'dsn': '\033[1;35m', 'extattr': '\033[1;31m', 'inode': '\033[90m'
}

ICONS = {
    'dir': '\uf115', 'symlink': '\uf481', 'exe': '\uf489', 'py': '\U000f0320',
    'rex': '\U000f1064', 'rexx': '\U000f1064', 'sh': '\uf489', 'txt': '\uf15c',
    'md': '\uf48a', 'jcl': '\U000f09ee', 'c': '\ue61e', 'cpp': '\ue61d',
    'h': '\uf0fd', 'json': '\ue60b', 'xml': '\U000f05c0', 'csv': '\U000f0219',
    'zip': '\uf410', 'tar': '\uf410', 'gz': '\uf410', 'default': '\uf15b'
}

# ==============================================================================
# Configuration Management
# ==============================================================================
def load_config():
    default_config = {
        'editor': os.environ.get('EDITOR', 'vi'),
        'color_dir': curses.COLOR_BLUE,
        'color_exe': curses.COLOR_GREEN,
        'color_sym': curses.COLOR_CYAN,
        'color_def': curses.COLOR_WHITE,
        'save_columns': False
    }
    conf_path = os.path.expanduser('~/.pyeza.json')
    if os.path.exists(conf_path):
        try:
            with open(conf_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception: pass
    return default_config

def save_config(config):
    conf_path = os.path.expanduser('~/.pyeza.json')
    try:
        with open(conf_path, 'w') as f: json.dump(config, f, indent=2)
    except Exception: pass

def sync_ansi_colors(config):
    ansimap = {0:'30', 1:'31', 2:'32', 3:'33', 4:'34', 5:'35', 6:'36', 7:'37'}
    COLORS['dir'] = f"\033[1;{ansimap[config['color_dir']]}m"
    COLORS['exe'] = f"\033[1;{ansimap[config['color_exe']]}m"
    COLORS['symlink'] = f"\033[1;{ansimap[config['color_sym']]}m"
    COLORS['file'] = f"\033[{ansimap[config['color_def']]}m"

def apply_ls_colors():
    ls_colors = os.environ.get('LS_COLORS', '')
    if not ls_colors: return
    mapping = {'di': 'dir', 'ex': 'exe', 'ln': 'symlink', 'fi': 'file'}
    for part in ls_colors.split(':'):
        if '=' in part:
            key, val = part.split('=', 1)
            if key in mapping: COLORS[mapping[key]] = f'\033[{val}m'

def disable_ansi_colors():
    for k in COLORS:
        COLORS[k] = ''

# ==============================================================================
# Core File Logic
# ==============================================================================
def get_icon(filename, mode):
    if stat.S_ISDIR(mode): return ICONS['dir']
    if stat.S_ISLNK(mode): return ICONS['symlink']
    if mode & stat.S_IXUSR or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
        return ICONS['exe']
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ICONS.get(ext, ICONS['default'])

def get_owner_name(uid, gid, numeric=False):
    if numeric: return str(uid), str(gid)
    try:
        import pwd
        user = pwd.getpwuid(uid).pw_name
    except (ImportError, KeyError): user = str(uid)
    try:
        import grp
        group = grp.getgrgid(gid).gr_name
    except (ImportError, KeyError): group = str(gid)
    return user, group

def format_size(st, use_blocks=False):
    if use_blocks and hasattr(st, 'st_blocks'):
        size = st.st_blocks * 512.0
    else:
        size = float(st.st_size)
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if size < 1024.0:
            return f"{size:4.1f}{unit}" if unit != 'B' else f"{int(size):4}B"
        size /= 1024.0
    return f"{size:4.1f}P"

def get_color(mode):
    if stat.S_ISDIR(mode): return COLORS['dir']
    if stat.S_ISLNK(mode): return COLORS['symlink']
    if mode & stat.S_IXUSR or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
        return COLORS['exe']
    return COLORS['file']

def get_acls(target_dir):
    acls = {}
    try:
        res = subprocess.run(['ls', '-A', '-l'], cwd=target_dir, 
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for line in res.stdout.splitlines():
            if len(line) > 10 and line[0] in ('-', 'd', 'l', 'c', 'b', 'p', 's'):
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    perms = parts[0]
                    name = parts[8].split(' -> ')[0]
                    if perms.endswith('+'):
                        acls[name] = True
    except Exception: pass
    return acls

def get_git_branch(target_dir):
    try:
        res = subprocess.run(['git', 'branch', '--show-current'],
                             cwd=target_dir, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception: pass
    return None

def get_git_statuses_recursive(target_dir):
    statuses = {}
    try:
        res = subprocess.run(['git', 'status', '--porcelain', '.'],
                             cwd=target_dir, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
        for line in res.stdout.splitlines():
            if len(line) > 3:
                status, filepath = line[:2], line[3:].strip('"')
                statuses[filepath] = status
    except Exception: pass
    return statuses

def get_zos_tags(target_dir):
    tags = {}
    try:
        res = subprocess.run(['ls', '-T', '-A', '-1'],
                             cwd=target_dir, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 4:
                state, codeset, t_flag = parts[0], parts[1], parts[2]
                name = " ".join(parts[3:])
                if state in ('t', 'b', '-', 'm'):
                    tags[name] = (state, codeset, t_flag)
    except Exception: pass
    return tags

def get_extattrs(target_dir, files):
    attrs = {}
    if not files: return attrs
    chunk_size = 500
    try:
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i+chunk_size]
            res = subprocess.run(['extattr'] + chunk, cwd=target_dir, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.DEVNULL, text=True)
            for line in res.stdout.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    name = parts[4]
                    if name in chunk:
                        attrs[name] = parts[:4]
    except Exception: pass
    return attrs

_ZFS_DSN_CACHE = {}
def get_zfs_dsn(target_path):
    try:
        st = os.lstat(target_path)
        if stat.S_ISDIR(st.st_mode):
            cache_key = os.path.abspath(target_path)
        else:
            cache_key = os.path.dirname(os.path.abspath(target_path))
            
        if cache_key in _ZFS_DSN_CACHE:
            return _ZFS_DSN_CACHE[cache_key]
            
        res = subprocess.run(['df', '-P', cache_key], stdout=subprocess.PIPE, 
                             stderr=subprocess.DEVNULL, text=True)
        lines = res.stdout.splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            if len(parts) >= 1: 
                _ZFS_DSN_CACHE[cache_key] = parts[0]
                return parts[0]
    except Exception: pass
    return None

def format_git_badge(status):
    if not status: return f"{COLORS['git_clean']}--{COLORS['reset']}"
    if '?' in status: color = COLORS['git_untracked']
    elif 'M' in status or 'R' in status: color = COLORS['git_mod']
    elif 'A' in status: color = COLORS['git_add']
    else: color = COLORS['git_mod']
    return f"{color}{status:<2}{COLORS['reset']}"

def format_tag_badge(tag_info):
    if not tag_info: return " " * 13
    state, codeset, _ = tag_info
    return f"{COLORS['tags']}{state} {codeset:<10}{COLORS['reset']} "

def format_extattr_badge(ext_info):
    if not ext_info: return f"{COLORS['extattr']}[----]{COLORS['reset']} "
    return f"{COLORS['extattr']}[{''.join(ext_info[:4])}]{COLORS['reset']} "

def get_header_str(args, force_long=False):
    out = ""
    if args.inode:
        out += f"{'Inode':<10} "
    if args.long or force_long:
        if args.octal: out += f"{'Octal':<5} "
        if getattr(args, 'show_perms', True): out += f"{'Permissions':<11} "
        if getattr(args, 'show_links', True): out += f"{'Ln':>2} "
        if getattr(args, 'show_user', True): out += f"{'User':<8} "
        if getattr(args, 'show_group', True): out += f"{'Group':<8} "
        if getattr(args, 'show_size', True): out += f"{'Size':>5} "
        if getattr(args, 'show_time', True):
            time_lbl = "Accessed" if args.access else "Changed" if args.ctime else "Modified"
            out += f"{time_lbl:<12} "
    
    if args.git: out += f"{'Git':<3}"
    if args.tags: out += f"{'Tag Info':<13}"
    if args.extattr: out += f"{'ExtAttr':<7}"
    
    icon_pad = "  " if args.icons else ""
    out += f"{icon_pad}Name"
    
    if args.dsn: out += "  [Dataset]"
    return out

def print_grid(items):
    if not items: return
    term_width = shutil.get_terminal_size((80, 20)).columns
    max_len = max(item[1] for item in items)
    col_width = max_len + 2 
    cols = max(1, term_width // col_width)
    rows = (len(items) + cols - 1) // cols
    for row in range(rows):
        for col in range(cols):
            idx = col * rows + row
            if idx < len(items):
                ansi_str, vis_len = items[idx]
                padding = " " * (col_width - vis_len)
                print(f"{ansi_str}{padding}", end="")
        print()

def build_dict(entry, st, path, rel_path, g_stats, tags, x_stats, acls, args):
    size = int(st.st_blocks * 512) if (
        args.blocks and hasattr(st, 'st_blocks')) else int(st.st_size)
    user, group = get_owner_name(st.st_uid, st.st_gid, args.numeric)
    
    time_val = st.st_atime if args.access else st.st_ctime if args.ctime else st.st_mtime
        
    data = {
        "name": entry, "path": rel_path, "size_bytes": size,
        "inode": st.st_ino, "permissions": stat.filemode(st.st_mode),
        "octal_perms": oct(st.st_mode)[-4:], "has_acl": acls.get(entry, False),
        "links": st.st_nlink, "owner": user, "group": group, "timestamp": time_val
    }
    
    if stat.S_ISDIR(st.st_mode): data["type"] = "dir"
    elif stat.S_ISLNK(st.st_mode): 
        data["type"] = "symlink"
        try: data["target"] = os.readlink(path)
        except OSError: pass
    else: data["type"] = "file"
    
    git_key = rel_path if args.tree else entry.split('/')[0]
    if args.git and git_key in g_stats: data["git_status"] = g_stats[git_key]
    
    tag_info = tags.get(entry)
    if args.tags and tag_info:
        data["tag_state"], data["tag_codeset"] = tag_info[0], tag_info[1]
        
    x_info = x_stats.get(entry)
    if args.extattr and x_info:
        data["extattr"] = {
            "apf": x_info[0] == 'a', "program_control": x_info[1] == 'p',
            "shared_address_space": x_info[2] == 's', 
            "shared_library": x_info[3] == 'l'
        }
        
    if args.dsn:
        dsn_val = get_zfs_dsn(path)
        if dsn_val: data["zfs_dataset"] = dsn_val
        
    return data

def format_entry(entry, st, path, rel_path, g_stats, tags, x_stats, acls, args, 
                 t_pfx="", force_long=False, show_dsn=None):
    color = get_color(st.st_mode)
    icon = f"{get_icon(entry, st.st_mode)} " if args.icons else ""
    
    inode_str = f"{COLORS['inode']}{st.st_ino:<10}{COLORS['reset']} " if args.inode else ""
    octal_str = f"{COLORS['perms']}{oct(st.st_mode)[-4:]:>5}{COLORS['reset']} " if args.octal else ""
    
    git_key = rel_path if args.tree else entry.split('/')[0]
    git_badge = f"{format_git_badge(g_stats.get(git_key))} " if args.git else ""
    tag_badge = format_tag_badge(tags.get(entry)) if args.tags else ""
    x_badge = format_extattr_badge(x_stats.get(entry)) if args.extattr else ""
    
    sym_tgt = ""
    tgt_vis_len = 0
    
    if stat.S_ISLNK(st.st_mode) and (args.long or args.dsn or force_long):
        try:
            target = os.readlink(path)
            t_col = COLORS['dsn'] if target.startswith('//') else COLORS['symlink']
            sym_tgt = f" \uf178 {t_col}{target}{COLORS['reset']}"
            tgt_vis_len += 3 + len(target)
        except OSError: pass

    if args.dsn:
        dsn_val = show_dsn if show_dsn is not None else get_zfs_dsn(path)
        if dsn_val:
            sym_tgt += f"  {COLORS['dsn']}[{dsn_val}]{COLORS['reset']}"
            tgt_vis_len += 4 + len(dsn_val)
    
    if args.long or force_long:
        perms = stat.filemode(st.st_mode) + ('+' if acls.get(entry) else ' ')
        links = st.st_nlink
        user, group = get_owner_name(st.st_uid, st.st_gid, args.numeric)
        size_str = format_size(st, use_blocks=args.blocks)
        
        time_val = st.st_atime if args.access else st.st_ctime if args.ctime else st.st_mtime
        time_str = datetime.fromtimestamp(time_val).strftime('%b %d %H:%M')
        
        out = inode_str
        if args.octal: out += octal_str
        if getattr(args, 'show_perms', True):
            out += f"{COLORS['perms']}{perms}{COLORS['reset']} "
        if getattr(args, 'show_links', True):
            out += f"{links:2} "
        if getattr(args, 'show_user', True):
            out += f"{COLORS['user']}{user:<8}{COLORS['reset']} "
        if getattr(args, 'show_group', True):
            out += f"{COLORS['group']}{group:<8}{COLORS['reset']} "
        if getattr(args, 'show_size', True):
            out += f"{COLORS['size']}{size_str:>5}{COLORS['reset']} "
        if getattr(args, 'show_time', True):
            out += f"{COLORS['time']}{time_str}{COLORS['reset']} "
        out += f"{git_badge}{tag_badge}{x_badge}"
        out += f"{COLORS['tree_line']}{t_pfx}{COLORS['reset']}"
        out += f"{color}{icon}{entry}{COLORS['reset']}{sym_tgt}"
        return out, 0
    else:
        out = inode_str + f"{git_badge}{tag_badge}{x_badge}"
        out += f"{COLORS['tree_line']}{t_pfx}{COLORS['reset']}"
        out += f"{color}{icon}{entry}{COLORS['reset']}{sym_tgt}"
        vlen = 11 if args.inode else 0
        vlen += 3 if args.git else 0
        vlen += 13 if args.tags else 0
        vlen += 7 if args.extattr else 0
        vlen += len(t_pfx) + (2 if args.icons else 0)
        vlen += len(entry) + tgt_vis_len
        return out, vlen

def process_directory(target_dir, args, g_stats, prefix="", r_base="", root=True, last_dsn=None, depth=1):
    contents = []
    try: raw_entries = os.listdir(target_dir)
    except PermissionError:
        print(f"{prefix}{CMD_NAME}: permission denied '{target_dir}'", file=sys.stderr)
        return contents

    if not args.all:
        raw_entries = [e for e in raw_entries if not e.startswith('.')]
    elif root:
        if '..' not in raw_entries: raw_entries.append('..')

    zos_tags = get_zos_tags(target_dir) if args.tags else {}
    x_stats = get_extattrs(target_dir, raw_entries) if args.extattr else {}
    acls = get_acls(target_dir) if (args.long or args.tree or args.oneline) else {}

    entries_with_stats = []
    for entry in raw_entries:
        if entry == '..': p = os.path.dirname(os.path.abspath(target_dir))
        else: p = os.path.join(target_dir, entry)
            
        try:
            st = os.lstat(p)
            if args.allowed_exts and not stat.S_ISDIR(st.st_mode):
                if not entry.lower().endswith(args.allowed_exts): continue
            if args.regex_pattern and not stat.S_ISDIR(st.st_mode):
                if not args.regex_pattern.search(entry): continue
            entries_with_stats.append((entry, st, p))
        except OSError: continue

    dots = [e for e in entries_with_stats if e[0] == '..']
    files = [e for e in entries_with_stats if e[0] != '..']
    
    if args.sort_size:
        files.sort(key=lambda x: x[1].st_size, reverse=not args.reverse)
    elif args.time:
        if args.access: files.sort(key=lambda x: x[1].st_atime, reverse=not args.reverse)
        elif args.ctime: files.sort(key=lambda x: x[1].st_ctime, reverse=not args.reverse)
        else: files.sort(key=lambda x: x[1].st_mtime, reverse=not args.reverse)
    else:
        files.sort(key=lambda x: x[0].lower(), reverse=args.reverse)

    if getattr(args, 'group_directories_first', False):
        files.sort(key=lambda x: 0 if stat.S_ISDIR(x[1].st_mode) else 1)
        
    if args.reverse and not args.sort_size and not args.time:
        entries_with_stats = files + dots
    else:
        entries_with_stats = dots + files

    if last_dsn is None:
        last_dsn = [None]

    short_items = []
    for i, (entry, st, path) in enumerate(entries_with_stats):
        is_last = (i == len(entries_with_stats) - 1)
        rel_path = os.path.join(r_base, entry) if r_base else entry
        t_conn = "\u2514\u2500\u2500 " if (args.tree and is_last) else "\u251c\u2500\u2500 " if args.tree else ""
        
        disp_dsn = ""
        if args.dsn:
            cur_dsn = get_zfs_dsn(path)
            if cur_dsn and cur_dsn != last_dsn[0]:
                disp_dsn = cur_dsn
                last_dsn[0] = cur_dsn

        full_prefix = prefix + t_conn
        fmt_str, vlen = format_entry(
            entry, st, path, rel_path, g_stats, zos_tags, x_stats, acls, 
            args, t_pfx=full_prefix, show_dsn=disp_dsn
        )
        
        if args.long or args.tree or args.oneline: print(fmt_str)
        else: short_items.append((fmt_str, vlen))
            
        item_data = build_dict(
            entry, st, path, rel_path, g_stats, zos_tags, x_stats, acls, args
        )
            
        max_lvl = getattr(args, 'level', None)
        if args.tree and stat.S_ISDIR(st.st_mode) and entry != '..' and (max_lvl is None or depth < max_lvl):
            extension = "    " if is_last else "\u2502   "
            children = process_directory(
                path, args, g_stats, prefix + extension, rel_path, root=False, last_dsn=last_dsn, depth=depth + 1
            )
            item_data["children"] = children
        contents.append(item_data)

    if not (args.long or args.tree or args.oneline) and root: print_grid(short_items)
    return contents

# ==============================================================================
# TUI (Text User Interface) Implementation
# ==============================================================================
def apply_curses_colors(cfg):
    if curses.has_colors():
        curses.init_pair(1, cfg['color_dir'], -1)
        curses.init_pair(2, cfg['color_exe'], -1)
        curses.init_pair(3, cfg['color_sym'], -1)
        curses.init_pair(4, cfg['color_def'], -1)
        curses.init_pair(5, curses.COLOR_RED, -1)     
        curses.init_pair(6, curses.COLOR_MAGENTA, -1) 
        curses.init_pair(7, curses.COLOR_WHITE, -1)   
        for c_idx in range(8):
            try:
                curses.init_pair(10 + c_idx, c_idx, -1)
            except curses.error:
                pass   

def get_input(stdscr, y, w, prompt, default=""):
    stdscr.addstr(y, 0, prompt.ljust(w-1)[:w-1], curses.A_REVERSE)
    stdscr.move(y, len(prompt))
    try: curses.curs_set(1)
    except: pass
    curses.echo()
    res = stdscr.getstr(y, len(prompt), 100).decode('utf-8', 'ignore').strip()
    curses.noecho()
    try: curses.curs_set(0)
    except: pass
    return res

def popup_input(stdscr, title, prompt, default=""):
    h, w = stdscr.getmaxyx()
    box_w = min(max(len(prompt) + 16, 48), max(24, w - 4))
    box_h = 7
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    win = curses.newwin(box_h, box_w, start_y, start_x)
    win.keypad(True)
    b_attr = (curses.color_pair(3) | curses.A_BOLD) if curses.has_colors() else curses.A_BOLD
    win.attron(b_attr)
    win.box()
    win.attroff(b_attr)

    t_str = f" {title} "
    win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
    win.addstr(2, 2, prompt[:box_w - 4], curses.A_BOLD)

    field_w = box_w - 4
    win.addstr(3, 2, " " * field_w, curses.A_REVERSE)
    hint = "ENTER: Confirm | ESC: Cancel"
    win.addstr(5, max(2, (box_w - len(hint)) // 2), hint[:box_w - 4], curses.A_DIM)

    buf = list(default)
    try: curses.curs_set(1)
    except Exception: pass

    while True:
        disp = "".join(buf)[-(field_w - 1):]
        win.addstr(3, 2, disp.ljust(field_w), curses.A_REVERSE)
        win.move(3, 2 + min(len(disp), field_w - 1))
        win.refresh()

        k = win.getch()
        if k == 27:
            try: curses.curs_set(0)
            except Exception: pass
            win.erase()
            win.refresh()
            stdscr.touchwin()
            stdscr.refresh()
            return None
        elif k in (curses.KEY_ENTER, 10, 13):
            try: curses.curs_set(0)
            except Exception: pass
            win.erase()
            win.refresh()
            stdscr.touchwin()
            stdscr.refresh()
            return "".join(buf).strip()
        elif k in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
        elif 32 <= k <= 126:
            buf.append(chr(k))

def popup_confirm(stdscr, title, prompt):
    h, w = stdscr.getmaxyx()
    box_w = min(max(len(prompt) + 10, 44), max(24, w - 4))
    box_h = 6
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    win = curses.newwin(box_h, box_w, start_y, start_x)
    win.keypad(True)
    b_attr = (curses.color_pair(5) | curses.A_BOLD) if curses.has_colors() else curses.A_BOLD
    win.attron(b_attr)
    win.box()
    win.attroff(b_attr)

    t_str = f" {title} "
    win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
    win.addstr(2, max(2, (box_w - len(prompt)) // 2), prompt[:box_w - 4], curses.A_BOLD)

    hint = "Press [Y] to confirm or [N / ESC] to cancel"
    win.addstr(4, max(2, (box_w - len(hint)) // 2), hint[:box_w - 4],
               curses.color_pair(4) if curses.has_colors() else curses.A_NORMAL)
    win.refresh()

    while True:
        k = win.getch()
        if k in (ord('y'), ord('Y')):
            win.erase()
            win.refresh()
            stdscr.touchwin()
            stdscr.refresh()
            return True
        if k in (ord('n'), ord('N'), ord('q'), ord('Q'), 27):
            win.erase()
            win.refresh()
            stdscr.touchwin()
            stdscr.refresh()
            return False

def popup_message(stdscr, title, message, is_error=True):
    h, w = stdscr.getmaxyx()
    box_w = min(max(len(message) + 8, 42), max(24, w - 4))
    box_h = 6
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    win = curses.newwin(box_h, box_w, start_y, start_x)
    pair = 5 if is_error else 2
    b_attr = (curses.color_pair(pair) | curses.A_BOLD) if curses.has_colors() else curses.A_BOLD
    win.attron(b_attr)
    win.box()
    win.attroff(b_attr)

    t_str = f" {title} "
    win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
    win.addstr(2, 2, message[:box_w - 4], curses.A_BOLD)
    hint = "Press any key to continue"
    win.addstr(4, max(2, (box_w - len(hint)) // 2), hint[:box_w - 4], curses.A_DIM)
    win.refresh()
    win.getch()

def popup_columns(stdscr, args, config, use_color=True):
    col_defs = [
        ('inode',      'Inode Number',          'I'),
        ('octal',      'Octal Permissions',     'O'),
        ('show_perms', 'Symbolic Permissions',  'P'),
        ('show_links', 'Hard Links (Ln)',       'L'),
        ('show_user',  'Owner / User',          'U'),
        ('show_group', 'Group Name',            'K'),
        ('numeric',    'Numeric UID / GID',     'N'),
        ('show_size',  'File Size',             'F'),
        ('blocks',     'Size in 512B Blocks',   'B'),
        ('show_time',  'Timestamp Column',      'E'),
        ('git',        'Git Status Badge',      'G'),
        ('tags',       'z/OS File Tags (chtag)','T'),
        ('extattr',    'z/OS ExtAttr [apsl]',   'X'),
        ('icons',      'Nerd Font Icons',       'W'),
        ('dsn',        'zFS Dataset Name',      'M'),
    ]
    sel_idx = 0

    while True:
        h, w = stdscr.getmaxyx()
        box_h = min(len(col_defs) + 6, max(10, h - 2))
        box_w = min(58, max(36, w - 4))
        start_y = max(0, (h - box_h) // 2)
        start_x = max(0, (w - box_w) // 2)

        win = curses.newwin(box_h, box_w, start_y, start_x)
        win.keypad(True)
        win.erase()
        for r_idx in range(box_h):
            try:
                win.addstr(r_idx, 0, " " * (box_w - 1))
            except curses.error:
                pass

        has_c = use_color and curses.has_colors()

        b_attr = (curses.color_pair(3) | curses.A_BOLD) if has_c else curses.A_BOLD
        on_attr = (curses.color_pair(2) | curses.A_BOLD) if has_c else curses.A_BOLD
        off_attr = (curses.color_pair(5) | curses.A_BOLD) if has_c else curses.A_NORMAL
        txt_attr = (curses.color_pair(7) | curses.A_BOLD) if has_c else curses.A_NORMAL
        key_attr = (curses.color_pair(6) | curses.A_BOLD) if has_c else curses.A_BOLD

        win.attron(b_attr)
        win.box()
        win.attroff(b_attr)

        can_save = bool(config.get('save_columns', False))
        t_str = " TUI Columns (Add / Remove) "
        win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
        if can_save:
            sub_str = "SPACE: Toggle | a: All | d: Def | s: Save | q/ESC: Exit"
        else:
            sub_str = "SPACE/ENTER: Toggle | a: All | d: Default | q/ESC: Exit"
        win.addstr(1, 2, sub_str.center(box_w - 4)[:box_w - 4], b_attr)
        try:
            win.hline(2, 1, curses.ACS_HLINE, box_w - 2, b_attr)
        except curses.error:
            win.addstr(2, 1, "-" * (box_w - 2), b_attr)

        list_h = box_h - 5
        top_i = max(0, min(sel_idx - list_h + 1, len(col_defs) - list_h)) if sel_idx >= list_h else 0

        for idx in range(list_h):
            c_i = top_i + idx
            if c_i >= len(col_defs):
                break
            attr_name, label, hk = col_defs[c_i]
            enabled = bool(getattr(args, attr_name, True))
            is_sel = (c_i == sel_idx)

            row_y = 3 + idx
            chk = "[x]" if enabled else "[ ]"
            ptr = ">" if is_sel else " "
            c_attr = on_attr if enabled else off_attr
            l_attr = txt_attr

            if is_sel:
                win.addstr(row_y, 2, " " * (box_w - 4), curses.A_REVERSE)
                c_attr |= curses.A_REVERSE
                l_attr |= curses.A_REVERSE
                k_attr = key_attr | curses.A_REVERSE
            else:
                win.addstr(row_y, 2, " " * (box_w - 4), curses.A_NORMAL)
                k_attr = key_attr

            try:
                win.addstr(row_y, 2, f" {ptr} {chk} ", c_attr)
                win.addstr(row_y, 9, f"{label:<28}"[:box_w - 19], l_attr)
                if box_w >= 44:
                    win.addstr(row_y, box_w - 10, f"[{hk}]", k_attr)
            except curses.error:
                pass

        if can_save:
            ftr_hint = " s: Save layout to ~/.pyeza.json | Changes apply live "
        else:
            ftr_hint = " Changes apply live (Enable 'Save Columns' in 'o' Settings) "
        win.addstr(box_h - 2, 2, ftr_hint.center(box_w - 4)[:box_w - 4], curses.A_DIM)
        win.refresh()

        k = win.getch()
        if k == 27:
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            return False
        elif k in (ord('q'), ord('Q'), ord('v'), ord('V')):
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            return False
        elif k in (ord('s'), ord('S')) and can_save:
            saved_cols = {}
            for attr_name, _, _ in col_defs:
                saved_cols[attr_name] = bool(getattr(args, attr_name, True))
            config['columns'] = saved_cols
            save_config(config)
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            popup_message(stdscr, "Columns Saved", "Saved column preferences to ~/.pyeza.json", is_error=False)
            return True
        elif k == curses.KEY_UP:
            sel_idx = max(0, sel_idx - 1)
        elif k == curses.KEY_DOWN:
            sel_idx = min(len(col_defs) - 1, sel_idx + 1)
        elif k in (ord(' '), curses.KEY_ENTER, 10, 13):
            attr_name = col_defs[sel_idx][0]
            setattr(args, attr_name, not bool(getattr(args, attr_name, True)))
        elif k in (ord('a'), ord('A')):
            for attr_name, _, _ in col_defs:
                setattr(args, attr_name, True)
        elif k in (ord('d'), ord('D')):
            defaults = {
                'inode': False, 'octal': False, 'show_perms': True,
                'show_links': True, 'show_user': True, 'show_group': True,
                'numeric': False, 'show_size': True, 'blocks': False,
                'show_time': True, 'git': False, 'tags': False,
                'extattr': False, 'icons': False, 'dsn': False
            }
            for k_def, v_def in defaults.items():
                setattr(args, k_def, v_def)
        else:
            ch = chr(k).upper() if 32 <= k <= 126 else ''
            for c_i, (attr_name, _, hk) in enumerate(col_defs):
                if ch == hk:
                    sel_idx = c_i
                    setattr(args, attr_name, not bool(getattr(args, attr_name, True)))
                    break

def popup_chtag(stdscr, entry, path, use_color=True):
    opts = [
        ("1", "Text: ISO8859-1 (ASCII)",   ['chtag', '-tc', 'ISO8859-1', path]),
        ("2", "Text: IBM-1047 (EBCDIC)",   ['chtag', '-tc', 'IBM-1047', path]),
        ("3", "Text: UTF-8",               ['chtag', '-tc', 'UTF-8', path]),
        ("4", "Text: Custom Codeset...",   None),
        ("5", "Binary (-b)",               ['chtag', '-b', path]),
        ("6", "Mixed Text/Binary (-m)",    ['chtag', '-m', path]),
        ("7", "Remove File Tag (-r)",      ['chtag', '-r', path]),
    ]
    sel_idx = 0
    while True:
        h, w = stdscr.getmaxyx()
        box_h = min(len(opts) + 6, max(10, h - 2))
        box_w = min(54, max(34, w - 4))
        start_y = max(0, (h - box_h) // 2)
        start_x = max(0, (w - box_w) // 2)

        win = curses.newwin(box_h, box_w, start_y, start_x)
        win.keypad(True)
        win.erase()
        for r_idx in range(box_h):
            try: win.addstr(r_idx, 0, ' ' * (box_w - 1))
            except curses.error: pass
        has_c = use_color and curses.has_colors()
        b_attr = (curses.color_pair(3) | curses.A_BOLD) if has_c else curses.A_BOLD
        txt_attr = (curses.color_pair(7) | curses.A_BOLD) if has_c else curses.A_NORMAL
        key_attr = (curses.color_pair(2) | curses.A_BOLD) if has_c else curses.A_BOLD

        win.attron(b_attr)
        win.box()
        win.attroff(b_attr)

        t_str = f" z/OS File Tag (chtag): {entry[:20]} "
        win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
        sub_str = "UP/DN/1-7: Select | ENTER: Apply | ESC/q: Cancel"
        win.addstr(1, max(2, (box_w - len(sub_str)) // 2), sub_str[:box_w - 4], b_attr)
        try:
            win.hline(2, 1, curses.ACS_HLINE, box_w - 2, b_attr)
        except curses.error:
            win.addstr(2, 1, "-" * (box_w - 2), b_attr)

        for idx, (hk, label, _) in enumerate(opts):
            row_y = 3 + idx
            if row_y >= box_h - 2:
                break
            is_sel = (idx == sel_idx)
            ptr = ">" if is_sel else " "
            l_attr = (txt_attr | curses.A_REVERSE) if is_sel else txt_attr
            k_attr = (key_attr | curses.A_REVERSE) if is_sel else key_attr
            if is_sel:
                win.addstr(row_y, 2, " " * (box_w - 4), curses.A_REVERSE)
            try:
                win.addstr(row_y, 3, f"{ptr} [{hk}] ", k_attr)
                win.addstr(row_y, 10, label[:box_w - 12], l_attr)
            except curses.error:
                pass

        win.refresh()
        k = win.getch()
        if k in (27, ord('q'), ord('Q')):
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            return False
        elif k == curses.KEY_UP:
            sel_idx = max(0, sel_idx - 1)
        elif k == curses.KEY_DOWN:
            sel_idx = min(len(opts) - 1, sel_idx + 1)
        else:
            chosen = None
            if k in (curses.KEY_ENTER, 10, 13):
                chosen = opts[sel_idx]
            elif 32 <= k <= 126:
                ch = chr(k)
                for idx, item in enumerate(opts):
                    if item[0] == ch:
                        sel_idx = idx
                        chosen = item
                        break
            if chosen is not None:
                win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
                cmd = chosen[2]
                if cmd is None:
                    cs = popup_input(stdscr, "Custom Codeset", f"Enter codeset for '{entry}':", default="IBM-1047")
                    if not cs:
                        return False
                    t_mode = popup_input(stdscr, "Tag Mode", "Mode (-tc for text, -mc for mixed):", default="-tc")
                    if not t_mode:
                        return False
                    cmd = ['chtag', t_mode, cs, path]
                try:
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if res.returncode == 0:
                        popup_message(stdscr, "chtag Complete", f"Updated file tag for '{entry}'", is_error=False)
                        return True
                    else:
                        err = (res.stderr or res.stdout or "chtag failed").strip()
                        popup_message(stdscr, "chtag Error", err, is_error=True)
                        return False
                except Exception as e:
                    popup_message(stdscr, "chtag Error", str(e), is_error=True)
                    return False

def popup_extattr(stdscr, entry, path, cur_ext=None, use_color=True):
    flags = [
        ('a', 'APF Authorized'),
        ('p', 'Program Controlled'),
        ('s', 'Shared Address Space'),
        ('l', 'Shared Library'),
    ]
    state = {}
    if cur_ext and len(cur_ext) >= 4:
        for idx, (f_char, _) in enumerate(flags):
            state[f_char] = (cur_ext[idx] == f_char)
    else:
        try:
            res = subprocess.run(['extattr', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            for line in res.stdout.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 4 and all(len(p) == 1 for p in parts[:4]):
                    for idx, (f_char, _) in enumerate(flags):
                        state[f_char] = (parts[idx] == f_char)
                    break
        except Exception:
            pass
    for f_char, _ in flags:
        state.setdefault(f_char, False)

    sel_idx = 0
    while True:
        h, w = stdscr.getmaxyx()
        box_h = 10
        box_w = min(54, max(34, w - 4))
        start_y = max(0, (h - box_h) // 2)
        start_x = max(0, (w - box_w) // 2)

        win = curses.newwin(box_h, box_w, start_y, start_x)
        win.keypad(True)
        win.erase()
        for r_idx in range(box_h):
            try: win.addstr(r_idx, 0, ' ' * (box_w - 1))
            except curses.error: pass
        has_c = use_color and curses.has_colors()
        b_attr = (curses.color_pair(3) | curses.A_BOLD) if has_c else curses.A_BOLD
        on_attr = (curses.color_pair(2) | curses.A_BOLD) if has_c else curses.A_BOLD
        off_attr = (curses.color_pair(5) | curses.A_BOLD) if has_c else curses.A_NORMAL
        txt_attr = (curses.color_pair(7) | curses.A_BOLD) if has_c else curses.A_NORMAL

        win.attron(b_attr)
        win.box()
        win.attroff(b_attr)

        t_str = f" z/OS ExtAttr: {entry[:22]} "
        win.addstr(0, max(2, (box_w - len(t_str)) // 2), t_str[:box_w - 4], b_attr | curses.A_REVERSE)
        sub_str = "SPACE: Toggle | ENTER/s: Apply | ESC/q: Cancel"
        win.addstr(1, max(2, (box_w - len(sub_str)) // 2), sub_str[:box_w - 4], b_attr)
        try:
            win.hline(2, 1, curses.ACS_HLINE, box_w - 2, b_attr)
        except curses.error:
            win.addstr(2, 1, "-" * (box_w - 2), b_attr)

        for idx, (f_char, label) in enumerate(flags):
            row_y = 3 + idx
            en = state[f_char]
            is_sel = (idx == sel_idx)
            chk = f"[+{f_char}]" if en else f"[-{f_char}]"
            ptr = ">" if is_sel else " "
            c_attr = on_attr if en else off_attr
            l_attr = txt_attr
            if is_sel:
                win.addstr(row_y, 2, " " * (box_w - 4), curses.A_REVERSE)
                c_attr |= curses.A_REVERSE
                l_attr |= curses.A_REVERSE
            try:
                win.addstr(row_y, 3, f"{ptr} {chk} ", c_attr)
                win.addstr(row_y, 11, label[:box_w - 13], l_attr)
            except curses.error:
                pass

        win.refresh()
        k = win.getch()
        if k in (27, ord('q'), ord('Q')):
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            return False
        elif k == curses.KEY_UP:
            sel_idx = max(0, sel_idx - 1)
        elif k == curses.KEY_DOWN:
            sel_idx = min(len(flags) - 1, sel_idx + 1)
        elif k == ord(' '):
            f_char = flags[sel_idx][0]
            state[f_char] = not state[f_char]
        elif k in (ord('a'), ord('p'), ord('s'), ord('l')) and k != ord('s'):
            ch = chr(k)
            state[ch] = not state[ch]
        elif k in (curses.KEY_ENTER, 10, 13, ord('s'), ord('S')):
            win.erase(); win.refresh(); stdscr.touchwin(); stdscr.refresh()
            arg_flags = [f"+{fc}" if state[fc] else f"-{fc}" for fc, _ in flags]
            try:
                res = subprocess.run(['extattr'] + arg_flags + [path],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0:
                    badge = "".join(fc if state[fc] else "-" for fc, _ in flags)
                    popup_message(stdscr, "ExtAttr Complete", f"Set [{badge}] on '{entry}'", is_error=False)
                    return True
                else:
                    err = (res.stderr or res.stdout or "extattr failed").strip()
                    popup_message(stdscr, "ExtAttr Error", err, is_error=True)
                    return False
            except Exception as e:
                popup_message(stdscr, "ExtAttr Error", str(e), is_error=True)
                return False

def show_help(stdscr, title, lines):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    has_c = curses.has_colors()

    hdr_attr = (curses.color_pair(3) | curses.A_REVERSE | curses.A_BOLD) if has_c else curses.A_REVERSE
    sec_attr = (curses.color_pair(6) | curses.A_BOLD) if has_c else curses.A_BOLD
    key_attr = (curses.color_pair(2) | curses.A_BOLD) if has_c else curses.A_BOLD
    sep_attr = (curses.color_pair(3) | curses.A_BOLD) if has_c else curses.A_NORMAL
    txt_attr = curses.color_pair(7) if has_c else curses.A_NORMAL

    hdr = f" {title} Help (Tutorial) | Press any key to return "
    stdscr.addstr(0, 0, hdr.ljust(w-1)[:w-1], hdr_attr)

    for i, line in enumerate(lines):
        row = i + 2
        if row >= h - 1:
            break
        if not line.strip():
            continue
        if line.endswith(":") and ":" not in line[:-1]:
            try:
                stdscr.addstr(row, 2, line[:w-4], sec_attr)
            except curses.error:
                pass
        elif ":" in line:
            k_part, d_part = line.split(":", 1)
            try:
                stdscr.addstr(row, 2, k_part[:w-4], key_attr)
                col_x = 2 + len(k_part)
                if col_x < w - 2:
                    stdscr.addstr(row, col_x, ":", sep_attr)
                if col_x + 1 < w - 2:
                    stdscr.addstr(row, col_x + 1, d_part[:(w - 3 - col_x)], txt_attr)
            except curses.error:
                pass
        else:
            try:
                stdscr.addstr(row, 2, line[:w-4], txt_attr)
            except curses.error:
                pass

    ftr = " Press any key to close "
    stdscr.addstr(h - 1, 0, ftr.ljust(w-1)[:w-1], hdr_attr)
    stdscr.getch()

def settings_menu(stdscr, config, use_color=True):
    color_names = ['BLK', 'RED', 'GRN', 'YEL', 'BLU', 'MAG', 'CYN', 'WHT']
    sel_idx = 0
    opts = ['editor', 'save_columns', 'color_dir', 'color_exe', 'color_sym', 'color_def']
    labels = ['Default Editor', 'Save Columns', 'Dir Color', 'Exe Color', 'Sym Color', 'Def Text']
    samples = {
        'editor': 'Press ENTER to change editor command',
        'save_columns': 'Persist TUI column layout in ~/.pyeza.json (Default: OFF)',
        'color_dir': 'drwxr-xr-x  sample_dir/',
        'color_exe': '-rwxr-xr-x  zoseza.py*',
        'color_sym': 'lrwxrwxrwx  link -> target',
        'color_def': '-rw-r--r--  README.md'
    }

    help_lines = [
        "Settings Navigation:",
        "  UP/DOWN       : Move selection",
        "  LEFT/RIGHT    : Cycle colors or toggle Save Columns (ON/OFF)",
        "  SPACE/ENTER   : Edit Default Editor or toggle Save Columns",
        "",
        "Actions:",
        "  s             : Save config to ~/.pyeza.json and exit",
        "  ESC           : Go back to directory browser without saving",
        "  q             : Quit menu without saving"
    ]

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        has_c = use_color and curses.has_colors()

        hdr_attr = (curses.color_pair(3) | curses.A_REVERSE | curses.A_BOLD) if has_c else curses.A_REVERSE
        sec_attr = (curses.color_pair(6) | curses.A_BOLD) if has_c else curses.A_BOLD
        lbl_attr = (curses.color_pair(2) | curses.A_BOLD) if has_c else curses.A_BOLD
        sep_attr = (curses.color_pair(3) | curses.A_BOLD) if has_c else curses.A_NORMAL
        txt_attr = (curses.color_pair(7) | curses.A_BOLD) if has_c else curses.A_NORMAL

        hdr = f" {CMD_NAME} Settings | UP/DN: Sel | L/R/SPACE: Toggle | s: Save | F1: Help | q: Quit "
        stdscr.addstr(0, 0, hdr.ljust(w-1)[:w-1], hdr_attr)

        if h > 3:
            stdscr.addstr(2, 2, "Configuration & Color Preferences:"[:w-4], sec_attr)
            try:
                stdscr.hline(3, 2, curses.ACS_HLINE, min(w - 4, 68), sep_attr)
            except curses.error:
                stdscr.addstr(3, 2, "-" * min(w - 4, 68), sep_attr)

        for i, opt in enumerate(opts):
            row = i + 4
            if row >= h - 2:
                break
            val = config.get(opt, False if opt == 'save_columns' else '')
            is_sel = (i == sel_idx)
            is_color = opt.startswith('color_')
            is_bool = (opt == 'save_columns')
            if is_color:
                val_str = f"< {color_names[val]} >"
            elif is_bool:
                val_str = "< ON >" if val else "< OFF >"
            else:
                val_str = str(val)
            sample_str = samples.get(opt, '')

            if is_color and has_c:
                val_attr = curses.color_pair(10 + (val % 8)) | curses.A_BOLD
            elif is_bool and has_c:
                val_attr = (curses.color_pair(2) if val else curses.color_pair(5)) | curses.A_BOLD
            else:
                val_attr = txt_attr

            ptr = " > " if is_sel else "   "
            lbl_text = f"{ptr}{labels[i].ljust(15)}"
            l_attr = (lbl_attr | curses.A_REVERSE) if is_sel else lbl_attr
            v_attr = (val_attr | curses.A_REVERSE) if is_sel else val_attr

            try:
                stdscr.addstr(row, 2, lbl_text[:w-4], l_attr)
                col_x = 2 + len(lbl_text)
                if col_x + 3 < w - 2:
                    stdscr.addstr(row, col_x, " : ", sep_attr)
                    col_x += 3
                val_disp = val_str.ljust(10)
                if col_x + len(val_disp) < w - 2:
                    stdscr.addstr(row, col_x, val_disp, v_attr)
                    col_x += len(val_disp)
                if is_color and col_x + 4 < w - 2:
                    preview = f"  [{sample_str}]"
                    stdscr.addstr(row, col_x, preview[:(w - 2 - col_x)], val_attr)
                elif not is_color and col_x + 4 < w - 2:
                    hint = f"  ({sample_str})"
                    stdscr.addstr(row, col_x, hint[:(w - 2 - col_x)], sep_attr)
            except curses.error:
                pass

        ftr = " s:Save & Apply | LEFT/RIGHT/SPACE:Change | ENTER:Edit | ESC/q:Cancel "
        stdscr.addstr(h - 1, 0, ftr.ljust(w-1)[:w-1], hdr_attr)

        k = stdscr.getch()
        if k == 27:
            return None

        if k == curses.KEY_F1: show_help(stdscr, "Settings", help_lines)
        elif k == ord('q'): return None
        elif k == ord('s'):
            if not config.get('save_columns', False) and 'columns' in config:
                del config['columns']
            return config
        elif k == curses.KEY_UP: sel_idx = max(0, sel_idx - 1)
        elif k == curses.KEY_DOWN: sel_idx = min(len(opts) - 1, sel_idx + 1)
        elif k == curses.KEY_RIGHT:
            if opts[sel_idx].startswith('color_'):
                config[opts[sel_idx]] = (config[opts[sel_idx]] + 1) % 8
            elif opts[sel_idx] == 'save_columns':
                config['save_columns'] = not bool(config.get('save_columns', False))
        elif k == curses.KEY_LEFT:
            if opts[sel_idx].startswith('color_'):
                config[opts[sel_idx]] = (config[opts[sel_idx]] - 1) % 8
            elif opts[sel_idx] == 'save_columns':
                config['save_columns'] = not bool(config.get('save_columns', False))
        elif k in (ord(' '), curses.KEY_ENTER, 10, 13):
            if opts[sel_idx] == 'editor':
                new_ed = popup_input(stdscr, "Default Editor", "Editor command ($EDITOR):", default=str(config['editor']))
                if new_ed: config['editor'] = new_ed
            elif opts[sel_idx] == 'save_columns':
                config['save_columns'] = not bool(config.get('save_columns', False))

def addstr_ansi(stdscr, y, x, text, sel=False, max_w=80):
    parts = text.split('\033[')
    curr_x = x
    if sel: stdscr.addstr(y, 0, " " * (max_w - 1), curses.A_REVERSE)
    for part in parts:
        if curr_x >= max_w - 1: break
        code, content = "", part
        if 'm' in part and part != parts[0]:
            idx = part.find('m')
            code, content = part[:idx], part[idx+1:]
        attr = curses.A_REVERSE if sel else 0
        if curses.has_colors():
            if '34' in code: attr |= curses.color_pair(1)
            elif '32' in code: attr |= curses.color_pair(2)
            elif '36' in code: attr |= curses.color_pair(3)
            elif '33' in code: attr |= curses.color_pair(4)
            elif '31' in code: attr |= curses.color_pair(5)
            elif '35' in code: attr |= curses.color_pair(6)
            elif '90' in code: attr |= curses.color_pair(7)
        allowed = (max_w - 1) - curr_x
        if allowed <= 0: break
        if content[:allowed]:
            try: stdscr.addstr(y, curr_x, content[:allowed], attr)
            except curses.error: pass
            curr_x += len(content[:allowed])

def show_file_info(stdscr, entry, st, path):
    abs_path = os.path.abspath(path)
    parent_dir = os.path.dirname(abs_path) if not stat.S_ISDIR(st.st_mode) else abs_path

    if stat.S_ISDIR(st.st_mode): f_type = "Directory"
    elif stat.S_ISLNK(st.st_mode): f_type = "Symbolic Link"
    elif stat.S_ISREG(st.st_mode): f_type = "Regular File"
    elif stat.S_ISFIFO(st.st_mode): f_type = "FIFO / Named Pipe"
    elif stat.S_ISSOCK(st.st_mode): f_type = "Socket"
    elif stat.S_ISCHR(st.st_mode): f_type = "Character Device"
    elif stat.S_ISBLK(st.st_mode): f_type = "Block Device"
    else: f_type = "Unknown"

    sym_target = None
    if stat.S_ISLNK(st.st_mode):
        try: sym_target = os.readlink(path)
        except OSError as e: sym_target = f"(Error reading link: {e})"

    user_name, group_name = get_owner_name(st.st_uid, st.st_gid, numeric=False)
    perms_sym = stat.filemode(st.st_mode)
    perms_oct = oct(st.st_mode)[-4:]
    size_human = format_size(st, use_blocks=False).strip()
    blocks_512 = getattr(st, 'st_blocks', 0)

    mtime_str = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    atime_str = datetime.fromtimestamp(st.st_atime).strftime('%Y-%m-%d %H:%M:%S')
    ctime_str = datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S')

    # Query z/OS file tags (ls -T)
    tag_str = "Untagged / Not Available"
    try:
        res = subprocess.run(['ls', '-d', '-T', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        out_lines = res.stdout.splitlines()
        if out_lines:
            parts = out_lines[0].strip().split()
            if len(parts) >= 3 and parts[0] in ('t', 'b', '-', 'm'):
                state_map = {'t': 'Text (t)', 'b': 'Binary (b)', 'm': 'Mixed (m)', '-': 'Untagged (-)'}
                tag_str = f"{state_map.get(parts[0], parts[0])} | Codeset: {parts[1]} |TxtFlag: {parts[2]}"
    except Exception: pass

    # Query z/OS extended attributes (extattr)
    ext_str = "None / Not Available"
    ext_details = []
    try:
        res = subprocess.run(['extattr', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for line in res.stdout.splitlines():
            parts = line.split(None, 4)
            if len(parts) >= 4 and all(len(p) == 1 for p in parts[:4]):
                flags = "".join(parts[:4])
                flag_desc = []
                if parts[0] == 'a': flag_desc.append("APF Authorized (a)")
                if parts[1] == 'p': flag_desc.append("Program Controlled (p)")
                if parts[2] == 's': flag_desc.append("Shared Address Space (s)")
                if parts[3] == 'l': flag_desc.append("Shared Library (l)")
                ext_str = f"[{flags}] " + (", ".join(flag_desc) if flag_desc else "No active flags")
                break
    except Exception: pass

    # Query zFS Dataset & Mount info (df -P)
    dsn_val = get_zfs_dsn(path) or "Unknown"
    mount_point = "Unknown"
    try:
        res = subprocess.run(['df', '-P', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        d_lines = res.stdout.splitlines()
        if len(d_lines) >= 2:
            d_parts = d_lines[1].split()
            if len(d_parts) >= 6:
                mount_point = d_parts[5]
    except Exception: pass

    # Query ACL entries (getfacl or ls -ld)
    has_acl = False
    acl_lines = []
    try:
        res = subprocess.run(['ls', '-d', '-l', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if res.stdout:
            p_field = res.stdout.splitlines()[0].split()[0]
            if p_field.endswith('+'):
                has_acl = True
    except Exception: pass

    if has_acl:
        try:
            res = subprocess.run(['getfacl', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            for l in res.stdout.splitlines():
                if l.strip() and not l.startswith('#'):
                    acl_lines.append("    " + l.strip())
        except Exception: pass

    # Query Git status & branch
    git_branch = get_git_branch(parent_dir)
    git_status = "Clean / Tracked"
    if git_branch:
        try:
            res = subprocess.run(['git', 'status', '--porcelain', abs_path],
                                 cwd=parent_dir, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if res.stdout.strip():
                git_status = res.stdout.strip()[:2].strip()
        except Exception: pass
    else:
        git_status = "Not in a Git repository"

    info_lines = [
        f"File Name        : {entry}",
        f"Full Path        : {abs_path}",
        f"File Type        : {f_type}",
    ]
    if sym_target is not None:
        info_lines.append(f"Symlink Target   : {sym_target}")

    info_lines.extend([
        "",
        "--- Ownership & Permissions ---",
        f"Permissions      : {perms_sym}{'+' if has_acl else ''} (Octal: {perms_oct})",
        f"Owner (UID)      : {user_name} ({st.st_uid})",
        f"Group (GID)      : {group_name} ({st.st_gid})",
        f"Extended ACLs    : {'Yes (+)' if has_acl else 'No'}",
    ])
    if acl_lines:
        info_lines.extend(acl_lines[:10])

    info_lines.extend([
        "",
        "--- Size & Storage ---",
        f"Size             : {size_human} ({st.st_size:,} bytes)",
        f"512B Blocks      : {blocks_512}",
        f"Inode            : {st.st_ino}",
        f"Hard Links       : {st.st_nlink}",
        f"Device ID        : {st.st_dev}",
        "",
        "--- z/OS USS Attributes ---",
        f"File Tag (chtag) : {tag_str}",
        f"ExtAttr          : {ext_str}",
        f"zFS Dataset      : {dsn_val}",
        f"Mount Point      : {mount_point}",
        "",
        "--- Timestamps ---",
        f"Modified (mtime) : {mtime_str}",
        f"Accessed (atime) : {atime_str}",
        f"Changed  (ctime) : {ctime_str}",
        "",
        "--- Git Integration ---",
        f"Git Branch       : {git_branch or 'N/A'}",
        f"Git Status       : {git_status}",
    ])

    top = 0
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        hdr = f" File Info: {entry} | UP/DN: Scroll | q/ESC/i: Close "
        stdscr.addstr(0, 0, hdr.ljust(w - 1)[:w - 1], curses.A_REVERSE)

        view_h = h - 2
        for idx in range(view_h):
            if top + idx < len(info_lines):
                line = info_lines[top + idx]
                attr = curses.A_BOLD if line.startswith("---") else curses.A_NORMAL
                try:
                    stdscr.addstr(idx + 1, 2, line[:w - 4], attr)
                except curses.error:
                    pass

        ftr = " Press q, i, or ESC to return to browser "
        stdscr.addstr(h - 1, 0, ftr.ljust(w - 1)[:w - 1], curses.A_REVERSE)

        k = stdscr.getch()
        if k == 27:
            break

        if k in (ord('q'), ord('i'), curses.KEY_ENTER, 10, 13):
            break
        elif k == curses.KEY_UP:
            top = max(0, top - 1)
        elif k == curses.KEY_DOWN:
            top = min(max(0, len(info_lines) - view_h), top + 1)
        elif k == curses.KEY_PPAGE:
            top = max(0, top - (view_h - 1))
        elif k == curses.KEY_NPAGE:
            top = min(max(0, len(info_lines) - view_h), top + (view_h - 1))

def view_file(stdscr, path):
    raw_bytes = None
    default_lines = []
    try:
        with open(path, 'r', errors='replace') as f:
            default_lines = [line.rstrip('\r\n') for line in f]
    except Exception as e:
        default_lines = [f"Error reading file {path}: {e}"]

    try:
        with open(path, 'rb') as bf:
            raw_bytes = bf.read()
    except Exception:
        raw_bytes = None

    modes = ['AUTO', 'ISO8859-1', 'IBM-1047', 'HEX']
    mode_idx = 0

    def render_mode_lines(m_name):
        if m_name == 'AUTO' or raw_bytes is None:
            return default_lines
        if m_name == 'ISO8859-1':
            text = raw_bytes.decode('latin-1', errors='replace')
            return text.splitlines()
        if m_name == 'IBM-1047':
            text = raw_bytes.decode('cp1047', errors='replace').replace('\x15', '\n')
            return text.splitlines()
        if m_name == 'HEX':
            h_lines = [
                "Offset    Hexadecimal                                       ASCII             EBCDIC (1047)",
                "--------  ------------------------------------------------  ----------------  ----------------"
            ]
            limit = min(len(raw_bytes), 262144)
            for off in range(0, limit, 16):
                chunk = raw_bytes[off:off+16]
                hex_part = " ".join(f"{b:02X}" for b in chunk).ljust(47)
                asc_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk).ljust(16)
                try:
                    ebc_dec = chunk.decode('cp1047', errors='replace')
                    ebc_part = "".join(ch if (' ' <= ch <= '~') else "." for ch in ebc_dec).ljust(16)
                except Exception:
                    ebc_part = "." * len(chunk)
                h_lines.append(f"{off:08X}  {hex_part}   {asc_part}  {ebc_part}")
            if len(raw_bytes) > limit:
                h_lines.append(f"... (Hex dump truncated at {limit} bytes) ...")
            return h_lines
        return default_lines

    lines = render_mode_lines(modes[mode_idx])

    help_lines = [
        "Viewer Navigation:",
        "  UP/DOWN       : Scroll line by line",
        "  PgUp/PgDn     : Scroll by page",
        "  Home/End      : Jump to top or bottom of file",
        "",
        "Encoding & Hex Inspection:",
        "  c             : Cycle decoding (AUTO -> ISO8859-1 -> IBM-1047 -> HEX)",
        "  h             : Toggle side-by-side Hex / ASCII / EBCDIC dump view",
        "",
        "Search & Exit:",
        "  /             : Open search prompt at bottom",
        "  n             : Jump to next search match",
        "  ESC or q      : Go back to directory browser"
    ]

    top, query = 0, ""
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        for i in range(h - 1):
            if top + i < len(lines):
                stdscr.addstr(i, 0, lines[top + i][:w-1])

        m_label = modes[mode_idx]
        stat_b = f" {os.path.basename(path)} [{m_label}] | c:Code h:Hex /:Find n:Next F1:Help q:Quit "
        stdscr.addstr(h - 1, 0, stat_b[:w-1].ljust(w-1), curses.A_REVERSE)

        k = stdscr.getch()
        if k == 27:
            break

        if k == curses.KEY_F1: show_help(stdscr, "File Viewer", help_lines)
        elif k == ord('q'): break
        elif k == curses.KEY_UP: top = max(0, top - 1)
        elif k == curses.KEY_DOWN: top = min(max(0, len(lines) - h + 1), top + 1)
        elif k == curses.KEY_PPAGE: top = max(0, top - (h - 2))
        elif k == curses.KEY_NPAGE: top = min(max(0, len(lines) - h + 1), top + (h - 2))
        elif k in (curses.KEY_HOME, ord('g')): top = 0
        elif k in (curses.KEY_END, ord('G')): top = max(0, len(lines) - h + 1)
        elif k in (ord('c'), ord('C')):
            mode_idx = (mode_idx + 1) % len(modes)
            lines = render_mode_lines(modes[mode_idx])
            top = min(top, max(0, len(lines) - h + 1))
        elif k in (ord('h'), ord('H')):
            mode_idx = 3 if modes[mode_idx] != 'HEX' else 0
            lines = render_mode_lines(modes[mode_idx])
            top = 0
        elif k == ord('/'):
            query = get_input(stdscr, h-1, w, " Search: ")
            for i in range(top, len(lines)):
                if query.lower() in lines[i].lower():
                    top = i; break
        elif k == ord('n') and query:
            for i in range(top + 1, len(lines)):
                if query.lower() in lines[i].lower():
                    top = i; break

def tui_loop(stdscr, start_paths, args):
    try:
        curses.set_escdelay(25)
    except Exception:
        pass
    curses.curs_set(0)
    stdscr.keypad(True)
    
    config = load_config()
    use_tui_color = getattr(args, 'use_color', True) and curses.has_colors()
    if use_tui_color:
        curses.start_color()
        curses.use_default_colors()
        apply_curses_colors(config)
        sync_ansi_colors(config)
    
    if not start_paths:
        start_paths = ['.']
        
    first_path = os.path.abspath(start_paths[0])
    explicit_files = None
    
    if os.path.isdir(first_path) and len(start_paths) == 1:
        current_dir = first_path
    else:
        if os.path.exists(first_path) and not os.path.isdir(first_path):
            current_dir = os.path.dirname(first_path)
        else:
            current_dir = os.path.abspath('.') if os.path.isdir('.') else '/'
        explicit_files = {os.path.basename(os.path.abspath(p)) for p in start_paths}
        
    initial_dir = current_dir
    prev_dir = None
    sel_idx, top_idx = 0, 0
    sort_by = 'time' if args.time else 'size' if args.sort_size else 'name'
    sort_rev = args.reverse
    current_filter = ""
    
    for col_attr in ('show_perms', 'show_links', 'show_user', 'show_group', 'show_size', 'show_time'):
        if not hasattr(args, col_attr):
            setattr(args, col_attr, True)

    saved_cols = config.get('columns') if config.get('save_columns', False) else None
    if isinstance(saved_cols, dict):
        for c_key, c_val in saved_cols.items():
            if c_key in ('show_perms', 'show_links', 'show_user', 'show_group', 'show_size', 'show_time'):
                setattr(args, c_key, bool(c_val))
            elif hasattr(args, c_key) and not getattr(args, c_key):
                setattr(args, c_key, bool(c_val))

    items = []
    g_stats, tags, x_stats, acls = {}, {}, {}, {}
    
    help_lines = [
        "Navigation:",
        "  UP/DOWN      : Move cursor line by line",
        "  PgUp/PgDn    : Scroll directory list by page",
        "  Home/End     : Jump to first or last entry",
        "  ENTER        : Open Directory or File Viewer (with ASCII/EBCDIC/Hex)",
        "  ESC          : Go up one directory",
        "",
        "File & z/OS Operations:",
        "  i            : Inspect full file info/metadata",
        "  e            : Edit file (vi, etc)",
        "  m / A        : Create new directory (m) / new empty file (A)",
        "  p            : Change permissions (chmod octal popup)",
        "  u            : Change z/OS file tag (chtag popup)",
        "  x            : Modify z/OS extended attributes (extattr popup)",
        "  D / R / C    : Delete / Rename / Copy file or directory",
        "",
        "Sorting & Filtering:",
        "  s / t / a / z: Sort Size (s), MTime (t), ATime (a), CTime (z)",
        "  n / r / d    : Sort Name (n), Reverse (r), Group Dirs First (d)",
        "  .            : Toggle hidden dotfiles (-a)",
        "  f or /       : Filter by string (c to clear)",
        "",
        "Column & View Toggles:",
        "  v            : Open interactive Columns Menu (Add/Remove any column)",
        "  I / O / N    : Toggle Inode / Octal perms / Numeric UID & GID",
        "  G / T / X / M: Toggle Git / z/OS Tags / ExtAttr / zFS Dataset",
        "  B / W        : Toggle 512B Blocks / Nerd Font Icons",
        "",
        "Settings:",
        "  o            : Change colors/editor",
        "  q            : Quit"
    ]
    
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        
        if current_dir != prev_dir:
            try: raw = os.listdir(current_dir)
            except Exception as e:
                raw = []
                stdscr.addstr(1, 0, f"Error: {e}")
                
            if not args.all:
                raw = [e for e in raw if not e.startswith('.')]
                
            if explicit_files and current_dir == initial_dir:
                raw = [e for e in raw if e in explicit_files or e == '..']
                
            g_stats = get_git_statuses_recursive(current_dir) if args.git else {}
            tags = get_zos_tags(current_dir) if args.tags else {}
            x_stats = get_extattrs(current_dir, raw) if args.extattr else {}
            acls = get_acls(current_dir)
            prev_dir = current_dir
            sel_idx, top_idx = 0, 0
            
        items = []
        raw_files = []
        dots = []
        
        if current_dir != '/':
            try: p_st = os.lstat(os.path.dirname(current_dir))
            except: p_st = None
            if p_st: dots.append(('..', p_st, os.path.dirname(current_dir)))
            
        for entry in raw:
            if current_filter and current_filter.lower() not in entry.lower(): continue
            if entry == '..': continue 
            
            p = os.path.join(current_dir, entry)
            try: raw_files.append((entry, os.lstat(p), p))
            except: pass
            
        if sort_by == 'size':
            raw_files.sort(key=lambda x: x[1].st_size, reverse=not sort_rev)
        elif sort_by == 'time':
            raw_files.sort(key=lambda x: x[1].st_mtime, reverse=not sort_rev)
        elif sort_by == 'atime':
            raw_files.sort(key=lambda x: x[1].st_atime, reverse=not sort_rev)
        elif sort_by == 'ctime':
            raw_files.sort(key=lambda x: x[1].st_ctime, reverse=not sort_rev)
        else:
            raw_files.sort(key=lambda x: x[0].lower(), reverse=sort_rev)

        if getattr(args, 'group_directories_first', False):
            raw_files.sort(key=lambda x: 0 if stat.S_ISDIR(x[1].st_mode) else 1)
            
        if sort_rev and sort_by == 'name':
            items = raw_files + dots
        else:
            items = dots + raw_files
            
        if len(items) == (1 if current_dir != '/' else 0): 
            items.append(('(No Matches)', None, ''))
            
        sel_idx = max(0, min(sel_idx, len(items) - 1))
        
        list_h = h - 4
        if sel_idx < top_idx: top_idx = sel_idx
        elif sel_idx >= top_idx + list_h: top_idx = sel_idx - (list_h - 1)
        
        hdr = f" Dir: {current_dir}"
        if args.dsn:
            c_dsn = get_zfs_dsn(current_dir)
            if c_dsn: hdr += f" [{c_dsn}]"
        
        hdr += f" | Sort: {sort_by.upper()}{' (Rev)' if sort_rev else ''}{' [Dirs1st]' if getattr(args, 'group_directories_first', False) else ''}"
        if current_filter or (explicit_files and current_dir == initial_dir): 
            f_str = current_filter if current_filter else "[Explicit Glob]"
            hdr += f" | Flt: '{f_str}'"
        stdscr.addstr(0, 0, hdr[:w-1].ljust(w-1), curses.A_REVERSE)
        
        col_hdr = get_header_str(args, force_long=True)
        stdscr.addstr(1, 0, col_hdr[:w-1].ljust(w-1), curses.A_BOLD)
        try:
            stdscr.hline(2, 0, curses.ACS_HLINE, w - 1)
        except curses.error:
            stdscr.addstr(2, 0, "-" * (w - 1), curses.A_NORMAL)
        
        last_tui_dsn = None
        for idx_all in range(top_idx + list_h):
            if idx_all >= len(items):
                break
            entry, st, path = items[idx_all]
            disp_dsn = ""
            if st and args.dsn:
                cur_dsn = get_zfs_dsn(path)
                if cur_dsn and cur_dsn != last_tui_dsn:
                    disp_dsn = cur_dsn
                    last_tui_dsn = cur_dsn
            if idx_all < top_idx:
                continue
            i = idx_all - top_idx
            if not st:
                stdscr.addstr(i + 3, 0, entry, curses.A_NORMAL)
                continue
            ansi_str, _ = format_entry(
                entry, st, path, entry, g_stats, tags, x_stats, acls, args,
                force_long=True, show_dsn=disp_dsn
            )
            addstr_ansi(stdscr, i + 3, 0, ansi_str, (idx_all == sel_idx), w)
                
        ftr = " q:Quit i:Info v:Cols p,u,x:Attr m,A,D,R,C:Ops .:Dot d:Dirs F1:Help "
        stdscr.addstr(h - 1, 0, ftr.ljust(w-1)[:w-1], curses.A_REVERSE)
        
        k = stdscr.getch()
        if k == 27:
            if current_dir != '/':
                current_dir = os.path.dirname(current_dir)
                current_filter = ""
                prev_dir = None
                
        elif k == curses.KEY_F1:
            show_help(stdscr, "Browser", help_lines)
            prev_dir = None 
        elif k == ord('q'): break
        elif k == curses.KEY_UP: sel_idx -= 1
        elif k == curses.KEY_DOWN: sel_idx += 1
        elif k == curses.KEY_PPAGE: sel_idx = max(0, sel_idx - list_h)
        elif k == curses.KEY_NPAGE: sel_idx = min(len(items) - 1, sel_idx + list_h)
        elif k == curses.KEY_HOME: sel_idx = 0
        elif k == curses.KEY_END: sel_idx = len(items) - 1
        elif k == ord('.'):
            args.all = not args.all
            prev_dir = None
        elif k == ord('d'):
            args.group_directories_first = not getattr(args, 'group_directories_first', False)
        elif k == ord('s'): sort_by = 'size'
        elif k == ord('t'): sort_by = 'time'; args.access = False; args.ctime = False
        elif k == ord('a'): sort_by = 'atime'; args.access = True; args.ctime = False
        elif k == ord('z'): sort_by = 'ctime'; args.access = False; args.ctime = True
        elif k == ord('n'): sort_by = 'name'
        elif k == ord('r'): sort_rev = not sort_rev
        elif k == ord('m'):
            new_d = popup_input(stdscr, "Create Directory (mkdir)", "New directory name:")
            if new_d:
                try:
                    os.makedirs(os.path.join(current_dir, new_d), exist_ok=False)
                    popup_message(stdscr, "Directory Created", f"Created directory '{new_d}'", is_error=False)
                    prev_dir = None
                except Exception as e:
                    popup_message(stdscr, "mkdir Error", str(e), is_error=True)
        elif k == ord('A'):
            new_f = popup_input(stdscr, "Create New File", "New file name:")
            if new_f:
                target_f = os.path.join(current_dir, new_f)
                if os.path.exists(target_f):
                    popup_message(stdscr, "File Exists", f"'{new_f}' already exists", is_error=True)
                else:
                    try:
                        with open(target_f, 'a'):
                            pass
                        popup_message(stdscr, "File Created", f"Created empty file '{new_f}'", is_error=False)
                        prev_dir = None
                    except Exception as e:
                        popup_message(stdscr, "Create Error", str(e), is_error=True)
        elif k == ord('p'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                cur_oct = oct(sel[1].st_mode)[-4:]
                new_oct = popup_input(stdscr, "Change Permissions (chmod)", f"Octal mode for '{sel[0]}':", default=cur_oct)
                if new_oct and new_oct != cur_oct:
                    try:
                        mode_int = int(new_oct, 8)
                        os.chmod(sel[2], mode_int)
                        popup_message(stdscr, "chmod Complete", f"Set permissions of '{sel[0]}' to {new_oct}", is_error=False)
                        prev_dir = None
                    except Exception as e:
                        popup_message(stdscr, "chmod Error", str(e), is_error=True)
        elif k == ord('u'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                if popup_chtag(stdscr, sel[0], sel[2], use_tui_color):
                    prev_dir = None
        elif k == ord('x'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                if popup_extattr(stdscr, sel[0], sel[2], x_stats.get(sel[0]), use_tui_color):
                    prev_dir = None
        elif k == ord('v') or k == ord('V'):
            prev_g, prev_t, prev_x = args.git, args.tags, args.extattr
            popup_columns(stdscr, args, config, use_tui_color)
            if (args.git and not prev_g) or (args.tags and not prev_t) or (args.extattr and not prev_x):
                prev_dir = None
        elif k == ord('I'): args.inode = not args.inode
        elif k == ord('O'): args.octal = not args.octal
        elif k == ord('N'): args.numeric = not args.numeric
        elif k == ord('G'):
            args.git = not args.git
            if args.git and not g_stats: g_stats = get_git_statuses_recursive(current_dir)
        elif k == ord('T'):
            args.tags = not args.tags
            if args.tags and not tags: tags = get_zos_tags(current_dir)
        elif k == ord('X'):
            args.extattr = not args.extattr
            if args.extattr and not x_stats: x_stats = get_extattrs(current_dir, raw)
        elif k == ord('M'): args.dsn = not args.dsn
        elif k == ord('B'): args.blocks = not args.blocks
        elif k == ord('W'): args.icons = not args.icons
        elif k == ord('c'): 
            current_filter = ""
            if explicit_files:
                explicit_files = None
                prev_dir = None
        elif k == ord('f') or k == ord('/'):
            current_filter = get_input(stdscr, h-1, w, " Filter: ")
        elif k == ord('D'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                kind = "directory" if stat.S_ISDIR(sel[1].st_mode) else "file"
                if popup_confirm(stdscr, "Confirm Delete", f"Delete {kind} '{sel[0]}'?"):
                    try:
                        if stat.S_ISDIR(sel[1].st_mode): shutil.rmtree(sel[2])
                        else: os.remove(sel[2])
                        popup_message(stdscr, "Delete Complete", f"Deleted {kind} '{sel[0]}'", is_error=False)
                        prev_dir = None
                    except Exception as e:
                        popup_message(stdscr, "Delete Error", str(e), is_error=True)
        elif k == ord('R'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                new_n = popup_input(stdscr, "Rename Item", f"Rename '{sel[0]}' to:", default=sel[0])
                if new_n and new_n != sel[0]:
                    try:
                        os.rename(sel[2], os.path.join(current_dir, new_n))
                        popup_message(stdscr, "Rename Complete", f"Renamed '{sel[0]}' to '{new_n}'", is_error=False)
                        prev_dir = None
                    except Exception as e:
                        popup_message(stdscr, "Rename Error", str(e), is_error=True)
        elif k == ord('C'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                new_n = popup_input(stdscr, "Copy Item", f"Copy '{sel[0]}' to:", default=sel[0])
                if new_n and new_n != sel[0]:
                    try:
                        dst = os.path.join(current_dir, new_n)
                        if stat.S_ISDIR(sel[1].st_mode): shutil.copytree(sel[2], dst)
                        else: shutil.copy2(sel[2], dst)
                        popup_message(stdscr, "Copy Complete", f"Copied '{sel[0]}' to '{new_n}'", is_error=False)
                        prev_dir = None
                    except Exception as e:
                        popup_message(stdscr, "Copy Error", str(e), is_error=True)
        elif k == ord('o'):
            new_cfg = settings_menu(stdscr, dict(config), use_tui_color)
            if new_cfg:
                config = new_cfg
                save_config(config)
                if use_tui_color:
                    apply_curses_colors(config)
                    sync_ansi_colors(config)
                popup_message(stdscr, "Settings Saved", "Saved editor & colors to ~/.pyeza.json", is_error=False)
                prev_dir = None 
        elif k == ord('i'):
            sel = items[sel_idx]
            if sel[1]:
                show_file_info(stdscr, sel[0], sel[1], sel[2])
        elif k == ord('e'):
            sel = items[sel_idx]
            if sel[1] and not stat.S_ISDIR(sel[1].st_mode):
                curses.endwin()
                subprocess.run([config.get('editor', 'vi'), sel[2]])
                stdscr.clear()
                prev_dir = None 
        elif k in (curses.KEY_ENTER, 10, 13):
            sel = items[sel_idx]
            if not sel[1]: continue
            if stat.S_ISDIR(sel[1].st_mode):
                if sel[0] == '..': current_dir = os.path.dirname(current_dir)
                else: current_dir = sel[2]
                current_filter = ""
                prev_dir = None
            else:
                view_file(stdscr, sel[2])

# ==============================================================================
# Main CLI Entry Point
# ==============================================================================
def main():
    cfg = load_config()
    sync_ansi_colors(cfg)
    apply_ls_colors() 
    
    parser = argparse.ArgumentParser(description="Python eza clone for z/OS (TUI Config saved to ~/.pyeza.json)")
    parser.add_argument('paths', nargs='*', default=['.'])
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('-l', '--long', action='store_true')
    parser.add_argument('-g', '--git', action='store_true')
    parser.add_argument('-t', '--time', action='store_true')
    parser.add_argument('-u', '--access', action='store_true')
    parser.add_argument('-c', '--ctime', action='store_true')
    parser.add_argument('-i', '--icons', action='store_true')
    parser.add_argument('--inode', action='store_true')
    parser.add_argument('-O', '--octal', action='store_true')
    parser.add_argument('-n', '--numeric', action='store_true')
    parser.add_argument('-b', '--blocks', action='store_true')
    parser.add_argument('-J', '--json', metavar='FILE')
    parser.add_argument('-e', '--ext', metavar='EXT')
    parser.add_argument('-R', '--regex', metavar='PATTERN')
    parser.add_argument('-T', '--tags', action='store_true')
    parser.add_argument('-x', '--extattr', action='store_true')
    parser.add_argument('--tree', action='store_true', help="Display recursive directory tree")
    parser.add_argument('-L', '--level', type=int, metavar='DEPTH',
                        help="Limit recursion depth of --tree")
    parser.add_argument('--group-directories-first', action='store_true',
                        help="List directories before regular files")
    parser.add_argument('-d', '--directory', action='store_true')
    parser.add_argument('-S', '--sort-size', action='store_true')
    parser.add_argument('-r', '--reverse', action='store_true')
    parser.add_argument('-1', '--oneline', action='store_true')
    parser.add_argument('-D', '--dsn', action='store_true', help="Show underlying zFS dataset names")
    parser.add_argument('--color', choices=['auto', 'always', 'never'], default='auto',
                        help="When to use terminal colors (auto, always, never)")
    parser.add_argument('--no-color', action='store_true',
                        help="Disable all terminal colors (same as --color=never)")
    parser.add_argument('-v', '--version', action='version',
                        version=f"%(prog)s {VERSION} (z/OS USS)",
                        help="Show program's version number and exit")
    parser.add_argument('--tui', action='store_true')
    
    args = parser.parse_args()
    
    if args.no_color or args.color == 'never' or 'NO_COLOR' in os.environ:
        args.use_color = False
    elif args.color == 'always':
        args.use_color = True
    else:
        args.use_color = sys.stdout.isatty()
        
    if not args.use_color:
        disable_ansi_colors()
    
    if args.tui:
        os.environ.setdefault('ESCDELAY', '25')
        curses.wrapper(tui_loop, args.paths, args)
        return
    
    if args.ext:
        exts = [x.lower().strip() for x in args.ext.split(',')]
        args.allowed_exts = tuple(x if x.startswith('.') else '.' + x for x in exts)
    else: args.allowed_exts = ()
        
    if args.regex:
        try: args.regex_pattern = re.compile(args.regex)
        except re.error as e:
            print(f"{CMD_NAME}: invalid regex - {e}", file=sys.stderr)
            sys.exit(1)
    else: args.regex_pattern = None
        
    all_json_data = []

    file_paths = []
    dir_paths = []
    
    for p in args.paths:
        if os.path.isdir(p) and not args.directory:
            dir_paths.append(p)
        else:
            file_paths.append(p)

    if file_paths:
        short_items = []
        prev_file_dsn = None
        path_dict = {"target": "files", "contents": []}
        
        if args.long or args.tree or args.oneline:
            hdr_str = get_header_str(args)
            print(f"\033[1;4m{hdr_str}\033[0m" if args.use_color else hdr_str)
        
        for path in file_paths:
            try:
                st = os.lstat(path)
                t_stat, x_stat, acls = {}, {}, {}
                
                if args.long or args.oneline or args.tree:
                    # Run a single file ACL check
                    try:
                        res = subprocess.run(['ls', '-A', '-l', path], stdout=subprocess.PIPE, text=True)
                        for line in res.stdout.splitlines():
                            if line and line[0] in ('-', 'd', 'l', 'c', 'b', 'p', 's'):
                                perms = line.split()[0]
                                if perms.endswith('+'): acls[path] = True
                    except: pass
                
                if args.tags:
                    try:
                        res = subprocess.run(['ls', '-T', '-1', path], 
                                             stdout=subprocess.PIPE, text=True)
                        parts = res.stdout.splitlines()[0].strip().split()
                        if len(parts) >= 4:
                            t_stat[path] = (parts[0], parts[1], parts[2])
                    except Exception: pass
                if args.extattr:
                    try:
                        res = subprocess.run(['extattr', path], 
                                             stdout=subprocess.PIPE, text=True)
                        parts = res.stdout.splitlines()[0].split(None, 4)
                        if len(parts) >= 5: x_stat[path] = parts[:4]
                    except Exception: pass
                
                disp_dsn = ""
                if args.dsn:
                    cur_dsn = get_zfs_dsn(path)
                    if cur_dsn and cur_dsn != prev_file_dsn:
                        disp_dsn = cur_dsn
                        prev_file_dsn = cur_dsn
                fmt_str, vlen = format_entry(
                    path, st, path, path, {}, t_stat, x_stat, acls, args, show_dsn=disp_dsn
                )
                
                if args.long or args.tree or args.oneline:
                    print(fmt_str)
                else:
                    short_items.append((fmt_str, vlen))
                
                p_dict = build_dict(path, st, path, path, {}, t_stat, x_stat, acls, args)
                path_dict["contents"].append(p_dict)
            except OSError:
                print(f"{CMD_NAME}: cannot access '{path}'", file=sys.stderr)
                
        if not (args.long or args.tree or args.oneline):
            print_grid(short_items)
            
        all_json_data.append(path_dict)
        if dir_paths:
            print()

    for i, path in enumerate(dir_paths):
        path_dict = {"target": path, "contents": []}
        
        if len(args.paths) > 1 or args.git or args.tree or args.dsn:
            header = f"{path}"
            if args.dsn:
                dsn = get_zfs_dsn(path)
                if dsn:
                    h_fmt = f"{COLORS['dsn']}[{dsn}]{COLORS['reset']}"
                    header += f" {h_fmt}"
                    path_dict["zfs_dataset"] = dsn
            if args.git:
                branch = get_git_branch(path)
                if branch:
                    b_fmt = f"{COLORS['branch']}\ue0a0 {branch}{COLORS['reset']}"
                    header += f" on {b_fmt}"
                    path_dict["git_branch"] = branch
            print(f"{header}:")
        
        if args.long or args.tree or args.oneline:
            hdr_str = get_header_str(args)
            print(f"\033[1;4m{hdr_str}\033[0m" if args.use_color else hdr_str)
            
        g_stats = get_git_statuses_recursive(path) if args.git else {}
        path_dict["contents"] = process_directory(path, args, g_stats)
        
        all_json_data.append(path_dict)
        if i < len(dir_paths) - 1: print()
            
    if args.json:
        try:
            with open(args.json, 'w') as f: json.dump(all_json_data, f, indent=2)
            print(f"\n[+] Exported directory data to {args.json}")
        except Exception as e:
            print(f"{CMD_NAME}: Failed to write JSON - {e}", file=sys.stderr)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
