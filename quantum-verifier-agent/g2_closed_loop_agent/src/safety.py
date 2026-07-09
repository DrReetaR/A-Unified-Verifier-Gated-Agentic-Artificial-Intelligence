"""Hardware-safety rules for experiment proposals.

The guard models a conservative pre-check that prevents an agent from sending
unsafe or impractical experiments to a real backend. In this educational version
it gates local simulations, but the same pattern can be placed before IBM
Quantum, Braket, IonQ, or lab-control APIs.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Tuple
import math


@dataclass
class HardwareLimits:
    max_qubits: int = 8
    max_shots: int = 4096
    max_depth: int = 64
    max_layers: int = 4
    max_abs_angle: float = 2 * math.pi
    max_pulse_amplitude: float = 1.0
    max_duty_cycle: float = 0.40
    min_interrogation_time: float = 0.05
    max_interrogation_time: float = 3.00


@dataclass
class ExperimentProposal:
    task_type: str
    n_qubits: int
    shots: int
    depth: int
    layers: int
    angles: Tuple[float, ...] = ()
    pulse_amplitude: float = 0.0
    duty_cycle: float = 0.0
    interrogation_time: float = 1.0
    notes: str = ""


@dataclass
class SafetyDecision:
    accepted: bool
    reasons: List[str]
    repaired: bool
    repaired_proposal: ExperimentProposal


class HardwareSafetyGuard:
    def __init__(self, limits: HardwareLimits | None = None):
        self.limits = limits or HardwareLimits()

    def check(self, proposal: ExperimentProposal) -> SafetyDecision:
        reasons: List[str] = []
        p = ExperimentProposal(**asdict(proposal))
        repaired = False

        if p.n_qubits > self.limits.max_qubits:
            reasons.append(f"n_qubits {p.n_qubits} exceeds limit {self.limits.max_qubits}")
            p.n_qubits = self.limits.max_qubits
            repaired = True
        if p.shots > self.limits.max_shots:
            reasons.append(f"shots {p.shots} exceeds limit {self.limits.max_shots}")
            p.shots = self.limits.max_shots
            repaired = True
        if p.depth > self.limits.max_depth:
            reasons.append(f"depth {p.depth} exceeds limit {self.limits.max_depth}")
            p.depth = self.limits.max_depth
            repaired = True
        if p.layers > self.limits.max_layers:
            reasons.append(f"layers {p.layers} exceeds limit {self.limits.max_layers}")
            p.layers = self.limits.max_layers
            repaired = True

        new_angles = []
        for a in p.angles:
            if abs(a) > self.limits.max_abs_angle:
                reasons.append(f"angle {a:.3f} clipped to ±{self.limits.max_abs_angle:.3f}")
                a = max(-self.limits.max_abs_angle, min(self.limits.max_abs_angle, a))
                repaired = True
            new_angles.append(a)
        p.angles = tuple(new_angles)

        if p.pulse_amplitude > self.limits.max_pulse_amplitude:
            reasons.append(f"pulse_amplitude {p.pulse_amplitude:.3f} exceeds {self.limits.max_pulse_amplitude:.3f}")
            p.pulse_amplitude = self.limits.max_pulse_amplitude
            repaired = True
        if p.duty_cycle > self.limits.max_duty_cycle:
            reasons.append(f"duty_cycle {p.duty_cycle:.3f} exceeds {self.limits.max_duty_cycle:.3f}")
            p.duty_cycle = self.limits.max_duty_cycle
            repaired = True
        if not (self.limits.min_interrogation_time <= p.interrogation_time <= self.limits.max_interrogation_time):
            reasons.append(
                f"interrogation_time {p.interrogation_time:.3f} outside "
                f"[{self.limits.min_interrogation_time:.3f}, {self.limits.max_interrogation_time:.3f}]"
            )
            p.interrogation_time = max(
                self.limits.min_interrogation_time,
                min(self.limits.max_interrogation_time, p.interrogation_time),
            )
            repaired = True

        # In this prototype, a repaired proposal is accepted after clipping.
        # A production system may reject instead of repairing depending on lab policy.
        accepted = True
        if not reasons:
            reasons.append("accepted: proposal within all configured hardware-safety limits")
        return SafetyDecision(accepted=accepted, reasons=reasons, repaired=repaired, repaired_proposal=p)
