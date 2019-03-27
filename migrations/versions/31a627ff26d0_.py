"""

Revision ID: 31a627ff26d0
Revises: d3b2cffb2b9c
Create Date: 2018-05-18 16:05:12.490642
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "31a627ff26d0"
down_revision = "d3b2cffb2b9c"


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_restricted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_users_is_restricted"), "users", ["is_restricted"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_users_is_restricted"), table_name="users")
    op.drop_column("users", "is_restricted")
