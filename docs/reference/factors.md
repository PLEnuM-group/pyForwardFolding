# Factor reference

This page documents every factor shipped with pyForwardFolding. For each factor we list:

- The YAML `type:` value and the corresponding Python class
- Its **exposed parameters** (internal names — what `param_mapping` keys are)
- Its **required input variables** (keys the dataset must provide)
- The **constructor arguments** in YAML form
- A short summary of what it computes

`param_mapping` rules (rename via string, fix via numeric) apply to every factor — see
[Concepts → Factors](../concepts/factors.md).

The class registry is `pyForwardFolding.factor.FACTORSTR_CLASS_MAPPING`; every key below is a key in
that dict.

---

## Unbinned factors

### `PowerLawFlux`

Power-law differential flux

$$F = \Phi_0 \cdot \Phi_\text{base} \cdot \left(\tfrac{E}{E_\text{pivot}}\right)^{-\gamma}$$

| Attribute             | Value                                                    |
| --------------------- | -------------------------------------------------------- |
| Exposed parameters    | `flux_norm`, `spectral_index`                            |
| Required variables    | `true_energy`                                            |
| YAML keys             | `name`, `pivot_energy`, `baseline_norm`, optional `param_mapping` |

```yaml
- name: astro
  type: PowerLawFlux
  pivot_energy: 1.0e5
  baseline_norm: 1.0e-18
  param_mapping:
    flux_norm: astro_norm
    spectral_index: astro_index
```

---

### `BrokenPowerLawFlux`

Broken power law with a smooth pivot adjustment to keep `flux_norm` interpretable at `pivot_energy`.

| Attribute             | Value                                                                    |
| --------------------- | ------------------------------------------------------------------------ |
| Exposed parameters    | `flux_norm`, `spectral_index_1`, `spectral_index_2`, `logEbreak`         |
| Required variables    | `true_energy`                                                            |
| YAML keys             | `name`, `pivot_energy`, `baseline_norm`, optional `param_mapping`         |

`logEbreak` is $\log_{10}(E_\text{break} / \mathrm{GeV})$.

```yaml
- name: astro_broken
  type: BrokenPowerLawFlux
  pivot_energy: 1.0e5
  baseline_norm: 1.0e-18
  param_mapping:
    flux_norm: astro_norm
    spectral_index_1: gamma_low
    spectral_index_2: gamma_high
    logEbreak: log10_Ebreak
```

---

### `FluxNorm`

Pure scalar normalization $F = \Phi_0$. Useful for chaining a free overall scale onto a fixed shape.

| Attribute             | Value                                |
| --------------------- | ------------------------------------ |
| Exposed parameters    | `flux_norm`                          |
| Required variables    | *(none)*                             |
| YAML keys             | `name`, optional `param_mapping`     |

```yaml
- name: galactic_norm
  type: FluxNorm
  param_mapping:
    flux_norm: gp_norm
```

---

### `GaisserZenithFactor`

Atmospheric π/K Gaisser bracket

$$B(E, \theta) = \frac{1}{1 + a_\pi E \cos\theta^\star / \varepsilon_\pi}
              + R_{K/\pi} \cdot \frac{1}{1 + b_K E \cos\theta^\star / \varepsilon_K},$$

normalized so that $B(E_\text{pivot}, \text{vertical}) = 1$. Uses the Chirkin (2004)
Earth-curvature corrected effective $\cos\theta^\star$ when `earth_curvature: true`.

| Attribute             | Value                                       |
| --------------------- | ------------------------------------------- |
| Exposed parameters    | `kaon_pion_ratio`                           |
| Required variables    | `true_energy`, `true_zenith` (radians)      |
| YAML keys             | `name`, `pivot_energy`, optional `epsilon_pi` (default 115), `epsilon_K` (850), `a_pi` (1.0), `b_K` (1.0), `earth_curvature` (true), `param_mapping` |

The factor uses $|\cos\theta|$ internally so atmospheric symmetry is automatic.

```yaml
- name: atmo_zenith
  type: GaisserZenithFactor
  pivot_energy: 1.0e5
  param_mapping:
    kaon_pion_ratio: 0.213          # fix at canonical value
```

