"""Run the complete G2 closed-loop quantum-agent experiment.

Usage:
    python experiments/run_experiment.py

Outputs are written to ../results and ../plots relative to the project root.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import pandas as pd

from src.qaoa_agent import ClosedLoopQAOAAgent
from src.sensor_agent import QuantumSensorCopilot
from src.safety import ExperimentProposal, HardwareSafetyGuard
from src.vqc_agent import AutonomousVQCAgent


def ensure_dirs() -> None:
    (PROJECT_ROOT / "results").mkdir(exist_ok=True)
    (PROJECT_ROOT / "plots").mkdir(exist_ok=True)


def run_safety_demo(guard: HardwareSafetyGuard) -> pd.DataFrame:
    proposals = [
        ExperimentProposal("qaoa_unsafe_shots", n_qubits=4, shots=9000, depth=20, layers=2, angles=(0.1, 0.2)),
        ExperimentProposal("vqc_too_many_qubits", n_qubits=12, shots=1024, depth=8, layers=1, angles=(0.0,)),
        ExperimentProposal("sensor_unsafe_tau", n_qubits=1, shots=512, depth=3, layers=1, interrogation_time=6.0),
        ExperimentProposal("pulse_overdrive", n_qubits=1, shots=512, depth=3, layers=1, pulse_amplitude=1.4, duty_cycle=0.55),
        ExperimentProposal("safe_reference", n_qubits=2, shots=1024, depth=8, layers=1, pulse_amplitude=0.4, duty_cycle=0.2),
    ]
    rows = []
    for p in proposals:
        d = guard.check(p)
        rows.append(
            {
                "task_type": p.task_type,
                "accepted": d.accepted,
                "repaired": d.repaired,
                "original_qubits": p.n_qubits,
                "safe_qubits": d.repaired_proposal.n_qubits,
                "original_shots": p.shots,
                "safe_shots": d.repaired_proposal.shots,
                "original_tau": p.interrogation_time,
                "safe_tau": d.repaired_proposal.interrogation_time,
                "reasons": " | ".join(d.reasons),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(PROJECT_ROOT / "results" / "safety_guard_demo.csv", index=False)
    return df


def run_all() -> None:
    ensure_dirs()
    guard = HardwareSafetyGuard()

    # 1) Autonomous VQC design
    vqc = AutonomousVQCAgent(guard=guard, seed=11)
    vqc_result = vqc.design()
    pd.DataFrame(vqc_result.template_results).to_csv(PROJECT_ROOT / "results" / "vqc_template_search.csv", index=False)

    # 2) Autonomous QAOA MaxCut design
    graph_edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0), (0, 2, 0.7)]
    qaoa = ClosedLoopQAOAAgent(guard=guard, seed=7)
    qaoa_result = qaoa.design("weighted_4_node_ring_plus_diagonal", 4, graph_edges, max_p=2, iterations=160)
    pd.DataFrame(qaoa_result.trace).to_csv(PROJECT_ROOT / "results" / "qaoa_optimization_trace.csv", index=False)
    pd.DataFrame(qaoa_result.top_bitstrings).to_csv(PROJECT_ROOT / "results" / "qaoa_top_bitstrings.csv", index=False)

    # 3) Quantum sensor copilot
    sensor = QuantumSensorCopilot(guard=guard, seed=19)
    sensor_result = sensor.estimate(true_phase=0.62, rounds=14, shots=256)
    pd.DataFrame(sensor_result.trace).to_csv(PROJECT_ROOT / "results" / "sensor_adaptive_trace.csv", index=False)

    # 4) Safety demo
    safety_df = run_safety_demo(guard)

    # 5) Summary results
    summary = pd.DataFrame(
        [
            {
                "module": "Autonomous VQC design",
                "benchmark": vqc_result.dataset_name,
                "main_metric": "classification_accuracy",
                "value": vqc_result.accuracy,
                "secondary_metric": "selected_template",
                "secondary_value": vqc_result.selected_template,
                "safety_repairs": vqc_result.safety_repairs,
            },
            {
                "module": "Autonomous QAOA design",
                "benchmark": qaoa_result.graph_name,
                "main_metric": "approximation_ratio",
                "value": qaoa_result.approximation_ratio,
                "secondary_metric": "expected_cut_cost",
                "secondary_value": f"{qaoa_result.best_cost:.4f}",
                "safety_repairs": qaoa_result.safety_repairs,
            },
            {
                "module": "Quantum sensor copilot",
                "benchmark": "Ramsey phase estimation",
                "main_metric": "absolute_phase_error",
                "value": sensor_result.absolute_error,
                "secondary_metric": "posterior_std",
                "secondary_value": f"{sensor_result.final_std:.4f}",
                "safety_repairs": sensor_result.safety_repairs,
            },
            {
                "module": "Hardware-safety guard",
                "benchmark": "unsafe proposal repair test",
                "main_metric": "unsafe_proposals_repaired",
                "value": float(safety_df["repaired"].sum()),
                "secondary_metric": "total_demo_proposals",
                "secondary_value": str(len(safety_df)),
                "safety_repairs": int(safety_df["repaired"].sum()),
            },
        ]
    )
    summary.to_csv(PROJECT_ROOT / "results" / "summary_results.csv", index=False)
    with open(PROJECT_ROOT / "results" / "summary_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "vqc": vqc_result.__dict__,
                "qaoa": qaoa_result.__dict__,
                "sensor": sensor_result.__dict__,
            },
            f,
            indent=2,
        )

    # Plots: each chart is separate.
    qaoa_trace = pd.DataFrame(qaoa_result.trace)
    plt.figure(figsize=(8, 5))
    plt.plot(qaoa_trace["iteration"], qaoa_trace["best_cost"])
    plt.xlabel("Closed-loop iteration")
    plt.ylabel("Best expected MaxCut cost")
    plt.title("Autonomous QAOA Design: Best Cost Improvement")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "plots" / "qaoa_best_cost.png", dpi=180)
    plt.close()

    sensor_trace = pd.DataFrame(sensor_result.trace)
    plt.figure(figsize=(8, 5))
    plt.plot(sensor_trace["round"], sensor_trace["abs_error"])
    plt.xlabel("Adaptive sensing round")
    plt.ylabel("Absolute phase error")
    plt.title("Quantum Sensor Copilot: Error Reduction")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "plots" / "sensor_error_reduction.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(sensor_trace["round"], sensor_trace["posterior_std"])
    plt.xlabel("Adaptive sensing round")
    plt.ylabel("Posterior standard deviation")
    plt.title("Quantum Sensor Copilot: Uncertainty Reduction")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "plots" / "sensor_uncertainty.png", dpi=180)
    plt.close()

    vqc_df = pd.DataFrame(vqc_result.template_results)
    plt.figure(figsize=(8, 5))
    plt.bar(vqc_df["template"], vqc_df["accuracy"])
    plt.xticks(rotation=25, ha="right")
    plt.xlabel("VQC template")
    plt.ylabel("Verification accuracy")
    plt.title("Autonomous VQC Architecture Search")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "plots" / "vqc_template_accuracy.png", dpi=180)
    plt.close()

    print("G2 Closed-loop Quantum Agent experiment completed.")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run_all()
