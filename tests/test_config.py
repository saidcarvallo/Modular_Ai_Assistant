import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.request import Request

from app.config import Settings, settings
from app.main import create_app
from app.model_manager.fallback import classify_provider_error, fallback_order, should_retry
from app.tools.documents import DocumentTool
from app.providers.ollama import OllamaProvider
from app.providers.base import ProviderConfig
from app.tools.registry import build_tool_registry
from app.tools.tasks import TaskTool


def test_default_settings_exist() -> None:
    assert settings.app_name == "Aether AI Personal Assistant"
    assert settings.app_env in {"development", "production", "test"}
    assert settings.gemini_model
    assert settings.ollama_model


def test_settings_ignore_gemini_key_placeholder() -> None:
    configured = Settings(GEMINI_API_KEY="your_key_here", _env_file=None)
    assert configured.gemini_api_key == ""


def test_assistant_handles_missing_provider(assistant) -> None:
    for provider in assistant.provider_manager.providers.values():
        provider.config.enabled = False
    response = asyncio.run(assistant.generate_response("Hola"))
    assert "No enabled provider" in response


def test_tool_registry_and_task_tool_work(memory_manager) -> None:
    registry = build_tool_registry(memory=memory_manager)
    assert registry.get("create_task") is not None
    assert registry.get("list_tasks") is not None
    assert registry.get("read_document") is None

    task_tool = TaskTool(memory=memory_manager)
    result = task_tool.create_task("Revisar roadmap")
    assert result["status"] == "created"
    assert result["title"] == "Revisar roadmap"
    assert len(task_tool.list_tasks()) == 1


def test_assistant_executes_tool_call(assistant) -> None:
    result = assistant.execute_tool_call({"name": "create_task", "arguments": {"title": "Planear sprint", "description": "Primera tarea"}})
    assert result["status"] == "created"
    assert result["title"] == "Planear sprint"
    assert len(assistant.memory.list_tasks()) == 1


def test_fallback_logic_classifies_errors() -> None:
    assert classify_provider_error("quota exceeded") == "quota"
    assert classify_provider_error("401 unauthorized") == "authentication"
    assert classify_provider_error("timeout connecting to provider") == "connectivity"
    assert fallback_order(["gemini", "ollama"]) == ["gemini", "ollama"]
    assert should_retry("quota exceeded", 0) is True
    assert should_retry("401 unauthorized", 0) is False


def test_memory_manager_tracks_basic_entities(assistant) -> None:
    assistant.memory.save_conversation("user", "Prueba de historial")
    assistant.memory.add_task("Tarea persistente")
    assistant.memory.add_note("Nota persistente", "Contenido de prueba")
    assert assistant.memory.list_conversation_history()[-1].content == "Prueba de historial"
    assert assistant.get_memory_summary()["tasks"] >= 1


def test_memory_manager_updates_and_deletes_notes(assistant) -> None:
    note = assistant.memory.add_note("Borrador", "Contenido inicial")

    updated = assistant.memory.update_note(note.id, "Nota final", "Contenido editado")
    assert updated is not None
    assert updated.title == "Nota final"
    assert updated.body == "Contenido editado"
    assert assistant.memory.delete_note(note.id) is True
    assert assistant.memory.delete_note(note.id) is False
    assert assistant.memory.update_note(note.id, "Otra", "Otra") is None


def test_upcoming_reminders_excludes_past_dates(assistant) -> None:
    past = assistant.memory.add_reminder(
        "Pasado",
        datetime.now(timezone.utc) - timedelta(days=1),
    )
    future = assistant.memory.add_reminder(
        "Futuro",
        datetime.now(timezone.utc) + timedelta(days=1),
    )

    reminders = assistant.memory.list_upcoming_reminders()

    assert [reminder.id for reminder in reminders] == [future.id]
    assert past.id not in [reminder.id for reminder in reminders]


def test_registered_note_update_changes_the_saved_note(assistant) -> None:
    note = assistant.memory.add_note("Borrador", "Contenido viejo")
    result = assistant.execute_tool_call(
        {
            "name": "update_note",
            "arguments": {
                "note_id": note.id,
                "title": "Final",
                "body": "Contenido nuevo",
            },
        }
    )
    assert result == {"status": "updated", "note_id": note.id, "title": "Final"}
    assert assistant.memory.session.get(type(note), note.id).body == "Contenido nuevo"


def test_registered_note_update_reports_missing_note(assistant) -> None:
    result = assistant.execute_tool_call(
        {
            "name": "update_note",
            "arguments": {"note_id": 404, "title": "Missing", "body": "No note"},
        }
    )
    assert result == {"status": "not_found", "note_id": 404}


