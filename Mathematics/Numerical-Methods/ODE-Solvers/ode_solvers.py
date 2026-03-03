# -*- coding: utf-8 -*-
"""
    ODE Solvers — Step-by-Step Integration Methods
    ================================================
    Compares three classical explicit Runge-Kutta solvers on test problems
    and produces an artistic phase-space portrait of a damped pendulum.

    Methods covered:
        1. Forward Euler         (1st order)
        2. Heun's method (RK2)   (2nd order, predictor-corrector)
        3. Classic RK4           (4th order, the workhorse)

    Test problems:
        • Scalar decay   y' = −y,  y(0) = 1          exact: e^{−t}
        • Damped pendulum  θ'' = −b θ' − (g/L) sin θ  (phase-space portrait)

    Run:  python ode_solvers.py
    Deps: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import deque


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. SOLVER IMPLEMENTATIONS ---
# ─────────────────────────────────────────────────────────────────────────────

def euler(f, t_span, y0, h):
    """Forward Euler: y_{n+1} = y_n + h · f(t_n, y_n)."""
    t0, tf = t_span
    N = round((tf - t0) / h)           # avoid np.arange float drift
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for n in range(len(t) - 1):
        y[n + 1] = y[n] + h * f(t[n], y[n])
    return t, y

def heun(f, t_span, y0, h):
    """Heun's method (RK2): predictor-corrector."""
    t0, tf = t_span
    N = round((tf - t0) / h)
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for n in range(len(t) - 1):
        k1 = f(t[n],     y[n])
        k2 = f(t[n] + h, y[n] + h * k1)
        y[n + 1] = y[n] + (h / 2) * (k1 + k2)
    return t, y

def rk4(f, t_span, y0, h):
    """Classic 4th-order Runge-Kutta."""
    t0, tf = t_span
    N = round((tf - t0) / h)
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0
    for n in range(len(t) - 1):
        k1 = f(t[n],         y[n])
        k2 = f(t[n] + h/2,   y[n] + (h/2) * k1)
        k3 = f(t[n] + h/2,   y[n] + (h/2) * k2)
        k4 = f(t[n] + h,     y[n] + h * k3)
        y[n + 1] = y[n] + (h / 6) * (k1 + 2*k2 + 2*k3 + k4)
    return t, y


# ─────────────────────────────────────────────────────────────────────────────
# --- 1b. ADAMS-BASHFORTH MULTI-STEP METHODS ---
# ─────────────────────────────────────────────────────────────────────────────
# Adams-Bashforth methods are *explicit multi-step* methods: each step reuses
# f-evaluations from previous steps, costing only ONE new evaluation per step
# after the startup phase.  They are started using RK4.

def adams_bashforth2(f, t_span, y0, h):
    """
    2-step Adams-Bashforth (AB2), order 2.
        y_{n+1} = y_n + h/2 * (3 f_n - f_{n-1})
    Uses one RK4 step for startup.
    """
    t0, tf = t_span
    N = round((tf - t0) / h)
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0

    # Startup: one RK4 step to get y[1]
    k1 = f(t[0], y[0]); k2 = f(t[0]+h/2, y[0]+(h/2)*k1)
    k3 = f(t[0]+h/2, y[0]+(h/2)*k2); k4 = f(t[0]+h, y[0]+h*k3)
    y[1] = y[0] + (h/6)*(k1+2*k2+2*k3+k4)

    f_prev = f(t[0], y[0])
    f_curr = f(t[1], y[1])

    for n in range(1, len(t) - 1):
        y[n + 1] = y[n] + (h / 2) * (3 * f_curr - f_prev)
        f_prev = f_curr
        f_curr = f(t[n + 1], y[n + 1])
    return t, y

