"""

Revision ID: e40889bed1ba
Revises: b72321d58252
Create Date: 2019-02-10 21:55:49.665314
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e40889bed1ba"
down_revision = "b72321d58252"


def upgrade():
    op.add_column(
        "projects",
        sa.Column("transfer_issue_url", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("projects", "transfer_issue_url")
