# Conceptual overview

## What "forward folding" means here

You have a collection of Monte Carlo events with true properties $X = (E, \theta, \ldots)$,
reconstructed quantities $\hat X = (\hat E, \hat\theta, \ldots)$, and per-event weights $w_i$ that
encode the detector response so that the differential rate is

$$
R(X) = w \cdot M(X \mid \theta).
$$

$M(X \mid \theta)$ is the differential flux model with free parameters $\theta$.

A "forward-folded" prediction in bin $A$ is obtained by re-weighting every MC event with the current
model and histogramming by their **reconstructed** quantities:

$$
\mu_A(X, \hat X, \theta) = \sum_i I_A(\hat X_i) \cdot w_i \cdot M(X_i \mid \theta),
$$

where $I_A$ is the bin indicator. This avoids fitting a parametric form to histogrammed data;
instead the histogram itself is differentiable in $\theta$ through the per-event weights.

## How the math maps to classes

A model is built compositionally:

$$
M(X \mid \theta) = \sum_C m_C(X \mid \theta_C),
\quad\text{with}\quad
m_C(X \mid \theta_C) = \prod_f F_{f,C}(X \mid \theta_f).
$$

The classes mirror this structure exactly:

| Symbol                                                | Class                                                                 | Role                                                |
| ----------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------- |
| $F(X \mid \theta_f)$                                  | [`Factor`](../reference/api/factor.md) (subclasses of `AbstractUnbinnedFactor`) | A single multiplicative per-event factor            |
| $m_C(X^D) \cdot w_i^D \cdot S^D(X^D)$                 | [`ModelComponent`](../reference/api/model_component.md)               | Product of factors                                  |
| $M^D(X^D \mid \theta) \cdot w^D_i$                    | [`Model`](../reference/api/model.md)                                  | Sum of components, with one baseline-weight name per component |
| $\mu^D_A(X^D, \hat X^D, \theta)$                      | [`BinnedExpectation`](../reference/api/binned_expectation.md)         | Histograms one model over one binning and lifetime  |
| $S_A^D$                                               | `AbstractBinnedFactor` (e.g. `SnowStormGradient`, `ScaledTemplate`)   | Additive per-bin correction                         |
| $\hat\mu^D_A(X^D, \hat X^D, \theta)$                  | [`Analysis`](../reference/api/analysis.md)                            | Collection of binned expectations (multi-detector)  |
| $\mathcal L$                                          | [`Likelihood`](../reference/api/likelihood.md)                        | Evaluates the binned likelihood + priors            |

## Why factor composition?

The factor abstraction lets you build complicated flux models from small reusable pieces. For
example, an atmospheric flux component might be the product of:

- a `PowerLawFlux` (spectral shape),
- a `GaisserZenithFactor` (atmospheric zenith dependence),
- a `VetoThreshold` or `FixedVeto` (atmospheric self-veto effect),

while an astrophysical component might be a single `PowerLawFlux` or a `BrokenPowerLawFlux`. Both
components reuse the same `PowerLawFlux` class with different configuration.

Detector systematics that act per-event (e.g. ice optical-property reweighting via
`SnowstormGauss`, `GradientReweight`, or `ClassifierGradientReweight`) are *also* just factors —
they slot into a component multiplicatively without any special-casing.

Systematics that act per-bin (e.g. SnowStorm gradients integrated over MC ensembles, or scaled
template additions) are **binned** factors. They live on the [`BinnedExpectation`](../reference/api/binned_expectation.md)
rather than inside the [`Model`](../reference/api/model.md) and are added to the histogram
after it has been built.

## Parameter exposure and naming

Every factor declares an internal list of `factor_parameters` (e.g. `["flux_norm", "spectral_index"]`).
When you build a factor you can pass `param_mapping` to control how those internal names appear in
the global parameter dictionary that the likelihood sees:

- **Rename**: map an internal name to a string — e.g. `flux_norm: "astro_norm"` exposes the
  parameter as `astro_norm`.
- **Fix**: map an internal name to a number — e.g. `spectral_index: 2.7` removes that parameter
  from the free parameters of the fit and uses 2.7 directly.
- **Default**: parameters not listed in `param_mapping` are exposed under their original name.

This is what makes two `PowerLawFlux` factors in the same model — one for astrophysical, one for
atmospheric — coexist without name collisions.

## Multi-detector / multi-sample analyses

A single [`Analysis`](../reference/api/analysis.md) holds a dict of named binned expectations. You
can use this to:

- Combine multiple detectors (e.g. tracks and cascades, IceCube and KM3NeT).
- Combine multiple event selections / topologies within the same detector.
- Share parameters across samples — because each component pulls from the same flat parameter
  dictionary, a parameter renamed `astro_norm` in two different factors is automatically the same
  parameter at fit time.

Each binned expectation has its own dataset, its own binning, its own lifetime, and optionally its
own binned factors, but they all evaluate the likelihood jointly.

## The fitting story

1. Choose a likelihood:
   [`PoissonLikelihood`](../reference/api/likelihood.md) (standard binned Poisson) or
   [`SAYLikelihood`](../reference/api/likelihood.md) (the Argüelles, Schneider, Yuan likelihood that
   accounts for limited MC statistics, [arXiv:1901.04645](https://arxiv.org/abs/1901.04645)).
2. Attach priors. `UniformPrior` is a dummy (provides bounds but no log-PDF contribution);
   `GaussianUnivariatePrior` adds Gaussian pulls.
3. Pick a minimizer. [`ScipyMinimizer`](../reference/api/minimizer.md) uses L-BFGS-B and is the
   simplest option. [`MinuitMinimizer`](../reference/api/minimizer.md) wraps iMinuit and exposes
   covariance / MIGRAD diagnostics.
4. For tests on top of fits, use the [`statistics`](../reference/api/statistics.md) module:
   `Hypothesis`, `HypothesisTest`, `PseudoExpGenerator`, discovery potential, Asimov asymptotics.

The full math (including detector systematics and multi-detector combination) is laid out in the
[README's model-structure section](https://github.com/chrhck/pyForwardFolding#model-structure).
