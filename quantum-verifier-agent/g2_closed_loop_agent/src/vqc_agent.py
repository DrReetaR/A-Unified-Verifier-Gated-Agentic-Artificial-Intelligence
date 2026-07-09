"""Autonomous VQC architecture-search and verification loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
import math
import numpy as np

from .safety import ExperimentProposal, HardwareSafetyGuard
from .simulator import apply_cnot, apply_single_qubit_gate, expectation_z, ry, zero_state


@dataclass
class VQCTaskResult:
    dataset_name: str
    selected_template: str
    accuracy: float
    loss: float
    trainable_parameters: int
    safety_repairs: int
    closed_loop_iterations: int
    template_results: List[Dict[str, float | str]]


class AutonomousVQCAgent:
    """Template-search agent for a tiny parity classification VQC benchmark.

    This is a classroom-friendly prototype of autonomous VQC design. The agent
    tries several candidate circuit templates, checks safety, simulates the
    circuit, verifies task-level accuracy, and selects the smallest correct
    circuit.
    """

    def __init__(self, guard: HardwareSafetyGuard | None = None, seed: int = 11):
        self.guard = guard or HardwareSafetyGuard()
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def parity_dataset() -> List[Tuple[Tuple[float, float], int]]:
        # Angle 0 encodes |0>, angle pi encodes |1>. Label is XOR parity.
        return [((0.0, 0.0), 0), ((math.pi, 0.0), 1), ((0.0, math.pi), 1), ((math.pi, math.pi), 0)]

    def _run_template(self, template: str, features: Tuple[float, float], params: np.ndarray) -> float:
        n = 2
        state = zero_state(n)
        state = apply_single_qubit_gate(state, ry(features[0]), 0, n)
        state = apply_single_qubit_gate(state, ry(features[1]), 1, n)

        if template == "single_qubit_baseline":
            # No entanglement; cannot represent XOR well.
            state = apply_single_qubit_gate(state, ry(params[0]), 0, n)
            readout_qubit = 0
        elif template == "entangled_parity_vqc":
            # CNOT makes qubit-1 carry XOR for computational-basis encoded data.
            state = apply_cnot(state, control=0, target=1, n_qubits=n)
            state = apply_single_qubit_gate(state, ry(params[0]), 1, n)
            readout_qubit = 1
        elif template == "two_rotation_entangled_vqc":
            state = apply_single_qubit_gate(state, ry(params[0]), 0, n)
            state = apply_cnot(state, control=0, target=1, n_qubits=n)
            state = apply_single_qubit_gate(state, ry(params[1]), 1, n)
            readout_qubit = 1
        else:
            raise ValueError(f"unknown template {template}")
        z = expectation_z(state, readout_qubit, n)
        # Probability label=1: |1> readout -> (1-Z)/2
        return float((1.0 - z) / 2.0)

    def _loss_accuracy(self, template: str, data, params: np.ndarray) -> Tuple[float, float]:
        losses = []
        correct = 0
        eps = 1e-8
        for x, y in data:
            p1 = min(1 - eps, max(eps, self._run_template(template, x, params)))
            losses.append(-(y * math.log(p1) + (1 - y) * math.log(1 - p1)))
            correct += int((p1 >= 0.5) == bool(y))
        return float(np.mean(losses)), correct / len(data)

    def design(self) -> VQCTaskResult:
        data = self.parity_dataset()
        templates = [
            ("single_qubit_baseline", 1, 2),
            ("entangled_parity_vqc", 1, 3),
            ("two_rotation_entangled_vqc", 2, 5),
        ]
        template_results: List[Dict[str, float | str]] = []
        safety_repairs = 0
        total_iterations = 0

        for template, n_params, depth in templates:
            prop = ExperimentProposal(
                task_type="vqc_architecture_search",
                n_qubits=2,
                shots=1024,
                depth=depth,
                layers=1,
                angles=tuple([0.0] * n_params),
                notes=f"template={template}",
            )
            decision = self.guard.check(prop)
            safety_repairs += int(decision.repaired)

            # Closed-loop parameter search. For the exact parity template, zero
            # parameters already solve the task; other templates receive a fair
            # random search budget.
            best_params = np.zeros(n_params)
            best_loss, best_acc = self._loss_accuracy(template, data, best_params)
            for it in range(60):
                candidate = self.rng.uniform(-math.pi, math.pi, size=n_params)
                cand_loss, cand_acc = self._loss_accuracy(template, data, candidate)
                total_iterations += 1
                if (cand_acc > best_acc) or (cand_acc == best_acc and cand_loss < best_loss):
                    best_loss, best_acc, best_params = cand_loss, cand_acc, candidate
            template_results.append(
                {
                    "template": template,
                    "accuracy": float(best_acc),
                    "loss": float(best_loss),
                    "n_parameters": float(n_params),
                    "depth": float(depth),
                    "best_params": ";".join(f"{x:.4f}" for x in best_params),
                }
            )

        # Choose the highest accuracy; break ties by smaller depth/parameters.
        selected = sorted(
            template_results,
            key=lambda r: (-float(r["accuracy"]), float(r["depth"]), float(r["n_parameters"])),
        )[0]
        return VQCTaskResult(
            dataset_name="two_qubit_parity_xor",
            selected_template=str(selected["template"]),
            accuracy=float(selected["accuracy"]),
            loss=float(selected["loss"]),
            trainable_parameters=int(float(selected["n_parameters"])),
            safety_repairs=safety_repairs,
            closed_loop_iterations=total_iterations,
            template_results=template_results,
        )
