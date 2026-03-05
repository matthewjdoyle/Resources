# FFT & Spectral Methods — Design Document

## Overview

Add a fifth major section (§5) to the Numerical Methods reference covering FFT
and spectral methods. Follows the same structural pattern as §1–§4: formula
boxes, convergence analysis, code examples, diagnostic plots, comparison table,
and a dark artistic figure.

## Subsections

### 5.1 The Discrete Fourier Transform

- Definition of the DFT/IDFT pair (formula box)
- Matrix form: F_N as the Vandermonde-like matrix of roots of unity
- Naïve O(N²) implementation
- Comparison with `np.fft.fft` for validation

### 5.2 The FFT (Cooley-Tukey)

- Radix-2 decimation-in-time decomposition
- Why it reduces O(N²) → O(N log N): butterfly diagram concept
- Recursive Python implementation
- Timing comparison: naïve DFT vs recursive FFT vs NumPy FFT
- **Figure 12**: log-log timing plot confirming N² vs N log N scaling

### 5.3 The 2D DFT

- Extension to 2D grids via row-column decomposition
- Spatial frequencies (kx, ky) and their physical meaning
- Demo: 2D FFT of a synthetic pattern (e.g. superimposed gratings)
- Connection to the diffraction simulation in §4 (which uses `fft2`)
- **Figure 13**: input pattern + 2D magnitude spectrum (log scale)

### 5.4 Power Spectral Density

- Periodogram as |X[k]|²/N — why it's noisy
- Welch's method: segmented averaging with overlap
- Windowing functions (rectangular, Hann, Hamming) and spectral leakage
- Demo: composite signal (sum of sinusoids) buried in noise → PSD reveals
  the hidden frequencies
- **Figure 14**: noisy time-domain signal + PSD (periodogram vs Welch)

### 5.5 Spectral Differentiation

- Differentiation in the Fourier domain: multiply by ikω
- Implementation for periodic functions on [0, 2π]
- Convergence comparison: spectral vs 2nd-order finite differences vs
  4th-order finite differences
- **Figure 15**: error convergence (spectral achieves machine-precision
  at ~20 points for smooth functions)

### 5.6 Chebyshev Polynomials & Spectral Methods

- Chebyshev nodes: cos(jπ/N), clustering at endpoints
- Barycentric Lagrange interpolation on Chebyshev nodes
- Exponential (spectral) convergence for analytic functions vs algebraic
  convergence on equispaced nodes
- Gibbs phenomenon at discontinuities
- **Figure 16**: Chebyshev vs equispaced interpolation of a step function
  and a smooth function

### 5.7 Implementation & When to Use

- In Practice box: use `scipy.fft` (faster than `numpy.fft`, supports
  real-valued transforms, multi-threading)
- `scipy.signal.welch` for power spectra
- Tips: zero-padding for frequency resolution, `rfft` for real signals,
  proper normalisation
- Comparison table: when to use DFT vs Chebyshev vs wavelets

## Artistic Figure (Section 5 of script)

**Signal reconstruction from partial Fourier coefficients.**

Dark background (`#0d1117`). A clean composite signal (sum of ~5 sinusoids)
is corrupted by Gaussian noise. Progressive reconstructions are overlaid,
each retaining an increasing number of Fourier coefficients (e.g. top-5,
top-10, top-20, all). The clean signal glows white; partial reconstructions
are ghostly in graded colours; the noisy input is faint grey.

Output: `fft_spectral_artistic.png` (static) + `fft_spectral_artistic.gif`
(animated sweep of coefficient count).

- **Figure 17**: artistic signal reconstruction figure

## File Structure

```
FFT-Spectral/
  fft_spectral.py              # main script (sections 1–5)
  fft_timing.png               # Fig 12
  fft_2d_spectrum.png          # Fig 13
  fft_power_spectrum.png       # Fig 14
  fft_spectral_diff.png        # Fig 15
  fft_chebyshev.png            # Fig 16
  fft_spectral_artistic.png    # Fig 17
  fft_spectral_artistic.gif    # animated reconstruction
```

## HTML Changes

- Add §5 nav entries to sidebar
- Add full §5 content to `<main>` (before `</main>`)
- Figure numbering: 12–17
- Section ID: `id="s5"`, subsection IDs: `fft-dft`, `fft-cooley-tukey`,
  `fft-2d`, `fft-psd`, `fft-spectral-diff`, `fft-chebyshev`, `fft-practice`

## Dependencies

numpy, matplotlib, scipy (all already used by existing sections).
No new dependencies required.
