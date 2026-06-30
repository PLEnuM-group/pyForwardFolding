import pickle
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from .backend import Array, backend
from .binning import AbstractBinning


class AbstractFactor:
    """
    Abstract class representing a per-event factor.
    """

    def __init__(
        self,
        name: str,
        param_mapping: Optional[Dict[str, Union[str, float]]] = None,
    ):
        """
        Initialize the factor with a name and parameter mapping.

        Args:
            name (str): Identifier for the factor.
            param_mapping (dict, optional): Dictionary keyed by internal
                factor parameter name. Each value can be either:

                - a ``str``: rename — the parameter is exposed under this
                  name in the global parameter dictionary.
                - a numeric (``int`` or ``float``, but not ``bool``): fix —
                  the parameter is held at this constant value and is *not*
                  exposed in the analysis.

                Internal parameters not listed in the mapping keep their
                original name and remain exposed. If ``None`` (default), all
                factor parameters are exposed under their original names.
        """
        self.name = name
        self.param_mapping = param_mapping
        self.factor_parameters: List[str] = []

        # Split param_mapping entries into renames (str values) and fixed
        # constants (numeric values). Bools are explicitly excluded so that
        # accidental boolean entries are caught rather than silently
        # interpreted as 0/1 constants.
        if param_mapping is None:
            self._renames: Dict[str, str] = {}
            self.fixed_factor_params: Dict[str, float] = {}
        else:
            self._renames = {
                k: v for k, v in param_mapping.items() if isinstance(v, str)
            }
            self.fixed_factor_params = {
                k: float(v)
                for k, v in param_mapping.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            }

    @property
    def parameter_mapping(self) -> Dict[str, str]:
        """
        Mapping of *fittable* factor parameters (internal name -> exposed
        name). Parameters that were fixed via ``param_mapping`` (numeric
        value) are excluded; parameters not listed in the mapping default to
        identity (internal name == exposed name).
        """
        result: Dict[str, str] = {}
        for par in self.factor_parameters:
            if par in self.fixed_factor_params:
                continue  # fixed -> not exposed
            result[par] = self._renames.get(par, par)
        return result

    @property
    def exposed_parameters(self) -> List[str]:
        return list(self.parameter_mapping.values())

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Any:
        raise NotImplementedError

    def __repr__(self):
        """
        String representation of the AbstractFactor object.

        Returns:
            str: A string representation of the factor.
        """
        factor_type = type(self).__name__
        lines = []
        lines.append(f"{factor_type}: {self.name}")
        if self.factor_parameters:
            lines.append(f"  Parameters: {self.parameter_mapping}")
        return "\n".join(lines)

    def _repr_markdown_(self) -> str:
        """
        Markdown representation of the AbstractFactor object.

        Returns:
            str: A markdown representation of the factor.
        """
        return self.repr_markdown()

    def repr_markdown(
        self,
        indent_level: int = 0,
        bullet_style: str = "-",
        include_type_in_name: bool = True,
    ) -> str:
        """
        Configurable markdown representation of the AbstractFactor object as a list.

        Args:
            indent_level (int): The level of indentation (each level adds 2 spaces). Default is 0.
            bullet_style (str): Style for bullet points ("-", "*", "+"). Default is "-".
            include_type_in_name (bool): Whether to include factor type in the name. Default is True.

        Returns:
            str: A configurable markdown representation of the factor as a list.
        """
        factor_type = type(self).__name__

        indent = "  " * indent_level
        sub_indent = "  " * (indent_level + 1)
        sub_sub_indent = "  " * (indent_level + 2)

        lines = []
        if include_type_in_name:
            lines.append(f"{indent}{bullet_style} **{factor_type}** (`{self.name}`)")
        else:
            lines.append(f"{indent}{bullet_style} `{self.name}`")
            
        if self.factor_parameters:
            lines.append(f"{sub_indent}{bullet_style} Parameters:")
            for factor_param, exposed_param in self.parameter_mapping.items():
                lines.append(f"{sub_sub_indent}{bullet_style} `{factor_param}` → `{exposed_param}`")
        return "\n".join(lines)


