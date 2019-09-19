"""

Revision ID: 9cbd7c1a6757
Revises: 31a627ff26d0
Create Date: 2018-05-18 19:31:27.158543
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9cbd7c1a6757"
down_revision = "31a627ff26d0"


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "age_consent", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column("users", sa.Column("consented_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "cookies_consent",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column("users", sa.Column("joined_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("left_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "org_consent", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "profile_consent",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("users", "profile_consent")
    op.drop_column("users", "org_consent")
    op.drop_column("users", "left_at")
    op.drop_column("users", "joined_at")
    op.drop_column("users", "cookies_consent")
    op.drop_column("users", "consented_at")
    op.drop_column("users", "age_consent")
