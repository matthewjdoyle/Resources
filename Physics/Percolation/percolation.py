# -*- coding: utf-8 -*-
"""
    Percolation Theory — Monte Carlo Simulation
    =============================================
    Site and bond percolation on a 2D square lattice.  The simulation uses a
    weighted quick-union–find with path compression for efficient cluster
    detection, and a Newman-Ziff–style permutation sweep for the animated
    transition.

    Topics covered:
        1. Union-Find data structure
        2. Site percolation (random site occupation)
        3. Bond percolation (random bond activation)
        4. Spanning cluster detection (top ↔ bottom)
        5. Order parameter P∞(p) — fraction of sites in spanning cluster
        6. Cluster size distribution at criticality
        7. Finite-size scaling collapse
        8. Monte Carlo threshold estimation for multiple lattice sizes
        9. Diagnostic figure — 2×2 grid
       10. Artistic lattice figures — below, at, and above threshold
       11. Animated GIF — Newman-Ziff sweep from p = 0 to p = 1

    Run:  python percolation.py
    Deps: numpy, matplotlib, pillow (for GIF via PillowWriter)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.animation import PillowWriter
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. UNION-FIND ---
# ─────────────────────────────────────────────────────────────────────────────

class UnionFind:
    """Weighted quick-union with path compression."""

    def __init__(self, n):
        self.parent = np.arange(n, dtype=np.int32)
        self.size = np.ones(n, dtype=np.int32)

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # path compression
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # weighted: attach smaller tree under larger
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]

    def component_size(self, x):
        return self.size[self.find(x)]


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. SITE PERCOLATION ---
# ─────────────────────────────────────────────────────────────────────────────

def site_percolation(L, p, rng=None):
    """
    Generate a site-percolation configuration on an L×L square lattice.
    Each site is open with probability p.
    Returns:
        grid   — boolean L×L array (True = open)
        labels — integer L×L array with cluster labels (-1 = closed)
        uf     — UnionFind instance for the open sites
    """
    if rng is None:
        rng = np.random.default_rng()
    grid = rng.random((L, L)) < p
    uf = UnionFind(L * L)
    labels = -np.ones((L, L), dtype=np.int32)

    for i in range(L):
        for j in range(L):
            if not grid[i, j]:
                continue
            idx = i * L + j
            # connect to open right and down neighbours
            if j + 1 < L and grid[i, j + 1]:
                uf.union(idx, i * L + j + 1)
            if i + 1 < L and grid[i + 1, j]:
                uf.union(idx, (i + 1) * L + j)

    for i in range(L):
        for j in range(L):
            if grid[i, j]:
                labels[i, j] = uf.find(i * L + j)

    return grid, labels, uf


def has_spanning_cluster(grid, labels, uf, L):
    """Check whether any cluster connects the top row to the bottom row."""
    top_roots = set()
    for j in range(L):
        if grid[0, j]:
            top_roots.add(uf.find(j))
    for j in range(L):
        if grid[L - 1, j]:
            if uf.find((L - 1) * L + j) in top_roots:
                return True
    return False


def spanning_cluster_mask(grid, labels, uf, L):
    """Return a boolean mask of sites belonging to the spanning cluster."""
    top_roots = set()
    for j in range(L):
        if grid[0, j]:
            top_roots.add(uf.find(j))
    spanning_roots = set()
    for j in range(L):
        if grid[L - 1, j]:
            r = uf.find((L - 1) * L + j)
            if r in top_roots:
                spanning_roots.add(r)
    if not spanning_roots:
        return np.zeros((L, L), dtype=bool)
    mask = np.zeros((L, L), dtype=bool)
    for i in range(L):
        for j in range(L):
            if grid[i, j] and uf.find(i * L + j) in spanning_roots:
                mask[i, j] = True
    return mask


def order_parameter(grid, labels, uf, L):
    """Fraction of open sites in the spanning cluster (P∞)."""
    mask = spanning_cluster_mask(grid, labels, uf, L)
    n_open = grid.sum()
    if n_open == 0:
        return 0.0
    return mask.sum() / n_open


def cluster_size_distribution(grid, labels, uf, L):
    """Return {size: count} for finite (non-spanning) clusters."""
    span_mask = spanning_cluster_mask(grid, labels, uf, L)
    root_counted = set()
    sizes = []
    for i in range(L):
        for j in range(L):
            if grid[i, j] and not span_mask[i, j]:
                r = uf.find(i * L + j)
                if r not in root_counted:
                    root_counted.add(r)
                    sizes.append(uf.component_size(r))
    return Counter(sizes)


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. BOND PERCOLATION ---
# ─────────────────────────────────────────────────────────────────────────────

def bond_percolation(L, p, rng=None):
    """
    Generate a bond-percolation configuration on an L×L square lattice.
    All sites are open; each bond is active with probability p.
    Returns:
        labels — integer L×L array with cluster labels
        uf     — UnionFind instance
    """
    if rng is None:
        rng = np.random.default_rng()
    uf = UnionFind(L * L)
    for i in range(L):
        for j in range(L):
            idx = i * L + j
            if j + 1 < L and rng.random() < p:
                uf.union(idx, i * L + j + 1)
            if i + 1 < L and rng.random() < p:
                uf.union(idx, (i + 1) * L + j)
    labels = np.array([uf.find(k) for k in range(L * L)], dtype=np.int32).reshape(L, L)
    return labels, uf


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. MONTE CARLO SWEEPS ---
# ─────────────────────────────────────────────────────────────────────────────

def sweep_percolation_probability(L, p_values, n_trials=200, rng=None):
    """Monte Carlo estimate of Π(p) — probability that a spanning cluster exists."""
    if rng is None:
        rng = np.random.default_rng(42)
    results = np.zeros(len(p_values))
    for ip, p in enumerate(p_values):
        count = 0
        for _ in range(n_trials):
            grid, labels, uf = site_percolation(L, p, rng)
            if has_spanning_cluster(grid, labels, uf, L):
                count += 1
        results[ip] = count / n_trials
    return results


def sweep_order_parameter(L, p_values, n_trials=100, rng=None):
    """Monte Carlo estimate of P∞(p) — average order parameter."""
    if rng is None:
        rng = np.random.default_rng(42)
    results = np.zeros(len(p_values))
    for ip, p in enumerate(p_values):
        total = 0.0
        for _ in range(n_trials):
            grid, labels, uf = site_percolation(L, p, rng)
            total += order_parameter(grid, labels, uf, L)
        results[ip] = total / n_trials
    return results


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. NEWMAN-ZIFF PERMUTATION SWEEP ---
# ─────────────────────────────────────────────────────────────────────────────

def newman_ziff_sweep(L, rng=None):
    """
    Open sites one at a time in a random permutation order.
    At each step, record:
        p          — fraction of sites open so far
        grid       — boolean L×L occupancy
        uf         — UnionFind state
        is_spanning — whether a spanning cluster exists
    Yields (p, grid, uf, is_spanning) at each step.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    N = L * L
    perm = rng.permutation(N)
    grid = np.zeros((L, L), dtype=bool)
    uf = UnionFind(N)

    for step, site in enumerate(perm, 1):
        i, j = divmod(int(site), L)
        grid[i, j] = True
        idx = i * L + j
        # connect to open neighbours
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < L and 0 <= nj < L and grid[ni, nj]:
                uf.union(idx, ni * L + nj)
        p = step / N
        spanning = has_spanning_cluster(grid, grid, uf, L)
        yield p, grid.copy(), uf, spanning


