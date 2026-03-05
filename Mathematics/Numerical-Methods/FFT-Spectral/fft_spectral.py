# -*- coding: utf-8 -*-
"""
    FFT & Spectral Methods
    ========================
    From the Discrete Fourier Transform through the Cooley-Tukey FFT
    algorithm to spectral differentiation and Chebyshev polynomials,
    with 2-D transforms, power-spectral-density estimation, and an
    artistic Fourier-reconstruction visualisation.

    Topics covered:
        1. DFT — naïve O(N²) implementation & validation
        2. Cooley-Tukey FFT — recursive O(N log N) + timing benchmark
        3. 2-D DFT — spatial-frequency analysis of a test pattern
        4. Power Spectral Density — periodogram & Welch's method
        5. Spectral Differentiation — Fourier vs finite differences
        6. Chebyshev Polynomials — spectral convergence & Gibbs
        7. Artistic figure — signal reconstruction from partial
           Fourier coefficients

    Run:  python fft_spectral.py
    Deps: numpy, matplotlib, scipy
"""

import warnings
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
import time

warnings.filterwarnings('ignore', category=np.RankWarning)


# ─────────────────────────────────────────────────────────────────────────────
# --- 1. THE DISCRETE FOURIER TRANSFORM  (naïve O(N²)) ---
# ─────────────────────────────────────────────────────────────────────────────

def dft_naive(x):
    """Compute the DFT of x via the direct O(N²) matrix–vector product."""
    N = len(x)
    n = np.arange(N)
    k = n.reshape(-1, 1)
    W = np.exp(-2j * np.pi * k * n / N)
    return W @ x


def idft_naive(X):
    """Inverse DFT via conjugate trick: x = conj(DFT(conj(X))) / N."""
    N = len(X)
    return np.conj(dft_naive(np.conj(X))) / N


# ─────────────────────────────────────────────────────────────────────────────
# --- 2. COOLEY-TUKEY FFT  (recursive radix-2, O(N log N)) ---
# ─────────────────────────────────────────────────────────────────────────────

