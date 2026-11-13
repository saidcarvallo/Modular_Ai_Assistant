from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Aether AI Personal Assistant", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(default="sqlite:///./aether.db", alias="DATABASE_URL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash-lite", alias="GEMINI_MODEL")
    ollama_model: str = Field(default="qwen3:8b", alias="OLLAMA_MODEL")
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")
    active_provider: str = Field(default="gemini", alias="ACTIVE_PROVIDER")

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def normalize_gemini_api_key(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        key = value.strip()
        if key.lower() in {"your_key_here", "your_api_key_here", "replace_me"}:
            return ""
        return key

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
