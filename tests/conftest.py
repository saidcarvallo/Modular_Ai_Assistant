import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def memory_manager(tmp_path):
    from app.memory.manager import MemoryManager
    from app.memory import models

    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    models.Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    manager = MemoryManager(session=session)
    try:
        yield manager
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def assistant(memory_manager):
    from app.core.assistant import AetherAssistant

    return AetherAssistant(memory=memory_manager)