def test_provider_manager_configuration(assistant) -> None:
    config = assistant.provider_manager.configure_provider(
        "gemini",
        api_key="abc123",
        model="gemini-3.5-flash-lite",
        enabled=True,
    )
    assert config["provider"] == "gemini"
    assert config["api_key_configured"] is True
    assert assistant.provider_manager.list_config()[0]["provider"] == "gemini"


def test_provider_health_report_tracks_status_details(assistant) -> None:
    assistant.provider_manager.record_result("gemini", success=True)
    assistant.provider_manager.record_result("gemini", success=False, error="quota exceeded")

    status = assistant.provider_manager.health_report()
    gemini_status = next(item for item in status if item.provider == "gemini")
    assert gemini_status.available is False
    assert gemini_status.last_error == "quota exceeded"
    assert gemini_status.requests >= 2


def test_document_tool_reads_and_summarizes_files(tmp_path) -> None:
    target = tmp_path / "plan.txt"
    target.write_text("Aether is a personal assistant for managing tasks, notes, and reminders. It helps users stay organized.", encoding="utf-8")

    tool = DocumentTool()
    read_result = tool.read_document(str(target))
    summary_result = tool.summarize_document(str(target))

    assert read_result["status"] == "ok"
    assert read_result["chars"] > 0
    assert summary_result["status"] == "summarized"
    assert "Aether" in str(summary_result["summary"]) or "assistant" in str(summary_result["summary"]).lower()


def test_document_tool_extracts_pdf_text(tmp_path, monkeypatch) -> None:
    target = tmp_path / "report.pdf"
    target.write_bytes(b"test pdf")

    class FakePage:
        def extract_text(self):
            return "Text extracted from a PDF."

    class FakeReader:
        def __init__(self, path):
            self.pages = [FakePage()]

    monkeypatch.setattr("app.tools.documents.PdfReader", FakeReader)
    result = DocumentTool().read_document(str(target))
    assert result["status"] == "ok"
    assert result["words"] == 5


def test_assistant_includes_recent_turns_in_next_prompt(assistant) -> None:
    class FakeProvider:
        def __init__(self):
            self.config = SimpleNamespace(enabled=True)
            self.prompts = []

        async def generate(self, prompt, *, system_prompt=None, tools=None):
            self.prompts.append(prompt)
            return "Respuesta de prueba"

    provider = FakeProvider()
    assistant.provider_manager.providers = {"fake": provider}
    assistant.provider_name = "fake"

    asyncio.run(assistant.generate_response("Me llamo Ana"))
    asyncio.run(assistant.generate_response("¿Cómo me llamo?"))

    assert "User: Me llamo Ana" in provider.prompts[1]
    assert "Assistant: Respuesta de prueba" in provider.prompts[1]


def test_main_app_factory_exposes_fastapi_app() -> None:
    app = create_app()
    assert app.title == settings.app_name
    assert app is not None


def test_ollama_provider_sends_chat_request(monkeypatch) -> None:
    captured_request = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"message":{"content":"Hola desde Ollama"}}'

    def fake_urlopen(request, timeout):
        captured_request["request"] = request
        captured_request["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.providers.ollama.request.urlopen", fake_urlopen)
    provider = OllamaProvider(
        ProviderConfig(name="ollama", model="qwen3:8b", host="http://localhost:11434")
    )
    response = asyncio.run(provider.generate("Hola", system_prompt="Responde en español"))

    payload = json.loads(captured_request["request"].data)
    assert isinstance(captured_request["request"], Request)
    assert captured_request["request"].full_url == "http://localhost:11434/api/chat"
    assert payload["model"] == "qwen3:8b"
    assert payload["messages"][0] == {"role": "system", "content": "Responde en español"}
    assert response == "Hola desde Ollama"


def test_assistant_falls_back_to_second_provider(assistant) -> None:
    class FakeProvider:
        def __init__(self, name, response=None, error=None):
            self.config = SimpleNamespace(enabled=True)
            self.response = response
            self.error = error

        def health_check(self):
            raise AssertionError("Chat should not require a separate health check")

        async def generate(self, prompt, *, system_prompt=None, tools=None):
            if self.error:
                raise self.error
            return self.response

    assistant.provider_name = "gemini"
    assistant.provider_manager.providers["gemini"] = FakeProvider("gemini", error=RuntimeError("API key missing"))
    assistant.provider_manager.providers["ollama"] = FakeProvider("ollama", response="Respuesta local")

    response = asyncio.run(assistant.generate_response("Hola"))

    assert response == "Respuesta local"
    assert assistant.provider_name == "ollama"
