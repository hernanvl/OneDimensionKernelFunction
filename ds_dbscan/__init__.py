"""DS-DBSCAN: device-sensitive DBSCAN for 2D LiDAR scans.

A radial power warp ``r' = r ** alpha`` is applied to a scan's polar
coordinates before clustering with standard DBSCAN. The exponent ``alpha``
is derived from the scan's characteristic range and the sensor's angular
resolution, so far-field returns are pulled inward and a single ``eps``
becomes a workable compromise across the whole scan.
"""
from .estimator import DSDBSCAN
from .kernel import logistic, schedule_alpha, transition_range, warp_polar
from .metrics import ari, n_clusters, noise_rate

__all__ = [
    "DSDBSCAN",
    "logistic",
    "schedule_alpha",
    "transition_range",
    "warp_polar",
    "ari",
    "n_clusters",
    "noise_rate",
]
__version__ = "0.1.0"
