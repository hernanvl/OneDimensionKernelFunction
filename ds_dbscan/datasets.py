"""Loaders for the 2D LiDAR scans used in the DS-DBSCAN experiments.

Real scans are stored as CSV files with columns
``timestamp, quality, angle_deg, distance_mm`` produced by the recording
tool; each distinct timestamp corresponds to one full scan (frame).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def load_scans_csv(path, min_quality=0, flip_angle=True):
    """Load a recorded CSV into a list of scans.

    Parameters
    ----------
    path : str
        Path to the recorded CSV.
    min_quality : int
        Drop returns whose reported quality is below this value.
    flip_angle : bool
        Apply the ``(180 - angle) % 360`` convention used by the recorder.

    Returns
    -------
    list of tuple(ndarray, ndarray)
        One ``(r, theta)`` pair per frame, with ``r`` in metres and ``theta``
        in radians.
    """
    df = pd.read_csv(path)
    if min_quality:
        df = df[df["quality"] >= min_quality]
    scans = []
    for _, frame in df.groupby("timestamp", sort=True):
        angle_deg = frame["angle_deg"].to_numpy(dtype=float)
        if flip_angle:
            angle_deg = (180.0 - angle_deg) % 360.0
        theta = np.radians(angle_deg)
        r = frame["distance_mm"].to_numpy(dtype=float) / 1000.0
        mask = r > 0
        scans.append((r[mask], theta[mask]))
    return scans


def polar_to_xy(r, theta):
    """Convert polar returns to an ``(n, 2)`` Cartesian array."""
    r = np.asarray(r, dtype=float)
    theta = np.asarray(theta, dtype=float)
    return np.column_stack([r * np.cos(theta), r * np.sin(theta)])


def stack_polar(r, theta):
    """Stack range and angle into the ``(n, 2)`` array that ``DSDBSCAN.fit`` expects."""
    return np.column_stack([np.asarray(r, dtype=float), np.asarray(theta, dtype=float)])
