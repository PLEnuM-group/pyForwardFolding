# Binning

A binning is the bridge between per-event predictions and a histogram. Every
[`BinnedExpectation`](../reference/api/binned_expectation.md) owns one
[`AbstractBinning`](../reference/api/binning.md) object.

## RectangularBinning

The standard choice. An n-dimensional rectangular grid; each dimension is bound to one variable name
and has its own list of bin edges.

```python
from pyForwardFolding.binning import RectangularBinning
import jax.numpy as jnp

binning = RectangularBinning(
    bin_variables=("log10_reco_energy", "cos_reco_zenith"),
    bin_edges=(jnp.linspace(2, 7, 31), jnp.linspace(-1, 0, 25)),
)
```

In YAML:

```yaml
binning:
  type: RectangularBinning
  bin_vars_edges:
    - ["log10_reco_energy", "linear", [2, 7, 31]]   # linspace(2, 7, 31)
    - ["cos_reco_zenith",   "linear", [-1, 0, 25]]
    - ["psi_deg",           "array",  [0, 1, 3, 10, 30]]   # custom edges
```

Each entry is `[variable_name, edge_type, edges]`:

- `linear`: `edges` is `[start, stop, num]`, expanded with `linspace`.
- `array`: `edges` is the literal list of edges.

Events outside any dimension's edges are masked out and contribute zero weight.

### Bin-index caching

`RectangularBinning` caches the per-event bin indices keyed by **dataset name**, so the bin
assignment is computed once per dataset and re-used across every minimizer call. This is one of the
main reasons fits are fast. Call `binning.clear_bin_indices(ds_key)` if you swap a dataset out in
place.

## RectangularBinning2DTo3D

A specialization that takes 2D binning variables and inflates the resulting histogram to 3D by
repeating along a third axis (useful when comparing against a 3D template). The bin edges along the
third dimension are set at construction time but the events themselves are not binned in that
dimension — every event is uniformly spread across the third axis.

## RelaxedBinning

A differentiable, soft binning using a tanh kernel:

$$
K(x; a, b) = \tfrac{1}{2}\left(1 + \tanh\!\tfrac{x-a}{s}\,\tanh\!\tfrac{-(x-b)}{s}\right)
$$

This gives each event a smooth membership weight in each bin rather than a hard 0/1, which is
sometimes useful when fitting against bin boundaries that themselves depend on parameters.

> **Note:** `RelaxedBinning` is implemented in the codebase but the constructor currently raises
> `NotImplementedError`. If you need soft binning today, treat it as experimental.

## Binning vs. binned factors

It's worth separating two concepts that both end up "per bin":

1. **Binning** decides *how* an event becomes a histogram cell.
2. **Binned factors** (subclasses of `AbstractBinnedFactor`) live on a `BinnedExpectation` and are
   **added** to the resulting histogram, after the histogram is built. They are how per-bin
   detector systematics enter the model.

```text
hist = binning.build_histogram(weights × model_weights) * lifetime
     + sum( binned_factor.evaluate(...) * lifetime, over binned_factors )
```

See `PerBinPolynomial`, `SnowStormGradient`, and `ScaledTemplate` for concrete binned factors.
