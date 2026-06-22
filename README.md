# OneDimensionKernelFunction

A project to evaluate clustering improvements for 2D LiDAR systems using kernel functions or other algorithms.

The primary lidar for this work is:  
- SLAMTEC RPLiDAR A1: https://www.slamtec.com/en/Lidar/A1/

---

Authors/Team:

- Aaron S. Crandall \<aaron.crandall@ue-germany.de>
- Hernan Vinicio Lopez Morocho \<hernan.lopez@ue-germany.de>

---

## DS-DBSCAN Python package

`ds_dbscan` provides a scikit-learn-compatible estimator that applies a
device-sensitive radial warp (`r' = r ** alpha`) before clustering a 2D LiDAR
scan with standard DBSCAN. The exponent `alpha` is derived per scan from the
median range and the sensor's angular resolution.

### Install

```bash
pip install -e .
```

### Usage

```python
import numpy as np
from ds_dbscan import DSDBSCAN

# X: columns are range r (metres) and angle theta (radians)
X = np.column_stack([r, theta])
labels = DSDBSCAN(eps=0.12, min_samples=3,
                  delta_theta=np.radians(1.0), s_obj=0.40).fit_predict(X)
```

With `alpha_min == alpha_max == 1` the warp is the identity and the result is
identical to `sklearn.cluster.DBSCAN`.

### Command line

```bash
ds-dbscan path/to/scan.csv --frame 0 --delta-theta 0.0175 --s-obj 0.40
```

### Tests

```bash
pip install -e .[test]
pytest -q
```

### Layout

- `ds_dbscan/kernel.py` — radial power warp and logistic `alpha` schedule
- `ds_dbscan/estimator.py` — `DSDBSCAN` scikit-learn estimator
- `ds_dbscan/datasets.py` — loader for recorded scan CSVs
- `ds_dbscan/metrics.py` — noise rate, cluster count, ARI
- `tests/` — unit tests run in CI (`.github/workflows/ci.yml`)

Licensed under the MIT License (see `LICENSE`).

