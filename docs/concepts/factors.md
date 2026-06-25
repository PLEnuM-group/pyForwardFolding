# Factors

A **factor** is the smallest building block of a model. It takes a dictionary of per-event input
variables and a dictionary of parameter values, and returns a per-event multiplicative weight.

## The two kinds of factor

```text
AbstractFactor
├── AbstractUnbinnedFactor   ← operates on per-event MC, returns a per-event array
└── AbstractBinnedFactor     ← evaluated after histogramming, returns a per-bin (mean, variance) tuple
```

**Unbinned factors** (the vast majority) are what you compose inside a `ModelComponent`. They are
multiplied together to produce the per-event component weight.

**Binned factors** (e.g. `SnowStormGradient`, `ScaledTemplate`, `PerBinPolynomial`) live on the
`BinnedExpectation` and are added to the histogram after it has been built. They typically
parametrize a per-bin systematic correction that is expensive to evaluate per event but cheap to
evaluate per bin.

## Anatomy of a factor

Every concrete factor class exposes two key attributes:

- `factor_parameters: List[str]` — the internal names of the parameters it consumes.
- `required_variables: List[str]` — the keys it expects to find in the input variable dictionary.

For example, `PowerLawFlux` declares:

```python
self.factor_parameters = ["flux_norm", "spectral_index"]
self.req_vars = ["true_energy"]
```

When evaluated, it pulls `true_energy` from the dataset and `flux_norm` / `spectral_index` from the
parameter dict (after applying any rename from `param_mapping`), and returns

$$
F = \text{flux\_norm} \cdot \text{baseline\_norm} \cdot \left(\tfrac{E}{E_{\text{pivot}}}\right)^{-\gamma}.
$$

## Parameter renaming and fixing

`param_mapping` is the bridge between **factor-internal parameter names** (which the factor's
mathematics uses) and **globally exposed parameter names** (which appear in the fit).

```yaml
- name: "powerlaw_astro"
  type: "PowerLawFlux"
  pivot_energy: 1.0e5
  baseline_norm: 1.0e-18
  param_mapping:
    flux_norm: "astro_norm"     # rename → exposed as astro_norm
    spectral_index: "astro_idx" # rename → exposed as astro_idx

- name: "powerlaw_atmo"
  type: "PowerLawFlux"
  pivot_energy: 1.0
  baseline_norm: 1.4e-5
  param_mapping:
    flux_norm: "atmo_norm"      # different exposed name
    spectral_index: 2.7         # numeric → fixed, not in the fit
```

Rules:

| Value type in `param_mapping` | Effect                                                                |
| ----------------------------- | --------------------------------------------------------------------- |
| `str`                         | Rename — parameter is exposed under the given name                    |
| `int` / `float` (not `bool`)  | Fix — parameter is held at this constant and not exposed              |
| (key not listed)              | Identity — parameter is exposed under its factor-internal name        |
| `param_mapping=None`          | All parameters are exposed under their factor-internal names          |

This is why two `PowerLawFlux` factors can coexist in the same model: just give them different
`param_mapping` values.

## Composition

Inside a `ModelComponent`, factors are **multiplied** in evaluation order:

```python
component_weight_i = ∏_f F_f(X_i, θ_f)
```

That means order doesn't matter mathematically, but giving factors meaningful names helps with
debugging and with reading the `repr_markdown()` output.

Inside a `Model`, components are **summed**, each multiplied by its **baseline weight**
(the inverse-generation weight column of your MC):

```python
event_weight_i = w_i · Σ_C m_C(X_i, θ_C)
```

where the baseline weight column is named per component, so you could in principle give different
components different baseline weights (e.g. `astro_baseline_weight` vs. `atmo_baseline_weight`)
for samples generated under different assumptions.

## Built-in factors at a glance

The full catalogue lives at [Factor reference](../reference/factors.md). At time of writing the
library ships:

- **Fluxes:** `PowerLawFlux`, `BrokenPowerLawFlux`, `FluxNorm`, `FlavorRatio`
- **Atmospheric shape:** `GaisserZenithFactor`
- **Galactic plane:** `GalacticPlaneBox`, `SegmentedPlane`
- **Atmospheric self-veto:** `VetoThreshold`, `FixedVeto`
- **Reweighting / interpolation:** `DeltaGamma`, `ModelInterpolator`, `GradientReweight`,
  `ClassifierGradientReweight`, `SnowstormGauss`
- **Cuts:** `SoftCut`
- **Binned (per-bin):** `SnowStormGradient`, `ScaledTemplate`, `PerBinPolynomial`

Adding a new factor is a small amount of code (one subclass with `evaluate`, `construct_from`, and
the two attribute lists). See [How-to → Custom factor](../how-to/custom-factor.md).
