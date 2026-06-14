"""File-based config adapter tests."""

from pathlib import Path

from app.infrastructure.config_loader import ConfigLoader
from app.schemas.configs import DiseaseConfig

CONFIGS_DIRECTORY = Path(__file__).resolve().parents[2] / "configs"


def test_loads_example_disease_json() -> None:
    loader = ConfigLoader(CONFIGS_DIRECTORY)

    disease = loader.load_model("diseases", "respiratory_like_v1", DiseaseConfig)

    assert disease.id == "respiratory_like_v1"
    assert disease.transmission_probability == 0.08
