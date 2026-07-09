# Verifier-Gated Agentic AI for Reliable Quantum Software and Control

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tools/grammar/test_firstperson_cleaner.py)

Reference implementation for the paper **"A Unified Verifier-Gated Agentic AI
Framework for Reliable Quantum Code Generation, Autonomous Circuit Design, and
Closed-Loop Quantum Control."**

The central idea: in quantum software automation, reliability comes from a strong
**verifier** and a **safety guard** inside the agent loop, not from a larger
generator. Two cooperating agents share one
`plan → generate → check → repair` contract. Everything runs **offline** on exact
state-vector simulators — no quantum hardware, vendor cloud, or paid model required.

---

## Highlights

| Agent | Benchmark | Result |
|---|---|---|
| **G1** Verifier-in-the-loop code agent | 10-task OpenQASM suite | **100% pass**, mean TVD ≈ 2.2×10⁻¹⁶, avg **1.30** iterations, 3/3 injected bugs repaired |
| **G2** Autonomous VQC design | two-qubit parity (XOR) | **100% accuracy**, selects minimal entangled circuit (1 parameter) |
| **G2** Closed-loop QAOA | weighted 4-node MaxCut | approximation ratio **0.965** (cut 3.8598 / optimum 4.0) |
| **G2** Adaptive quantum sensing | Ramsey phase estimation | phase error **5.8×10⁻³ rad**, σ reduced ~14× |
| **G2** Hardware-safety guard | unsafe-proposal stress test | **4/4 unsafe proposals repaired** |

All numbers are regenerated from the code in this repository.

---

## Repository structure

```
quantum-verifier-agent/
├── g1_code_agent/            # Agent I: quantum code generation, verification, repair
│   ├── src/                  #   agent, OpenQASM simulator, tasks, code templates
│   ├── experiments/          #   run_experiment.py (reproduces the benchmark)
│   ├── results/              #   benchmark CSV/JSON, generated code, plots
│   ├── data/                 #   reference-paper metadata
│   └── notebooks/            #   Colab-ready demo
├── g2_closed_loop_agent/     # Agent II: closed-loop control & optimization
│   ├── src/                  #   qaoa_agent, vqc_agent, sensor_agent, safety, simulator
│   ├── experiments/          #   run_experiment.py (reproduces all G2 results)
│   ├── results/              #   traces, summaries
│   └── plots/                #   figures
├── paper/                    # Manuscript (LaTeX + PDF + DOCX) and figures
├── tools/grammar/            # First-person grammar checker + pytest suite
├── requirements.txt
├── LICENSE                   # MIT
└── CITATION.cff
```

---

## Quick start

```bash
git clone https://github.com/<your-username>/quantum-verifier-agent.git
cd quantum-verifier-agent
pip install -r requirements.txt
```

Reproduce **G1** (code agent) results:

```bash
cd g1_code_agent
python experiments/run_experiment.py
# -> results/benchmark_results.csv, generated_qasm/, generated_python/, plots/
```

Reproduce **G2** (closed-loop agent) results:

```bash
cd g2_closed_loop_agent
python experiments/run_experiment.py
# -> results/summary_results.{csv,json}, traces, plots/
```

Both runs are deterministic (fixed seeds) and reproduce the reported metrics
identically.

---

## Method in one paragraph

A task is solved by iterating a fixed contract: an artifact is *generated*, then an
executable oracle *verifies* it; on failure the same feedback drives a bounded
*repair*, terminating within `K` iterations. **G1** defines correctness as the
total-variation distance between the simulated measurement distribution and a task
target `p*` (pass threshold `τ = 0.02`). **G2** replaces the software oracle with
physics simulators and inserts a **hardware-safety guard** that clips or gates every
proposal (qubits, shots, depth, layers, angles, pulse amplitude, duty cycle,
interrogation time) before execution. The generator/proposer is the only component to
swap for a full LLM deployment; the verifier, guard, and guarantees are unchanged.

---

## Grammar tool (academic writing)

`tools/grammar/` contains a deterministic first-person cleaner used to keep the
manuscript in impersonal voice (removes `we/our/us/I/...` and rephrases).

```bash
cd tools/grammar
pytest -v test_firstperson_cleaner.py     # 55 tests
python firstperson_cleaner.py "We show that our method works."
# -> "This work shows that the method works."
```

---

## Citation

If this repository is useful, please cite the accompanying paper (see
[`CITATION.cff`](CITATION.cff) and `paper/`).

## License

Released under the [MIT License](LICENSE).
