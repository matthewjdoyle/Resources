# Physics Poster Template — tikzposter

A competition-quality LaTeX poster template for physics research conferences.  
**A0 portrait** (841 × 1189 mm) with a **deep purple & emerald green** color scheme.

---

## Quick Start

```bash
pdflatex physics_poster.tex
# or, for better font support:
lualatex physics_poster.tex
```

The template compiles to a single-page A0 PDF ready for printing.

## Required LaTeX Packages

Most are included in a standard TeX Live / MiKTeX installation:

| Package | Purpose |
|---------|---------|
| `tikzposter` | Poster framework |
| `helvet` + `sfmath` | Sans-serif body & math fonts |
| `amsmath`, `amssymb` | Equation typesetting |
| `physics` | Bra-ket, derivatives, etc. |
| `siunitx` | SI units (`\qty`, `\SI`, `\unit`) |
| `graphicx` | Figure inclusion |
| `booktabs` | Professional tables |
| `tcolorbox` | Highlight boxes |
| `qrcode` | QR code generation |
| `hyperref` | Hyperlinks |
| `microtype` | Microtypography |
| `enumitem` | List customisation |

Install any missing packages:

```bash
# TeX Live
tlmgr install tikzposter physics siunitx tcolorbox qrcode

# MiKTeX — packages auto-install on first use
```

## Customisation

### Swap the Colour Scheme

The colours are defined in the `\definecolorstyle{PhysicsGreenPurple}` block near the top of the file. Change the RGB values there to match your institution or preference. Key colours:

| Variable | Default | Role |
|----------|---------|------|
| `DeepPurple` | `(75, 0, 130)` | Block titles, title bar |
| `EmeraldGreen` | `(0, 135, 81)` | Accent boxes, inner blocks |
| `LightPurple` | `(220, 208, 240)` | Purple highlight box bg |
| `LightGreen` | `(237, 248, 242)` | Green highlight box bg |

### Add Your Logos

Uncomment the two `\includegraphics` lines inside `\titlegraphic{}` and point them at your logo files in `figures/`.

### Change the Poster Size

Edit the `\documentclass` options:

```latex
% 36×48 inches (US standard)
\documentclass[25pt, custom, width=91.44cm, height=121.92cm, portrait, ...]{tikzposter}

% A1
\documentclass[25pt, a1paper, portrait, ...]{tikzposter}
```

### Physics-Specific Tips

- Use `\qty{value}{unit}` (or `\SI{value}{unit}`) from `siunitx` for all quantities: `\qty{3e8}{\metre\per\second}`
- Use `\bra{}`, `\ket{}`, `\braket{}` from `physics` for quantum notation
- Place vector graphics (`.pdf`) in `figures/` for scalable, print-quality images
- All raster images should be ≥ 300 DPI at A0 print size

## Tips for Competition-Quality Posters

1. **Less is more** — aim for 300–800 words total. Let figures tell the story.
2. **Visual hierarchy** — title readable from 6 m; section headers from 3 m; body text from 1.5 m.
3. **High-res figures** — use vector (PDF/SVG) wherever possible. Raster ≥ 300 DPI.
4. **Consistent styling** — keep figure fonts, line widths, and colour scales uniform.
5. **Accessible colours** — the default palette passes WCAG AA (≥ 4.5 : 1 contrast). Avoid relying on colour alone to convey information.
6. **Tell a story** — Hook → Method → Discovery → Impact.
7. **QR code** — link to the full paper, code repository, or supplementary data.
8. **Test print** — print at 25 % scale on A4 and check readability from arm's length.

## Print Checklist

- [ ] PDF page size is 841 × 1189 mm (`pdfinfo physics_poster.pdf`)
- [ ] All fonts embedded (`pdffonts physics_poster.pdf`)
- [ ] Single page, correct orientation
- [ ] Figures sharp at 100 % zoom
- [ ] QR code scans successfully
- [ ] No placeholder text remaining
- [ ] Author names, affiliations, and contact info correct
- [ ] References formatted and complete
- [ ] 25 % scale test print reviewed

## File Structure

```
Physics Poster Template/
├── physics_poster.tex      ← Main template (edit this)
├── README.md               ← You are here
└── figures/                ← Place your figures here
    └── .gitkeep
```

## License

Feel free to use and adapt this template for your research.
