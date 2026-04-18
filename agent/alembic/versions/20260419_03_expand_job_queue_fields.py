"""expand job queue fields"""

from alembic import op
import sqlalchemy as sa


revision = "20260419_03"
down_revision = "20260418_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.add_column(sa.Column("payload_json", sa.String(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("result_json", sa.String(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("error_message", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
        batch_op.add_column(sa.Column("available_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("finished_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("locked_by", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("locked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    pass
