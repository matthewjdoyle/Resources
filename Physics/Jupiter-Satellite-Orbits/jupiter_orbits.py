# -*- coding: utf-8 -*-
"""
Jupiter's Galilean Moons — N-body orbit simulation
===================================================

Simulates the orbits of Io, Europa, Ganymede, and Callisto around Jupiter
using a symplectic leapfrog (Störmer-Verlet) integrator that preserves energy
over long integration times.

Outputs
-------
jupiter_diagnostic.png  — 2×3 diagnostic panel
jupiter_artistic.png    — dark-background 3D artistic rendering
jupiter_orbits.gif      — animated rotating 3D view

Usage
-----
    python jupiter_orbits.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

# ─── Constants & physical data ────────────────────────────────────────────────

G = 6.67430e-11  # gravitational constant (m³ kg⁻¹ s⁻²)

BODIES = {
    "Jupiter":  {"mass": 1.89819e27, "color": "#ffcc00", "radius_km": 69_911},
    "Io":       {"mass": 8.9319e22,  "a": 4.2180e8, "v": 17334.0, "color": "#ff6b35", "radius_km": 1_821.6},
    "Europa":   {"mass": 4.7998e22,  "a": 6.7110e8, "v": 13740.0, "color": "#4fc3f7", "radius_km": 1_560.8},
    "Ganymede": {"mass": 1.4819e23,  "a": 1.0704e9, "v": 10880.0, "color": "#ab47bc", "radius_km": 2_634.1},
    "Callisto": {"mass": 1.0759e23,  "a": 1.8827e9, "v": 8204.0,  "color": "#78909c", "radius_km": 2_410.3},
}

MOON_NAMES = ["Io", "Europa", "Ganymede", "Callisto"]
ALL_NAMES = ["Jupiter"] + MOON_NAMES

# Known orbital periods (days) for reference
KNOWN_PERIODS = {"Io": 1.769, "Europa": 3.551, "Ganymede": 7.155, "Callisto": 16.689}

OUTPUT_DIR = Path(__file__).parent


def marker_sizes(jupiter_ms=16):
    """Compute marker sizes proportional to sqrt(radius), with Jupiter as reference."""
    r_jup = BODIES["Jupiter"]["radius_km"]
    sizes = {}
    for name in ALL_NAMES:
        r = BODIES[name]["radius_km"]
        sizes[name] = jupiter_ms * np.sqrt(r / r_jup)
    return sizes


# ─── Section 1: Physics engine ────────────────────────────────────────────────

def compute_accelerations(pos, masses):
    """Vectorised pairwise gravitational acceleration (no Python loops)."""
    n = len(masses)
    # pos shape: (n, 3)
    # Displacement vectors: r_ij = pos[j] - pos[i]
    diff = pos[np.newaxis, :, :] - pos[:, np.newaxis, :]  # (n, n, 3)
    dist_sq = np.sum(diff ** 2, axis=2)                     # (n, n)
    np.fill_diagonal(dist_sq, 1.0)  # avoid division by zero
    inv_dist3 = dist_sq ** (-1.5)
    np.fill_diagonal(inv_dist3, 0.0)

    # acc[i] = sum_j G * m_j * (pos[j] - pos[i]) / |r_ij|^3
    acc = G * np.einsum("ij,ijk,j->ik", inv_dist3, diff, masses)
    return acc


def leapfrog_step(pos, vel, masses, dt):
    """Störmer-Verlet symplectic integrator — conserves energy over long times."""
    acc = compute_accelerations(pos, masses)
    vel_half = vel + 0.5 * dt * acc
    pos_new = pos + dt * vel_half
    acc_new = compute_accelerations(pos_new, masses)
    vel_new = vel_half + 0.5 * dt * acc_new
    return pos_new, vel_new


def total_energy(pos, vel, masses):
    """Total mechanical energy: kinetic + gravitational potential."""
    n = len(masses)
    KE = 0.5 * np.sum(masses[:, None] * vel ** 2)

    PE = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r = np.linalg.norm(pos[j] - pos[i])
            PE -= G * masses[i] * masses[j] / r
    return KE + PE


# ─── Section 2: Orbital element extraction ────────────────────────────────────

def orbital_elements(r_vec, v_vec, mu):
    """
    Compute Keplerian elements from state vector.

    Parameters
    ----------
    r_vec : (3,) position relative to central body
    v_vec : (3,) velocity relative to central body
    mu    : G * (M_central + m_body)

    Returns
    -------
    a : semi-major axis (m)
    e : eccentricity
    inc : inclination (rad)
    T : orbital period (s)
    """
    r = np.linalg.norm(r_vec)
    v = np.linalg.norm(v_vec)

    # Specific angular momentum
    h_vec = np.cross(r_vec, v_vec)
    h = np.linalg.norm(h_vec)

    # Semi-major axis (vis-viva)
    a = 1.0 / (2.0 / r - v ** 2 / mu)

    # Eccentricity vector
    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r
    e = np.linalg.norm(e_vec)

    # Inclination
    inc = np.arccos(np.clip(h_vec[2] / h, -1, 1))

    # Period
    T = 2.0 * np.pi * np.sqrt(np.abs(a) ** 3 / mu)

    return a, e, inc, T


# ─── Section 3: Main simulation ──────────────────────────────────────────────

def build_initial_state():
    """Construct initial position and velocity arrays."""
    n = len(ALL_NAMES)
    pos = np.zeros((n, 3))
    vel = np.zeros((n, 3))

    for i, name in enumerate(MOON_NAMES):
        body = BODIES[name]
        pos[i + 1] = [body["a"], 0.0, 0.0]
        vel[i + 1] = [0.0, body["v"], 0.0]

    return pos, vel


def run_simulation(days=200, dt=60.0, save_every=100):
    """
    Integrate the system for the given duration.

    Parameters
    ----------
    days : simulation duration
    dt   : time step in seconds (60 s = 1 minute)
    save_every : save state every N steps

    Returns
    -------
    t_arr   : (K,) time array in seconds
    pos_arr : (K, n_bodies, 3) positions
    vel_arr : (K, n_bodies, 3) velocities
    """
    masses = np.array([BODIES[name]["mass"] for name in ALL_NAMES])
    pos, vel = build_initial_state()

    total_steps = int(days * 86400 / dt)
    n_saves = total_steps // save_every + 1

    t_arr = np.zeros(n_saves)
    pos_arr = np.zeros((n_saves, len(ALL_NAMES), 3))
    vel_arr = np.zeros((n_saves, len(ALL_NAMES), 3))

    pos_arr[0] = pos.copy()
    vel_arr[0] = vel.copy()
    save_idx = 1

    print(f"Integrating {days} days ({total_steps:,} steps, dt = {dt:.0f}s)...")

    for step in range(1, total_steps + 1):
        pos, vel = leapfrog_step(pos, vel, masses, dt)

        if step % save_every == 0:
            t_arr[save_idx] = step * dt
            pos_arr[save_idx] = pos.copy()
            vel_arr[save_idx] = vel.copy()
            save_idx += 1

            # Progress
            day = step * dt / 86400
            if int(day) % 20 == 0 and step % (save_every * 10) == 0:
                print(f"  Day {int(day):>4d}/{days}", end="\r", flush=True)

    print(f"  Done — {save_idx} snapshots saved.        ")
    return t_arr[:save_idx], pos_arr[:save_idx], vel_arr[:save_idx]


# ─── Section 4: Diagnostic figure ────────────────────────────────────────────

def compute_relative(pos_arr):
    """Positions relative to Jupiter (index 0)."""
    return pos_arr[:, 1:, :] - pos_arr[:, 0:1, :]


def compute_distances(rel_pos):
    """Radial distance of each moon from Jupiter over time."""
    return np.linalg.norm(rel_pos, axis=2)  # (K, 4)


def compute_energy_history(t_arr, pos_arr, vel_arr):
    """Compute total energy at each saved snapshot."""
    masses = np.array([BODIES[name]["mass"] for name in ALL_NAMES])
    energies = np.zeros(len(t_arr))
    for k in range(len(t_arr)):
        energies[k] = total_energy(pos_arr[k], vel_arr[k], masses)
    return energies


def compute_orbital_elements_history(t_arr, pos_arr, vel_arr):
    """Compute orbital elements for each moon at each snapshot."""
    masses = np.array([BODIES[name]["mass"] for name in ALL_NAMES])
    n_moons = len(MOON_NAMES)
    K = len(t_arr)

    a_hist = np.zeros((K, n_moons))
    e_hist = np.zeros((K, n_moons))
    inc_hist = np.zeros((K, n_moons))
    T_hist = np.zeros((K, n_moons))

    for k in range(K):
        jup_pos = pos_arr[k, 0]
        jup_vel = vel_arr[k, 0]
        for m in range(n_moons):
            r_rel = pos_arr[k, m + 1] - jup_pos
            v_rel = vel_arr[k, m + 1] - jup_vel
            mu = G * (masses[0] + masses[m + 1])
            a, e, inc, T = orbital_elements(r_rel, v_rel, mu)
            a_hist[k, m] = a
            e_hist[k, m] = e
            inc_hist[k, m] = inc
            T_hist[k, m] = T

    return a_hist, e_hist, inc_hist, T_hist


def make_diagnostic_figure(t_arr, pos_arr, vel_arr):
    """Create 2×3 diagnostic panel and save to jupiter_diagnostic.png."""
    print("Generating diagnostic figure...")

    t_days = t_arr / 86400.0
    rel_pos = compute_relative(pos_arr)
    distances = compute_distances(rel_pos)
    energies = compute_energy_history(t_arr, pos_arr, vel_arr)
    a_hist, e_hist, inc_hist, T_hist = compute_orbital_elements_history(
        t_arr, pos_arr, vel_arr
    )

    moon_colors = [BODIES[n]["color"] for n in MOON_NAMES]

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(
        "Jupiter–Galilean Moon System: Diagnostic Panel",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    fig.subplots_adjust(hspace=0.35, wspace=0.3, top=0.92, bottom=0.08)

    # (a) Top-down orbital paths (x-y plane)
    ax = axes[0, 0]
    ms = marker_sizes(jupiter_ms=14)
    for m, name in enumerate(MOON_NAMES):
        ax.plot(
            rel_pos[:, m, 0] / 1e9,
            rel_pos[:, m, 1] / 1e9,
            color=moon_colors[m],
            alpha=0.7,
            linewidth=0.5,
            label=name,
        )
        # Moon position at final snapshot
        ax.plot(
            rel_pos[-1, m, 0] / 1e9,
            rel_pos[-1, m, 1] / 1e9,
            "o", color=moon_colors[m],
            markersize=ms[name], zorder=11,
        )
    ax.plot(0, 0, "o", color="#ffcc00", markersize=ms["Jupiter"], zorder=10)
    ax.set_xlabel("x (10⁶ km)")
    ax.set_ylabel("y (10⁶ km)")
    ax.set_title("(a) Orbital Paths (x–y plane)")
    ax.set_aspect("equal")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (b) Orbital distance vs time
    ax = axes[0, 1]
    for m, name in enumerate(MOON_NAMES):
        ax.plot(t_days, distances[:, m] / 1e9, color=moon_colors[m], linewidth=0.6, label=name)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Distance from Jupiter (10⁶ km)")
    ax.set_title("(b) Orbital Distance vs Time")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (c) Energy conservation: ΔE/E₀ vs time
    ax = axes[1, 0]
    E0 = energies[0]
    dE_rel = (energies - E0) / np.abs(E0)
    ax.plot(t_days, dE_rel, color="#e53935", linewidth=0.8)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("ΔE / |E₀|")
    ax.set_title("(c) Energy Conservation")
    ax.ticklabel_format(axis="y", style="scientific", scilimits=(-3, 3))
    ax.grid(True, alpha=0.3)

    # (d) Kepler's law: T²/a³ ratios
    ax = axes[1, 1]
    # Use median values over simulation
    a_med = np.median(a_hist, axis=0)
    T_med = np.median(T_hist, axis=0)
    kepler_ratio = T_med ** 2 / a_med ** 3
    kepler_expected = 4 * np.pi ** 2 / (G * BODIES["Jupiter"]["mass"])

    bars = ax.bar(MOON_NAMES, kepler_ratio / kepler_expected, color=moon_colors, edgecolor="black", linewidth=0.5)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8, label="Kepler prediction")
    ax.set_ylabel("T²/a³ (normalised)")
    ax.set_title("(d) Kepler's Third Law Verification")
    ax.set_ylim(0.98, 1.02)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # (e) Laplace resonance: conjunction angles
    ax = axes[0, 2]
    # Compute mean longitudes
    theta_io = np.arctan2(rel_pos[:, 0, 1], rel_pos[:, 0, 0])
    theta_eu = np.arctan2(rel_pos[:, 1, 1], rel_pos[:, 1, 0])
    theta_ga = np.arctan2(rel_pos[:, 2, 1], rel_pos[:, 2, 0])

    # Laplace angle: λ_Io - 3λ_Europa + 2λ_Ganymede ≈ 180°
    laplace_angle = np.unwrap(theta_io) - 3 * np.unwrap(theta_eu) + 2 * np.unwrap(theta_ga)
    laplace_deg = np.degrees(laplace_angle) % 360

    ax.scatter(t_days, laplace_deg, s=0.3, color="#66bb6a", alpha=0.5)
    ax.axhline(180, color="white" if False else "gray", linestyle="--", linewidth=0.8, label="180° (exact resonance)")
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Laplace angle (°)")
    ax.set_title("(e) Laplace Resonance")
    ax.set_ylim(0, 360)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Period ratios annotation
    T_io = np.median(T_hist[:, 0]) / 86400
    T_eu = np.median(T_hist[:, 1]) / 86400
    T_ga = np.median(T_hist[:, 2]) / 86400
    T_ca = np.median(T_hist[:, 3]) / 86400
    ratio_text = (
        f"Period ratios:\n"
        f"Europa/Io = {T_eu / T_io:.3f} (≈2)\n"
        f"Ganymede/Io = {T_ga / T_io:.3f} (≈4)\n"
        f"Callisto/Io = {T_ca / T_io:.3f} (≈9.4)"
    )
    ax.text(
        0.98, 0.02, ratio_text, transform=ax.transAxes,
        fontsize=7, verticalalignment="bottom", horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

    # (f) Eccentricity evolution
    ax = axes[1, 2]
    for m, name in enumerate(MOON_NAMES):
        ax.plot(t_days, e_hist[:, m], color=moon_colors[m], linewidth=0.6, label=name)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Eccentricity")
    ax.set_title("(f) Eccentricity Evolution")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    out = OUTPUT_DIR / "jupiter_diagnostic.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {out}")


# ─── Section 5: Artistic 3D figure ───────────────────────────────────────────

def make_artistic_figure(pos_arr):
    """Create polished dark-background 3D orbital rendering."""
    print("Generating artistic figure...")

    rel_pos = compute_relative(pos_arr)
    bg_color = "#0e1117"

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Dark styling
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.xaxis.set_pane_color((0, 0, 0, 0))
    ax.yaxis.set_pane_color((0, 0, 0, 0))
    ax.zaxis.set_pane_color((0, 0, 0, 0))
    ax.grid(False)
    ax.set_axis_off()

    # Marker sizes proportional to sqrt(radius)
    ms = marker_sizes(jupiter_ms=18)

    # Jupiter: simple dot, no glow
    ax.plot([0], [0], [0], "o", color="#ffcc00", markersize=ms["Jupiter"], zorder=20)

    # Colormaps for each moon
    cmaps = {
        "Io": LinearSegmentedColormap.from_list("io", ["#1a0a00", "#ff6b35", "#ffcc00"]),
        "Europa": LinearSegmentedColormap.from_list("eu", ["#0a1a2e", "#4fc3f7", "#e1f5fe"]),
        "Ganymede": LinearSegmentedColormap.from_list("ga", ["#1a0a2e", "#ab47bc", "#e1bee7"]),
        "Callisto": LinearSegmentedColormap.from_list("ca", ["#0a1a1a", "#78909c", "#cfd8dc"]),
    }

    n_pts = len(rel_pos)
    for m, name in enumerate(MOON_NAMES):
        x = rel_pos[:, m, 0] / 1e9
        y = rel_pos[:, m, 1] / 1e9
        z = rel_pos[:, m, 2] / 1e9

        # Gradient trail: colour by time (fading in)
        c_norm = np.linspace(0, 1, n_pts)
        sc = ax.scatter(
            x, y, z,
            c=c_norm,
            cmap=cmaps[name],
            s=0.3,
            alpha=0.7,
            depthshade=True,
        )

        # Current position marker (relative size)
        ax.plot(
            [x[-1]], [y[-1]], [z[-1]],
            "o",
            color=BODIES[name]["color"],
            markersize=ms[name],
            zorder=15,
            markeredgecolor="white",
            markeredgewidth=0.5,
        )
        ax.text(
            x[-1], y[-1], z[-1] + 0.06e0,
            f"  {name}",
            color="white",
            fontsize=8,
            alpha=0.9,
            zorder=16,
        )

    # Axis limits
    limit = 2.2
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.view_init(elev=25, azim=-60)

    # Title
    fig.text(
        0.5, 0.93,
        "Jupiter's Galilean Moons",
        ha="center", va="center",
        color="white", fontsize=18, alpha=0.85,
        fontweight="light",
    )

    # Legend with orbital periods
    legend_text = "  ".join(
        f"{n}: {KNOWN_PERIODS[n]:.2f}d" for n in MOON_NAMES
    )
    fig.text(
        0.5, 0.06,
        legend_text,
        ha="center", va="center",
        color="white", fontsize=9, alpha=0.6,
        family="monospace",
    )

    out = OUTPUT_DIR / "jupiter_artistic.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=bg_color)
    plt.close(fig)
    print(f"  Saved: {out}")


# ─── Section 6: Animated GIF ─────────────────────────────────────────────────

def make_animation(pos_arr, n_frames=120):
    """Create rotating 3D animation and save as GIF."""
    print(f"Generating animation ({n_frames} frames)...")

    rel_pos = compute_relative(pos_arr)
    bg_color = "#0e1117"

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.xaxis.set_pane_color((0, 0, 0, 0))
    ax.yaxis.set_pane_color((0, 0, 0, 0))
    ax.zaxis.set_pane_color((0, 0, 0, 0))
    ax.grid(False)
    ax.set_axis_off()

    limit = 2.2
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)

    moon_colors = [BODIES[n]["color"] for n in MOON_NAMES]
    ms = marker_sizes(jupiter_ms=14)
    n_snapshots = len(rel_pos)

    def update(frame):
        ax.cla()
        ax.set_facecolor(bg_color)
        ax.xaxis.set_pane_color((0, 0, 0, 0))
        ax.yaxis.set_pane_color((0, 0, 0, 0))
        ax.zaxis.set_pane_color((0, 0, 0, 0))
        ax.grid(False)
        ax.set_axis_off()
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_zlim(-limit, limit)

        # Azimuth rotation
        azim = -60 + (360 * frame / n_frames)
        ax.view_init(elev=25, azim=azim)

        # Jupiter: simple dot, no glow
        ax.plot([0], [0], [0], "o", color="#ffcc00", markersize=ms["Jupiter"], zorder=20)

        # Current time index
        t_idx = min(int(frame * n_snapshots / n_frames), n_snapshots - 1)

        for m, name in enumerate(MOON_NAMES):
            x = rel_pos[:, m, 0] / 1e9
            y = rel_pos[:, m, 1] / 1e9
            z = rel_pos[:, m, 2] / 1e9

            # Full orbit trail (faded)
            ax.plot(x, y, z, color=moon_colors[m], alpha=0.2, linewidth=0.5)

            # Current position (relative size)
            ax.plot(
                [x[t_idx]], [y[t_idx]], [z[t_idx]],
                "o",
                color=moon_colors[m],
                markersize=ms[name],
                zorder=15,
                markeredgecolor="white",
                markeredgewidth=0.3,
            )

        # Title
        day = t_idx * 200.0 / n_snapshots
        ax.set_title(
            f"Day {day:.0f}",
            color="white", fontsize=11, alpha=0.7, pad=-5,
        )

        return []

    anim = FuncAnimation(fig, update, frames=n_frames, blit=False)
    out = OUTPUT_DIR / "jupiter_orbits.gif"
    anim.save(str(out), writer=PillowWriter(fps=20), dpi=100, savefig_kwargs={"facecolor": bg_color})
    plt.close(fig)
    print(f"  Saved: {out}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def print_summary(t_arr, pos_arr, vel_arr):
    """Print simulation summary to console."""
    energies = compute_energy_history(t_arr, pos_arr, vel_arr)
    _, _, _, T_hist = compute_orbital_elements_history(t_arr, pos_arr, vel_arr)

    E0 = energies[0]
    dE_max = np.max(np.abs((energies - E0) / np.abs(E0)))

    print("\n-- Simulation Summary --------------------------")
    print(f"  Duration:       {t_arr[-1] / 86400:.0f} days")
    print(f"  Snapshots:      {len(t_arr):,}")
    print(f"  Max |dE/E0|:    {dE_max:.2e}")

    print(f"\n  {'Moon':<12} {'T_sim (d)':>10} {'T_known (d)':>12} {'Error':>8}")
    print(f"  {'-'*44}")
    for m, name in enumerate(MOON_NAMES):
        T_sim = np.median(T_hist[:, m]) / 86400
        T_known = KNOWN_PERIODS[name]
        err = abs(T_sim - T_known) / T_known * 100
        print(f"  {name:<12} {T_sim:>10.4f} {T_known:>12.3f} {err:>7.2f}%")

    T_io = np.median(T_hist[:, 0]) / 86400
    T_eu = np.median(T_hist[:, 1]) / 86400
    T_ga = np.median(T_hist[:, 2]) / 86400
    print(f"\n  Laplace resonance ratios:")
    print(f"    Europa/Io    = {T_eu / T_io:.4f}  (exact: 2.0)")
    print(f"    Ganymede/Io  = {T_ga / T_io:.4f}  (exact: 4.0)")
    print(f"{'-' * 50}\n")


if __name__ == "__main__":
    # Run simulation
    t_arr, pos_arr, vel_arr = run_simulation(days=200, dt=60.0, save_every=100)

    # Print summary
    print_summary(t_arr, pos_arr, vel_arr)

    # Generate all outputs
    make_diagnostic_figure(t_arr, pos_arr, vel_arr)
    make_artistic_figure(pos_arr)
    make_animation(pos_arr, n_frames=120)

    print("All outputs generated.")
