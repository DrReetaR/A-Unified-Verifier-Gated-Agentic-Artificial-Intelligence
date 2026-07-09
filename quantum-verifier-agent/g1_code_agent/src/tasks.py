"""Benchmark tasks for the G1 quantum code-generation/debugging agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class QuantumTask:
    task_id: str
    title: str
    prompt: str
    expected_distribution: Dict[str, float]
    family: str
    initial_mode: str = "correct"  # correct, buggy, invalid
    target_language: str = "OpenQASM2"


TASKS = [
    QuantumTask(
        "T01_BELL",
        "Bell State Generator",
        "Generate a 2-qubit Bell state circuit and measure both qubits.",
        {"00": 0.5, "11": 0.5},
        "state-preparation",
    ),
    QuantumTask(
        "T02_GHZ3",
        "GHZ-3 State Generator",
        "Generate a 3-qubit GHZ state circuit and measure all qubits.",
        {"000": 0.5, "111": 0.5},
        "state-preparation",
    ),
    QuantumTask(
        "T03_QRB",
        "Quantum Random Bit",
        "Generate a one-qubit random bit using a Hadamard gate and measurement.",
        {"0": 0.5, "1": 0.5},
        "basic-primitives",
    ),
    QuantumTask(
        "T04_UNIFORM3",
        "Uniform 3-Qubit Superposition",
        "Generate a uniform superposition over all 3-qubit basis states.",
        {format(i, "03b"): 1 / 8 for i in range(8)},
        "state-preparation",
    ),
    QuantumTask(
        "T05_GROVER2",
        "2-Qubit Grover Search",
        "Generate a 2-qubit Grover circuit that marks and returns state |11>.",
        {"11": 1.0},
        "algorithm-generation",
    ),
    QuantumTask(
        "T06_BV101",
        "Bernstein-Vazirani Secret 101",
        "Generate a Bernstein-Vazirani circuit for secret bitstring 101 and measure the secret register.",
        {"101": 1.0},
        "algorithm-generation",
    ),
    QuantumTask(
        "T07_REPETITION3",
        "3-Qubit Repetition Code Encoding",
        "Encode logical |1> into the 3-qubit repetition code state |111>.",
        {"111": 1.0},
        "error-correction-coding",
    ),
    QuantumTask(
        "T08_BUGGY_BELL",
        "Repair Missing Entangling Gate",
        "Debug a Bell-state program where the entangling CX gate is missing.",
        {"00": 0.5, "11": 0.5},
        "debugging-repair",
        initial_mode="buggy",
    ),
    QuantumTask(
        "T09_BUGGY_GROVER",
        "Repair Incomplete Grover Diffuser",
        "Debug a Grover program where the diffuser is missing.",
        {"11": 1.0},
        "debugging-repair",
        initial_mode="buggy",
    ),
    QuantumTask(
        "T10_INVALID_GATE",
        "Repair Invalid OpenQASM Gate Typo",
        "Debug an OpenQASM program containing an invalid two-qubit gate name.",
        {"00": 0.5, "11": 0.5},
        "linting-repair",
        initial_mode="invalid",
    ),
]
