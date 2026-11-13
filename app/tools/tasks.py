from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.memory.manager import MemoryManager
from app.memory.models import Task


class CreateTaskInput(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None


class UpdateTaskInput(BaseModel):
    task_id: int


@dataclass
class TaskTool:
    """Controlled task operations exposed to the assistant via the registry."""

    memory: MemoryManager | None = None

    def create_task(self, title: str, description: str | None = None) -> dict[str, str | int | None]:
        payload = CreateTaskInput(title=title, description=description)
        if self.memory is None:
            raise RuntimeError("Task tool requires a memory manager")
        task = self.memory.add_task(payload.title, payload.description)
        return {"status": "created", "task_id": task.id, "title": task.title, "description": task.description}

    def list_tasks(self) -> list[dict[str, str | int | bool | None]]:
        if self.memory is None:
            raise RuntimeError("Task tool requires a memory manager")
        return [
            {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
            }
            for task in self.memory.list_tasks()
        ]

    def complete_task(self, task_id: int) -> dict[str, str | int]:
        payload = UpdateTaskInput(task_id=task_id)

        if self.memory is None:
            raise RuntimeError("Task tool requires a memory manager")
        task = self.memory.session.query(Task).filter(Task.id == payload.task_id).first()
        if task is None:
            return {"status": "not_found", "task_id": payload.task_id}
        task.completed = True
        self.memory.session.commit()
        return {"status": "completed", "task_id": task.id}

    def delete_task(self, task_id: int) -> dict[str, str | int]:
        payload = UpdateTaskInput(task_id=task_id)

        if self.memory is None:
            raise RuntimeError("Task tool requires a memory manager")
        if not self.memory.delete_task(payload.task_id):
            return {"status": "not_found", "task_id": payload.task_id}
        return {"status": "deleted", "task_id": payload.task_id}
