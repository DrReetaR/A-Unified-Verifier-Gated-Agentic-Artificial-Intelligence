"""Agentic quantum software-engineering prototype.

Pipeline: Plan -> Generate -> Lint -> Simulate -> Verify -> Repair -> Export.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from .code_templates import get_qasm_template, qasm_to_pennylane_python, qasm_to_qiskit_python
from .quantum_simulator import OpenQASMSimulator, QASMError
from .tasks import QuantumTask


@dataclass
class AgentTrace:
    task_id: str
    title: str
    prompt: str
    family: str
    status: str
    passed: bool
    iterations: int
    total_variation_distance: float
    max_probability_error: float
    expected_distribution: Dict[str, float]
    observed_distribution: Dict[str, float]
    lint_errors: List[str]
    repair_actions: List[str]
    generated_qasm: str
    qiskit_code: str
    pennylane_code: str


class QuantumCodeAgent:
    def __init__(self, pass_tvd_threshold: float = 0.02, max_iterations: int = 3):
        self.pass_tvd_threshold = pass_tvd_threshold
        self.max_iterations = max_iterations
        self.simulator = OpenQASMSimulator(shots=1024, seed=2026)

    def solve(self, task: QuantumTask) -> AgentTrace:
        qasm = self._generate(task, mode=task.initial_mode)
        repair_actions: List[str] = []
        last_lint_errors: List[str] = []
        observed: Dict[str, float] = {}
        tvd = 1.0
        max_err = 1.0
        passed = False

        for iteration in range(1, self.max_iterations + 1):
            last_lint_errors = self.simulator.lint(qasm)
            if last_lint_errors:
                repair_actions.append("Lint failed; regenerated from verified task template.")
                qasm = self._repair(task, qasm, last_lint_errors, observed)
                continue

            try:
                sim = self.simulator.run(qasm)
                observed = sim.probabilities
                tvd, max_err = self._distribution_distance(task.expected_distribution, observed)
                passed = tvd <= self.pass_tvd_threshold
                if passed:
                    break
                repair_actions.append(
                    f"Verifier failed with TVD={tvd:.4f}; regenerated using algorithm-aware template."
                )
                qasm = self._repair(task, qasm, last_lint_errors, observed)
            except QASMError as exc:
                last_lint_errors = [str(exc)]
                repair_actions.append(f"Simulation failed: {exc}; regenerated from verified template.")
                qasm = self._repair(task, qasm, last_lint_errors, observed)

        status = "PASS" if passed else "FAIL"
        return AgentTrace(
            task_id=task.task_id,
            title=task.title,
            prompt=task.prompt,
            family=task.family,
            status=status,
            passed=passed,
            iterations=iteration,
            total_variation_distance=tvd,
            max_probability_error=max_err,
            expected_distribution=task.expected_distribution,
            observed_distribution=observed,
            lint_errors=last_lint_errors,
            repair_actions=repair_actions,
            generated_qasm=qasm,
            qiskit_code=qasm_to_qiskit_python(qasm),
            pennylane_code=qasm_to_pennylane_python(qasm),
        )

    def _generate(self, task: QuantumTask, mode: str) -> str:
        return get_qasm_template(task.task_id, mode=mode)

    def _repair(
        self,
        task: QuantumTask,
        qasm: str,
        lint_errors: List[str],
        observed_distribution: Dict[str, float],
    ) -> str:
        # In a full LLM-agent system this is where the model would use lint +
        # simulator feedback. The offline baseline uses a verified template.
        return get_qasm_template(task.task_id, mode="correct")

    @staticmethod
    def _distribution_distance(expected: Dict[str, float], observed: Dict[str, float]) -> Tuple[float, float]:
        keys = set(expected) | set(observed)
        abs_diffs = [abs(expected.get(k, 0.0) - observed.get(k, 0.0)) for k in keys]
        tvd = 0.5 * sum(abs_diffs)
        max_err = max(abs_diffs) if abs_diffs else 0.0
        return tvd, max_err


def trace_to_row(trace: AgentTrace) -> Dict[str, object]:
    row = asdict(trace)
    # flatten verbose fields for CSV friendliness
    row["expected_distribution"] = str(trace.expected_distribution)
    row["observed_distribution"] = str({k: round(v, 6) for k, v in trace.observed_distribution.items()})
    row["lint_errors"] = " | ".join(trace.lint_errors)
    row["repair_actions"] = " | ".join(trace.repair_actions)
    row.pop("generated_qasm", None)
    row.pop("qiskit_code", None)
    row.pop("pennylane_code", None)
    return row
