from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

from app.memory.manager import MemoryManager


class ReminderInput(BaseModel):
    message: str = Field(..., min_length=1)
    scheduled_for: str | None = None


@dataclass
class ReminderTool:
    memory: MemoryManager | None = None

    def create_reminder(self, message: str, scheduled_for: str | None = None) -> dict[str, str | int | None]:
        payload = ReminderInput(message=message, scheduled_for=scheduled_for)
        scheduled_value = None

        if payload.scheduled_for:
            try:
                scheduled_value = datetime.fromisoformat(payload.scheduled_for)
            except ValueError as exc:
                raise ValueError("scheduled_for must be a valid ISO-8601 datetime") from exc

        if self.memory is None:
            raise RuntimeError("Reminder tool requires a memory manager")
        reminder = self.memory.add_reminder(payload.message, scheduled_value)
        return {
            "status": "created",
            "reminder_id": reminder.id,
            "message": reminder.message,
            "scheduled_for": str(reminder.scheduled_for) if reminder.scheduled_for else None,
        }

    def list_upcoming(self) -> list[dict[str, str | int | None]]:
        if self.memory is None:
            raise RuntimeError("Reminder tool requires a memory manager")
        upcoming = self.memory.list_upcoming_reminders()
        return [
            {
                "reminder_id": reminder.id,
                "message": reminder.message,
                "scheduled_for": str(reminder.scheduled_for) if reminder.scheduled_for else None,
            }
            for reminder in upcoming
        ]

    def delete_reminder(self, reminder_id: str | int) -> dict[str, str | int]:
        reminder_value = int(reminder_id)
        if self.memory is None:
            raise RuntimeError("Reminder tool requires a memory manager")
        if not self.memory.delete_reminder(reminder_value):
            return {"status": "not_found", "reminder_id": reminder_value}
        return {"status": "deleted", "reminder_id": reminder_value}