# ─────────────────────────────────────────────────────────────────────────────
# --- 6. COLOUR MAPS ---
# ─────────────────────────────────────────────────────────────────────────────

# Artistic lattice: cool tones for small clusters, gold for spanning
CMAP_CLUSTERS = LinearSegmentedColormap.from_list("percolation_clusters", [
    (0.00, "#0a0a2e"),   # void
    (0.15, "#1a1a4e"),   # deep indigo
    (0.30, "#2d4a7a"),   # steel blue
    (0.50, "#3d8b8b"),   # teal
    (0.70, "#6bb5a0"),   # sage
    (0.85, "#a5d6a7"),   # mint
    (1.00, "#c5e8c5"),   # pale green
])

GOLD = "#d4a017"
GOLD_BRIGHT = "#ffd700"


def lattice_art_image(grid, labels, uf, L, highlight_spanning=True):
    """
    Build an RGBA image of the lattice.
    Closed sites → near-black.
    Non-spanning open clusters → coloured by (cluster root mod 1).
    Spanning cluster → gold.
    """
    img = np.zeros((L, L, 4), dtype=np.float64)
    # background: dark
    img[..., 3] = 1.0
    img[~grid, :3] = [0.03, 0.03, 0.06]

    span_mask = spanning_cluster_mask(grid, labels, uf, L) if highlight_spanning else np.zeros((L, L), dtype=bool)

    # colour non-spanning open sites
    open_nonspan = grid & ~span_mask
    if open_nonspan.any():
        # use cluster root to assign a pseudo-random hue
        roots = np.zeros((L, L), dtype=np.float64)
        for i in range(L):
            for j in range(L):
                if open_nonspan[i, j]:
                    roots[i, j] = (uf.find(i * L + j) * 0.618033988749895) % 1.0
        colours = CMAP_CLUSTERS(roots)
        img[open_nonspan] = colours[open_nonspan]

    # spanning cluster in gold
    if span_mask.any():
        img[span_mask, :3] = [0.831, 0.627, 0.090]  # gold
        img[span_mask, 3] = 1.0

    return img


