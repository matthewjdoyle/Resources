# -*- coding: utf-8 -*-
"""
    Reaction-Diffusion & Turing Patterns
    ======================================
    The Gray-Scott model — two chemical species (U, V) diffusing and reacting
    on a 2D grid — spontaneously generates spots, stripes, coral-like
    labyrinths, and mitotic cell-division patterns from a uniform steady state
    plus tiny noise.  These are *Turing patterns*, predicted in 1952 and now
    understood to underlie animal coat markings, sea-shell pigmentation,
    and chemical oscillations.

    PDE:
        ∂U/∂t = Dᵤ ∇²U  −  U V²  +  F (1 − U)
        ∂V/∂t = Dᵥ ∇²V  +  U V²  −  (F + k) V

    Numerics:
        • Spatial discretisation — 5-point Laplacian stencil (2nd-order finite
          differences) with periodic boundary conditions.
        • Time integration — forward Euler (explicit), stable for the diffusion
          constants and grid spacing used here.

    Topics covered:
        1. Gray-Scott model implementation (vectorised NumPy)
        2. Parameter sweep — four classic pattern regimes
        3. Diagnostic figure — concentration fields + time-evolution snapshots
        4. Artistic figure — high-resolution Turing pattern mosaic
        5. Artistic figure — single pattern with phase-gradient colouring

    Run:  python reaction_diffusion.py
    Deps: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. GRAY-SCOTT MODEL ---
# ─────────────────────────────────────────────────────────────────────────────

def laplacian_2d(Z, dx):
    """
    5-point discrete Laplacian on a 2D array with periodic (wrap-around)
    boundary conditions.  Returns ∇²Z with the same shape as Z.
    """
    return (
        np.roll(Z, +1, axis=0) + np.roll(Z, -1, axis=0) +
        np.roll(Z, +1, axis=1) + np.roll(Z, -1, axis=1) - 4 * Z
    ) / dx**2


def gray_scott_step(U, V, Du, Dv, F, k, dt, dx):
    """
    One forward-Euler time step of the Gray-Scott system.
    Modifies U, V in place for performance (avoids allocation each step).
    """
    lap_U = laplacian_2d(U, dx)
    lap_V = laplacian_2d(V, dx)
    uvv = U * V * V
    U += dt * (Du * lap_U - uvv + F * (1.0 - U))
    V += dt * (Dv * lap_V + uvv - (F + k) * V)
    return U, V


def init_grid(N, seed_radius=6, n_seeds=5, rng=None):
    """
    Initialise the concentration fields.
    U = 1 everywhere, V = 0 everywhere, then seed small square patches of
    V = 0.25 (with U = 0.5 inside them) plus a dusting of noise.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    U = np.ones((N, N))
    V = np.zeros((N, N))
    # seed patches to break symmetry
    for _ in range(n_seeds):
        cx = rng.integers(seed_radius, N - seed_radius)
        cy = rng.integers(seed_radius, N - seed_radius)
        U[cx-seed_radius:cx+seed_radius, cy-seed_radius:cy+seed_radius] = 0.50
        V[cx-seed_radius:cx+seed_radius, cy-seed_radius:cy+seed_radius] = 0.25
    # light noise to encourage natural symmetry-breaking
    U += 0.02 * rng.standard_normal((N, N))
    V += 0.02 * rng.standard_normal((N, N))
    return np.clip(U, 0, 1), np.clip(V, 0, 1)


