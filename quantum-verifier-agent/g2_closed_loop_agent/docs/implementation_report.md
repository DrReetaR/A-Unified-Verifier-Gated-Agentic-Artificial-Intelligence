# Implementation Report: G2 Closed-Loop Quantum Control, Optimization & Experiment Agents

## 1. Problem Statement

The G2 group contains papers focused on autonomous quantum experimentation, calibration, quantum control, variational-circuit design, QAOA optimization, and safety-gated execution. The common future enhancement is to move from static quantum programs to **closed-loop agentic systems** that propose, validate, execute, observe, and improve quantum experiments.

This project implements a practical prototype that can be executed locally. It does not require physical quantum hardware. The implemented framework contains four components:

- Autonomous VQC architecture-search agent
- Autonomous QAOA MaxCut optimization agent
- Adaptive quantum sensor copilot
- Hardware-safety guard for agent proposals

## 2. Research Gap Addressed

Many LLM/agentic quantum-computing papers show promising workflows, but direct hardware execution can be unsafe or expensive. This implementation therefore places a **safety gate** before every agent proposal and uses a **simulator-in-the-loop** for verification. This makes the workflow suitable for teaching, reproducible experiments, and later migration to real backends.

## 3. Proposed Architecture

```text
User Goal / Quantum Task
        ↓
Agent Proposal Generator
        ↓
Hardware Safety Guard
        ↓
Local Simulator / Backend Tool
        ↓
Metric Evaluation
        ↓
Closed-Loop Memory and Next Proposal
```

The present package uses deterministic/rule-based proposal generation. The upgrade path is to replace the proposal generator with an LLM, RAG, or multi-agent planner while keeping the same safety and verification layer.

## 4. Module 1: Autonomous VQC Design

The VQC agent searches circuit templates for a two-qubit parity/XOR benchmark. The safety guard checks circuit size and execution parameters before evaluation. The selected template was:

**entangled_parity_vqc**

Results:

- Accuracy: **1.0000**
- Loss: **0.000000**
- Trainable parameters: **1**
- Closed-loop iterations: **180**

This demonstrates an autonomous circuit-selection loop where correctness is verified using simulator feedback.

## 5. Module 2: Autonomous QAOA MaxCut Design

The QAOA agent solves a weighted four-node MaxCut problem. It searches over safe p-layer QAOA circuits and angles, then locally refines the best solution.

Results:

- Graph: **weighted_4_node_ring_plus_diagonal**
- Qubits: **4**
- Selected QAOA layers: **p = 2**
- Expected cut cost: **3.859753**
- Approximation ratio: **0.964938**
- Closed-loop iterations: **240**

Best angles:

```json
{
  "gammas": [
    2.323250919880003,
    2.6372330707532137
  ],
  "betas": [
    0.9506381681052898,
    1.2716752434877385
  ]
}
```

Top measured bitstrings are stored in `results/qaoa_top_bitstrings.csv`.

## 6. Module 3: Quantum Sensor Copilot

The sensor copilot simulates a Ramsey phase-estimation workflow. The agent adaptively chooses the interrogation time, performs simulated measurement, updates a Bayesian posterior, and repeats.

Results:

- True phase used in simulation: **0.6200**
- Final estimate: **0.625843**
- Absolute error: **0.005843**
- Posterior standard deviation: **0.006026**
- Rounds: **14**
- Shots per round: **256**

The safety guard repaired interrogation-time proposals that exceeded the configured hardware limit.

## 7. Module 4: Hardware-Safety Guard

The safety guard prevents unsafe agent actions before execution. It checks:

- Maximum qubits
- Maximum shots
- Maximum circuit depth
- Maximum QAOA/VQC layers
- Angle bounds
- Pulse amplitude
- Duty cycle
- Sensor interrogation time

In the safety demo, **4 out of 5** proposals required repair. The detailed log is available in `results/safety_guard_demo.csv`.

## 8. How LLM / Agentic AI / GenAI Can Be Incorporated

The current prototype uses rule-based proposal generation. To convert it into a full LLM-agentic system:

1. Add a RAG index over Qiskit, PennyLane, OpenQASM, ARTIQ, and hardware manuals.
2. Let the LLM generate candidate VQC/QAOA/control proposals in JSON.
3. Send every proposal to `HardwareSafetyGuard`.
4. Execute accepted proposals using simulator tools.
5. Feed metrics back to the LLM as observations.
6. Repeat until the objective is reached or safety/human-approval limits stop the run.

## 9. Suggested Research Paper Structure

Title: **A Hardware-Safe Closed-Loop Agentic AI Framework for Autonomous VQC Design, QAOA Optimization, and Quantum Sensor Experiment Planning**

Sections:

1. Introduction
2. Literature Survey on Agentic Quantum Computing
3. Proposed Safety-Gated Closed-Loop Framework
4. VQC Architecture Search Method
5. QAOA Optimization Method
6. Quantum Sensor Copilot Method
7. Results and Discussion
8. Limitations and Future Enhancement

## 10. Future Enhancement

- Add real LLM proposal generation with local Ollama models or API-based LLMs.
- Add Qiskit/PennyLane code emitters for selected circuits.
- Add formal verification rules for quantum circuits.
- Add real backend execution after human approval.
- Add multi-agent roles: planner, safety officer, simulator, debugger, report writer.