def adams_bashforth4(f, t_span, y0, h):
    """
    4-step Adams-Bashforth (AB4), order 4.
        y_{n+1} = y_n + h/24 * (55 f_n - 59 f_{n-1} + 37 f_{n-2} - 9 f_{n-3})
    Uses three RK4 steps for startup.
    """
    t0, tf = t_span
    N = round((tf - t0) / h)
    t = np.linspace(t0, tf, N + 1)
    y = np.zeros((len(t), len(y0)))
    y[0] = y0

    # Startup: three RK4 steps to get y[1], y[2], y[3]
    for n in range(3):
        k1 = f(t[n], y[n])
        k2 = f(t[n]+h/2, y[n]+(h/2)*k1)
        k3 = f(t[n]+h/2, y[n]+(h/2)*k2)
        k4 = f(t[n]+h,   y[n]+h*k3)
        y[n+1] = y[n] + (h/6)*(k1+2*k2+2*k3+k4)

    # Store the last four f-values in a bounded deque
    fs = deque([f(t[i], y[i]) for i in range(4)], maxlen=4)

    for n in range(3, len(t) - 1):
        f0, f1, f2, f3 = fs[0], fs[1], fs[2], fs[3]
        y[n + 1] = y[n] + (h / 24) * (55*f3 - 59*f2 + 37*f1 - 9*f0)
        fs.append(f(t[n + 1], y[n + 1]))
    return t, y

# ─────────────────────────────────────────────────────────────────────────────
# --- 2. TEST PROBLEM: SCALAR DECAY  y' = -y ---
# ─────────────────────────────────────────────────────────────────────────────

decay_rhs  = lambda t, y: np.array([-y[0]])
decay_exact = lambda t: np.exp(-t)

T_END = 5.0
h_demo = 0.5

t_e, y_e = euler(decay_rhs, (0, T_END), [1.0], h_demo)
t_h, y_h = heun( decay_rhs, (0, T_END), [1.0], h_demo)
t_r, y_r = rk4(  decay_rhs, (0, T_END), [1.0], h_demo)

t_fine  = np.linspace(0, T_END, 500)
y_exact = decay_exact(t_fine)


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. ERROR vs STEP-SIZE (h) STUDY ---
# ─────────────────────────────────────────────────────────────────────────────

h_values = np.logspace(-3, 0, 30)   # h from 0.001 → 1.0  (30 log-spaced points)

def global_error(solver, h):
    """Global error at t=T_END for y'=-y."""
    t_arr, y_arr = solver(decay_rhs, (0, T_END), [1.0], h)
    return abs(y_arr[-1, 0] - decay_exact(t_arr[-1]))

err_e  = [global_error(euler,           h) for h in h_values]
err_h  = [global_error(heun,            h) for h in h_values]
err_r  = [global_error(rk4,             h) for h in h_values]
err_ab2 = [global_error(adams_bashforth2, h) for h in h_values]
err_ab4 = [global_error(adams_bashforth4, h) for h in h_values]


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. DIAGNOSTIC FIGURE ---
# ─────────────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(14, 9))
fig.suptitle("ODE Solvers — Diagnostic Overview", fontsize=14, fontweight='bold', y=0.98)
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

solver_data = [
    ("Forward Euler",    t_e, y_e, "#e74c3c"),
    ("Heun's (RK2)",     t_h, y_h, "#e67e22"),
    ("RK4",              t_r, y_r, "#2980b9"),
]