def simulate(N, Du, Dv, F, k, n_steps, dt=1.0, dx=1.0,
             snapshot_every=None, seed=42):
    """
    Run the Gray-Scott simulation and return the final (U, V) fields.
    If *snapshot_every* is given, also return a list of V-field snapshots
    at the requested interval (useful for time-lapse visualisation).
    """
    rng = np.random.default_rng(seed)
    U, V = init_grid(N, seed_radius=max(3, N // 40), n_seeds=6, rng=rng)
    snapshots = []
    for step in range(n_steps):
        U, V = gray_scott_step(U, V, Du, Dv, F, k, dt, dx)
        if snapshot_every and step % snapshot_every == 0:
            snapshots.append(V.copy())
    if snapshot_every:
        return U, V, snapshots
    return U, V


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. PATTERN REGIMES ---
# ─────────────────────────────────────────────────────────────────────────────
# The Gray-Scott model's behaviour depends critically on (F, k).
# Four classic regimes — each producing a qualitatively different Turing pattern.

REGIMES = {
    "Mitosis (self-replicating spots)": dict(F=0.0367, k=0.0649),
    "Coral / labyrinthine":            dict(F=0.0545, k=0.0620),
    "Spots (solitons)":                dict(F=0.0300, k=0.0620),
    "Worms / stripes":                 dict(F=0.0580, k=0.0650),
}


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. COMPUTE DATA ---
# ─────────────────────────────────────────────────────────────────────────────

N_GRID    = 200          # spatial resolution
DU, DV    = 0.16, 0.08   # diffusion coefficients (Du > Dv is essential)
DT, DX    = 1.0, 1.0
N_STEPS   = 18000        # enough iterations for patterns to mature

# --- (a) Time-evolution snapshots for the coral regime ----------------------
print("Simulating coral regime with time-evolution snapshots …")
snap_regime = REGIMES["Coral / labyrinthine"]
U_snap, V_snap, time_snaps = simulate(
    N_GRID, DU, DV, snap_regime["F"], snap_regime["k"],
    n_steps=N_STEPS, dt=DT, dx=DX,
    snapshot_every=N_STEPS // 8, seed=42,
)

# --- (b) All four regimes for the parameter sweep --------------------------
regime_results = {}
for name, params in REGIMES.items():
    print(f"Simulating: {name}  (F={params['F']}, k={params['k']}) …")
    U_r, V_r = simulate(N_GRID, DU, DV, params["F"], params["k"],
                         n_steps=N_STEPS, dt=DT, dx=DX)
    regime_results[name] = V_r


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. DIAGNOSTIC FIGURE ---
# ─────────────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(16, 11))
fig.suptitle("Reaction-Diffusion — Gray-Scott Model  ·  Diagnostic Overview",
             fontsize=14, fontweight='bold', y=0.98)
gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.40, wspace=0.25)

# ── Row 1: time evolution of the coral regime (4 snapshots) ────────────────
snap_indices = [0, len(time_snaps)//3, 2*len(time_snaps)//3, -1]
snap_labels  = ["Early", "Developing", "Maturing", "Steady state"]
for col, (idx, label) in enumerate(zip(snap_indices, snap_labels)):
    ax = fig.add_subplot(gs[0, col])
    ax.imshow(time_snaps[idx], cmap='inferno', vmin=0, vmax=0.35,
              interpolation='bilinear')
    ax.set_title(f"{label}\nstep ≈ {idx * (N_STEPS // 8) if idx >= 0 else N_STEPS}",
                 fontsize=10, fontweight='bold')
    ax.set_xticks([]); ax.set_yticks([])
    if col == 0:
        ax.set_ylabel("Time evolution\n(coral regime)", fontsize=10)

# ── Row 2: four pattern regimes ───────────────────────────────────────────
for col, (name, V_field) in enumerate(regime_results.items()):
    ax = fig.add_subplot(gs[1, col])
    ax.imshow(V_field, cmap='cividis', vmin=0, vmax=0.35,
              interpolation='bilinear')
    short_name = name.split("(")[0].strip() if "(" in name else name.split("/")[0].strip()
    ax.set_title(short_name, fontsize=10, fontweight='bold')
    # Show F, k below the title
    params = REGIMES[name]
    ax.set_xlabel(f"F = {params['F']},  k = {params['k']}", fontsize=8,
                  color='#555555')
    ax.set_xticks([]); ax.set_yticks([])
    if col == 0:
        ax.set_ylabel("Parameter sweep\n(V concentration)", fontsize=10)

plt.savefig("rd_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: rd_diagnostic.png")
plt.show()
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. ARTISTIC FIGURE — TURING PATTERN MOSAIC ---
# ─────────────────────────────────────────────────────────────────────────────
# High-resolution render of all four regimes, dark background, custom colourmap,
# presented as museum-quality panels.

print("\nRendering Turing pattern mosaic …")

# Higher-res simulation for the artistic panels
N_ART   = 300
N_STEPS_ART = 25000

art_results = {}
for name, params in REGIMES.items():
    print(f"  High-res: {name} …")
    _, V_a = simulate(N_ART, DU, DV, params["F"], params["k"],
                       n_steps=N_STEPS_ART, dt=DT, dx=DX, seed=42)
    art_results[name] = V_a

# Custom colourmap: deep ocean → bioluminescent teal → warm white
cmap_turing = LinearSegmentedColormap.from_list("turing", [
    (0.00, "#050520"),    # deep void
    (0.15, "#0a1628"),    # dark ocean
    (0.30, "#0d3b66"),    # deep blue
    (0.50, "#1b998b"),    # teal / viridian
    (0.70, "#4ecdc4"),    # bioluminescent
    (0.85, "#f7fff7"),    # pale glow
    (1.00, "#ffe66d"),    # warm highlight
])

with plt.style.context('dark_background'):

    fig_art, axes = plt.subplots(2, 2, figsize=(13, 13))
    fig_art.patch.set_facecolor('#050510')

    fig_art.suptitle(
        "T U R I N G   P A T T E R N S\n"
        r"Gray-Scott reaction-diffusion  ·  $D_u = 0.16, \; D_v = 0.08$",
        color='white', alpha=0.75, fontsize=16, fontweight='bold', y=0.97,
    )

    for ax, (name, V_field) in zip(axes.flat, art_results.items()):
        ax.imshow(V_field, cmap=cmap_turing, vmin=0, vmax=0.35,
                  interpolation='bilinear')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('#1a1a2e')

        # Clean label
        short = name.split("(")[0].strip() if "(" in name else name.split("/")[0].strip()
        params = REGIMES[name]
        ax.set_title(f"{short}\nF = {params['F']},  k = {params['k']}",
                     color='white', alpha=0.65, fontsize=11, fontweight='bold',
                     pad=8)

    plt.subplots_adjust(wspace=0.06, hspace=0.15)
    plt.savefig("rd_turing_mosaic_artistic.png", dpi=200, bbox_inches='tight',
                facecolor=fig_art.get_facecolor())
    print("Saved: rd_turing_mosaic_artistic.png")
    plt.show()
    plt.close(fig_art)


# ─────────────────────────────────────────────────────────────────────────────
# --- 6. ARTISTIC FIGURE — SINGLE PATTERN, PHASE-GRADIENT COLOURING ---
# ─────────────────────────────────────────────────────────────────────────────
# Take the coral/labyrinthine pattern and colour it by the local gradient
# magnitude of V — revealing the sharp reaction fronts as luminous contours
# against a dark background.  The effect is reminiscent of a topographic map
# lit from within.

print("\nRendering phase-gradient visualisation …")

V_coral = art_results["Coral / labyrinthine"]
# Compute gradient magnitude via central differences
Vy, Vx = np.gradient(V_coral)
grad_mag = np.sqrt(Vx**2 + Vy**2)

# Custom colourmap: void → electric blue → magenta → gold fire
cmap_gradient = LinearSegmentedColormap.from_list("gradient_fire", [
    (0.00, "#020106"),
    (0.12, "#0d0221"),
    (0.25, "#261447"),
    (0.38, "#6b1d7a"),
    (0.50, "#c94277"),
    (0.62, "#f04f78"),
    (0.75, "#f7a156"),
    (0.88, "#fcf6b1"),
    (1.00, "#ffffff"),
])

with plt.style.context('dark_background'):

    fig_grad, ax_grad = plt.subplots(figsize=(11, 11))
    fig_grad.patch.set_facecolor('#020106')
    ax_grad.set_facecolor('#020106')

    # Layer 1: gradient magnitude as luminous contours
    ax_grad.imshow(grad_mag, cmap=cmap_gradient, interpolation='bilinear',
                   vmin=0, vmax=np.percentile(grad_mag, 99))

    # Layer 2: faint V-field underlay for depth
    ax_grad.imshow(V_coral, cmap='bone', alpha=0.08, interpolation='bilinear')

    ax_grad.set_xticks([]); ax_grad.set_yticks([])
    for sp in ax_grad.spines.values():
        sp.set_edgecolor('#0d0221')

    ax_grad.set_title(
        "R E A C T I O N   F R O N T S\n"
        r"$|\nabla V|$  of the Gray-Scott labyrinthine pattern",
        color='white', alpha=0.75, fontsize=15, fontweight='bold', pad=16,
    )

    ax_grad.annotate(
        "Sharp reaction fronts separate\n"
        "regions of high and low activator\n"
        "concentration — the signature of\n"
        "a Turing instability",
        xy=(0.03, 0.04), xycoords='axes fraction',
        fontsize=9, color='#888888', alpha=0.7, style='italic',
        verticalalignment='bottom',
    )

    plt.tight_layout()
    plt.savefig("rd_reaction_fronts_artistic.png", dpi=200, bbox_inches='tight',
                facecolor=fig_grad.get_facecolor())
    print("Saved: rd_reaction_fronts_artistic.png")
    plt.show()
    plt.close(fig_grad)


print("\nAll plots complete.")
