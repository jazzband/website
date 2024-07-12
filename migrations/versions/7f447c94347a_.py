"""

Revision ID: 7f447c94347a
Revises: a78f4b5d7dee
Create Date: 2017-11-17 14:59:36.177805
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7f447c94347a"
down_revision = "a78f4b5d7dee"


def upgrade():
    op.add_column(
        "projects", sa.Column("uploads_count", sa.SmallInteger(), nullable=True)
    )


def downgrade():
    op.drop_column("projects", "uploads_count")
