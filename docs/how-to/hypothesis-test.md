# Perform a hypothesis test

The [`statistics`](../reference/api/statistics.md) module wraps the fit machinery in standard
frequentist primitives: hypotheses, null/alternative distributions, pseudo-experiments, discovery
potential, parameter scans, and uncertainties.

## Set up two hypotheses

```python
from pyForwardFolding.statistics import Hypothesis, HypothesisTest

H0 = Hypothesis("null", llh, fixed_pars={"astro_norm": 0.0})   # background-only
H1 = Hypothesis("alt",  llh)                                   # signal + background

test = HypothesisTest(H0, H1, dataset)
```

`HypothesisTest.from_likelihood(llh, dataset, fixed_params)` is a shortcut that builds H0 with the
given fixed parameters and H1 with everything free.

## Evaluate the test statistic on observed data

```python
ts = test.test(observed_data)           # −2 Δlog L
print(test.dof)                          # degrees of freedom = 1 in this example
print(test.free_parameters)              # {'astro_norm'}
```

## Null and alternative distributions

```python
ts_null = test.null_dist(nexp=1000)
ts_alt  = test.alt_dist(nexp=1000)
```

Each pseudo-experiment Poisson-fluctuates the prediction once, fits H0 and H1, and records
$-2(\log\mathcal L_{H_0} - \log\mathcal L_{H_1})$. Generation uses `Hypothesis.generate_pseudo_experiments`
internally.

## Discovery potential

Find the smallest signal strength for which the **median** alternative TS exceeds the σ-threshold
of the null distribution (only works for one degree of freedom).

```python
null, alt, x_disc = test.discovery_potential(
    nexp_null=1000,
    nexp_alt=200,
    sigma_level=3,
)
print(f"3σ discovery at astro_norm = {x_disc:.3f}")
```

Pass `null_dist=...` to reuse a previously generated null distribution. The Asimov asymptotic
shortcut (no pseudo-experiments) is

```python
x_disc_asimov = test.discovery_potential_asimov(sigma_level=3)
```

This uses the χ² quantile at the chosen σ-level instead of fluctuated pseudo-experiments and is
typically a fine starting point that you can later refine with the full Monte-Carlo flavour above.

## Profile-likelihood scan and uncertainty

```python
xs, ts_profile = test.scan(observed_data, scan_points=21)         # −2 Δlog L vs free parameter
sigma_unc       = test.uncertainty(observed_data, sigma_level=1)   # ±1σ symmetric
```

Both are one-degree-of-freedom only (i.e. exactly one free parameter that's fixed in H0).

## Power (P(reject H0 | H1))

```python
p = test.power(nexp=1000, sigma_level=3)
print(f"3σ power = {p:.2%}")
```

## Choosing the minimizer

Both hypotheses accept a `minimizer` argument; default is `ScipyMinimizer(llh)`. If you want Minuit
diagnostics in your fits:

```python
from pyForwardFolding.minimizer import MinuitMinimizer
H1 = Hypothesis("alt", llh, minimizer=MinuitMinimizer(llh, simplex_prefit=True))
```

Same minimizer is reused across pseudo-experiments, so any caching it does is preserved.
