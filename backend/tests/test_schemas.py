"""Configuration schema validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.configs import DiseaseConfig


def test_disease_config_validates_probability_range() -> None:
    with pytest.raises(ValidationError):
        DiseaseConfig(
            id="invalid",
            name="Invalid disease",
            transmission_probability=1.2,
            incubation_days=2,
            infectious_days=5,
        )


def test_disease_config_accepts_minimal_valid_profile() -> None:
    config = DiseaseConfig(
        id="test",
        name="Test profile",
        transmission_probability=0.1,
        incubation_days=2,
        infectious_days=5,
    )

    assert config.severe_case_probability == 0.05
