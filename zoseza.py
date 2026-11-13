#!/usr/bin/env python3
import os
import sys
import stat
import argparse
import subprocess
import shutil
import json
from datetime import datetime

# ANSI Color Codes
COLORS = {
    'reset': '\033[0m', 'dir': '\033[1;34m', 'exe': '\033[1;32m',       
    'symlink': '\033[1;36m', 'file': '\033[0m', 'size': '\033[1;32m',      
    'time': '\033[34m', 'perms': '\033[33m', 'user': '\033[33m',        
    'group': '\033[33m', 'git_clean': '\033[90m', 'git_mod': '\033[33m',     
    'git_add': '\033[32m', 'git_untracked': '\033[31m',
    'branch': '\033[36m', 'tree_line': '\033[90m', 'tags': '\033[35m'
}

ICONS = {
    'dir': '', 'symlink': '', 'exe': '', 'py': '󰌠',
    'rex': '󱁤', 'rexx': '󱁤', 'sh': '', 'txt': '',
    'md': '', 'jcl': '󰧮', 'c': '', 'cpp': '',
    'h': '', 'json': '', 'xml': '󰗀', 'csv': '󰈙',
    'zip': '', 'tar': '', 'gz': '', 'default': ''
}

def parse_ls_colors():
    ls_colors = os.environ.get('LS_COLORS', '')
    if not ls_colors: return
    mapping = {'di': 'dir', 'ex': 'exe', 'ln': 'symlink', 'fi': 'file'}
    for part in ls_colors.split(':'):
        if '=' in part:
            key, val = part.split('=', 1)
            if key in mapping:
                COLORS[mapping[key]] = f'\033[{val}m'

def get_icon(filename, mode):
    if stat.S_ISDIR(mode): return ICONS['dir']
    if stat.S_ISLNK(mode): return ICONS['symlink']
    if mode & stat.S_IXUSR or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
        return ICONS['exe']
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ICONS.get(ext, ICONS['default'])

def get_owner_name(uid, gid):
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
    """Fetches z/OS file tags using ls -T"""
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

def format_git_badge(status):
    if not status: return f"{COLORS['git_clean']}--{COLORS['reset']}"
    if '?' in status: color = COLORS['git_untracked']
    elif 'M' in status or 'R' in status: color = COLORS['git_mod']
    elif 'A' in status: color = COLORS['git_add']
    else: color = COLORS['git_mod']
    return f"{color}{status:<2}{COLORS['reset']}"

def format_tag_badge(tag_info):
    if not tag_info: return ""
    state, codeset, _ = tag_info
    return f"{COLORS['tags']}{state} {codeset:<10}{COLORS['reset']} "

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

def build_dict(entry, st, rel_path, git_statuses, zos_tags, args):
    size = int(st.st_blocks * 512) if (
        args.blocks and hasattr(st, 'st_blocks')
    ) else int(st.st_size)
    
    user, group = get_owner_name(st.st_uid, st.st_gid)
    data = {
        "name": entry, "path": rel_path, "size_bytes": size,
        "permissions": stat.filemode(st.st_mode), "links": st.st_nlink,
        "owner": user, "group": group, "mtime": st.st_mtime
    }
    
    if stat.S_ISDIR(st.st_mode): data["type"] = "dir"
    elif stat.S_ISLNK(st.st_mode): data["type"] = "symlink"
    else: data["type"] = "file"
    
    git_key = rel_path if args.tree else entry.split('/')[0]
    if args.git and git_key in git_statuses:
        data["git_status"] = git_statuses[git_key]
        
    tag_info = zos_tags.get(entry)
    if args.tags and tag_info:
        data["tag_state"] = tag_info[0]
        data["tag_codeset"] = tag_info[1]
        
    return data

def format_entry(entry, st, rel_path, git_statuses, zos_tags, args, tree_prefix=""):
    color = get_color(st.st_mode)
    icon = f"{get_icon(entry, st.st_mode)} " if args.icons else ""
    
    git_key = rel_path if args.tree else entry.split('/')[0]
    badge = format_git_badge(git_statuses.get(git_key))
    git_badge = f"{badge} " if args.git else ""
    tag_badge = format_tag_badge(zos_tags.get(entry)) if args.tags else ""
    
    if args.long:
        perms = stat.filemode(st.st_mode)
        links = st.st_nlink
        user, group = get_owner_name(st.st_uid, st.st_gid)
        size_str = format_size(st, use_blocks=args.blocks)
        mtime = datetime.fromtimestamp(st.st_mtime).strftime('%b %d %H:%M')
        
        out = f"{COLORS['perms']}{perms}{COLORS['reset']} "
        out += f"{links:2} "
        out += f"{COLORS['user']}{user:<8}{COLORS['reset']} "
        out += f"{COLORS['group']}{group:<8}{COLORS['reset']} "
        out += f"{COLORS['size']}{size_str:>5}{COLORS['reset']} "
        out += f"{COLORS['time']}{mtime}{COLORS['reset']} "
        out += f"{git_badge}"
        out += f"{tag_badge}"
        out += f"{COLORS['tree_line']}{tree_prefix}{COLORS['reset']}"
        out += f"{color}{icon}{entry}{COLORS['reset']}"
        return out, 0
    else:
        out = f"{git_badge}"
        out += f"{tag_badge}"
        out += f"{COLORS['tree_line']}{tree_prefix}{COLORS['reset']}"
        out += f"{color}{icon}{entry}{COLORS['reset']}"
        
        vlen = 3 if args.git else 0
        vlen += 13 if (args.tags and tag_badge) else 0
        vlen += len(tree_prefix)
        vlen += 2 if args.icons else 0
        vlen += len(entry)
        return out, vlen

