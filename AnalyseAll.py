#!/usr/bin/env python3
"""
analyze_advanced.py

Enhanced analysis comparing automated trajectories against human trajectories:
  - Loads both human_seed_*.csv and automated_seed_*.csv
  - Processes trajectories (unwrap, zero at start, flip to positive quadrant, filter)
  - Computes discrete Fréchet distance matrix across all traces
  - Performs hierarchical clustering on combined set
  - Calculates silhouette score for overall clustering validity
  - Plots dendrogram labelling human vs automated
  - Generates per-cluster overlays, distinguishing human (blue) vs automated (red)

Dependencies:
  numpy, scipy, matplotlib, sklearn

Usage:
    python analyze_advanced.py [--clusters K]
"""
import os
import glob
import csv
import argparse
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score

# unwrap and preprocess unchanged

def unwrap_deg(angle_list):
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


def load_and_process(path):
    xs, ys = [], []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                xs.append(float(row['x']))
                ys.append(float(row['y']))
            except:
                continue
    if len(xs) < 2:
        return None
    ys = unwrap_deg(ys)
    x0, y0 = xs[0], ys[0]
    dx = [x - x0 for x in xs]
    dy = [y - y0 for y in ys]
    # flip into positive quadrant
    if dx[-1] < 0:
        dx = [-d for d in dx]
    if dy[-1] < 0:
        dy = [-d for d in dy]
    # retain only non-negative
    pts = [(x, y) for x, y in zip(dx, dy) if x >= 0 and y >= 0]
    if len(pts) < 2:
        return None
    return np.array(pts)


def discrete_frechet(P, Q):
    n, m = len(P), len(Q)
    ca = np.full((n, m), -1.0)
    def c(i, j):
        if ca[i, j] > -1:
            return ca[i, j]
        d = np.linalg.norm(P[i] - Q[j])
        if i == 0 and j == 0:
            ca[i, j] = d
        elif i > 0 and j == 0:
            ca[i, j] = max(c(i-1, 0), d)
        elif i == 0 and j > 0:
            ca[i, j] = max(c(0, j-1), d)
        else:
            ca[i, j] = max(min(c(i-1, j), c(i, j-1), c(i-1, j-1)), d)
        return ca[i, j]
    return c(n-1, m-1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clusters', type=int, default=5,
                        help='Number of clusters')
    args = parser.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))
    # gather files
    human_files = glob.glob(os.path.join(base, 'human_seed_*.csv'))
    auto_files  = glob.glob(os.path.join(base, 'automated_seed_*.csv'))
    all_files = []
    labels = []
    trajs = []
    # load human
    for p in human_files:
        pts = load_and_process(p)
        if pts is None: continue
        all_files.append(p)
        labels.append('H:' + os.path.basename(p))
        trajs.append(pts)
    # load automated
    for p in auto_files:
        pts = load_and_process(p)
        if pts is None: continue
        all_files.append(p)
        labels.append('A:' + os.path.basename(p))
        trajs.append(pts)

    N = len(trajs)
    if N < 2:
        print('Not enough trajectories to compare.'); return
    # compute distance matrix
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(i+1, N):
            d = discrete_frechet(trajs[i], trajs[j])
            D[i, j] = D[j, i] = d

    # clustering
    dm = squareform(D)
    Z = linkage(dm, method='average')
    # dendrogram
    plt.figure(figsize=(10,6))
    dendrogram(Z, labels=labels, leaf_rotation=90)
    plt.title('Hierarchical Clustering of Human & Automated')
    plt.tight_layout()
    plt.savefig(os.path.join(base,'dendrogram.png'))
    print('Dendrogram saved.')

    # assignment and silhouette
    clusters = fcluster(Z, t=args.clusters, criterion='maxclust')
    print('Cluster assignments:')
    for lab, c in zip(labels, clusters): print(f'  {lab} -> {c}')
    sil = silhouette_score(D, clusters, metric='precomputed')
    print(f'Silhouette score: {sil:.3f}')

    # per-cluster overlay plots
    for c_id in range(1, args.clusters+1):
        idx = [i for i, cl in enumerate(clusters) if cl == c_id]
        if not idx: continue
        plt.figure()
        for i in idx:
            pts = trajs[i]
            style = 'b-' if labels[i].startswith('H:') else 'r--'
            plt.plot(pts[:,0], pts[:,1], style, alpha=0.7)
        plt.title(f'Cluster {c_id} (n={len(idx)})')
        plt.xlabel('ΔX'); plt.ylabel('ΔY'); plt.grid(True)
        plt.savefig(os.path.join(base, f'cluster_{c_id}.png'))
        print(f'Cluster {c_id} plot saved.')

if __name__ == '__main__':
    main()
