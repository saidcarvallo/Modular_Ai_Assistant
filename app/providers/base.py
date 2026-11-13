from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ProviderType(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"


@dataclass
class ProviderConfig:
    name: str
    model: str
    api_key: str = ""
    host: str = ""
    enabled: bool = True
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStatus:
    provider: str
    available: bool
    last_error: Optional[str] = None
    last_success: Optional[str] = None
    requests: int = 0
    tokens_used: int = 0


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
    ) -> str | Dict[str, Any]:
        raise NotImplementedError

    def stats(self) -> Dict[str, Any]:
        return {"provider": self.name, "model": self.config.model, "enabled": self.config.enabled}
