#!/usr/bin/env python3
"""
plot_trajectories_colored.py

Searches its own directory for:
    human_seed_*.csv
    automated_seed_*.csv

Plots:
  - All human trajectories in blue
  - Automated trajectories colored by seed value:
      seed <= 0.2  -> green
      seed <= 0.4  -> purple
      seed <= 0.6  -> orange
      seed <= 0.8  -> red
      seed <= 1.0  -> yellow (or any distinct color)

Each trajectory:
  - Loads X/Y columns (ignores time/garbage)
  - Un-wraps Y across ±180° smoothly
  - Computes deltas relative to the first point (so start at 0,0)

Usage:
    python plot_trajectories_colored.py
"""

import os
import glob
import csv
import matplotlib.pyplot as plt


def unwrap_deg(angle_list):
    """Unwraps a list of angles across ±180° boundary."""
    if not angle_list:
        return []
    unwrapped = [angle_list[0]]
    offset = 0.0
    for prev, curr in zip(angle_list[:-1], angle_list[1:]):
        diff = curr + offset - unwrapped[-1]
        if diff > 180:
            offset -= 360
        elif diff < -180:
            offset += 360
        unwrapped.append(curr + offset)
    return unwrapped


def load_xy(path):
    """Loads X and Y from a CSV with headers 'time','x','y'."""
    xs, ys = [], []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                xs.append(float(row['x']))
                ys.append(float(row['y']))
            except (ValueError, KeyError):
                continue
    return xs, ys


def get_seed_color(seed):
    """Returns plot color based on seed thresholds."""
    if seed <= 0.2:
        return 'green'
    elif seed <= 0.4:
        return 'purple'
    elif seed <= 0.6:
        return 'orange'
    elif seed <= 0.8:
        return 'red'
    else:
        return 'yellow'


def plot_human(files):
    for path in files:
        xs, ys = load_xy(path)
        if not xs:
            continue
        ys_un = unwrap_deg(ys)
        x0, y0 = xs[0], ys_un[0]
        dx = [x - x0 for x in xs]
        dy = [y - y0 for y in ys_un]
        label = os.path.basename(path).replace('.csv','')
        plt.plot(dx, dy, color='blue', label=f"Human: {label}")


def plot_automated(files):
    for path in files:
        # extract seed from filename, e.g. automated_seed_0.537362.csv
        fname = os.path.basename(path)
        try:
            seed_str = fname.split('_seed_')[1].rstrip('.csv')
            seed = float(seed_str)
        except (IndexError, ValueError):
            seed = None
        xs, ys = load_xy(path)
        if not xs or seed is None:
            continue
        ys_un = unwrap_deg(ys)
        x0, y0 = xs[0], ys_un[0]
        dx = [x - x0 for x in xs]
        dy = [y - y0 for y in ys_un]
        color = get_seed_color(seed)
        label = f"Automated (seed={seed:.3f})"
        plt.plot(dx, dy, color=color, label=label)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    human_files = glob.glob(os.path.join(base, "human_seed_*.csv"))
    auto_files  = glob.glob(os.path.join(base, "automated_seed_*.csv"))

    if not human_files and not auto_files:
        print("No matching CSVs found in", base)
        return

    plt.figure()
    plot_human(human_files)
    plot_automated(auto_files)

    plt.axhline(0, color='gray', linewidth=0.5)
    plt.axvline(0, color='gray', linewidth=0.5)
    plt.xlabel('ΔX from start')
    plt.ylabel('ΔY from start')
    plt.title('Trajectories: Human (blue) vs Automated (colored by seed)')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
