# Binning reference

The binning types available in YAML are dispatched through
`AbstractBinning.construct_from(config)` and selected by the `type:` field.

## `RectangularBinning`

A multi-dimensional rectangular grid. Currently the only fully supported binning.

```yaml
binning:
  type: RectangularBinning
  bin_vars_edges:
    - ["log10_reco_energy", "linear", [2, 7, 31]]   # linspace(2, 7, 31)
    - ["cos_reco_zenith",   "linear", [-1, 0, 25]]
    - ["psi_deg",           "array",  [0, 1, 3, 10, 30]]   # custom edges
```

Each entry of `bin_vars_edges` is `[variable_name, edge_type, edges]`:

- `linear`: `edges` is `[start, stop, num]`, expanded with `jax.numpy.linspace`.
- `array`: `edges` is the literal list of bin edges.

Internals:

- `binning.required_variables` returns the list of `variable_name`s.
- `binning.hist_dims` returns the tuple of bin counts (one per dimension).
- Bin indices are cached per dataset key, so repeated `analysis.evaluate(...)` calls don't
  re-compute them. Use `binning.clear_bin_indices(ds_key)` if you swap a dataset out in place.

## `RectangularBinning2DTo3D`

Specialization of `RectangularBinning` that takes 2D binning variables and inflates the resulting
histogram to a 3D one by repeating along a third axis. Useful for comparing to a 3D template when
the events themselves don't carry that third dimension.

Constructed in Python (no shorthand YAML dispatch yet):

```python
from pyForwardFolding.binning import RectangularBinning2DTo3D
import jax.numpy as jnp

binning = RectangularBinning2DTo3D(
    bin_variables=("log10_reco_energy", "cos_reco_zenith"),
    bin_edges=(jnp.linspace(2, 7, 31), jnp.linspace(-1, 0, 25)),
    bin_edges_3d=jnp.linspace(0, 1, 11),
)
```

## `RelaxedBinning`

Differentiable, soft-edged 1D binning using a tanh kernel:

$$
K(x; a, b) = \tfrac{1}{2}\left[1 + \tanh\!\tfrac{x-a}{s}\,\tanh\!\tfrac{-(x-b)}{s}\right].
$$

```yaml
binning:
  type: RelaxedBinning
  bin_variable: log10_reco_energy
  bin_edges: [2, 7, 31]    # linspace args
  slope: 0.1
```

!!! warning
    `RelaxedBinning` is wired into `AbstractBinning.construct_from`, but its constructor currently
    raises `NotImplementedError`. Treat it as experimental.
