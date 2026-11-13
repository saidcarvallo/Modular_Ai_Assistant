from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.config import settings
from app.model_manager.capabilities import DEFAULT_CAPABILITIES
from app.model_manager.fallback import classify_provider_error, fallback_order, should_retry
from app.providers.base import ProviderConfig, ProviderStatus
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider


@dataclass
class ProviderManager:
    providers: Dict[str, Any] = field(default_factory=dict)
    active_provider: str = settings.active_provider
    provider_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.providers["gemini"] = GeminiProvider(
            ProviderConfig(
                name="gemini",
                model=settings.gemini_model,
                api_key=settings.gemini_api_key,
                enabled=True,
                priority=1,
            )
        )
        self.providers["ollama"] = OllamaProvider(
            ProviderConfig(
                name="ollama",
                model=settings.ollama_model,
                host=settings.ollama_host,
                enabled=True,
                priority=2,
            )
        )
        for name in self.providers:
            self.provider_status[name] = {
                "healthy": None,
                "last_error": None,
                "last_success": None,
                "requests": 0,
            }

    def _status_entry(self, provider_name: str) -> Dict[str, Any]:
        if provider_name not in self.provider_status:
            self.provider_status[provider_name] = {
                "healthy": None,
                "last_error": None,
                "last_success": None,
                "requests": 0,
            }
        return self.provider_status[provider_name]

    def record_result(self, provider_name: str, *, success: bool, error: Exception | str | None = None) -> Dict[str, Any]:
        if provider_name not in self.providers:
            raise KeyError(f"Unknown provider: {provider_name}")

        status = self._status_entry(provider_name)
        status["requests"] = int(status.get("requests", 0)) + 1
        status["healthy"] = success
        if success:
            status["last_success"] = datetime.now(timezone.utc).isoformat()
            status["last_error"] = None
        if error is not None:
            status["last_error"] = str(error)
        elif not success:
            status["last_error"] = "provider unavailable"
        return status

    def validate_provider(self, provider_name: str) -> Dict[str, Any]:
        if provider_name not in self.providers:
            raise KeyError(f"Unknown provider: {provider_name}")

        provider = self.providers[provider_name]
        healthy = provider.health_check()
        validation_error = getattr(provider, "last_health_error", None)
        self.record_result(
            provider_name,
            success=healthy,
            error=None if healthy else validation_error or "validation failed",
        )
        if healthy:
            self.active_provider = provider_name
        return {
            "provider": provider_name,
            "healthy": healthy,
            "status": self._status_entry(provider_name),
        }

    def configure_provider(
        self,
        provider_name: str,
        *,
        api_key: str | None = None,
        model: str | None = None,
        enabled: bool | None = None,
        host: str | None = None,
    ) -> Dict[str, Any]:
        if provider_name not in self.providers:
            raise KeyError(f"Unknown provider: {provider_name}")

        provider = self.providers[provider_name]
        if api_key is not None:
            if provider.config.api_key != api_key:
                provider.config.api_key = api_key
                if isinstance(provider, GeminiProvider):
                    provider.reset_client()
        if model is not None:
            provider.config.model = model
        if enabled is not None:
            provider.config.enabled = enabled
        if host is not None:
            provider.config.host = host

        self.active_provider = provider_name if provider.config.enabled else self.active_provider
        self._status_entry(provider_name)["healthy"] = None
        return {
            "provider": provider_name,
            "enabled": provider.config.enabled,
            "model": provider.config.model,
            "host": provider.config.host,
            "api_key_configured": bool(provider.config.api_key),
        }

    def health_report(self) -> List[ProviderStatus]:
        report: List[ProviderStatus] = []
        for name in self.providers:
            status = self._status_entry(name)
            available = bool(status.get("healthy"))
            if not available and status.get("last_error") is None:
                last_error = "not validated yet" if status.get("healthy") is None else "provider not available"
            else:
                last_error = status.get("last_error")
            report.append(
                ProviderStatus(
                    provider=name,
                    available=available,
                    last_error=last_error,
                    last_success=status.get("last_success"),
                    requests=int(status.get("requests", 0)),
                )
            )
        return report

    def select_provider(self, preferred: str | None = None) -> str:
        choice = preferred or self.active_provider
        if choice in self.providers and self.providers[choice].health_check():
            self.active_provider = choice
            self.record_result(choice, success=True)
            return choice

        for name in fallback_order(self.providers.keys()):
            if name != choice and self.providers[name].health_check():
                self.active_provider = name
                self.record_result(name, success=True)
                return name

        self.active_provider = "gemini"
        self.record_result(self.active_provider, success=False, error="no healthy providers available")
        return self.active_provider

    def handle_error(self, provider_name: str, error: Exception | str, retry_count: int = 0) -> str:
        self.record_result(provider_name, success=False, error=error)
        category = classify_provider_error(error)
        if category == "authentication":
            return provider_name

        if should_retry(error, retry_count):
            next_provider = self.select_provider(provider_name)
            return next_provider

        for name in fallback_order(self.providers.keys()):
            if name != provider_name and self.providers[name].health_check():
                self.active_provider = name
                self.record_result(name, success=True)
                return name

        self.active_provider = provider_name
        return provider_name

    def capabilities(self) -> Dict[str, str]:
        return {name: str(details.supports_function_calling) for name, details in DEFAULT_CAPABILITIES.items()}

    def list_config(self) -> List[Dict[str, Any]]:
        results = []
        for name, provider in self.providers.items():
            status = self._status_entry(name)
            healthy = bool(status.get("healthy"))
            results.append(
                {
                    "provider": name,
                    "model": provider.config.model,
                    "enabled": provider.config.enabled,
                    "host": provider.config.host,
                    "api_key_configured": bool(provider.config.api_key),
                    "healthy": healthy,
                    "active": name == self.active_provider,
                    "last_error": status.get("last_error"),
                    "last_success": status.get("last_success"),
                    "requests": int(status.get("requests", 0)),
                }
            )
        return results
