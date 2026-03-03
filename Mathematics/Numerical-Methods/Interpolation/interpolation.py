# -*- coding: utf-8 -*-
"""
    Polynomial & Spline Interpolation
    ==================================
    Demonstrates four interpolation approaches and their trade-offs,
    culminating in a striking visualisation of Runge's phenomenon.

    Methods covered:
        1. Lagrange polynomial interpolation
        2. Newton's divided-difference polynomial
        3. Cubic spline interpolation (via SciPy)
        4. Runge's phenomenon  (f = 1 / (1 + 25x²))

    Run:  python interpolation.py
    Deps: numpy, matplotlib, scipy
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.interpolate import CubicSpline

# ─────────────────────────────────────────────────────────────────────────────
# --- 1. LAGRANGE POLYNOMIAL INTERPOLATION ---
# ─────────────────────────────────────────────────────────────────────────────

def lagrange_basis(x_nodes, i, x):
    """Evaluate the i-th Lagrange basis polynomial L_i(x)."""
    xi = x_nodes[i]
    numerator   = np.prod([x - x_nodes[j] for j in range(len(x_nodes)) if j != i], axis=0)
    denominator = np.prod([xi - x_nodes[j] for j in range(len(x_nodes)) if j != i])
    return numerator / denominator

def lagrange_interpolate(x_nodes, y_nodes, x):
    """Evaluate the full Lagrange interpolating polynomial at x."""
    return sum(y_nodes[i] * lagrange_basis(x_nodes, i, x) for i in range(len(x_nodes)))


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. NEWTON'S DIVIDED-DIFFERENCE POLYNOMIAL ---
# ─────────────────────────────────────────────────────────────────────────────

def divided_differences(x_nodes, y_nodes):
    """
    Build the divided-difference coefficient table.
    Returns the diagonal (Newton's forward coefficients c[0], c[1], ...).
    """
    n = len(x_nodes)
    table = np.zeros((n, n))
    table[:, 0] = y_nodes.copy()
    for j in range(1, n):
        for i in range(n - j):
            table[i, j] = (table[i + 1, j - 1] - table[i, j - 1]) / (x_nodes[i + j] - x_nodes[i])
    return table[0, :]   # top row = Newton coefficients

def newton_interpolate(x_nodes, coeffs, x):
    """Evaluate Newton's divided-difference polynomial using Horner's method."""
    n = len(coeffs)
    result = coeffs[-1]
    for k in range(n - 2, -1, -1):
        result = result * (x - x_nodes[k]) + coeffs[k]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. DIAGNOSTIC FIGURE  (light background, 2×2 grid) ---
# ─────────────────────────────────────────────────────────────────────────────

# Test function: smooth bump  f(x) = sin(2x) * e^(-x²/2)
f_test = lambda x: np.sin(2 * x) * np.exp(-x**2 / 2)

x_dense   = np.linspace(-3, 3, 500)
y_true    = f_test(x_dense)

# 8 equally-spaced nodes
x_nodes_d = np.linspace(-3, 3, 8)
y_nodes_d = f_test(x_nodes_d)

# Build interpolants
coeffs_newton = divided_differences(x_nodes_d, y_nodes_d)
cs            = CubicSpline(x_nodes_d, y_nodes_d)

y_lagrange = lagrange_interpolate(x_nodes_d, y_nodes_d, x_dense)
y_newton   = newton_interpolate(x_nodes_d, coeffs_newton, x_dense)
y_spline   = cs(x_dense)

fig = plt.figure(figsize=(13, 9))
fig.suptitle("Interpolation Methods — Diagnostic Overview", fontsize=14, fontweight='bold', y=0.98)
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.30)

panel_data = [
    ("Lagrange Polynomial", y_lagrange, "#e74c3c"),
    ("Newton Divided Differences", y_newton, "#2980b9"),
    ("Cubic Spline",          y_spline,   "#27ae60"),
]

for idx, (title, y_interp, colour) in enumerate(panel_data):
    ax = fig.add_subplot(gs[idx // 2, idx % 2])
    ax.plot(x_dense, y_true,    "k--", lw=1.5, alpha=0.5, label="True f(x)")
    ax.plot(x_dense, y_interp, color=colour, lw=2,    label=title)
    ax.plot(x_nodes_d, y_nodes_d, "ko", ms=5, zorder=5, label="Nodes")
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

# 4th panel: error comparison
ax4 = fig.add_subplot(gs[1, 1])
for title, y_interp, colour in panel_data:
    ax4.semilogy(x_dense, np.abs(y_interp - y_true) + 1e-16, color=colour, lw=1.8, label=title)
    #                                              ↑ floor avoids log(0) on the semilogy plot
ax4.set_title("Absolute Error", fontsize=11, fontweight='bold')
ax4.set_xlabel("x"); ax4.set_ylabel("|error|  (log scale)")
ax4.legend(fontsize=8); ax4.grid(True, which='both', alpha=0.3)

plt.savefig("interpolation_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: interpolation_diagnostic.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. RUNGE'S PHENOMENON ---
# ─────────────────────────────────────────────────────────────────────────────
# Runge's function: spikes at the interval edges when using high-degree
# polynomials on equally-spaced nodes — a famous cautionary tale.

runge = lambda x: 1.0 / (1.0 + 25.0 * x**2)

x_runge = np.linspace(-1, 1, 800)
y_runge = runge(x_runge)

node_counts  = [5, 9, 13, 17]
runge_colors = ["#3498db", "#e67e22", "#e74c3c", "#8e44ad"]

fig2, axes = plt.subplots(2, 2, figsize=(13, 9))
fig2.suptitle("Runge's Phenomenon — f(x) = 1 / (1 + 25x²)",
              fontsize=14, fontweight='bold', y=0.98)

for ax, n, col in zip(axes.flat, node_counts, runge_colors):
    xn = np.linspace(-1, 1, n)
    yn = runge(xn)
    cn = divided_differences(xn, yn)
    yp = newton_interpolate(xn, cn, x_runge)

    ax.plot(x_runge, y_runge,   "k--", lw=2, alpha=0.7, label="f(x)  (true)")
    ax.plot(x_runge, yp,        color=col, lw=2, label=f"Polynomial  (n={n})")
    ax.plot(xn, yn,             "o", color=col, ms=6, zorder=5, label="Nodes")
    ax.set_ylim(-1.5, 2.0)
    ax.set_title(f"n = {n} equally-spaced nodes", fontsize=11, fontweight='bold')
    ax.set_xlabel("x"); ax.set_ylabel("p(x)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

plt.savefig("runges_phenomenon.png", dpi=150, bbox_inches='tight')
print("Saved: runges_phenomenon.png")
plt.show()
plt.close(fig2)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. ARTISTIC COMPARISON PLOT (dark background) ---
# ─────────────────────────────────────────────────────────────────────────────

with plt.style.context('dark_background'):

    fig3, ax = plt.subplots(figsize=(12, 7))
    fig3.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # Runge's function — the drama lives here
    n_low  = 9     # oscillating polynomial
    n_high = 5     # spline — tame even with fewer points

    # Low-degree polynomial (severe Runge oscillation)
    xn_bad = np.linspace(-1, 1, n_low)
    yn_bad = runge(xn_bad)
    cn_bad = divided_differences(xn_bad, yn_bad)
    yp_bad = newton_interpolate(xn_bad, cn_bad, x_runge)

    # Cubic spline (same nodes as bad polynomial)
    cs_good  = CubicSpline(xn_bad, yn_bad)
    yp_good  = cs_good(x_runge)

    # True function — white glow
    ax.plot(x_runge, y_runge, color='white', lw=3, alpha=0.9, label="True  f(x) = 1/(1+25x²)", zorder=5)

    # Polynomial — hot red, clipped to [-2.5, 3.0] for readability
    yp_clip = np.clip(yp_bad, -2.5, 3.0)
    ax.plot(x_runge, yp_clip, color='#ff4757', lw=2, alpha=0.85,
            label=f"Degree-{n_low-1} polynomial  (Runge oscillation)", zorder=4)

    # Spline — cool cyan
    ax.plot(x_runge, yp_good, color='#1dd1a1', lw=2.5, alpha=0.9,
            label=f"Cubic spline  (n={n_low} nodes)", zorder=4)

    # Node scatter with glow
    ax.scatter(xn_bad, yn_bad, s=80, color='white', zorder=10, label="Interpolation nodes")
    ax.scatter(xn_bad, yn_bad, s=250, color='white', alpha=0.12, zorder=9)

    # Annotation pointing to oscillation
    ax.annotate("Runge's\noscillation",
                xy=(-0.87, yp_clip[np.argmin(np.abs(x_runge + 0.87))]),
                xytext=(-0.60, 2.0),
                fontsize=10, color='#ff4757', alpha=0.9,
                arrowprops=dict(arrowstyle='->', color='#ff4757', lw=1.5),
                ha='center')

    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-2.6, 3.2)
    ax.set_xlabel("x", color='#aaaaaa', fontsize=12)
    ax.set_ylabel("y", color='#aaaaaa', fontsize=12)
    ax.tick_params(colors='#666666')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')

    legend = ax.legend(fontsize=10, loc='upper center',
                       facecolor='#1a1a2e', edgecolor='#333333', labelcolor='white')

    ax.set_title("I N T E R P O L A T I O N", color='white', alpha=0.7,
                 fontsize=16, fontweight='bold', pad=18)

    plt.tight_layout()
    plt.savefig("interpolation_artistic.png", dpi=180, bbox_inches='tight',
                facecolor=fig3.get_facecolor())
    print("Saved: interpolation_artistic.png")
    plt.show()
    plt.close(fig3)

print("\nAll plots complete.")
