# Datasets

The `datasets:` section is **optional**. It lets the loader read DataFrames from disk and translate
them into the dict-of-dicts format that `analysis.evaluate(...)` expects.

If you don't use this section, you're responsible for building the dataset dict yourself (as in the
[Quickstart](../getting-started/quickstart.md)). Most analyses do build the dataset in Python rather
than from the loader, because pre-processing and cuts usually live outside YAML.

## Schema

```yaml
datasets:
  - name: "ic86_tracks"                        # Used as the top-level dataset key
    path: "/path/to/events.parquet"            # File on disk
    param_mapping:                              # Map output keys (used by factors / binning)
      true_energy:                              # ...to input column names with optional transforms
        df_key: "energy_true"
      log10_reco_energy:
        df_key: "energy_reco"
        transform: "log10"
      cos_reco_zenith:
        df_key: "zenith_reco"
        transform: "cos"
      baseline_weight:
        df_key: "weight"
    # Optional: precomputed median energy stashed in the dataset under "median_energy"
    median_energy:
      energy_key: "energy_true"
      weight: "weight"
```

## What the loader does

For each entry:

1. Loads the DataFrame from `path` via `pyForwardFolding.config.load_dataframe`, which dispatches
   on file extension. Supported formats: CSV (`.csv`, `.txt`), Parquet (`.parquet`), Feather
   (`.feather`, `.ft`), HDF5 (`.h5`, `.hdf`, `.hdf5`), Excel (`.xlsx`, `.xls`), Pickle (`.pkl`,
   `.pickle`).
2. For each entry of `param_mapping`, pulls the column named by `df_key`, optionally applies a
   `transform` (which must be a method on `pyForwardFolding.backend.backend` — common choices are
   `log10`, `cos`, `sin`, `exp`), and stores it under the output key.
3. If `median_energy` is provided, computes
   `backend.weighted_median(df[energy_key], df[weight])` and stores it under the
   key `"median_energy"` — useful for factors like `DeltaGamma` that operate around a sample's
   median energy.

The returned object is:

```python
{
    "ic86_tracks": {
        "true_energy":       <jax array>,
        "log10_reco_energy": <jax array>,
        "cos_reco_zenith":   <jax array>,
        "baseline_weight":   <jax array>,
        "median_energy":     <jax array>,        # only if requested
    },
    "another_dataset": { ... },
}
```

which is exactly the shape `analysis.evaluate(datasets, parameter_values)` expects.

## Tips

- The **output keys** (left side of `param_mapping`) must match what your factors and binning
  expect. Cross-check against the `required_variables` of your `Analysis`:

  ```python
  ana = pyFF.config.analysis_from_config("config.yaml")
  print(ana.required_variables)
  ```

- The `df_key` (right side) is just the column name in your DataFrame. Use whatever your
  upstream pipeline produces.
- Multiple datasets can map the same `df_key` to different output names if needed — e.g. one
  dataset's `"e_reco"` and another's `"reco_energy"` both feed `"log10_reco_energy"`.
