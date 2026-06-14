"""Light peer-to-peer social influence via zone co-location.

Rather than a full social-network graph, agents that share a zone on a given tick
exert aggregate "pressure" on one another. Each zone's pressures are computed once
from the co-located agents, then applied to every agent in that zone. This stays
O(agents) per tick and fully deterministic (no randomness).

Pressures spread false-safety, anti-authority and panic beliefs, and also
propagate genuine peer warnings from trusting, worried agents. The nudges are
small so beliefs evolve gradually and stay bounded to [0, 1].
"""

from collections import defaultdict
from dataclasses import dataclass, field

from app.domain.agent import Agent

# Adoption rate of co-located "atmosphere" into personal peer-exposure signals.
_PEER_EMA = 0.2
# Slow propagation rate of actual beliefs between co-located agents.
_SPREAD = 0.08


@dataclass(frozen=True, slots=True)
class SocialUpdate:
    """Per-zone social pressures plus district-wide means for metrics."""

    zone_pressures: dict[str, dict[str, float]] = field(default_factory=dict)
    mean_rumor_pressure: float = 0.0
    mean_peer_warning_pressure: float = 0.0


class SocialInfluenceEngine:
    """Spread rumors and warnings through shared-zone presence."""

    def step(
        self,
        agents: list[Agent],
        zone_ids: tuple[str, ...],
        tick: int,
    ) -> SocialUpdate:
        by_zone: dict[str, list[Agent]] = defaultdict(list)
        for agent in agents:
            by_zone[agent.zone_id].append(agent)

        zone_pressures: dict[str, dict[str, float]] = {
            zone_id: self._empty_pressures() for zone_id in zone_ids
        }
        rumor_sum = 0.0
        warning_sum = 0.0
        for zone_id, local in by_zone.items():
            count = len(local)
            false_safety = sum(a.safety_rumor_exposure * a.rumor_belief for a in local) / count
            anti_authority = sum(a.anti_authority_exposure * a.rumor_belief for a in local) / count
            panic = sum(a.danger_rumor_exposure * a.rumor_belief for a in local) / count
            rumor = sum(a.rumor_exposure for a in local) / count
            warning = sum(a.perceived_risk * a.trust_authority for a in local) / count
            zone_pressures[zone_id] = {
                "rumor_pressure": round(rumor, 6),
                "false_safety_pressure": round(false_safety, 6),
                "anti_authority_pressure": round(anti_authority, 6),
                "panic_pressure": round(panic, 6),
                "peer_warning_pressure": round(warning, 6),
            }
            rumor_sum += rumor * count
            warning_sum += warning * count
            self._apply_zone(local, false_safety, anti_authority, panic, rumor, warning)

        total = len(agents) or 1
        return SocialUpdate(
            zone_pressures=zone_pressures,
            mean_rumor_pressure=round(rumor_sum / total, 6),
            mean_peer_warning_pressure=round(warning_sum / total, 6),
        )

    def _apply_zone(
        self,
        local: list[Agent],
        false_safety: float,
        anti_authority: float,
        panic: float,
        rumor: float,
        warning: float,
    ) -> None:
        bad_atmosphere = self._bounded(false_safety + anti_authority + panic)
        for agent in local:
            receptivity = 1.0 - agent.skepticism
            agent.peer_rumor_exposure = self._bounded(
                agent.peer_rumor_exposure * (1.0 - _PEER_EMA)
                + _PEER_EMA * bad_atmosphere * receptivity
            )
            agent.peer_warning_exposure = self._bounded(
                agent.peer_warning_exposure * (1.0 - _PEER_EMA) + _PEER_EMA * warning
            )
            agent.social_influence_exposure = self._bounded(
                0.5 * agent.peer_rumor_exposure + 0.5 * agent.peer_warning_exposure
            )
            # Beliefs physically diffuse between co-located agents.
            agent.safety_rumor_exposure = self._bounded(
                agent.safety_rumor_exposure + _SPREAD * false_safety * receptivity
            )
            agent.anti_authority_exposure = self._bounded(
                agent.anti_authority_exposure + _SPREAD * anti_authority * receptivity
            )
            agent.rumor_belief = self._bounded(
                agent.rumor_belief + 0.02 * rumor * receptivity
            )
            # Social anti-authority erodes trust in authority; warnings build peer trust.
            agent.trust_authority = self._bounded(
                agent.trust_authority - _SPREAD * anti_authority * agent.rumor_belief
            )
            agent.trust_peers = self._bounded(agent.trust_peers + 0.01 * warning)

    @staticmethod
    def _empty_pressures() -> dict[str, float]:
        return {
            "rumor_pressure": 0.0,
            "false_safety_pressure": 0.0,
            "anti_authority_pressure": 0.0,
            "panic_pressure": 0.0,
            "peer_warning_pressure": 0.0,
        }

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