# ─────────────────────────────────────────────────────────────────────────────
# --- 7. COMPUTE DATA ---
# ─────────────────────────────────────────────────────────────────────────────

PC_SITE = 0.592746    # exact site percolation threshold (square lattice)
BETA    = 5.0 / 36.0  # order parameter exponent
NU      = 4.0 / 3.0   # correlation length exponent

rng = np.random.default_rng(42)

# --- (a) Spanning probability Π(p) for multiple lattice sizes ----------------
print("Computing spanning probability Pi(p) for L = 16, 32, 64, 128 ...")
LATTICE_SIZES = [16, 32, 64, 128]
P_VALUES = np.linspace(0.40, 0.80, 60)
pi_curves = {}
for L in LATTICE_SIZES:
    n_trials = 400 if L <= 32 else (200 if L <= 64 else 100)
    print(f"  L = {L}  ({n_trials} trials per p-value) ...")
    pi_curves[L] = sweep_percolation_probability(L, P_VALUES, n_trials=n_trials, rng=rng)

# --- (b) Order parameter P∞(p) for L = 64 -----------------------------------
print("Computing order parameter P_inf(p) for L = 64 ...")
P_VALUES_OP = np.linspace(0.45, 0.85, 50)
P_inf = sweep_order_parameter(64, P_VALUES_OP, n_trials=100, rng=rng)

# --- (c) Cluster size distribution at p_c for L = 128 -----------------------
print("Computing cluster size distribution at p_c for L = 128 ...")
n_csd_trials = 50
combined_csd = Counter()
for _ in range(n_csd_trials):
    grid, labels, uf = site_percolation(128, PC_SITE, rng)
    combined_csd += cluster_size_distribution(grid, labels, uf, 128)


# ─────────────────────────────────────────────────────────────────────────────
# --- 8. DIAGNOSTIC FIGURE (2×2) ---
# ─────────────────────────────────────────────────────────────────────────────

print("\nRendering diagnostic figure ...")

fig = plt.figure(figsize=(14, 12))
fig.suptitle("Percolation — Diagnostic Overview",
             fontsize=14, fontweight='bold', y=0.98)
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.30)

# ── Panel 1: Spanning probability Π(p) ──────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
colours_L = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
for L, col in zip(LATTICE_SIZES, colours_L):
    ax1.plot(P_VALUES, pi_curves[L], '-', color=col, linewidth=1.5,
             label=f'L = {L}')
ax1.axvline(PC_SITE, color='grey', linestyle='--', alpha=0.6, label=f'$p_c$ = {PC_SITE:.4f}')
ax1.set_xlabel('Occupation probability $p$')
ax1.set_ylabel(r'Spanning probability $\Pi(p)$')
ax1.set_title(r'$\Pi(p)$ vs $p$', fontsize=11, fontweight='bold')
ax1.legend(fontsize=8, loc='lower right')
ax1.set_xlim(0.40, 0.80)
ax1.set_ylim(-0.05, 1.05)