---

### `FlavorRatio`

Per-flavor scaling using `true_type` (PDG-like codes 12 = ν_e, 14 = ν_μ, 16 = ν_τ, signs ignored).
Muon neutrinos are kept at 1; electron and tau are rescaled.

| Attribute             | Value                                        |
| --------------------- | -------------------------------------------- |
| Exposed parameters    | `nue_ratio`, `nutau_ratio`                   |
| Required variables    | `true_type`                                  |
| YAML keys             | `name`, optional `param_mapping`             |

```yaml
- name: flavor
  type: FlavorRatio
```

---

### `SegmentedPlane`

Galactic-plane component with **per-longitude-segment** norm and spectral index. Events outside the
latitude window `|true_lat| ≤ height` get zero weight.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | `galactic_norm_{i}`, `galactic_gamma_{i}` for each segment `i`   |
| Required variables    | `true_energy`, `true_lat`, `true_lon`                            |
| YAML keys             | `name`, `reference_energy`, `baseline_flux`, `segment_edges` (list of longitude edges), `height` (latitude half-width in radians), optional `param_mapping` |

```yaml
- name: gp_segmented
  type: SegmentedPlane
  reference_energy: 1.0e3
  baseline_flux: 1.0
  height: 0.087266            # ~5° in radians
  segment_edges: [-3.1416, -1.0, 0.0, 1.0, 3.1416]
```

---

### `GalacticPlaneBox`

Pure box selector in galactic latitude (no fittable parameters, no longitude dependence).
Returns 1 for $|\text{true\_lat}| \le \text{height}$, else 0. Pair with a `PowerLawFlux` and a
`FluxNorm` to model a galactic-plane component.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | *(none)*                                                         |
| Required variables    | `true_lat` (radians)                                             |
| YAML keys             | `name`, `height`, optional `param_mapping`                       |

```yaml
- name: gp_box
  type: GalacticPlaneBox
  height: 0.087266          # ~5°
```

---

### `SnowstormGauss`

Gaussian reweighting against a per-event sampled systematic value. Reweights events drawn uniformly
on `sys_sim_bounds` toward a Gaussian centred on `scale` with width `sys_gauss_width`.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | `scale`                                                          |
| Required variables    | `req_variable_name` (whatever you pass in YAML)                  |
| YAML keys             | `name`, `sys_gauss_width`, `sys_sim_bounds` (`[lo, hi]`), `req_variable_name`, optional `param_mapping` |

```yaml
- name: snowstorm_abs
  type: SnowstormGauss
  sys_gauss_width: 0.05
  sys_sim_bounds: [0.85, 1.15]
  req_variable_name: ice_absorption_sample
  param_mapping:
    scale: ice_absorption
```

---

### `DeltaGamma`

Spectral-index nuisance pull as $(E / E_\text{ref})^{-\Delta\gamma}$. Typically combined with a
`PowerLawFlux` to let the spectral index float as a nuisance parameter while keeping the
parameter-of-interest fixed.

| Attribute             | Value                                          |
| --------------------- | ---------------------------------------------- |
| Exposed parameters    | `delta_gamma`                                  |
| Required variables    | `true_energy` (and historically `median_energy`) |
| YAML keys             | `name`, `reference_energy`, optional `param_mapping` |

```yaml
- name: spectral_nuisance
  type: DeltaGamma
  reference_energy: 1.0e5
```

---

### `ModelInterpolator`

Differentiable interpolation between two precomputed event-weight sets:

$$F_i = (1 - \lambda) + \lambda \cdot \frac{w_\text{alt}}{w_\text{base}},$$

with safe handling of zero baseline weights. Useful when you have two MC weighting hypotheses and
want to fit the mixing fraction.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | `lambda_int`                                                     |
| Required variables    | `<baseline_weight>`, `<alternative_weight>` (names from YAML)     |
| YAML keys             | `name`, `baseline_weight`, `alternative_weight`, optional `param_mapping` |

```yaml
- name: model_interp
  type: ModelInterpolator
  baseline_weight: w_conv
  alternative_weight: w_prompt
```

---

### `GradientReweight`

