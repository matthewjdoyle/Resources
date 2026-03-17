#!/usr/bin/env python3
"""
README Coverage Tool - Scan repo directories and report README.md coverage.
Usage: python3 readme-coverage.py [ROOT] [--depth N] [--missing]
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".env", "dist", "build", ".next", ".nuxt", "target", ".cache",
    ".idea", ".vscode", "__MACOSX", ".DS_Store",
}

# ── ANSI colours ─────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

# ── Rendering helpers ─────────────────────────────────────────────────────────
W = 72

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

# ── Core logic ────────────────────────────────────────────────────────────────
def has_non_hidden_files(dirpath: Path) -> bool:
    """Return True if directory contains at least one non-hidden file."""
    try:
        for entry in dirpath.iterdir():
            if entry.is_file() and not entry.name.startswith("."):
                return True
    except PermissionError:
        pass
    return False

def find_readme(dirpath: Path):
    """Return (readme_path, line_count) if a README.md exists, else (None, 0)."""
    try:
        for entry in dirpath.iterdir():
            if entry.is_file() and entry.name.lower() == "readme.md":
                try:
                    text = entry.read_text(encoding="utf-8", errors="replace")
                    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
                    return entry, lines
                except (PermissionError, OSError):
                    return entry, 0
    except PermissionError:
        pass
    return None, 0

def scan_coverage(root: Path, max_depth=None, missing_only=False) -> list:
    results = []

    for dirpath, dirs, files in os.walk(root):
        current = Path(dirpath)

        # Compute depth relative to root
        try:
            rel = current.relative_to(root)
            depth = len(rel.parts)
        except ValueError:
            depth = 0

        # Skip hidden/ignored dirs
        dirs[:] = sorted([
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ])

        # Check depth limit (depth 0 = root itself)
        if max_depth is not None and depth > max_depth:
            dirs.clear()
            continue

        # Determine if this directory is significant
        is_root = (current == root)
        significant = is_root or has_non_hidden_files(current)
        if not significant:
            continue

        readme_path, line_count = find_readme(current)
        has_readme = readme_path is not None

        if missing_only and has_readme:
            continue

        rel_str = str(rel) if depth > 0 else "."
        # Normalise to forward slashes on Windows
        rel_str = rel_str.replace("\\", "/")

        results.append({
            "rel":        rel_str,
            "depth":      depth,
            "has_readme": has_readme,
            "lines":      line_count,
        })

    return results

def print_results(results, root: Path):
    path_col_w = W - 20  # reserve space for line count

    for r in results:
        rel   = r["rel"]
        lines = r["lines"]

        if r["has_readme"]:
            marker = f"{GREEN}✓{RESET}"
            path_str = f"{GREEN}{rel}{RESET}"

            # Line count hint
            if lines < 5:
                hint = f"  {DIM}(stub){RESET}"
            else:
                hint = f"  {DIM}{lines} lines{RESET}"

            # Pad path to align hints
            # Strip ANSI for length calc
            pad = max(0, path_col_w - len(rel))
            print(f"  {marker}  {path_str}{' ' * pad}{hint}")
        else:
            marker = f"{RED}✗{RESET}"
            path_str = f"{RED}{rel}{RESET}"
            print(f"  {marker}  {path_str}")

def print_summary(results):
    total   = len(results)
    covered = sum(1 for r in results if r["has_readme"])
    missing = total - covered
    ratio   = covered / total if total else 0
    pct     = ratio * 100

    divider()
    b = bar(ratio, width=24)
    pct_str     = f"{CYAN}{pct:.1f}%{RESET}"
    covered_str = f"{CYAN}{covered}{RESET}"
    missing_str = f"{CYAN}{missing}{RESET}"
    total_str   = f"{CYAN}{total}{RESET}"

    print(f"  {YELLOW}Coverage{RESET}  {b}  {covered_str} / {total_str}  {pct_str}")
    print(f"  {GREEN}✓ {covered_str} documented{RESET}   {RED}✗ {missing_str} missing{RESET}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Scan a directory tree and report README.md coverage."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Root directory to scan (default: repo root)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        metavar="N",
        help="Limit scan to N levels deep (default: unlimited)",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="Show only directories missing a README",
    )
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).resolve()
    else:
        root = Path(__file__).parent.parent.resolve()

    if not root.is_dir():
        print(f"{RED}Error: {root} is not a directory.{RESET}", file=sys.stderr)
        sys.exit(1)

    print()
    thick_divider()
    print(f"  {BOLD}README COVERAGE{RESET}  —  {DIM}{root}{RESET}")
    thick_divider()

    results = scan_coverage(root, max_depth=args.depth, missing_only=args.missing)

    qualifier = " missing" if args.missing else ""
    print(f"  {DIM}Scanning {len(results)}{qualifier} directories…{RESET}")
    print()

    print_results(results, root)

    print()
    print_summary(results)
    thick_divider()
    print()

if __name__ == "__main__":
    main()
