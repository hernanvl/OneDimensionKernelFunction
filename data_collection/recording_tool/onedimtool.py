#!/usr/bin/env python3
"""
RPLidar live animation + CSV recording, or replay from CSV.
"""

import argparse
import csv
import time
import sys
from rplidar import RPLidar

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

PORT_NAME = "/dev/ttyUSB0"
DMAX = 4000
IMIN = 0
IMAX = 50

#
#
#
def flip_angle(angle_deg):
    return (180.0 - angle_deg) % 360.0

# -------------------------
# Live recording animation
# -------------------------

def live_update(frame, iterator, line, writer):
    scan = next(iterator)
    timestamp = time.time()

    angles = []
    distances = []
    qualities = []

    for quality, angle, distance in scan:
        writer.writerow([timestamp, quality, angle, distance])
        #angles.append(np.radians(angle))
        angles.append(np.radians(flip_angle(angle)))

        distances.append(distance)
        qualities.append(quality)

    offsets = np.column_stack((angles, distances))
    line.set_offsets(offsets)
    line.set_array(np.array(qualities))

    return line,


# -------------------------
# Replay animation
# -------------------------

def replay_update(frame, scans, line):
    if frame >= len(scans):
        return line,

    scan = scans[frame]

    # angles = [np.radians(a) for _, a, _ in scan]
    angles = [np.radians(flip_angle(a)) for _, a, _ in scan]

    distances = [d for _, _, d in scan]
    qualities = [q for q, _, _ in scan]

    offsets = np.column_stack((angles, distances))
    line.set_offsets(offsets)
    line.set_array(np.array(qualities))

    return line,


# -------------------------
# Plot setup
# -------------------------

def setup_plot():
    fig = plt.figure()
    ax = plt.subplot(111, projection="polar")

    scatter = ax.scatter(
        [0, 0], [0, 0],
        s=5,
        c=[IMIN, IMAX],
        cmap=plt.cm.Greys_r,
        lw=0
    )

    ax.set_rmax(DMAX)
    ax.grid(True)

    return fig, scatter


# -------------------------
# Record mode
# -------------------------

def run_record(output_path):
    lidar = RPLidar(PORT_NAME)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "quality", "angle_deg", "distance_mm"])

        fig, scatter = setup_plot()
        iterator = lidar.iter_scans()

        ani = animation.FuncAnimation(
            fig,
            live_update,
            fargs=(iterator, scatter, writer),
            interval=50
        )

        try:
            plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            lidar.stop()
            lidar.disconnect()


# -------------------------
# Replay mode
# -------------------------

def run_replay(input_path):
    scans = []
    current_scan = []

    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        last_ts = None

        for row in reader:
            ts = float(row["timestamp"])
            q = int(row["quality"])
            a = float(row["angle_deg"])
            d = float(row["distance_mm"])

            if last_ts is None:
                last_ts = ts

            if ts != last_ts:
                scans.append(current_scan)
                current_scan = []
                last_ts = ts

            current_scan.append((q, a, d))

        if current_scan:
            scans.append(current_scan)

    fig, scatter = setup_plot()

    ani = animation.FuncAnimation(
        fig,
        replay_update,
        fargs=(scans, scatter),
        interval=50
    )

    plt.show()


# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Animate RPLidar scans live or replay from CSV."
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    record = subparsers.add_parser(
        "record", help="Record live Lidar data to CSV and animate"
    )
    record.add_argument(
        "output", help="Output CSV file"
    )

    replay = subparsers.add_parser(
        "replay", help="Replay animation from recorded CSV"
    )
    replay.add_argument(
        "input", help="Input CSV file"
    )

    args = parser.parse_args()

    if args.mode == "record":
        run_record(args.output)
    elif args.mode == "replay":
        run_replay(args.input)


if __name__ == "__main__":
    main()
