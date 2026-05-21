import json
from functools import lru_cache
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_env_csv_or_json_list(
    value: str,
    *,
    empty_fallback: Optional[list[str]] = None,
) -> list[str]:
    """Parse .env list values: JSON array (e.g. '["a","b"]') or comma-separated ('a,b')."""
    s = value.strip()
    if not s:
        return list(empty_fallback) if empty_fallback is not None else []
    if s.startswith("["):
        parsed = json.loads(s)
        if not isinstance(parsed, list):
            raise ValueError("JSON CORS/API keys value must be an array")
        return [str(x).strip() for x in parsed if str(x).strip()]
    return [part.strip() for part in s.split(",") if part.strip()]


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    api_title: str = "Customer Service Chatbot API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM Configuration
    llm_provider: str = "openai"  # Options: openai, anthropic
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    model_name: str = "gpt-4o"  # or claude-3-5-sonnet-20240620
    temperature: float = 0.7
    max_tokens: int = 1000

    # Vector Store Configuration
    embeddings_model: str = "text-embedding-3-small"
    vector_store_path: str = "./data/vectorstore"
    knowledge_base_path: str = "./data/knowledge_base"

    # Conversation Configuration
    max_conversation_history: int = 10
    conversation_memory_type: str = "buffer"  # Options: buffer, summary, window

    # Rate Limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # Security — stored as str so .env can use comma-separated lists (not JSON-only).
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8501",
        description="Comma-separated origins or a JSON array string.",
    )
    api_key_header: str = "X-API-Key"
    require_api_key: bool = False
    valid_api_keys: str = Field(
        default="",
        description="Comma-separated keys or a JSON array string.",
    )

    # Database (optional)
    database_url: Optional[str] = "sqlite:///./data/conversations.db"

    # Business Configuration
    company_name: str = "Your Company"
    support_email: str = "support@yourcompany.com"
    business_hours: str = "Monday-Friday, 9 AM - 5 PM EST"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return parse_env_csv_or_json_list(
            self.cors_origins,
            empty_fallback=["http://localhost:3000", "http://localhost:8501"],
        )

    @property
    def valid_api_keys_list(self) -> list[str]:
        return parse_env_csv_or_json_list(self.valid_api_keys)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
