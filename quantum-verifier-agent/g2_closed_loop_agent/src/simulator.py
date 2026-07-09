"""Lightweight state-vector utilities for the G2 Closed-Loop Quantum Agent.

The project intentionally avoids cloud quantum hardware or heavy quantum SDKs so it
can run in Google Colab, a normal laptop, or a classroom lab system.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
import math
import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = (1 / math.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)


def rx(theta: float) -> np.ndarray:
    return np.array(
        [[math.cos(theta / 2), -1j * math.sin(theta / 2)],
         [-1j * math.sin(theta / 2), math.cos(theta / 2)]],
        dtype=complex,
    )


def ry(theta: float) -> np.ndarray:
    return np.array(
        [[math.cos(theta / 2), -math.sin(theta / 2)],
         [math.sin(theta / 2), math.cos(theta / 2)]],
        dtype=complex,
    )


def rz(theta: float) -> np.ndarray:
    return np.array(
        [[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]],
        dtype=complex,
    )


def zero_state(n_qubits: int) -> np.ndarray:
    state = np.zeros(2 ** n_qubits, dtype=complex)
    state[0] = 1.0
    return state


def plus_state(n_qubits: int) -> np.ndarray:
    state = zero_state(n_qubits)
    for q in range(n_qubits):
        state = apply_single_qubit_gate(state, H, q, n_qubits)
    return state


def _embed_single(gate: np.ndarray, target: int, n_qubits: int) -> np.ndarray:
    # Basis ordering is |q_{n-1} ... q_1 q_0>, so q0 is the least-significant bit.
    ops = []
    for q in reversed(range(n_qubits)):
        ops.append(gate if q == target else I2)
    full = ops[0]
    for op in ops[1:]:
        full = np.kron(full, op)
    return full


def apply_single_qubit_gate(state: np.ndarray, gate: np.ndarray, target: int, n_qubits: int) -> np.ndarray:
    return _embed_single(gate, target, n_qubits) @ state


def apply_cnot(state: np.ndarray, control: int, target: int, n_qubits: int) -> np.ndarray:
    out = np.zeros_like(state)
    for idx, amp in enumerate(state):
        if ((idx >> control) & 1) == 1:
            flipped = idx ^ (1 << target)
            out[flipped] += amp
        else:
            out[idx] += amp
    return out


def apply_cz_phase_by_cost(
    state: np.ndarray,
    graph_edges: Sequence[Tuple[int, int, float]],
    gamma: float,
) -> np.ndarray:
    out = state.copy()
    for idx in range(len(state)):
        cost = maxcut_cost_of_bitstring(idx, graph_edges)
        out[idx] *= np.exp(-1j * gamma * cost)
    return out


def probabilities(state: np.ndarray) -> np.ndarray:
    probs = np.abs(state) ** 2
    return probs / probs.sum()


def expectation_z(state: np.ndarray, qubit: int, n_qubits: int) -> float:
    probs = probabilities(state)
    exp = 0.0
    for idx, p in enumerate(probs):
        bit = (idx >> qubit) & 1
        exp += p * (1 if bit == 0 else -1)
    return float(np.real(exp))


def bitstring(idx: int, n_qubits: int) -> str:
    return format(idx, f"0{n_qubits}b")[::-1]


def maxcut_cost_of_bitstring(idx: int, graph_edges: Sequence[Tuple[int, int, float]]) -> float:
    total = 0.0
    for i, j, w in graph_edges:
        total += w if (((idx >> i) & 1) != ((idx >> j) & 1)) else 0.0
    return total


def sample_counts(state: np.ndarray, n_qubits: int, shots: int, rng: np.random.Generator) -> Dict[str, int]:
    probs = probabilities(state)
    draws = rng.choice(len(probs), size=shots, p=probs)
    counts: Dict[str, int] = {}
    for d in draws:
        key = bitstring(int(d), n_qubits)
        counts[key] = counts.get(key, 0) + 1
    return counts


def qaoa_state(
    n_qubits: int,
    graph_edges: Sequence[Tuple[int, int, float]],
    gammas: Sequence[float],
    betas: Sequence[float],
) -> np.ndarray:
    if len(gammas) != len(betas):
        raise ValueError("gammas and betas must have same length")
    state = plus_state(n_qubits)
    for gamma, beta in zip(gammas, betas):
        state = apply_cz_phase_by_cost(state, graph_edges, gamma)
        for q in range(n_qubits):
            state = apply_single_qubit_gate(state, rx(2 * beta), q, n_qubits)
    return state


def expected_maxcut_cost(
    state: np.ndarray,
    graph_edges: Sequence[Tuple[int, int, float]],
) -> float:
    probs = probabilities(state)
    return float(sum(p * maxcut_cost_of_bitstring(i, graph_edges) for i, p in enumerate(probs)))


def best_bitstrings_by_probability(
    state: np.ndarray,
    n_qubits: int,
    graph_edges: Sequence[Tuple[int, int, float]],
    top_k: int = 5,
) -> List[Dict[str, float]]:
    probs = probabilities(state)
    order = np.argsort(probs)[::-1][:top_k]
    return [
        {
            "bitstring_little_endian": bitstring(int(i), n_qubits),
            "probability": float(probs[i]),
            "maxcut_cost": float(maxcut_cost_of_bitstring(int(i), graph_edges)),
        }
        for i in order
    ]
