# -*- coding: utf-8 -*-
"""
    param_test.py
    =============
    Runs a matrix of parameter variants on every test image for both
    backends, saves the SVGs, then writes an HTML gallery so results
    can be compared visually in a browser.

    Usage:
        python param_test.py [--images-dir DIR] [--out-dir DIR]

    Outputs:
        <out-dir>/index.html   — gallery (open this in a browser)
        <out-dir>/*.svg        — all generated SVGs
"""

import argparse
import html
import time
from pathlib import Path

from vectorize import vectorize, vectorize_vtracer

# ─────────────────────────────────────────────────────────────────────────────
# Parameter variants
# ─────────────────────────────────────────────────────────────────────────────

CUSTOM_VARIANTS = [
    {
        "label":  "default",
        "params": "ε=2.0  colors=16  smooth=off",
        "kwargs": {},
    },
    {
        "label":  "low detail",
        "params": "ε=4.0",
        "kwargs": {"epsilon": 4.0},
    },
    {
        "label":  "high detail",
        "params": "ε=0.5",
        "kwargs": {"epsilon": 0.5},
    },
    {
        "label":  "6 colors",
        "params": "colors=6",
        "kwargs": {"n_colors": 6},
    },
    {
        "label":  "32 colors",
        "params": "colors=32",
        "kwargs": {"n_colors": 32},
    },
    {
        "label":  "smooth",
        "params": "smooth=on",
        "kwargs": {"smooth": True},
    },
    {
        "label":  "smooth + high detail",
        "params": "smooth=on  ε=0.5",
        "kwargs": {"smooth": True, "epsilon": 0.5},
    },
    {
        "label":  "large min-area",
        "params": "min_area=200",
        "kwargs": {"min_area": 200.0},
    },
    {
        "label":  "half scale",
        "params": "scale=0.5",
        "kwargs": {"scale": 0.5},
    },
]

