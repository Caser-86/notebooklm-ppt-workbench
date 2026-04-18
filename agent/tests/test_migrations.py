from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

import app.db as db_module


def test_alembic_files_exist():
    assert Path("alembic.ini").exists()
    assert Path("alembic/env.py").exists()
    assert Path("alembic/script.py.mako").exists()


def run_alembic_upgrade(db_file: Path, revision: str = "head") -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")
    command.upgrade(config, revision)


def test_clean_sqlite_database_upgrades_to_head(tmp_path):
    db_file = tmp_path / "clean.db"

    run_alembic_upgrade(db_file)

    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    inspector = inspect(engine)

    assert "project" in inspector.get_table_names()
    project_columns = {column["name"] for column in inspector.get_columns("project")}
    assert {"brief", "prompt_draft", "source_manifest_json", "updated_at"}.issubset(project_columns)
    job_columns = {column["name"] for column in inspector.get_columns("job")}
    assert {"payload_json", "result_json", "attempt_count", "max_attempts", "available_at", "locked_by"}.issubset(job_columns)


def test_legacy_sqlite_upgrades_to_head(tmp_path):
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

    run_alembic_upgrade(db_file)

    inspector = inspect(engine)
    project_columns = {column["name"] for column in inspector.get_columns("project")}

    assert {"brief", "prompt_draft", "source_manifest_json", "updated_at"}.issubset(project_columns)
    job_columns = {column["name"] for column in inspector.get_columns("job")}
    assert {"payload_json", "result_json", "attempt_count", "max_attempts", "available_at", "locked_by"}.issubset(job_columns)


def test_startup_upgrade_helper_upgrades_database_before_use(tmp_path):
    db_file = tmp_path / "startup.db"
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

    db_module.upgrade_db_to_head(f"sqlite:///{db_file}")

    inspector = inspect(engine)
    project_columns = {column["name"] for column in inspector.get_columns("project")}

    assert {"brief", "prompt_draft", "source_manifest_json", "updated_at"}.issubset(project_columns)
