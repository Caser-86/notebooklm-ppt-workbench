# SQLite-First Alembic Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a formal SQLite-first Alembic migration workflow so new local databases initialize cleanly, legacy local databases upgrade safely, and future schema changes stop depending on ad-hoc startup patches.

**Architecture:** Add a standard Alembic environment under `agent/`, create a baseline revision for the current schema plus a targeted legacy-upgrade path for known old SQLite states, and change `agent/app/db.py` so startup upgrades the local database to `head`. Keep the existing `ensure_legacy_project_columns()` helper only as a short-lived transition fallback until Alembic-based upgrades are proven by tests.

**Tech Stack:** FastAPI, SQLModel, SQLAlchemy, Alembic, SQLite, pytest

---

## File Structure

### Migration infrastructure

- Create: `agent/alembic.ini`
  - Alembic configuration for the agent workspace
- Create: `agent/alembic/env.py`
  - engine wiring and metadata registration
- Create: `agent/alembic/script.py.mako`
  - standard revision template
- Create: `agent/alembic/versions/`
  - migration revision files

### Backend integration

- Modify: `agent/pyproject.toml`
  - add Alembic dependency
- Modify: `agent/app/db.py`
  - replace startup-time schema patching as the primary path with Alembic upgrade-to-head
- Optionally modify: `agent/app/main.py`
  - only if startup upgrade placement needs to move out of `db.py`

### Tests

- Modify: `agent/tests/test_db.py`
  - expand legacy-upgrade coverage
- Create: `agent/tests/test_migrations.py`
  - clean-init and upgrade-to-head coverage
- Optionally modify: `agent/tests/conftest.py`
  - test helpers for temporary Alembic database paths
- Reuse: `agent/tests/test_projects_api.py`
- Reuse: `agent/tests/test_pptx_import_api.py`

### Docs

- Modify: `docs/DELIVERY.md`
  - document Alembic-backed migration flow
- Modify: `docs/ACCEPTANCE.md`
  - add migration-specific acceptance checks

## Task 1: Add Alembic To The Agent Project

**Files:**
- Modify: `agent/pyproject.toml`
- Create: `agent/alembic.ini`
- Create: `agent/alembic/env.py`
- Create: `agent/alembic/script.py.mako`

- [ ] **Step 1: Write the failing import/config test**

Add a test that proves Alembic can be imported and the migration environment files exist.

```python
def test_alembic_files_exist():
    assert Path("alembic.ini").exists()
    assert Path("alembic/env.py").exists()
    assert Path("alembic/script.py.mako").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_migrations.py::test_alembic_files_exist -v`
Expected: FAIL because the Alembic files do not exist yet.

- [ ] **Step 3: Add the Alembic dependency**

Update `agent/pyproject.toml`.

```toml
dependencies = [
  ...
  "alembic>=1.14,<1.15",
]
```

- [ ] **Step 4: Add `alembic.ini`**

Create `agent/alembic.ini`.

```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///data/app.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers = console
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

- [ ] **Step 5: Add `env.py`**

Create `agent/alembic/env.py`.

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models import SQLModel

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 6: Add `script.py.mako`**

Create `agent/alembic/script.py.mako` using the standard Alembic revision template.

```python
"""${message}"""

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 7: Run the migration environment test**

Run: `python -m pytest tests/test_migrations.py::test_alembic_files_exist -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml alembic.ini alembic/env.py alembic/script.py.mako tests/test_migrations.py
git commit -m "feat: add alembic migration scaffold"
```

## Task 2: Add Baseline And Legacy SQLite Revisions

**Files:**
- Create: `agent/alembic/versions/<timestamp>_baseline_schema.py`
- Create: `agent/alembic/versions/<timestamp>_upgrade_legacy_project_columns.py`
- Modify: `agent/tests/test_db.py`
- Modify: `agent/tests/test_migrations.py`

- [ ] **Step 1: Write the failing legacy-upgrade test**

Add a test that starts from a reduced legacy schema and expects Alembic upgrade to reach the current model.

```python
def test_legacy_sqlite_upgrades_to_head(tmp_path):
    db_file = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE project (id INTEGER PRIMARY KEY, title TEXT NOT NULL, preferred_language TEXT NOT NULL, created_at TEXT NOT NULL)"))

    run_alembic_upgrade(db_file, "head")

    columns = inspect(engine).get_columns("project")
    assert any(column["name"] == "brief" for column in columns)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_migrations.py::test_legacy_sqlite_upgrades_to_head -v`
Expected: FAIL because no revisions exist yet.

- [ ] **Step 3: Add the baseline revision**

Create the first revision for the current schema.

```python
def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("preferred_language", sa.String(), nullable=False),
        sa.Column("preferred_style", sa.String(), nullable=False, server_default="default"),
        sa.Column("brief", sa.String(), nullable=False, server_default=""),
        sa.Column("prompt_draft", sa.String(), nullable=False, server_default=""),
        sa.Column("source_manifest_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("insight_summary", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    ...
```

- [ ] **Step 4: Add the legacy-upgrade revision**

