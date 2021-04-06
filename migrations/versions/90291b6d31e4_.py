"""

Revision ID: 90291b6d31e4
Revises: a74099e498a6
Create Date: 2021-03-26 13:47:53.109876
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "90291b6d31e4"
down_revision = "a74099e498a6"


def upgrade():
    op.add_column(
        "project_memberships", sa.Column("left_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("team_slug", sa.String(length=255), nullable=True)
    )


def downgrade():
    op.drop_column("projects", "team_slug")
    op.drop_column("project_memberships", "left_at")
