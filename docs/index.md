# pyForwardFolding

!!! warning "AI-generated documentation — provisional"
    This documentation site was drafted by an AI assistant by reading the source code. It is a
    **first pass** and will be reviewed and rewritten by a human maintainer at a later date.
    Individual claims may be wrong, incomplete, or out of date — when in doubt, **cross-check
    against the source** under `pyForwardFolding/` and the examples under `examples/`.

**pyForwardFolding** is a JAX-based Python framework for forward-folding analyses of binned data,
originally developed for neutrino-telescope physics but applicable to any analysis that builds a
predicted histogram from weighted Monte Carlo events and fits it to data.

It provides:

- A compositional model description: **factors** combine into **components**, which combine into **models**.
- A **binning** layer that turns weighted per-event predictions into histograms.
- A YAML-driven **configuration system** so analyses can be defined declaratively, without writing Python.
- Built-in **likelihoods** (Poisson and SAY) with **Gaussian / uniform priors**.
- **Minimizers** (SciPy L-BFGS-B and iMinuit) and a **statistics** module for hypothesis tests,
  pseudo-experiments, Asimov fits, discovery potential, and parameter scans.
- A **JAX backend** so the full forward model is differentiable and JIT-compilable.

## At a glance

```python
import pyForwardFolding as pyFF

# 1. Build the analysis from a YAML config
ana = pyFF.config.analysis_from_config("test.yaml")
params, priors = pyFF.config.params_from_config("test.yaml")

# 2. Evaluate the predicted histograms for some data
predicted, _ = ana.evaluate(data, params)

# 3. Fit
llh   = pyFF.likelihood.PoissonLikelihood(ana, priors)
mini  = pyFF.minimizer.ScipyMinimizer(llh)
result, best_fit, fmin = mini.minimize(observed, data)
```

## Where to go next

- New to the framework? Start with [Getting started → Installation](getting-started/installation.md)
  and the [Quickstart](getting-started/quickstart.md).
- Want to understand the math and class structure? Read [Concepts → Overview](concepts/overview.md).
- Looking up what a particular factor does? See the [Factor reference](reference/factors.md) —
  every factor is documented with its required input variables and exposed parameters.
- Writing your first YAML config? Jump to [Configuration → Overview](configuration/overview.md).

## Project layout

```text
pyForwardFolding/
├── pyForwardFolding/      # the library
│   ├── factor.py          # all per-event and per-bin Factor classes
│   ├── model_component.py # ModelComponent: product of factors
│   ├── model.py           # Model: sum of components
│   ├── binning.py         # AbstractBinning, RectangularBinning, ...
│   ├── binned_expectation.py
│   ├── analysis.py        # Combines binned expectations
│   ├── likelihood.py      # PoissonLikelihood, SAYLikelihood, priors
│   ├── minimizer.py       # ScipyMinimizer, MinuitMinimizer
│   ├── statistics.py      # Hypothesis, HypothesisTest, pseudo-experiments
│   ├── config.py          # YAML → Analysis / dataset / parameters
│   ├── backend.py         # JAX backend abstraction
│   └── clustering.py      # Event clustering utilities
├── examples/              # Worked examples (notebooks + YAML)
└── tests/
```
