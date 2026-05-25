# Likelihood and priors

Once an [`Analysis`](../reference/api/analysis.md) can predict histograms, the likelihood combines
those predictions with observed counts and (optionally) priors on the parameters.

## Available likelihoods

### PoissonLikelihood

The standard binned-Poisson log-likelihood (constant terms dropped):

$$
\log \mathcal{L} = \sum_A \left[ -\mu_A + n_A \log\mu_A - \log(n_A!) \right]
$$

evaluated per bin and summed. Empty-expectation bins are skipped by default (substitute a tiny
$\mu \to 10^{-8}$ to keep gradients finite); set `empty_bins="throw"` to error instead.

```python
from pyForwardFolding.likelihood import PoissonLikelihood, UniformPrior

priors = [UniformPrior(prior_seeds, prior_bounds)]
llh = PoissonLikelihood(ana, priors)
value = llh.llh(observed_counts, datasets, parameter_values)
```

### SAYLikelihood

The "Argüelles, Schneider, Yuan" effective likelihood that accounts for **limited MC statistics**
([arXiv:1901.04645](https://arxiv.org/abs/1901.04645)). It marginalises the Poisson mean over a
Gamma prior whose width comes from the per-bin MC sum-of-squared-weights:

$$
\alpha = \tfrac{\mu^2}{\sigma_\mu^2} + 1, \quad \beta = \tfrac{\mu}{\sigma_\mu^2}
$$

$$
\log\mathcal{L}_\text{SAY} = \alpha\log\beta + \log\Gamma(n + \alpha) - \log\Gamma(n+1) - (n+\alpha)\log(1+\beta) - \log\Gamma(\alpha)
$$

Use this when MC statistics are limited relative to data — it's a drop-in replacement for
`PoissonLikelihood`:

```python
from pyForwardFolding.likelihood import SAYLikelihood
llh = SAYLikelihood(ana, priors)
```

## Priors

Every exposed parameter of the analysis **must** appear in at least one prior — the likelihood
constructor checks this and raises `ValueError` on a mismatch.

### UniformPrior

A dummy prior that contributes 0 to the log-likelihood but does carry bounds and seeds. Use this
for any parameter you want to leave un-pulled.

```python
from pyForwardFolding.likelihood import UniformPrior

UniformPrior(
    prior_seeds={"astro_norm": 1.0, "astro_index": 2.0},
    prior_bounds={"astro_norm": (0.0, float("inf")), "astro_index": (-float("inf"), float("inf"))},
)
```

### GaussianUnivariatePrior

A product of independent Gaussian pulls (un-normalised — only the quadratic term is added). Use this
for nuisance parameters constrained to within some tolerance of a nominal value.

```python
from pyForwardFolding.likelihood import GaussianUnivariatePrior

GaussianUnivariatePrior(
    prior_params={"kaon_pion_ratio": (0.213, 0.05)},  # (mean, std)
    prior_seeds={"kaon_pion_ratio": 0.213},
    prior_bounds={"kaon_pion_ratio": (0.0, 1.0)},
)
```

The corresponding YAML keys are `prior_params_gauss`, `prior_seeds_gauss`, and `prior_bounds_gauss`,
loaded automatically by [`params_from_config`](../reference/api/config.md). Parameters that appear
only in `prior_*` (uniform) get a `UniformPrior`; parameters that appear in `prior_*_gauss` get an
additional `GaussianUnivariatePrior`.

## Combining

The total log-likelihood is the sum of the binned term and all prior log-PDFs:

$$
\log \mathcal L_\text{total} = \log\mathcal L_\text{binned} + \sum_p \log p_\text{prior}.
$$

A single fit may use multiple priors (e.g. one `UniformPrior` for the free parameters of interest
plus one `GaussianUnivariatePrior` for nuisance pulls). The constructor concatenates seeds and
bounds across priors for the minimizer.
