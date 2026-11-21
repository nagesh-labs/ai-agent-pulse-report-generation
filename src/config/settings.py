"""Configuration loader and schema validator for the Mobile App Feedback Pulse project."""

from pathlib import Path
from typing import Optional
import os
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if present
load_dotenv()


class AppConfig(BaseModel):
    package_id: str = "com.nextbillion.groww"
    platform: str = "google_play"
    country: str = "in"
    lang: str = "en"


class IngestionConfig(BaseModel):
    default_weeks_back: int = Field(default=10, ge=8, le=12)
    min_weeks: int = 8
    max_weeks: int = 12
    batch_size: int = 200
    max_reviews_sample: int = 1500
    rate_limit_delay_seconds: float = 1.0
    min_word_count: int = Field(default=9, description="Strictly more than 8 words (>=9)")
    remove_emojis: bool = True
    english_only: bool = True


class AgentConfig(BaseModel):
    provider: str = "groq"
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.2
    api_key_env: str = "GROQ_API_KEY"
    max_themes: int = Field(default=5, le=5)
    top_themes_count: int = 3
    quotes_count: int = 3
    action_ideas_count: int = 3
    max_word_count: int = Field(default=250, le=250)

    @property
    def api_key(self) -> str:
        """Resolve Groq API key from environment."""
        return os.environ.get(self.api_key_env, "").strip()


class DeliveryConfig(BaseModel):
    email_recipient: str = "nagesh14423@gmail.com"
    pulse_title_prefix: str = "[Weekly Pulse] Groww App Reviews"
    google_doc_id: str = "1chaQkkUovsVC7OGYM1HOSiPPFGW3bdcuOKSm6eLopSM"


class MCPConfig(BaseModel):
    server_url: str = "https://ai-agent-mcp-server.vercel.app/sse"
    health_url: str = "https://ai-agent-mcp-server.vercel.app/health"
    auth_key_env: str = "MCP_AUTH_KEY"
    timeout_seconds: float = 30.0

    @property
    def auth_key(self) -> str:
        """Resolve authentication key from environment or settings."""
        return os.environ.get(self.auth_key_env, "").strip()


class StorageConfig(BaseModel):
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")


class ProjectSettings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path | str] = None) -> "ProjectSettings":
        """Load configuration from a YAML file, falling back to defaults if not found."""
        if config_path is None:
            config_path = Path("config/settings.yaml")
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            return cls()

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)


# Global default instance
settings = ProjectSettings.load_from_yaml()
