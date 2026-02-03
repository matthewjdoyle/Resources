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
# We place them on the X-axis with velocity on the Y-axis for circular orbits.
# This bypasses the NASA download error entirely.
print("Setting up initial conditions (Offline Mode)...", flush=True)

# Format: [x, y, z, vx, vy, vz]
y0 = np.concatenate([
    [0, 0, 0, 0, 0, 0],                # Jupiter (Center)
    [4.217e8, 0, 0, 0, 17334, 0],      # Io
    [6.710e8, 0, 0, 0, 13740, 0],      # Europa
    [1.070e9, 0, 0, 0, 10880, 0],      # Ganymede
    [1.883e9, 0, 0, 0, 8204, 0]        # Callisto
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
days = 1000
print(f"\rStarting integration for {days} days...", flush=True)

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