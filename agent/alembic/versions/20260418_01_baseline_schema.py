"""baseline schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260418_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS project (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                preferred_language TEXT NOT NULL,
                preferred_style TEXT NOT NULL DEFAULT 'default',
                brief TEXT NOT NULL DEFAULT '',
                prompt_draft TEXT NOT NULL DEFAULT '',
                source_manifest_json TEXT NOT NULL DEFAULT '{}',
                insight_summary TEXT NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS job (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, job_type TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'auto', status TEXT NOT NULL DEFAULT 'draft', attention_reason TEXT NOT NULL DEFAULT '', notebook_session_path TEXT NOT NULL DEFAULT '', retry_count INTEGER NOT NULL DEFAULT 0, created_at DATETIME NOT NULL)"))
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS rebuildversion (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, version_number INTEGER NOT NULL, slide_count INTEGER NOT NULL DEFAULT 0, display_clone_path TEXT NOT NULL, editable_rebuild_path TEXT NOT NULL, created_at DATETIME NOT NULL)"))
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS sourcerevision (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, revision_number INTEGER NOT NULL, source_manifest_json TEXT NOT NULL, insight_summary TEXT NOT NULL DEFAULT '', created_at DATETIME NOT NULL)"))
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS importedpresentation (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, source_type TEXT NOT NULL DEFAULT 'generic_pptx', filename TEXT NOT NULL, original_file_path TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'uploaded', page_count INTEGER NOT NULL DEFAULT 0, error_message TEXT NOT NULL DEFAULT '', created_at DATETIME NOT NULL)"))
    op.execute(sa.text("CREATE TABLE IF NOT EXISTS importedslideasset (id INTEGER PRIMARY KEY, import_id INTEGER NOT NULL, slide_index INTEGER NOT NULL, preview_image_path TEXT NOT NULL, text_dump TEXT NOT NULL DEFAULT '', structure_json_path TEXT NOT NULL DEFAULT '')"))

    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_job_project_id ON job (project_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_rebuildversion_project_id ON rebuildversion (project_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_sourcerevision_project_id ON sourcerevision (project_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_importedpresentation_project_id ON importedpresentation (project_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_importedslideasset_import_id ON importedslideasset (import_id)"))


def downgrade() -> None:
    pass
