# -*- coding: utf-8 -*-
"""
    Numerical Integration (Quadrature)
    =====================================
    Three classical quadrature rules with convergence analysis and an
    artistic visualisation and a physics simulation of Fresnel/Fraunhofer
    diffraction through a triangular aperture (the diffraction integral
    is itself a numerical-integration problem, evaluated via FFT).

    Methods covered:
        1. Composite Trapezoidal Rule   (O(h²))
        2. Composite Simpson's 1/3 Rule (O(h⁴))
        3. Gauss-Legendre Quadrature    (exact for polynomials of degree ≤ 2n−1)

    Test integral:  ∫₀^π  sin(x) dx  =  2  (exact)

    Run:  python quadrature.py
    Deps: numpy, matplotlib, scipy
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import warnings
from scipy.special import roots_legendre


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. QUADRATURE IMPLEMENTATIONS ---
# ─────────────────────────────────────────────────────────────────────────────

def trapezoidal(f, a, b, n):
    """Composite trapezoidal rule over n panels."""
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1])

def simpsons(f, a, b, n):
    """
    Composite Simpson's 1/3 rule over n panels (n must be even).
    Automatically bumps n up by 1 if odd, with a warning.
    """
    if n % 2 != 0:
        warnings.warn(f"Simpson's rule requires even n; bumping {n} → {n + 1}.",
                       stacklevel=2)
        n += 1
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return (h / 3) * (y[0] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-2:2]) + y[-1])

def gauss_legendre(f, a, b, n):
    """
    n-point Gauss-Legendre quadrature, mapped from [-1,1] to [a,b].
    Exact for polynomials of degree ≤ 2n − 1.
    """
    nodes, weights = roots_legendre(n)
    # Map nodes from [-1, 1] to [a, b]
    t = 0.5 * (b - a) * nodes + 0.5 * (a + b)
    return 0.5 * (b - a) * np.dot(weights, f(t))


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. TEST INTEGRAL  ∫₀^π  sin(x) dx = 2 ---
# ─────────────────────────────────────────────────────────────────────────────

f     = np.sin
a, b  = 0.0, np.pi
exact = 2.0

# Quick accuracy check
for n in [4, 8, 16]:
    t = trapezoidal(f, a, b, n)
    s = simpsons(f,    a, b, n)
    g = gauss_legendre(f, a, b, n // 2)  # GL needs far fewer points
    print(f"n={n:3d} | Trap={t:.8f}  Simp={s:.8f}  GL(n/2)={g:.8f}  (exact={exact})")


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. CONVERGENCE ANALYSIS ---
# ─────────────────────────────────────────────────────────────────────────────

n_values = np.arange(2, 101, 2)    # composite panels

err_trap = [abs(trapezoidal(f, a, b, n) - exact) for n in n_values]
err_simp = [abs(simpsons(f,    a, b, n) - exact) for n in n_values]

# For Gauss-Legendre, x-axis is number of quadrature points (much fewer needed)
n_gl    = np.arange(1, 21)
err_gl  = [abs(gauss_legendre(f, a, b, n) - exact) for n in n_gl]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Quadrature Convergence — ∫₀^π sin(x) dx = 2",
             fontsize=13, fontweight='bold')

# Left: error vs n (log-log)
ax0 = axes[0]
ax0.loglog(n_values, err_trap, 'o-', color='#e74c3c', lw=2, ms=4, label="Trapezoidal  O(h²)")
ax0.loglog(n_values, err_simp, 's-', color='#2980b9', lw=2, ms=4, label="Simpson's    O(h⁴)")
ax0.loglog(n_gl,     err_gl,   '^-', color='#27ae60', lw=2, ms=5, label="Gauss-Legendre")

# Reference slopes
h_ref = n_values[5:30].astype(float)
scale_trap = err_trap[10] * n_values[10]**2
ax0.loglog(h_ref, scale_trap / h_ref**2, 'k--', lw=1, alpha=0.35, label="O(n⁻²)")
ax0.loglog(h_ref, scale_trap / h_ref**4 * 5, 'k:',  lw=1, alpha=0.35, label="O(n⁻⁴)")

ax0.set_xlabel("Number of panels / points  n")
ax0.set_ylabel("|I_approx − 2|  (log scale)")
ax0.set_title("Absolute Error vs n"); ax0.legend(fontsize=9); ax0.grid(True, which='both', alpha=0.3)

# Right: comparison at same number of function evaluations.
# For trap/Simpson, n panels ≈ n+1 evaluations; for GL, n/2 points ≈ n/2 evaluations.
evals = np.arange(4, 60, 2)
err_trap_e = [abs(trapezoidal(f, a, b, n) - exact) for n in evals]
err_simp_e = [abs(simpsons(f,    a, b, n) - exact) for n in evals]
err_gl_e   = [abs(gauss_legendre(f, a, b, max(1, n // 2)) - exact) for n in evals]

ax1 = axes[1]
ax1.semilogy(evals, err_trap_e, 'o-', color='#e74c3c', lw=2, ms=4, label="Trapezoidal")
ax1.semilogy(evals, err_simp_e, 's-', color='#2980b9', lw=2, ms=4, label="Simpson's")
ax1.semilogy(evals, err_gl_e,   '^-', color='#27ae60', lw=2, ms=4, label="Gauss-Legendre")
ax1.set_xlabel("Number of panels  n  (≈ function evaluations)")
ax1.set_ylabel("|error|  (log scale)")
ax1.set_title("Error vs Panels (proxy for function evaluations)")
ax1.legend(fontsize=9); ax1.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig("quadrature_convergence.png", dpi=150, bbox_inches='tight')
print("\nSaved: quadrature_convergence.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. PANEL VISUALISATION (diagnostic) ---
# ─────────────────────────────────────────────────────────────────────────────

n_panels = 6
x_dense  = np.linspace(a, b, 500)

fig2, axes2 = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
fig2.suptitle("Integration Panel Visualisation  (n = 6 panels)", fontsize=13, fontweight='bold')

panel_colours = ['#e74c3c', '#2980b9', '#27ae60']
panel_labels  = ["Trapezoidal\n(linear segments)", "Simpson's\n(parabolic arcs)", "Gauss-Legendre\n(optimal nodes)"]

for ax, col, lab in zip(axes2, panel_colours, panel_labels):
    ax.plot(x_dense, f(x_dense), 'k-', lw=2.5, zorder=5)
    ax.fill_between(x_dense, f(x_dense), alpha=0.08, color='gray')
    ax.set_xlabel("x"); ax.set_title(lab, fontweight='bold')
    ax.grid(True, alpha=0.25)

# Trapezoidal: shaded trapezoids
ax = axes2[0]
x_t = np.linspace(a, b, n_panels + 1)
for i in range(n_panels):
    xs = [x_t[i], x_t[i], x_t[i+1], x_t[i+1]]
    ys = [0, f(x_t[i]), f(x_t[i+1]), 0]
    ax.fill(xs, ys, alpha=0.35, color=panel_colours[0], edgecolor='white', lw=0.8)
ax.plot(x_t, f(x_t), 'o', color='white', ms=6, zorder=6, markeredgecolor=panel_colours[0])

# Simpson's: parabola through each pair of panels
ax = axes2[1]
x_s = np.linspace(a, b, n_panels + 1)
for i in range(0, n_panels, 2):
    xi = np.linspace(x_s[i], x_s[i+2], 100)
    # Fit quadratic through three points
    pts_x = [x_s[i], x_s[i+1], x_s[i+2]]
    pts_y = [f(xj) for xj in pts_x]
    poly = np.polyfit(pts_x, pts_y, 2)
    yi   = np.polyval(poly, xi)
    ax.fill_between(xi, yi, alpha=0.35, color=panel_colours[1])
    ax.plot(xi, yi, '--', color=panel_colours[1], lw=1.2, alpha=0.7)
ax.plot(x_s, f(x_s), 'o', color='white', ms=6, zorder=6, markeredgecolor=panel_colours[1])

# Gauss-Legendre: show node positions
ax = axes2[2]
n_gl_vis = 6
gl_nodes, gl_weights = roots_legendre(n_gl_vis)
gl_t = 0.5 * (b - a) * gl_nodes + 0.5 * (a + b)
gl_y = f(gl_t)
for xn, yn, wn in zip(gl_t, gl_y, gl_weights):
    ax.plot([xn, xn], [0, yn], '-', color=panel_colours[2], lw=2.5, alpha=0.6)
    ax.plot(xn, yn, 'o', color='white', ms=7, zorder=6, markeredgecolor=panel_colours[2])
    ax.annotate(f"w={wn:.2f}", xy=(xn, yn/2), fontsize=7, ha='center', color=panel_colours[2])

plt.tight_layout()
plt.savefig("quadrature_panels.png", dpi=150, bbox_inches='tight')
print("Saved: quadrature_panels.png")
plt.show()
plt.close(fig2)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. DIFFRACTION THROUGH A TRIANGULAR APERTURE ---
#     The Fresnel diffraction integral is itself a numerical-integration
#     problem: we evaluate ∬ U₀(x',y') · H(x-x',y-y',z) dx'dy' via FFT.
#
#     Two propagation methods are used depending on the Fresnel number:
#       • Angular-spectrum method  (near-field, N_F ≳ 3)
#       • Single-FFT Fresnel integral (far-field, N_F ≲ 3)
#     The second method naturally rescales the output grid with z, avoiding
#     the wrap-around aliasing that plagues the angular spectrum at large z.
# ─────────────────────────────────────────────────────────────────────────────

from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import PowerNorm

# --- Physical parameters ---
wavelength = 532e-9          # 532 nm green laser
k          = 2 * np.pi / wavelength
side       = 0.5e-3          # equilateral triangle side length (0.5 mm)

# --- Computational grid ---
N     = 1024
L     = 8.0e-3              # 8 mm grid extent
dx    = L / N
x     = np.linspace(-L/2, L/2, N, endpoint=False)
X, Y  = np.meshgrid(x, x)

# --- Triangular aperture mask (equilateral, centred at origin) ---
h_tri    = side * np.sqrt(3) / 2
v_top    = np.array([0,  2*h_tri/3])
v_left   = np.array([-side/2, -h_tri/3])
v_right  = np.array([ side/2, -h_tri/3])

def _edge_sign(p, v1, v2):
    """Positive if point p is on the interior side of edge v1→v2."""
    return (v2[0]-v1[0])*(p[1]-v1[1]) - (v2[1]-v1[1])*(p[0]-v1[0])

aperture = (
    (_edge_sign(np.array([X, Y]), v_left, v_right)  >= 0) &
    (_edge_sign(np.array([X, Y]), v_right, v_top)    >= 0) &
    (_edge_sign(np.array([X, Y]), v_top,   v_left)   >= 0)
).astype(np.float64)

# --- Frequency grid (for angular-spectrum method) ---
fx = np.fft.fftfreq(N, d=dx)
FX, FY = np.meshgrid(fx, fx)
A0 = np.fft.fft2(aperture)

# Centred coordinates (for single-FFT Fresnel method)
x1 = (np.arange(N) - N // 2) * dx
X1, Y1 = np.meshgrid(x1, x1)


def compute_diffraction(z):
    """
    Compute diffraction intensity at distance z.

    Uses the angular-spectrum method when the transfer function is
    adequately sampled (validity = λzN/L² < 2), and the single-FFT
    Fresnel integral otherwise.  Returns (I, dx_out).
    """
    validity = wavelength * z * N / L**2
    if validity < 2.0:
        H = np.exp(1j*k*z) * np.exp(-1j * np.pi * wavelength * z * (FX**2 + FY**2))
        U = np.fft.ifft2(A0 * H)
        return np.abs(U)**2, dx
    else:
        chirp = np.exp(1j * np.pi / (wavelength * z) * (X1**2 + Y1**2))
        U = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(aperture * chirp)))
        dx2 = wavelength * z / (N * dx)
        return np.abs(U)**2, dx2


# --- Propagation distances  (N_F = a² / λz) ---
fresnel_targets = [50, 10, 3, 1, 0.3, 0.05]
z_values = [side**2 / (wavelength * nf) for nf in fresnel_targets]
patterns_data = [compute_diffraction(z) for z in z_values]


# ── 5a. Static horizontal-strip figure ──────────────────────────────────────

with plt.style.context('dark_background'):

    n_panels = len(fresnel_targets)
    fig3, axes3 = plt.subplots(1, n_panels, figsize=(3.2 * n_panels, 4.0))
    fig3.patch.set_facecolor('#0d1117')

    for idx, (ax, nf, z, (I, dx_out)) in enumerate(
            zip(axes3, fresnel_targets, z_values, patterns_data)):
        ax.set_facecolor('#0d1117')

        # Adaptive view: max of aperture-scale and diffraction-lobe scale
        view_half = max(3 * side, 5 * wavelength * z / side)
        crop_pix  = min(int(view_half / dx_out), N // 2 - 1)
        crop_pix  = max(crop_pix, 16)
        c = N // 2
        I_crop = I[c - crop_pix : c + crop_pix, c - crop_pix : c + crop_pix]
        I_norm = I_crop / I_crop.max() if I_crop.max() > 0 else I_crop

        ext = crop_pix * dx_out * 1e3  # half-extent in mm
        ax.imshow(I_norm, extent=[-ext, ext, -ext, ext], origin='lower',
                  cmap='inferno', norm=PowerNorm(gamma=0.45),
                  interpolation='bicubic')

        ax.set_title(f"$N_F = {nf}$", color='white', fontsize=10, fontweight='bold')
        ax.tick_params(colors='#555555', labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor('#2a2a2a')
        ax.set_xlabel("x  (mm)", color='#aaaaaa', fontsize=9)
        if idx == 0:
            ax.set_ylabel("y  (mm)", color='#aaaaaa', fontsize=9)
        else:
            ax.set_yticklabels([])

    axes3[0].text(0.03, 0.95, "Fresnel\n(near-field)",
                  transform=axes3[0].transAxes, color='#48dbfb',
                  fontsize=8, va='top', fontweight='bold')
    axes3[-1].text(0.97, 0.95, "Fraunhofer\n(far-field)",
                   transform=axes3[-1].transAxes, color='#1dd1a1',
                   fontsize=8, va='top', ha='right', fontweight='bold')

    fig3.suptitle("D I F F R A C T I O N  —  T R I A N G U L A R   A P E R T U R E",
                  color='white', alpha=0.75, fontsize=13, fontweight='bold', y=0.99)
    fig3.text(0.5, 0.01,
              "Fresnel diffraction integral via FFT  ·  λ = 532 nm  ·  a = 0.5 mm",
              color='#888888', fontsize=8.5, ha='center')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("quadrature_diffraction.png", dpi=180, bbox_inches='tight',
                facecolor=fig3.get_facecolor())
    print("Saved: quadrature_diffraction.png")
    plt.show()
    plt.close(fig3)


# ── 5b. Animated GIF: Fresnel → Fraunhofer sweep ────────────────────────────

with plt.style.context('dark_background'):

    n_frames = 60
    z_sweep  = np.geomspace(z_values[0], z_values[-1], n_frames)
    c        = N // 2

    fig4, ax4 = plt.subplots(figsize=(5, 5))
    fig4.patch.set_facecolor('#0d1117')
    ax4.set_facecolor('#0d1117')

    def _update(frame):
        ax4.clear()
        ax4.set_facecolor('#0d1117')

        z  = z_sweep[frame]
        nf = side**2 / (wavelength * z)
        I, dx_out = compute_diffraction(z)

        view_half = max(3 * side, 5 * wavelength * z / side)
        crop_pix  = min(int(view_half / dx_out), N // 2 - 1)
        crop_pix  = max(crop_pix, 16)
        Ic = I[c - crop_pix : c + crop_pix, c - crop_pix : c + crop_pix]
        Ic = Ic / Ic.max() if Ic.max() > 0 else Ic

        ext = crop_pix * dx_out * 1e3
        ax4.imshow(Ic, extent=[-ext, ext, -ext, ext], origin='lower',
                   cmap='inferno', norm=PowerNorm(gamma=0.45),
                   interpolation='bicubic')
        ax4.text(0.03, 0.97, f"$N_F$ = {nf:.2f}", transform=ax4.transAxes,
                 color='white', fontsize=11, va='top', fontweight='bold')
        ax4.set_xlabel("x  (mm)", color='#aaaaaa', fontsize=10)
        ax4.set_ylabel("y  (mm)", color='#aaaaaa', fontsize=10)
        ax4.tick_params(colors='#555555')
        for sp in ax4.spines.values():
            sp.set_edgecolor('#2a2a2a')
        ax4.set_title("Triangular Aperture Diffraction",
                      color='white', alpha=0.75, fontsize=12, fontweight='bold')

    anim = FuncAnimation(fig4, _update, frames=n_frames, interval=80, blit=False)
    anim.save("quadrature_diffraction.gif", writer=PillowWriter(fps=12),
              dpi=120, savefig_kwargs={'facecolor': fig4.get_facecolor()})
    print("Saved: quadrature_diffraction.gif")
    plt.close(fig4)

print("\nAll plots complete.")
