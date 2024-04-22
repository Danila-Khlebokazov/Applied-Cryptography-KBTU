import random
import enum


class Qubit:
    def __init__(self, polarization: int):
        self._polarization = polarization

    @property
    def polarization(self):
        try:
            return self._polarization
        finally:
            self._polarization = random.randrange(0, 360)

    def __repr__(self):
        return f"Qubit({self.polarization})"

    def __str__(self):
        return f"Qubit({self.polarization})"


class Replicator:
    polarization_map = {
        (1, 1): random.choice([90, 270]),
        (1, 0): random.choice([0, 180]),
        (2, 0): 45,
        (2, 1): 360 - 45
    }

    @staticmethod
    def create_qubits(bases: list["Gate"], initial_key_bits: list[int]):
        if len(bases) != len(initial_key_bits):
            raise ValueError("Bases and key bits must have the same length")

        return [Qubit(polarization=Replicator.polarization_map.get((base.gate_type.value, bit))) for base, bit in
                zip(bases, initial_key_bits)]


class Gate:
    class GateBases(enum.Enum):
        RECTANGULAR = 1
        DIAGONAL = 2

    def __init__(self, gate_basis: GateBases):
        self.gate_type = gate_basis

    @staticmethod
    def _rectangular(qubit: Qubit):
        qubit_polarization = qubit.polarization
        # print(qubit_polarization, "rectangular")
        if qubit_polarization == 0 or qubit_polarization == 180:
            # print("rectangular-0")
            return 0
        elif qubit_polarization == 90 or qubit_polarization == 270:
            # print("rectangular-90")
            return 1
        return random.choice([0, 1])

    @staticmethod
    def _diagonal(qubit: Qubit):
        qubit_polarization = qubit.polarization
        # print(qubit_polarization, "diagonal")
        # print(qubit_polarization, "diagonal-")
        if qubit_polarization == 45:
            # print("diagonal-45")
            return 0
        elif qubit_polarization == 315:
            # print("diagonal-315")
            return 1
        return random.choice([0, 1])

    def calculate(self, qubit: Qubit):
        if self.gate_type == self.GateBases.RECTANGULAR:
            return self._rectangular(qubit)
        elif self.gate_type == self.GateBases.DIAGONAL:
            return self._diagonal(qubit)
