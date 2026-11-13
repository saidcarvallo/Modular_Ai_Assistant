from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib import error, request

from app.providers.base import LLMProvider, ProviderConfig


class OllamaProvider(LLMProvider):
    """Local Ollama adapter for offline or fallback operation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def health_check(self) -> bool:
        if not self.config.enabled or not self.config.host:
            return False

        endpoint = self.config.host.rstrip("/") + "/api/tags"
        try:
            with request.urlopen(endpoint, timeout=2) as response:
                payload = response.read()
            parsed = json.loads(payload.decode("utf-8"))
            return isinstance(parsed, dict) or isinstance(parsed, list)
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, OSError):
            return False

    def _generate_sync(self, prompt: str, *, system_prompt: str | None = None, tools: list[Any] | None = None) -> str | dict[str, Any]:
        if not self.config.host:
            raise RuntimeError("Ollama host is missing")
        if not self.config.model:
            raise RuntimeError("Ollama model is missing")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "unknown_tool"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                    },
                }
                for tool in tools
                if isinstance(tool, dict)
            ]

        body = json.dumps(payload).encode("utf-8")
        endpoint = self.config.host.rstrip("/") + "/api/chat"
        http_request = request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not connect to Ollama at {endpoint}: {exc.reason}") from exc
        except (TimeoutError, OSError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned invalid JSON") from exc

        message = result.get("message")
        if not isinstance(message, dict):
            raise RuntimeError(f"Ollama response did not contain a message: {result}")

        tool_calls = message.get("tool_calls")
        if tool_calls:
            call = tool_calls[0].get("function", {})
            if call.get("name"):
                return {
                    "name": call["name"],
                    "arguments": call.get("arguments") or {},
                }

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama returned an empty response")
        return content

    async def generate(self, prompt: str, *, system_prompt: str | None = None, tools: list[Any] | None = None) -> str | dict[str, Any]:
        if not self.config.enabled:
            raise RuntimeError("Ollama provider is disabled")

        return await asyncio.to_thread(
            self._generate_sync,
            prompt,
            system_prompt=system_prompt,
            tools=tools,
        )
