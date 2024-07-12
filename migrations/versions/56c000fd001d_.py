"""

Revision ID: 56c000fd001d
Revises: bcc2ac4b6ecc
Create Date: 2017-10-30 20:19:07.278647
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "56c000fd001d"
down_revision = "bcc2ac4b6ecc"


def upgrade():
    op.create_table(
        "project_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("username", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("password", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_credentials_is_active"),
        "project_credentials",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "release_username_password_is_active_idx",
        "project_credentials",
        ["username", "password", "is_active"],
        unique=False,
    )

    op.drop_column("projects", "secret_key")
    op.drop_column("projects", "client_id")


def downgrade():
    op.add_column(
        "projects",
        sa.Column("client_id", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("secret_key", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.drop_index(
        "release_username_password_is_active_idx", table_name="project_credentials"
    )
    op.drop_index(
        op.f("ix_project_credentials_is_active"), table_name="project_credentials"
    )
    op.drop_table("project_credentials")