# ── Panel 2: Order parameter P∞(p) ─────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(P_VALUES_OP, P_inf, 'o-', color='#2ca02c', markersize=3, linewidth=1.2)
ax2.axvline(PC_SITE, color='grey', linestyle='--', alpha=0.6, label=f'$p_c$')
ax2.set_xlabel('Occupation probability $p$')
ax2.set_ylabel(r'Order parameter $P_\infty(p)$')
ax2.set_title(r'$P_\infty(p)$ vs $p$  (L = 64)', fontsize=11, fontweight='bold')
ax2.legend(fontsize=8)
ax2.set_xlim(0.45, 0.85)

# ── Panel 3: Cluster size distribution (log-log) ───────────────────────────
ax3 = fig.add_subplot(gs[1, 0])
sizes = sorted(combined_csd.keys())
counts = [combined_csd[s] for s in sizes]
ax3.scatter(sizes, counts, s=8, color='#9467bd', alpha=0.7, edgecolors='none')
# power-law guide: n_s ~ s^{-tau}, tau = 187/91 ≈ 2.055
s_fit = np.array(sizes, dtype=float)
counts_arr = np.array(counts, dtype=float)
if len(s_fit) > 2:
    tau = 187.0 / 91.0
    # restrict guide line to s < L where power-law holds (finite-size cutoff)
    scaling_mask = s_fit < 128
    s_scaling = s_fit[scaling_mask]
    counts_scaling = counts_arr[scaling_mask]
    mid = len(s_scaling) // 4
    c_guide = counts_scaling[mid] * s_scaling[mid]**tau
    ax3.plot(s_scaling, c_guide * s_scaling**(-tau), '--', color='#e377c2', alpha=0.8,
             label=rf'$\tau = 187/91 \approx {tau:.2f}$')
ax3.set_xscale('log')
ax3.set_yscale('log')
ax3.set_xlabel('Cluster size $s$')
ax3.set_ylabel('Count $n_s$')
ax3.set_title(f'Cluster size distribution at $p_c$  (L = 128)', fontsize=11, fontweight='bold')
ax3.legend(fontsize=8)

# ── Panel 4: Finite-size scaling collapse ───────────────────────────────────
ax4 = fig.add_subplot(gs[1, 1])
for L, col in zip(LATTICE_SIZES, colours_L):
    x_scaled = (P_VALUES - PC_SITE) * L**(1.0 / NU)
    ax4.plot(x_scaled, pi_curves[L], '-', color=col, linewidth=1.5,
             label=f'L = {L}')
ax4.axvline(0, color='grey', linestyle='--', alpha=0.4)
ax4.set_xlabel(r'$(p - p_c)\,L^{1/\nu}$')
ax4.set_ylabel(r'$\Pi(p)$')
ax4.set_title(r'Finite-size scaling collapse ($\nu = 4/3$)', fontsize=11, fontweight='bold')
ax4.legend(fontsize=8, loc='lower right')

plt.savefig("Physics/Percolation/perc_diagnostic.png", dpi=150, bbox_inches='tight')
print("Saved: perc_diagnostic.png")
plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# --- 9. ARTISTIC LATTICE FIGURES ---
# ─────────────────────────────────────────────────────────────────────────────

L_ART = 150

