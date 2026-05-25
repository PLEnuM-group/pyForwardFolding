# Likelihood reference

## Likelihood classes

| Class                      | Use when                                                |
| -------------------------- | ------------------------------------------------------- |
| `PoissonLikelihood`        | Standard binned Poisson likelihood                      |
| `SAYLikelihood`            | MC statistics are limited (arXiv:1901.04645)            |

Both accept `(analysis: Analysis, priors: List[AbstractPrior])` and expose

```python
llh.llh(observed_data, datasets, parameter_values, empty_bins="skip")
```

`empty_bins` can be `"skip"` (default — substitute $10^{-8}$ when the expectation is zero) or
`"throw"` (raise `ValueError`).

### Poisson — formula

$$
\log\mathcal L = \sum_A \big[-\mu_A + n_A \log\mu_A - \log(n_A!)\big] \;+\; \sum_p \log p_\text{prior}.
$$

The factorial term is computed via `gammaln(n+1)` and so stays differentiable.

### SAY — formula

For each bin:

$$
\alpha = \tfrac{\mu^2}{\sigma_\mu^2} + 1, \quad \beta = \tfrac{\mu}{\sigma_\mu^2}
$$

$$
\log \mathcal L_\text{eff} = \alpha\log\beta + \log\Gamma(n+\alpha) - \log\Gamma(n+1) - (n+\alpha)\log(1+\beta) - \log\Gamma(\alpha)
$$

When $\sigma_\mu^2 = 0$ (no MC variance information) the bin falls back to the Poisson term. The
implementation also clips $\sigma_\mu^2 \le \mu^2$ to keep $\alpha, \beta$ well-defined under
nuisance-parameter induced negative-weight contributions.

## Prior classes

| Class                         | Notes                                                            |
| ----------------------------- | ---------------------------------------------------------------- |
| `UniformPrior`                | Dummy prior. Bounds + seeds, but zero log-PDF contribution.      |
| `GaussianUnivariatePrior`     | Product of independent Gaussians (un-normalised; only the −½ z² term is added). |

Every parameter exposed by the analysis **must** appear in at least one prior — the likelihood
constructor checks this and raises `ValueError` on a mismatch.

```python
from pyForwardFolding.likelihood import UniformPrior, GaussianUnivariatePrior

uniform = UniformPrior(
    prior_seeds={"astro_norm": 1.0, "astro_index": 2.0},
    prior_bounds={"astro_norm": (0.0, float("inf")), "astro_index": (-float("inf"), float("inf"))},
)

gauss = GaussianUnivariatePrior(
    prior_params={"kaon_pion_ratio": (0.213, 0.05)},
    prior_seeds={"kaon_pion_ratio": 0.213},
    prior_bounds={"kaon_pion_ratio": (0.0, 1.0)},
)
```

## Helpers

- `likelihood.get_analysis()` — returns the wrapped `Analysis`.
- `likelihood.get_seeds()` — concatenates `prior_seeds` across all priors.
- `likelihood.get_bounds()` — concatenates `prior_bounds` across all priors.

These are what the minimizers use to assemble flat seed / bound vectors automatically.
