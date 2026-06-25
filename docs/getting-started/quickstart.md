# Quickstart

This page walks through a minimal end-to-end analysis: build a toy Monte Carlo dataset, configure a
two-component model (astrophysical + atmospheric) from YAML, predict histograms, and fit.

The full notebook this is adapted from lives at
[`examples/toy_example_w_config.ipynb`](https://github.com/chrhck/pyForwardFolding/blob/develop/examples/toy_example_w_config.ipynb)
and the YAML config at
[`examples/test.yaml`](https://github.com/chrhck/pyForwardFolding/blob/develop/examples/test.yaml).

## 1. Generate (or load) Monte Carlo data

pyForwardFolding consumes per-event Monte Carlo. Each event needs:

- True quantities used by your model factors (here: `true_energy`, `true_zenith`).
- Reconstructed quantities used by your binning (here: `log10_reco_energy`, `cos_reco_zenith`).
- A baseline weight (here: `baseline_weight`) — typically the inverse generation probability
  multiplied by any per-event normalization that you don't want to refit.

```python
import numpy as np
import jax.numpy as jnp
import pyForwardFolding as pyFF

n = int(5e6)
event_energies = 10 ** np.random.uniform(2, 8, size=n)
event_zenith   = np.arccos(np.random.uniform(-1, 1, size=n))

reco_energy = 10 ** (np.log10(event_energies) + np.random.normal(0, 0.2, size=n))
reco_zenith = np.arccos(
    np.clip(np.cos(event_zenith) + np.random.normal(0, 0.05, size=n), -1, 1)
)
baseline_weights = event_energies * np.log(10) * 6 / n * 1e5

data = {
    "dataset": {
        "log10_reco_energy": jnp.log10(jnp.asarray(reco_energy)),
        "cos_reco_zenith":  jnp.cos(jnp.asarray(reco_zenith)),
        "baseline_weight":  jnp.asarray(baseline_weights),
        "true_energy":      jnp.asarray(event_energies),
        "true_zenith":      jnp.asarray(event_zenith),
    }
}
```

The top-level key `"dataset"` is the **dataset key** that the YAML config will refer to.

## 2. Define the analysis in YAML

Save the following as `test.yaml`. It declares two factors (an astrophysical power-law flux and an
atmospheric Gaisser-shape × power-law flux), groups them into two components (`astro`, `atmo`),
combines them into one model, and bins the prediction in a 30 × 24 (`log10_reco_energy`,
`cos_reco_zenith`) histogram:

```yaml
factors:
  - name: "powerlaw"
    type: "PowerLawFlux"
    pivot_energy: 1.0e5
    baseline_norm: 1.0e-18
    param_mapping:
      flux_norm: "astro_norm"
      spectral_index: "astro_index"
  - name: "atmo_powerlaw"
    type: "PowerLawFlux"
    pivot_energy: 1.0
    baseline_norm: 0.000014
    param_mapping:
      flux_norm: "atmo_norm"
      spectral_index: 2.7        # fixed (numeric value, not a string)
  - name: "atmo_zenith"
    type: "GaisserZenithFactor"
    pivot_energy: 1.0e5
    baseline_norm: 1.0e-18
    param_mapping:
      kaon_pion_ratio: 0.213     # fixed

components:
  - name: "astro"
    factors: ["powerlaw"]
  - name: "atmo"
    factors: ["atmo_powerlaw", "atmo_zenith"]

models:
  - name: "model"
    components:
      - { name: "astro", baseline_weight: "baseline_weight" }
      - { name: "atmo",  baseline_weight: "baseline_weight" }

histograms:
  - name: det1
    binning:
      type: RectangularBinning
      bin_vars_edges:
        - ["log10_reco_energy", "linear", [2, 7, 31]]
        - ["cos_reco_zenith",   "linear", [-1, 0, 25]]
    lifetime: 315600000           # 10 years in seconds
    models: [["model", "dataset"]]

model_parameters:
  astro_norm: 1.44
  astro_index: 2.0
  atmo_norm: 1.0

prior_bounds:
  astro_norm:  [0.0, .inf]
  astro_index: [-.inf, .inf]
  atmo_norm:   [0.0, .inf]

prior_seeds:
  astro_norm: 1.44
  astro_index: 2.0
  atmo_norm: 1.0
```

A line-by-line walkthrough of every section lives at
[Configuration → Overview](../configuration/overview.md).

## 3. Build the analysis

```python
ana    = pyFF.config.analysis_from_config("test.yaml")
params, priors = pyFF.config.params_from_config("test.yaml")
print(ana)              # rich textual / markdown summary
```

`ana` is an [`Analysis`](../reference/api/analysis.md) — a container of one or more
[`BinnedExpectation`](../reference/api/binned_expectation.md) objects. `params` is a dict of
parameter seeds and `priors` is a list of prior objects ready to pass to a likelihood.

## 4. Predict histograms

```python
predicted, predicted_ssq = ana.evaluate(data, params)
# predicted["det1"] is a (30, 24) JAX array — counts per (E, cosθ) bin
```

To get the prediction broken down per model component (e.g. `astro` vs. `atmo`):

```python
per_comp, _ = ana.evaluate_per_component(data, params)
per_comp["det1"]["astro"]   # only the astrophysical contribution
per_comp["det1"]["atmo"]    # only the atmospheric contribution
```

## 5. Fit

```python
llh  = pyFF.likelihood.PoissonLikelihood(ana, priors)
mini = pyFF.minimizer.ScipyMinimizer(llh)

# Treat the prediction itself as observed data ("Asimov fit")
result, best_fit, fmin = mini.minimize(predicted, data)
print(best_fit)   # should recover params (no statistical fluctuation)
```

For a real fit, replace `predicted` with the observed counts dict
(`{"det1": observed_counts_2d}`). For a Poisson pseudo-experiment, use
[`Hypothesis.generate_pseudo_experiments`](../reference/api/statistics.md).

## 6. Scan a parameter

```python
import numpy as np

norms = np.linspace(0, 3, 11)
ts = []
for x in norms:
    _, _, fmin = mini.minimize(predicted, data, fixed_pars={"astro_norm": x})
    ts.append(fmin)
ts = 2 * (np.asarray(ts) - np.min(ts))   # −2 Δlog L profile
```

## What's next

- Read [Concepts → Overview](../concepts/overview.md) for the math behind factors, components, and binning.
- See the [Configuration reference](../configuration/overview.md) for every key the YAML schema accepts.
- See the [Factor reference](../reference/factors.md) for the parameters and required variables of
  every available factor.
