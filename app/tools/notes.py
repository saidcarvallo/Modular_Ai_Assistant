from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.memory.manager import MemoryManager


class NoteInput(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


@dataclass
class NotesTool:
    memory: MemoryManager | None = None

    def save_note(self, title: str, body: str) -> dict[str, str | int]:
        payload = NoteInput(title=title, body=body)
        if self.memory is None:
            raise RuntimeError("Notes tool requires a memory manager")
        note = self.memory.add_note(payload.title, payload.body)
        return {"status": "saved", "title": note.title, "note_id": note.id}

    def search_notes(self, query: str) -> list[dict[str, str | int]]:
        if self.memory is None:
            raise RuntimeError("Notes tool requires a memory manager")
        matches = self.memory.search_notes(query)
        return [{"note_id": note.id, "title": note.title, "body": note.body} for note in matches]

    def update_note(self, note_id: int, title: str, body: str) -> dict[str, str | int]:
        payload = NoteInput(title=title, body=body)
        if self.memory is None:
            raise RuntimeError("Notes tool requires a memory manager")
        note = self.memory.update_note(note_id, payload.title, payload.body)
        if note is None:
            return {"status": "not_found", "note_id": note_id}
        return {"status": "updated", "note_id": note.id, "title": note.title}
