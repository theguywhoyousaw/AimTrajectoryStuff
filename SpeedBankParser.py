#!/usr/bin/env python3
import re
import sys

def parse_profiles(header_path):
    """
    Parse the SpeedProfile entries from the given header file.
    Returns a list of tuples (dist, data_list).
    """
    with open(header_path, 'r') as f:
        lines = f.readlines()

    profiles = []
    i = 0
    # look for each entry starting with a lone '{'
    while i < len(lines):
        if lines[i].strip() == "{":
            # next line has dx, dy, dist,
            header_line = lines[i+1].strip().rstrip(',')
            parts = [p.strip() for p in header_line.split(',')]
            if len(parts) >= 3:
                dist = float(parts[2].rstrip('f'))
            else:
                i += 1
                continue

            # skip to the opening brace of the data array
            # which should be two lines down
            j = i + 3
            data = []
            # collect floats until the closing '}'
            while j < len(lines):
                line = lines[j].strip()
                if line.startswith('}'):
                    break
                # strip trailing commas and 'f' suffix
                val_str = line.rstrip(',').rstrip('f')
                try:
                    data.append(float(val_str))
                except ValueError:
                    pass
                j += 1

            if len(data) == 100:
                profiles.append((dist, data))
            else:
                print(f"Warning: found {len(data)} data points (expected 100) at entry starting line {i+1}", file=sys.stderr)

            # move index past this entry
            i = j
        i += 1

    return profiles

def check_distances(profiles, tol=1e-6):
    """
    For each profile, compare dist to sum(data).
    Prints any mismatches.
    """
    mismatches = []
    for idx, (dist, data) in enumerate(profiles):
        s = sum(data)
        if abs(s - dist) > tol:
            mismatches.append((idx, dist, s))
    return mismatches

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/speed_bank.h")
        sys.exit(1)
    header_path = sys.argv[1]
    profiles = parse_profiles(header_path)
    mismatches = check_distances(profiles)
    if not mismatches:
        print("All entries OK: sum(data) matches dist within tolerance.")
    else:
        print(f"{len(mismatches)} mismatches found:")
        for idx, dist, s in mismatches:
            print(f" Entry #{idx:3d}: dist = {dist:.8f}, sum(data) = {s:.8f}, diff = {s - dist:.2e}")

if __name__ == "__main__":
    main()