def fft_radix2(x):
    """
    Recursive radix-2 decimation-in-time FFT.
    Input length must be a power of 2.
    """
    N = len(x)
    if N <= 1:
        return x.copy().astype(complex)
    if N % 2 != 0:
        raise ValueError("Length must be a power of 2")
    even = fft_radix2(x[::2])
    odd  = fft_radix2(x[1::2])
    twiddle = np.exp(-2j * np.pi * np.arange(N // 2) / N)
    return np.concatenate([even + twiddle * odd,
                           even - twiddle * odd])


# --- Validation ---
np.random.seed(42)
x_test = np.random.randn(256)
assert np.allclose(fft_radix2(x_test), np.fft.fft(x_test)), \
    "Radix-2 FFT does not match np.fft.fft!"
print("✓ Radix-2 FFT matches np.fft.fft to machine precision")


# --- Timing benchmark ---
sizes_timing  = [2**p for p in range(4, 13)]     # 16 … 4096
time_naive    = []
time_radix2   = []
time_numpy    = []

for N in sizes_timing:
    sig = np.random.randn(N)

    # Naïve DFT (skip for N > 4096 — too slow)
    if N <= 4096:
        t0 = time.perf_counter()
        for _ in range(max(1, 5000 // N)):
            dft_naive(sig)
        reps = max(1, 5000 // N)
        time_naive.append((time.perf_counter() - t0) / reps)
    else:
        time_naive.append(np.nan)

    # Recursive FFT
    t0 = time.perf_counter()
    for _ in range(max(1, 5000 // N)):
        fft_radix2(sig)
    reps = max(1, 5000 // N)
    time_radix2.append((time.perf_counter() - t0) / reps)

    # NumPy FFT
    t0 = time.perf_counter()
    for _ in range(max(1, 50000 // N)):
        np.fft.fft(sig)
    reps = max(1, 50000 // N)
    time_numpy.append((time.perf_counter() - t0) / reps)

    print(f"  N={N:5d}  naive={time_naive[-1]:.4e}s  "
          f"radix2={time_radix2[-1]:.4e}s  numpy={time_numpy[-1]:.4e}s")

# --- Timing figure ---
fig1, ax1 = plt.subplots(figsize=(8, 5))
fig1.suptitle("DFT / FFT Timing Comparison", fontsize=13, fontweight='bold')

Ns = np.array(sizes_timing, dtype=float)
ax1.loglog(Ns, time_naive,  'o-', color='#e74c3c', lw=2, ms=5,
           label="Naïve DFT  O(N²)")
ax1.loglog(Ns, time_radix2, 's-', color='#2980b9', lw=2, ms=5,
           label="Radix-2 FFT  O(N log N)")
ax1.loglog(Ns, time_numpy,  '^-', color='#27ae60', lw=2, ms=5,
           label="NumPy FFT (C)")

# Reference slopes
ref = Ns[2:7]
ax1.loglog(ref, 3e-6 * (ref / ref[0])**2,  'k--', lw=1, alpha=0.3,
           label="O(N²)")
ax1.loglog(ref, 3e-5 * (ref / ref[0]) * np.log2(ref / ref[0] + 1),
           'k:', lw=1, alpha=0.3, label="O(N log N)")

ax1.set_xlabel("Signal length  N")
ax1.set_ylabel("Wall-clock time  (s)")
ax1.legend(fontsize=9); ax1.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig("fft_timing.png", dpi=150, bbox_inches='tight')
print("\nSaved: fft_timing.png")
plt.show(); plt.close(fig1)


# ─────────────────────────────────────────────────────────────────────────────
# --- 3. THE 2-D DFT ---
# ─────────────────────────────────────────────────────────────────────────────

Ngrid = 512
x2 = np.linspace(0, 1, Ngrid, endpoint=False)
X2, Y2 = np.meshgrid(x2, x2)

# Superimposed gratings at different angles / frequencies
pattern = (np.sin(2 * np.pi * 8 * X2) +
           np.sin(2 * np.pi * 12 * Y2) +
           np.sin(2 * np.pi * (5 * X2 + 10 * Y2)) +
           0.5 * np.sin(2 * np.pi * 20 * X2) * np.cos(2 * np.pi * 15 * Y2))

F2 = np.fft.fftshift(np.fft.fft2(pattern))
mag2 = np.log1p(np.abs(F2))

fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(11, 5))
fig2.suptitle("2-D DFT — Spatial-Frequency Decomposition",
              fontsize=13, fontweight='bold')

ax2a.imshow(pattern, cmap='gray', origin='lower',
            extent=[0, 1, 0, 1])
ax2a.set_title("Spatial Domain", fontweight='bold')
ax2a.set_xlabel("x"); ax2a.set_ylabel("y")

freq_ext = [-Ngrid/2, Ngrid/2, -Ngrid/2, Ngrid/2]
ax2b.imshow(mag2, cmap='inferno', origin='lower', extent=freq_ext)
ax2b.set_title("log(1 + |F(kx, ky)|)", fontweight='bold')
ax2b.set_xlabel("$k_x$  (cycles)"); ax2b.set_ylabel("$k_y$  (cycles)")
ax2b.set_xlim(-50, 50); ax2b.set_ylim(-50, 50)

plt.tight_layout()
plt.savefig("fft_2d_spectrum.png", dpi=150, bbox_inches='tight')
print("Saved: fft_2d_spectrum.png")
plt.show(); plt.close(fig2)


# ─────────────────────────────────────────────────────────────────────────────
# --- 4. POWER SPECTRAL DENSITY ---
# ─────────────────────────────────────────────────────────────────────────────

from scipy.signal import welch, get_window

fs   = 1000.0                    # sampling rate (Hz)
T    = 2.0                       # duration (s)
t_psd = np.arange(0, T, 1/fs)
np.random.seed(7)

# Composite signal: 3 sinusoids buried in noise
freqs_true = [50, 120, 300]
amps_true  = [1.0, 0.6, 0.3]
signal_clean = sum(a * np.sin(2*np.pi*f*t_psd) for a, f in zip(amps_true, freqs_true))
noise  = 1.5 * np.random.randn(len(t_psd))
signal = signal_clean + noise

# Periodogram
N_psd  = len(signal)
X_psd  = np.fft.rfft(signal)
f_psd  = np.fft.rfftfreq(N_psd, d=1/fs)
periodogram = (2.0 / (N_psd * fs)) * np.abs(X_psd)**2

# Welch PSD
f_welch, psd_welch = welch(signal, fs=fs, window='hann',
                           nperseg=256, noverlap=128)

fig3, axes3 = plt.subplots(3, 1, figsize=(10, 8))
fig3.suptitle("Power Spectral Density — Hidden Sinusoids in Noise",
              fontsize=13, fontweight='bold')

axes3[0].plot(t_psd, signal, color='#888888', lw=0.5, alpha=0.7)
axes3[0].plot(t_psd, signal_clean, color='#e74c3c', lw=1.2, label="Clean signal")
axes3[0].set_xlabel("Time (s)"); axes3[0].set_ylabel("Amplitude")
axes3[0].set_title("Time Domain", fontweight='bold')
axes3[0].legend(fontsize=9); axes3[0].set_xlim(0, 0.2)
axes3[0].grid(True, alpha=0.3)

axes3[1].semilogy(f_psd, periodogram, color='#2980b9', lw=0.8, alpha=0.7)
for freq in freqs_true:
    axes3[1].axvline(freq, color='#e74c3c', ls='--', lw=1, alpha=0.5)
axes3[1].set_xlabel("Frequency (Hz)"); axes3[1].set_ylabel("PSD (V²/Hz)")
axes3[1].set_title("Periodogram  (noisy)", fontweight='bold')
axes3[1].set_xlim(0, fs/2); axes3[1].grid(True, alpha=0.3)

axes3[2].semilogy(f_welch, psd_welch, color='#27ae60', lw=2)
for freq in freqs_true:
    axes3[2].axvline(freq, color='#e74c3c', ls='--', lw=1, alpha=0.5)
axes3[2].set_xlabel("Frequency (Hz)"); axes3[2].set_ylabel("PSD (V²/Hz)")
axes3[2].set_title("Welch's Method  (averaged, Hann window)", fontweight='bold')
axes3[2].set_xlim(0, fs/2); axes3[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("fft_power_spectrum.png", dpi=150, bbox_inches='tight')
print("Saved: fft_power_spectrum.png")
plt.show(); plt.close(fig3)


# ─────────────────────────────────────────────────────────────────────────────
# --- 5. SPECTRAL DIFFERENTIATION ---
# ─────────────────────────────────────────────────────────────────────────────

def spectral_derivative(f_vals, L=2*np.pi):
    """Differentiate periodic f on [0, L) via Fourier coefficients."""
    N = len(f_vals)
    F = np.fft.fft(f_vals)
    freqs = np.fft.fftfreq(N, d=L / (2*np.pi*N))
    # Zero the Nyquist mode for even N to keep result real
    if N % 2 == 0:
        F[N // 2] = 0
    return np.real(np.fft.ifft(1j * freqs * F))


def fd2_derivative(f_vals, dx):
    """2nd-order centred finite difference."""
    return (np.roll(f_vals, -1) - np.roll(f_vals, 1)) / (2 * dx)


def fd4_derivative(f_vals, dx):
    """4th-order centred finite difference."""
    return (-np.roll(f_vals, -2) + 8*np.roll(f_vals, -1)
            - 8*np.roll(f_vals, 1) + np.roll(f_vals, 2)) / (12 * dx)


# Test function: f(x) = sin(3x) + cos(7x),  f'(x) = 3cos(3x) - 7sin(7x)
test_f      = lambda x: np.sin(3*x) + np.cos(7*x)
test_fprime = lambda x: 3*np.cos(3*x) - 7*np.sin(7*x)

Ns_diff = np.arange(8, 129, 2)
err_spectral = []
err_fd2      = []
err_fd4      = []

for Nd in Ns_diff:
    xd = np.linspace(0, 2*np.pi, Nd, endpoint=False)
    dx_d = 2*np.pi / Nd
    fv = test_f(xd)
    exact_d = test_fprime(xd)

    err_spectral.append(np.max(np.abs(spectral_derivative(fv) - exact_d)))
    err_fd2.append(np.max(np.abs(fd2_derivative(fv, dx_d) - exact_d)))
    err_fd4.append(np.max(np.abs(fd4_derivative(fv, dx_d) - exact_d)))

fig4, ax4 = plt.subplots(figsize=(8, 5))
fig4.suptitle("Spectral vs Finite-Difference Differentiation",
              fontsize=13, fontweight='bold')

ax4.semilogy(Ns_diff, err_fd2,      'o-', color='#e74c3c', lw=2, ms=4,
             label="FD 2nd order  O(h²)")
ax4.semilogy(Ns_diff, err_fd4,      's-', color='#2980b9', lw=2, ms=4,
             label="FD 4th order  O(h⁴)")
ax4.semilogy(Ns_diff, err_spectral, '^-', color='#27ae60', lw=2, ms=4,
             label="Spectral (Fourier)")

ax4.axhline(1e-14, color='#888888', ls=':', lw=1, alpha=0.5, label="Machine ε")
ax4.set_xlabel("Number of grid points  N")
ax4.set_ylabel("Max |error|  (log scale)")
ax4.set_title("f(x) = sin(3x) + cos(7x)  on  [0, 2π)", fontweight='bold')
ax4.legend(fontsize=9); ax4.grid(True, which='both', alpha=0.3)
ax4.set_ylim(1e-16, 1e1)

plt.tight_layout()
plt.savefig("fft_spectral_diff.png", dpi=150, bbox_inches='tight')
print("Saved: fft_spectral_diff.png")
plt.show(); plt.close(fig4)


# ─────────────────────────────────────────────────────────────────────────────
# --- 6. CHEBYSHEV POLYNOMIALS & SPECTRAL CONVERGENCE ---
# ─────────────────────────────────────────────────────────────────────────────

def chebyshev_nodes(n):
    """n Chebyshev–Gauss–Lobatto nodes on [-1, 1]."""
    return np.cos(np.pi * np.arange(n) / (n - 1))


def barycentric_interp(xn, fn, x):
    """Barycentric Lagrange interpolation with Chebyshev weights."""
    n = len(xn)
    w = np.ones(n)
    w[0] = 0.5; w[-1] = 0.5
    w *= (-1.0)**np.arange(n)

    # Evaluate at target points x
    numer = np.zeros_like(x)
    denom = np.zeros_like(x)
    exact_idx = np.full(x.shape, -1, dtype=int)

    for j in range(n):
        diff = x - xn[j]
        mask_exact = np.abs(diff) < 1e-15
        exact_idx[mask_exact] = j
        safe = np.where(mask_exact, 1.0, diff)
        term = w[j] / safe
        term[mask_exact] = 0.0
        numer += term * fn[j]
        denom += term

    result = numer / denom
    for j in range(n):
        result[exact_idx == j] = fn[j]
    return result


# --- Test functions ---
runge     = lambda x: 1.0 / (1.0 + 25.0 * x**2)
step_func = lambda x: np.where(x < 0, -1.0, 1.0)

x_fine = np.linspace(-1, 1, 1000)

fig5, axes5 = plt.subplots(2, 2, figsize=(12, 9))
fig5.suptitle("Chebyshev vs Equispaced Interpolation",
              fontsize=13, fontweight='bold')

# --- Top-left: Runge function, equispaced ---
ax = axes5[0, 0]
ax.plot(x_fine, runge(x_fine), 'k-', lw=2.5, label="True function")
for n_pts, col in [(9, '#e74c3c'), (15, '#2980b9'), (21, '#27ae60')]:
    xn = np.linspace(-1, 1, n_pts)
    fn = runge(xn)
    poly = np.polyfit(xn, fn, n_pts - 1)
    ax.plot(x_fine, np.polyval(poly, x_fine), '--', color=col, lw=1.5,
            label=f"n = {n_pts}")
ax.set_title("Equispaced Nodes — Runge's Function", fontweight='bold')
ax.set_ylim(-0.5, 1.5); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# --- Top-right: Runge function, Chebyshev ---
ax = axes5[0, 1]
ax.plot(x_fine, runge(x_fine), 'k-', lw=2.5, label="True function")
for n_pts, col in [(9, '#e74c3c'), (15, '#2980b9'), (21, '#27ae60')]:
    xn = chebyshev_nodes(n_pts)
    fn = runge(xn)
    yi = barycentric_interp(xn, fn, x_fine)
    ax.plot(x_fine, yi, '--', color=col, lw=1.5, label=f"n = {n_pts}")
ax.set_title("Chebyshev Nodes — Runge's Function", fontweight='bold')
ax.set_ylim(-0.5, 1.5); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

# --- Bottom-left: convergence comparison ---
ax = axes5[1, 0]
ns_conv = np.arange(5, 61)
err_equi = []
err_cheb = []
for n_pts in ns_conv:
    # Equispaced
    xn_e = np.linspace(-1, 1, n_pts)
    fn_e = runge(xn_e)
    poly  = np.polyfit(xn_e, fn_e, n_pts - 1)
    err_equi.append(np.max(np.abs(np.polyval(poly, x_fine) - runge(x_fine))))
    # Chebyshev
    xn_c = chebyshev_nodes(n_pts)
    fn_c = runge(xn_c)
    yi_c = barycentric_interp(xn_c, fn_c, x_fine)
    err_cheb.append(np.max(np.abs(yi_c - runge(x_fine))))

ax.semilogy(ns_conv, err_equi, 'o-', color='#e74c3c', lw=2, ms=3,
            label="Equispaced (diverges!)")
ax.semilogy(ns_conv, err_cheb, 's-', color='#27ae60', lw=2, ms=3,
            label="Chebyshev (exponential)")
ax.set_xlabel("Number of nodes  n")
ax.set_ylabel("Max |error|")
ax.set_title("Convergence: 1/(1 + 25x²)", fontweight='bold')
ax.legend(fontsize=9); ax.grid(True, which='both', alpha=0.3)

# --- Bottom-right: step function — Gibbs phenomenon ---
ax = axes5[1, 1]
ax.plot(x_fine, step_func(x_fine), 'k-', lw=2.5, label="True step")
for n_pts, col in [(11, '#e74c3c'), (21, '#2980b9'), (51, '#27ae60')]:
    xn_c = chebyshev_nodes(n_pts)
    fn_c = step_func(xn_c)
    yi_c = barycentric_interp(xn_c, fn_c, x_fine)
    ax.plot(x_fine, yi_c, '-', color=col, lw=1.2, alpha=0.8,
            label=f"Chebyshev n = {n_pts}")
ax.set_title("Gibbs Phenomenon — Step Function", fontweight='bold')
ax.set_ylim(-1.5, 1.5); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("fft_chebyshev.png", dpi=150, bbox_inches='tight')
print("Saved: fft_chebyshev.png")
plt.show(); plt.close(fig5)


# ─────────────────────────────────────────────────────────────────────────────
# --- 7. ARTISTIC FIGURE — SIGNAL RECONSTRUCTION ---
#     Demonstrates how the Fourier transform separates signal from noise:
#     keep only the spectral peaks above a descending threshold to
#     progressively recover the clean waveform.
# ─────────────────────────────────────────────────────────────────────────────

from matplotlib.animation import FuncAnimation, PillowWriter

# Build a composite signal — low-frequency, clearly visible waveform
np.random.seed(2026)
N_art   = 4096
fs_art  = 500.0
t_art   = np.arange(N_art) / fs_art

components = [
    (1.0,   3.0, 0.0),     # (amplitude, frequency Hz, phase)
    (0.8,   7.5, 1.2),
    (0.5,  13.0, 0.5),
    (0.35, 21.0, 2.8),
]
clean = sum(a * np.sin(2*np.pi*f*t_art + p) for a, f, p in components)
noisy = clean + 0.6 * np.random.randn(N_art)

# Fourier analysis — identify spectral peaks above noise floor
F_art     = np.fft.rfft(noisy)
freqs_art = np.fft.rfftfreq(N_art, d=1/fs_art)
magnitude = np.abs(F_art)
mag_order = np.argsort(magnitude)[::-1]


def reconstruct_top_k(k):
    """Reconstruct keeping only the k largest-magnitude Fourier bins."""
    F_k = np.zeros_like(F_art)
    idx = mag_order[:k]
    F_k[idx] = F_art[idx]
    return np.fft.irfft(F_k, n=N_art)


# ── 7a. Static artistic figure ──────────────────────────────────────────────

with plt.style.context('dark_background'):

    fig6, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [2.5, 1]})
    fig6.patch.set_facecolor('#0d1117')
    for a in (ax_top, ax_bot):
        a.set_facecolor('#0d1117')

    # --- Top panel: time domain ---
    # Noisy signal — faint background
    ax_top.plot(t_art, noisy, color='#444444', lw=0.35, alpha=0.45, zorder=1)

    # Progressive reconstructions (increasing detail)
    ks      = [4, 8, 16, 40]
    colours = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1']
    for k, col in zip(ks, colours):
        recon = reconstruct_top_k(k)
        ax_top.plot(t_art, recon, color=col, lw=1.3, alpha=0.6, zorder=3,
                    label=f"Top {k} coefficients")

    # Clean signal — bright white on top
    ax_top.plot(t_art, clean, color='white', lw=2, alpha=0.9, zorder=5,
                label="Clean signal")

    ax_top.axhline(0, color='#333333', lw=0.8)
    ax_top.set_xlim(0, 2.0)
    ax_top.set_ylim(-3.5, 3.5)
    ax_top.set_xlabel("Time  (s)", color='#aaaaaa', fontsize=11)
    ax_top.set_ylabel("Amplitude", color='#aaaaaa', fontsize=11)
    ax_top.tick_params(colors='#555555')
    for sp in ax_top.spines.values():
        sp.set_edgecolor('#2a2a2a')
    ax_top.legend(fontsize=9, loc='upper right',
                  facecolor='#1a1a2e', edgecolor='#333333',
                  labelcolor='white')

    # --- Bottom panel: frequency domain ---
    ax_bot.semilogy(freqs_art, magnitude / N_art, color='#666666', lw=0.5,
                    alpha=0.6, zorder=1)

    # Highlight the kept coefficients at each level
    for k, col in zip(ks, colours):
        idx = mag_order[:k]
        ax_bot.scatter(freqs_art[idx], magnitude[idx] / N_art,
                       color=col, s=25, zorder=4, alpha=0.8)

    ax_bot.set_xlim(0, 50)
    ax_bot.set_ylim(1e-4, 1)
    ax_bot.set_xlabel("Frequency  (Hz)", color='#aaaaaa', fontsize=11)
    ax_bot.set_ylabel("|X[k]| / N", color='#aaaaaa', fontsize=11)
    ax_bot.tick_params(colors='#555555')
    for sp in ax_bot.spines.values():
        sp.set_edgecolor('#2a2a2a')
    ax_bot.grid(True, which='both', alpha=0.15)

    fig6.suptitle("F O U R I E R   R E C O N S T R U C T I O N",
                  color='white', alpha=0.75, fontsize=14,
                  fontweight='bold', y=0.98)
    fig6.text(0.5, 0.005,
              "Recovering a composite signal from noisy Fourier coefficients",
              color='#888888', fontsize=9, ha='center')

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])
    plt.savefig("fft_spectral_artistic.png", dpi=180, bbox_inches='tight',
                facecolor=fig6.get_facecolor())
    print("Saved: fft_spectral_artistic.png")
    plt.show(); plt.close(fig6)


# ── 7b. Animated GIF — progressive reconstruction ───────────────────────────

with plt.style.context('dark_background'):

    k_sweep  = np.unique(np.geomspace(1, len(F_art), 80).astype(int))
    n_frames = len(k_sweep)

    fig7, ax7 = plt.subplots(figsize=(10, 5))
    fig7.patch.set_facecolor('#0d1117')
    ax7.set_facecolor('#0d1117')

    def _update_art(frame):
        ax7.clear()
        ax7.set_facecolor('#0d1117')

        k = k_sweep[frame]
        recon = reconstruct_top_k(k)

        ax7.plot(t_art, noisy, color='#333333', lw=0.3, alpha=0.4)
        ax7.plot(t_art, clean, color='white',   lw=1.0, alpha=0.3)
        ax7.plot(t_art, recon, color='#48dbfb',  lw=1.8, alpha=0.9)

        ax7.set_xlim(0, 2.0); ax7.set_ylim(-3.5, 3.5)
        ax7.set_xlabel("Time  (s)", color='#aaaaaa', fontsize=10)
        ax7.set_ylabel("Amplitude", color='#aaaaaa', fontsize=10)
        ax7.tick_params(colors='#555555')
        for sp in ax7.spines.values():
            sp.set_edgecolor('#2a2a2a')
        ax7.set_title("Fourier Reconstruction",
                      color='white', alpha=0.75, fontsize=12,
                      fontweight='bold')
        ax7.text(0.03, 0.95,
                 f"Top {k} / {len(F_art)} coefficients",
                 transform=ax7.transAxes, color='white',
                 fontsize=11, va='top', fontweight='bold')

    anim = FuncAnimation(fig7, _update_art, frames=n_frames,
                         interval=80, blit=False)
    anim.save("fft_spectral_artistic.gif", writer=PillowWriter(fps=12),
              dpi=120, savefig_kwargs={'facecolor': fig7.get_facecolor()})
    print("Saved: fft_spectral_artistic.gif")
    plt.close(fig7)

print("\nAll plots complete.")
