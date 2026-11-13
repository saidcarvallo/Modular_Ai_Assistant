from __future__ import annotations

import asyncio
from typing import Any

from google import genai
from google.genai import types

from app.providers.base import LLMProvider, ProviderConfig


class GeminiProvider(LLMProvider):
    """Gemini adapter that uses the official google-genai SDK."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = None
        self.last_health_error: str | None = None

    def health_check(self) -> bool:
        self.last_health_error = None
        if not self.config.enabled:
            self.last_health_error = "Gemini provider is disabled"
            return False
        if not self.config.api_key or len(self.config.api_key) < 10:
            self.last_health_error = "Gemini API key is missing or invalid"
            return False

        try:
            client = self._client_instance()
            client.models.generate_content(
                model=self.config.model,
                contents="Reply with OK",
                config=types.GenerateContentConfig(max_output_tokens=8),
            )
            return True
        except Exception as exc:
            self.last_health_error = str(exc).replace(self.config.api_key, "[redacted]")
            return False

    def _client_instance(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.config.api_key)
        return self._client

    def reset_client(self) -> None:
        self._client = None

    async def generate(self, prompt: str, *, system_prompt: str | None = None, tools: list[Any] | None = None) -> str | dict[str, Any]:
        if not self.config.enabled:
            raise RuntimeError("Gemini provider is disabled")
        if not self.config.api_key:
            raise RuntimeError("Gemini API key is missing")

        return await asyncio.to_thread(
            self._generate_sync,
            prompt,
            system_prompt=system_prompt,
            tools=tools,
        )

    def _generate_sync(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        tools: list[Any] | None = None,
    ) -> str | dict[str, Any]:
        client = self._client_instance()
        generate_config = types.GenerateContentConfig()

        if system_prompt:
            generate_config.system_instruction = system_prompt

        if tools:
            declarations = []
            for tool in tools:
                if hasattr(tool, "name") and hasattr(tool, "description") and hasattr(tool, "parameters"):
                    declarations.append(
                        types.FunctionDeclaration(
                            name=tool.name,
                            description=tool.description,
                            parameters=tool.parameters,
                        )
                    )
                elif isinstance(tool, dict):
                    declarations.append(
                        types.FunctionDeclaration(
                            name=tool.get("name", "unknown_tool"),
                            description=tool.get("description", "Tool without description."),
                            parameters=tool.get(
                                "parameters",
                                {"type": "object", "properties": {}},
                            ),
                        )
                    )
            if declarations:
                generate_config.tools = [types.Tool(function_declarations=declarations)]

        response = client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=generate_config,
        )

        if getattr(response, "text", None):
            return response.text

        candidate = getattr(response, "candidates", [None])[0]
        if candidate is None:
            return "Gemini returned an empty response."

        content = getattr(candidate, "content", None)
        if content is None:
            return "Gemini returned no content."

        parts = getattr(content, "parts", [])
        if not parts:
            return "Gemini returned no usable parts."

        first_part = parts[0]
        if hasattr(first_part, "text") and first_part.text:
            return first_part.text
        if hasattr(first_part, "function_call"):
            function_call = first_part.function_call
            args = getattr(function_call, "args", {}) or {}
            if hasattr(args, "items"):
                arguments = dict(args.items())
            elif isinstance(args, dict):
                arguments = dict(args)
            else:
                arguments = {"value": str(args)}
            return {
                "name": getattr(function_call, "name", "unknown_tool"),
                "arguments": arguments,
            }
        return str(first_part)
