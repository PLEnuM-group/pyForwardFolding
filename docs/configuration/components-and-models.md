# Components and models

## `components:`

A component is a **product of factors**. Each entry lists factor names (defined under
[`factors:`](factors.md)) by name; the loader looks them up and groups them.

```yaml
components:
  - name: "astro"
    factors: ["powerlaw_astro"]
  - name: "atmo"
    factors: ["atmo_powerlaw", "atmo_zenith"]
```

Factor names must be unique **within a component**.

> A `ModelComponent` is mathematically $m_C(X \mid \theta_C) = \prod_f F_{f,C}(X \mid \theta_f)$;
> see [Concepts → Overview](../concepts/overview.md) for the math.

## `models:`

A model is a **sum of components**, where each component is paired with a **baseline-weight key**
naming the column in your dataset that holds the per-event generation weight for that component.

```yaml
models:
  - name: "model"
    components:
      - name: "astro"
        baseline_weight: "baseline_weight"
      - name: "atmo"
        baseline_weight: "baseline_weight"
```

Multiple components can share a single baseline-weight column (as above) if the MC was generated
under a common weighting scheme. If different components come from different MC sets with
different generation weights, give them distinct baseline-weight column names.

> Mathematically: $M^D(X^D \mid \theta) \cdot w^D_i$ where the per-event $w_i^D$ is the baseline
> weight named here.

Component names within one model must be unique.

## How they feed into histograms

The `histograms:` section ties **one or more `(model, dataset)` pairs** to a binning. So a single
model can be evaluated against multiple datasets (multi-detector / multi-sample analyses) by
listing several pairs in the `models:` field of a histogram entry:

```yaml
histograms:
  - name: combined
    binning: ...
    models:
      - ["model", "ic86_tracks"]
      - ["model", "ic86_cascades"]
```

See [Histograms](histograms.md) for details.
