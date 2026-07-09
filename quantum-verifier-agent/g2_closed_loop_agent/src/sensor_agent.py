"""Adaptive quantum sensor copilot using Ramsey-style phase estimation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import math
import numpy as np

from .safety import ExperimentProposal, HardwareSafetyGuard


@dataclass
class SensorRunResult:
    true_phase: float
    final_estimate: float
    absolute_error: float
    final_std: float
    rounds: int
    shots_per_round: int
    safety_repairs: int
    trace: List[Dict[str, float]]


class QuantumSensorCopilot:
    """Closed-loop Ramsey phase-estimation copilot.

    It chooses a safe interrogation time, simulates measurements, updates a grid
    posterior, and repeats. This captures the agentic pattern used in real
    sensor-control workflows without requiring lab hardware.
    """

    def __init__(self, guard: HardwareSafetyGuard | None = None, seed: int = 19):
        self.guard = guard or HardwareSafetyGuard()
        self.rng = np.random.default_rng(seed)

    def _measurement_probability(self, phase: float, tau: float, visibility: float = 0.96) -> float:
        # Probability of measuring |0> after Ramsey evolution.
        return float((1.0 + visibility * math.cos(phase * tau)) / 2.0)

    def estimate(self, true_phase: float = 0.62, rounds: int = 14, shots: int = 256) -> SensorRunResult:
        grid = np.linspace(0.0, math.pi, 2401)
        posterior = np.ones_like(grid) / len(grid)
        trace: List[Dict[str, float]] = []
        safety_repairs = 0
        tau = 0.30

        for r in range(rounds):
            mean = float(np.sum(grid * posterior))
            std = float(np.sqrt(np.sum((grid - mean) ** 2 * posterior)))
            # Adaptive policy: increase interrogation time as uncertainty drops,
            # but pass every proposal through the hardware-safety guard.
            proposed_tau = min(3.5, max(0.05, 0.8 / max(std, 0.08)))
            prop = ExperimentProposal(
                task_type="ramsey_phase_estimation",
                n_qubits=1,
                shots=shots,
                depth=3,
                layers=1,
                pulse_amplitude=0.75,
                duty_cycle=0.25,
                interrogation_time=proposed_tau,
                notes="adaptive Ramsey sensing proposal",
            )
            decision = self.guard.check(prop)
            safety_repairs += int(decision.repaired)
            tau = decision.repaired_proposal.interrogation_time
            shots = decision.repaired_proposal.shots

            p0_true = self._measurement_probability(true_phase, tau)
            count0 = int(self.rng.binomial(shots, p0_true))
            # Bayesian grid update under binomial likelihood.
            p0_grid = np.array([self._measurement_probability(phi, tau) for phi in grid])
            likelihood = (p0_grid ** count0) * ((1 - p0_grid) ** (shots - count0))
            likelihood = np.maximum(likelihood, 1e-300)
            posterior = posterior * likelihood
            posterior = posterior / posterior.sum()
            mean = float(np.sum(grid * posterior))
            std = float(np.sqrt(np.sum((grid - mean) ** 2 * posterior)))
            trace.append(
                {
                    "round": r + 1,
                    "tau": float(tau),
                    "shots": float(shots),
                    "count0": float(count0),
                    "posterior_mean": mean,
                    "posterior_std": std,
                    "abs_error": abs(mean - true_phase),
                }
            )

        final_mean = trace[-1]["posterior_mean"]
        final_std = trace[-1]["posterior_std"]
        return SensorRunResult(
            true_phase=true_phase,
            final_estimate=final_mean,
            absolute_error=abs(final_mean - true_phase),
            final_std=final_std,
            rounds=rounds,
            shots_per_round=shots,
            safety_repairs=safety_repairs,
            trace=trace,
        )
