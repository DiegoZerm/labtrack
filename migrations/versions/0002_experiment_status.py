"""Agrega status a experiments; los registros existentes quedan en completed."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "experiments",
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
    )


def downgrade():
    # SQLite no puede borrar columnas directamente: batch recrea la tabla.
    with op.batch_alter_table("experiments") as batch:
        batch.drop_column("status")