Linear gradient reweighting (e.g. Barr parameters):

$$F_i = \frac{w_\text{base} + \sum_p \alpha_p \cdot g_{p,i}}{w_\text{base}}.$$

Each parameter `alpha_p` is exposed; the per-event gradient $g_{p,i}$ is read from the dataset.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | The keys of `gradient_key_mapping`                               |
| Required variables    | The values of `gradient_key_mapping` and `baseline_weight`       |
| YAML keys             | `name`, `gradient_key_mapping` (dict), `baseline_weight`, optional `param_mapping` |

```yaml
- name: barr_gradients
  type: GradientReweight
  baseline_weight: w_conv
  gradient_key_mapping:
    barr_w: dw_w
    barr_y: dw_y
```

---

### `ClassifierGradientReweight`

Polynomial reweighting from classifier-fit log-weight gradients:

$$r_i(\alpha) = \exp\left(\sum_{p, k} g_{p,k,i} \cdot (\alpha_p - \alpha_p^\text{nom})^k\right).$$

Each `(param, order)` pair in `poly_features` consumes one input column named per
`gradient_col_template` (default `"g_{param}_{order}"`).

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | The unique `param` names in `poly_features`                      |
| Required variables    | One column per `(param, order)` tuple, named via `gradient_col_template` |
| YAML keys             | `name`, `poly_features` (list of `[param, order]`), `nominal_values` (dict), optional `gradient_col_template`, optional `param_mapping` |

```yaml
- name: cls_grad
  type: ClassifierGradientReweight
  poly_features:
    - [abs,  1]
    - [abs,  2]
    - [qeff, 1]
    - [qeff, 2]
  nominal_values:
    abs:  1.0
    qeff: 1.0
```

---

### `VetoThreshold`

Second-order log-passing-fraction reweighting for the atmospheric self-veto:

$$\log_{10} \mathrm{PF}_i = a_i + b_i \cdot \Delta E + c_i \cdot \Delta E^2,$$

with $\Delta E = E_\text{rescale} \cdot 10^{e_\text{threshold}} - E_\text{anchor}$ and the
per-event $(a, b, c)$ coefficients read from the dataset.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | `e_threshold`                                                    |
| Required variables    | The column names you pass as `threshold_a`, `threshold_b`, `threshold_c` |
| YAML keys             | `name`, `threshold_a`, `threshold_b`, `threshold_c`, `rescale_energy`, `anchor_energy`, optional `param_mapping` |

```yaml
- name: veto
  type: VetoThreshold
  threshold_a: pf_a
  threshold_b: pf_b
  threshold_c: pf_c
  rescale_energy: 100.0
  anchor_energy: 100.0
```

---

### `FixedVeto`

Applies a fixed per-event passing fraction column.

| Attribute             | Value                                                |
| --------------------- | ---------------------------------------------------- |
| Exposed parameters    | *(none)*                                             |
| Required variables    | The column passed as `passing_fraction`               |
| YAML keys             | `name`, `passing_fraction`, optional `param_mapping`  |

```yaml
- name: pf
  type: FixedVeto
  passing_fraction: passing_fraction
```

---

### `SoftCut`

Differentiable sigmoid cut on a variable: returns $\sigma(\mathrm{slope} \cdot (x - x_\text{cut}))$.

| Attribute             | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| Exposed parameters    | *(none — `cut_value` is a configuration constant)*               |
| Required variables    | `cut_variable`                                                   |
| YAML keys             | `name`, `cut_variable`, `slope`, `cut_value`, optional `param_mapping` |

```yaml
- name: e_softcut
  type: SoftCut
  cut_variable: log10_reco_energy
  slope: 5.0
  cut_value: 3.0
```

---

## Binned factors

Binned factors live on a `BinnedExpectation` (under `hist_factors:` in YAML) and are added to the
histogram after it has been built. They return a `(mu_add, ssq_add)` tuple per bin.

### `SnowStormGradient`

Additive per-bin systematic reweighting using a precomputed gradient pickle.

