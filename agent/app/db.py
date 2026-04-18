from pathlib import Path

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DATA_DIR / 'app.db'}", connect_args={"check_same_thread": False})


def ensure_legacy_project_columns(target_engine) -> None:
    expected_columns = {
        "preferred_style": "TEXT NOT NULL DEFAULT 'default'",
        "brief": "TEXT NOT NULL DEFAULT ''",
        "prompt_draft": "TEXT NOT NULL DEFAULT ''",
        "source_manifest_json": "TEXT NOT NULL DEFAULT '{}'",
        "insight_summary": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }

    with target_engine.begin() as connection:
        existing_tables = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        if "project" not in existing_tables:
            return

        current_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(project)"))
        }
        for column_name, column_definition in expected_columns.items():
            if column_name not in current_columns:
                connection.execute(text(f"ALTER TABLE project ADD COLUMN {column_name} {column_definition}"))


def init_db() -> None:
    ensure_legacy_project_columns(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
