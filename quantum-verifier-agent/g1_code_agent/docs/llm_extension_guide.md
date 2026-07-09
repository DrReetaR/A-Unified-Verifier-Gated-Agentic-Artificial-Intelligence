# How to Extend This Prototype with an Actual LLM Agent

## Option A: Local Ollama model

Replace `QuantumCodeAgent._generate()` with a call to an Ollama model such as Qwen-Coder, DeepSeek-Coder, CodeLlama, or another coding model.

Suggested prompt:

```text
You are a quantum programming assistant. Generate valid OpenQASM 2.0 only.
Task: {task.prompt}
Constraints:
- Use qreg q[n] and creg c[n]
- Use only h, x, z, cx, cz, swap, ccx, measure
- End with measurement
Return only code.
```

Then send linter and simulator feedback back to the model:

```text
The generated OpenQASM failed verification.
Lint errors: {lint_errors}
Observed distribution: {observed_distribution}
Expected distribution: {expected_distribution}
Repair the OpenQASM code. Return only corrected code.
```

## Option B: RAG over quantum documentation

Add a vector database containing:

- Qiskit documentation
- PennyLane documentation
- OpenQASM 2/3 specifications
- quantum algorithm examples
- extracted method notes from the 33 G1 papers

The retrieval result should be included before code generation.

## Option C: Research comparison table

Compare four systems:

| System | Generator | Repair | Verifier |
|---|---|---|---|
| Baseline | template | no | simulator |
| LLM zero-shot | LLM | no | simulator |
| RAG-LLM | LLM + retrieved docs | no | simulator |
| Agentic verifier loop | LLM + retrieved docs | yes | simulator + lint |

Metrics:

- pass rate
- total variation distance
- syntax-error rate
- number of repair iterations
- token cost
- runtime
- hallucinated-gate rate
