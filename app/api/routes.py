from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.core.assistant import AetherAssistant

router = APIRouter()
assistant = AetherAssistant(provider_name=settings.active_provider)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    provider: str = "gemini"


class ProviderConfigRequest(BaseModel):
    api_key: str | None = None
    model: str | None = None
    enabled: bool | None = None
    host: str | None = None


class ProviderSwitchRequest(BaseModel):
    provider: str


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "aether"}


@router.get("/providers")
async def list_providers() -> list[dict[str, object]]:
    return assistant.provider_manager.list_config()


@router.get("/providers/status")
async def provider_status() -> dict[str, list[dict[str, object]]]:
    return {"providers": [status.__dict__ for status in assistant.provider_manager.health_report()]}


@router.post("/providers/{provider_name}/validate")
async def validate_provider(provider_name: str) -> dict[str, object]:
    result = assistant.provider_manager.validate_provider(provider_name)
    assistant.provider_name = provider_name if result["healthy"] else assistant.provider_name
    return result


@router.post("/providers/active")
async def set_active_provider(request: ProviderSwitchRequest) -> dict[str, object]:
    provider_name = assistant.provider_manager.select_provider(request.provider)
    assistant.provider_name = provider_name
    return {"active_provider": provider_name, "configured": assistant.provider_manager.list_config()}


@router.post("/providers/{provider_name}/configure")
async def configure_provider(provider_name: str, request: ProviderConfigRequest) -> dict[str, object]:
    updated = assistant.provider_manager.configure_provider(
        provider_name,
        api_key=request.api_key,
        model=request.model,
        enabled=request.enabled,
        host=request.host,
    )
    if request.enabled is not None and request.enabled:
        assistant.provider_name = provider_name
    return updated


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    reply = await assistant.generate_response(request.message)
    return ChatResponse(reply=reply, provider=assistant.provider_name)
