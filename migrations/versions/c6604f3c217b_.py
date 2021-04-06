"""

Revision ID: c6604f3c217b
Revises: 5eff8a811c74
Create Date: 2021-03-26 20:34:56.095188
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c6604f3c217b"
down_revision = "5eff8a811c74"


def upgrade():
    op.add_column(
        "projects", sa.Column("membership_count", sa.SmallInteger(), nullable=True)
    )


def downgrade():
    op.drop_column("projects", "membership_count")