def render_artistic_lattice(p, filename, title_text, subtitle_text,
                            require_spanning=False):
    """Render a single artistic lattice figure with dark background."""
    print(f"  Rendering {filename} (p = {p}) ...")
    seed = 42
    while True:
        trial_rng = np.random.default_rng(seed)
        grid, labels, uf = site_percolation(L_ART, p, trial_rng)
        if not require_spanning or has_spanning_cluster(grid, labels, uf, L_ART):
            break
        seed += 1
    img = lattice_art_image(grid, labels, uf, L_ART)

    with plt.style.context('dark_background'):
        fig, ax = plt.subplots(figsize=(10, 10))
        fig.patch.set_facecolor('#050510')
        ax.set_facecolor('#050510')
        ax.imshow(img, interpolation='nearest')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('#1a1a2e')

        ax.set_title(
            f"{title_text}\n{subtitle_text}",
            color='white', alpha=0.75, fontsize=14, fontweight='bold', pad=14,
        )

        plt.tight_layout()
        plt.savefig(f"Physics/Percolation/{filename}", dpi=200, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        plt.close(fig)
    print(f"  Saved: {filename}")


print("\nRendering artistic lattice figures ...")
render_artistic_lattice(0.45, "perc_lattice_below_artistic.png",
                        "B E L O W   T H R E S H O L D",
                        r"$p = 0.45 < p_c$  —  small isolated clusters")

render_artistic_lattice(PC_SITE, "perc_lattice_critical_artistic.png",
                        "A T   T H R E S H O L D",
                        rf"$p \approx {PC_SITE}$  —  fractal spanning cluster",
                        require_spanning=True)

render_artistic_lattice(0.75, "perc_lattice_above_artistic.png",
                        "A B O V E   T H R E S H O L D",
                        r"$p = 0.75 > p_c$  —  dominant spanning cluster")


# ─────────────────────────────────────────────────────────────────────────────
# --- 10. ANIMATED GIF — NEWMAN-ZIFF SWEEP ---
# ─────────────────────────────────────────────────────────────────────────────

print("\nRendering percolation transition GIF ...")

L_GIF = 100
N_GIF = L_GIF * L_GIF
N_FRAMES = 96
frame_interval = max(1, N_GIF // N_FRAMES)

# Pre-compute all frames via Newman-Ziff
frames = []
sweep_rng = np.random.default_rng(42)

# Build the full sweep and sample frames
perm = sweep_rng.permutation(N_GIF)
grid_gif = np.zeros((L_GIF, L_GIF), dtype=bool)
uf_gif = UnionFind(N_GIF)

frame_count = 0
for step, site in enumerate(perm, 1):
    i, j = divmod(int(site), L_GIF)
    grid_gif[i, j] = True
    idx = i * L_GIF + j
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < L_GIF and 0 <= nj < L_GIF and grid_gif[ni, nj]:
            uf_gif.union(idx, ni * L_GIF + nj)

    if step % frame_interval == 0 or step == N_GIF:
        p_val = step / N_GIF
        # Build labels for current state
        labels_gif = -np.ones((L_GIF, L_GIF), dtype=np.int32)
        for ii in range(L_GIF):
            for jj in range(L_GIF):
                if grid_gif[ii, jj]:
                    labels_gif[ii, jj] = uf_gif.find(ii * L_GIF + jj)
        img = lattice_art_image(grid_gif, labels_gif, uf_gif, L_GIF)
        frames.append((p_val, img))
        frame_count += 1
        if frame_count >= N_FRAMES:
            break

# Build animation
with plt.style.context('dark_background'):
    fig_gif, ax_gif = plt.subplots(figsize=(8, 8))
    fig_gif.patch.set_facecolor('#050510')
    ax_gif.set_facecolor('#050510')
    ax_gif.set_xticks([]); ax_gif.set_yticks([])
    for sp in ax_gif.spines.values():
        sp.set_edgecolor('#1a1a2e')

    im = ax_gif.imshow(frames[0][1], interpolation='nearest')
    title = ax_gif.set_title(
        f"P E R C O L A T I O N   T R A N S I T I O N\n$p = {frames[0][0]:.3f}$",
        color='white', alpha=0.75, fontsize=13, fontweight='bold', pad=12,
    )

    writer = PillowWriter(fps=12)
    gif_path = "Physics/Percolation/perc_transition.gif"
    with writer.saving(fig_gif, gif_path, dpi=100):
        for p_val, img in frames:
            im.set_data(img)
            title.set_text(
                f"P E R C O L A T I O N   T R A N S I T I O N\n$p = {p_val:.3f}$"
            )
            writer.grab_frame()

    plt.close(fig_gif)

print(f"Saved: perc_transition.gif  ({len(frames)} frames)")
print("\nAll plots complete.")
