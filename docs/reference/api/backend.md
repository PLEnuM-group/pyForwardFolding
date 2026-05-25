# `pyForwardFolding.backend`

The JAX-based numerical backend. The `Backend` protocol defines the operations that factors,
binnings, and likelihoods rely on; `JAXBackend` is the concrete implementation. The default
instance is exposed as `pyForwardFolding.backend.backend`.

If you write custom factors, prefer `backend.<op>` over importing JAX or NumPy directly — it keeps
your code differentiable and JIT-compatible.

::: pyForwardFolding.backend
