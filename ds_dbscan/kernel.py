"""Device-sensitive radial warp for 2D LiDAR scans.

The warp is a radial power transform ``r' = r ** alpha`` whose exponent is
scheduled logistically from the scan's characteristic (median) range and the
sensor's angular resolution. With ``alpha < 1`` the stretched far field is
compressed; with ``alpha == 1`` the map is the identity.
"""
from __future__ import annotations

import numpy as np


def logistic(z):
    """Standard logistic function ``sigma(z) = 1 / (1 + exp(-z))``."""
    return 1.0 / (1.0 + np.exp(-z))


def transition_range(s_obj, min_samples, delta_theta):
    """Range at which an object of width ``s_obj`` is sampled by ``min_samples`` beams.

    ``r0 = s_obj / (min_samples * delta_theta)`` with ``delta_theta`` in radians.
    """
    return s_obj / (min_samples * delta_theta)


def schedule_alpha(r_bar, r0, alpha_min, alpha_max, tau):
    """Logistic schedule for the warp exponent.

    ``alpha = alpha_min + (alpha_max - alpha_min) * sigma((r0 - r_bar) / tau)``.
    The result is bounded to ``[alpha_min, alpha_max]`` and equals the midpoint
    when ``r_bar == r0``.
    """
    return alpha_min + (alpha_max - alpha_min) * logistic((r0 - r_bar) / tau)


def warp_polar(r, theta, alpha):
    """Apply ``r' = r ** alpha`` and return the warped Cartesian coordinates.

    Parameters
    ----------
    r, theta : array-like
        Ranges (metres) and angles (radians) of the returns.
    alpha : float
        Warp exponent. ``alpha == 1`` reproduces the unwarped coordinates.

    Returns
    -------
    numpy.ndarray of shape (n, 2)
        Warped ``(x, y)`` coordinates.
    """
    r = np.asarray(r, dtype=float)
    theta = np.asarray(theta, dtype=float)
    r_warped = np.power(r, alpha)
    x = r_warped * np.cos(theta)
    y = r_warped * np.sin(theta)
    return np.column_stack([x, y])
