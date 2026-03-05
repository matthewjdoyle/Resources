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
    ".mod": "Fortran",
    ".tex": "LaTeX", ".bib": "LaTeX",
    ".aux": "LaTeX", ".fls": "LaTeX", ".fdb_latexmk": "LaTeX",
    ".bbl": "LaTeX", ".sty": "LaTeX", ".blg": "LaTeX",
    ".cls": "LaTeX", ".toc": "LaTeX", ".lof": "LaTeX", ".listing": "LaTeX",
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
    # Build / config
    ".bat": "Make",
    # Text data – subdivided
    ".csv": "CSV/TSV", ".tsv": "CSV/TSV",
    ".log": "Log", ".out": "Log",
    ".txt": "Text Data", ".dat": "Text Data", ".data": "Text Data",
    ".in":  "Text Data", ".x": "Text Data",
    # SVG is text-readable but semantically an image
    ".svg": "Image",
}

# ── Filename-based detection (no extension) ─────────────────────────────────
FNAME_LANG = {
    "Makefile": "Make",
    "Dockerfile": "Docker",
    ".gitignore": "Git",
    ".gitattributes": "Git",
}

# ── Binary file type detection ──────────────────────────────────────────────
EXT_BINARY = {
    ".png": "Image", ".jpg": "Image", ".jpeg": "Image", ".gif": "Image",
    ".bmp": "Image", ".webp": "Image", ".ico": "Image",
    ".tiff": "Image", ".tif": "Image",
    ".mp4": "Video", ".mov": "Video", ".avi": "Video",
    ".mkv": "Video", ".webm": "Video", ".flv": "Video",
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".ogg": "Audio", ".aac": "Audio", ".m4a": "Audio",
    ".pdf": "PDF",
    ".ttf": "Font", ".otf": "Font", ".woff": "Font", ".woff2": "Font",
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
    "CSV/TSV":    "\033[38;5;109m",
    "Log":        "\033[38;5;245m",
    "Text Data":  "\033[38;5;144m",
    "Image":      "\033[38;5;176m",
    "Video":      "\033[38;5;204m",
    "Audio":      "\033[38;5;141m",
    "PDF":        "\033[38;5;203m",
    "Font":       "\033[38;5;223m",
    "Make":       "\033[38;5;178m",
    "Git":        "\033[38;5;209m",
}

def lc(lang):
    return LANG_COLOUR.get(lang, "\033[38;5;250m")

