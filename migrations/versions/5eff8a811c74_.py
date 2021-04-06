"""

Revision ID: 5eff8a811c74
Revises: 90291b6d31e4
Create Date: 2021-03-26 19:37:03.459550
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5eff8a811c74"
down_revision = "90291b6d31e4"


def upgrade():
    op.add_column(
        "project_memberships", sa.Column("synced_at", sa.DateTime(), nullable=False)
    )


def downgrade():
    op.drop_column("project_memberships", "synced_at")
