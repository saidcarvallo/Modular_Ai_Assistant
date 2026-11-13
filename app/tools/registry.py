from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict

from app.memory.manager import MemoryManager
from app.tools.notes import NotesTool
from app.tools.reminders import ReminderTool
from app.tools.tasks import TaskTool


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any]
    parameters: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """Explicit list of tools the model may request."""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def as_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self.list()
        ]

    def as_function_declarations(self) -> list[dict[str, Any]]:
        return self.as_schema()

    def execute(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered")
        return tool.handler(**kwargs)


def build_tool_registry(memory: MemoryManager | None = None) -> ToolRegistry:
    registry = ToolRegistry()

    task_tool = TaskTool(memory=memory)
    reminder_tool = ReminderTool(memory=memory)
    notes_tool = NotesTool(memory=memory)
    registry.register(
        ToolSpec(
            name="create_task",
            description="Create a new task for the user.",
            handler=task_tool.create_task,
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title for the task."},
                    "description": {"type": "string", "description": "Optional task description."},
                },
                "required": ["title"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="list_tasks",
            description="List the current tasks.",
            handler=task_tool.list_tasks,
            parameters={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="complete_task",
            description="Mark a task as completed.",
            handler=task_tool.complete_task,
            parameters={
                "type": "object",
                "properties": {"task_id": {"type": "integer", "description": "ID of the task to mark complete."}},
                "required": ["task_id"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="delete_task",
            description="Delete a task using its task ID.",
            handler=task_tool.delete_task,
            parameters={
                "type": "object",
                "properties": {"task_id": {"type": "integer", "description": "ID of the task to delete."}},
                "required": ["task_id"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="create_reminder",
            description="Create a reminder for a specific time or text message.",
            handler=reminder_tool.create_reminder,
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Reminder text."},
                    "scheduled_for": {"type": "string", "description": "Optional ISO datetime for the reminder."},
                },
                "required": ["message"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="list_upcoming_reminders",
            description="List upcoming reminders.",
            handler=reminder_tool.list_upcoming,
            parameters={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="delete_reminder",
            description="Delete a reminder by its reminder ID.",
            handler=reminder_tool.delete_reminder,
            parameters={
                "type": "object",
                "properties": {"reminder_id": {"type": "integer", "description": "ID of the reminder to delete."}},
                "required": ["reminder_id"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="save_note",
            description="Save a note with a title and body.",
            handler=notes_tool.save_note,
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note."},
                    "body": {"type": "string", "description": "Content of the note."},
                },
                "required": ["title", "body"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="search_notes",
            description="Search notes by keyword or phrase.",
            handler=notes_tool.search_notes,
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Text to look up in notes."}},
                "required": ["query"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="update_note",
            description="Update an existing note.",
            handler=notes_tool.update_note,
            parameters={
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "ID of the note to update."},
                    "title": {"type": "string", "description": "Title of the note to update."},
                    "body": {"type": "string", "description": "Updated content."},
                },
                "required": ["note_id", "title", "body"],
            },
        )
    )

    return registry
