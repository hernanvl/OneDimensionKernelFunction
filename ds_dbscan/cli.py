"""Command-line entry point: cluster a recorded 2D LiDAR scan and report metrics.

Runs both classical DBSCAN and DS-DBSCAN on one frame of a recorded scan and
prints the noise rate and cluster count for each, so the effect of the warp
can be checked from the terminal.
"""
from __future__ import annotations

import argparse

import numpy as np
from sklearn.cluster import DBSCAN

from .datasets import load_scans_csv, polar_to_xy, stack_polar
from .estimator import DSDBSCAN
from .metrics import n_clusters, noise_rate


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cluster a recorded 2D LiDAR scan with DBSCAN and DS-DBSCAN "
                    "and report the noise rate and cluster count.")
    parser.add_argument("csv", help="recorded scan CSV "
                                     "(timestamp,quality,angle_deg,distance_mm)")
    parser.add_argument("--frame", type=int, default=0, help="frame index to cluster")
    parser.add_argument("--eps", type=float, default=0.12)
    parser.add_argument("--min-samples", type=int, default=3)
    parser.add_argument("--delta-theta", type=float, default=np.radians(1.0),
                        help="angular resolution in radians")
    parser.add_argument("--s-obj", type=float, default=0.40,
                        help="representative object width in metres")
    args = parser.parse_args(argv)

    scans = load_scans_csv(args.csv)
    if not scans:
        parser.error("no scans found in the CSV")
    if not 0 <= args.frame < len(scans):
        parser.error(f"frame must be in [0, {len(scans) - 1}]")
    r, theta = scans[args.frame]

    base = DBSCAN(eps=args.eps, min_samples=args.min_samples)
    base_labels = base.fit_predict(polar_to_xy(r, theta))
    ds = DSDBSCAN(eps=args.eps, min_samples=args.min_samples,
                  delta_theta=args.delta_theta, s_obj=args.s_obj)
    ds_labels = ds.fit_predict(stack_polar(r, theta))

    print(f"points:    {len(r)}")
    print(f"DBSCAN     noise={noise_rate(base_labels):.3f}  "
          f"clusters={n_clusters(base_labels)}")
    print(f"DS-DBSCAN  noise={noise_rate(ds_labels):.3f}  "
          f"clusters={n_clusters(ds_labels)}  alpha={ds.alpha_:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
