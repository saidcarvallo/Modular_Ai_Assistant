from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.memory.database import SessionLocal
from app.memory.models import Conversation, Note, Reminder, Task


class MemoryManager:
    """Persistent storage for conversations, tasks, notes, and reminders."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()

    def save_conversation(self, role: str, content: str) -> Conversation:
        entry = Conversation(role=role, content=content)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list_conversation_history(self, limit: int | None = None) -> list[Conversation]:
        query = self.session.query(Conversation).order_by(Conversation.created_at.asc())
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def list_tasks(self) -> list[Task]:
        return self.session.query(Task).order_by(Task.created_at.asc()).all()

    def add_task(self, title: str, description: str | None = None) -> Task:
        task = Task(title=title, description=description)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def complete_task(self, task_id: int) -> Task | None:
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if task is None:
            return None
        task.completed = True
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if task is None:
            return False
        self.session.delete(task)
        self.session.commit()
        return True

    def add_note(self, title: str, body: str) -> Note:
        note = Note(title=title, body=body)
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    def update_note(self, note_id: int, title: str, body: str) -> Note | None:
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note is None:
            return None
        note.title = title
        note.body = body
        self.session.commit()
        self.session.refresh(note)
        return note

    def delete_note(self, note_id: int) -> bool:
        note = self.session.query(Note).filter(Note.id == note_id).first()
        if note is None:
            return False
        self.session.delete(note)
        self.session.commit()
        return True

    def search_notes(self, query: str) -> list[Note]:
        return (
            self.session.query(Note)
            .filter((Note.title.ilike(f"%{query}%")) | (Note.body.ilike(f"%{query}%")))
            .all()
        )

    def add_reminder(self, message: str, scheduled_for=None) -> Reminder:
        reminder = Reminder(message=message, scheduled_for=scheduled_for)
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder

    def list_upcoming_reminders(self) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        return (
            self.session.query(Reminder)
            .filter(Reminder.scheduled_for.isnot(None), Reminder.scheduled_for >= now)
            .order_by(Reminder.scheduled_for.asc())
            .all()
        )

    def delete_reminder(self, reminder_id: int) -> bool:
        reminder = self.session.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder is None:
            return False
        self.session.delete(reminder)
        self.session.commit()
        return True

    def build_context(self, limit: int = 10) -> list[dict[str, str]]:
        entries = self.list_conversation_history(limit=limit)
        return [{"role": entry.role, "content": entry.content} for entry in entries]

    def get_user_memory_summary(self) -> dict[str, object]:
        return {
            "tasks": len(self.list_tasks()),
            "notes": self.session.query(Note).count(),
            "reminders": self.session.query(Reminder).count(),
            "conversations": self.session.query(Conversation).count(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
