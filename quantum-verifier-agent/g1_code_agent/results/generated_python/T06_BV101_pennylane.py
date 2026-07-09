import pennylane as qml
dev = qml.device('default.qubit', wires=4, shots=1024)

@qml.qnode(dev)
def circuit():
    qml.PauliX(wires=3)
    qml.Hadamard(wires=0)
    qml.Hadamard(wires=1)
    qml.Hadamard(wires=2)
    qml.Hadamard(wires=3)
    qml.CNOT(wires=[0, 3])
    qml.CNOT(wires=[2, 3])
    qml.Hadamard(wires=0)
    qml.Hadamard(wires=1)
    qml.Hadamard(wires=2)
    return qml.probs(wires=range(4))

print(circuit())
