"""File-based config adapter tests."""

from app.infrastructure.config_loader import ConfigLoader
from app.schemas.configs import DiseaseConfig

def test_loads_example_disease_json(config_loader: ConfigLoader) -> None:
    disease = config_loader.load_model("diseases", "respiratory_like_v1", DiseaseConfig)

    assert disease.id == "respiratory_like_v1"
    assert disease.beta_base == 0.08
    assert disease.tick_minutes == 60


def test_converts_validated_configs_to_domain(config_loader: ConfigLoader) -> None:
    scenario = config_loader.load_scenario("district_v1_market_outbreak")
    disease_config = config_loader.load_disease("respiratory_like_v1")

    world = config_loader.to_world(scenario)
    disease = config_loader.to_disease(disease_config)

    assert world.zones["market"].contact_rate == 18.0
    assert world.destinations_from("market")
    assert disease.incubation_ticks == 84


def test_policy_config_supports_explicit_phase_three_impacts(config_loader: ConfigLoader) -> None:
    policy = config_loader.to_policy(config_loader.load_policy("local_alert_policy"))

    assert policy.mobility_impact == 0.3
    assert policy.contact_impact == 0.35
    assert policy.target_zone_id == "market"
