# Build an analysis from a YAML config

This is the recommended way to set up an analysis: keep the structural description in YAML, keep
the dataset construction in Python.

## Minimal recipe

```python
import pyForwardFolding as pyFF

ana    = pyFF.config.analysis_from_config("path/to/config.yaml")
params, priors = pyFF.config.params_from_config("path/to/config.yaml")
```

`ana` is ready to evaluate; `params` is a dict of seed values; `priors` is a list of prior objects.

## Inspecting what you built

`Analysis` and all its sub-objects have rich `__repr__` and `_repr_markdown_` implementations:

```python
print(ana)                       # plain-text tree of expectations → models → components → factors
ana                              # in Jupyter: rendered as markdown
ana.required_variables           # set of dataset keys you must provide
ana.exposed_parameters           # set of parameter names the fit will see
```

For a graphical view (requires `networkx` and optionally `pygraphviz`):

```python
fig = ana.render_graph(figsize=(14, 10), layout="hierarchical")
```

## Common pitfalls

**ValueError: Mismatch between exposed parameters and prior variables**
Every parameter exposed by the analysis must appear in some prior. The fix is usually either
(a) add the missing parameter to `prior_seeds`/`prior_bounds` in the YAML, or (b) `fix` it in the
relevant factor's `param_mapping` if you don't want it in the fit.

**ValueError: Baseline weight '...' not found in input variables**
The `baseline_weight:` keyword in `models:` refers to a key your dataset must contain. Check the
spelling against your dataset dict.

**Unknown factor type: ...**
The `type:` field must match a key in `pyForwardFolding.factor.FACTORSTR_CLASS_MAPPING`. List the
available ones from a Python prompt:

```python
from pyForwardFolding.factor import FACTORSTR_CLASS_MAPPING
print(list(FACTORSTR_CLASS_MAPPING))
```

## Building the dataset

Two options:

1. **Build it in Python** (most common). Just provide a `dict[str, dict[str, jax.Array]]` matching
   what `ana.required_variables` requests.
2. **Use the YAML loader** by adding a `datasets:` section and calling
   `pyFF.config.dataset_from_config("config.yaml")` — see [Configuration → Datasets](../configuration/datasets.md).

## Building an analysis in Python instead

For programmatic use (e.g. inside tests, or when generating configurations) you can skip YAML
entirely and assemble the objects yourself:

```python
from pyForwardFolding.factor import PowerLawFlux
from pyForwardFolding.model_component import ModelComponent
from pyForwardFolding.model import Model
from pyForwardFolding.binning import RectangularBinning
from pyForwardFolding.binned_expectation import BinnedExpectation
from pyForwardFolding.analysis import Analysis
import jax.numpy as jnp

astro = PowerLawFlux("powerlaw", pivot_energy=1e5, baseline_norm=1e-18,
                      param_mapping={"flux_norm": "astro_norm", "spectral_index": "astro_index"})
comp  = ModelComponent("astro", [astro])
model = Model.from_pairs("model", [("baseline_weight", comp)])

binning = RectangularBinning(
    bin_variables=("log10_reco_energy", "cos_reco_zenith"),
    bin_edges=(jnp.linspace(2, 7, 31), jnp.linspace(-1, 0, 25)),
)
exp = BinnedExpectation("det1", [("dataset", model)], binning, lifetime=3.156e8)
ana = Analysis({"det1": exp})
```
