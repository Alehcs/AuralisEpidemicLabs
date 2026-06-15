"""Tunable behavior/transmission strength parameters.

Phase 6 lifts the previously hand-tuned, module-level behavior constants into a
single immutable parameter object. Defaults reproduce Phase 5 behavior exactly,
so a simulation created without a behavior config is byte-for-byte unchanged.
The sensitivity sweep runner overrides individual fields to study their effect.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BehaviorParameters:
    """Bounded strengths controlling how behavior bends transmission."""

    # Transmission hazard modifiers.
    susceptible_protection_strength: float = 0.6
    infectious_protection_strength: float = 0.5
    risk_compensation_strength: float = 0.6
    # Contact mixing modifier.
    distancing_contact_strength: float = 0.5
    # Cognitive -> behavior coupling strengths.
    false_safety_amplification_strength: float = 0.45
    anti_authority_compliance_penalty: float = 0.15
    fatigue_protection_penalty: float = 0.35
    peer_warning_protection_boost: float = 0.0
