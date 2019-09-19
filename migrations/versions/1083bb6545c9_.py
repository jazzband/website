"""

Revision ID: 1083bb6545c9
Revises: 56c000fd001d
Create Date: 2017-10-30 20:20:34.414930
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1083bb6545c9"
down_revision = "56c000fd001d"


def upgrade():
    op.create_table(
        "project_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("date_joined", sa.DateTime(), nullable=True),
        sa.Column("is_lead", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_memberships_is_lead"),
        "project_memberships",
        ["is_lead"],
        unique=False,
    )
    op.drop_table("project_members")


def downgrade():
    op.create_table(
        "project_members",
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("project_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "date_joined", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column("is_lead", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="project_members_project_id_fkey"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="project_members_user_id_fkey"
        ),
    )
    op.drop_index(
        op.f("ix_project_memberships_is_lead"), table_name="project_memberships"
    )
    op.drop_table("project_memberships")
