# -*- coding: utf-8 -*-
"""
    Numerical Integration (Quadrature)
    =====================================
    Three classical quadrature rules with convergence analysis and an
    artistic visualisation of how each rule approximates a smooth curve.

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
# --- 5. ARTISTIC DARK FIGURE ---
# ─────────────────────────────────────────────────────────────────────────────

with plt.style.context('dark_background'):

    fig3, ax = plt.subplots(figsize=(12, 7))
    fig3.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # True curve — glowing white
    ax.plot(x_dense, f(x_dense), color='white', lw=3, alpha=0.9, zorder=5)
    ax.fill_between(x_dense, f(x_dense), alpha=0.10, color='white')

    # Overlay three rule approximations side by side in different colours
    n_art = 8
    art_colours = ['#ff6b6b', '#48dbfb', '#1dd1a1']
    art_labels  = ["Trapezoidal", "Simpson's", "Gauss-Legendre"]

    offsets = [-0.04, 0.0, 0.04]  # slight vertical offset for readability
    for colour, label, offset in zip(art_colours, art_labels, offsets):
        if label == "Trapezoidal":
            x_n = np.linspace(a, b, n_art + 1)
            for i in range(n_art):
                xs = [x_n[i], x_n[i], x_n[i+1], x_n[i+1]]
                ys = [offset, f(x_n[i]) + offset, f(x_n[i+1]) + offset, offset]
                ax.fill(xs, ys, alpha=0.22, color=colour, zorder=2)
                ax.plot([x_n[i], x_n[i+1]], [f(x_n[i]) + offset, f(x_n[i+1]) + offset],
                        '-', color=colour, lw=1.5, alpha=0.8)
            ax.plot(x_n, f(x_n), 'o', color=colour, ms=7, zorder=6, alpha=0.9, label=label)

        elif label == "Simpson's":
            x_n = np.linspace(a, b, n_art + 1)
            for i in range(0, n_art, 2):
                xi = np.linspace(x_n[i], x_n[i+2], 80)
                poly = np.polyfit([x_n[i], x_n[i+1], x_n[i+2]],
                                  [f(x_n[i]), f(x_n[i+1]), f(x_n[i+2])], 2)
                yi = np.polyval(poly, xi) + offset
                ax.fill_between(xi, offset, yi, alpha=0.22, color=colour, zorder=2)
                ax.plot(xi, yi, '-', color=colour, lw=1.5, alpha=0.6)
            ax.plot(x_n, f(x_n) + offset, 'o', color=colour, ms=7, zorder=6, alpha=0.9, label=label)

        else:  # Gauss-Legendre
            gl_n, gl_w = roots_legendre(n_art)
            gl_t_art = 0.5 * (b - a) * gl_n + 0.5 * (a + b)
            gl_y_art = f(gl_t_art)
            for xn, yn in zip(gl_t_art, gl_y_art):
                ax.plot([xn, xn], [offset, yn + offset], '-', color=colour, lw=2, alpha=0.7, zorder=3)
            ax.plot(gl_t_art, gl_y_art + offset, 'o', color=colour, ms=9, zorder=6,
                    alpha=0.9, label=label)
            ax.scatter(gl_t_art, gl_y_art + offset, s=120, color=colour, alpha=0.15, zorder=5)

    ax.axhline(0, color='#333333', lw=1)
    ax.set_xlim(-0.1, np.pi + 0.1); ax.set_ylim(-0.3, 1.45)
    ax.set_xlabel("x", color='#aaaaaa', fontsize=12)
    ax.set_ylabel("f(x) = sin(x)", color='#aaaaaa', fontsize=12)
    ax.tick_params(colors='#555555')
    for sp in ax.spines.values():
        sp.set_edgecolor('#2a2a2a')

    legend = ax.legend(fontsize=11, loc='upper right',
                       facecolor='#1a1a2e', edgecolor='#333333', labelcolor='white')

    # Annotate exact value
    ax.text(np.pi / 2, 1.25, f"∫ sin(x) dx = {exact}  (exact)",
            color='white', alpha=0.6, fontsize=11, ha='center')

    ax.set_title("N U M E R I C A L   I N T E G R A T I O N",
                 color='white', alpha=0.75, fontsize=14, fontweight='bold', pad=14)

    plt.tight_layout()
    plt.savefig("quadrature_artistic.png", dpi=180, bbox_inches='tight',
                facecolor=fig3.get_facecolor())
    print("Saved: quadrature_artistic.png")
    plt.show()
    plt.close(fig3)

print("\nAll plots complete.")
