"""

Revision ID: a78f4b5d7dee
Revises: 73d96d3120ff
Create Date: 2017-11-16 23:18:23.416997
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a78f4b5d7dee"
down_revision = "73d96d3120ff"


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "has_2fa", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.create_index(op.f("ix_users_has_2fa"), "users", ["has_2fa"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_users_has_2fa"), table_name="users")
    op.drop_column("users", "has_2fa")
