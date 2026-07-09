import pennylane as qml
dev = qml.device('default.qubit', wires=3, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.Hadamard(wires=1)
    qml.Hadamard(wires=2)
    return qml.probs(wires=range(3))

print(circuit())
