"""Lightweight OpenQASM 2.0 simulator used by the G1 quantum-code agent.

Supported subset: qreg, creg, h, x, z, s, t, cx, cz, swap, ccx, measure.
This keeps the project runnable on normal laptops and Google Colab without Qiskit.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Dict, List, Tuple

import numpy as np


class QASMError(Exception):
    """Raised when the simplified OpenQASM parser or simulator fails."""


@dataclass
class SimulationResult:
    probabilities: Dict[str, float]
    statevector: np.ndarray
    measured_qubits: List[int]
    measured_cbits: List[int]
    num_qubits: int


_SINGLE_GATES = {
    "h": (1 / math.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex),
    "x": np.array([[0, 1], [1, 0]], dtype=complex),
    "z": np.array([[1, 0], [0, -1]], dtype=complex),
    "s": np.array([[1, 0], [0, 1j]], dtype=complex),
    "t": np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], dtype=complex),
}


class OpenQASMSimulator:
    """Small statevector simulator for benchmark verification.

    Qubit indexing follows the common little-endian simulator convention:
    q[0] is the least significant bit. Output bitstrings are formatted in
    classical-register order, highest classical bit first.
    """

    def __init__(self, shots: int = 1024, seed: int = 42):
        self.shots = shots
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _strip_comments(qasm: str) -> List[str]:
        cleaned = []
        for raw in qasm.splitlines():
            line = raw.split("//", 1)[0].strip()
            if line:
                cleaned.append(line)
        return cleaned

    @staticmethod
    def lint(qasm: str) -> List[str]:
        """Return human-readable lint errors for a simplified OpenQASM program."""
        errors: List[str] = []
        qreg_seen = False
        creg_seen = False
        for line_no, line in enumerate(OpenQASMSimulator._strip_comments(qasm), start=1):
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue
            if line.startswith("qreg"):
                qreg_seen = True
                if not re.match(r"qreg\s+q\[\d+\]\s*;?$", line):
                    errors.append(f"Line {line_no}: malformed qreg declaration")
                continue
            if line.startswith("creg"):
                creg_seen = True
                if not re.match(r"creg\s+c\[\d+\]\s*;?$", line):
                    errors.append(f"Line {line_no}: malformed creg declaration")
                continue
            if line.startswith("measure"):
                if not re.match(r"measure\s+q(\[\d+\])?\s*->\s*c(\[\d+\])?\s*;?$", line):
                    errors.append(f"Line {line_no}: unsupported measurement syntax: {line}")
                continue
            gate = line.split()[0].strip().rstrip(";")
            if gate not in set(_SINGLE_GATES) | {"cx", "cz", "swap", "ccx"}:
                errors.append(f"Line {line_no}: unsupported or unknown gate '{gate}'")
        if not qreg_seen:
            errors.append("Missing qreg declaration")
        if not creg_seen:
            errors.append("Missing creg declaration")
        if "measure" not in qasm:
            errors.append("Missing measurement instruction")
        return errors

    def run(self, qasm: str) -> SimulationResult:
        lines = self._strip_comments(qasm)
        n_qubits = None
        n_cbits = None
        ops: List[Tuple[str, Tuple[int, ...]]] = []
        measurements: List[Tuple[int, int]] = []

        for line in lines:
            line = line.rstrip(";").strip()
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue
            if line.startswith("qreg"):
                m = re.search(r"q\[(\d+)\]", line)
                if not m:
                    raise QASMError(f"Cannot parse qreg: {line}")
                n_qubits = int(m.group(1))
                continue
            if line.startswith("creg"):
                m = re.search(r"c\[(\d+)\]", line)
                if not m:
                    raise QASMError(f"Cannot parse creg: {line}")
                n_cbits = int(m.group(1))
                continue
            if line.startswith("measure"):
                # measure q -> c
                if re.match(r"measure\s+q\s*->\s*c$", line):
                    if n_qubits is None:
                        raise QASMError("qreg must be declared before measurement")
                    measurements = [(i, i) for i in range(n_qubits)]
                    continue
                m = re.match(r"measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\]$", line)
                if not m:
                    raise QASMError(f"Unsupported measurement syntax: {line}")
                measurements.append((int(m.group(1)), int(m.group(2))))
                continue

            gate, args = self._parse_gate(line)
            ops.append((gate, args))

        if n_qubits is None:
            raise QASMError("Missing qreg declaration")
        if n_cbits is None:
            raise QASMError("Missing creg declaration")
        if not measurements:
            raise QASMError("No measurements found")

        state = np.zeros(2 ** n_qubits, dtype=complex)
        state[0] = 1.0
        for gate, args in ops:
            if gate in _SINGLE_GATES:
                state = self._apply_single(state, _SINGLE_GATES[gate], args[0], n_qubits)
            elif gate == "cx":
                state = self._apply_cx(state, args[0], args[1], n_qubits)
            elif gate == "cz":
                state = self._apply_cz(state, args[0], args[1], n_qubits)
            elif gate == "swap":
                state = self._apply_swap(state, args[0], args[1], n_qubits)
            elif gate == "ccx":
                state = self._apply_ccx(state, args[0], args[1], args[2], n_qubits)
            else:
                raise QASMError(f"Unsupported gate: {gate}")

        probs = self._measurement_probabilities(state, measurements, n_cbits, n_qubits)
        measured_qubits = [q for q, _ in sorted(measurements, key=lambda x: x[1])]
        measured_cbits = [c for _, c in sorted(measurements, key=lambda x: x[1])]
        return SimulationResult(probs, state, measured_qubits, measured_cbits, n_qubits)

    @staticmethod
    def _parse_gate(line: str) -> Tuple[str, Tuple[int, ...]]:
        gate = line.split()[0]
        qubits = tuple(int(x) for x in re.findall(r"q\[(\d+)\]", line))
        expected = {"h": 1, "x": 1, "z": 1, "s": 1, "t": 1, "cx": 2, "cz": 2, "swap": 2, "ccx": 3}
        if gate not in expected:
            raise QASMError(f"Unknown gate: {gate}")
        if len(qubits) != expected[gate]:
            raise QASMError(f"Gate {gate} expected {expected[gate]} qubits but got {len(qubits)}")
        return gate, qubits

    @staticmethod
    def _apply_single(state: np.ndarray, gate: np.ndarray, target: int, n: int) -> np.ndarray:
        new_state = state.copy()
        step = 1 << target
        for base in range(0, 1 << n, step << 1):
            for offset in range(step):
                i0 = base + offset
                i1 = i0 + step
                a0, a1 = state[i0], state[i1]
                new_state[i0] = gate[0, 0] * a0 + gate[0, 1] * a1
                new_state[i1] = gate[1, 0] * a0 + gate[1, 1] * a1
        return new_state

    @staticmethod
    def _apply_cx(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
        new_state = state.copy()
        for i in range(1 << n):
            if ((i >> control) & 1) and not ((i >> target) & 1):
                j = i | (1 << target)
                new_state[i], new_state[j] = new_state[j], new_state[i]
        return new_state

    @staticmethod
    def _apply_cz(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
        new_state = state.copy()
        for i in range(1 << n):
            if ((i >> control) & 1) and ((i >> target) & 1):
                new_state[i] *= -1
        return new_state

    @staticmethod
    def _apply_swap(state: np.ndarray, q1: int, q2: int, n: int) -> np.ndarray:
        if q1 == q2:
            return state.copy()
        new_state = state.copy()
        for i in range(1 << n):
            b1, b2 = (i >> q1) & 1, (i >> q2) & 1
            if b1 != b2:
                j = i ^ ((1 << q1) | (1 << q2))
                if i < j:
                    new_state[i], new_state[j] = new_state[j], new_state[i]
        return new_state

    @staticmethod
    def _apply_ccx(state: np.ndarray, c1: int, c2: int, target: int, n: int) -> np.ndarray:
        new_state = state.copy()
        for i in range(1 << n):
            if ((i >> c1) & 1) and ((i >> c2) & 1) and not ((i >> target) & 1):
                j = i | (1 << target)
                new_state[i], new_state[j] = new_state[j], new_state[i]
        return new_state

    @staticmethod
    def _measurement_probabilities(
        state: np.ndarray, measurements: List[Tuple[int, int]], n_cbits: int, n_qubits: int
    ) -> Dict[str, float]:
        probs: Dict[str, float] = {}
        # map cbit -> qubit; output is c[n-1]...c[0]
        c_to_q = {c: q for q, c in measurements}
        measured_cbits = sorted(c_to_q.keys(), reverse=True)
        for basis_index, amp in enumerate(state):
            p = float(abs(amp) ** 2)
            if p < 1e-12:
                continue
            bits = []
            for c in measured_cbits:
                q = c_to_q[c]
                bits.append(str((basis_index >> q) & 1))
            key = "".join(bits)
            probs[key] = probs.get(key, 0.0) + p
        return dict(sorted(probs.items()))

    def counts_from_probabilities(self, probabilities: Dict[str, float]) -> Dict[str, int]:
        keys = list(probabilities.keys())
        p = np.array([probabilities[k] for k in keys], dtype=float)
        p = p / p.sum()
        samples = self.rng.multinomial(self.shots, p)
        return dict(zip(keys, map(int, samples)))
