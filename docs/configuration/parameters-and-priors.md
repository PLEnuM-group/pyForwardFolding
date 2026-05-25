# Parameters and priors

These sections feed the [`params_from_config`](../reference/api/config.md) loader, which produces
the parameter-seed dictionary used by `analysis.evaluate(...)` and the list of priors used by the
likelihood.

## `model_parameters`

A dict mapping **exposed parameter names** (the names you established through `param_mapping` in
the factors section) to default values. These are the values used when you evaluate the analysis
without fitting (e.g. to draw the prediction at the seed).

```yaml
model_parameters:
  astro_norm: 1.44
  astro_index: 2.0
  atmo_norm: 1.0
```

## `prior_bounds` and `prior_seeds`

Parameters listed here are wrapped in a [`UniformPrior`](../reference/api/likelihood.md) — i.e. they
contribute nothing to the log-likelihood but provide bounds and seeds to the minimizer. This is the
default for any parameter of interest you want to leave un-pulled.

```yaml
prior_bounds:
  astro_norm:  [0.0, .inf]
  astro_index: [-.inf, .inf]
  atmo_norm:   [0.0, .inf]

prior_seeds:
  astro_norm: 1.44
  astro_index: 2.0
  atmo_norm: 1.0
```

`.inf` is the YAML 1.1 spelling that `pyyaml` parses as a float infinity. Use `-.inf` for negative
infinity.

## `prior_*_gauss` (optional)

For parameters you want to pull toward a nominal value with a Gaussian penalty, add the parallel
`_gauss` sections. The loader will then construct an additional
[`GaussianUnivariatePrior`](../reference/api/likelihood.md).

```yaml
prior_bounds_gauss:
  kaon_pion_ratio: [0.0, 1.0]
  ice_absorption:  [0.5, 1.5]

prior_params_gauss:
  kaon_pion_ratio: [0.213, 0.05]      # (mean, sigma)
  ice_absorption:  [1.0,   0.10]

prior_seeds_gauss:
  kaon_pion_ratio: 0.213
  ice_absorption:  1.0
```

## What `params_from_config` returns

```python
params, priors = pyFF.config.params_from_config("config.yaml")
# params: {"astro_norm": 1.44, "astro_index": 2.0, "atmo_norm": 1.0}
# priors: [UniformPrior(...), GaussianUnivariatePrior(...)]   # if _gauss section present
#         [UniformPrior(...)]                                  # otherwise
```

The full set of exposed parameters **must** be covered by the union of all priors — otherwise the
likelihood constructor will raise `ValueError`. So:

- Every free parameter that should appear in the fit needs an entry in either
  `prior_bounds`/`prior_seeds` (uniform) **or** in the `_gauss` triple.
- A parameter can appear in both — `UniformPrior` then provides the bounds, and the Gaussian prior
  adds the pull on top.