def process_directory(target_dir, args, git_statuses, 
                      prefix="", rel_base="", is_root=True):
    contents = []
    try:
        raw_entries = os.listdir(target_dir)
    except PermissionError:
        msg = f"{prefix}pyeza: permission denied '{target_dir}'"
        print(msg, file=sys.stderr)
        return contents

    if not args.all:
        raw_entries = [e for e in raw_entries if not e.startswith('.')]

    zos_tags = get_zos_tags(target_dir) if args.tags else {}

    entries_with_stats = []
    for entry in raw_entries:
        path = os.path.join(target_dir, entry)
        try:
            st = os.lstat(path)
            if args.allowed_exts and not stat.S_ISDIR(st.st_mode):
                if not entry.lower().endswith(args.allowed_exts):
                    continue
            entries_with_stats.append((entry, st, path))
        except OSError: continue

    if args.sort_size:
        entries_with_stats.sort(key=lambda x: x[1].st_size, reverse=not args.reverse)
    elif args.time:
        entries_with_stats.sort(key=lambda x: x[1].st_mtime, reverse=not args.reverse)
    else:
        entries_with_stats.sort(key=lambda x: x[0].lower(), reverse=args.reverse)

    short_items = []
    for i, (entry, st, path) in enumerate(entries_with_stats):
        is_last = (i == len(entries_with_stats) - 1)
        rel_path = os.path.join(rel_base, entry) if rel_base else entry
        
        tree_connector = "└── " if (args.tree and is_last) else "├── " if args.tree else ""
        
        full_prefix = prefix + tree_connector
        fmt_str, vis_len = format_entry(
            entry, st, rel_path, git_statuses, zos_tags, args, tree_prefix=full_prefix
        )
        
        if args.long or args.tree or args.oneline: print(fmt_str)
        else: short_items.append((fmt_str, vis_len))
            
        item_data = build_dict(entry, st, rel_path, git_statuses, zos_tags, args)
            
        if args.tree and stat.S_ISDIR(st.st_mode):
            extension = "    " if is_last else "│   "
            children = process_directory(
                path, args, git_statuses, prefix + extension, 
                rel_path, is_root=False
            )
            item_data["children"] = children
            
        contents.append(item_data)

    if not (args.long or args.tree or args.oneline) and is_root:
        print_grid(short_items)
        
    return contents

def main():
    parse_ls_colors()
    
    parser = argparse.ArgumentParser(description="Python eza clone for z/OS")
    parser.add_argument('paths', nargs='*', default=['.'])
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('-l', '--long', action='store_true')
    parser.add_argument('-g', '--git', action='store_true')
    parser.add_argument('-t', '--time', action='store_true')
    parser.add_argument('-i', '--icons', action='store_true')
    parser.add_argument('-b', '--blocks', action='store_true')
    parser.add_argument('-J', '--json', metavar='FILE')
    parser.add_argument('-e', '--ext', metavar='EXT')
    
    # Restored standard z/OS behavior
    parser.add_argument('-T', '--tags', action='store_true',
                        help='Show z/OS file tags (EBCDIC/ASCII)')
    parser.add_argument('--tree', action='store_true',
                        help='Recurse into directories as a tree')
    
    parser.add_argument('-d', '--directory', action='store_true')
    parser.add_argument('-S', '--sort-size', action='store_true')
    parser.add_argument('-r', '--reverse', action='store_true')
    parser.add_argument('-1', '--oneline', action='store_true')
    
    args = parser.parse_args()
    
    if args.ext:
        exts = [x.lower().strip() for x in args.ext.split(',')]
        args.allowed_exts = tuple(x if x.startswith('.') else '.' + x for x in exts)
    else:
        args.allowed_exts = ()
        
    all_json_data = []

    for i, path in enumerate(args.paths):
        path_dict = {"target": path, "contents": []}
        
        if (len(args.paths) > 1 or args.git or args.tree) and not args.directory:
            header = f"{path}"
            if args.git and os.path.isdir(path):
                branch = get_git_branch(path)
                if branch:
                    b_fmt = f"{COLORS['branch']} {branch}{COLORS['reset']}"
                    header += f" on {b_fmt}"
                    path_dict["git_branch"] = branch
            print(f"{header}:")
        
        if os.path.isdir(path) and not args.directory:
            g_stats = get_git_statuses_recursive(path) if args.git else {}
            path_dict["contents"] = process_directory(path, args, g_stats)
        else:
            try:
                st = os.lstat(path)
                t_stat = {}
                if args.tags:
                    try:
                        res = subprocess.run(['ls', '-T', '-1', path], 
                                             stdout=subprocess.PIPE, text=True)
                        parts = res.stdout.splitlines()[0].strip().split()
                        if len(parts) >= 4:
                            t_stat[path] = (parts[0], parts[1], parts[2])
                    except Exception: pass
                fmt_str, _ = format_entry(path, st, path, {}, t_stat, args)
                print(fmt_str)
                path_dict["contents"].append(build_dict(path, st, path, {}, t_stat, args))
            except OSError:
                print(f"pyeza: cannot access '{path}': No such file", file=sys.stderr)
        
        all_json_data.append(path_dict)
        if i < len(args.paths) - 1: print()
            
    if args.json:
        try:
            with open(args.json, 'w') as f: json.dump(all_json_data, f, indent=2)
            print(f"\n[+] Exported directory data to {args.json}")
        except Exception as e:
            print(f"pyeza: Failed to write JSON - {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
