# -*- coding: utf-8 -*-
"""
    Root-Finding Methods
    =====================
    Three classical algorithms for solving f(x) = 0, with a convergence
    comparison and an artistic Newton fractal visualisation.

    Methods covered:
        1. Bisection method         (guaranteed, linear convergence)
        2. Newton-Raphson method    (quadratic convergence, needs f')
        3. Secant method            (superlinear ~1.618, no derivative)

    Bonus:  Newton fractal for p(z) = z³ − 1  in the complex plane.

    Run:  python root_finding.py
    Deps: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. BISECTION METHOD ---
# ─────────────────────────────────────────────────────────────────────────────

def bisection(f, a, b, tol=1e-10, max_iter=100):
    """
    Bisect [a, b] until |f(mid)| < tol or max iterations reached.
    Returns (root, list of midpoints).
    """
    assert f(a) * f(b) < 0, "f(a) and f(b) must have opposite signs."
    history = []
    for _ in range(max_iter):
        mid = (a + b) / 2
        history.append(mid)
        if abs(f(mid)) < tol or (b - a) / 2 < tol:
            break
        if f(a) * f(mid) < 0:
            b = mid
        else:
            a = mid
    return mid, history


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. NEWTON-RAPHSON METHOD ---
# ─────────────────────────────────────────────────────────────────────────────

def newton_raphson(f, df, x0, tol=1e-10, max_iter=50):
    """
    Apply x_{n+1} = x_n − f(x_n)/f'(x_n) until convergence.
    Returns (root, list of iterates).
    """
    x = x0
    history = [x]
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            break
        dfx = df(x)
        if abs(dfx) < 1e-14:          # guard against zero derivative
            print(f"  newton_raphson: |f'(x)| ≈ 0 at x={x:.6e}, stopping.")
            break
        x = x - fx / dfx
        history.append(x)
    return x, history


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. SECANT METHOD ---
# ─────────────────────────────────────────────────────────────────────────────

def secant(f, x0, x1, tol=1e-10, max_iter=50):
    """
    Approximate f'(x) with the secant slope between the last two iterates.
    Returns (root, list of iterates).
    """
    x2 = x1                             # safe default if loop exits early
    history = [x0, x1]
    for _ in range(max_iter):
        f0, f1 = f(x0), f(x1)
        if abs(f1 - f0) < 1e-14:      # secant slope nearly zero — stop
            break
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        history.append(x2)
        if abs(x2 - x1) < tol:
            break
        x0, x1 = x1, x2
    return x2, history


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. DIAGNOSTIC FIGURE (light background) ---
# ─────────────────────────────────────────────────────────────────────────────

# Test function: f(x) = x³ − x − 2   (one real root at x ≈ 1.5214)
f  = lambda x: x**3 - x - 2
df = lambda x: 3*x**2 - 1
true_root = 1.5213797068045676

root_b, hist_b = bisection(f, 1.0, 2.0)
root_n, hist_n = newton_raphson(f, df, x0=1.5)
root_s, hist_s = secant(f, 1.0, 2.0)

# Errors relative to true root
err_b = [abs(x - true_root) for x in hist_b]
err_n = [abs(x - true_root) for x in hist_n]
err_s = [abs(x - true_root) for x in hist_s]

# Trim near-zero errors to avoid log(0) on the semilogy plot
floor = 1e-16                         # machine-epsilon-scale floor
err_b = [max(e, floor) for e in err_b]
err_n = [max(e, floor) for e in err_n]
err_s = [max(e, floor) for e in err_s]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Root-Finding Methods — f(x) = x³ − x − 2", fontsize=13, fontweight='bold')

# Left: function + root marked
ax0 = axes[0]
xs  = np.linspace(0.8, 2.2, 400)
ax0.plot(xs, f(xs), 'k-', lw=2, label="f(x)")
ax0.axhline(0, color='gray', lw=0.8, ls='--')
ax0.axvline(true_root, color='#8e44ad', lw=1.5, ls=':', alpha=0.7, label=f"Root  x* ≈ {true_root:.6f}")
# Show first few bisection midpoints
for i, xm in enumerate(hist_b[:6]):
    ax0.plot(xm, f(xm), 'o', color='#e74c3c', ms=6 - i*0.5, alpha=0.8, zorder=5)
ax0.set_xlabel("x"); ax0.set_ylabel("f(x)")
ax0.set_title("Function & bisection iterates"); ax0.legend(fontsize=9); ax0.grid(True, alpha=0.3)

# Right: convergence plot
ax1 = axes[1]
ax1.semilogy(range(len(err_b)), err_b, 'o-', color='#e74c3c', lw=2, ms=5, label="Bisection")
ax1.semilogy(range(len(err_n)), err_n, 's-', color='#2980b9', lw=2, ms=5, label="Newton-Raphson")
ax1.semilogy(range(len(err_s)), err_s, '^-', color='#27ae60', lw=2, ms=5, label="Secant")
ax1.set_xlabel("Iteration"); ax1.set_ylabel("|x_n − x*|  (log scale)")
ax1.set_title("Convergence Comparison"); ax1.legend(fontsize=10); ax1.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig("root_finding_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: root_finding_diagnostic.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. NEWTON FRACTAL (artistic) ---
# ─────────────────────────────────────────────────────────────────────────────
# Apply Newton-Raphson to p(z) = z³ − 1 over a grid of complex starting points.
# Each pixel is coloured by which of the three cube roots it converges to,
# and shaded by how many iterations it took — producing a stunning fractal.

print("\nComputing Newton fractal for p(z) = z³ − 1  …  (may take a few seconds)")

RES   = 800          # pixel resolution per axis (increase for print quality)
LIMIT = 1.5          # domain half-width: [-LIMIT, LIMIT] × [-LIMIT, LIMIT]
MAX_ITER = 50        # Newton iterations — 50 is enough for TOL below
TOL      = 1e-6      # convergence tolerance for root assignment

x_arr = np.linspace(-LIMIT, LIMIT, RES)
y_arr = np.linspace(-LIMIT, LIMIT, RES)
Z = x_arr[np.newaxis, :] + 1j * y_arr[:, np.newaxis]

# The three roots of z³ − 1
roots = np.array([1.0 + 0j,
                  np.exp(2j * np.pi / 3),
                  np.exp(4j * np.pi / 3)])

# Newton iteration: z ← z − (z³−1)/(3z²)
root_id  = -np.ones(Z.shape, dtype=int)    # which root did pixel converge to?
iter_map = np.zeros(Z.shape, dtype=float)  # how many iterations?

Zc = Z.copy()
converged = np.zeros(Z.shape, dtype=bool)

for it in range(1, MAX_ITER + 1):
    denom = 3 * Zc**2
    # Avoid division by zero at the origin
    safe = np.abs(denom) > 1e-12
    Zc[safe] = Zc[safe] - (Zc[safe]**3 - 1) / denom[safe]

    # Check which pixels just converged to a root
    for k, r in enumerate(roots):
        newly = (~converged) & (np.abs(Zc - r) < TOL)
        root_id[newly]  = k
        iter_map[newly] = it
        converged |= newly

    if converged.all():
        break

# Unresolved pixels → assign nearest root by final position
for i in np.argwhere(root_id == -1):
    row, col = i
    dists = np.abs(Zc[row, col] - roots)
    root_id[row, col] = np.argmin(dists)

# Build RGB image
# Base colours for the three roots
base_colours = np.array([
    [0.12, 0.47, 0.71],   # blue   (root 1)
    [0.84, 0.15, 0.16],   # red    (root 2)
    [0.17, 0.63, 0.17],   # green  (root 3)
])

# Normalise iteration count → shading (darker = more iterations).
# Exponent 0.45 gives good visual contrast in the fractal boundary region.
shade = 1.0 - (iter_map / MAX_ITER) ** 0.45

img = np.zeros((*Z.shape, 3))
for k in range(3):
    mask = root_id == k
    for c in range(3):
        img[mask, c] = base_colours[k, c] * shade[mask]

img = np.clip(img, 0, 1)

# ── Plot ──────────────────────────────────────────────────────────────────
with plt.style.context('dark_background'):

    fig4, ax = plt.subplots(figsize=(9, 9))
    fig4.patch.set_facecolor('black')
    ax.set_facecolor('black')

    ax.imshow(img, extent=[-LIMIT, LIMIT, -LIMIT, LIMIT], origin='lower', interpolation='bilinear')

    # Mark the three roots
    colours_r = ['#5b9bd5', '#e04848', '#4caf50']
    labels_r  = ['z = 1', 'z = e^{2πi/3}', 'z = e^{4πi/3}']
    for r, col, lab in zip(roots, colours_r, labels_r):
        ax.plot(r.real, r.imag, 'o', color='white', ms=8, zorder=5)
        ax.plot(r.real, r.imag, 'o', color='white', ms=20, alpha=0.15, zorder=4)
        ax.annotate(lab, xy=(r.real, r.imag), xytext=(r.real + 0.12, r.imag + 0.10),
                    color='white', fontsize=10, alpha=0.85)

    ax.set_xlim(-LIMIT, LIMIT); ax.set_ylim(-LIMIT, LIMIT)
    ax.set_xlabel("Re(z)", color='#888888', fontsize=11)
    ax.set_ylabel("Im(z)", color='#888888', fontsize=11)
    ax.tick_params(colors='#555555')
    for sp in ax.spines.values():
        sp.set_edgecolor('#333333')

    ax.set_title("N E W T O N   F R A C T A L\n"
                 r"p(z) = z³ − 1",
                 color='white', alpha=0.75, fontsize=14, fontweight='bold', pad=14)

    plt.tight_layout()
    plt.savefig("newton_fractal.png", dpi=180, bbox_inches='tight',
                facecolor=fig4.get_facecolor())
    print("Saved: newton_fractal.png")
    plt.show()
    plt.close(fig4)

print("\nAll plots complete.")
