from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import subprocess
import sys
import threading

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.memory.database import init_db


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db()
        yield

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.include_router(router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"app": settings.app_name, "status": "initialized"}

    return app


app = create_app()


def run_api(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def run_ui(host: str = "127.0.0.1", port: int = 8501) -> None:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/ui/streamlit_app.py",
        "--server.address",
        host,
        "--server.port",
        str(port),
    ]
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Aether AI Personal Assistant locally")
    parser.add_argument("--mode", choices=["api", "ui", "both"], default="api", help="Select which service to start")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the FastAPI server")
    parser.add_argument("--ui-host", default="127.0.0.1", help="Host for the Streamlit interface")
    parser.add_argument("--ui-port", type=int, default=8501, help="Port for the Streamlit interface")
    args = parser.parse_args(argv)

    if args.mode == "api":
        run_api(args.host, args.port)
        return

    if args.mode == "ui":
        run_ui(args.ui_host, args.ui_port)
        return

    api_thread = threading.Thread(target=run_api, args=(args.host, args.port), daemon=True)
    api_thread.start()
    run_ui(args.ui_host, args.ui_port)


if __name__ == "__main__":
    main()
