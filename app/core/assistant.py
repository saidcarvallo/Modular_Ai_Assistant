from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.conversation import ConversationManager
from app.core.prompts import SYSTEM_PROMPT
from app.memory.manager import MemoryManager
from app.model_manager.manager import ProviderManager
from app.tools.registry import build_tool_registry


@dataclass
class AetherAssistant:
    """Orchestrates provider selection, tool execution, and message generation."""

    provider_name: str = settings.active_provider
    conversation: ConversationManager = field(default_factory=ConversationManager)
    tool_registry: Any = field(init=False)
    provider_manager: ProviderManager = field(default_factory=ProviderManager)
    memory: MemoryManager = field(default_factory=MemoryManager)

    def __post_init__(self) -> None:
        self.tool_registry = build_tool_registry(memory=self.memory)

    def add_message(self, role: str, content: str) -> None:
        self.conversation.add_message(role, str(content))
        self.memory.save_conversation(role, str(content))

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation.history()

    def _provider_instance(self):
        provider_map = self.provider_manager.providers
        return provider_map.get(self.provider_name, provider_map["gemini"])

    def extract_tool_call(self, payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, dict):
            name = payload.get("name") or payload.get("tool_name")
            if name:
                args = payload.get("arguments") or payload.get("args") or {}
                return {"name": name, "arguments": args}
        if hasattr(payload, "name") and hasattr(payload, "args"):
            args = getattr(payload, "args", {}) or {}
            return {"name": getattr(payload, "name"), "arguments": dict(args) if hasattr(args, "items") else {"value": str(args)}}
        return None

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        name = tool_call.get("name")
        arguments = tool_call.get("arguments") or {}
        if not name:
            raise ValueError("Tool call does not contain a name")

        tool = self.tool_registry.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered")

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        if not isinstance(arguments, dict):
            arguments = {"value": arguments}

        return tool.handler(**arguments)

    async def generate_response(self, user_message: str, tools: Optional[List[Any]] = None) -> str:
        self.add_message("user", user_message)
        previous_turns = self.get_history()[:-1][-20:]
        prompt = user_message
        if previous_turns:
            history = "\n".join(
                f"{turn['role'].title()}: {turn['content']}" for turn in previous_turns
            )
            prompt = f"Conversation so far:\n{history}\n\nUser: {user_message}"

        provider_names = [self.provider_name]
        provider_names.extend(
            name for name in self.provider_manager.providers if name != self.provider_name
        )
        errors: list[str] = []
        declarations = tools or self.tool_registry.as_function_declarations()

        for provider_name in provider_names:
            provider = self.provider_manager.providers.get(provider_name)
            if provider is None or not provider.config.enabled:
                continue

            try:
                response = await provider.generate(
                    prompt,
                    system_prompt=SYSTEM_PROMPT,
                    tools=declarations,
                )
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")
                self.provider_manager.record_result(provider_name, success=False, error=exc)
                continue

            self.provider_name = provider_name
            self.provider_manager.active_provider = provider_name
            self.provider_manager.record_result(provider_name, success=True)
            tool_call = self.extract_tool_call(response)
            if tool_call is not None:
                try:
                    tool_result = self.execute_tool_call(tool_call)
                except Exception as exc:
                    message = f"The provider requested a tool, but it could not be completed: {exc}"
                    self.add_message("assistant", message)
                    return message

                follow_up_prompt = (
                    f"User request: {user_message}\n"
                    f"The tool '{tool_call['name']}' was executed with arguments "
                    f"{json.dumps(tool_call.get('arguments', {}), ensure_ascii=False)}. "
                    f"Result: {json.dumps(tool_result, ensure_ascii=False, default=str)}. "
                    "Based only on this result, answer the user succinctly."
                )
                try:
                    follow_up = await provider.generate(
                        follow_up_prompt,
                        system_prompt=(
                            "You are Aether. After a tool call, answer the user using the tool result. "
                            "Do not invent data beyond the tool output."
                        ),
                        tools=[],
                    )
                    self.add_message("assistant", str(follow_up))
                    return str(follow_up)
                except Exception as exc:
                    self.provider_manager.record_result(provider_name, success=False, error=exc)
                    message = (
                        f"The tool completed, but {provider_name} could not format its result: "
                        f"{json.dumps(tool_result, ensure_ascii=False, default=str)}"
                    )
                    self.add_message("assistant", message)
                    return message

            self.add_message("assistant", str(response))
            return str(response)

        if not errors:
            message = "No enabled provider is configured. Enable Gemini or Ollama in the Providers tab."
        else:
            message = "No provider could answer. " + " | ".join(errors)
        self.add_message("assistant", message)
        return message

    def send_message(self, user_message: str, tools: Optional[List[Any]] = None) -> str:
        return asyncio.run(self.generate_response(user_message, tools=tools))

    def get_memory_summary(self) -> dict[str, object]:
        return self.memory.get_user_memory_summary()
