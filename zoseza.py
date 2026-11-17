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
  -d, --directory       List directories themselves, not their contents.
  -S, --sort-size       Sort files by size (largest first).
  -r, --reverse         Reverse the current sort order.
  -1, --oneline         Display one entry per line.
  -D, --dsn             Show underlying zFS dataset names for directories and symlinks.
  --color WHEN          When to use terminal colors: auto, always, never (default: auto).
  --no-color            Disable all terminal colors (alias for --color=never).
  --tui                 Launch the interactive fullscreen Text User Interface.

TUI Hotkeys:
  UP/DOWN : Navigate              s/t/a/C : Sort (Size/MTime/ATime/CTime)
  ENTER   : Open Dir/File         n/r     : Sort (Name/Reverse)
  ESC     : Go up one dir         f or /  : Filter by string
  e       : Edit file             c       : Clear filter
  D/R/C   : Delete/Rename/Copy    I/O/N   : Toggle Inode/Octal/Numeric IDs
  q       : Quit                  F1      : Show help tutorial
  o       : Open settings

Change History:
  2026-11-17: Added --color (auto/always/never) and --no-color CLI options.
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
        'color_def': curses.COLOR_WHITE
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
        out += f"{'Permissions':<11} "
        out += f"{'Ln':>2} "
        out += f"{'User':<8} "
        out += f"{'Group':<8} "
        out += f"{'Size':>5} "
        
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
                 t_pfx="", force_long=False):
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
        dsn_val = get_zfs_dsn(path)
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
        out += f"{COLORS['perms']}{perms}{COLORS['reset']} "
        out += f"{links:2} "
        out += f"{COLORS['user']}{user:<8}{COLORS['reset']} "
        out += f"{COLORS['group']}{group:<8}{COLORS['reset']} "
        out += f"{COLORS['size']}{size_str:>5}{COLORS['reset']} "
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

