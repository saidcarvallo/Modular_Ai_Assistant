from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ConversationMessage:
    role: str
    content: str


@dataclass
class ConversationManager:
    """Keeps the assistant's conversation state in memory for the MVP."""

    messages: List[ConversationMessage] = field(default_factory=list)

    def add_message(self, role: str, text: str) -> None:
        self.messages.append(ConversationMessage(role=role, content=text))

    def add_user_message(self, text: str) -> None:
        self.add_message("user", text)

    def add_assistant_message(self, text: str) -> None:
        self.add_message("assistant", text)

    def history(self) -> List[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in self.messages]
