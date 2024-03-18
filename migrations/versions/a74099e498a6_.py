"""

Revision ID: a74099e498a6
Revises: b09168ebba73
Create Date: 2019-04-16 13:34:33.857569
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a74099e498a6"
down_revision = "b09168ebba73"


def upgrade():
    op.drop_column("users", "access_token")


def downgrade():
    op.add_column(
        "users",
        sa.Column(
            "access_token", sa.VARCHAR(length=200), autoincrement=False, nullable=True
        ),
    )
