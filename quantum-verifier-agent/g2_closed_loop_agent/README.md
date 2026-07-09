# G2 Closed-Loop Quantum Control, Optimization & Experiment Agents

This package implements the G2 future-enhancement direction:

**Closed-loop quantum control, optimization & experiment agents**  
Best research possibility: **Autonomous VQC/QAOA design, quantum sensor copilot, hardware-safe experiment agent**.

The code is self-contained and runs without IBM Quantum access, paid LLM APIs, Qiskit, or PennyLane. It uses a lightweight NumPy state-vector simulator so students can run it on a normal laptop or Google Colab. The architecture is designed so an LLM/Agentic-AI layer can be added later as a proposal generator.

## Implemented Modules

1. **Autonomous VQC Design Agent** (`src/vqc_agent.py`)  
   Searches safe VQC templates, verifies them on a two-qubit parity/XOR task, and selects the smallest correct circuit.

2. **Autonomous QAOA Design Agent** (`src/qaoa_agent.py`)  
   Performs closed-loop QAOA parameter search for a weighted 4-node MaxCut problem using simulator feedback.

3. **Quantum Sensor Copilot** (`src/sensor_agent.py`)  
   Simulates adaptive Ramsey phase estimation using a Bayesian posterior and safe interrogation-time proposals.

4. **Hardware-Safety Guard** (`src/safety.py`)  
   Validates and repairs unsafe proposals before simulation/execution: qubit count, shots, circuit depth, layer count, pulse amplitude, duty cycle, and sensing time.

## Main Results

| Module | Metric | Result |
|---|---:|---:|
| Autonomous VQC design | Classification accuracy | 1.0000 |
| Autonomous QAOA design | Approximation ratio | 0.9649 |
| Autonomous QAOA design | Expected cut cost | 3.8598 |
| Quantum sensor copilot | Absolute phase error | 0.005843 |
| Quantum sensor copilot | Posterior std. | 0.006026 |
| Hardware-safety demo | Unsafe proposals repaired | 4/5 |

## How to Run

```bash
pip install -r requirements.txt
python experiments/run_experiment.py
```

Results will be regenerated in `results/` and plots in `plots/`.

## Files to Check

- `results/summary_results.csv` — overall metrics
- `results/qaoa_optimization_trace.csv` — closed-loop QAOA iterations
- `results/vqc_template_search.csv` — VQC architecture search result
- `results/sensor_adaptive_trace.csv` — adaptive sensing rounds
- `results/safety_guard_demo.csv` — unsafe proposal repair log
- `plots/*.png` — generated result graphs
- `docs/implementation_report.md` — detailed explanation
- `docs/G2_19_paper_to_component_mapping.csv` — mapping of the 19 G2 papers to prototype components

## Suggested Paper Title

**A Hardware-Safe Closed-Loop Agentic AI Framework for Autonomous VQC Design, QAOA Optimization, and Quantum Sensor Experiment Planning**
