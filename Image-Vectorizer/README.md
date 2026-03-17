# Image Vectorizer

Converts raster images (PNG, JPG, BMP, GIF, TIFF, WebP) to SVG vector graphics.

## Algorithm

1. **Load & preprocess** — PIL RGBA → numpy; optional `--scale` rescaling
2. **Color quantization** — k-means++ via `cv2.kmeans`, N colors
3. **Contour tracing** — `cv2.findContours` with `RETR_CCOMP` hierarchy (outer boundaries + holes)
4. **Path simplification** — Ramer-Douglas-Peucker via `cv2.approxPolyDP`
5. **Bezier fitting** *(optional)* — periodic B-spline via `scipy.splprep` converted to cubic Bezier segments
6. **SVG assembly** — `svgwrite`; `fill-rule="evenodd"` handles holes automatically

## Installation

```bash
pip install -r requirements.txt
```

All packages install as pure wheels on Windows — no compiler required.

## Usage

```
python vectorize.py <input> <output> [options]

positional:
  input              Image file (PNG/JPG/BMP/GIF/TIFF/WebP)
  output             Output SVG path

options:
  --colors N         Quantization colors (default: 16)
  --detail {low,medium,high}
                     RDP preset: low=4.0px, medium=2.0px, high=0.5px (default: medium)
  --epsilon F        RDP epsilon in pixels — overrides --detail
  --smooth           Fit cubic Bezier curves (slower, smoother output)
  --min-area PX      Min contour area to include in px (default: 30)
  --scale F          Resize input by factor before processing (default: 1.0)
```

`--detail` and `--epsilon` are mutually exclusive.

## Examples

```bash
# Basic conversion
python vectorize.py photo.jpg output.svg

# Fewer colors, smooth curves
python vectorize.py photo.jpg output.svg --colors 8 --smooth

# Logo/flat art — few colors, aggressive simplification
python vectorize.py logo.png output.svg --colors 4 --detail low

# High-fidelity with Bezier curves
python vectorize.py artwork.png output.svg --colors 24 --detail high --smooth

# Large image — scale down first for speed
python vectorize.py large.png output.svg --scale 0.5 --colors 12
```

## Notes

- Transparent pixels (alpha < 128) are excluded from all masks; SVG background is transparent
- Colors are rendered largest-region-first for correct layer ordering
- If the output SVG exceeds 50,000 path segments, a warning is printed suggesting higher `--epsilon` or fewer `--colors`
