"""Run the G1 quantum code-generation/debugging agent benchmark.

Usage:
    python experiments/run_experiment.py
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import pandas as pd

from src.agent import QuantumCodeAgent, trace_to_row
from src.tasks import TASKS


def ensure_dirs() -> dict:
    dirs = {
        "results": ROOT / "results",
        "qasm": ROOT / "results" / "generated_qasm",
        "py": ROOT / "results" / "generated_python",
        "plots": ROOT / "results" / "plots",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def plot_results(df: pd.DataFrame, plots_dir: Path) -> None:
    # Plot 1: total variation distance by task
    plt.figure(figsize=(10, 5))
    plt.bar(df["task_id"], df["total_variation_distance"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Total Variation Distance")
    plt.title("Verifier Error by Quantum Programming Task")
    plt.tight_layout()
    plt.savefig(plots_dir / "tvd_by_task.png", dpi=180)
    plt.close()

    # Plot 2: iterations by task
    plt.figure(figsize=(10, 5))
    plt.bar(df["task_id"], df["iterations"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Agent Iterations")
    plt.title("Agentic Repair Iterations")
    plt.tight_layout()
    plt.savefig(plots_dir / "iterations_by_task.png", dpi=180)
    plt.close()

    # Plot 3: pass/fail count
    counts = df["status"].value_counts().reindex(["PASS", "FAIL"], fill_value=0)
    plt.figure(figsize=(5, 4))
    plt.bar(counts.index, counts.values)
    plt.ylabel("Number of Tasks")
    plt.title("Quantum Code Agent Pass/Fail Summary")
    plt.tight_layout()
    plt.savefig(plots_dir / "pass_fail_summary.png", dpi=180)
    plt.close()


def write_report(df: pd.DataFrame, traces, report_path: Path) -> None:
    pass_rate = 100 * df["passed"].mean()
    avg_tvd = df["total_variation_distance"].mean()
    avg_iter = df["iterations"].mean()
    repaired = df["repair_actions"].fillna("").str.len().gt(0).sum()

    report = f"""# G1 Implementation Report: Quantum Code-Generation and Debugging Agent

## Research Group

**G1 – Quantum software engineering and code-generation agents**  
Future enhancement direction: quantum coding copilot, Qiskit/PennyLane/OpenQASM migration, and simulator-backed quantum debugging agent.

## Prototype Implemented

This mini-project implements a self-contained quantum code agent with the following loop:

1. Understand a quantum programming task.
2. Generate OpenQASM 2.0 code.
3. Lint the generated program.
4. Simulate the circuit using a lightweight statevector simulator.
5. Compare the observed output distribution with the expected distribution.
6. Repair the program when linting or verification fails.
7. Export final OpenQASM, Qiskit-style Python, and PennyLane-style Python.

The implementation is intentionally local and reproducible. It does not require IBM Quantum hardware, Qiskit installation, or a paid LLM API. The template generator can be replaced by an Ollama/OpenAI/Hugging Face LLM while keeping the verifier and repair loop unchanged.

## Benchmark Summary

| Metric | Value |
|---|---:|
| Benchmark tasks | {len(df)} |
| Passed tasks | {int(df['passed'].sum())} |
| Pass rate | {pass_rate:.1f}% |
| Average total variation distance | {avg_tvd:.6f} |
| Average agent iterations | {avg_iter:.2f} |
| Tasks requiring repair | {int(repaired)} |

## Implemented Task Families

- State preparation: Bell, GHZ, uniform superposition.
- Algorithm generation: Grover search and Bernstein-Vazirani.
- Quantum error-correction coding: 3-qubit repetition-code encoding.
- Debugging and repair: missing entangling gate, incomplete Grover diffuser, invalid OpenQASM gate typo.
- Code migration/export: OpenQASM to Qiskit-style Python and PennyLane-style Python.

## Result Interpretation

The agent achieved **{pass_rate:.1f}% pass rate** on the offline benchmark. The intentionally buggy tasks required additional iterations, demonstrating the value of a verifier-in-the-loop approach. For student or research use, this can be extended into a true LLM-based quantum coding copilot by replacing `src/code_templates.py` with a model call and using the same simulator feedback for automatic repair.

## Suggested Research Paper Title

**Verifier-in-the-Loop Agentic AI Framework for Reliable Quantum Code Generation and Debugging**

## Future Enhancements

1. Add RAG over Qiskit, PennyLane, OpenQASM 3, and CUDA-Q documentation.
2. Replace the template generator with local LLMs such as CodeLlama, Qwen-Coder, DeepSeek-Coder, or a fine-tuned small model.
3. Add mutation-based quantum program repair using known bug patterns.
4. Add Qiskit Aer backend for larger circuits when Qiskit is installed.
5. Add OpenQASM 3 features such as gates, defcal, classical control, and timing.
6. Add benchmark comparison between zero-shot LLM, RAG-LLM, agentic repair, and verifier-only approaches.

## Reproduction

```bash
pip install -r requirements.txt
python experiments/run_experiment.py
```

Generated outputs are stored in `results/`.
"""
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    dirs = ensure_dirs()
    agent = QuantumCodeAgent(pass_tvd_threshold=0.02, max_iterations=3)
    traces = [agent.solve(task) for task in TASKS]

    rows = [trace_to_row(t) for t in traces]
    df = pd.DataFrame(rows)
    df.to_csv(dirs["results"] / "benchmark_results.csv", index=False)
    df.to_json(dirs["results"] / "benchmark_results.json", orient="records", indent=2)

    for trace in traces:
        (dirs["qasm"] / f"{trace.task_id}.qasm").write_text(trace.generated_qasm + "\n", encoding="utf-8")
        (dirs["py"] / f"{trace.task_id}_qiskit.py").write_text(trace.qiskit_code, encoding="utf-8")
        (dirs["py"] / f"{trace.task_id}_pennylane.py").write_text(trace.pennylane_code, encoding="utf-8")

    plot_results(df, dirs["plots"])
    write_report(df, traces, dirs["results"] / "implementation_report.md")

    print("G1 Quantum Code Agent benchmark complete")
    print(df[["task_id", "status", "iterations", "total_variation_distance", "repair_actions"]].to_string(index=False))


if __name__ == "__main__":
    main()