def process_directory(target_dir, args, g_stats, prefix="", r_base="", root=True):
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
        
    if args.reverse and not args.sort_size and not args.time:
        entries_with_stats = files + dots
    else:
        entries_with_stats = dots + files

    short_items = []
    for i, (entry, st, path) in enumerate(entries_with_stats):
        is_last = (i == len(entries_with_stats) - 1)
        rel_path = os.path.join(r_base, entry) if r_base else entry
        t_conn = "\u2514\u2500\u2500 " if (args.tree and is_last) else "\u251c\u2500\u2500 " if args.tree else ""
        
        full_prefix = prefix + t_conn
        fmt_str, vlen = format_entry(
            entry, st, path, rel_path, g_stats, zos_tags, x_stats, acls, 
            args, t_pfx=full_prefix
        )
        
        if args.long or args.tree or args.oneline: print(fmt_str)
        else: short_items.append((fmt_str, vlen))
            
        item_data = build_dict(
            entry, st, path, rel_path, g_stats, zos_tags, x_stats, acls, args
        )
            
        if args.tree and stat.S_ISDIR(st.st_mode) and entry != '..':
            extension = "    " if is_last else "\u2502   "
            children = process_directory(
                path, args, g_stats, prefix + extension, rel_path, root=False
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

def get_confirm(stdscr, y, w, prompt):
    stdscr.addstr(y, 0, prompt.ljust(w-1)[:w-1], curses.A_REVERSE)
    k = stdscr.getch()
    return k in (ord('y'), ord('Y'))

def show_help(stdscr, title, lines):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    
    hdr = f" {title} Help (Tutorial) | Press any key to return "
    stdscr.addstr(0, 0, hdr.ljust(w-1)[:w-1], curses.A_REVERSE)
    
    for i, line in enumerate(lines):
        if i + 2 < h - 1:
            stdscr.addstr(i + 2, 2, line[:w-4])
            
    ftr = " Press any key to close "
    stdscr.addstr(h - 1, 0, ftr.ljust(w-1)[:w-1], curses.A_REVERSE)
    stdscr.getch()

def settings_menu(stdscr, config):
    color_names = ['BLK', 'RED', 'GRN', 'YEL', 'BLU', 'MAG', 'CYN', 'WHT']
    sel_idx = 0
    opts = ['editor', 'color_dir', 'color_exe', 'color_sym', 'color_def']
    labels = ['Default Editor', 'Dir Color', 'Exe Color', 'Sym Color', 'Def Text']
    
    help_lines = [
        "UP/DOWN       : Move selection",
        "LEFT/RIGHT    : Cycle through available colors",
        "ENTER         : Edit the text value (Editor)",
        "s             : Save config to ~/.pyeza.json and exit",
        "ESC           : Go back to directory browser without saving",
        "q             : Quit menu without saving"
    ]
    
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        
        hdr = f" {CMD_NAME} Settings | UP/DN: Sel | L/R: Color | s: Save | F1: Help | q: Quit "
        stdscr.addstr(0, 0, hdr.ljust(w-1)[:w-1], curses.A_REVERSE)
        
        for i, opt in enumerate(opts):
            val = config[opt]
            val_str = color_names[val] if opt.startswith('color_') else str(val)
            display = f" {labels[i].ljust(15)} : {val_str}"
            attr = curses.A_REVERSE if i == sel_idx else curses.A_NORMAL
            stdscr.addstr(i + 2, 2, display[:w-4], attr)
            
        stdscr.nodelay(True)
        k = stdscr.getch()
        stdscr.nodelay(False)
        
        if k == -1: k = stdscr.getch()
            
        if k == 27: 
            stdscr.nodelay(True)
            k2 = stdscr.getch()
            stdscr.nodelay(False)
            if k2 == -1: return None 
            else: curses.ungetch(k2)
            
        if k == curses.KEY_F1: show_help(stdscr, "Settings", help_lines)
        elif k == ord('q'): return None
        elif k == ord('s'): return config
        elif k == curses.KEY_UP: sel_idx = max(0, sel_idx - 1)
        elif k == curses.KEY_DOWN: sel_idx = min(len(opts) - 1, sel_idx + 1)
        elif k == curses.KEY_RIGHT and opts[sel_idx].startswith('color_'):
            config[opts[sel_idx]] = (config[opts[sel_idx]] + 1) % 8
        elif k == curses.KEY_LEFT and opts[sel_idx].startswith('color_'):
            config[opts[sel_idx]] = (config[opts[sel_idx]] - 1) % 8
        elif k in (curses.KEY_ENTER, 10, 13) and opts[sel_idx] == 'editor':
            new_ed = get_input(stdscr, h-1, w, " New Editor Command: ")
            if new_ed: config['editor'] = new_ed

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

def view_file(stdscr, path):
    try:
        with open(path, 'r', errors='replace') as f:
            lines = [line.rstrip('\n') for line in f]
    except Exception as e:
        lines = [f"Error reading file {path}: {e}"]

    help_lines = [
        "UP/DOWN       : Scroll line by line",
        "PgUp/PgDn     : Scroll by page",
        "/             : Open search prompt at bottom",
        "n             : Jump to next search match",
        "ESC           : Go back to directory browser",
        "q             : Go back to directory browser"
    ]

    top, query = 0, ""
    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        
        for i in range(h - 1):
            if top + i < len(lines):
                stdscr.addstr(i, 0, lines[top + i][:w-1])
                
        stat_b = f" {path} | UP/DN: Scroll | /: Find | n: Next | F1: Help | q: Quit "
        stdscr.addstr(h - 1, 0, stat_b[:w-1].ljust(w-1), curses.A_REVERSE)
        
        stdscr.nodelay(True)
        k = stdscr.getch()
        stdscr.nodelay(False)
        
        if k == -1: k = stdscr.getch()
            
        if k == 27: 
            stdscr.nodelay(True)
            k2 = stdscr.getch()
            stdscr.nodelay(False)
            if k2 == -1: break
            else: curses.ungetch(k2)
            
        if k == curses.KEY_F1: show_help(stdscr, "File Viewer", help_lines)
        elif k == ord('q'): break
        elif k == curses.KEY_UP: top = max(0, top - 1)
        elif k == curses.KEY_DOWN: top = min(max(0, len(lines) - h + 1), top + 1)
        elif k == curses.KEY_PPAGE: top = max(0, top - (h - 2))
        elif k == curses.KEY_NPAGE: top = min(max(0, len(lines) - h + 1), top + (h - 2))
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
    
    items = []
    g_stats, tags, x_stats, acls = {}, {}, {}, {}
    
    help_lines = [
        "Navigation:",
        "  UP/DOWN      : Move cursor",
        "  ENTER        : Open Directory or File",
        "  ESC          : Go up one directory",
        "",
        "File Operations:",
        "  e            : Edit file (vi, etc)",
        "  D            : Delete file/dir",
        "  R            : Rename file/dir",
        "  C            : Copy file/dir",
        "",
        "Sorting & Filtering:",
        "  s            : Sort Size",
        "  t            : Sort MTime (Modified)",
        "  a            : Sort ATime (Accessed)",
        "  C            : Sort CTime (Changed)",
        "  n            : Sort Name",
        "  r            : Reverse Sort",
        "  f or /       : Filter by string",
        "  c            : Clear filter",
        "",
        "View Toggles:",
        "  I            : Toggle Inode visibility",
        "  O            : Toggle Octal permissions",
        "  N            : Toggle Numeric UIDs/GIDs",
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
            raw_files.sort(key=lambda x: (-x[1].st_size if not sort_rev else x[1].st_size))
        elif sort_by == 'time':
            raw_files.sort(key=lambda x: (-x[1].st_mtime if not sort_rev else x[1].st_mtime))
        elif sort_by == 'atime':
            raw_files.sort(key=lambda x: (-x[1].st_atime if not sort_rev else x[1].st_atime))
        elif sort_by == 'ctime':
            raw_files.sort(key=lambda x: (-x[1].st_ctime if not sort_rev else x[1].st_ctime))
        else:
            raw_files.sort(key=lambda x: (x[0].lower() if not sort_rev else -ord(x[0][0])))
            
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
        
        hdr += f" | Sort: {sort_by.upper()}{' (Rev)' if sort_rev else ''}"
        if current_filter or (explicit_files and current_dir == initial_dir): 
            f_str = current_filter if current_filter else "[Explicit Glob]"
            hdr += f" | Flt: '{f_str}'"
        stdscr.addstr(0, 0, hdr[:w-1].ljust(w-1), curses.A_REVERSE)
        
        col_hdr = get_header_str(args, force_long=True)
        stdscr.addstr(1, 0, col_hdr[:w-1].ljust(w-1), curses.A_BOLD)
        stdscr.addstr(2, 0, "\u2500" * (w-1), curses.A_NORMAL)
        
        for i in range(list_h):
            if top_idx + i < len(items):
                entry, st, path = items[top_idx + i]
                if not st: 
                    stdscr.addstr(i + 3, 0, entry, curses.A_NORMAL)
                    continue
                    
                ansi_str, _ = format_entry(
                    entry, st, path, entry, g_stats, tags, x_stats, acls, args, force_long=True
                )
                addstr_ansi(stdscr, i + 3, 0, ansi_str, (top_idx + i == sel_idx), w)
                
        ftr = " q:Quit o:Opt D,R,C:Ops s,t,a,C,n,r:Srt I,O,N:Tgls f,c:Flt F1:Help "
        stdscr.addstr(h - 1, 0, ftr.ljust(w-1)[:w-1], curses.A_REVERSE)
        
        stdscr.nodelay(True)
        k = stdscr.getch()
        stdscr.nodelay(False)
        
        if k == -1: k = stdscr.getch()
            
        if k == 27: 
            stdscr.nodelay(True)
            k2 = stdscr.getch()
            stdscr.nodelay(False)
            if k2 == -1: 
                if current_dir != '/':
                    current_dir = os.path.dirname(current_dir)
                    current_filter = ""
                    prev_dir = None
            else: curses.ungetch(k2)
                
        elif k == curses.KEY_F1:
            show_help(stdscr, "Browser", help_lines)
            prev_dir = None 
        elif k == ord('q'): break
        elif k == curses.KEY_UP: sel_idx -= 1
        elif k == curses.KEY_DOWN: sel_idx += 1
        elif k == ord('s'): sort_by = 'size'
        elif k == ord('t'): sort_by = 'time'; args.access = False; args.ctime = False
        elif k == ord('a'): sort_by = 'atime'; args.access = True; args.ctime = False
        elif k == ord('C'): sort_by = 'ctime'; args.access = False; args.ctime = True
        elif k == ord('n'): sort_by = 'name'
        elif k == ord('r'): sort_rev = not sort_rev
        elif k == ord('I'): args.inode = not args.inode
        elif k == ord('O'): args.octal = not args.octal
        elif k == ord('N'): args.numeric = not args.numeric
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
                if get_confirm(stdscr, h-1, w, f" Delete {sel[0]}? (y/N): "):
                    try:
                        if stat.S_ISDIR(sel[1].st_mode): shutil.rmtree(sel[2])
                        else: os.remove(sel[2])
                        prev_dir = None
                    except Exception as e:
                        stdscr.addstr(h-1, 0, f" Err: {e} "[:w-1].ljust(w-1), curses.A_REVERSE)
                        stdscr.getch()
        elif k == ord('R'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                new_n = get_input(stdscr, h-1, w, f" Rename {sel[0]} to: ")
                if new_n:
                    try:
                        os.rename(sel[2], os.path.join(current_dir, new_n))
                        prev_dir = None
                    except Exception as e:
                        stdscr.addstr(h-1, 0, f" Err: {e} "[:w-1].ljust(w-1), curses.A_REVERSE)
                        stdscr.getch()
        elif k == ord('C'):
            sel = items[sel_idx]
            if sel[1] and sel[0] != '..':
                new_n = get_input(stdscr, h-1, w, f" Copy {sel[0]} to: ")
                if new_n:
                    try:
                        dst = os.path.join(current_dir, new_n)
                        if stat.S_ISDIR(sel[1].st_mode): shutil.copytree(sel[2], dst)
                        else: shutil.copy2(sel[2], dst)
                        prev_dir = None
                    except Exception as e:
                        stdscr.addstr(h-1, 0, f" Err: {e} "[:w-1].ljust(w-1), curses.A_REVERSE)
                        stdscr.getch()
        elif k == ord('o'):
            new_cfg = settings_menu(stdscr, dict(config))
            if new_cfg:
                config = new_cfg
                save_config(config)
                if use_tui_color:
                    apply_curses_colors(config)
                    sync_ansi_colors(config)
                prev_dir = None 
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
    parser.add_argument('--tree', action='store_true')
    parser.add_argument('-d', '--directory', action='store_true')
    parser.add_argument('-S', '--sort-size', action='store_true')
    parser.add_argument('-r', '--reverse', action='store_true')
    parser.add_argument('-1', '--oneline', action='store_true')
    parser.add_argument('-D', '--dsn', action='store_true', help="Show underlying zFS dataset names")
    parser.add_argument('--color', choices=['auto', 'always', 'never'], default='auto',
                        help="When to use terminal colors (auto, always, never)")
    parser.add_argument('--no-color', action='store_true',
                        help="Disable all terminal colors (same as --color=never)")
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
                
                fmt_str, vlen = format_entry(
                    path, st, path, path, {}, t_stat, x_stat, acls, args
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

