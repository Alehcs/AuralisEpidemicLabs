"""Deterministic population creation and schedule assignment."""

import random

from app.domain.agent import Agent, EpidemiologicalState, RoutineType
from app.domain.disease import DiseaseProfile
from app.domain.world import World, Zone
from app.schemas.configs import (
    AgentPopulationConfig,
    BehavioralProfileConfig,
    CognitiveDistributionConfig,
    InitialOutbreakConfig,
)

# Built-in additive cognitive biases keyed by recognizable profile names. They
# cover both the canonical Phase 4 archetypes (obedient, skeptical, curious,
# fatigued, altruistic, antisocial) and the existing population profile names so
# behavior is interpretable without forcing every config to redeclare biases.
# Population configs may override any of these via ``behavioral_profiles``.
DEFAULT_PROFILE_BIAS: dict[str, dict[str, float]] = {
    "obedient": {"trust_authority": 0.25, "compliance": 0.25, "skepticism": -0.15},
    "skeptical": {"trust_authority": -0.25, "skepticism": 0.3, "rumor_belief": 0.1},
    "skeptics": {"trust_authority": -0.25, "skepticism": 0.3, "rumor_belief": 0.1},
    "curious": {"curiosity": 0.35, "rumor_belief": 0.15, "trust_peers": 0.1},
    "fatigued": {"fatigue": 0.3, "compliance": -0.1},
    "evaders": {"trust_authority": -0.15, "compliance": -0.25, "skepticism": 0.2},
    "altruistic": {"compliance": 0.2, "trust_authority": 0.1, "trust_peers": 0.15},
    "altruists": {"compliance": 0.2, "trust_authority": 0.1, "trust_peers": 0.15},
    "antisocial": {"trust_peers": -0.25, "compliance": -0.2, "rumor_belief": 0.15},
    "griefers": {"trust_authority": -0.2, "compliance": -0.3, "rumor_belief": 0.25},
}

# Independent offset so cognitive draws never perturb the deterministic Phase 1-3
# population/outbreak random stream; same seed still reproduces identical state.
_COGNITION_SEED_OFFSET = 0x5F3759DF


