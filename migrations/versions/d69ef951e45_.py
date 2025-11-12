"""Add leads_team_slug to projects

Revision ID: d69ef951e45
Revises: e40889bed1ba
Create Date: 2025-11-12 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d69ef951e45"
down_revision = "e40889bed1ba"


def upgrade():
    op.add_column(
        "projects",
        sa.Column("leads_team_slug", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("projects", "leads_team_slug")

