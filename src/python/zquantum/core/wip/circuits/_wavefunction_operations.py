from dataclasses import dataclass
from numbers import Number

from ._gates import _sub_symbols, Parameter
from typing import Tuple, Sequence
import numpy as np


@dataclass(frozen=True)
class MultiPhaseOperation:
    """Operation applying distinct phase to each wavefunction component.

    MultiPhaseOperation with parameters theta_1, theta_2, .... theta_2^N,
    transforms a N qubit wavefunction (psi_1, psi_2, ..., psi_2^N)
    into (exp(i theta_1)psi_1, exp(i theta_2) psi_2, ..., exp(i theta_2^N) psi_2^N).
    """

    params: Tuple[Parameter, ...]

    def __post_init__(self):
        if any(isinstance(param, Number) and param.imag != 0 for param in self.params):
            raise ValueError("MultiPhaseOperation supports only real parameters.")

    @property
    def qubit_indices(self) -> Tuple[int, ...]:
        n_qubits = int(np.log2(len(self.params)))
        return tuple(range(n_qubits))

    def bind(self, symbols_map) -> "MultiPhaseOperation":
        return self.replace_params(
            tuple(_sub_symbols(param, symbols_map) for param in self.params)
        )

    def replace_params(
        self, new_params: Tuple[Parameter, ...]
    ) -> "MultiPhaseOperation":
        return MultiPhaseOperation(new_params)

    def apply(self, wavefunction: Sequence[Parameter]) -> Sequence[Parameter]:
        if len(wavefunction) != len(self.params):
            raise ValueError(
                f"MultiPhaseOperation with {len(self.params)} params cannot be "
                f"applied to wavefunction of length {len(wavefunction)}."
            )

        try:
            exp_params = np.exp(np.asarray(self.params, dtype=float) * 1j)
        except TypeError as e:
            raise RuntimeError(
                "MultiPhaseOperation can only be applied only if all symbolic "
                "parameters are bound to real numbers."
            ) from e
        return np.multiply(np.asarray(wavefunction), exp_params)
