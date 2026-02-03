# -*- coding: utf-8 -*-
"""
Created on Tue Feb  3 01:06:36 2026

@author: Matt
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from astroquery.jplhorizons import Horizons
from astropy.time import Time
import socket

# Increase timeout for slow NASA connections
socket.setdefaulttimeout(30)

# --- 1. SETUP ---
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
body_ids = {'Jupiter': '599', 'Io': '501', 'Europa': '502', 'Ganymede': '503', 'Callisto': '504'}

# --- 2. FETCH REAL DATA (Step-by-Step) ---
def get_real_data():
    print("--- CONNECTING TO NASA JPL HORIZONS ---")
    t_start = Time.now().jd
    y_list = []
    
    for name in names:
        jpl_id = body_ids[name]
        print(f"1. Querying data for {name}...", end=" ", flush=True)
        
        try:
            # Query specific body
            obj = Horizons(id=jpl_id, location='@0', epochs=t_start)
            vec = obj.vectors()[0]
            print("Done.")
            
            # EXTRACT & CONVERT immediately to pure Python floats
            # (Crucial to prevent 'object' errors in solver)
            row = [
                float(vec['x']), float(vec['y']), float(vec['z']),
                float(vec['vx']), float(vec['vy']), float(vec['vz'])
            ]
            
            # Convert km -> meters
            y_list.extend([val * 1000 for val in row])
            
        except Exception as e:
            print(f"\nFAILED to fetch {name}. Error: {e}")
            print("Check your internet connection or VPN.")
            return None

    return np.array(y_list)

# Execute the fetch
y0 = get_real_data()

if y0 is None:
    print("CRITICAL ERROR: Could not retrieve data. Stopping.")
    exit()

# --- 3. PHYSICS ENGINE ---
last_printed_day = -1

def n_body_equations(t, y, masses):
    global last_printed_day
    
    # Progress Tracker
    day = int(t / 86400)
    if day > last_printed_day:
        print(f"Simulating Day {day} / 30...", end='\r', flush=True)
        last_printed_day = day

    n = len(masses)
    state = y.reshape((n, 6))
    pos = state[:, :3]
    vel = state[:, 3:]
    acc = np.zeros_like(pos)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                r_vec = pos[j] - pos[i]
                r_mag = np.linalg.norm(r_vec)
                
                # Gravity Softening (Prevent crashes if < 1000km)
                if r_mag < 1e6: r_mag = 1e6
                
                acc[i] += G * masses[j] * r_vec / r_mag**3
    
    return np.concatenate((vel, acc), axis=1).flatten()

# --- 4. RUN SIMULATION ---
days = 30
t_span = (0, days * 24 * 3600)
print(f"\n--- STARTING PHYSICS ENGINE ({days} Days) ---")

# LSODA is the robust solver that worked in the offline version
sol = solve_ivp(n_body_equations, t_span, y0, args=(masses,), method='LSODA', rtol=1e-6)

print("\nSimulation Complete!")

# --- 5. PLOTTING ---
data = sol.y.reshape((len(names), 6, -1))
jup_pos = data[0, :3, :]

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
colors = ['orange', 'red', 'brown', 'purple', 'gray']

for i, name in enumerate(names):
    if name == 'Jupiter': continue
    
    x = data[i, 0, :] - jup_pos[0, :]
    y = data[i, 1, :] - jup_pos[1, :]
    z = data[i, 2, :] - jup_pos[2, :]
    
    ax.plot(x, y, z, label=name, color=colors[i])

ax.set_title(f"Real Orbits (Data: {Time.now().iso[:10]})")
ax.legend()
plt.show()

# --- 6. KEPLER CHECK ---
print("\n--- KEPLER'S LAW CHECK ---")
print(f"{'Moon':<10} | {'Ratio (T^2/a^3)':<20}")

for i, name in enumerate(names):
    if name == 'Jupiter': continue
    
    rx = data[i, 0, :] - jup_pos[0, :]
    ry = data[i, 1, :] - jup_pos[1, :]
    rz = data[i, 2, :] - jup_pos[2, :]
    
    dist = np.sqrt(rx**2 + ry**2 + rz**2)
    a = np.mean(dist)
    
    theta = np.unwrap(np.arctan2(ry, rx))
    
    # Using sol.t ensures alignment
    coeffs = np.polyfit(sol.t, theta, 1)
    omega = np.abs(coeffs[0])
    
    T_sec = 2 * np.pi / omega
    ratio = (T_sec**2) / (a**3)
    
    print(f"{name:<10} | {ratio:.4e}")