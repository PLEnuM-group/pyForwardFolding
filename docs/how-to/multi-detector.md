# Set up a multi-detector / multi-sample analysis

The basic idea: one `Analysis` holds *several* `BinnedExpectation` objects keyed by name, each with
its own dataset, binning, lifetime, and binned factors. Parameters with the same exposed name in
different samples become the **same** fit parameter automatically.

## YAML

Two histograms, one per detector, sharing the same model:

```yaml
factors:
  - name: powerlaw
    type: PowerLawFlux
    pivot_energy: 1.0e5
    baseline_norm: 1.0e-18
    param_mapping:
      flux_norm: astro_norm
      spectral_index: astro_index

components:
  - { name: astro, factors: [powerlaw] }

models:
  - name: model
    components:
      - { name: astro, baseline_weight: baseline_weight }

histograms:
  - name: ic86_tracks
    binning:
      type: RectangularBinning
      bin_vars_edges:
        - ["log10_reco_energy", "linear", [2.5, 7, 31]]
        - ["cos_reco_zenith",   "linear", [-1, 0, 25]]
    lifetime: 315600000
    models: [["model", "ic86_tracks"]]
  - name: ic86_cascades
    binning:
      type: RectangularBinning
      bin_vars_edges:
        - ["log10_reco_energy", "linear", [3, 7, 21]]
        - ["cos_reco_zenith",   "linear", [-1, 0, 13]]
    lifetime: 315600000
    models: [["model", "ic86_cascades"]]

model_parameters:  { astro_norm: 1.0, astro_index: 2.5 }
prior_seeds:       { astro_norm: 1.0, astro_index: 2.5 }
prior_bounds:
  astro_norm:  [0.0, .inf]
  astro_index: [-.inf, .inf]
```

## Dataset

```python
data = {
    "ic86_tracks":   {...},
    "ic86_cascades": {...},
}
ana = pyFF.config.analysis_from_config("config.yaml")
ana.evaluate(data, params)
# → {"ic86_tracks": (31, 24) array, "ic86_cascades": (20, 12) array}, plus matching ssq dict
```

## Different per-detector systematics

Each `BinnedExpectation` has its own `hist_factors`, so detector-specific binned systematics live
on the relevant entry only:

```yaml
- name: ic86_tracks
  binning: ...
  models: [["model", "ic86_tracks"]]
  hist_factors:
    - { name: snowstorm_tracks, type: SnowStormGradient, ... }

- name: ic86_cascades
  binning: ...
  models: [["model", "ic86_cascades"]]
  hist_factors:
    - { name: snowstorm_cascades, type: SnowStormGradient, ... }
```

Per-event detector systematics (e.g. one `SnowstormGauss` per detector) typically end up in
separate **components** that are then composed differently per model. You can either:

- Have one shared model and let per-event factors read from per-detector dataset columns, or
- Use *different* models per histogram (the `models:` of a histogram is `[[model_name, dataset_key], ...]`,
  so you can list any combination).

## Joint fitting

The likelihood is summed over all expectations automatically:

```python
llh  = pyFF.likelihood.PoissonLikelihood(ana, priors)
mini = pyFF.minimizer.ScipyMinimizer(llh)
mini.minimize(
    observed={"ic86_tracks": tracks_hist, "ic86_cascades": cascades_hist},
    dataset=data,
)
```

`astro_norm` and `astro_index` are common parameters and are fitted jointly. If you wanted, say, a
separate spectral index per detector, you'd give the two `PowerLawFlux` factors different
`spectral_index → ...` rename targets and put them in *different* components (e.g. `astro_tracks`
vs. `astro_cascades`) feeding *different* models.
