# -*- coding: utf-8 -*-
"""
    compare.py
    ==========
    Run both vectorization backends (custom and vtracer) on a single input
    image and print a side-by-side comparison table of file size and time.

    Usage:
        python compare.py INPUT [--out-dir DIR]

    Example:
        python compare.py test-images/test-image-eyes.jpg
        python compare.py test-images/test-image-flowers.jpg --out-dir /tmp/cmp/
"""

import argparse
import sys
import time
from pathlib import Path

from vectorize import vectorize, vectorize_vtracer


def _human_size(n_bytes: int) -> str:
    if n_bytes >= 1024 * 1024:
        return f"{n_bytes / 1024 / 1024:.1f} MB"
    return f"{n_bytes / 1024:.1f} KB"


def run_comparison(input_path: str, out_dir: str) -> None:
    src = Path(input_path)
    if not src.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stem = src.stem
    custom_out  = str(out / f"{stem}-custom.svg")
    vtracer_out = str(out / f"{stem}-vtracer.svg")

    results = []

    # ── custom backend ───────────────────────────────────────────────────────
    t0 = time.perf_counter()
    vectorize(input_path=input_path, output_path=custom_out)
    elapsed_custom = time.perf_counter() - t0
    size_custom = Path(custom_out).stat().st_size
    results.append(("custom",  custom_out,  size_custom,  elapsed_custom))

    # ── vtracer backend ──────────────────────────────────────────────────────
    t0 = time.perf_counter()
    vectorize_vtracer(input_path=input_path, output_path=vtracer_out)
    elapsed_vtracer = time.perf_counter() - t0
    size_vtracer = Path(vtracer_out).stat().st_size
    results.append(("vtracer", vtracer_out, size_vtracer, elapsed_vtracer))

    # ── print table ──────────────────────────────────────────────────────────
    col_b = max(len(r[0]) for r in results)
    col_f = max(len(r[1]) for r in results)
    header = f"  {'Backend':<{col_b}}  {'Output file':<{col_f}}  {'Size':>8}  {'Time':>8}"
    sep    = "  " + "─" * (len(header) - 2)

    print()
    print(header)
    print(sep)
    for backend, outfile, size, elapsed in results:
        print(
            f"  {backend:<{col_b}}  {outfile:<{col_f}}"
            f"  {_human_size(size):>8}  {elapsed:>6.1f} s"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="compare",
        description="Run custom and vtracer backends on an image and compare results.",
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument(
        "--out-dir", default="./test-images/",
        help="Directory for output SVGs (default: ./test-images/)",
    )
    args = parser.parse_args()
    run_comparison(args.input, args.out_dir)


if __name__ == "__main__":
    main()
