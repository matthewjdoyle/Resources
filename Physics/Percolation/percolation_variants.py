# -*- coding: utf-8 -*-
"""
    Percolation Variants
    ====================
    Five exotic percolation models on 2D square lattices, each with a distinct
    physical motivation and visual signature.

    Variants:
        1. Gradient percolation     — spatially varying p(x)
        2. Explosive percolation    — Achlioptas product rule
        3. Bootstrap percolation    — k-core pruning (k=3)
        4. Invasion percolation     — greedy growth from seed
        5. Directed percolation     — bonds only go down/right

    Run:  python percolation_variants.py
    Deps: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap, Normalize
from collections import deque
import heapq
from matplotlib.animation import PillowWriter
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ─────────────────────────────────────────────────────────────────────────────
# --- UNION-FIND ---
# ─────────────────────────────────────────────────────────────────────────────

class UnionFind:
    """Weighted quick-union with path compression."""

    def __init__(self, n):
        self.parent = np.arange(n, dtype=np.int32)
        self.size = np.ones(n, dtype=np.int32)

    def find(self, x):
        root = int(x)
        while self.parent[root] != root:
            root = self.parent[root]
        xi = int(x)
        while self.parent[xi] != root:
            self.parent[xi], xi = root, self.parent[xi]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]

    def component_size(self, x):
        return int(self.size[self.find(x)])


# ─────────────────────────────────────────────────────────────────────────────
# --- COLOUR HELPERS ---
# ─────────────────────────────────────────────────────────────────────────────

DARK_BG = '#0e1117'

def _save(fig, name):
    path = os.path.join(SCRIPT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  saved {name}')


# ═════════════════════════════════════════════════════════════════════════════
# 1. GRADIENT PERCOLATION
# ═════════════════════════════════════════════════════════════════════════════

def gradient_percolation(L=200, seed=42):
    """
    p(x) = 1 - x/L varies linearly across columns.
    The percolation front (boundary of the spanning cluster) is a fractal curve.
    """
    rng = np.random.default_rng(seed)
    p_field = np.tile(1.0 - np.arange(L) / L, (L, 1))  # p decreases left→right
    grid = rng.random((L, L)) < p_field

    uf = UnionFind(L * L)
    for i in range(L):
        for j in range(L):
            if not grid[i, j]:
                continue
            idx = i * L + j
            if j + 1 < L and grid[i, j + 1]:
                uf.union(idx, i * L + j + 1)
            if i + 1 < L and grid[i + 1, j]:
                uf.union(idx, (i + 1) * L + j)

    # find spanning cluster (top ↔ bottom)
    top_roots = {uf.find(j) for j in range(L) if grid[0, j]}
    bot_roots = {uf.find((L - 1) * L + j) for j in range(L) if grid[L - 1, j]}
    spanning = top_roots & bot_roots

    labels = np.full((L, L), np.nan)
    front = np.zeros((L, L), dtype=bool)

    for i in range(L):
        for j in range(L):
            if grid[i, j]:
                r = uf.find(i * L + j)
                if r in spanning:
                    labels[i, j] = j / L  # colour by x-position
                    # detect front: open site adjacent to a closed site
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < L and 0 <= nj < L and not grid[ni, nj]:
                            front[i, j] = True
                            break
                else:
                    labels[i, j] = -1  # non-spanning cluster

    return grid, labels, front, p_field


def plot_gradient_artistic(L=200, seed=42):
    grid, labels, front, p_field = gradient_percolation(L, seed)
    fig, ax = plt.subplots(figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    # background: p(x) gradient
    cmap_bg = LinearSegmentedColormap.from_list('pbg', ['#1a237e', '#b71c1c'], N=256)
    ax.imshow(p_field, cmap=cmap_bg, alpha=0.25, interpolation='nearest')

    # spanning cluster coloured by position
    cmap_span = LinearSegmentedColormap.from_list('span', ['#1565c0', '#e65100'], N=256)
    span_vis = np.where(labels >= 0, labels, np.nan)
    ax.imshow(span_vis, cmap=cmap_span, alpha=0.7, interpolation='nearest')

    # fractal front in gold
    front_vis = np.where(front, 1.0, np.nan)
    ax.imshow(front_vis, cmap=LinearSegmentedColormap.from_list('g', ['#ffd600', '#ffd600']),
              alpha=0.95, interpolation='nearest')

    ax.set_axis_off()
    ax.set_title('Gradient Percolation', color='white', fontsize=14, fontweight='bold', pad=10)
    _save(fig, 'perc_gradient_artistic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 2. EXPLOSIVE PERCOLATION (ACHLIOPTAS PROCESS)
# ═════════════════════════════════════════════════════════════════════════════

def explosive_percolation(L=200, seed=42):
    """
    Achlioptas product rule: at each step pick two random bonds, add the one
    whose merger produces the smaller resulting component (product rule).
    This delays the giant component, producing an abrupt-looking transition.
    """
    N = L * L
    rng = np.random.default_rng(seed)
    uf = UnionFind(N)

    # generate all possible bonds
    bonds = []
    for i in range(L):
        for j in range(L):
            idx = i * L + j
            if j + 1 < L:
                bonds.append((idx, i * L + j + 1))
            if i + 1 < L:
                bonds.append((idx, (i + 1) * L + j))
    rng.shuffle(bonds)

    max_comp = 0
    added = 0
    total_bonds = len(bonds)

    # add bonds using product rule
    b = 0
    occupied = np.zeros(N, dtype=bool)
    history = []
    while b + 1 < total_bonds:
        b1 = bonds[b]
        b2 = bonds[b + 1]
        b += 2

        # product of component sizes after each merge
        s1a, s1b = uf.component_size(b1[0]), uf.component_size(b1[1])
        s2a, s2b = uf.component_size(b2[0]), uf.component_size(b2[1])

        if uf.find(b1[0]) != uf.find(b1[1]):
            prod1 = s1a * s1b
        else:
            prod1 = float('inf')  # already connected

        if uf.find(b2[0]) != uf.find(b2[1]):
            prod2 = s2a * s2b
        else:
            prod2 = float('inf')

        # pick the bond that minimises the product (delays giant component)
        if prod1 <= prod2:
            chosen = b1
        else:
            chosen = b2

        if uf.find(chosen[0]) != uf.find(chosen[1]):
            uf.union(chosen[0], chosen[1])
            added += 1
            occupied[chosen[0]] = True
            occupied[chosen[1]] = True

        new_max = max(uf.component_size(chosen[0]), max_comp)
        if new_max > max_comp:
            max_comp = new_max
            # record when giant component jumps
            history.append((added, max_comp))

        # stop once giant component has ~40% of sites
        if max_comp > 0.4 * N:
            break

    # build labels: colour by component
    labels = np.zeros((L, L), dtype=int)
    for i in range(L):
        for j in range(L):
            labels[i, j] = uf.find(i * L + j)

    # find the giant component root
    sizes = {}
    for i in range(N):
        r = uf.find(i)
        sizes[r] = uf.component_size(i)
    giant_root = max(sizes, key=sizes.get)

    return labels, giant_root, uf


def plot_explosive_artistic(L=200, seed=42):
    labels, giant_root, uf = explosive_percolation(L, seed)

    fig, ax = plt.subplots(figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    # colour: giant component in hot colours, rest in cool
    img = np.zeros((L, L, 4))
    for i in range(L):
        for j in range(L):
            r = uf.find(i * L + j)
            sz = uf.component_size(i * L + j)
            if r == giant_root:
                # giant component: red/orange gradient by size
                t = min(1.0, sz / (L * L * 0.4))
                img[i, j] = [0.9 + 0.1 * t, 0.3 * (1 - t), 0.05, 0.9]
            elif sz > 5:
                img[i, j] = [0.2, 0.3, 0.6, 0.5]
            else:
                img[i, j] = [0.15, 0.15, 0.2, 0.3]

    ax.imshow(img, interpolation='nearest')
    ax.set_axis_off()
    ax.set_title('Explosive Percolation', color='white', fontsize=14, fontweight='bold', pad=10)
    _save(fig, 'perc_explosive_artistic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 3. BOOTSTRAP PERCOLATION (k-CORE)
# ═════════════════════════════════════════════════════════════════════════════

MOORE_NBRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def bootstrap_percolation(L=200, p=0.55, k=3, seed=42):
    """
    Standard site percolation at probability p, then iteratively prune any
    occupied site with fewer than k occupied neighbours (Moore neighbourhood,
    8 neighbours including diagonals). The surviving sites form the k-core.
    """
    rng = np.random.default_rng(seed)
    grid = rng.random((L, L)) < p
    original = grid.copy()

    # iterative pruning
    changed = True
    while changed:
        changed = False
        to_remove = []
        for i in range(L):
            for j in range(L):
                if not grid[i, j]:
                    continue
                nbrs = 0
                for di, dj in MOORE_NBRS:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < L and 0 <= nj < L and grid[ni, nj]:
                        nbrs += 1
                if nbrs < k:
                    to_remove.append((i, j))
        if to_remove:
            changed = True
            for i, j in to_remove:
                grid[i, j] = False

    return original, grid


def plot_bootstrap_artistic(L=200, p=0.55, k=3, seed=42):
    original, core = bootstrap_percolation(L, p, k, seed)

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor=DARK_BG)
    fig.subplots_adjust(wspace=0.05)

    n_orig = original.sum()
    n_core = core.sum()
    pruned = original & ~core

    for ax_idx, (ax, title_txt) in enumerate(zip(axes, ['Before pruning', 'After pruning'])):
        ax.set_facecolor(DARK_BG)
        img = np.zeros((L, L, 4))
        img[..., 3] = 1.0
        img[..., :3] = [0.03, 0.03, 0.06]  # dark bg for unoccupied

        if ax_idx == 0:
            # before: all occupied sites in warm teal
            img[original, :3] = [0.27, 0.71, 0.67]
            count_txt = f'{n_orig} sites'
        else:
            # after: survivors in vivid green, pruned in faded red
            img[core, :3] = [0.18, 0.85, 0.35]
            img[pruned, :3] = [0.55, 0.15, 0.12]
            img[pruned, 3] = 0.45
            count_txt = f'{n_core} survived, {n_orig - n_core} pruned'

        ax.imshow(img, interpolation='nearest')
        ax.set_axis_off()
        ax.set_title(title_txt, color='white', fontsize=12, fontweight='bold', pad=8)
        ax.text(0.5, -0.02, count_txt, transform=ax.transAxes,
                ha='center', va='top', color='#aaaaaa', fontsize=10)

    fig.suptitle(f'Bootstrap Percolation ($k = {k}$,  $p = {p}$)', color='white',
                 fontsize=14, fontweight='bold', y=0.97)
    _save(fig, 'perc_bootstrap_artistic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 4. INVASION PERCOLATION
# ═════════════════════════════════════════════════════════════════════════════

def invasion_percolation(L=300, n_steps=None, seed=42):
    """
    Greedy growth from the centre: assign random weights to all sites, then
    grow a single cluster by always invading the boundary site with the
    smallest weight. No tuneable parameter — self-organised criticality.
    """
    if n_steps is None:
        n_steps = L * L // 3

    rng = np.random.default_rng(seed)
    weights = rng.random((L, L))

    invaded = np.zeros((L, L), dtype=bool)
    order = np.full((L, L), -1, dtype=int)

    # start from centre
    ci, cj = L // 2, L // 2
    invaded[ci, cj] = True
    order[ci, cj] = 0

    # priority queue: (weight, i, j)
    heap = []
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = ci + di, cj + dj
        if 0 <= ni < L and 0 <= nj < L:
            heapq.heappush(heap, (weights[ni, nj], ni, nj))

    step = 1
    while heap and step < n_steps:
        w, i, j = heapq.heappop(heap)
        if invaded[i, j]:
            continue
        invaded[i, j] = True
        order[i, j] = step
        step += 1

        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < L and 0 <= nj < L and not invaded[ni, nj]:
                heapq.heappush(heap, (weights[ni, nj], ni, nj))

    return invaded, order, step


def plot_invasion_artistic(L=300, seed=42):
    invaded, order, total = invasion_percolation(L, seed=seed)

    fig, ax = plt.subplots(figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    # colour by invasion order: warm centre → cool edges
    vis = np.where(order >= 0, order / max(total, 1), np.nan)
    cmap = plt.cm.magma.copy()
    cmap.set_bad(DARK_BG)
    ax.imshow(vis, cmap=cmap, interpolation='nearest')
    ax.set_axis_off()
    ax.set_title('Invasion Percolation', color='white', fontsize=14, fontweight='bold', pad=10)
    _save(fig, 'perc_invasion_artistic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 5. DIRECTED PERCOLATION
# ═════════════════════════════════════════════════════════════════════════════

def directed_percolation(L=200, p=0.645, seed=42):
    """
    Each bond pointing down or right is independently open with probability p.
    BFS from the entire top row determines reachable sites.
    The critical threshold for directed bond percolation on the square lattice
    is p_c ≈ 0.6447.
    """
    rng = np.random.default_rng(seed)
    # bonds: down_bonds[i,j] = bond from (i,j) to (i+1,j)
    #        right_bonds[i,j] = bond from (i,j) to (i,j+1)
    down_bonds = rng.random((L - 1, L)) < p
    right_bonds = rng.random((L, L - 1)) < p

    reachable = np.zeros((L, L), dtype=bool)
    depth = np.full((L, L), -1, dtype=int)

    # BFS from top row
    queue = deque()
    for j in range(L):
        reachable[0, j] = True
        depth[0, j] = 0
        queue.append((0, j))

    while queue:
        i, j = queue.popleft()
        # down
        if i + 1 < L and down_bonds[i, j] and not reachable[i + 1, j]:
            reachable[i + 1, j] = True
            depth[i + 1, j] = depth[i, j] + 1
            queue.append((i + 1, j))
        # right
        if j + 1 < L and right_bonds[i, j] and not reachable[i, j + 1]:
            reachable[i, j + 1] = True
            depth[i, j + 1] = depth[i, j] + 1
            queue.append((i, j + 1))

    return reachable, depth


def plot_directed_artistic(L=200, seed=42):
    reachable, depth = directed_percolation(L, seed=seed)

    fig, ax = plt.subplots(figsize=(8, 8), facecolor=DARK_BG)
    ax.set_facecolor(DARK_BG)

    max_d = depth.max() if depth.max() > 0 else 1
    vis = np.where(reachable, depth / max_d, np.nan)
    cmap = LinearSegmentedColormap.from_list('dp', ['#00e5ff', '#006064'], N=256)
    cmap.set_bad(DARK_BG)
    ax.imshow(vis, cmap=cmap, interpolation='nearest')
    ax.set_axis_off()
    ax.set_title('Directed Percolation', color='white', fontsize=14, fontweight='bold', pad=10)
    _save(fig, 'perc_directed_artistic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 6. STANDARD SITE PERCOLATION (for comparison panel)
# ═════════════════════════════════════════════════════════════════════════════

def standard_percolation(L=200, p=0.593, seed=42):
    """Standard site percolation at criticality for the diagnostic comparison."""
    rng = np.random.default_rng(seed)
    grid = rng.random((L, L)) < p
    uf = UnionFind(L * L)
    for i in range(L):
        for j in range(L):
            if not grid[i, j]:
                continue
            idx = i * L + j
            if j + 1 < L and grid[i, j + 1]:
                uf.union(idx, i * L + j + 1)
            if i + 1 < L and grid[i + 1, j]:
                uf.union(idx, (i + 1) * L + j)

    # find spanning cluster
    top_roots = {uf.find(j) for j in range(L) if grid[0, j]}
    bot_roots = {uf.find((L - 1) * L + j) for j in range(L) if grid[L - 1, j]}
    spanning = top_roots & bot_roots

    labels = np.full((L, L), -1, dtype=int)
    for i in range(L):
        for j in range(L):
            if grid[i, j]:
                labels[i, j] = uf.find(i * L + j)

    return grid, labels, spanning, uf


# ═════════════════════════════════════════════════════════════════════════════
# 7. DIAGNOSTIC FIGURE — 2×3 COMPARISON GRID
# ═════════════════════════════════════════════════════════════════════════════

def plot_diagnostic_comparison():
    """2×3 light-background grid comparing standard + 5 variants."""
    L_diag = 150
    seed = 42

    fig = plt.figure(figsize=(15, 10), facecolor='white')
    gs = gridspec.GridSpec(2, 3, wspace=0.15, hspace=0.25)

    titles_and_data = []

    # (a) Standard
    print('  diagnostic: standard percolation ...')
    grid_s, labels_s, spanning_s, uf_s = standard_percolation(L_diag, p=0.593, seed=seed)
    img_s = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            r = labels_s[i, j]
            if r >= 0:
                if r in spanning_s:
                    img_s[i, j] = [0.85, 0.65, 0.13]  # gold
                else:
                    img_s[i, j] = [0.37, 0.51, 0.71]  # steel blue
    titles_and_data.append(('(a) Standard Site', img_s))

    # (b) Gradient
    print('  diagnostic: gradient percolation ...')
    grid_g, labels_g, front_g, _ = gradient_percolation(L_diag, seed)
    img_g = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            v = labels_g[i, j]
            if front_g[i, j]:
                img_g[i, j] = [0.85, 0.65, 0.13]
            elif v >= 0:
                img_g[i, j] = [0.2 + 0.6 * v, 0.3, 0.7 - 0.5 * v]
            elif v == -1:
                img_g[i, j] = [0.75, 0.75, 0.8]
    titles_and_data.append(('(b) Gradient', img_g))

    # (c) Explosive
    print('  diagnostic: explosive percolation ...')
    labels_e, giant_e, uf_e = explosive_percolation(L_diag, seed)
    img_e = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            r = uf_e.find(i * L_diag + j)
            if r == giant_e:
                img_e[i, j] = [0.9, 0.25, 0.05]
            elif uf_e.component_size(i * L_diag + j) > 3:
                img_e[i, j] = [0.37, 0.51, 0.71]
            else:
                img_e[i, j] = [0.82, 0.82, 0.85]
    titles_and_data.append(('(c) Explosive', img_e))

    # (d) Bootstrap k=3
    print('  diagnostic: bootstrap percolation ...')
    orig_b, core_b = bootstrap_percolation(L_diag, p=0.55, k=3, seed=seed)
    img_b = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            if core_b[i, j]:
                img_b[i, j] = [0.18, 0.72, 0.35]
            elif orig_b[i, j]:
                img_b[i, j] = [0.78, 0.78, 0.8]
    titles_and_data.append(('(d) Bootstrap ($k=3$)', img_b))

    # (e) Invasion
    print('  diagnostic: invasion percolation ...')
    inv_mask, inv_order, inv_total = invasion_percolation(L_diag, n_steps=L_diag * L_diag // 3, seed=seed)
    cmap_inv = plt.cm.magma
    img_e2 = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            if inv_order[i, j] >= 0:
                t = inv_order[i, j] / max(inv_total, 1)
                c = cmap_inv(t)
                img_e2[i, j] = c[:3]
    titles_and_data.append(('(e) Invasion', img_e2))

    # (f) Directed
    print('  diagnostic: directed percolation ...')
    reach_d, depth_d = directed_percolation(L_diag, p=0.645, seed=seed)
    max_d = max(depth_d.max(), 1)
    img_d = np.full((L_diag, L_diag, 3), 0.95)
    for i in range(L_diag):
        for j in range(L_diag):
            if reach_d[i, j]:
                t = depth_d[i, j] / max_d
                img_d[i, j] = [0.0, 0.9 * (1 - 0.6 * t), 0.9 * (1 - 0.3 * t)]
    titles_and_data.append(('(f) Directed', img_d))

    for idx, (title, img) in enumerate(titles_and_data):
        ax = fig.add_subplot(gs[idx // 3, idx % 3])
        ax.imshow(img, interpolation='nearest')
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_axis_off()

    _save(fig, 'perc_variants_diagnostic.png')


# ═════════════════════════════════════════════════════════════════════════════
# 8. ANIMATED GIFs
# ═════════════════════════════════════════════════════════════════════════════

def _gif_setup(title_text):
    """Create a dark-background figure for GIF frames."""
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor('#1a1a2e')
    title = ax.set_title(title_text, color='white', alpha=0.75,
                         fontsize=13, fontweight='bold', pad=12)
    return fig, ax, title


def gif_gradient(L=100, n_frames=72, seed=42):
    """Animate gradient percolation: sweep a global scale factor on p(x)."""
    rng = np.random.default_rng(seed)
    rand_field = rng.random((L, L))
    p_x = 1.0 - np.arange(L) / L  # base gradient

    scales = np.linspace(0.3, 1.6, n_frames)
    cmap_span = LinearSegmentedColormap.from_list('span', ['#1565c0', '#e65100'], N=256)

    frames = []
    for scale in scales:
        p_field = np.clip(scale * p_x, 0, 1)
        grid = rand_field < p_field[np.newaxis, :]

        uf = UnionFind(L * L)
        for i in range(L):
            for j in range(L):
                if not grid[i, j]:
                    continue
                idx = i * L + j
                if j + 1 < L and grid[i, j + 1]:
                    uf.union(idx, i * L + j + 1)
                if i + 1 < L and grid[i + 1, j]:
                    uf.union(idx, (i + 1) * L + j)

        top_roots = {uf.find(j) for j in range(L) if grid[0, j]}
        bot_roots = {uf.find((L - 1) * L + j) for j in range(L) if grid[L - 1, j]}
        spanning = top_roots & bot_roots

        img = np.zeros((L, L, 4))
        img[..., 3] = 1.0
        img[~grid, :3] = [0.03, 0.03, 0.06]
        for i in range(L):
            for j in range(L):
                if grid[i, j]:
                    r = uf.find(i * L + j)
                    if r in spanning:
                        # front detection
                        is_front = False
                        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < L and 0 <= nj < L and not grid[ni, nj]:
                                is_front = True
                                break
                        if is_front:
                            img[i, j, :3] = [1.0, 0.84, 0.0]
                        else:
                            c = cmap_span(j / L)
                            img[i, j, :3] = c[:3]
                            img[i, j, 3] = 0.8
                    else:
                        img[i, j, :3] = [0.2, 0.25, 0.4]

        frames.append((scale, img))

    fig, ax, title = _gif_setup('G R A D I E N T   P E R C O L A T I O N\nscale = 0.30')
    im = ax.imshow(frames[0][1], interpolation='nearest')

    gif_path = os.path.join(SCRIPT_DIR, 'perc_gradient.gif')
    writer = PillowWriter(fps=12)
    with writer.saving(fig, gif_path, dpi=100):
        for scale, img in frames:
            im.set_data(img)
            title.set_text(f'G R A D I E N T   P E R C O L A T I O N\nscale = {scale:.2f}')
            writer.grab_frame()
    plt.close(fig)
    print('  saved perc_gradient.gif')


def gif_explosive(L=100, n_frames=80, seed=42):
    """Animate explosive percolation: bonds added via product rule."""
    N = L * L
    rng = np.random.default_rng(seed)
    uf = UnionFind(N)

    bonds = []
    for i in range(L):
        for j in range(L):
            idx = i * L + j
            if j + 1 < L:
                bonds.append((idx, i * L + j + 1))
            if i + 1 < L:
                bonds.append((idx, (i + 1) * L + j))
    rng.shuffle(bonds)

    total_bonds = len(bonds)
    frame_interval = max(1, (total_bonds // 2) // n_frames)

    # pre-compute all frames
    frames = []
    b = 0
    added = 0
    max_size = 0
    while b + 1 < total_bonds:
        b1, b2 = bonds[b], bonds[b + 1]
        b += 2

        if uf.find(b1[0]) != uf.find(b1[1]):
            prod1 = uf.component_size(b1[0]) * uf.component_size(b1[1])
        else:
            prod1 = float('inf')
        if uf.find(b2[0]) != uf.find(b2[1]):
            prod2 = uf.component_size(b2[0]) * uf.component_size(b2[1])
        else:
            prod2 = float('inf')

        chosen = b1 if prod1 <= prod2 else b2
        if uf.find(chosen[0]) != uf.find(chosen[1]):
            uf.union(chosen[0], chosen[1])
            added += 1

        if added % frame_interval == 0 or added == total_bonds // 2:
            # find largest component
            max_size = 0
            max_root = 0
            roots_seen = set()
            for idx in range(N):
                r = uf.find(idx)
                if r not in roots_seen:
                    roots_seen.add(r)
                    s = uf.component_size(idx)
                    if s > max_size:
                        max_size = s
                        max_root = r

            img = np.zeros((L, L, 4))
            img[..., 3] = 1.0
            img[..., :3] = [0.03, 0.03, 0.06]
            for i in range(L):
                for j in range(L):
                    r = uf.find(i * L + j)
                    sz = uf.component_size(i * L + j)
                    if r == max_root:
                        img[i, j, :3] = [0.95, 0.25, 0.05]
                    elif sz > 5:
                        hue = (r * 0.618) % 1.0
                        img[i, j, :3] = [0.15 + 0.25 * hue, 0.25 + 0.2 * (1 - hue), 0.5 + 0.2 * hue]
                    else:
                        img[i, j, :3] = [0.08, 0.08, 0.12]

            frac = max_size / N
            frames.append((added / total_bonds, frac, img))

        if max_size > 0.5 * N:
            break

    fig, ax, title = _gif_setup('E X P L O S I V E   P E R C O L A T I O N\nbonds = 0.00')
    im = ax.imshow(frames[0][2], interpolation='nearest')

    gif_path = os.path.join(SCRIPT_DIR, 'perc_explosive.gif')
    writer = PillowWriter(fps=12)
    with writer.saving(fig, gif_path, dpi=100):
        for bfrac, cfrac, img in frames:
            im.set_data(img)
            title.set_text(f'E X P L O S I V E   P E R C O L A T I O N\n'
                           f'bonds = {bfrac:.2f}   giant = {cfrac:.1%}')
            writer.grab_frame()
    plt.close(fig)
    print('  saved perc_explosive.gif')


def gif_bootstrap(L=100, p=0.55, k=3, n_frames=60, seed=42):
    """Animate bootstrap pruning: show each round of the cascade."""
    rng = np.random.default_rng(seed)
    grid = rng.random((L, L)) < p
    original = grid.copy()

    frames = []

    # frame 0: initial state
    def _snap(grid, original):
        img = np.zeros((L, L, 4))
        img[..., 3] = 1.0
        img[..., :3] = [0.03, 0.03, 0.06]
        for i in range(L):
            for j in range(L):
                if grid[i, j]:
                    img[i, j, :3] = [0.18, 0.75, 0.35]
                elif original[i, j]:
                    img[i, j, :3] = [0.5, 0.5, 0.5]
        return img

    frames.append(('initial', _snap(grid, original)))

    # iterative pruning rounds
    round_num = 0
    while True:
        to_remove = []
        for i in range(L):
            for j in range(L):
                if not grid[i, j]:
                    continue
                nbrs = 0
                for di, dj in MOORE_NBRS:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < L and 0 <= nj < L and grid[ni, nj]:
                        nbrs += 1
                if nbrs < k:
                    to_remove.append((i, j))
        if not to_remove:
            break
        round_num += 1
        for i, j in to_remove:
            grid[i, j] = False
        frames.append((f'round {round_num} (−{len(to_remove)})', _snap(grid, original)))

    # pad: repeat last frame a few times for visual pause
    for _ in range(10):
        frames.append((f'stable (round {round_num})', frames[-1][1]))

    # if too many frames, subsample
    if len(frames) > n_frames:
        indices = np.linspace(0, len(frames) - 1, n_frames, dtype=int)
        frames = [frames[i] for i in indices]

    fig, ax, title = _gif_setup(f'B O O T S T R A P   P E R C O L A T I O N  (k={k})\ninitial')
    im = ax.imshow(frames[0][1], interpolation='nearest')

    gif_path = os.path.join(SCRIPT_DIR, 'perc_bootstrap.gif')
    writer = PillowWriter(fps=8)
    with writer.saving(fig, gif_path, dpi=100):
        for label, img in frames:
            im.set_data(img)
            title.set_text(f'B O O T S T R A P   P E R C O L A T I O N  ($k={k}$)\n{label}')
            writer.grab_frame()
    plt.close(fig)
    print('  saved perc_bootstrap.gif')


def gif_invasion(L=150, n_frames=80, seed=42):
    """Animate invasion percolation: cluster grows step by step."""
    n_steps = L * L // 3
    rng = np.random.default_rng(seed)
    weights = rng.random((L, L))

    invaded = np.zeros((L, L), dtype=bool)
    order = np.full((L, L), -1, dtype=int)

    ci, cj = L // 2, L // 2
    invaded[ci, cj] = True
    order[ci, cj] = 0

    heap = []
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = ci + di, cj + dj
        if 0 <= ni < L and 0 <= nj < L:
            heapq.heappush(heap, (weights[ni, nj], ni, nj))

    frame_interval = max(1, n_steps // n_frames)
    cmap = plt.cm.magma

    frames = []
    step = 1
    while heap and step < n_steps:
        w, i, j = heapq.heappop(heap)
        if invaded[i, j]:
            continue
        invaded[i, j] = True
        order[i, j] = step
        step += 1

        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < L and 0 <= nj < L and not invaded[ni, nj]:
                heapq.heappush(heap, (weights[ni, nj], ni, nj))

        if step % frame_interval == 0 or step >= n_steps - 1:
            img = np.zeros((L, L, 4))
            img[..., 3] = 1.0
            img[..., :3] = [0.03, 0.03, 0.06]
            vis = order.copy().astype(float)
            mask = order >= 0
            if mask.any():
                vis[mask] = vis[mask] / step
                for ii in range(L):
                    for jj in range(L):
                        if mask[ii, jj]:
                            c = cmap(vis[ii, jj])
                            img[ii, jj, :3] = c[:3]
            frames.append((step, img))

    fig, ax, title = _gif_setup('I N V A S I O N   P E R C O L A T I O N\nsites = 0')
    im = ax.imshow(frames[0][1], interpolation='nearest')

    gif_path = os.path.join(SCRIPT_DIR, 'perc_invasion.gif')
    writer = PillowWriter(fps=12)
    with writer.saving(fig, gif_path, dpi=100):
        for s, img in frames:
            im.set_data(img)
            title.set_text(f'I N V A S I O N   P E R C O L A T I O N\n'
                           f'sites invaded = {s}')
            writer.grab_frame()
    plt.close(fig)
    print('  saved perc_invasion.gif')


def gif_directed(L=100, n_frames=72, seed=42):
    """Animate directed percolation: BFS wavefront row by row."""
    rng = np.random.default_rng(seed)
    p = 0.645
    down_bonds = rng.random((L - 1, L)) < p
    right_bonds = rng.random((L, L - 1)) < p

    reachable = np.zeros((L, L), dtype=bool)
    depth = np.full((L, L), -1, dtype=int)

    queue = deque()
    for j in range(L):
        reachable[0, j] = True
        depth[0, j] = 0
        queue.append((0, j))

    # BFS recording steps
    steps = []
    while queue:
        i, j = queue.popleft()
        steps.append((i, j))
        if i + 1 < L and down_bonds[i, j] and not reachable[i + 1, j]:
            reachable[i + 1, j] = True
            depth[i + 1, j] = depth[i, j] + 1
            queue.append((i + 1, j))
        if j + 1 < L and right_bonds[i, j] and not reachable[i, j + 1]:
            reachable[i, j + 1] = True
            depth[i, j + 1] = depth[i, j] + 1
            queue.append((i, j + 1))

    # build frames at intervals
    total = len(steps)
    frame_interval = max(1, total // n_frames)
    cmap_dp = LinearSegmentedColormap.from_list('dp', ['#00e5ff', '#006064'], N=256)

    frames = []
    shown = np.zeros((L, L), dtype=bool)
    max_depth = max(depth.max(), 1)

    for idx, (si, sj) in enumerate(steps):
        shown[si, sj] = True
        if (idx + 1) % frame_interval == 0 or idx == total - 1:
            img = np.zeros((L, L, 4))
            img[..., 3] = 1.0
            img[..., :3] = [0.03, 0.03, 0.06]
            for ii in range(L):
                for jj in range(L):
                    if shown[ii, jj]:
                        t = depth[ii, jj] / max_depth
                        c = cmap_dp(t)
                        img[ii, jj, :3] = c[:3]
                        # highlight wavefront (just added)
            # highlight the most recently added row band
            frames.append((idx + 1, img))

    fig, ax, title = _gif_setup('D I R E C T E D   P E R C O L A T I O N\nsites = 0')
    im = ax.imshow(frames[0][1], interpolation='nearest')

    gif_path = os.path.join(SCRIPT_DIR, 'perc_directed.gif')
    writer = PillowWriter(fps=12)
    with writer.saving(fig, gif_path, dpi=100):
        for s, img in frames:
            im.set_data(img)
            title.set_text(f'D I R E C T E D   P E R C O L A T I O N\n'
                           f'sites reached = {s}')
            writer.grab_frame()
    plt.close(fig)
    print('  saved perc_directed.gif')


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('Generating percolation variant figures ...')

    print('\n1. Gradient percolation')
    plot_gradient_artistic()

    print('\n2. Explosive percolation')
    plot_explosive_artistic()

    print('\n3. Bootstrap percolation')
    plot_bootstrap_artistic()

    print('\n4. Invasion percolation')
    plot_invasion_artistic()

    print('\n5. Directed percolation')
    plot_directed_artistic()

    print('\n6. Diagnostic comparison grid')
    plot_diagnostic_comparison()

    print('\n--- Animated GIFs ---')

    print('\n7. Gradient percolation GIF')
    gif_gradient()

    print('\n8. Explosive percolation GIF')
    gif_explosive()

    print('\n9. Bootstrap percolation GIF')
    gif_bootstrap()

    print('\n10. Invasion percolation GIF')
    gif_invasion()

    print('\n11. Directed percolation GIF')
    gif_directed()

    print('\nDone — all variant figures and GIFs generated.')