class AbstractUnbinnedFactor(AbstractFactor):
    """
    Abstract class for factors that operate on unbinned data.
    """

    def __init__(self, name: str, param_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize the unbinned factor with a name and parameter mapping.
        Args:
            name (str): Identifier for the factor.
            param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
        """
        super().__init__(name, param_mapping)
        self.req_vars: List[str] = []

    @property
    def required_variables(self) -> List[str]:
        """
        Get the required variables for the unbinned factor.

        Returns:
            List[str]: A list of required variables.
        """
        return self.req_vars

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        raise NotImplementedError

    @classmethod
    def construct_from(
        cls: Type["AbstractUnbinnedFactor"], config: Dict[str, Any]
    ) -> "AbstractUnbinnedFactor":
        factor_type = config.get("type")
        if factor_type is None:
            raise ValueError(
                "Configuration must contain a 'type' key to identify the factor type."
            )
        factor_class = FACTORSTR_CLASS_MAPPING.get(factor_type)

        if factor_class is None:
            raise ValueError(f"Unknown factor type: {factor_type}")

        return factor_class.construct_from(config)  # type: ignore[attr-defined]

    def __repr__(self):
        """
        String representation of the AbstractUnbinnedFactor object.

        Returns:
            str: A string representation of the unbinned factor.
        """
        
        lines = super().__repr__().splitlines()  
        if self.required_variables:
            lines.append(f"  Required variables: {self.required_variables}") # type: ignore
        return "\n".join(lines)

    def _repr_markdown_(self) -> str:
        """
        Markdown representation of the AbstractUnbinnedFactor object.

        Returns:
            str: A markdown representation of the unbinned factor.
        """
        return self.repr_markdown()

    def repr_markdown(
        self,
        indent_level: int = 0,
        bullet_style: str = "-",
        include_type_in_name: bool = True,
    ) -> str:
        """
        Configurable markdown representation of the AbstractUnbinnedFactor object as a list.

        Args:
            indent_level (int): The level of indentation (each level adds 2 spaces). Default is 0.
            bullet_style (str): Style for bullet points ("-", "*", "+"). Default is "-".
            include_type_in_name (bool): Whether to include factor type in the name. Default is True.

        Returns:
            str: A configurable markdown representation of the unbinned factor as a list.
        """

        sub_indent = "  " * (indent_level + 1)
        sub_sub_indent = "  " * (indent_level + 2)

        lines = [AbstractFactor.repr_markdown(self, indent_level, bullet_style, include_type_in_name)]
        if self.required_variables:
            lines.append(f"{sub_indent}{bullet_style} Required variables:")
            for var in self.required_variables:
                lines.append(f"{sub_sub_indent}{bullet_style} `{var}`")
        return "\n".join(lines)


class AbstractBinnedFactor(AbstractFactor):
    """
    Abstract base class for factors that contribute to a binned expectation.
    This class should be inherited by specific implementations of binned factors.
    """

    def __init__(
        self,
        name: str,
        binning: AbstractBinning,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the AbstractBinnedFactor with a name, binning, and parameter mapping.

        Args:
            name (str): Identifier for the factor.
            binning (AbstractBinning): The binning strategy for this factor.
            param_mapping (Optional[Dict[str, str]]): Dictionary mapping factor parameter names to names in the parameter dictionary.
        """
        super().__init__(name, param_mapping)
        self.binning = binning

    @classmethod
    def construct_from(
        cls: Type["AbstractBinnedFactor"],
        config: Dict[str, Any],
        binning: AbstractBinning,
    ) -> "AbstractBinnedFactor":
        factor_type = config.get("type")
        if factor_type is None:
            raise ValueError(
                "Configuration must contain a 'type' key to identify the factor type."
            )
        factor_class = FACTORSTR_CLASS_MAPPING.get(factor_type)

        if factor_class is None:
            raise ValueError(f"Unknown factor type: {factor_type}")

        return factor_class.construct_from(config, binning)  # type: ignore[attr-defined]

    def repr_markdown(
        self,
        indent_level: int = 0,
        bullet_style: str = "-",
        include_type_in_name: bool = True,
    ) -> str:
        """
        Configurable markdown representation of the AbstractBinnedFactor object as a list.

        Args:
            indent_level (int): The level of indentation (each level adds 2 spaces). Default is 0.
            bullet_style (str): Style for bullet points ("-", "*", "+"). Default is "-".
            include_type_in_name (bool): Whether to include factor type in the name. Default is True.

        Returns:
            str: A configurable markdown representation of the binned factor as a list.
        """

        indent = "  " * indent_level
        sub_indent = "  " * (indent_level + 1)

        lines = [AbstractFactor.repr_markdown(self, indent_level, bullet_style, include_type_in_name)]
        lines.append(f"{indent}{bullet_style} Binning: {type(self.binning).__name__}")
        lines.append(f"{sub_indent}{bullet_style} Dimensions: `{self.binning.hist_dims}`")
        return "\n".join(lines)


def get_required_variable_values(
    factor: AbstractUnbinnedFactor,
    input_variable_values: Dict[str, Union[Array, float]],
) -> Dict[str, Union[Array, float]]:
    """
    Extract required variable values for a factor from the input dictionary.

    Args:
        factor (AbstractFactor): The factor requesting variables.
        input_variable_values (dict): Dictionary containing all available input variables.

    Returns:
        dict: Dictionary containing only the required variables for the factor.
    """
    req_vars = factor.required_variables
    return {var: input_variable_values[var] for var in req_vars}


def get_parameter_values(
    factor: AbstractFactor, parameter_dict: Dict[str, float]
) -> Dict[str, float]:
    """
    Extract parameter values for a factor from the parameter dictionary.

    Args:
        factor (AbstractFactor): The factor requesting variables.
        parameter_dict (dict): Dictionary mapping parameter names to values.

    Returns:
        dict: Dictionary containing only the exposed variables for the factor.
    """

    par_mapping = factor.parameter_mapping
    parameter_values = {
        factor_var_name: parameter_dict[par_name]
        for factor_var_name, par_name in par_mapping.items()
    }
    # Inject factor-level fixed parameters so evaluate() still sees them.
    parameter_values.update(factor.fixed_factor_params)
    return parameter_values


class PowerLawFlux(AbstractUnbinnedFactor):
    """
    Factor that applies a power law flux model.

    Parameters required by this factor are: `flux_norm` and `spectral_index`.
    Variables required by this factor are: `true_energy`.

    Args:
        name (str): Identifier for the factor.
        pivot_energy (float): Reference energy for the power law.
        baseline_norm (float): Baseline normalization factor.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        pivot_energy: float,
        baseline_norm: float,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.pivot_energy = pivot_energy
        self.baseline_norm = baseline_norm

        self.factor_parameters: List[str] = ["flux_norm", "spectral_index"]
        self.req_vars: List[str] = ["true_energy"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "PowerLawFlux":
        param_mapping = config.get("param_mapping", None)
        return PowerLawFlux(
            name=config["name"],
            pivot_energy=config["pivot_energy"],
            baseline_norm=config["baseline_norm"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        true_energy = input_values["true_energy"]
        flux_norm = exposed_values["flux_norm"]
        spectral_index = exposed_values["spectral_index"]

        return (
            flux_norm
            * self.baseline_norm
            * backend.power(true_energy / self.pivot_energy, -spectral_index)
        )

class BrokenPowerLawFlux(AbstractUnbinnedFactor):
    """
    Factor that applies a broken power law flux model.

    Parameters required by this factor are: `flux_norm`, `spectral_index_1`, `spectral_index_2` and `logEbreak`.
    Variables required by this factor are: `true_energy`.

    Args:
        name (str): Identifier for the factor.
        pivot_energy (float): Reference energy for the power law.
        baseline_norm (float): Baseline normalization factor.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        pivot_energy: float,
        baseline_norm: float,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.pivot_energy = pivot_energy
        self.baseline_norm = baseline_norm

        self.factor_parameters: List[str] = ["flux_norm", "spectral_index_1", "spectral_index_2", "logEbreak"]
        self.req_vars: List[str] = ["true_energy"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "BrokenPowerLawFlux":
        param_mapping = config.get("param_mapping", None)
        return BrokenPowerLawFlux(
            name=config["name"],
            pivot_energy=config["pivot_energy"],
            baseline_norm=config["baseline_norm"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        true_energy = input_values["true_energy"]
        flux_norm = exposed_values["flux_norm"]
        spectral_index_1 = exposed_values["spectral_index_1"]
        spectral_index_2 = exposed_values["spectral_index_2"]
        Ebreak = 10**exposed_values["logEbreak"]

        flux = flux_norm

        #transform norm to  give flux at pivot energy
        flux *= backend.where(
            self.pivot_energy < Ebreak,
            (self.pivot_energy/Ebreak)**spectral_index_1,
            (self.pivot_energy/Ebreak)**spectral_index_2
                              )
        
        #calculate flux
        flux *= backend.where(
            true_energy < Ebreak,
            (true_energy/Ebreak)**(-spectral_index_1),
            (true_energy/Ebreak)**(-spectral_index_2),
        )

        return flux * self.baseline_norm

class GaisserZenithFactor(AbstractUnbinnedFactor):
    """
    Factor that applies the zenith-dependent piece of the Gaisser atmospheric
    neutrino flux parametrization, *excluding* the E^{-gamma} baseline shape.

    Intended to be multiplied with a separate spectral factor (e.g. a spline
    or `PowerLawFlux`) and a `FluxNorm` factor. This factor only contributes
    the pi/K bracket

        B(E, theta) = 1 / (1 + a * E * cos(theta*) / eps_pi)
                    + R_K * 1 / (1 + b * E * cos(theta*) / eps_K)

    normalized so that B(pivot_energy, vertical) = 1. Here `cos(theta*)` is
    the Chirkin (2004) Earth-curvature-corrected effective cosine (if
    `earth_curvature=True`), or plain `cos(theta)` otherwise. The formula
    is applied to the *atmospheric* zenith angle, which is symmetric in
    up/down, so the absolute value of `cos(true_zenith)` is used
    internally.

    Physical effect: the bracket is ~constant at low energies and adds an
    additional power of E that depends on `cos(theta*)` above the critical
    energies. Horizontal showers transition later, producing a relatively
    harder spectrum at the horizon (the "secant-theta" enhancement).

    Parameters required by this factor are: `kaon_pion_ratio`.
    Variables required by this factor are: `true_energy` and `true_zenith`
    (the zenith angle in radians).

    Args:
        name (str): Identifier for the factor.
        pivot_energy (float): Reference energy [GeV] at which the bracket is
            normalized to 1 (at vertical incidence). This factor evaluates
            to 1 at (pivot_energy, vertical).
        epsilon_pi (float): Pion critical energy [GeV]. Default 115 GeV.
        epsilon_K (float): Kaon critical energy [GeV]. Default 850 GeV.
        a_pi (float): Pion interaction coefficient inside the pion term.
            Default 1.0.
        b_K (float): Kaon interaction coefficient inside the kaon term.
            Default 1.0.
        earth_curvature (bool): If True, apply the Chirkin (2004) effective
            cosine to prevent the unphysical sec(theta) divergence at the
            horizon. Default True.
        param_mapping (dict): Dictionary mapping factor parameter names to
            names in the parameter dictionary.
    """

    # Chirkin (2004) parametrization constants for cos(theta*)
    _CHIRKIN_P1 = 0.102573
    _CHIRKIN_P2 = -0.068287
    _CHIRKIN_P3 = 0.958633
    _CHIRKIN_P4 = 0.0407253
    _CHIRKIN_P5 = 0.817285

    def __init__(
        self,
        name: str,
        pivot_energy: float,
        epsilon_pi: float = 115.0,
        epsilon_K: float = 850.0,
        a_pi: float = 1.0,
        b_K: float = 1.0,
        earth_curvature: bool = True,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.pivot_energy = pivot_energy
        self.epsilon_pi = epsilon_pi
        self.epsilon_K = epsilon_K
        self.a_pi = a_pi
        self.b_K = b_K
        self.earth_curvature = earth_curvature

        self.factor_parameters: List[str] = ["kaon_pion_ratio"]
        self.req_vars: List[str] = ["true_energy", "true_zenith"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "GaisserZenithFactor":
        param_mapping = config.get("param_mapping", None)
        return GaisserZenithFactor(
            name=config["name"],
            pivot_energy=config["pivot_energy"],
            epsilon_pi=config.get("epsilon_pi", 115.0),
            epsilon_K=config.get("epsilon_K", 850.0),
            a_pi=config.get("a_pi", 1.0),
            b_K=config.get("b_K", 1.0),
            earth_curvature=config.get("earth_curvature", True),
            param_mapping=param_mapping,
        )

    def _chirkin_cos_theta_star(self, cos_theta: Any) -> Any:
        """
        Chirkin (2004) Earth-curvature corrected effective cosine.

        At vertical (cos_theta = 1) returns ~0.991; at horizon (cos_theta = 0)
        returns ~0.105, replacing the unphysical sec(theta) divergence of the
        flat-Earth approximation with a finite slant depth.
        """
        p1, p2, p3 = self._CHIRKIN_P1, self._CHIRKIN_P2, self._CHIRKIN_P3
        p4, p5 = self._CHIRKIN_P4, self._CHIRKIN_P5
        return backend.sqrt(
            cos_theta * cos_theta
            + p1 * p1
            + p2 * backend.power(cos_theta, p3)
            + p4 * backend.power(cos_theta, p5)
        )

    def _effective_cos_theta(self, cos_theta: Any) -> Any:
        if self.earth_curvature:
            return self._chirkin_cos_theta_star(cos_theta)
        return cos_theta

    def _bracket(
        self, energy: Any, cos_theta_star: Any, kaon_pion_ratio: Any
    ) -> Any:
        """Gaisser bracket [1/(1+a*E*cos*/eps_pi) + R*1/(1+b*E*cos*/eps_K)]."""
        pi_term = 1.0 / (
            1.0 + self.a_pi * energy * cos_theta_star / self.epsilon_pi
        )
        K_term = 1.0 / (
            1.0 + self.b_K * energy * cos_theta_star / self.epsilon_K
        )
        return pi_term + kaon_pion_ratio * K_term

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)

        true_energy = input_values["true_energy"]
        true_zenith = input_values["true_zenith"]
        kaon_pion_ratio = exposed_values["kaon_pion_ratio"]

        # Atmospheric flux is symmetric in up/down: use |cos(theta)| so the
        # parametrization (defined on downgoing) also applies to upgoing
        # events, which are produced in the opposite-hemisphere atmosphere.
        cos_theta = backend.abs(backend.cos(true_zenith))
        cos_theta_star = self._effective_cos_theta(cos_theta)

        # Per-event bracket
        bracket = self._bracket(true_energy, cos_theta_star, kaon_pion_ratio)

        # Normalize at (pivot_energy, vertical) using the same earth_curvature
        # setting, so the factor evaluates to 1 at the reference point
        # regardless of toggle.
        cos_theta_star_ref = self._effective_cos_theta(1.0)
        bracket_ref = self._bracket(
            self.pivot_energy, cos_theta_star_ref, kaon_pion_ratio
        )

        return bracket / bracket_ref


class FlavorRatio(AbstractUnbinnedFactor):
    """
    Factor that applies a power law flux model and scales each neutrino flavor

    Parameters required by this factor are: `flux_norm` and `spectral_index`.
    Variables required by this factor are: `true_energy`.

    Args:
        name (str): Identifier for the factor.
        pivot_energy (float): Reference energy for the power law.
        baseline_norm (float): Baseline normalization factor.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.factor_parameters: List[str] = ["nue_ratio","nutau_ratio"]
        self.req_vars: List[str] = ["true_type"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "FlavorRatio":
        param_mapping = config.get("param_mapping", None)
        return FlavorRatio(
            name=config["name"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        true_type = input_values["true_type"]
        nue_ratio = exposed_values["nue_ratio"]
        nutau_ratio = exposed_values["nutau_ratio"]

        ratios = backend.zeros(true_type.shape)


        nue_mask = abs(true_type) == 12
        numu_mask = abs(true_type) == 14
        nutau_mask = abs(true_type) == 16

        ratios = backend.where(nue_mask,nue_ratio,ratios)
        ratios = backend.where(numu_mask,1.,ratios)
        ratios = backend.where(nutau_mask,nutau_ratio,ratios)

        
        return ratios

class FluxNorm(AbstractUnbinnedFactor):
    """
    Factor that applies a simple flux normalization.

    Parameters required by this factor are: `flux_norm`.
    
    Args:
        name (str): Identifier for the factor.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(self, name: str, param_mapping: Optional[Dict[str, str]] = None):
        super().__init__(name, param_mapping)

        self.factor_parameters = ["flux_norm"]
        self.req_vars = []

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "FluxNorm":
        param_mapping = config.get("param_mapping", None)
        return FluxNorm(
            name=config["name"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        exposed_values = get_parameter_values(self, parameter_values)
        flux_norm = exposed_values["flux_norm"]

        return backend.array(flux_norm)



class SegmentedPlane(AbstractUnbinnedFactor):
    """
    Factor that applies a segment-wise delta gamma scaling and a flux norm to a precalculated Galactic Plane weight.

    Parameters required by this factor are: `segmented_norm_{i}` and `segmented_gamma_{i}` where i corresponds to each segment index.
    Variables required by this factor are: `true_energy`, `true_lat` and `true_lon`.

    Args:
        name (str): Identifier for the factor.
        reference_energy (float): Reference energy for scaling.
        baseline_flux (float): Overall scaling of the factor.
        segment_edges (list): List of all segment edges.
        height (float): Height cut around the galactic horizon.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name,
        param_mapping: Optional[Dict[str, str]] = None,
        reference_energy: float = 1e3,
        baseline_flux: float = 1.0,
        segment_edges: list = [0.],
        height: float = 3.14159265359,
    ):
        super().__init__(name, param_mapping)
        self.reference_energy = reference_energy
        self.baseline_flux = baseline_flux
        self.segment_edges = segment_edges
        self.num_segments = len(segment_edges)
        self.height = height

        self.factor_parameters = [f"galactic_norm_{i}" for i in range(self.num_segments)]
        self.factor_parameters += [f"galactic_gamma_{i}" for i in range(self.num_segments)]
        self.req_vars = ["true_energy", "true_lat", "true_lon"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "SegmentedPlane":
        param_mapping = config.get("param_mapping", None)
        return SegmentedPlane(
            name=config["name"],
            reference_energy=config["reference_energy"],
            baseline_flux=config["baseline_flux"],
            segment_edges=config["segment_edges"],
            height=config["height"],
            param_mapping=param_mapping,
        )

    def evaluate(self, input_variables, parameter_values):
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)

        norms = backend.asarray([exposed_values[f"galactic_norm_{i}"] for i in range(self.num_segments)])
        gammas = backend.asarray([exposed_values[f"galactic_gamma_{i}"] for i in range(self.num_segments)])

        true_energy = input_values["true_energy"]
        true_lat = input_values["true_lat"]
        true_lon = input_values["true_lon"]

        # Get segment number for each event
        edges = backend.sort(backend.asarray(self.segment_edges))
        segments = backend.searchsorted(edges, true_lon, side="right") - 1
        segments = backend.mod(segments, edges.shape[0]).astype(int)
        
        norm = norms[segments]
        gamma = gammas[segments]

        # check whether events are in plane or outside
        in_plane = backend.abs(true_lat) <= self.height

        weight = (
            norm
            * self.baseline_flux
            * backend.power(true_energy / self.reference_energy, -gamma)
        )

        weight = backend.where(in_plane, weight, 0.0)
        return weight



class GalacticPlaneBox(AbstractUnbinnedFactor):
    """
    Box-shaped analytical galactic-plane selector.

    Returns 1.0 for events inside the latitude band |true_lat| <= height
    (in radians) and 0.0 outside. Pure geometry — no fittable parameters
    and no longitude dependence (the box is a band in latitude only,
    spanning all longitudes).

    Intended to be multiplied with a spectral factor (e.g. `PowerLawFlux`
    or a spline) and a `FluxNorm` to model a galactic-plane flux
    component. Edges are hard; this introduces a non-differentiability in
    `true_lat` but `true_lat` is per-event input data, not a fit
    parameter, so gradient-based fits are unaffected.

    No parameters required by this factor.
    Variables required by this factor are: `true_lat` (in radians).

    Args:
        name (str): Identifier for the factor.
        height (float): Latitude half-width of the box in radians. Events
            with |true_lat| <= height return 1.0, others return 0.0.
        param_mapping (dict): Dictionary mapping factor parameter names
            to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        height: float,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)
        self.height = height
        self.factor_parameters: List[str] = []
        self.req_vars: List[str] = ["true_lat"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "GalacticPlaneBox":
        param_mapping = config.get("param_mapping", None)
        return GalacticPlaneBox(
            name=config["name"],
            height=config["height"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        true_lat = input_values["true_lat"]
        in_plane = backend.abs(true_lat) <= self.height
        return backend.where(in_plane, 1.0, 0.0)


class SnowstormGauss(AbstractUnbinnedFactor):
    """
    Factor that implements a Gaussian reweighting scheme for systematic uncertainty modeling.

    Parameters required by this factor are: `scale`.
    Variables required by this factor are specified by `req_variable_name`.

    Args:
        name (str): Identifier for the factor.
        sys_gauss_width (float): Width of the Gaussian distribution.
        sys_sim_bounds (tuple): Bounds for the simulated parameter space (min, max).
        req_variable_name (str): Name of the required variable for reweighting.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name,
        sys_gauss_width,
        sys_sim_bounds,
        req_variable_name,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.sys_gauss_width = sys_gauss_width
        self.sys_sim_bounds = sys_sim_bounds
        self.req_vars = [req_variable_name]
        self.factor_parameters = ["scale"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "SnowstormGauss":
        param_mapping = config.get("param_mapping", None)
        return SnowstormGauss(
            name=config["name"],
            sys_gauss_width=config["sys_gauss_width"],
            sys_sim_bounds=tuple(config["sys_sim_bounds"]),
            req_variable_name=config["req_variable_name"],
            param_mapping=param_mapping,
        )

    def evaluate(self, input_variables, parameter_values):
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        sys_value = exposed_values["scale"]
        sys_par = input_values[self.req_vars[0]]

        return (
            backend.gauss_pdf(sys_par, sys_value, self.sys_gauss_width)
            / backend.gauss_cdf(self.sys_sim_bounds[1], sys_value, self.sys_gauss_width)
        ) / backend.uniform_pdf(sys_par, self.sys_sim_bounds[0], self.sys_sim_bounds[1])


class DeltaGamma(AbstractUnbinnedFactor):
    """
    Factor that applies a delta gamma scaling.

    Parameters required by this factor are: `delta_gamma`.
    Variables required by this factor are: `true_energy` and `median_energy`.

    Args:
        name (str): Identifier for the factor.
        reference_energy (float): Reference energy for scaling.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name,
        param_mapping: Optional[Dict[str, str]] = None,
        reference_energy: float = 1.0,
    ):
        super().__init__(name, param_mapping)
        self.reference_energy = reference_energy

        self.factor_parameters = ["delta_gamma"]
        self.req_vars = ["true_energy"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "DeltaGamma":
        param_mapping = config.get("param_mapping", None)
        return DeltaGamma(
            name=config["name"],
            reference_energy=config["reference_energy"],
            param_mapping=param_mapping,
        )

    def evaluate(self, input_variables, parameter_values):
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)

        delta_gamma = exposed_values["delta_gamma"]
        true_energy = input_values["true_energy"]
        # median_energy = input_values["median_energy"]
        return backend.power(true_energy / self.reference_energy, -delta_gamma)


class ModelInterpolator(AbstractUnbinnedFactor):
    """
    Interpolation between two models.

    Parameters required by this factor are: `lambda_int`.
    Variables required by this factor are: `baseline_weight` and `alternative_weight`.

    Args:
        name (str): Identifier for the factor.
        baseline_weight (str): Name of the baseline weight variable.
        alternative_weight (str): Name of the alternative weight variable.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        baseline_weight: str,
        alternative_weight: str,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)
        self.base_key = baseline_weight
        self.alt_key = alternative_weight
        self.req_vars = [self.base_key, self.alt_key]
        self.factor_parameters: List[str] = ["lambda_int"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "ModelInterpolator":
        param_mapping = config.get("param_mapping", None)
        return ModelInterpolator(
            name=config["name"],
            baseline_weight=config["baseline_weight"],
            alternative_weight=config["alternative_weight"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, float | Array],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        baseline_weight = input_values[self.base_key]
        alternative_weight = input_values[self.alt_key]
        lambda_int = exposed_values["lambda_int"]

        # If baseline weight is 0 also return 1
        sanitized_baseline_weight = backend.where(
            baseline_weight == 0, 1, baseline_weight
        )

        log_sanitized_baseline_weight = backend.log(sanitized_baseline_weight)
        log_alternative_weight = backend.log(alternative_weight)

        result = backend.where(
            baseline_weight == 0,
            1,
            (1 - lambda_int)
            + lambda_int
            * backend.exp(log_alternative_weight - log_sanitized_baseline_weight),
        )

        return result


class GradientReweight(AbstractUnbinnedFactor):
    """
    Gradient reweight application. (e.g barr parameters)
    Requires precalculated gradients.

    Parameters required by this factor are the keys of `gradient_key_mapping`.
    Variables required by this factor are the values of `gradient_key_mapping` and `baseline_weight`.

    Args:
        name (str): Identifier for the factor.
        gradient_key_mapping (dict): Dictionary mapping exposed variable names to gradient variable names.
        baseline_weight (str): Name of the baseline weight variable.
    """

    def __init__(
        self,
        name: str,
        gradient_key_mapping: Dict[str, str],
        baseline_weight: str,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)
        self.baseline_weight = baseline_weight
        self.grad_key_map = gradient_key_mapping
        self.req_vars = list(self.grad_key_map.values()) + [self.baseline_weight]
        self.factor_parameters = list(self.grad_key_map.keys())

        self._eps = 1e-36

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "GradientReweight":
        param_mapping = config.get("param_mapping", None)
        return GradientReweight(
            name=config["name"],
            gradient_key_mapping=config["gradient_key_mapping"],
            baseline_weight=config["baseline_weight"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, float | Array],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        baseline = input_values.get(self.baseline_weight, 1.)
        reweight = backend.array(baseline)
        for par in self.factor_parameters:
            par_gradient = input_variables[self.grad_key_map[par]]
            par_value = exposed_values[par]
            base_value = self.base_values.get(par, 0)
            reweight += (base_value - par_value) * par_gradient

        safe_baseline = backend.where(baseline > self._eps, baseline, backend.zeros(baseline.shape) + 1)
        result = reweight / safe_baseline
        return backend.where(baseline > self._eps, result, backend.zeros(result.shape))


class ClassifierGradientReweight(AbstractUnbinnedFactor):
    """
    Per-event reweighting using classifier-fitted polynomial coefficients
    in log-weight space. Implements:

        r_j(alpha) = exp( sum_{param,p} g_{param,p,j} * (alpha_param - alpha_nom_param)^p )

    The g columns are expected to be present in the dataset, written by gradients.py
    with the naming convention g_{param}_{order} (e.g. g_abs_1, g_qeff_2).

    Parameters required by this factor are the unique parameter names in `poly_features`.
    Variables required by this factor are the g columns derived from `poly_features`.

    Args:
        name (str): Identifier for the factor.
        poly_features (list): List of (param, order) tuples matching those used in training,
                              e.g. [("abs", 1), ("abs", 2), ("qeff", 1), ("qeff", 2)].
        nominal_values (dict): Nominal systematic values, e.g. {"abs": 1.0, "qeff": 1.0}.
        gradient_col_template (str): Format string for gradient column names.
                                     Defaults to "g_{param}_{order}".
        param_mapping (dict, optional): Parameter name remapping passed to base class.
    """

    def __init__(
        self,
        name: str,
        poly_features: List[Tuple[str, int]],
        nominal_values: Dict[str, float],
        gradient_col_template: str = "g_{param}_{order}",
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)
        self.poly_features          = poly_features
        self.nominal_values         = nominal_values
        self.gradient_col_template  = gradient_col_template

        # One input variable per polynomial term (the g columns in the dataset)
        self.req_vars = [
            gradient_col_template.format(param=param, order=order)
            for param, order in poly_features
        ]
        # One free parameter per unique systematic (duplicates collapsed)
        self.factor_parameters = list(dict.fromkeys(param for param, _ in poly_features))

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "ClassifierGradientReweight":
        return cls(
            name                   = config["name"],
            poly_features          = [tuple(pf) for pf in config["poly_features"]],
            nominal_values         = config["nominal_values"],
            gradient_col_template  = config.get("gradient_col_template", "g_{param}_{order}"),
            param_mapping          = config.get("param_mapping", None),
        )

    def evaluate(
        self,
        input_variables: Dict[str, float | Array],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values   = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)

        log_r = backend.zeros(
            input_values[self.req_vars[0]].shape
        )
        for param, order in self.poly_features:
            col         = self.gradient_col_template.format(param=param, order=order)
            g_col       = input_values[col]
            delta_alpha = exposed_values[param] - self.nominal_values[param]
            log_r       = log_r + (delta_alpha ** order) * g_col

        return backend.exp(log_r)

class VetoThreshold(AbstractUnbinnedFactor):
    """
    Changes the atm. passing fraction according to a second-order expansion of
    log10(splined_passing_fraction)

    Parameters required by this factor are: `e_threshold`.
    Variables required by this factor are the coefficients of the expansion.
    """

    def __init__(
        self,
        name,
        threshold_a,
        threshold_b,
        threshold_c,
        rescale_energy,
        anchor_energy,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Read fir coefficients as well as anchor energy [GeV]

        Args:
            threshold_: coefficients of second-order expansion
            anchor_energy: energy at which log10(PF) was expanded
            rescale_energy: scale 10**(fit parameter) to energy # TODO
        """

        super().__init__(name, param_mapping)

        self.a = threshold_a
        self.b = threshold_b
        self.c = threshold_c
        self.e_rescale = rescale_energy
        self.e_anchor = anchor_energy
        self.req_vars = [self.a, self.b, self.c]
        self.factor_parameters: List[str] = ["e_threshold"]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "VetoThreshold":
        param_mapping = config.get("param_mapping", None)
        return VetoThreshold(
            name=config["name"],
            threshold_a=config["threshold_a"],
            threshold_b=config["threshold_b"],
            threshold_c=config["threshold_c"],
            rescale_energy=config["rescale_energy"],
            anchor_energy=config["anchor_energy"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, float | Array],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        exposed_values = get_parameter_values(self, parameter_values)
        e_threshold = exposed_values["e_threshold"]
        a = input_values[self.a]
        b = input_values[self.b]
        c = input_values[self.c]
        # parameter value to original energy scale, minus point at which
        # expansion was done
        # parameter itself transformed to log10:
        # e_t is log_10(energy threshold / 100 GeV)
        e = self.e_rescale * backend.exp(backend.log(10) * e_threshold) - self.e_anchor
        # i.e. energy threshold in [5 GeV, 3 TeV] = e_t in [-1.301, 1.477]

        # second order expansion from fit coefficients
        log_pf = a + b * e + c * e * e
        # expansion is in log10(passing_fraction)
        reweight = backend.exp(backend.log(10) * log_pf)
        # atm. weights are multiplied by passing fraction
        return reweight

class FixedVeto(AbstractUnbinnedFactor):
    """
    Applies a fixed per-event passing fraction to the component weights.

    No parameters required.
    Variables required are the per-event passing fractions.
    
    Args:
        name (str): Identifier for the factor.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(self, 
                 name: str, 
                 passing_fraction: str,
                 param_mapping: Optional[Dict[str, str]] = None):
        super().__init__(name, param_mapping)

        self.factor_parameters = []
        self.pf_key = passing_fraction
        self.req_vars = [self.pf_key]


    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "FixedVeto":
        param_mapping = config.get("param_mapping", None)
        return FixedVeto(
            name=config["name"],
            passing_fraction=config["passing_fraction"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, Union[Array, float]],
        parameter_values: Dict[str, float],
    ) -> Array:
        
        input_values = get_required_variable_values(self, input_variables)
        pf = input_values[self.pf_key]

        return backend.array(pf)

class SoftCut(AbstractUnbinnedFactor):
    """
    Factor for a soft cut on a specific variable.

    Parameters required by this factor are: `soft_cut`.
    Variables required by this factor are specified by `cut_variable`.
    
    Args:
        name (str): Identifier for the factor.
        cut_variable (str): Name of the variable to apply the soft cut on.
        slope (float): Slope of the sigmoid function defining the softness of the cut.
        param_mapping (dict): Dictionary mapping factor parameter names to names in the parameter dictionary.

    """

    def __init__(
        self,
        name: str,
        cut_variable: str,
        slope: float,
        cut_value: float,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, param_mapping)

        self.cut_variable = cut_variable
        self.slope = slope
        self.cut_value = cut_value
        self.factor_parameters = []#["soft_cut"]
        self.req_vars = [self.cut_variable]

    @classmethod
    def construct_from(cls, config: Dict[str, Any]) -> "SoftCut":
        param_mapping = config.get("param_mapping", None)
        return SoftCut(
            name=config["name"],
            cut_variable=config["cut_variable"],
            slope=config["slope"],
            cut_value=config["cut_value"],
            param_mapping=param_mapping,
        )

    def evaluate(
        self,
        input_variables: Dict[str, float | Array],
        parameter_values: Dict[str, float],
    ) -> Array:
        input_values = get_required_variable_values(self, input_variables)
        #exposed_values = get_parameter_values(self, parameter_values)

        cut_var = backend.asarray(input_values[self.cut_variable])
        cut_val = self.cut_value#exposed_values["soft_cut"]

        return backend.sigmoid(self.slope * (cut_var - cut_val))


class PerBinPolynomial(AbstractBinnedFactor):
    """
    Factor that applies a polynomial reweighting per bin.
    The polynomial coefficients are provided as a list of lists,
    where each inner list corresponds to a bin and contains the coefficients
    for the polynomial in that bin.

    Parameters required by this factor are: `scale`.

    Args:
        name (str): Identifier for the factor.
        binning (AbstractBinning): Binning object for the factor.
        coefficients (List[List[float]]): List of lists containing polynomial coefficients for each bin.
        param_mapping (Optional[Dict[str, str]]): Dictionary mapping factor parameter names to names in the parameter dictionary.
    """

    def __init__(
        self,
        name: str,
        binning: AbstractBinning,
        coefficients: Array,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, binning, param_mapping)

        if coefficients.shape[0] not in [2, 3]:
            raise ValueError(
                "PerBinPolynomial only supports up to 2nd and 3rd order polynomials."
            )

        if self.binning.hist_dims != coefficients.shape[1:]:
            raise ValueError(
                f"Shape of coefficients {coefficients.shape[1:]} does not match binning dimensions {self.binning.hist_dims}."
            )

        self.coefficients = coefficients
        self.factor_parameters = ["scale"]

    @classmethod
    def construct_from(
        cls, config: Dict[str, Any], binning: AbstractBinning
    ) -> "PerBinPolynomial":
        
        coeffs_file = config.get("coefficients_file", None)
        if coeffs_file is not None:
            with open(coeffs_file, "rb") as f:
                coefficients = pickle.load(f)
        else:
            raise ValueError(
                "Configuration must contain 'coefficients_file' key to load polynomial coefficients."
            )
        
        return PerBinPolynomial(
            name=config["name"],
            binning=binning,
            coefficients=coefficients,
            param_mapping=config.get("param_mapping", None),
        )

    def evaluate(
        self, input_variables, parameter_values: Dict[str, float]
    ) -> Tuple[Array, Optional[Array]]:
        """
        Evaluate the polynomial reweighting for each bin based on the input variables.

        Args:
            input_variables (dict): Dictionary containing input variables.
            parameter_values (dict): Dictionary containing parameter values.

        Returns:
            Tuple[Array, Array]: Mean and variance of the polynomial reweighting per bin.
        """
        
        exposed_values = get_parameter_values(self, parameter_values)
        scale = exposed_values["scale"]


        if self.coefficients.shape[0] == 2:
            mu_add = scale * self.coefficients[0] + self.coefficients[1]

        elif self.coefficients.shape[0] == 3:
            mu_add = (
                scale**2 * self.coefficients[0]
                + scale * self.coefficients[1] 
                + self.coefficients[2]
            )
        else:
            raise RuntimeError(
                "PerBinPolynomial only supports 2nd and 3rd order polynomials")
        
        return mu_add, None

class SnowStormGradient(AbstractBinnedFactor):
    """
    Factor that applies a systematic parameter gradient.
    Is applied additive to each detector histogram.
    """

    def __init__(
        self,
        name: str,
        binning: AbstractBinning,
        parameters: List[str],
        gradient_names: List[str],
        default: List[float],
        split_values: List[float],
        gradient_pickle: str,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Parameters
        ----------
        name : str
            Name of the factor
        binning : AbstractBinning
            Binning object for the factor
        parameters : list
            List of parameter names
        gradient_names : list
            List of gradient dictionary keys for each parameter
        default : list
            List of default parameter values
        split_values : list
            List of split values for each parameter
        gradient_pickle : str
            Path to pickle file containing the gradients

        """
        super().__init__(name, binning, param_mapping)

        self.defaults = default
        self.split_values = split_values
        self.gradient_names = gradient_names

        with open(gradient_pickle, "rb") as f:
            self.gradients = pickle.load(f)

        self.factor_parameters = parameters

        ndim_grads = [len(be) - 1 for be in self.gradients["binning"]]

        for gname in self.gradient_names:
            grad = self.gradients[gname]["gradient"]
            if grad.shape != tuple(ndim_grads):
                raise ValueError(
                   f"Gradient '{gname}' has shape {grad.shape}, expected {ndim_grads}"
                )

        if list(self.binning.hist_dims) != ndim_grads:
            raise ValueError(
                f"Mismatch between binning dimensions ({self.binning.hist_dims}) and gradient dimensions ({ndim_grads})"
            )

        # TODO: check if bin edges are compatible?

    @classmethod
    def construct_from(
        cls, config: Dict[str, Any], binning: AbstractBinning
    ) -> "SnowStormGradient":
        return SnowStormGradient(
            name=config["name"],
            binning=binning,
            parameters=config["parameters"],
            gradient_names=config["gradient_names"],
            default=config["default"],
            split_values=config["split_values"],
            gradient_pickle=config["gradient_pickle"],
            param_mapping=config.get("param_mapping", None),
        )

    def evaluate(
        self, input_variables, parameter_values: Dict[str, float]
    ) -> Tuple[Array, Array]:
        """
        Evaluate the systematic parameter gradient for the given
        detector configuration and the given exposed variables.

        """

        t_gradients = float(self.gradients["livetime"])
        exposed_values = get_parameter_values(self, parameter_values)

        # calculate variation of systematic parameters w.r.t. split
        #   value in order to correctly relate to the gradient dict.
        #   Overall parameter shifts are taken into account here so
        #   that gradients are applied w.r.t. their split value
        #   but the fit parameter itself corresponds to the shifted value
        mu_add = backend.zeros(self.binning.hist_dims)
        ssq_add = backend.zeros(self.binning.hist_dims)

        for i, sys_par in enumerate(self.exposed_parameters):
            sys_val = exposed_values[sys_par]
            gradient: Array = self.gradients[self.gradient_names[i]]

            mu_add += (sys_val - self.split_values[i]) * gradient["gradient"]
            ssq_add += (
                (sys_val - self.split_values[i]) * gradient["gradient_error"]
            ) ** 2

        return mu_add / t_gradients, ssq_add / t_gradients**2


class ScaledTemplate(AbstractBinnedFactor):
    def __init__(
        self,
        name: str,
        binning: AbstractBinning,
        template_file: str,
        param_mapping: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, binning, param_mapping)

        with open(template_file, "rb") as f:
            self.template = pickle.load(f)

        self.factor_parameters = ["template_norm"]

    @classmethod
    def construct_from(
        cls, config: Dict[str, Any], binning: AbstractBinning
    ) -> "ScaledTemplate":
        return ScaledTemplate(
            name=config["name"],
            binning=binning,
            template_file=config["template_file"],
            param_mapping=config.get("param_mapping", None),
        )

    def evaluate(
        self, input_variables, parameter_values: Dict[str, float]
    ) -> Tuple[Array, Optional[Array]]:
        exposed_values = get_parameter_values(self, parameter_values)
        template_norm = exposed_values["template_norm"]

        # TODO: compare template binning with configured one
        if "template_fluctuation" in self.template:
            template_fluct = (
                self.template["template_fluctuation"] * template_norm
            ) ** 2
            template_fluct = template_fluct.reshape(self.binning.hist_dims)
        else:
            template_fluct = None
        return (self.template["template"] * template_norm).reshape(
            self.binning.hist_dims
        ), template_fluct


FACTORSTR_CLASS_MAPPING = {
    "PowerLawFlux": PowerLawFlux,
    "BrokenPowerLawFlux": BrokenPowerLawFlux,
    "GaisserZenithFactor": GaisserZenithFactor,
    "FlavorRatio": FlavorRatio,
    "FluxNorm": FluxNorm,
    "SegmentedPlane": SegmentedPlane,
    "GalacticPlaneBox": GalacticPlaneBox,
    "SnowstormGauss": SnowstormGauss,
    "DeltaGamma": DeltaGamma,
    "GradientReweight": GradientReweight,
    "ClassifierGradientReweight": ClassifierGradientReweight,
    "ModelInterpolator": ModelInterpolator,
    "VetoThreshold": VetoThreshold,
    "FixedVeto": FixedVeto,
    "SoftCut": SoftCut,
    "SnowStormGradient": SnowStormGradient,
    "ScaledTemplate": ScaledTemplate,
    "PerBinPolynomial": PerBinPolynomial,
}
