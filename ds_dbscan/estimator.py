"""scikit-learn-compatible DS-DBSCAN estimator."""
from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.cluster import DBSCAN

from .kernel import schedule_alpha, transition_range, warp_polar


class DSDBSCAN(BaseEstimator, ClusterMixin):
    """Device-sensitive DBSCAN for 2D LiDAR scans.

    The estimator applies the radial power warp ``r' = r ** alpha`` to a
    scan's polar coordinates and then runs standard DBSCAN on the warped
    Cartesian coordinates. The exponent is computed per scan from the median
    range and the sensor geometry, so the estimator follows the same
    ``fit`` / ``fit_predict`` / ``labels_`` interface as
    :class:`sklearn.cluster.DBSCAN`. When ``alpha_min == alpha_max == 1`` the
    warp is the identity and the result is identical to plain DBSCAN.

    Parameters
    ----------
    eps : float
        Neighbourhood radius passed to the underlying DBSCAN.
    min_samples : int
        Minimum number of points to form a core point.
    delta_theta : float
        Sensor angular resolution in radians.
    alpha_min, alpha_max : float
        Lower and upper bounds of the warp exponent.
    tau : float
        Steepness of the logistic schedule, in metres.
    s_obj : float
        Representative object width (metres) used to derive the transition range.

    Attributes
    ----------
    labels_ : ndarray of shape (n,)
        Cluster labels for each point; noise is labelled ``-1``.
    alpha_ : float
        Warp exponent selected for the fitted scan.
    transition_range_ : float
        Transition range ``r0`` derived from the sensor geometry.
    """

    def __init__(self, eps=0.12, min_samples=3, delta_theta=np.radians(1.0),
                 alpha_min=0.30, alpha_max=0.70, tau=1.5, s_obj=0.40):
        self.eps = eps
        self.min_samples = min_samples
        self.delta_theta = delta_theta
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.tau = tau
        self.s_obj = s_obj

    def _select_alpha(self, r):
        r_bar = float(np.median(r))
        r0 = transition_range(self.s_obj, self.min_samples, self.delta_theta)
        alpha = schedule_alpha(r_bar, r0, self.alpha_min, self.alpha_max, self.tau)
        return alpha, r0

    def fit(self, X, y=None):
        """Cluster a scan given as polar coordinates.

        Parameters
        ----------
        X : array-like of shape (n, 2)
            Columns are range ``r`` (metres) and angle ``theta`` (radians).
        """
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != 2:
            raise ValueError("X must have shape (n, 2) with columns (r, theta).")
        r, theta = X[:, 0], X[:, 1]
        self.alpha_, self.transition_range_ = self._select_alpha(r)
        self.warped_coords_ = warp_polar(r, theta, self.alpha_)
        self._dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        self._dbscan.fit(self.warped_coords_)
        self.labels_ = self._dbscan.labels_
        return self

    def fit_predict(self, X, y=None):
        """Cluster ``X`` and return the per-point labels."""
        self.fit(X)
        return self.labels_
