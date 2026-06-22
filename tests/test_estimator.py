import numpy as np
from sklearn.base import clone
from sklearn.cluster import DBSCAN

from ds_dbscan import DSDBSCAN
from ds_dbscan.datasets import polar_to_xy, stack_polar
from ds_dbscan.metrics import noise_rate


def _synthetic_scan(seed=0):
    rng = np.random.default_rng(seed)
    r = rng.uniform(0.3, 10.0, size=300)
    theta = rng.uniform(-np.pi, np.pi, size=300)
    return r, theta


def test_sklearn_api_contract():
    est = DSDBSCAN()
    params = est.get_params()
    assert "eps" in params and "s_obj" in params
    cloned = clone(est)  # requires a well-behaved __init__
    assert isinstance(cloned, DSDBSCAN)


def test_fit_predict_shape_and_labels():
    r, theta = _synthetic_scan()
    labels = DSDBSCAN().fit_predict(stack_polar(r, theta))
    assert labels.shape == (r.size,)
    assert labels.dtype.kind == "i"
    assert hasattr(DSDBSCAN().fit(stack_polar(r, theta)), "labels_")


def test_reduces_to_dbscan_when_alpha_one():
    r, theta = _synthetic_scan(seed=1)
    ds = DSDBSCAN(alpha_min=1.0, alpha_max=1.0).fit(stack_polar(r, theta))
    base = DBSCAN(eps=0.12, min_samples=3).fit(polar_to_xy(r, theta))
    assert np.array_equal(ds.labels_, base.labels_)
    assert np.isclose(ds.alpha_, 1.0)


def test_records_alpha_and_transition_range():
    r, theta = _synthetic_scan()
    ds = DSDBSCAN().fit(stack_polar(r, theta))
    assert 0.30 <= ds.alpha_ <= 0.70
    assert ds.transition_range_ > 0


def test_warp_does_not_increase_noise_on_farfield_scan():
    # a far wall sampled at a coarse step: returns spread apart with range
    theta = np.radians(np.arange(0, 60, 2.0))
    r = np.full_like(theta, 9.0)
    X_polar = stack_polar(r, theta)
    ds_noise = noise_rate(DSDBSCAN(delta_theta=np.radians(2.0)).fit_predict(X_polar))
    base_noise = noise_rate(DBSCAN(eps=0.12, min_samples=3).fit_predict(polar_to_xy(r, theta)))
    assert ds_noise <= base_noise


def test_rejects_bad_input_shape():
    bad = np.zeros((10, 3))
    try:
        DSDBSCAN().fit(bad)
    except ValueError:
        return
    raise AssertionError("expected ValueError for X with 3 columns")
