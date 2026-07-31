"""Evaluation metrics for DS-DBSCAN clustering of 2D LiDAR scans."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import adjusted_rand_score


def noise_rate(labels):
    """Fraction of points labelled as noise (DBSCAN label ``-1``)."""
    labels = np.asarray(labels)
    if labels.size == 0:
        return 0.0
    return float(np.mean(labels == -1))


def n_clusters(labels):
    """Number of clusters found, excluding the noise label."""
    labels = np.asarray(labels)
    return int(len(set(labels.tolist()) - {-1}))


def ari(labels_true, labels_pred):
    """Adjusted Rand Index of a labelling against the ground truth."""
    return float(adjusted_rand_score(labels_true, labels_pred))