Create a second revision that upgrades old `project` tables missing current columns.

```python
def upgrade() -> None:
    with op.batch_alter_table("project") as batch_op:
        batch_op.add_column(sa.Column("preferred_style", sa.String(), nullable=False, server_default="default"))
        batch_op.add_column(sa.Column("brief", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("prompt_draft", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("source_manifest_json", sa.String(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("insight_summary", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("updated_at", sa.String(), nullable=False, server_default=""))
```

- [ ] **Step 5: Add migration test helpers**

Update `tests/test_migrations.py` or `tests/conftest.py` with a helper that runs Alembic against a temporary SQLite path.

```python
def run_alembic_upgrade(db_file: Path, revision: str = "head") -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")
    command.upgrade(config, revision)
```

- [ ] **Step 6: Run migration verification**

Run:

- `python -m pytest tests/test_db.py -v`
- `python -m pytest tests/test_migrations.py -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add alembic/versions tests/test_db.py tests/test_migrations.py
git commit -m "feat: add baseline and legacy sqlite migrations"
```

## Task 3: Upgrade To Head During Startup

**Files:**
- Modify: `agent/app/db.py`
- Modify: `agent/tests/test_migrations.py`

- [ ] **Step 1: Write the failing startup test**

Add a test proving startup upgrades a legacy database before API use.

```python
def test_startup_upgrades_database_before_session_use(tmp_path):
    db_file = tmp_path / "startup.db"
    create_legacy_project_table(db_file)

    init_db_for_path(db_file)

    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    columns = inspect(engine).get_columns("project")
    assert any(column["name"] == "brief" for column in columns)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_migrations.py::test_startup_upgrades_database_before_session_use -v`
Expected: FAIL because startup still relies on direct patching or create_all ordering.

- [ ] **Step 3: Add Alembic upgrade helper in `db.py`**

Update `agent/app/db.py`.

```python
from alembic import command
from alembic.config import Config


def upgrade_db_to_head(target_url: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(config, "head")
```

- [ ] **Step 4: Call upgrade during DB init**

```python
def init_db() -> None:
    upgrade_db_to_head(f"sqlite:///{DATA_DIR / 'app.db'}")
    SQLModel.metadata.create_all(engine)
```

- [ ] **Step 5: Keep the old patch only as a short-term fallback**

Move `ensure_legacy_project_columns()` behind the Alembic path or mark it as transitional support only.

- [ ] **Step 6: Run startup verification**

Run: `python -m pytest tests/test_migrations.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/db.py tests/test_migrations.py
git commit -m "feat: run alembic upgrade on startup"
```

## Task 4: Verify API Compatibility After Migration

**Files:**
- Reuse: `agent/tests/test_projects_api.py`
- Reuse: `agent/tests/test_pptx_import_api.py`
- Reuse: `agent/tests/test_db.py`

- [ ] **Step 1: Add a migration-backed API regression test if needed**

If current coverage does not explicitly exercise upgraded databases, add one test:

```python
def test_upgraded_legacy_database_supports_project_create(tmp_path):
    db_file = tmp_path / "legacy-api.db"
    create_legacy_project_table(db_file)
    run_alembic_upgrade(db_file)
    client = build_client_for_db(db_file)
    response = client.post("/projects", json={"title": "Post-upgrade", "preferred_language": "zh-CN"})
    assert response.status_code == 201
```

- [ ] **Step 2: Run the regression suite**

Run:

- `python -m pytest tests/test_projects_api.py -v`
- `python -m pytest tests/test_pptx_import_api.py -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_projects_api.py tests/test_pptx_import_api.py
git commit -m "test: verify api compatibility after migrations"
```

## Task 5: Update Delivery And Acceptance Guidance

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Update delivery notes**

Add:

```md
Database schema upgrades are now managed through Alembic.
SQLite local databases initialize or upgrade to head during startup.
```

- [ ] **Step 2: Update acceptance checks**

Add:

```md
1. verify a clean local database starts successfully
2. verify a legacy local database upgrades successfully
3. verify project and import APIs still work after upgrade
```

- [ ] **Step 3: Run final verification**

Run:

- `cd agent && python -m pytest -q`

Expected:

- backend suite passes

- [ ] **Step 4: Commit**

```bash
git add docs/DELIVERY.md docs/ACCEPTANCE.md
git commit -m "docs: add sqlite migration guidance"
```

## Self-Review

### Spec coverage

- Alembic setup under `agent/`: covered by Task 1
- baseline and legacy upgrade path: covered by Task 2
- startup upgrade-to-head behavior: covered by Task 3
- regression tests for new and old local databases: covered by Tasks 2-4
- docs and acceptance updates: covered by Task 5

### Placeholder scan

No `TODO`, `TBD`, or vague deferred instructions remain. Each task contains concrete files, commands, and implementation sketches.

### Type consistency

The plan consistently uses:

- `upgrade_db_to_head`
- baseline revision
- legacy-upgrade revision
- `sqlite:///...` URL override

These names are aligned across setup, runtime upgrade, and migration tests.
