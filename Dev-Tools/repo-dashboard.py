#!/usr/bin/env python3
"""
GitHub Repo Dashboard - Terminal report of all repos in this folder.
Usage: python3 repo-dashboard.py
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# ── Language detection map ──────────────────────────────────────────────────
EXT_LANG = {
    ".py": "Python", ".pyw": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
    ".rs": "Rust",
    ".go": "Go",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".r": "R", ".R": "R",
    ".m": "MATLAB",
    ".f90": "Fortran", ".f95": "Fortran", ".f03": "Fortran", ".for": "Fortran",
    ".tex": "LaTeX", ".bib": "LaTeX",
    ".md": "Markdown", ".markdown": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".sql": "SQL",
    ".ipynb": "Jupyter",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".lua": "Lua",
    ".jl": "Julia",
    ".cs": "C#",
    ".dockerfile": "Docker",
    ".nw": "Noweb",
    # Raw text data
    ".csv": "Data", ".tsv": "Data",
    ".dat": "Data", ".data": "Data",
    ".txt": "Data",
    ".log": "Data",
    ".out": "Data",
    ".in":  "Data",
    ".x":   "Data",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".env", "dist", "build", ".next", ".nuxt", "target", ".cache",
    ".idea", ".vscode", "__MACOSX", ".DS_Store",
}

# ── ANSI colours ─────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
BLACK  = "\033[30m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
MAGENTA= "\033[35m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"
BG_DARK= "\033[48;5;236m"

# Per-language colours
LANG_COLOUR = {
    "Python":     "\033[38;5;220m",
    "JavaScript": "\033[38;5;226m",
    "TypeScript": "\033[38;5;75m",
    "HTML":       "\033[38;5;208m",
    "CSS":        "\033[38;5;147m",
    "Rust":       "\033[38;5;202m",
    "Go":         "\033[38;5;87m",
    "C":          "\033[38;5;105m",
    "C++":        "\033[38;5;99m",
    "R":          "\033[38;5;32m",
    "MATLAB":     "\033[38;5;214m",
    "Fortran":    "\033[38;5;153m",
    "Shell":      "\033[38;5;82m",
    "LaTeX":      "\033[38;5;217m",
    "Markdown":   "\033[38;5;252m",
    "JSON":       "\033[38;5;180m",
    "YAML":       "\033[38;5;185m",
    "Jupyter":    "\033[38;5;166m",
    "Julia":      "\033[38;5;134m",
    "Data":       "\033[38;5;109m",
}

def lc(lang):
    return LANG_COLOUR.get(lang, "\033[38;5;250m")

# ── Analysis ──────────────────────────────────────────────────────────────────
def analyse_repo(repo_path: Path):
    lang_lines  = defaultdict(int)
    lang_files  = defaultdict(int)
    total_files = 0
    total_lines = 0
    binary_files = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = Path(root) / fname
            ext   = fpath.suffix.lower()
            lang  = EXT_LANG.get(ext) or EXT_LANG.get(fpath.suffix)

            # Try reading; skip binaries silently
            try:
                text = fpath.read_text(encoding="utf-8", errors="strict")
                lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            except (UnicodeDecodeError, PermissionError, OSError):
                binary_files += 1
                continue

            total_files += 1
            total_lines += lines
            bucket = lang if lang else "Other"
            lang_files[bucket] += 1
            lang_lines[bucket] += lines

    return {
        "lang_lines":   dict(lang_lines),
        "lang_files":   dict(lang_files),
        "total_files":  total_files,
        "total_lines":  total_lines,
        "binary_files": binary_files,
    }

# ── Rendering helpers ─────────────────────────────────────────────────────────
W = 72  # total print width

def divider(char="─", colour=DIM):
    print(f"{colour}{char * W}{RESET}")

def thick_divider(colour=CYAN):
    print(f"{colour}{'═' * W}{RESET}")

def bar(ratio, width=28, filled_char="█", empty_char="░"):
    filled = round(ratio * width)
    return filled_char * filled + DIM + empty_char * (width - filled) + RESET

def fmt_lines(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}k"
    return str(n)

def print_lang_table(lang_lines, lang_files, total_lines, indent="  "):
    if not lang_lines:
        print(f"{indent}{DIM}No source files detected.{RESET}")
        return
    sorted_langs = sorted(lang_lines.items(), key=lambda x: x[1], reverse=True)
    for lang, lines in sorted_langs:
        ratio   = lines / total_lines if total_lines else 0
        pct     = ratio * 100
        files   = lang_files.get(lang, 0)
        b       = bar(ratio, width=24)
        colour  = lc(lang)
        lang_str = f"{colour}{BOLD}{lang:<12}{RESET}"
        pct_str  = f"{colour}{pct:5.1f}%{RESET}"
        lines_str= f"{CYAN}{fmt_lines(lines):>6}{RESET}"
        files_str= f"{DIM}{files:>4} file{'s' if files != 1 else ' '}{RESET}"
        print(f"{indent}{lang_str}  {b}  {pct_str}  {lines_str} lines  {files_str}")

def print_repo_card(name, stats):
    total_l = stats["total_lines"]
    total_f = stats["total_files"]
    binary  = stats["binary_files"]

    thick_divider()
    print(f"  {BOLD}{WHITE}{name}{RESET}")
    divider()
    print(f"  {BOLD}Files:{RESET} {CYAN}{total_f:,}{RESET}  "
          f"{BOLD}Lines:{RESET} {CYAN}{fmt_lines(total_l)}{RESET}  "
          f"{DIM}Binary/skipped: {binary}{RESET}")
    divider(char="·")
    print_lang_table(stats["lang_lines"], stats["lang_files"], total_l)

def print_overall(all_stats, repos):
    thick_divider(colour=YELLOW)
    print(f"  {BOLD}{YELLOW}OVERALL SUMMARY  —  {len(repos)} repositories{RESET}")
    thick_divider(colour=YELLOW)

    agg_lines = defaultdict(int)
    agg_files = defaultdict(int)
    grand_lines = 0
    grand_files = 0
    grand_binary = 0

    for s in all_stats:
        grand_lines  += s["total_lines"]
        grand_files  += s["total_files"]
        grand_binary += s["binary_files"]
        for lang, v in s["lang_lines"].items():
            agg_lines[lang] += v
        for lang, v in s["lang_files"].items():
            agg_files[lang] += v

    print(f"  {BOLD}Total files:{RESET} {CYAN}{grand_files:,}{RESET}   "
          f"{BOLD}Total lines:{RESET} {CYAN}{fmt_lines(grand_lines)}{RESET}   "
          f"{DIM}Binary/skipped: {grand_binary}{RESET}")
    divider(char="─", colour=YELLOW)
    print_lang_table(dict(agg_lines), dict(agg_files), grand_lines)

    # Top 5 repos by lines
    ranked = sorted(zip(repos, all_stats), key=lambda x: x[1]["total_lines"], reverse=True)
    divider(char="·", colour=YELLOW)
    print(f"  {BOLD}Largest repos by lines of code:{RESET}")
    for i, (name, s) in enumerate(ranked[:5], 1):
        ratio = s["total_lines"] / grand_lines if grand_lines else 0
        b     = bar(ratio, width=20)
        print(f"  {DIM}{i}.{RESET} {WHITE}{BOLD}{name:<40}{RESET}  {b}  "
              f"{CYAN}{fmt_lines(s['total_lines']):>7}{RESET}")

    thick_divider(colour=YELLOW)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    root = Path(__file__).parent.resolve()
    repos = sorted(
        [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")],
        key=lambda p: p.name.lower(),
    )

    print()
    thick_divider(colour=MAGENTA)
    print(f"  {BOLD}{MAGENTA}GITHUB REPO DASHBOARD{RESET}  {DIM}{root}{RESET}")
    thick_divider(colour=MAGENTA)
    print(f"  {DIM}Scanning {len(repos)} repositories…{RESET}")
    print()

    all_stats = []
    for repo in repos:
        sys.stdout.write(f"  {DIM}  → {repo.name:<50}\r{RESET}")
        sys.stdout.flush()
        stats = analyse_repo(repo)
        all_stats.append(stats)
        # Only print repos with actual code
        if stats["total_files"] > 0:
            print_repo_card(repo.name, stats)

    print()
    print_overall(all_stats, [r.name for r in repos])
    print()

if __name__ == "__main__":
    main()
