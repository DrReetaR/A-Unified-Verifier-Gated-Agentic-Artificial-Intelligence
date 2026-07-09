"""Closed-loop QAOA design agent for a small MaxCut benchmark."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
import math
import numpy as np

from .safety import ExperimentProposal, HardwareSafetyGuard
from .simulator import best_bitstrings_by_probability, expected_maxcut_cost, qaoa_state


@dataclass
class QAOARunResult:
    graph_name: str
    n_qubits: int
    p_layers: int
    best_cost: float
    approximation_ratio: float
    best_angles: Dict[str, List[float]]
    safety_repairs: int
    iterations: int
    trace: List[Dict[str, float]]
    top_bitstrings: List[Dict[str, float]]


def brute_force_optimum(n_qubits: int, edges: Sequence[Tuple[int, int, float]]) -> float:
    best = 0.0
    for idx in range(2 ** n_qubits):
        cost = 0.0
        for i, j, w in edges:
            cost += w if (((idx >> i) & 1) != ((idx >> j) & 1)) else 0.0
        best = max(best, cost)
    return best


class ClosedLoopQAOAAgent:
    """Autonomous p-layer QAOA search with a hardware-safety pre-check.

    The agent proposes candidate p, gamma, beta values, checks them using
    HardwareSafetyGuard, simulates the circuit, and keeps improving until the
    budget is exhausted.
    """

    def __init__(self, guard: HardwareSafetyGuard | None = None, seed: int = 7):
        self.guard = guard or HardwareSafetyGuard()
        self.rng = np.random.default_rng(seed)

    def _evaluate(self, n_qubits: int, edges, gammas, betas) -> float:
        state = qaoa_state(n_qubits, edges, gammas, betas)
        return expected_maxcut_cost(state, edges)

    def design(self, graph_name: str, n_qubits: int, edges: Sequence[Tuple[int, int, float]], max_p: int = 2, iterations: int = 160) -> QAOARunResult:
        optimum = brute_force_optimum(n_qubits, edges)
        best = {"cost": -1.0, "gammas": [], "betas": [], "p": 1}
        trace: List[Dict[str, float]] = []
        safety_repairs = 0

        # Stage 1: safe random architecture/parameter proposals.
        for it in range(iterations):
            p = int(self.rng.integers(1, max_p + 1))
            gammas = tuple(float(x) for x in self.rng.uniform(0, math.pi, size=p))
            betas = tuple(float(x) for x in self.rng.uniform(0, math.pi / 2, size=p))
            angles = gammas + betas
            prop = ExperimentProposal(
                task_type="qaoa_maxcut",
                n_qubits=n_qubits,
                shots=2048,
                depth=2 * p * n_qubits + len(edges),
                layers=p,
                angles=angles,
                notes="QAOA random-search proposal",
            )
            decision = self.guard.check(prop)
            safety_repairs += int(decision.repaired)
            p = decision.repaired_proposal.layers
            angles = decision.repaired_proposal.angles
            gammas = angles[:p]
            betas = angles[p:2*p]
            cost = self._evaluate(n_qubits, edges, gammas, betas)
            if cost > best["cost"]:
                best = {"cost": cost, "gammas": list(gammas), "betas": list(betas), "p": p}
            trace.append({"iteration": it, "candidate_cost": cost, "best_cost": best["cost"], "p_layers": p})

        # Stage 2: local closed-loop refinement around the best proposal.
        step = 0.16
        for local_it in range(80):
            p = int(best["p"])
            g = np.array(best["gammas"], dtype=float)
            b = np.array(best["betas"], dtype=float)
            proposal_g = tuple(np.mod(g + self.rng.normal(0, step, size=p), math.pi))
            proposal_b = tuple(np.mod(b + self.rng.normal(0, step, size=p), math.pi / 2))
            prop = ExperimentProposal(
                task_type="qaoa_maxcut_refinement",
                n_qubits=n_qubits,
                shots=2048,
                depth=2 * p * n_qubits + len(edges),
                layers=p,
                angles=tuple(proposal_g + proposal_b),
                notes="QAOA local refinement proposal",
            )
            decision = self.guard.check(prop)
            safety_repairs += int(decision.repaired)
            angles = decision.repaired_proposal.angles
            proposal_g = angles[:p]
            proposal_b = angles[p:2*p]
            cost = self._evaluate(n_qubits, edges, proposal_g, proposal_b)
            if cost > best["cost"]:
                best = {"cost": cost, "gammas": list(proposal_g), "betas": list(proposal_b), "p": p}
                step *= 0.99
            else:
                step *= 0.985
            trace.append({"iteration": iterations + local_it, "candidate_cost": cost, "best_cost": best["cost"], "p_layers": p})

        state = qaoa_state(n_qubits, edges, best["gammas"], best["betas"])
        top = best_bitstrings_by_probability(state, n_qubits, edges, top_k=6)
        ratio = best["cost"] / optimum if optimum > 0 else 0.0
        return QAOARunResult(
            graph_name=graph_name,
            n_qubits=n_qubits,
            p_layers=int(best["p"]),
            best_cost=float(best["cost"]),
            approximation_ratio=float(ratio),
            best_angles={"gammas": [float(x) for x in best["gammas"]], "betas": [float(x) for x in best["betas"]]},
            safety_repairs=safety_repairs,
            iterations=len(trace),
            trace=trace,
            top_bitstrings=top,
        )