| Attribute             | Value                                                                    |
| --------------------- | ------------------------------------------------------------------------ |
| Exposed parameters    | Whatever you pass as `parameters`                                        |
| Required variables    | *(none — purely additive over the histogram)*                            |
| YAML keys             | `name`, `parameters` (list), `gradient_names` (list, same length), `default` (list), `split_values` (list), `gradient_pickle` (path), optional `param_mapping` |

The pickle is expected to be a dict with keys `binning`, `livetime`, and one entry per
`gradient_name` containing `{"gradient": ndarray, "gradient_error": ndarray}` with shapes matching
the binning.

```yaml
- name: snowstorm
  type: SnowStormGradient
  parameters: [ice_absorption, dom_efficiency]
  gradient_names: [abs, qeff]
  default: [1.0, 1.0]
  split_values: [1.0, 1.0]
  gradient_pickle: gradients/snowstorm_ic86.pkl
```

---

### `ScaledTemplate`

A per-bin template (loaded from a pickle) scaled by a single parameter `template_norm`. The pickle
must contain `{"template": ndarray}` and optionally `{"template_fluctuation": ndarray}` for the
per-bin MC variance.

| Attribute             | Value                                              |
| --------------------- | -------------------------------------------------- |
| Exposed parameters    | `template_norm`                                    |
| Required variables    | *(none)*                                           |
| YAML keys             | `name`, `template_file`, optional `param_mapping`  |

```yaml
- name: muon_template
  type: ScaledTemplate
  template_file: templates/muons_ic86.pkl
  param_mapping:
    template_norm: muon_norm
```

---

### `PerBinPolynomial`

Per-bin polynomial in a single parameter `scale`. The coefficients pickle is an array of shape
`(order+1, *hist_dims)` where order is 1 or 2 (i.e. only 2nd- and 3rd-order polynomials are
supported).

| Attribute             | Value                                                |
| --------------------- | ---------------------------------------------------- |
| Exposed parameters    | `scale`                                              |
| Required variables    | *(none)*                                             |
| YAML keys             | `name`, `coefficients_file`, optional `param_mapping`|

```yaml
- name: binned_systematic
  type: PerBinPolynomial
  coefficients_file: systematics/poly_coeffs.pkl
```

---

## Quick lookup table

| Factor                       | Exposed parameters                                            | Required variables                                |
| ---------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| `PowerLawFlux`               | `flux_norm`, `spectral_index`                                 | `true_energy`                                     |
| `BrokenPowerLawFlux`         | `flux_norm`, `spectral_index_1`, `spectral_index_2`, `logEbreak` | `true_energy`                                  |
| `FluxNorm`                   | `flux_norm`                                                   | —                                                 |
| `GaisserZenithFactor`        | `kaon_pion_ratio`                                             | `true_energy`, `true_zenith`                      |
| `FlavorRatio`                | `nue_ratio`, `nutau_ratio`                                    | `true_type`                                       |
| `SegmentedPlane`             | `galactic_norm_{i}`, `galactic_gamma_{i}`                     | `true_energy`, `true_lat`, `true_lon`             |
| `GalacticPlaneBox`           | —                                                             | `true_lat`                                        |
| `SnowstormGauss`             | `scale`                                                       | `<req_variable_name>`                             |
| `DeltaGamma`                 | `delta_gamma`                                                 | `true_energy`                                     |
| `ModelInterpolator`          | `lambda_int`                                                  | `<baseline_weight>`, `<alternative_weight>`       |
| `GradientReweight`           | keys of `gradient_key_mapping`                                | values of `gradient_key_mapping`, `<baseline_weight>` |
| `ClassifierGradientReweight` | unique `param`s in `poly_features`                            | one g-column per `(param, order)`                 |
| `VetoThreshold`              | `e_threshold`                                                 | `threshold_a`, `threshold_b`, `threshold_c` columns |
| `FixedVeto`                  | —                                                             | `<passing_fraction>`                              |
| `SoftCut`                    | —                                                             | `<cut_variable>`                                  |
| `SnowStormGradient` (binned) | from YAML `parameters`                                        | — (binned-only)                                   |
| `ScaledTemplate` (binned)    | `template_norm`                                               | — (binned-only)                                   |
| `PerBinPolynomial` (binned)  | `scale`                                                       | — (binned-only)                                   |
