# Run a fit

## Setup

Start from an `Analysis`, a parameter seed dict, and a list of priors — as produced by
`pyFF.config.analysis_from_config(...)` and `pyFF.config.params_from_config(...)`.

```python
ana   = pyFF.config.analysis_from_config("config.yaml")
params, priors = pyFF.config.params_from_config("config.yaml")

llh   = pyFF.likelihood.PoissonLikelihood(ana, priors)
mini  = pyFF.minimizer.ScipyMinimizer(llh, tol=1e-10)
```

For limited-MC analyses use `SAYLikelihood`; for Minuit's covariance use `MinuitMinimizer`.

## Best-fit on real data

```python
observed = {"det1": observed_counts_2d}          # one entry per BinnedExpectation
result, best_fit, fmin = mini.minimize(observed, data)
print(best_fit)
```

`result` is the underlying optimiser object (scipy `OptimizeResult` or iMinuit info dict),
`best_fit` is the dict of best-fit parameter values, and `fmin` is the **negative** log-likelihood
at the minimum.

## Profile likelihood scan

```python
import numpy as np

xs = np.linspace(0, 3, 21)
ts = []
for x in xs:
    _, _, fmin = mini.minimize(observed, data, fixed_pars={"astro_norm": x})
    ts.append(fmin)
ts = 2 * (np.asarray(ts) - np.min(ts))    # −2 Δ log L
```

`fixed_pars` accepts an arbitrary dict and pins those parameters during minimisation. All
remaining parameters are still profiled (re-minimised at each scan point).

## Asimov fit

To get the best-fit point for the (un-fluctuated) prediction itself — useful for sanity checks and
for asymptotic sensitivity estimates — use the prediction as observed data:

```python
asimov, _ = ana.evaluate(data, params)             # one expectation dict
_, best_fit, _ = mini.minimize(asimov, data)
assert all(abs(best_fit[k] - params[k]) < 1e-6 for k in params)
```

## Using Minuit instead

```python
mini = pyFF.minimizer.MinuitMinimizer(llh, tol=1e-2, strategy=1, simplex_prefit=True)
info, best_fit, fmin = mini.minimize(observed, data)
print(info["hess_inv"])                  # iMinuit covariance
print(info["success"], info["message"])  # MIGRAD diagnostics
```

`simplex_prefit=True` runs `simplex()` before `migrad()`; useful for difficult starting points.

## Fisher-information sensitivity (no fitting required)

For quick sensitivity studies you can skip the fit and use the Fisher-information matrix
evaluated at the seed:

```python
fim = ana.fisher_information(data, params)              # per-expectation matrices
cov = ana.covariance(data, params)                       # {"total": ..., "det1": ...}
var = ana.variance(data, params)                         # {"total": {param: σ², ...}, ...}
```

This uses `jax.jacfwd` and the Poisson Fisher formula $I_{ij} = \sum_k \partial_i \mu_k \partial_j \mu_k / \mu_k$.
