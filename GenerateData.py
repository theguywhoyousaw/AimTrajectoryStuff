#!/usr/bin/env python3
"""
log_to_csv.py

Parse an aim‐movement log dragged‐and‐dropped onto this script,
splitting it into per‐dataset CSVs and appending if they exist.

Usage:
    python log_to_csv.py path/to/logfile.txt

Outputs:
    For each "New dataset (TYPE), Seed fSEED:" marker in the log,
    creates/appends to TYPE_seed_SEED.csv in the same directory as the log.
    Each CSV has columns: time, x, y

Lines without X/Y data or dataset markers are ignored.
"""

import os
import re
import csv
import sys

def parse_log(logfile):
    # Pattern to detect new dataset markers
    new_pat = re.compile(r'New dataset \(([^)]+)\), Seed f([0-9.]+)')
    # Pattern to extract X and Y values
    xy_pat  = re.compile(r'X:\s*f?(-?[0-9.]+),\s*Y:\s*f?(-?[0-9.]+)')
    # Pattern to extract time (first numeric field)
    time_pat = re.compile(r'^\d+\t([\d.]+)')

    outdir = os.path.dirname(logfile) or '.'
    current_csv = None

    with open(logfile, 'r') as f:
        for line in f:
            # Detect new dataset
            m_new = new_pat.search(line)
            if m_new:
                dtype, seed = m_new.group(1), m_new.group(2)
                fname = f"{dtype.strip().lower().replace(' ','_')}_seed_{seed}.csv"
                current_csv = os.path.join(outdir, fname)
                # Create file with header if missing
                if not os.path.exists(current_csv):
                    with open(current_csv, 'w', newline='') as out:
                        csv.writer(out).writerow(['time','x','y'])
                continue

            # Detect X/Y lines
            if current_csv:
                m_xy = xy_pat.search(line)
                m_time = time_pat.match(line)
                if m_xy and m_time:
                    time = m_time.group(1)
                    x, y = m_xy.group(1), m_xy.group(2)
                    with open(current_csv, 'a', newline='') as out:
                        csv.writer(out).writerow([time, x, y])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python log_to_csv.py <log_file.txt>")
        sys.exit(1)
    logfile = sys.argv[1]
    parse_log(logfile)
    print("Finished: CSV files are in the same directory as the log.")
