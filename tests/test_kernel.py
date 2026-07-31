import numpy as np

from ds_dbscan.kernel import logistic, schedule_alpha, transition_range, warp_polar


def test_identity_warp_when_alpha_is_one():
    rng = np.random.default_rng(0)
    r = rng.uniform(0.2, 12.0, size=200)
    theta = rng.uniform(-np.pi, np.pi, size=200)
    warped = warp_polar(r, theta, alpha=1.0)
    expected = np.column_stack([r * np.cos(theta), r * np.sin(theta)])
    assert np.allclose(warped, expected)


def test_schedule_is_bounded():
    alpha_min, alpha_max = 0.30, 0.70
    for r_bar in np.linspace(0.1, 20.0, 50):
        a = schedule_alpha(r_bar, r0=3.0, alpha_min=alpha_min,
                           alpha_max=alpha_max, tau=1.5)
        assert alpha_min <= a <= alpha_max


def test_schedule_midpoint_at_transition():
    a = schedule_alpha(r_bar=3.0, r0=3.0, alpha_min=0.30, alpha_max=0.70, tau=1.5)
    assert np.isclose(a, 0.50)


def test_transition_range_formula():
    # r0 = s_obj / (min_samples * delta_theta)
    r0 = transition_range(s_obj=0.06, min_samples=3, delta_theta=np.radians(1.34))
    assert np.isclose(r0, 0.06 / (3 * np.radians(1.34)))
    assert 0.8 < r0 < 0.9  # matches the value reported for the real moving data


def test_warp_pulls_far_field_inward():
    # for alpha < 1, returns beyond 1 m move inward, returns inside 1 m move outward
    r = np.array([0.5, 1.0, 4.0, 12.0])
    theta = np.zeros_like(r)
    xy = warp_polar(r, theta, alpha=0.4)
    r_warped = np.hypot(xy[:, 0], xy[:, 1])
    assert r_warped[2] < r[2] and r_warped[3] < r[3]
    assert np.isclose(r_warped[1], 1.0)
    assert r_warped[0] > r[0]


def test_logistic_range():
    z = np.linspace(-10, 10, 100)
    s = logistic(z)
    assert np.all((s > 0) & (s < 1))
