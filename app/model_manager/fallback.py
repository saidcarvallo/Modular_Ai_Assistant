from __future__ import annotations

from typing import Iterable


def classify_provider_error(error: Exception | str) -> str:
    message = str(error).lower()
    if "quota" in message or "rate limit" in message or "limit" in message or "429" in message:
        return "quota"
    if "unauthorized" in message or "authentication" in message or "api key" in message or "401" in message:
        return "authentication"
    if "connection" in message or "timeout" in message or "unreachable" in message or "refused" in message:
        return "connectivity"
    if "unsupported" in message or "compatibility" in message or "tool" in message:
        return "compatibility"
    return "unknown"


def fallback_order(enabled_providers: Iterable[str]) -> list[str]:
    preferred = ["gemini", "ollama"]
    ordered = [provider for provider in preferred if provider in set(enabled_providers)]
    extras = [provider for provider in enabled_providers if provider not in ordered]
    return ordered + extras


def should_retry(error: Exception | str, retry_count: int, max_retries: int = 2) -> bool:
    if retry_count >= max_retries:
        return False
    category = classify_provider_error(error)
    return category not in {"authentication"}
