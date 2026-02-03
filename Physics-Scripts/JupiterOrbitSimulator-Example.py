# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. SETUP CONSTANTS & MASSES ---
G = 6.67430e-11 

# Masses (kg)
masses_dict = {
    'Jupiter': 1.898e27,
    'Io': 8.9319e22,
    'Europa': 4.7998e22,
    'Ganymede': 1.4819e23,
    'Callisto': 1.0759e23
}
names = list(masses_dict.keys())
masses = np.array(list(masses_dict.values()))

# --- 2. INITIAL CONDITIONS (MANUAL / OFFLINE) ---
print("Setting up initial conditions (Offline Mode)...", flush=True)

# Format: [x, y, z, vx, vy, vz]
y0 = np.concatenate([
    [0, 0, 0, 0, 0, 0],                # Jupiter (Center)
    [4.217e8, 0, 1e6, 0, 17334, 0],      # Io
    [6.710e8, 0, 1e8, 0, 13740, 0],      # Europa
    [1.070e9, 0, 1e9, 0, 10880, 0],      # Ganymede
    [1.883e9, 1e3, 0, 0, 8204, 0]        # Callisto
])

# --- 3. PHYSICS ENGINE ---
last_printed_day = -1

def n_body_equations(t, y, masses):
    global last_printed_day
    
    # Progress Tracker
    day = int(t / 86400) # 86400 seconds in a day
    if day > last_printed_day:
        print(f"Simulating Day {day}...", end='\r', flush=True) # \r updates the same line
        last_printed_day = day

    n = len(masses)
    state = y.reshape((n, 6))
    pos = state[:, :3]
    vel = state[:, 3:]
    acc = np.zeros_like(pos)
    
    # Force calculation
    for i in range(n):
        for j in range(n):
            if i != j:
                r_vec = pos[j] - pos[i]
                r_mag = np.linalg.norm(r_vec)
                # Safety check to prevent crashes if bodies overlap
                if r_mag < 1000: r_mag = 1000 
                acc[i] += G * masses[j] * r_vec / r_mag**3
    
    return np.concatenate((vel, acc), axis=1).flatten()

# --- 4. RUN SIMULATION ---
days = 200
print(f"Starting integration for {days} days...", flush=True, end = '\r')

t_span = (0, days * 24 * 3600)
# 'LSODA' is faster/more robust than default 'RK45'
sol = solve_ivp(n_body_equations, t_span, y0, args=(masses,), method='LSODA', rtol=1e-6)

print("\nSimulation Complete!", flush=True)

# --- 5. PLOTTING ---
data = sol.y.reshape((len(names), 6, -1))
jup_pos = data[0, :3, :]

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
colors = ['orange', 'red', 'brown', 'purple', 'gray']

for i, name in enumerate(names):
    if name == 'Jupiter': continue
    
    # Relative to Jupiter
    x = data[i, 0, :] - jup_pos[0, :]
    y = data[i, 1, :] - jup_pos[1, :]
    z = data[i, 2, :] - jup_pos[2, :]
    
    ax.plot(x, y, z, label=name, color=colors[i])

ax.set_title("Orbits of Galilean Moons (Offline Simulation)")
ax.legend()
plt.show()

# --- 6. KEPLER CHECK ---
print("\n--- KEPLER'S LAW CHECK ---")
print(f"{'Moon':<10} | {'Ratio (T^2/a^3)':<20}")

for i, name in enumerate(names):
    if name == 'Jupiter': continue
    
    # Get arrays
    rx = data[i, 0, :] - jup_pos[0, :]
    ry = data[i, 1, :] - jup_pos[1, :]
    rz = data[i, 2, :] - jup_pos[2, :]
    
    # Semi-major axis (a)
    dist = np.sqrt(rx**2 + ry**2 + rz**2)
    a = np.mean(dist)
    
    # Period (T) via Angle Slope
    theta = np.unwrap(np.arctan2(ry, rx))
    
    # Use sol.t to ensure array lengths match perfectly
    coeffs = np.polyfit(sol.t, theta, 1)
    omega = np.abs(coeffs[0])
    
    T_sec = 2 * np.pi / omega
    ratio = (T_sec**2) / (a**3)
    
    print(f"{name:<10} | {ratio:.4e}")
    
# --- 7. ARTISTIC PLOT

# Switch to dark background for high contrast
# plt.style.use('dark_background')

fig_art = plt.figure(figsize=(12, 10))
ax_art = fig_art.add_subplot(111, projection='3d')

# --- STYLE SETTINGS ---
# Remove the gray "panes" (walls) of the 3D box
ax_art.xaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
ax_art.yaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
ax_art.zaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))

# Turn off the grid lines and axes
ax_art.grid(False)
ax_art.set_axis_off()

# Set the background color to pure black
fig_art.patch.set_facecolor('black')
ax_art.set_facecolor('black')

# different maps for different moons to distinguish them
cmaps = ['autumn', 'cool', 'winter', 'spring'] 

# --- PLOTTING ---
# 1. Plot Jupiter (The "Star" in the center)
# We plot it twice: once solid, once large and transparent for a "glow" effect
ax_art.plot([0], [0], [0], 'o', color='#ffcc00', markersize=6, zorder=20)
ax_art.plot([0], [0], [0], 'o', color='#ffcc00', markersize=20, alpha=0.2, zorder=19)

for i, name in enumerate(names):
    if name == 'Jupiter': continue
    
    # Extract coordinates relative to Jupiter
    x = data[i, 0, :] - jup_pos[0, :]
    y = data[i, 1, :] - jup_pos[1, :]
    z = data[i, 2, :] - jup_pos[2, :]
    
    # Create time gradient (0 to 1)
    c_norm = np.linspace(0, 1, len(x))
    
    # Create spatial gradient (0 to 1)
    c_norm = ( x - np.min(x) ) / (np.max(x) - np.min(x))
    
    # 3D Scatter with gradient coloring
    # s=0.5 makes a fine, smooth line-like appearance
    # alpha=0.8 allows for some blending
    sc = ax_art.scatter(x, y, z, c=c_norm, cmap=cmaps[i % 4], 
                        s=0.5, alpha=0.8, depthshade=True)
    
    # Add a bright "head" to the trail (current position)
    ax_art.scatter(x[-1], y[-1], z[-1], color='white', s=10, alpha=1.0)


# Force aspect ratio to be equal
limit = 2.0e9 # 2 million km
ax_art.set_xlim(-limit, limit)
ax_art.set_ylim(-limit, limit)
ax_art.set_zlim(-limit, limit)

# Add a title
plt.title("O R B I T S", color='white', alpha=0.6, y=0.95, fontsize=15)

# Set a nice initial viewing angle (elevation, azimuth)
ax_art.view_init(elev=30, azim=-60)
plt.show()