# ── Analysis ──────────────────────────────────────────────────────────────────
def analyse_repo(repo_path: Path):
    lang_lines  = defaultdict(int)
    lang_files  = defaultdict(int)
    ext_detail  = defaultdict(lambda: defaultdict(lambda: {"files": 0, "lines": 0}))
    total_files = 0
    total_lines = 0
    binary_files = 0
    binary_cat_files = defaultdict(int)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = Path(root) / fname
            ext   = fpath.suffix.lower()
            lang  = EXT_LANG.get(ext) or EXT_LANG.get(fpath.suffix) or FNAME_LANG.get(fname)

            # Try reading; categorise binaries by type
            try:
                text = fpath.read_text(encoding="utf-8", errors="strict")
                lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
            except (UnicodeDecodeError, PermissionError, OSError):
                binary_files += 1
                bcat = EXT_BINARY.get(ext)
                if bcat:
                    binary_cat_files[bcat] += 1
                continue

            total_files += 1
            total_lines += lines
            bucket = lang if lang else "Other"
            lang_files[bucket] += 1
            lang_lines[bucket] += lines
            if bucket in ("Other", "Log"):
                key = fpath.suffix if fpath.suffix else fname
                ext_detail[bucket][key]["files"] += 1
                ext_detail[bucket][key]["lines"] += lines

    return {
        "lang_lines":      dict(lang_lines),
        "lang_files":      dict(lang_files),
        "total_files":     total_files,
        "total_lines":     total_lines,
        "binary_files":    binary_files,
        "binary_cat_files": dict(binary_cat_files),
        "ext_detail":      {k: dict(v) for k, v in ext_detail.items()},
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

def print_lang_table(lang_lines, lang_files, total_lines, binary_cat_files=None, total_files_all=0, indent="  "):
    if not lang_lines and not binary_cat_files:
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

    # Binary asset rows
    if binary_cat_files:
        total_binary = sum(binary_cat_files.values())
        print(f"{indent}{DIM}{'·' * 58}{RESET}")
        sorted_bcats = sorted(binary_cat_files.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_bcats:
            ratio  = count / total_binary if total_binary else 0
            b      = bar(ratio, width=24)
            colour = lc(cat)
            cat_str  = f"{colour}{BOLD}{cat:<12}{RESET}"
            cnt_str  = f"{CYAN}{count:>6}{RESET}"
            print(f"{indent}{cat_str}  {b}  {DIM}binary{RESET}  {cnt_str} files")

def print_ext_breakdown(label, agg_ext, colour_code):
    """Print a breakdown of file extensions within a category."""
    if not agg_ext:
        return
    total_files = sum(d["files"] for d in agg_ext.values())
    total_lines = sum(d["lines"] for d in agg_ext.values())
    sorted_exts = sorted(((e, d) for e, d in agg_ext.items() if d["lines"] > 0),
                         key=lambda x: x[1]["lines"], reverse=True)
    print(f"  {colour_code}{BOLD}{label}{RESET} breakdown  "
          f"{DIM}({total_files} file{'s' if total_files != 1 else ''}, "
          f"{fmt_lines(total_lines)} lines){RESET}")
    for ext, d in sorted_exts:
        ratio = d["lines"] / total_lines if total_lines else 0
        b     = bar(ratio, width=20)
        print(f"    {DIM}{ext:<16}{RESET}  {b}  "
              f"{CYAN}{fmt_lines(d['lines']):>6}{RESET} lines  "
              f"{DIM}{d['files']:>4} file{'s' if d['files'] != 1 else ' '}{RESET}")

def print_repo_card(name, stats):
    total_l  = stats["total_lines"]
    total_f  = stats["total_files"]
    binary   = stats["binary_files"]
    bcat     = stats.get("binary_cat_files", {})
    cat_bin  = sum(bcat.values())
    uncat    = binary - cat_bin

    thick_divider()
    print(f"  {BOLD}{WHITE}{name}{RESET}")
    divider()
    print(f"  {BOLD}Files:{RESET} {CYAN}{total_f:,}{RESET}  "
          f"{BOLD}Lines:{RESET} {CYAN}{fmt_lines(total_l)}{RESET}  "
          f"{DIM}Binary: {binary}"
          f"{f' (unrecognised: {uncat})' if uncat else ''}{RESET}")
    divider(char="·")
    print_lang_table(stats["lang_lines"], stats["lang_files"], total_l,
                     binary_cat_files=bcat, total_files_all=total_f)

def print_overall(all_stats, repos):
    thick_divider(colour=YELLOW)
    print(f"  {BOLD}{YELLOW}OVERALL SUMMARY  —  {len(repos)} repositories{RESET}")
    thick_divider(colour=YELLOW)

    agg_lines = defaultdict(int)
    agg_files = defaultdict(int)
    agg_bcat  = defaultdict(int)
    agg_ext_detail = defaultdict(lambda: defaultdict(lambda: {"files": 0, "lines": 0}))
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
        for cat, v in s.get("binary_cat_files", {}).items():
            agg_bcat[cat] += v
        for cat, exts in s.get("ext_detail", {}).items():
            for ext, d in exts.items():
                agg_ext_detail[cat][ext]["files"] += d["files"]
                agg_ext_detail[cat][ext]["lines"] += d["lines"]

    print(f"  {BOLD}Total files:{RESET} {CYAN}{grand_files:,}{RESET}   "
          f"{BOLD}Total lines:{RESET} {CYAN}{fmt_lines(grand_lines)}{RESET}   "
          f"{DIM}Binary: {grand_binary}{RESET}")
    divider(char="─", colour=YELLOW)
    print_lang_table(dict(agg_lines), dict(agg_files), grand_lines,
                     binary_cat_files=dict(agg_bcat), total_files_all=grand_files)

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

    # Extension breakdowns for Log and Other
    if agg_ext_detail.get("Log") or agg_ext_detail.get("Other"):
        print()
        for cat in ("Log", "Other"):
            if agg_ext_detail.get(cat):
                print_ext_breakdown(cat, dict(agg_ext_detail[cat]), lc(cat))
                print()

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
