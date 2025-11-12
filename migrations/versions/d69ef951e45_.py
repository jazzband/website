"""Add leads_team_slug to projects

Revision ID: d69ef951e45
Revises: c6604f3c217b
Create Date: 2025-11-12 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d69ef951e45"
down_revision = "c6604f3c217b"


def upgrade():
    op.add_column(
        "projects",
        sa.Column("leads_team_slug", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("projects", "leads_team_slug")

