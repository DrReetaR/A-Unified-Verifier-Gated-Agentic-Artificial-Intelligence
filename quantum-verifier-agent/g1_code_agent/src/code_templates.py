"""Template programs and target-language converters.

The project uses deterministic templates for the offline baseline. An actual LLM
can replace these functions while keeping the same verifier/repair loop.
"""
from __future__ import annotations

from textwrap import dedent


def get_qasm_template(task_id: str, mode: str = "correct") -> str:
    if task_id in {"T01_BELL", "T08_BUGGY_BELL", "T10_INVALID_GATE"}:
        if mode == "buggy":
            return dedent(
                """
                OPENQASM 2.0;
                include "qelib1.inc";
                qreg q[2];
                creg c[2];
                h q[0];
                measure q -> c;
                """
            ).strip()
        if mode == "invalid":
            return dedent(
                """
                OPENQASM 2.0;
                include "qelib1.inc";
                qreg q[2];
                creg c[2];
                h q[0];
                cxx q[0],q[1];
                measure q -> c;
                """
            ).strip()
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[2];
            creg c[2];
            h q[0];
            cx q[0],q[1];
            measure q -> c;
            """
        ).strip()

    if task_id == "T02_GHZ3":
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[3];
            creg c[3];
            h q[0];
            cx q[0],q[1];
            cx q[0],q[2];
            measure q -> c;
            """
        ).strip()

    if task_id == "T03_QRB":
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[1];
            creg c[1];
            h q[0];
            measure q -> c;
            """
        ).strip()

    if task_id == "T04_UNIFORM3":
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[3];
            creg c[3];
            h q[0];
            h q[1];
            h q[2];
            measure q -> c;
            """
        ).strip()

    if task_id in {"T05_GROVER2", "T09_BUGGY_GROVER"}:
        if mode == "buggy":
            return dedent(
                """
                OPENQASM 2.0;
                include "qelib1.inc";
                qreg q[2];
                creg c[2];
                h q[0];
                h q[1];
                cz q[0],q[1];
                measure q -> c;
                """
            ).strip()
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[2];
            creg c[2];
            h q[0];
            h q[1];
            cz q[0],q[1];
            h q[0];
            h q[1];
            x q[0];
            x q[1];
            cz q[0],q[1];
            x q[0];
            x q[1];
            h q[0];
            h q[1];
            measure q -> c;
            """
        ).strip()

    if task_id == "T06_BV101":
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[4];
            creg c[3];
            x q[3];
            h q[0];
            h q[1];
            h q[2];
            h q[3];
            cx q[0],q[3];
            cx q[2],q[3];
            h q[0];
            h q[1];
            h q[2];
            measure q[0] -> c[0];
            measure q[1] -> c[1];
            measure q[2] -> c[2];
            """
        ).strip()

    if task_id == "T07_REPETITION3":
        return dedent(
            """
            OPENQASM 2.0;
            include "qelib1.inc";
            qreg q[3];
            creg c[3];
            x q[0];
            cx q[0],q[1];
            cx q[0],q[2];
            measure q -> c;
            """
        ).strip()

    raise KeyError(f"No QASM template for {task_id}")


def qasm_to_qiskit_python(qasm: str, var_name: str = "qc") -> str:
    """Generate readable Qiskit code for the supported OpenQASM subset."""
    import re

    n_qubits = int(re.search(r"qreg\s+q\[(\d+)\]", qasm).group(1))
    n_cbits = int(re.search(r"creg\s+c\[(\d+)\]", qasm).group(1))
    lines = [
        "from qiskit import QuantumCircuit",
        f"{var_name} = QuantumCircuit({n_qubits}, {n_cbits})",
    ]
    for raw in qasm.splitlines():
        line = raw.strip().rstrip(";")
        if not line or line.startswith("OPENQASM") or line.startswith("include") or line.startswith("qreg") or line.startswith("creg"):
            continue
        if line.startswith("measure q -> c"):
            lines.append(f"{var_name}.measure(range({n_qubits}), range({min(n_qubits, n_cbits)}))")
            continue
        m = re.match(r"measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\]", line)
        if m:
            lines.append(f"{var_name}.measure({m.group(1)}, {m.group(2)})")
            continue
        gate = line.split()[0]
        qs = re.findall(r"q\[(\d+)\]", line)
        if len(qs) == 1:
            lines.append(f"{var_name}.{gate}({qs[0]})")
        elif len(qs) == 2:
            lines.append(f"{var_name}.{gate}({qs[0]}, {qs[1]})")
        elif len(qs) == 3:
            method = "ccx" if gate == "ccx" else gate
            lines.append(f"{var_name}.{method}({qs[0]}, {qs[1]}, {qs[2]})")
    return "\n".join(lines) + "\n"


def qasm_to_pennylane_python(qasm: str) -> str:
    """Generate an illustrative PennyLane script for supported gates."""
    import re

    n_qubits = int(re.search(r"qreg\s+q\[(\d+)\]", qasm).group(1))
    lines = [
        "import pennylane as qml",
        f"dev = qml.device('default.qubit', wires={n_qubits}, shots=1024)",
        "",
        "@qml.qnode(dev)",
        "def circuit():",
    ]
    for raw in qasm.splitlines():
        line = raw.strip().rstrip(";")
        if not line or line.startswith(("OPENQASM", "include", "qreg", "creg", "measure")):
            continue
        gate = line.split()[0]
        qs = [int(x) for x in re.findall(r"q\[(\d+)\]", line)]
        if gate == "h":
            lines.append(f"    qml.Hadamard(wires={qs[0]})")
        elif gate == "x":
            lines.append(f"    qml.PauliX(wires={qs[0]})")
        elif gate == "z":
            lines.append(f"    qml.PauliZ(wires={qs[0]})")
        elif gate == "cx":
            lines.append(f"    qml.CNOT(wires=[{qs[0]}, {qs[1]}])")
        elif gate == "cz":
            lines.append(f"    qml.CZ(wires=[{qs[0]}, {qs[1]}])")
        elif gate == "swap":
            lines.append(f"    qml.SWAP(wires=[{qs[0]}, {qs[1]}])")
        elif gate == "ccx":
            lines.append(f"    qml.Toffoli(wires=[{qs[0]}, {qs[1]}, {qs[2]}])")
    lines.append(f"    return qml.probs(wires=range({n_qubits}))")
    lines.append("")
    lines.append("print(circuit())")
    return "\n".join(lines) + "\n"
