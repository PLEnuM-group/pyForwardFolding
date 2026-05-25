# Fitting and statistics

## Minimizers

Both minimizers wrap an `AbstractLikelihood` and flatten the parameter dictionary into a vector for
the underlying optimizer.

### ScipyMinimizer (L-BFGS-B)

Default, simple, gradient-based via `scipy.optimize.minimize`. Uses JAX `value_and_grad` to provide
analytic gradients to L-BFGS-B.

```python
from pyForwardFolding.minimizer import ScipyMinimizer

mini = ScipyMinimizer(llh, tol=1e-10)
result, best_fit, fmin = mini.minimize(observed, data)
```

Pass `fixed_pars={"astro_norm": 1.5}` to hold parameters during the minimisation — this is how you
do profile-likelihood scans.

### MinuitMinimizer

Wraps [iminuit](https://iminuit.readthedocs.io). Gives you Minuit's covariance estimate and the
familiar MIGRAD output.

```python
from pyForwardFolding.minimizer import MinuitMinimizer

mini = MinuitMinimizer(llh, tol=1e-2, strategy=1, simplex_prefit=False)
info, best_fit, fmin = mini.minimize(observed, data)
print(info["hess_inv"])   # iminuit covariance
```

`info` carries `success`, `message`, `nfev`, `njev`, `hess_inv`.

## Hypotheses

A [`Hypothesis`](../reference/api/statistics.md) bundles a likelihood, a set of fixed parameters,
and a minimizer. It represents one parameter sub-space for a fit.

```python
from pyForwardFolding.statistics import Hypothesis

H0 = Hypothesis("null",  llh, fixed_pars={"astro_norm": 0.0})  # background only
H1 = Hypothesis("alt",   llh)                                  # everything free
```

`H.evaluate(observed, dataset)` runs the fit and returns the best-fit log-likelihood (with
`detailed=True` you also get the minimizer info and the best-fit parameter dict).
`H.generate_pseudo_experiments(nexp, dataset)` is a generator of Poisson-fluctuated histograms.
`H.asimov_experiment(dataset)` returns the (un-fluctuated) Asimov histogram.

## Hypothesis tests

[`HypothesisTest`](../reference/api/statistics.md) wraps two hypotheses and a dataset and provides
the standard frequentist machinery:

```python
from pyForwardFolding.statistics import HypothesisTest

test = HypothesisTest(H0, H1, dataset)
ts   = test.test(observed)                       # −2 Δlog L on one observation
null = test.null_dist(nexp=1000)                 # null TS distribution
alt  = test.alt_dist(nexp=1000)                  # alternative TS distribution
power = test.power(nexp=1000, sigma_level=3)     # P(reject H0 | H1)
```

For one-degree-of-freedom tests you also get:

- `test.discovery_potential(nexp_null, nexp_alt, sigma_level=3)` — root-finds the value of the
  free parameter at which the median TS under H1 equals the σ-threshold of the null distribution.
- `test.discovery_potential_asimov(sigma_level=3)` — same idea but using the Asimov asymptotic χ²
  shortcut (no pseudo-experiments).
- `test.scan(observed, scan_points)` — −2 Δlog L profile of the free parameter.
- `test.uncertainty(observed, sigma_level)` — symmetric ±σ uncertainty from the profile.

## Pseudo-experiments

[`PseudoExpGenerator`](../reference/api/statistics.md) evaluates the analysis once and then yields
independent Poisson-fluctuated copies of the predicted histograms.

```python
from pyForwardFolding.statistics import PseudoExpGenerator

gen = PseudoExpGenerator(ana, dataset, parameter_values)
for fake_obs in gen.generate(nexp=1000):
    ...
```

## Fisher information and covariance

`Analysis` itself can compute the Fisher information matrix (Poisson) and invert it for a
covariance / variance estimate without doing a real fit:

```python
fim = ana.fisher_information(datasets, parameter_values)   # {comp_name: matrix}
cov = ana.covariance(datasets, parameter_values)            # {"total": ..., comp_name: ...}
var = ana.variance(datasets, parameter_values)              # {comp_name: {param_name: variance}}
```

This uses `jax.jacfwd` on the per-bin expectation and is differentiable end-to-end.
