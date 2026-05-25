# Factors section

Every entry under `factors:` becomes one `AbstractUnbinnedFactor` instance, identified by `name`.
Other YAML sections refer to factors by these names.

## Common keys

Every factor entry has at least:

```yaml
- name: <unique string>      # Identifier; referenced from components.factors
  type: <FactorClassName>    # Must match a key in FACTORSTR_CLASS_MAPPING
  param_mapping:             # Optional. Rename or fix individual parameters.
    <internal_param>: <new_name_or_numeric_value>
  ...                        # Factor-specific keys (pivot_energy, baseline_norm, ...)
```

The available `type` values map directly to factor classes. The full list is in the
[Factor reference](../reference/factors.md); the most common ones are:

| `type:`                       | Models                                      |
| ----------------------------- | ------------------------------------------- |
| `PowerLawFlux`                | Spectral shape ∝ E^(−γ)                    |
| `BrokenPowerLawFlux`          | Power law with a spectral break at logEbreak |
| `FluxNorm`                    | Pure scalar normalization                   |
| `GaisserZenithFactor`         | Atmospheric pi/K zenith bracket             |
| `FlavorRatio`                 | Per-flavor rescaling (uses true_type)       |
| `GalacticPlaneBox` / `SegmentedPlane` | Galactic-plane selectors            |
| `VetoThreshold` / `FixedVeto` | Atmospheric self-veto reweighting           |
| `DeltaGamma`                  | Spectral-index nuisance pull                |
| `ModelInterpolator`           | Smooth interpolation between two MC models   |
| `GradientReweight` / `ClassifierGradientReweight` | Per-event gradient reweighting |
| `SnowstormGauss`              | Gaussian reweighting for systematics        |
| `SoftCut`                     | Differentiable sigmoid cut                  |

## `param_mapping`

This is how you bridge **factor-internal parameter names** to **globally exposed parameter names**
and how you fix parameters at compile time.

```yaml
param_mapping:
  flux_norm: "astro_norm"   # rename: exposed as astro_norm in the fit
  spectral_index: 2.7       # fix: held at 2.7, not in the fit
```

| Value type                   | Meaning                                                     |
| ---------------------------- | ----------------------------------------------------------- |
| String                       | Rename to that name                                         |
| Int / float (not bool)       | Fix at that value, drop from the free parameters            |
| Key not listed               | Identity — exposed under its internal name                  |
| `param_mapping` omitted      | All parameters exposed under their internal names           |

> **Tip:** when two factors share the same internal parameter (e.g. two `PowerLawFlux`'s both have
> `flux_norm`), use `param_mapping` to give them distinct exposed names. Otherwise they'll
> *intentionally* share the same fit parameter, which is occasionally what you want but usually
> isn't.

## Examples

A bare `PowerLawFlux`, exposing the natural parameter names:

```yaml
- name: "astro"
  type: "PowerLawFlux"
  pivot_energy: 1.0e5
  baseline_norm: 1.0e-18
  # no param_mapping → flux_norm and spectral_index are exposed under those names
```

A `PowerLawFlux` with both parameters renamed and a `FluxNorm` reusing the same fit parameter:

```yaml
- name: "atmo_shape"
  type: "PowerLawFlux"
  pivot_energy: 1.0
  baseline_norm: 1.4e-5
  param_mapping:
    flux_norm: "atmo_norm"
    spectral_index: "atmo_index"

- name: "atmo_scale"
  type: "FluxNorm"
  param_mapping:
    flux_norm: "atmo_norm"     # same name → same parameter at fit time
```

A `GaisserZenithFactor` fixing the K/π ratio at the canonical value:

```yaml
- name: "atmo_zenith"
  type: "GaisserZenithFactor"
  pivot_energy: 1.0e5
  epsilon_pi: 115.0
  epsilon_K:  850.0
  param_mapping:
    kaon_pion_ratio: 0.213
```

For every factor's full set of constructor keys, see the
[Factor reference](../reference/factors.md).
