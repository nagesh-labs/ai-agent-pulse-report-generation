"""Unit tests for configuration loading and validation."""

from pathlib import Path
from src.config.settings import ProjectSettings


def test_settings_load_from_yaml():
    """Verify that config/settings.yaml parses cleanly and adheres to constraints."""
    config_path = Path("config/settings.yaml")
    assert config_path.exists(), "config/settings.yaml must exist"

    settings = ProjectSettings.load_from_yaml(config_path)

    # App constraints
    assert settings.app.package_id == "com.nextbillion.groww"
    assert settings.app.platform == "google_play"
    assert settings.app.country == "in"

    # Ingestion constraints (8–12 weeks)
    assert 8 <= settings.ingestion.default_weeks_back <= 12
    assert settings.ingestion.min_weeks == 8
    assert settings.ingestion.max_weeks == 12

    # Agent constraints (Groq Llama 3.3 70B, max 5 themes, max 250 words, 3 top themes, 3 quotes, 3 actions)
    assert settings.agent.provider == "groq"
    assert "llama-3.3" in settings.agent.model_name
    assert settings.agent.max_themes <= 5
    assert settings.agent.top_themes_count == 3
    assert settings.agent.quotes_count == 3
    assert settings.agent.action_ideas_count == 3
    assert settings.agent.max_word_count <= 250


def test_settings_defaults():
    """Verify fallback to defaults when custom path does not exist."""
    settings = ProjectSettings.load_from_yaml("non_existent_config.yaml")
    assert settings.app.package_id == "com.nextbillion.groww"
    assert settings.agent.max_themes <= 5
    assert settings.agent.max_word_count <= 250

