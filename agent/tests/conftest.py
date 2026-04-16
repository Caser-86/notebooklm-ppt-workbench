from pathlib import Path

import pytest
from sqlmodel import SQLModel, Session, create_engine

import app.db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    original_engine = db_module.engine
    original_get_session = db_module.get_session

    db_module.engine = engine

    def get_session_override():
        with Session(engine) as session:
            yield session

    db_module.get_session = get_session_override
    app.dependency_overrides[original_get_session] = get_session_override

    try:
        yield
    finally:
        app.dependency_overrides.clear()
        db_module.engine = original_engine
        db_module.get_session = original_get_session
