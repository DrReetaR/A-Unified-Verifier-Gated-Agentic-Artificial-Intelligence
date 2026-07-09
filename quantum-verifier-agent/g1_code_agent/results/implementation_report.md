# G1 Implementation Report: Quantum Code-Generation and Debugging Agent

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
| Benchmark tasks | 10 |
| Passed tasks | 10 |
| Pass rate | 100.0% |
| Average total variation distance | 0.000000 |
| Average agent iterations | 1.30 |
| Tasks requiring repair | 3 |

## Implemented Task Families

- State preparation: Bell, GHZ, uniform superposition.
- Algorithm generation: Grover search and Bernstein-Vazirani.
- Quantum error-correction coding: 3-qubit repetition-code encoding.
- Debugging and repair: missing entangling gate, incomplete Grover diffuser, invalid OpenQASM gate typo.
- Code migration/export: OpenQASM to Qiskit-style Python and PennyLane-style Python.

## Result Interpretation

The agent achieved **100.0% pass rate** on the offline benchmark. The intentionally buggy tasks required additional iterations, demonstrating the value of a verifier-in-the-loop approach. For student or research use, this can be extended into a true LLM-based quantum coding copilot by replacing `src/code_templates.py` with a model call and using the same simulator feedback for automatic repair.

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
