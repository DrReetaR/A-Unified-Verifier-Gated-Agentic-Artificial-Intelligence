import pennylane as qml
dev = qml.device('default.qubit', wires=2, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.probs(wires=range(2))

print(circuit())
