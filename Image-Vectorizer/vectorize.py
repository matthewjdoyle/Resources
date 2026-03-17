# -*- coding: utf-8 -*-
"""
    Image Vectorizer
    ================
    Converts raster images (PNG/JPG/BMP/GIF/TIFF/WebP) to SVG vector
    graphics using k-means colour quantisation, contour tracing,
    Ramer-Douglas-Peucker simplification, and cubic Bezier curve fitting.

    Usage:
        python vectorize.py input.png output.svg
        python vectorize.py photo.jpg out.svg --colors 8 --detail medium --smooth

    Deps: opencv-python, numpy, Pillow, scipy, svgwrite, vtracer
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import svgwrite
from PIL import Image
from scipy.interpolate import splprep, splev


# ─────────────────────────────────────────────────────────────────────────────
# --- CONSTANTS ---
# ─────────────────────────────────────────────────────────────────────────────

DETAIL_PRESETS = {
    "low":    4.0,
    "medium": 2.0,
    "high":   0.5,
}

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

SEGMENT_WARN_THRESHOLD = 50_000


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. IMAGE LOADING ---
# ─────────────────────────────────────────────────────────────────────────────

def load_image(path: str, scale: float = 1.0):
    """Load image as RGBA numpy arrays (rgb uint8, alpha uint8), optionally rescaled.

    Returns:
        rgb   : (H, W, 3) uint8 array
        alpha : (H, W)    uint8 array
    """
    img = Image.open(path).convert("RGBA")

    if scale != 1.0:
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resample = Image.LANCZOS if scale < 1.0 else Image.BICUBIC
        img = img.resize((new_w, new_h), resample)

    arr = np.array(img, dtype=np.uint8)
    rgb   = arr[:, :, :3]
    alpha = arr[:, :, 3]
    return rgb, alpha


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. COLOR QUANTIZATION ---
# ─────────────────────────────────────────────────────────────────────────────

def quantize_colors(rgb: np.ndarray, alpha: np.ndarray, n_colors: int):
    """K-means colour quantisation on opaque pixels only.

    Returns:
        labels  : (H, W) int32 cluster index per pixel (-1 = transparent)
        palette : (K, 3) uint8 RGB palette, K ≤ n_colors
    """
    h, w = rgb.shape[:2]
    opaque_mask = alpha >= 128

    # Gather opaque pixels for clustering (convert to float32 for cv2.kmeans)
    pixels_rgb = rgb[opaque_mask].astype(np.float32)

    labels_flat = np.full(h * w, -1, dtype=np.int32)

    if pixels_rgb.shape[0] == 0:
        palette = np.zeros((n_colors, 3), dtype=np.uint8)
        return labels_flat.reshape(h, w), palette

    # Clamp n_colors to number of unique pixels
    n_colors = min(n_colors, pixels_rgb.shape[0])

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2)
    _, labels_opaque, centers = cv2.kmeans(
        pixels_rgb, n_colors, None, criteria,
        attempts=3, flags=cv2.KMEANS_PP_CENTERS
    )

    labels_opaque = labels_opaque.flatten().astype(np.int32)

    # Map cluster labels back to full pixel grid
    opaque_indices = np.where(opaque_mask.flatten())[0]
    labels_flat[opaque_indices] = labels_opaque
    labels = labels_flat.reshape(h, w)

    palette_rgb = centers.astype(np.uint8)  # centers are in RGB space (input was RGB)

    return labels, palette_rgb


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. CONTOUR EXTRACTION ---
# ─────────────────────────────────────────────────────────────────────────────

def extract_contours(mask: np.ndarray, min_area: float):
    """Extract outer contours and holes from a binary mask using RETR_CCOMP.

    Returns:
        outers : list of contour arrays (outer boundaries)
        holes  : list of contour arrays (hole boundaries)
    """
    mask_u8 = (mask > 0).astype(np.uint8) * 255
    contours, hierarchy = cv2.findContours(
        mask_u8, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
    )

    outers = []
    holes  = []

    if hierarchy is None:
        return outers, holes

    hierarchy = hierarchy[0]  # shape: (N, 4) — next, prev, child, parent

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        parent = hierarchy[i][3]
        if parent == -1:
            outers.append(contour)
        else:
            holes.append(contour)

    return outers, holes


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. PATH SIMPLIFICATION ---
# ─────────────────────────────────────────────────────────────────────────────

def simplify_contour(contour: np.ndarray, epsilon: float) -> np.ndarray:
    """Ramer-Douglas-Peucker simplification via cv2.approxPolyDP."""
    approx = cv2.approxPolyDP(contour, epsilon, closed=True)
    return approx.reshape(-1, 2)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. BEZIER CURVE FITTING ---
# ─────────────────────────────────────────────────────────────────────────────

def _catmull_rom_to_bezier(p0, p1, p2, p3):
    """Convert one Catmull-Rom segment (p1→p2) to cubic Bezier control points."""
    cp1 = p1 + (p2 - p0) / 6.0
    cp2 = p2 - (p3 - p1) / 6.0
    return cp1, cp2


def fit_spline_bezier_d(pts: np.ndarray) -> Optional[str]:
    """Fit a periodic cubic B-spline to pts and return an SVG path d-string.

    Uses scipy splprep with per=True (closed curve).
    Converts sampled spline segments to cubic Bezier via Catmull-Rom→Bezier.

    Returns None if fitting fails (too few points or degenerate geometry).
    """
    pts = pts.astype(float)
    n = len(pts)
    if n < 4:
        return None

    try:
        tck, _ = splprep([pts[:, 0], pts[:, 1]], per=True, k=3, s=0, quiet=True)
    except Exception:
        return None

    # Sample the spline at the simplified-contour points only.
    # Using max(n, 32) would inject phantom intermediate points, undoing the
    # RDP simplification and bloating the SVG with unnecessary C commands.
    n_samples = n
    u_fine = np.linspace(0, 1, n_samples, endpoint=False)
    sx, sy = splev(u_fine, tck)
    sampled = np.column_stack([sx, sy])

    # Build cubic Bezier path using Catmull-Rom→Bezier conversion
    m = len(sampled)
    parts = [f"M {sampled[0, 0]:.3f},{sampled[0, 1]:.3f}"]

    for i in range(m):
        p0 = sampled[(i - 1) % m]
        p1 = sampled[i % m]
        p2 = sampled[(i + 1) % m]
        p3 = sampled[(i + 2) % m]
        cp1, cp2 = _catmull_rom_to_bezier(p0, p1, p2, p3)
        end = p2
        parts.append(
            f"C {cp1[0]:.3f},{cp1[1]:.3f} "
            f"{cp2[0]:.3f},{cp2[1]:.3f} "
            f"{end[0]:.3f},{end[1]:.3f}"
        )

    parts.append("Z")
    return " ".join(parts)


def _polygon_d(pts: np.ndarray) -> str:
    """Build a simple polygon SVG path d-string from point array."""
    pts = pts.astype(float)
    coords = " L ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
    return f"M {coords} Z"


def fit_bezier_path(contour: np.ndarray, epsilon: float, smooth: bool) -> str:
    """Simplify contour and return SVG path d-string.

    Args:
        contour : raw cv2 contour array
        epsilon : RDP epsilon in pixels
        smooth  : if True, attempt spline Bezier fit; fall back to polygon
    """
    pts = simplify_contour(contour, epsilon)
    if len(pts) < 2:
        return ""

    if smooth:
        d = fit_spline_bezier_d(pts)
        if d is not None:
            return d

    return _polygon_d(pts)


# ─────────────────────────────────────────────────────────────────────────────
# --- 6. SVG ASSEMBLY ---
# ─────────────────────────────────────────────────────────────────────────────

def _rgb_to_hex(color: np.ndarray) -> str:
    """Convert (3,) uint8 RGB array to CSS hex string."""
    r, g, b = int(color[0]), int(color[1]), int(color[2])
    return f"#{r:02x}{g:02x}{b:02x}"


def build_svg(
    width: int,
    height: int,
    color_layers: list[tuple[str, list[str], list[str]]],
    output_path: str,
) -> None:
    """Assemble and save an SVG using svgwrite.

    Each colour layer is a <g fill-rule="evenodd"> containing all outer paths
    and hole paths. The evenodd rule makes holes work automatically without
    needing to reverse winding.

    Args:
        color_layers : sorted list of (hex_color, outer_ds, hole_ds) tuples
        output_path  : destination SVG file path
    """
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{width}px", f"{height}px"),
        profile="full",
    )
    dwg.viewbox(0, 0, width, height)

    total_segments = 0

    for hex_color, outer_ds, hole_ds in color_layers:
        if not outer_ds and not hole_ds:
            continue

        group = dwg.g(
            fill=hex_color,
            stroke="none",
            **{"fill-rule": "evenodd"},
        )

        for d in outer_ds:
            if d:
                group.add(dwg.path(d=d))
                total_segments += d.count("C") + d.count("L") + 1

        for d in hole_ds:
            if d:
                group.add(dwg.path(d=d))
                total_segments += d.count("C") + d.count("L") + 1

        dwg.add(group)

    if total_segments > SEGMENT_WARN_THRESHOLD:
        print(
            f"Warning: SVG contains {total_segments:,} path segments. "
            "Consider using a higher --epsilon or fewer --colors for a smaller file.",
            file=sys.stderr,
        )

    dwg.save()


# ─────────────────────────────────────────────────────────────────────────────
# --- 7. MAIN PIPELINE ---
# ─────────────────────────────────────────────────────────────────────────────

def vectorize(
    input_path: str,
    output_path: str,
    n_colors: int = 16,
    epsilon: float = 2.0,
    smooth: bool = False,
    min_area: float = 30.0,
    scale: float = 1.0,
) -> None:
    """Full raster-to-vector pipeline.

    Steps:
        1. Load & preprocess image
        2. Colour quantisation (k-means)
        3. Per-colour contour extraction
        4. Path simplification + optional Bezier fitting
        5. SVG assembly
    """
    def _log(msg):
        print(msg, file=sys.stderr)

    _log(f"Loading {input_path} ...")
    rgb, alpha = load_image(input_path, scale=scale)
    height, width = rgb.shape[:2]
    _log(f"  Image size: {width}×{height}  (after scale={scale})")

    _log(f"Quantising to {n_colors} colours ...")
    labels, palette = quantize_colors(rgb, alpha, n_colors)
    actual_colors = palette.shape[0]

    # Count pixels per colour, sort largest-first
    cluster_ids, counts = np.unique(labels[labels >= 0], return_counts=True)
    count_map = dict(zip(cluster_ids.tolist(), counts.tolist()))
    color_pixel_counts = sorted(
        ((count_map.get(c, 0), c) for c in range(actual_colors)),
        reverse=True,
    )

    color_layers = []

    _log("Tracing contours ...")
    for pixel_count, c in color_pixel_counts:
        if pixel_count == 0:
            continue

        mask = (labels == c)
        outers, holes = extract_contours(mask, min_area)

        if not outers and not holes:
            continue

        hex_color = _rgb_to_hex(palette[c])

        outer_ds = [fit_bezier_path(cnt, epsilon, smooth) for cnt in outers]
        hole_ds  = [fit_bezier_path(cnt, epsilon, smooth) for cnt in holes]

        # Filter empty strings
        outer_ds = [d for d in outer_ds if d]
        hole_ds  = [d for d in hole_ds  if d]

        color_layers.append((hex_color, outer_ds, hole_ds))

    _log(f"Assembling SVG → {output_path} ...")
    build_svg(width, height, color_layers, output_path)
    _log("Done.")


# ─────────────────────────────────────────────────────────────────────────────
# --- 8. VTRACER BACKEND ---
# ─────────────────────────────────────────────────────────────────────────────

def vectorize_vtracer(
    input_path: str,
    output_path: str,
    colormode: str = "color",
    mode: str = "spline",
    filter_speckle: int = 4,
    color_precision: int = 6,
    layer_difference: int = 16,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
) -> None:
    """Vectorize an image using the vtracer backend.

    Thin wrapper around vtracer.convert_image_to_svg_py with validated input.
    """
    from vtracer import convert_image_to_svg_py

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Running vtracer on {input_path} ...", file=sys.stderr)
    convert_image_to_svg_py(
        input_path,
        output_path,
        colormode=colormode,
        hierarchical="stacked",
        mode=mode,
        filter_speckle=filter_speckle,
        color_precision=color_precision,
        layer_difference=layer_difference,
        corner_threshold=corner_threshold,
        length_threshold=length_threshold,
        max_iterations=10,
        splice_threshold=45,
        path_precision=8,
    )
    print(f"Done → {output_path}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# --- 9. CLI ---
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vectorize",
        description="Convert a raster image to an SVG vector graphic.",
    )

    parser.add_argument("input",  help="Input image (PNG/JPG/BMP/GIF/TIFF/WebP)")
    parser.add_argument("output", help="Output SVG path")

    parser.add_argument(
        "--colors", type=int, default=16, metavar="N",
        help="Number of quantisation colours (default: 16)",
    )

    detail_group = parser.add_mutually_exclusive_group()
    detail_group.add_argument(
        "--detail", choices=["low", "medium", "high"], default=None,
        help="RDP simplification preset: low=4.0px, medium=2.0px, high=0.5px (default: medium)",
    )
    detail_group.add_argument(
        "--epsilon", type=float, default=None, metavar="F",
        help="RDP epsilon in pixels — overrides --detail",
    )

    parser.add_argument(
        "--smooth", action="store_true",
        help="Fit cubic Bezier curves instead of polygons (slower, smoother)",
    )
    parser.add_argument(
        "--min-area", type=float, default=30.0, metavar="PX",
        help="Minimum contour area in pixels to include (default: 30)",
    )
    parser.add_argument(
        "--scale", type=float, default=1.0, metavar="F",
        help="Resize input by this factor before processing (default: 1.0)",
    )

    # ── vtracer backend ──────────────────────────────────────────────────────
    parser.add_argument(
        "--backend", choices=["custom", "vtracer"], default="custom",
        help="Vectorization backend to use (default: custom)",
    )
    parser.add_argument(
        "--vt-colormode", choices=["color", "binary"], default="color",
        metavar="MODE", help="vtracer: color mode (default: color)",
    )
    parser.add_argument(
        "--vt-mode", choices=["spline", "polygon"], default="spline",
        metavar="MODE", help="vtracer: path mode (default: spline)",
    )
    parser.add_argument(
        "--vt-filter-speckle", type=int, default=4, metavar="N",
        help="vtracer: min region size in pixels (default: 4)",
    )
    parser.add_argument(
        "--vt-color-precision", type=int, default=6, metavar="N",
        help="vtracer: bits of colour precision (default: 6)",
    )
    parser.add_argument(
        "--vt-layer-difference", type=int, default=16, metavar="N",
        help="vtracer: min colour delta between layers (default: 16)",
    )
    parser.add_argument(
        "--vt-corner-threshold", type=int, default=60, metavar="N",
        help="vtracer: min angle in degrees for corner detection (default: 60)",
    )
    parser.add_argument(
        "--vt-length-threshold", type=float, default=4.0, metavar="F",
        help="vtracer: min spline segment length (default: 4.0)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input file not found: {args.input}")
    if input_path.suffix.lower() not in SUPPORTED_EXTS:
        parser.error(
            f"Unsupported file type '{input_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
        )

    # Resolve epsilon
    if args.epsilon is not None:
        epsilon = args.epsilon
    elif args.detail is not None:
        epsilon = DETAIL_PRESETS[args.detail]
    else:
        epsilon = DETAIL_PRESETS["medium"]

    if epsilon <= 0:
        parser.error("--epsilon must be positive")

    if args.colors < 1:
        parser.error("--colors must be >= 1")

    if args.scale <= 0:
        parser.error("--scale must be positive")

    if args.backend == "vtracer":
        vectorize_vtracer(
            input_path=str(input_path),
            output_path=args.output,
            colormode=args.vt_colormode,
            mode=args.vt_mode,
            filter_speckle=args.vt_filter_speckle,
            color_precision=args.vt_color_precision,
            layer_difference=args.vt_layer_difference,
            corner_threshold=args.vt_corner_threshold,
            length_threshold=args.vt_length_threshold,
        )
    else:
        vectorize(
            input_path=str(input_path),
            output_path=args.output,
            n_colors=args.colors,
            epsilon=epsilon,
            smooth=args.smooth,
            min_area=args.min_area,
            scale=args.scale,
        )


if __name__ == "__main__":
    main()
