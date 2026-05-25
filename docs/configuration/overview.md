# Configuration overview

pyForwardFolding analyses are described in a single YAML file that the
[`pyForwardFolding.config`](../reference/api/config.md) module compiles into an
[`Analysis`](../reference/api/analysis.md), a parameter-seed dict, and a list of priors.

The full reference example used throughout these pages is
[`examples/test.yaml`](https://github.com/chrhck/pyForwardFolding/blob/develop/examples/test.yaml).

## Top-level structure

```yaml
factors:        # Per-event multiplicative factors  → AbstractUnbinnedFactor instances
components:     # Products of factors               → ModelComponent
models:         # Sums of components with baseline weights → Model
histograms:     # Binning + lifetime + dataset-model pairing + optional binned factors → BinnedExpectation
                # An Analysis is the dict of named histograms.

model_parameters:      # Seed values used when evaluating the analysis without fitting
prior_bounds:          # Bounds for UniformPrior parameters
prior_seeds:           # Seeds for UniformPrior parameters

# Optional — only required if you want Gaussian priors on some parameters
prior_bounds_gauss:    # Bounds for parameters that also get a Gaussian pull
prior_params_gauss:    # (mean, std) for each Gaussian-pulled parameter
prior_seeds_gauss:     # Seeds for Gaussian-pulled parameters

# Optional — only required if you want to build the dataset from disk via the loader
datasets:              # Mapping of dataset name → DataFrame file + column transforms
```

## Loader entry points

```python
import pyForwardFolding as pyFF

ana                       = pyFF.config.analysis_from_config("config.yaml")
params, priors            = pyFF.config.params_from_config("config.yaml")
data                      = pyFF.config.dataset_from_config("config.yaml")   # optional
models_per_histogram_dset = pyFF.config.models_from_config("config.yaml")    # advanced
```

All four accept either a path (`str`) or an already-loaded `dict`.

## Build order

```text
factors   ──▶  components   ──▶  models   ──▶  histograms (BinnedExpectation)   ──▶  Analysis
parameters ───┐
priors    ────┴──▶ Likelihood ──▶ Minimizer / Hypothesis / HypothesisTest
datasets  ────────▶ evaluation
```

The loaders enforce this order, so the YAML sections can appear in any order in the file as long
as cross-references resolve.

## Walkthrough sections

- [Factors](factors.md) — every factor type, its YAML keys, and what they mean.
- [Components & models](components-and-models.md) — bundling factors and assigning baseline weights.
- [Histograms](histograms.md) — binning, lifetime, dataset binding, binned factors.
- [Parameters & priors](parameters-and-priors.md) — seeds, bounds, uniform vs. Gaussian.
- [Datasets](datasets.md) — letting the loader build datasets from on-disk DataFrames.
