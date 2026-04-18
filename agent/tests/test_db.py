from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

from app.db import ensure_legacy_project_columns
from app.models import Project


def test_ensure_legacy_project_columns_adds_missing_fields(tmp_path):
    db_file = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE project (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    preferred_language TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )

    ensure_legacy_project_columns(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        project = Project(title="Migrated", preferred_language="zh-CN")
        session.add(project)
        session.commit()
        session.refresh(project)

        assert project.id is not None
        assert project.brief == ""
