# Write a custom factor

The factor API is small. To add a new factor you implement one subclass and register it in the
`type:` dispatch table.

## Recipe

```python
from typing import Any, Dict, List, Optional, Union
from pyForwardFolding.backend import Array, backend
from pyForwardFolding.factor import AbstractUnbinnedFactor, FACTORSTR_CLASS_MAPPING


class MyCustomFactor(AbstractUnbinnedFactor):
    """One-line summary.

    Longer description: what physics it models, which other factors it
    composes with, edge cases.

    Parameters required by this factor: ``my_param``.
    Variables required by this factor:  ``my_variable``.

    Args:
        name (str): Identifier for the factor.
        my_constant (float): A configuration constant (not fitted).
        param_mapping (dict, optional): As for all factors.
    """

    def __init__(
        self,
        name: str,
        my_constant: float,
        param_mapping: Optional[Dict[str, Union[str, float]]] = None,
    ):
        super().__init__(name, param_mapping)
        self.my_constant = my_constant

        # Declare what this factor consumes:
        self.factor_parameters: List[str] = ["my_param"]
        self.req_vars: List[str] = ["my_variable"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "MyCustomFactor":
        # Build from a YAML dict (the ``factors:`` entry).
        return cls(
            name=config["name"],
            my_constant=config["my_constant"],
            param_mapping=config.get("param_mapping", None),
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        # Pull only the variables this factor declares it needs:
        from pyForwardFolding.factor import (
            get_required_variable_values,
            get_parameter_values,
        )
        inputs = get_required_variable_values(self, input_variables)
        params = get_parameter_values(self, parameter_values)

        x = inputs["my_variable"]
        a = params["my_param"]
        return backend.exp(a * x * self.my_constant)


# Register so YAML configs can refer to it by name:
FACTORSTR_CLASS_MAPPING["MyCustomFactor"] = MyCustomFactor
```

## Three things to get right

1. **`self.factor_parameters`** is the list of *internal* parameter names. They get bridged to
   global names through `param_mapping`. Users will not see these strings unless they're left
   un-renamed.
2. **`self.req_vars`** is the list of dataset keys the factor reads. Returning per-event arrays of
   the wrong shape will fail at histogramming time, not at factor evaluation, so cross-check.
3. **Use `pyForwardFolding.backend.backend`**, not raw NumPy or JAX. Going through the backend
   keeps the factor differentiable and JIT-compatible.

## Binned factors

If your factor naturally acts at the histogram level (e.g. a per-bin systematic), subclass
`AbstractBinnedFactor` instead. The differences:

- The constructor takes a `binning: AbstractBinning` argument and so does `construct_from`.
- `evaluate` returns a `(mu_add, ssq_add)` tuple — both per-bin arrays of shape `binning.hist_dims`,
  or `(mu_add, None)` if you don't have variance information.

See `pyForwardFolding.factor.ScaledTemplate` for a minimal example.

## Smoke test

```python
import jax.numpy as jnp

f = MyCustomFactor("my_factor", my_constant=0.5)
out = f.evaluate(
    {"my_variable": jnp.linspace(0, 1, 10)},
    {"my_param": 1.5},
)
print(out.shape)               # (10,)
print(f.exposed_parameters)    # ['my_param']
print(f.required_variables)    # ['my_variable']
```

Add a unit test in `tests/test_factor.py` and you're done.
