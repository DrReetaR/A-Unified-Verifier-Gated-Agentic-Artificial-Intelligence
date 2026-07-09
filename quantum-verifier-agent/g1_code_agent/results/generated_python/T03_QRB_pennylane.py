import pennylane as qml
dev = qml.device('default.qubit', wires=1, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    return qml.probs(wires=range(1))

print(circuit())
