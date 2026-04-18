"""upgrade legacy project columns"""

from alembic import op
import sqlalchemy as sa


revision = "20260418_02"
down_revision = "20260418_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_tables = {row[0] for row in bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))}
    if "project" not in existing_tables:
        return

    current_columns = {row[1] for row in bind.execute(sa.text("PRAGMA table_info(project)"))}
    expected_columns = {
        "preferred_style": "TEXT NOT NULL DEFAULT 'default'",
        "brief": "TEXT NOT NULL DEFAULT ''",
        "prompt_draft": "TEXT NOT NULL DEFAULT ''",
        "source_manifest_json": "TEXT NOT NULL DEFAULT '{}'",
        "insight_summary": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }

    for column_name, column_definition in expected_columns.items():
        if column_name not in current_columns:
            bind.execute(sa.text(f"ALTER TABLE project ADD COLUMN {column_name} {column_definition}"))


def downgrade() -> None:
    pass
