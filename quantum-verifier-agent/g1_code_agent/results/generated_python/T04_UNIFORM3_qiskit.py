from qiskit import QuantumCircuit
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.h(1)
qc.h(2)
qc.measure(range(3), range(3))