# Top row: each solver vs exact
for idx, (name, t_s, y_s, col) in enumerate(solver_data):
    ax = fig.add_subplot(gs[0, idx])
    ax.plot(t_fine,  y_exact,  'k--', lw=1.5, alpha=0.5, label="Exact e^{-t}")
    ax.plot(t_s,     y_s[:, 0], 'o-', color=col, lw=2, ms=5, label=name)
    ax.set_title(name, fontsize=11, fontweight='bold')
    ax.set_xlabel("t"); ax.set_ylabel("y(t)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# Bottom left (spans 2 cols): convergence plot
ax_conv = fig.add_subplot(gs[1, :2])
ax_conv.loglog(h_values, err_e, 'o-', color='#e74c3c', lw=2, ms=4, label="Euler  (O(h))")
ax_conv.loglog(h_values, err_h, 's-', color='#e67e22', lw=2, ms=4, label="Heun   (O(h²))")
ax_conv.loglog(h_values, err_r, '^-', color='#2980b9', lw=2, ms=4, label="RK4    (O(h⁴))")

# Reference slope lines — scale factor anchored at h_values[10]
h_ref = h_values[5:20]
scale = err_e[10] / h_values[10]**1
ax_conv.loglog(h_ref, scale * h_ref**1, 'k--', lw=1, alpha=0.4, label="O(h¹)")
ax_conv.loglog(h_ref, scale * h_ref**2 * 5, 'k:',  lw=1, alpha=0.4, label="O(h²)")
ax_conv.loglog(h_ref, scale * h_ref**4 * 200, 'k-.', lw=1, alpha=0.4, label="O(h⁴)")

ax_conv.set_xlabel("Step size  h");  ax_conv.set_ylabel("Global error  |y(T) − y_exact(T)|")
ax_conv.set_title("Global Error vs Step Size — confirms order of accuracy", fontsize=11, fontweight='bold')
ax_conv.legend(fontsize=9); ax_conv.grid(True, which='both', alpha=0.3)

# Bottom right: single step error table
ax_tbl = fig.add_subplot(gs[1, 2])
ax_tbl.axis('off')
h_sample = [1.0, 0.5, 0.25, 0.1]
rows = [[f"{h:.2f}",
         f"{global_error(euler, h):.2e}",
         f"{global_error(heun,  h):.2e}",
         f"{global_error(rk4,   h):.2e}"] for h in h_sample]
table = ax_tbl.table(
    cellText=rows,
    colLabels=["h", "Euler", "Heun", "RK4"],
    loc='center', cellLoc='center'
)
table.auto_set_font_size(False); table.set_fontsize(9.5)
table.scale(1.1, 1.6)
ax_tbl.set_title("Error at t = 5", fontsize=11, fontweight='bold')

plt.savefig("ode_solvers_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: ode_solvers_diagnostic.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. ADAMS-BASHFORTH COMPARISON FIGURE ---
# ─────────────────────────────────────────────────────────────────────────────
# Show AB2 / AB4 alongside Euler / RK4:
#  • Left:  trajectories for a moderate step size (h=0.5)
#  • Right: convergence (error vs h) — AB4 matches RK4's O(h^4) slope
#           but costs only ~1 f-eval/step after startup vs RK4's 4.

t_ab2, y_ab2 = adams_bashforth2(decay_rhs, (0, T_END), [1.0], h_demo)
t_ab4, y_ab4 = adams_bashforth4(decay_rhs, (0, T_END), [1.0], h_demo)

fig_ab, axes_ab = plt.subplots(1, 2, figsize=(13, 5))
fig_ab.suptitle("Adams-Bashforth Methods vs Runge-Kutta  —  $y' = -y$",
                fontsize=13, fontweight='bold')

# Left: trajectories
ax_l = axes_ab[0]
ax_l.plot(t_fine, y_exact, 'k--', lw=1.8, alpha=0.5, label="Exact $e^{-t}$")
ax_l.plot(t_e,   y_e[:,0],  'o-', color='#e74c3c', lw=1.5, ms=5, label="Euler  (O(h))")
ax_l.plot(t_r,   y_r[:,0],  's-', color='#2980b9', lw=1.5, ms=5, label="RK4    (O(h⁴), 4 evals/step)")
ax_l.plot(t_ab2, y_ab2[:,0],'v-', color='#e67e22', lw=1.5, ms=5, label="AB2    (O(h²), 1 eval/step)")
ax_l.plot(t_ab4, y_ab4[:,0],'^-', color='#27ae60', lw=1.5, ms=5, label="AB4    (O(h⁴), 1 eval/step)")
ax_l.set_xlabel("t"); ax_l.set_ylabel("y(t)")
ax_l.set_title(f"Trajectories  (h = {h_demo})", fontsize=11, fontweight='bold')
ax_l.legend(fontsize=8.5); ax_l.grid(True, alpha=0.3)

# Right: convergence comparison
ax_r = axes_ab[1]
ax_r.loglog(h_values, err_e,   'o-', color='#e74c3c', lw=2, ms=4, label="Euler  O(h¹)")
ax_r.loglog(h_values, err_r,   's-', color='#2980b9', lw=2, ms=4, label="RK4    O(h⁴)")
ax_r.loglog(h_values, err_ab2, 'v-', color='#e67e22', lw=2, ms=4, label="AB2    O(h²)")
ax_r.loglog(h_values, err_ab4, '^-', color='#27ae60', lw=2, ms=4, label="AB4    O(h⁴)")

# Reference slopes — same anchor as diagnostic plot
h_ref = h_values[5:20]
scale = err_e[10] / h_values[10]**1
ax_r.loglog(h_ref, scale * h_ref**1,       'k--',  lw=1, alpha=0.3, label="O(h¹)")
ax_r.loglog(h_ref, scale * h_ref**2 * 5,   'k:',   lw=1, alpha=0.3, label="O(h²)")
ax_r.loglog(h_ref, scale * h_ref**4 * 200, 'k-.',  lw=1, alpha=0.3, label="O(h⁴)")

ax_r.set_xlabel("Step size  h"); ax_r.set_ylabel("|error at t=5|  (log scale)")
ax_r.set_title("Convergence — same O(h⁴) order, fewer evals", fontsize=11, fontweight='bold')
ax_r.legend(fontsize=8.5); ax_r.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig("ode_adams_comparison.png", dpi=150, bbox_inches='tight')
print("Saved: ode_adams_comparison.png")
plt.show()
plt.close(fig_ab)


# ─────────────────────────────────────────────────────────────────────────────
# Damped pendulum:  θ'' = −b·θ' − (g/L)·sin(θ)
# Here b is the *effective* damping coefficient (already divided by mass m).
# State vector: [θ, ω]  where ω = dθ/dt

g, L, b = 9.81, 1.0, 0.3              # gravity, length, damping coeff
pendulum = lambda t, y: np.array([y[1], -b * y[1] - (g / L) * np.sin(y[0])])

with plt.style.context('dark_background'):

    fig5, ax = plt.subplots(figsize=(11, 8))
    fig5.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')

    # Several trajectories with different initial angles
    initial_angles = np.linspace(0.3, 3.0, 8)
    cmaps_p  = ['autumn', 'cool', 'winter', 'spring', 'plasma', 'magma', 'viridis', 'inferno']

    T_PEND = 20.0
    h_fine = 0.01                      # small step for smooth phase curves

    for theta0, cmap_name in zip(initial_angles, cmaps_p):
        t_arr, y_arr = rk4(pendulum, (0, T_PEND), [theta0, 0.0], h_fine)
        theta = y_arr[:, 0]
        omega  = y_arr[:, 1]

        # Colour by time: gradient fades as it spirals in
        c_norm = np.linspace(0, 1, len(theta))

        # Plot as multi-coloured scatter (thin points)
        ax.scatter(theta, omega, c=c_norm, cmap=cmap_name,
                   s=0.4, alpha=0.7, linewidths=0)

    # Equilibrium point glow
    ax.plot(0, 0, 'o', color='white', ms=7, zorder=10)
    ax.plot(0, 0, 'o', color='white', ms=25, alpha=0.10, zorder=9)

    ax.set_xlim(-3.5, 3.5); ax.set_ylim(-6, 6)
    ax.set_xlabel("θ  (radians)", color='#aaaaaa', fontsize=12)
    ax.set_ylabel("ω = dθ/dt  (rad/s)", color='#aaaaaa', fontsize=12)
    ax.tick_params(colors='#555555')
    for sp in ax.spines.values():
        sp.set_edgecolor('#2a2a2a')

    ax.set_title("P H A S E   S P A C E\nDamped Pendulum — RK4",
                 color='white', alpha=0.75, fontsize=14, fontweight='bold', pad=14)

    ax.annotate("equilibrium", xy=(0, 0), xytext=(0.6, 1.5),
                fontsize=9, color='white', alpha=0.6,
                arrowprops=dict(arrowstyle='->', color='white', lw=1.0, alpha=0.4))

    plt.tight_layout()
    plt.savefig("ode_phase_space.png", dpi=180, bbox_inches='tight',
                facecolor=fig5.get_facecolor())
    print("Saved: ode_phase_space.png")
    plt.show()
    plt.close(fig5)

print("\nAll plots complete.")
