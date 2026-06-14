"""Configuration schema validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.configs import DiseaseConfig


def test_disease_config_validates_probability_range() -> None:
    with pytest.raises(ValidationError):
        DiseaseConfig(
            id="invalid",
            name="Invalid disease",
            beta_base=1.2,
            incubation_days=2,
            infectious_days=5,
        )


def test_disease_config_accepts_minimal_valid_profile() -> None:
    config = DiseaseConfig(
        id="test",
        name="Test profile",
        beta_base=0.1,
        incubation_days=2,
        infectious_days=5,
    )

    assert config.asymptomatic_probability == 0.4
    assert config.tick_minutes == 60
