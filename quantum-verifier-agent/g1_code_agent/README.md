# G1 Quantum Code-Generation and Debugging Agent

This project implements the **G1 future-enhancement direction** from the 150-paper analysis:

> Quantum software engineering and code-generation agents: quantum coding copilot, Qiskit/PennyLane/OpenQASM migration, quantum debugging agent.

## What is implemented

A runnable local prototype of a **verifier-in-the-loop quantum programming agent**:

1. Generates OpenQASM 2.0 programs for quantum tasks.
2. Lints the generated quantum program.
3. Simulates the circuit with a lightweight built-in statevector simulator.
4. Compares measured probability distribution with the expected distribution.
5. Repairs wrong or invalid circuits using feedback.
6. Exports final code in OpenQASM, Qiskit-style Python, and PennyLane-style Python.
7. Produces CSV/JSON results, plots, and a report.

## Why this is suitable for LLM / Agentic AI / GenAI research

The current offline generator uses verified templates so the project is reproducible without paid APIs. For research, replace `src/code_templates.py` with a local LLM or cloud LLM and keep the same lint/simulate/verify/repair loop. This makes it useful for comparing:

- zero-shot LLM quantum code generation,
- RAG-assisted generation,
- agentic repair,
- simulator feedback,
- mutation-based debugging,
- Qiskit/OpenQASM/PennyLane migration.

## Run

```bash
pip install -r requirements.txt
python experiments/run_experiment.py
```

## Output

- `results/benchmark_results.csv`
- `results/benchmark_results.json`
- `results/implementation_report.md`
- `results/generated_qasm/*.qasm`
- `results/generated_python/*_qiskit.py`
- `results/generated_python/*_pennylane.py`
- `results/plots/*.png`

## Recommended paper title

**Verifier-in-the-Loop Agentic AI Framework for Reliable Quantum Code Generation and Debugging**
