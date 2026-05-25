# Installation

## Requirements

- Python ≥ 3.10, < 4
- A working installation of [JAX](https://jax.readthedocs.io) (pulled in automatically as a dependency).

The required runtime dependencies, as declared in `pyproject.toml`, are:

- `jax==0.6.1`, `jaxlib==0.6.1`
- `ml_dtypes==0.5.1`
- `numpy==2.2.6`, `pandas>=2.2`, `pyArrow>=19`
- `pyyaml>=6.0`
- `iminuit>=2.31`
- `scikit-learn>=1.6`

## From source

```sh
git clone https://github.com/chrhck/pyForwardFolding.git
cd pyForwardFolding
pip install .
```

For an editable install (recommended when developing):

```sh
pip install -e .
```

## Optional dependency groups

The project defines optional dependency groups in `pyproject.toml`:

| Group     | Installs                            | Use for                              |
| --------- | ----------------------------------- | ------------------------------------ |
| `tests`   | `pytest`, `pytest-mock`, `coverage` | Running the test suite               |
| `checks`  | `mypy`, `ruff`                      | Type-checking and linting            |
| `docs`    | `mkdocs-material`, `mkdocstrings`, `mkdocs-jupyter` | Building this documentation site |

Install with, e.g.:

```sh
pip install -e ".[docs,tests]"
```

## Using Hatch (recommended for development)

The project ships a [Hatch](https://hatch.pypa.io/) configuration. Hatch will create and manage a
virtual environment in `.venv/` for you:

```sh
hatch env create
hatch shell        # activate the environment
hatch run check    # ruff + mypy + spell check
hatch run format   # auto-format
```

## Verifying the install

```python
import pyForwardFolding as pyFF
print(pyFF.__version__)
```

On import, the package enables 64-bit precision in JAX (you'll see a one-time warning to that
effect). All numerical operations in pyForwardFolding go through this backend.
