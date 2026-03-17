# -*- coding: utf-8 -*-
"""
    Chaos & Dynamical Systems
    ===========================
    From the logistic map through the Lorenz attractor to the double
    pendulum, with Lyapunov exponent computation, bifurcation analysis,
    and artistic visualisations of strange attractors and sensitive
    dependence on initial conditions.

    Topics covered:
        1. Logistic Map — orbit diagram & cobweb plots
        2. Bifurcation Diagram — period-doubling route to chaos
        3. Lyapunov Exponents — quantifying chaos in the logistic map
        4. Lorenz System — the iconic strange attractor (RK4 integration)
        5. Double Pendulum — sensitive dependence on initial conditions
        6. Diagnostic figure — bifurcation + Lyapunov + Lorenz time series
        7. Artistic figure — 3D Lorenz attractor colour-coded by velocity
        8. Artistic figure — double pendulum sensitivity mosaic

    Run:  python chaos_dynamics.py
    Deps: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D            # noqa: F401 — registers 3D projection


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. LOGISTIC MAP  x_{n+1} = r · x_n · (1 − x_n) ---
# ─────────────────────────────────────────────────────────────────────────────

def logistic_map(r, x0, n_iter, n_skip=0):
    """
    Iterate the logistic map for *n_iter* steps, optionally discarding the
    first *n_skip* transient iterates.  Returns the retained orbit.
    """
    x = x0
    orbit = np.empty(n_iter)
    for i in range(n_iter + n_skip):
        x = r * x * (1.0 - x)
        if i >= n_skip:
            orbit[i - n_skip] = x
    return orbit


def cobweb(r, x0, n_steps=40):
    """
    Generate (x, y) pairs for a cobweb diagram of the logistic map at
    parameter *r* starting from *x0*.
    """
    xs, ys = [x0], [0.0]
    x = x0
    for _ in range(n_steps):
        y = r * x * (1 - x)
        xs += [x, y]
        ys += [y, y]
        x = y
    return np.array(xs), np.array(ys)


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. BIFURCATION DIAGRAM ---
# ─────────────────────────────────────────────────────────────────────────────

def bifurcation_data(r_min=2.5, r_max=4.0, n_r=2000, n_iter=300, n_skip=200):
    """
    Compute the bifurcation diagram of the logistic map.
    For each value of r, iterate the map and record the last *n_iter*
    values (after discarding *n_skip* transients).
    """
    rs = np.linspace(r_min, r_max, n_r)
    r_out, x_out = [], []
    for r in rs:
        orbit = logistic_map(r, 0.1, n_iter, n_skip)
        r_out.extend([r] * n_iter)
        x_out.extend(orbit)
    return np.array(r_out), np.array(x_out)


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. LYAPUNOV EXPONENT ---
# ─────────────────────────────────────────────────────────────────────────────

def lyapunov_exponent(r, x0=0.1, n_iter=10000, n_skip=500):
    r"""
    Compute the Lyapunov exponent for the logistic map:
        λ = lim_{N→∞} (1/N) Σ ln |f'(x_n)|   where f'(x) = r(1 − 2x)
    Positive λ ⟹ chaos;  negative λ ⟹ stable periodic orbit.
    """
    x = x0
    # skip transients
    for _ in range(n_skip):
        x = r * x * (1 - x)
    # accumulate log|derivative|
    lyap_sum = 0.0
    for _ in range(n_iter):
        deriv = abs(r * (1 - 2 * x))
        if deriv < 1e-14:
            return -np.inf                      # super-stable fixed point
        lyap_sum += np.log(deriv)
        x = r * x * (1 - x)
    return lyap_sum / n_iter


def lyapunov_spectrum(r_min=2.5, r_max=4.0, n_r=2000):
    """Compute Lyapunov exponent across a range of r values."""
    rs = np.linspace(r_min, r_max, n_r)
    lyaps = np.array([lyapunov_exponent(r) for r in rs])
    return rs, lyaps


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. LORENZ SYSTEM ---
# ─────────────────────────────────────────────────────────────────────────────
# dx/dt = σ(y − x)
# dy/dt = x(ρ − z) − y
# dz/dt = xy − βz
# Classic parameters: σ=10, ρ=28, β=8/3

def lorenz(t, state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    """Right-hand side of the Lorenz system."""
    x, y, z = state
    return np.array([
        sigma * (y - x),
        x * (rho - z) - y,
        x * y - beta * z,
    ])


def rk4_integrate(f, t_span, y0, h, **kwargs):
    """Classic RK4 integrator (matches your ODE-Solvers implementation)."""
    t0, tf = t_span
    N = round((tf - t0) / h)
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for n in range(len(t) - 1):
        k1 = f(t[n],       y[n],       **kwargs)
        k2 = f(t[n] + h/2, y[n] + (h/2)*k1, **kwargs)
        k3 = f(t[n] + h/2, y[n] + (h/2)*k2, **kwargs)
        k4 = f(t[n] + h,   y[n] + h*k3,     **kwargs)
        y[n + 1] = y[n] + (h / 6) * (k1 + 2*k2 + 2*k3 + k4)
    return t, y


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. DOUBLE PENDULUM ---
# ─────────────────────────────────────────────────────────────────────────────
# θ₁, θ₂ = angles;  ω₁, ω₂ = angular velocities
# Lagrangian mechanics → coupled 2nd-order ODEs (written as 4 first-order)

def double_pendulum(t, state, m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81):
    """
    Equations of motion for the double pendulum via the Lagrangian.
    State: [θ₁, ω₁, θ₂, ω₂]
    """
    th1, w1, th2, w2 = state
    delta = th2 - th1
    sin_d, cos_d = np.sin(delta), np.cos(delta)

    M = m1 + m2
    denom1 = M * L1 - m2 * L1 * cos_d**2
    denom2 = (L2 / L1) * denom1

    dw1 = (m2 * L1 * w1**2 * sin_d * cos_d
           + m2 * g * np.sin(th2) * cos_d
           + m2 * L2 * w2**2 * sin_d
           - M * g * np.sin(th1)) / denom1

    dw2 = (-m2 * L2 * w2**2 * sin_d * cos_d
           + M * (g * np.sin(th1) * cos_d
                  - L1 * w1**2 * sin_d
                  - g * np.sin(th2))) / denom2

    return np.array([w1, dw1, w2, dw2])


def pendulum_xy(theta1, theta2, L1=1.0, L2=1.0):
    """Convert angles to Cartesian positions of both bobs."""
    x1 =  L1 * np.sin(theta1)
    y1 = -L1 * np.cos(theta1)
    x2 = x1 + L2 * np.sin(theta2)
    y2 = y1 - L2 * np.cos(theta2)
    return x1, y1, x2, y2


# ─────────────────────────────────────────────────────────────────────────────
# --- 6. COMPUTE DATA ---
# ─────────────────────────────────────────────────────────────────────────────

print("Computing bifurcation diagram …")
r_bif, x_bif = bifurcation_data()

print("Computing Lyapunov exponent spectrum …")
r_lyap, lyap_vals = lyapunov_spectrum()

print("Integrating Lorenz system …")
t_lorenz, y_lorenz = rk4_integrate(lorenz, (0, 50), [1.0, 1.0, 1.0], h=0.005)

print("Integrating double pendulums …")
T_DP = 20.0
h_dp = 0.002
# Two nearby initial conditions — tiny perturbation in θ₁
ic_a = [np.pi/2,       0, np.pi/2,       0]
ic_b = [np.pi/2 + 1e-6, 0, np.pi/2,      0]
t_dp, y_dp_a = rk4_integrate(double_pendulum, (0, T_DP), ic_a, h_dp)
_,    y_dp_b = rk4_integrate(double_pendulum, (0, T_DP), ic_b, h_dp)


# ─────────────────────────────────────────────────────────────────────────────
# --- 7. DIAGNOSTIC FIGURE ---
# ─────────────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(16, 11))
fig.suptitle("Chaos & Dynamical Systems — Diagnostic Overview",
             fontsize=14, fontweight='bold', y=0.98)
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.50, wspace=0.35)

# ── (a) Bifurcation diagram ─────────────────────────────────────────────────
ax_bif = fig.add_subplot(gs[0, 0])
ax_bif.scatter(r_bif, x_bif, s=0.005, c='#2980b9', alpha=0.25, linewidths=0)
ax_bif.set_xlim(2.5, 4.0); ax_bif.set_ylim(0, 1)
ax_bif.set_xlabel("r"); ax_bif.set_ylabel("x*")
ax_bif.set_title("Bifurcation Diagram — Logistic Map", fontsize=11, fontweight='bold')
ax_bif.grid(True, alpha=0.2)

# Mark key r-values
for r_mark, label in [(3.0, "period-2"), (3.449, "period-4"),
                       (3.5699, "onset of chaos")]:
    ax_bif.axvline(r_mark, color='#e74c3c', lw=0.8, ls=':', alpha=0.5)
    ax_bif.annotate(label, xy=(r_mark, 0.95), fontsize=7, color='#e74c3c',
                    rotation=90, va='top', ha='right', alpha=0.7)

# ── (b) Lyapunov exponent spectrum ──────────────────────────────────────────
ax_lyap = fig.add_subplot(gs[0, 1])
ax_lyap.plot(r_lyap, lyap_vals, lw=0.6, color='#27ae60', alpha=0.8)
ax_lyap.axhline(0, color='#e74c3c', lw=1.2, ls='--', alpha=0.6)
ax_lyap.fill_between(r_lyap, lyap_vals, 0,
                     where=lyap_vals > 0, color='#e74c3c', alpha=0.15, label="λ > 0  (chaos)")
ax_lyap.fill_between(r_lyap, lyap_vals, 0,
                     where=lyap_vals < 0, color='#2980b9', alpha=0.15, label="λ < 0  (stable)")
ax_lyap.set_xlim(2.5, 4.0); ax_lyap.set_ylim(-2.5, 1.0)
ax_lyap.set_xlabel("r"); ax_lyap.set_ylabel("λ  (Lyapunov exponent)")
ax_lyap.set_title("Lyapunov Exponent — Logistic Map", fontsize=11, fontweight='bold')
ax_lyap.legend(fontsize=8); ax_lyap.grid(True, alpha=0.2)

# ── (c) Cobweb diagrams at two r-values ─────────────────────────────────────
for col, (r_val, title_extra) in enumerate([(3.2, "periodic"), (3.9, "chaotic")]):
    ax_cob = fig.add_subplot(gs[1, col])
    x_line = np.linspace(0, 1, 300)
    ax_cob.plot(x_line, r_val * x_line * (1 - x_line), 'k-', lw=1.8, label=f"f(x), r={r_val}")
    ax_cob.plot(x_line, x_line, 'gray', lw=1, ls='--', alpha=0.6, label="y = x")
    cx, cy = cobweb(r_val, 0.2, 60)
    ax_cob.plot(cx, cy, '-', color='#e74c3c', lw=0.8, alpha=0.7)
    ax_cob.set_xlim(0, 1); ax_cob.set_ylim(0, 1)
    ax_cob.set_xlabel("xₙ"); ax_cob.set_ylabel("xₙ₊₁")
    ax_cob.set_title(f"Cobweb — r = {r_val} ({title_extra})", fontsize=11, fontweight='bold')
    ax_cob.legend(fontsize=8); ax_cob.grid(True, alpha=0.2)

# ── (d) Lorenz x(t) time series ─────────────────────────────────────────────
ax_ts = fig.add_subplot(gs[2, 0])
ax_ts.plot(t_lorenz, y_lorenz[:, 0], lw=0.6, color='#8e44ad')
ax_ts.set_xlabel("t"); ax_ts.set_ylabel("x(t)")
ax_ts.set_title("Lorenz System — x(t) time series", fontsize=11, fontweight='bold')
ax_ts.grid(True, alpha=0.2)

# ── (e) Double pendulum divergence ──────────────────────────────────────────
ax_div = fig.add_subplot(gs[2, 1])
_, _, x2_a, y2_a = pendulum_xy(y_dp_a[:, 0], y_dp_a[:, 2])
_, _, x2_b, y2_b = pendulum_xy(y_dp_b[:, 0], y_dp_b[:, 2])
sep = np.sqrt((x2_a - x2_b)**2 + (y2_a - y2_b)**2)
ax_div.semilogy(t_dp, sep, lw=0.8, color='#e67e22')
ax_div.set_xlabel("t  (s)"); ax_div.set_ylabel("Separation  (m, log scale)")
ax_div.set_title("Double Pendulum — Sensitivity to Initial Conditions",
                 fontsize=11, fontweight='bold')
ax_div.annotate(f"Δθ₁(0) = 10⁻⁶ rad", xy=(0.02, 0.92), xycoords='axes fraction',
                fontsize=9, color='#555555')
ax_div.grid(True, which='both', alpha=0.2)

plt.savefig("chaos_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: chaos_diagnostic.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 8. ARTISTIC FIGURE — LORENZ ATTRACTOR (3D) ---
# ─────────────────────────────────────────────────────────────────────────────
# Colour-coded by instantaneous speed, dark background, subtle glow.

print("\nRendering Lorenz attractor …")

# High-resolution integration
t_art, y_art = rk4_integrate(lorenz, (0, 80), [0.1, 0.0, 0.0], h=0.002)
x_l, y_l, z_l = y_art[:, 0], y_art[:, 1], y_art[:, 2]

# Speed at each point (for colour mapping)
vx = np.gradient(x_l)
vy = np.gradient(y_l)
vz = np.gradient(z_l)
speed = np.sqrt(vx**2 + vy**2 + vz**2)
speed_norm = (speed - speed.min()) / (speed.max() - speed.min())

with plt.style.context('dark_background'):

    fig_lorenz = plt.figure(figsize=(12, 10))
    fig_lorenz.patch.set_facecolor('#0a0a12')
    ax3 = fig_lorenz.add_subplot(111, projection='3d')
    ax3.set_facecolor('#0a0a12')

    # Colour-coded line segments: split trajectory into chunks and
    # colour each by its average speed — gives a smooth gradient effect.
    n_pts = len(x_l)
    seg_size = 600
    for s in range(0, n_pts - seg_size, seg_size // 3):
        chunk = slice(s, s + seg_size)
        c = plt.cm.inferno(speed_norm[s + seg_size // 2])
        ax3.plot(x_l[chunk], y_l[chunk], z_l[chunk],
                 lw=0.45, alpha=0.85, color=c)

    # Bright scatter on top for colour bar reference and extra density
    stride = 6
    sc = ax3.scatter(x_l[::stride], y_l[::stride], z_l[::stride],
                     c=speed_norm[::stride], cmap='inferno',
                     s=1.2, alpha=0.9, linewidths=0, depthshade=False)

    # Soft glow halo
    ax3.scatter(x_l[::stride*4], y_l[::stride*4], z_l[::stride*4],
                c=speed_norm[::stride*4], cmap='inferno',
                s=12.0, alpha=0.12, linewidths=0, depthshade=False)

    # Mark the two unstable fixed points (the "eyes" of the butterfly)
    rho, beta = 28.0, 8.0/3.0
    fp = np.sqrt(beta * (rho - 1))
    for sign in [+1, -1]:
        ax3.scatter([sign*fp], [sign*fp], [rho-1],
                    color='white', s=30, alpha=0.5, zorder=10)
        ax3.scatter([sign*fp], [sign*fp], [rho-1],
                    color='white', s=150, alpha=0.05, zorder=9)

    ax3.set_xlim(-25, 25); ax3.set_ylim(-30, 30); ax3.set_zlim(0, 55)
    ax3.view_init(elev=22, azim=-60)

    # Minimalist axis styling
    ax3.set_xlabel("x", color='#444444', fontsize=10, labelpad=-4)
    ax3.set_ylabel("y", color='#444444', fontsize=10, labelpad=-4)
    ax3.set_zlabel("z", color='#444444', fontsize=10, labelpad=-4)
    ax3.tick_params(colors='#333333', labelsize=7)
    ax3.xaxis.pane.fill = False; ax3.yaxis.pane.fill = False; ax3.zaxis.pane.fill = False
    ax3.xaxis.pane.set_edgecolor('#1a1a2e')
    ax3.yaxis.pane.set_edgecolor('#1a1a2e')
    ax3.zaxis.pane.set_edgecolor('#1a1a2e')
    ax3.grid(True, alpha=0.08)

    ax3.set_title("L O R E N Z   A T T R A C T O R\n"
                   r"$\sigma = 10,\;\rho = 28,\;\beta = 8/3$",
                   color='white', alpha=0.75, fontsize=15, fontweight='bold', pad=18)

    # Colour bar
    cbar = fig_lorenz.colorbar(sc, ax=ax3, shrink=0.45, pad=0.08, aspect=25)
    cbar.set_label("Instantaneous speed", color='#666666', fontsize=9)
    cbar.ax.tick_params(colors='#444444', labelsize=7)

    plt.tight_layout()
    plt.savefig("chaos_lorenz_artistic.png", dpi=200, bbox_inches='tight',
                facecolor=fig_lorenz.get_facecolor())
    print("Saved: chaos_lorenz_artistic.png")
    plt.show()
    plt.close(fig_lorenz)


# ─────────────────────────────────────────────────────────────────────────────
# --- 9. ARTISTIC FIGURE — DOUBLE PENDULUM SENSITIVITY MOSAIC ---
# ─────────────────────────────────────────────────────────────────────────────
# Trace the tip of pendulum #2 for many nearby initial conditions.
# All start nearly identically, then diverge into wildly different paths —
# a visceral demonstration of deterministic chaos.

print("\nRendering double pendulum sensitivity mosaic …")

N_TRACES = 24
eps = np.linspace(-5e-3, 5e-3, N_TRACES)   # tiny perturbations to θ₁
base_ic = [np.pi * 0.75, 0.0, np.pi, 0.0]  # both arms raised — maximally chaotic

with plt.style.context('dark_background'):

    fig_dp, ax_dp = plt.subplots(figsize=(10, 10))
    fig_dp.patch.set_facecolor('#0d1117')
    ax_dp.set_facecolor('#0d1117')

    cmap_dp = plt.cm.twilight_shifted
    colours = [cmap_dp(i / (N_TRACES - 1)) for i in range(N_TRACES)]

    for i, d_theta in enumerate(eps):
        ic = base_ic.copy()
        ic[0] += d_theta
        _, y_dp = rk4_integrate(double_pendulum, (0, 15), ic, h=0.004)
        _, _, x2, y2 = pendulum_xy(y_dp[:, 0], y_dp[:, 2])

        # Fade alpha from tail to head
        n_pts = len(x2)
        seg_len = 800       # plot in segments for per-segment alpha
        for s in range(0, n_pts - seg_len, seg_len):
            alpha = 0.12 + 0.55 * (s / n_pts)
            ax_dp.plot(x2[s:s+seg_len+1], y2[s:s+seg_len+1],
                       color=colours[i], lw=0.35, alpha=alpha)

    # Pivot point
    ax_dp.plot(0, 0, 'o', color='white', ms=6, zorder=10)
    ax_dp.plot(0, 0, 'o', color='white', ms=22, alpha=0.08, zorder=9)

    ax_dp.set_xlim(-2.3, 2.3); ax_dp.set_ylim(-2.4, 1.8)
    ax_dp.set_aspect('equal')
    ax_dp.set_xlabel("x  (m)", color='#666666', fontsize=11)
    ax_dp.set_ylabel("y  (m)", color='#666666', fontsize=11)
    ax_dp.tick_params(colors='#444444')
    for sp in ax_dp.spines.values():
        sp.set_edgecolor('#222222')

    ax_dp.set_title("D O U B L E   P E N D U L U M\n"
                     f"{N_TRACES} traces  ·  Δθ₁ ∈ [−0.005, +0.005] rad",
                     color='white', alpha=0.75, fontsize=14, fontweight='bold', pad=14)

    ax_dp.annotate("pivot", xy=(0, 0), xytext=(0.35, 0.5),
                   fontsize=9, color='white', alpha=0.5,
                   arrowprops=dict(arrowstyle='->', color='white', lw=1, alpha=0.3))

    plt.tight_layout()
    plt.savefig("chaos_double_pendulum_artistic.png", dpi=200, bbox_inches='tight',
                facecolor=fig_dp.get_facecolor())
    print("Saved: chaos_double_pendulum_artistic.png")
    plt.show()
    plt.close(fig_dp)


# ─────────────────────────────────────────────────────────────────────────────
# --- 10. ARTISTIC FIGURE — BIFURCATION FRACTAL (high-res) ---
# ─────────────────────────────────────────────────────────────────────────────
# The bifurcation diagram itself is a fractal — self-similar at every zoom.
# Render at high density on a dark background with a striking colour map.

print("\nRendering high-res bifurcation fractal …")

r_hd, x_hd = bifurcation_data(r_min=2.8, r_max=4.0, n_r=4000, n_iter=500, n_skip=300)

with plt.style.context('dark_background'):

    fig_bf, ax_bf = plt.subplots(figsize=(14, 8))
    fig_bf.patch.set_facecolor('#0a0a12')
    ax_bf.set_facecolor('#0a0a12')

    ax_bf.scatter(r_hd, x_hd, s=0.08, c=x_hd, cmap='hot',
                  alpha=0.60, linewidths=0)

    ax_bf.set_xlim(2.8, 4.0); ax_bf.set_ylim(0, 1)
    ax_bf.set_xlabel("r", color='#666666', fontsize=12)
    ax_bf.set_ylabel("x*", color='#666666', fontsize=12)
    ax_bf.tick_params(colors='#444444')
    for sp in ax_bf.spines.values():
        sp.set_edgecolor('#1a1a2e')

    ax_bf.set_title("B I F U R C A T I O N\n"
                     r"$x_{n+1} = r\,x_n(1 - x_n)$",
                     color='white', alpha=0.75, fontsize=15, fontweight='bold', pad=14)

    # Annotate Feigenbaum's constant
    ax_bf.annotate("Feigenbaum's constant  δ ≈ 4.669…\n"
                   "governs the ratio of successive\n"
                   "period-doubling intervals",
                   xy=(3.57, 0.05), fontsize=8.5, color='#888888', alpha=0.7,
                   style='italic')

    plt.tight_layout()
    plt.savefig("chaos_bifurcation_artistic.png", dpi=200, bbox_inches='tight',
                facecolor=fig_bf.get_facecolor())
    print("Saved: chaos_bifurcation_artistic.png")
    plt.show()
    plt.close(fig_bf)

print("\nAll plots complete.")
