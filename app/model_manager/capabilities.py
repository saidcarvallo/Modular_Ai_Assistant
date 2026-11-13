from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderCapabilities:
    name: str
    supports_function_calling: bool = False
    supports_streaming: bool = False
    free_tier_available: bool = False
    local_fallback_available: bool = False
    notes: Optional[str] = None


DEFAULT_CAPABILITIES = {
    "gemini": ProviderCapabilities(
        name="gemini",
        supports_function_calling=True,
        free_tier_available=True,
        notes="Gemini Flash models support function calling and are suitable for tool orchestration.",
    ),
    "ollama": ProviderCapabilities(
        name="ollama",
        supports_function_calling=True,
        local_fallback_available=True,
        notes="Local tool use depends on the selected model and available hardware resources.",
    ),
}
