# Histograms

The `histograms:` section is a list of [`BinnedExpectation`](../reference/api/binned_expectation.md)
definitions. Together they form the `Analysis`.

## Anatomy

```yaml
histograms:
  - name: det1                            # Used as the dict key in Analysis.expectations
    binning:                              # → AbstractBinning.construct_from(...)
      type: RectangularBinning
      bin_vars_edges:
        - ["log10_reco_energy", "linear", [2, 7, 31]]
        - ["cos_reco_zenith",   "linear", [-1, 0, 25]]
    lifetime: 315600000                   # Seconds. Multiplied into the histogram.
    models:                               # List of [model_name, dataset_key] pairs
      - ["model", "dataset"]
    hist_factors:                         # Optional. List of binned factors.
      - name: snowstorm_grad
        type: SnowStormGradient
        parameters: ["ice_absorption", "dom_efficiency"]
        gradient_names: ["abs", "qeff"]
        default: [1.0, 1.0]
        split_values: [1.0, 1.0]
        gradient_pickle: "gradients/snowstorm_ic86.pkl"
```

### `binning`

Dispatched through `AbstractBinning.construct_from`. The available `type:` values are documented in
[Binning reference](../reference/binnings.md). For `RectangularBinning`, each `bin_vars_edges`
entry is `[variable_name, edge_type, edges]` with `edge_type` either `"linear"` (then `edges` is
`[start, stop, num]`) or `"array"` (then `edges` is the literal list).

### `lifetime`

Multiplicative factor applied to the histogram (and squared into the per-bin
sum-of-squared-weights). The conventional choice is seconds, so a per-event rate in Hz becomes a
count.

### `models`

A list of `[model_name, dataset_key]` pairs (note the order — model first, dataset second). The
**dataset key** is the top-level key of the dict you pass to `analysis.evaluate(datasets, ...)`,
and the dataset must contain (a) every `required_variables` of the chosen model and (b) every
variable the binning needs.

Multi-detector example:

```yaml
- name: combined
  binning: ...
  models:
    - ["model", "ic86_tracks"]
    - ["model", "ic86_cascades"]
```

### `hist_factors` (optional)

Binned factors (subclasses of `AbstractBinnedFactor`) added to the histogram after the per-event
prediction. They are dispatched through `AbstractBinnedFactor.construct_from` and currently include
`SnowStormGradient`, `ScaledTemplate`, `PerBinPolynomial`. See the
[Factor reference → Binned factors](../reference/factors.md#binned-factors) for their YAML keys.

## What the Analysis ends up as

```python
ana.expectations            # OrderedDict[name, BinnedExpectation]
ana["det1"].lifetime        # 315600000
ana["det1"].binning         # the RectangularBinning instance
ana["det1"].models          # [the_model_object]
ana["det1"].binned_factors  # [SnowStormGradient(...), ...] or []
```

The `Analysis` object has a rich `__repr__` and Jupyter `_repr_markdown_`, so simply printing it (or
displaying it in a notebook) gives you a full structural breakdown — useful for sanity-checking a
config.
