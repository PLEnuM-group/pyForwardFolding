# `pyForwardFolding.minimizer`

`ScipyMinimizer` (L-BFGS-B via SciPy) and `MinuitMinimizer` (MIGRAD via iMinuit) implementations of
`AbstractMinimizer`. Both wrap an `AbstractLikelihood` and flatten the parameter dictionary for the
underlying solver.

::: pyForwardFolding.minimizer