class PopulationGenerator:
    """Create agents, assign stable routines/zones, and seed an outbreak."""

    def generate(
        self,
        config: AgentPopulationConfig,
        world: World,
        disease: DiseaseProfile,
        outbreak: InitialOutbreakConfig,
        seed: int,
    ) -> list[Agent]:
        """Return identical schedule assignments for identical inputs and seed."""

        rng = random.Random(seed)
        zones = list(world.zones.values())
        home_zones = self._zones_by_kind(zones, {"residential", "periphery"}) or zones
        profiles = [profile.profile for profile in config.profiles]
        profile_weights = [profile.proportion for profile in config.profiles]
        routines = [RoutineType(item.routine_type) for item in config.routines]
        routine_weights = [item.proportion for item in config.routines]

        agents = []
        for index in range(config.population_size):
            routine = rng.choices(routines, weights=routine_weights, k=1)[0]
            home = rng.choices(home_zones, weights=[zone.capacity for zone in home_zones], k=1)[0]
            work_zone_id, school_zone_id = self._assignment_for_routine(routine, world, rng)
            agents.append(
                Agent(
                    id=f"agent-{index:05d}",
                    profile=rng.choices(profiles, weights=profile_weights, k=1)[0],
                    zone_id=home.id,
                    home_zone_id=home.id,
                    work_zone_id=work_zone_id,
                    school_zone_id=school_zone_id,
                    routine_type=routine,
                    movement_tendency=round(rng.uniform(0.55, 1.0), 6),
                    compliance_tendency=round(rng.uniform(0.2, 0.95), 6),
                    isolation_compliance=round(rng.uniform(0.2, 0.95), 6),
                )
            )

        seed_count = outbreak.exposed_agents + outbreak.infected_agents
        seeded_agents = rng.sample(agents, seed_count)
        for agent in seeded_agents:
            agent.zone_id = outbreak.zone_id
            agent.current_intended_destination = outbreak.zone_id

        for agent in seeded_agents[: outbreak.exposed_agents]:
            agent.state = EpidemiologicalState.EXPOSED
            agent.exposed_at_tick = 0

        for agent in seeded_agents[outbreak.exposed_agents :]:
            asymptomatic = rng.random() < disease.asymptomatic_probability
            agent.state = (
                EpidemiologicalState.INFECTED_ASYMPTOMATIC
                if asymptomatic
                else EpidemiologicalState.INFECTED_SYMPTOMATIC
            )
            agent.exposed_at_tick = 0
            agent.infected_at_tick = 0
            agent.infectiousness = 0.65 if asymptomatic else 1.0

        self._initialize_cognition(agents, config, seed)
        return agents

    def _initialize_cognition(
        self,
        agents: list[Agent],
        config: AgentPopulationConfig,
        seed: int,
    ) -> None:
        """Assign deterministic, bounded socio-cognitive state per agent.

        Uses a dedicated seeded stream so the existing population/outbreak draws
        remain byte-identical to earlier phases.
        """

        cog_rng = random.Random(seed ^ _COGNITION_SEED_OFFSET)
        means = config.cognition
        for agent in agents:
            bias = self._profile_bias(config, agent.profile)
            agent.trust_authority = self._draw(
                cog_rng, means.trust_authority_mean, bias.trust_authority, means.spread
            )
            agent.trust_peers = self._draw(
                cog_rng, means.trust_peers_mean, bias.trust_peers, means.spread
            )
            agent.fatigue = self._draw(
                cog_rng, means.fatigue_mean, bias.fatigue, means.spread
            )
            agent.skepticism = self._draw(
                cog_rng, means.skepticism_mean, bias.skepticism, means.spread
            )
            agent.curiosity = self._draw(
                cog_rng, means.curiosity_mean, bias.curiosity, means.spread
            )
            agent.rumor_belief = self._draw(
                cog_rng, means.rumor_belief_mean, bias.rumor_belief, means.spread
            )
            compliance = self._draw(
                cog_rng, means.compliance_mean, bias.compliance, means.spread
            )
            agent.compliance_tendency = compliance
            agent.isolation_compliance = compliance
            agent.adaptive_compliance = compliance
            agent.memory_alert_accuracy = 0.5

    @staticmethod
    def _profile_bias(
        config: AgentPopulationConfig,
        profile: str,
    ) -> BehavioralProfileConfig:
        override = config.behavioral_profiles.get(profile)
        if override is not None:
            return override
        defaults = DEFAULT_PROFILE_BIAS.get(profile, {})
        return BehavioralProfileConfig(**defaults)

    @staticmethod
    def _draw(
        rng: random.Random,
        mean: float,
        bias: float,
        spread: float,
    ) -> float:
        value = mean + bias + rng.uniform(-spread, spread)
        return round(min(1.0, max(0.0, value)), 6)

    @staticmethod
    def _zones_by_kind(zones: list[Zone], kinds: set[str]) -> list[Zone]:
        return [zone for zone in zones if zone.kind in kinds]

    def _assignment_for_routine(
        self,
        routine: RoutineType,
        world: World,
        rng: random.Random,
    ) -> tuple[str | None, str | None]:
        zones = list(world.zones.values())
        by_kind = {zone.kind: zone.id for zone in zones}
        if routine == RoutineType.STUDENT:
            school = by_kind.get("mixed", "work_school")
            return None, school
        if routine == RoutineType.TRADER:
            return by_kind.get("commerce", "market"), None
        if routine == RoutineType.HEALTHCARE:
            return by_kind.get("healthcare", "hospital"), None
        if routine == RoutineType.WORKER:
            candidates = [
                zone.id for zone in zones if zone.kind in {"mixed", "commerce", "transport"}
            ]
            return rng.choice(candidates), None
        return None, None