VTRACER_VARIANTS = [
    {
        "label":  "default",
        "params": "spline  color  precision=6",
        "kwargs": {},
    },
    {
        "label":  "polygon mode",
        "params": "mode=polygon",
        "kwargs": {"mode": "polygon"},
    },
    {
        "label":  "binary",
        "params": "colormode=binary",
        "kwargs": {"colormode": "binary"},
    },
    {
        "label":  "low precision",
        "params": "color_precision=3",
        "kwargs": {"color_precision": 3},
    },
    {
        "label":  "high precision",
        "params": "color_precision=8",
        "kwargs": {"color_precision": 8},
    },
    {
        "label":  "no speckle",
        "params": "filter_speckle=1",
        "kwargs": {"filter_speckle": 1},
    },
    {
        "label":  "heavy speckle filter",
        "params": "filter_speckle=16",
        "kwargs": {"filter_speckle": 16},
    },
    {
        "label":  "sharp corners",
        "params": "corner_threshold=10",
        "kwargs": {"corner_threshold": 10},
    },
    {
        "label":  "round corners",
        "params": "corner_threshold=120",
        "kwargs": {"corner_threshold": 120},
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


def _slug(label: str) -> str:
    return label.lower().replace(" ", "-").replace("+", "").replace("=", "").replace(".", "")


def _human(n: int) -> str:
    if n >= 1_048_576:
        return f"{n/1_048_576:.1f} MB"
    return f"{n/1024:.1f} KB"


def _run_custom(img_path: str, out_path: str, kwargs: dict) -> tuple[float, int]:
    """Run custom backend; return (elapsed_s, file_size_bytes)."""
    t0 = time.perf_counter()
    vectorize(input_path=img_path, output_path=out_path, **kwargs)
    elapsed = time.perf_counter() - t0
    return elapsed, Path(out_path).stat().st_size


def _run_vtracer(img_path: str, out_path: str, kwargs: dict) -> tuple[float, int]:
    """Run vtracer backend; return (elapsed_s, file_size_bytes)."""
    t0 = time.perf_counter()
    vectorize_vtracer(input_path=img_path, output_path=out_path, **kwargs)
    elapsed = time.perf_counter() - t0
    return elapsed, Path(out_path).stat().st_size


# ─────────────────────────────────────────────────────────────────────────────
# Core runner
# ─────────────────────────────────────────────────────────────────────────────

def run_matrix(images_dir: Path, out_dir: Path) -> dict:
    """
    Run all variants on all images.

    Returns a nested dict:
        results[backend][img_stem] = list of
            {"label", "params", "svg", "size", "elapsed"}
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in images_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )
    if not images:
        raise SystemExit(f"No images found in {images_dir}")

    results = {"custom": {}, "vtracer": {}}

    for img in images:
        stem = img.stem
        print(f"\n── {img.name} ──")

        # custom variants
        results["custom"][stem] = []
        for v in CUSTOM_VARIANTS:
            slug = _slug(v["label"])
            out = out_dir / f"custom-{stem}-{slug}.svg"
            print(f"  custom  {v['label']:<25}", end="", flush=True)
            elapsed, size = _run_custom(str(img), str(out), v["kwargs"])
            print(f"  {_human(size):>8}  {elapsed:.1f}s")
            results["custom"][stem].append({
                "label":   v["label"],
                "params":  v["params"],
                "svg":     out.name,
                "size":    size,
                "elapsed": elapsed,
            })

        # vtracer variants
        results["vtracer"][stem] = []
        for v in VTRACER_VARIANTS:
            slug = _slug(v["label"])
            out = out_dir / f"vtracer-{stem}-{slug}.svg"
            print(f"  vtracer {v['label']:<25}", end="", flush=True)
            elapsed, size = _run_vtracer(str(img), str(out), v["kwargs"])
            print(f"  {_human(size):>8}  {elapsed:.1f}s")
            results["vtracer"][stem].append({
                "label":   v["label"],
                "params":  v["params"],
                "svg":     out.name,
                "size":    size,
                "elapsed": elapsed,
            })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# HTML gallery
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, sans-serif;
    background: #111;
    color: #e8e8e8;
    padding: 24px;
}
h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 4px; }
.subtitle { color: #888; font-size: .85rem; margin-bottom: 32px; }

.backend-section { margin-bottom: 56px; }
.backend-title {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #aaa;
    border-bottom: 1px solid #333;
    padding-bottom: 8px;
    margin-bottom: 24px;
}
.backend-title span {
    background: #2a6;
    color: #fff;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: .75rem;
    letter-spacing: .05em;
    margin-left: 10px;
    vertical-align: middle;
}
.backend-title span.vt { background: #46a; }

.image-block { margin-bottom: 40px; }
.image-name {
    font-size: .9rem;
    font-weight: 600;
    color: #ccc;
    margin-bottom: 12px;
}

.card-row {
    display: flex;
    gap: 12px;
    overflow-x: auto;
    padding-bottom: 8px;
}
.card-row::-webkit-scrollbar { height: 6px; }
.card-row::-webkit-scrollbar-track { background: #222; }
.card-row::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }

.card {
    flex: 0 0 220px;
    background: #1e1e1e;
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    overflow: hidden;
    transition: border-color .15s;
}
.card:hover { border-color: #555; }

.card-preview {
    width: 100%;
    height: 160px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}
.card-preview img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
.card-preview.orig { background: #1a1a1a; }

.card-info {
    padding: 10px 12px 12px;
}
.card-label {
    font-size: .85rem;
    font-weight: 600;
    color: #e8e8e8;
    margin-bottom: 4px;
}
.card-params {
    font-size: .75rem;
    color: #777;
    font-family: monospace;
    margin-bottom: 6px;
    line-height: 1.4;
}
.card-stats {
    display: flex;
    gap: 10px;
    font-size: .75rem;
    color: #999;
}
.stat-size { color: #8cf; }
.stat-time { color: #aaa; }
.orig-label {
    font-size: .85rem;
    font-weight: 600;
    color: #e8e8e8;
    margin-bottom: 4px;
}
.orig-sub { font-size: .75rem; color: #666; }
"""

def _card_html(item: dict, images_dir_rel: str) -> str:
    label  = html.escape(item["label"])
    params = html.escape(item["params"])
    svg    = html.escape(item["svg"])
    size   = _human(item["size"])
    t      = f'{item["elapsed"]:.1f}s'
    return f"""
        <div class="card">
          <div class="card-preview">
            <img src="{svg}" alt="{label}" loading="lazy">
          </div>
          <div class="card-info">
            <div class="card-label">{label}</div>
            <div class="card-params">{params}</div>
            <div class="card-stats">
              <span class="stat-size">{size}</span>
              <span class="stat-time">{t}</span>
            </div>
          </div>
        </div>"""


def _orig_card(img_stem: str, images_dir_rel: str) -> str:
    # Try common extensions
    for ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"):
        candidate = Path(images_dir_rel) / f"{img_stem}{ext}"
        if candidate.exists():
            src = html.escape(str(candidate))
            name = html.escape(f"{img_stem}{ext}")
            return f"""
        <div class="card">
          <div class="card-preview orig">
            <img src="{src}" alt="original" loading="lazy">
          </div>
          <div class="card-info">
            <div class="orig-label">original</div>
            <div class="orig-sub">{name}</div>
          </div>
        </div>"""
    return ""


def write_html(results: dict, out_dir: Path, images_dir: Path) -> Path:
    # Relative path from out_dir to images_dir for original image src attributes
    try:
        images_rel = images_dir.relative_to(out_dir)
    except ValueError:
        images_rel = images_dir.resolve()

    sections_html = ""

    for backend, badge_cls in [("custom", ""), ("vtracer", "vt")]:
        badge = f'<span class="{badge_cls}">{backend}</span>'
        section = f'<div class="backend-section">\n'
        section += f'  <div class="backend-title">{backend} backend {badge}</div>\n'

        for stem, items in results[backend].items():
            orig = _orig_card(stem, str(images_rel))
            cards = "".join(_card_html(item, str(images_rel)) for item in items)
            section += f"""
  <div class="image-block">
    <div class="image-name">{html.escape(stem)}</div>
    <div class="card-row">
      {orig}
      {cards}
    </div>
  </div>
"""
        section += "</div>\n"
        sections_html += section

    total = sum(
        len(v) for bk in results.values() for v in bk.values()
    )
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vectorizer Parameter Test</title>
  <style>{CSS}</style>
</head>
<body>
  <h1>Vectorizer Parameter Test</h1>
  <p class="subtitle">{total} variants across {len(next(iter(results.values())))} images &mdash; scroll each row horizontally to compare</p>
  {sections_html}
</body>
</html>
"""

    out_path = out_dir / "index.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="param_test",
        description="Generate a visual parameter comparison gallery for the vectorizer.",
    )
    parser.add_argument(
        "--images-dir", default="./test-images/",
        help="Directory containing source images (default: ./test-images/)",
    )
    parser.add_argument(
        "--out-dir", default="./test-images/param-test/",
        help="Output directory for SVGs and HTML gallery (default: ./test-images/param-test/)",
    )
    args = parser.parse_args()

    images_dir = Path(args.images_dir).resolve()
    out_dir    = Path(args.out_dir).resolve()

    print(f"Images : {images_dir}")
    print(f"Output : {out_dir}")

    results  = run_matrix(images_dir, out_dir)
    html_out = write_html(results, out_dir, images_dir)

    print(f"\nGallery written → {html_out}")
    print("Open it in a browser to compare results.")


if __name__ == "__main__":
    main()
