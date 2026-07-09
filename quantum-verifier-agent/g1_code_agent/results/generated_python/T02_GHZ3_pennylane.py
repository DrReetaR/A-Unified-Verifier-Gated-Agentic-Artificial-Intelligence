import pennylane as qml
dev = qml.device('default.qubit', wires=3, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[0, 2])
    return qml.probs(wires=range(3))

print(circuit())
