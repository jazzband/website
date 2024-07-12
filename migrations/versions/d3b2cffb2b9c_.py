"""

Revision ID: d3b2cffb2b9c
Revises: 0bc7f15b1164
Create Date: 2017-11-20 14:25:57.182902
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d3b2cffb2b9c"
down_revision = "0bc7f15b1164"


def upgrade():
    op.drop_index(
        "release_username_password_is_active_idx", table_name="project_credentials"
    )
    op.alter_column("project_credentials", "password", new_column_name="key")
    op.create_index(
        "release_key_is_active_idx",
        "project_credentials",
        ["key", "is_active"],
        unique=False,
    )
    op.drop_column("project_credentials", "username")


def downgrade():
    op.drop_index("release_key_is_active_idx", table_name="project_credentials")
    op.alter_column("project_credentials", "key", new_column_name="password")
    op.add_column(
        "project_credentials",
        sa.Column("username", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "release_username_password_is_active_idx",
        "project_credentials",
        ["username", "password", "is_active"],
        unique=False,
    )
