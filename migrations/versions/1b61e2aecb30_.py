"""

Revision ID: 1b61e2aecb30
Revises: e40889bed1ba
Create Date: 2019-04-13 20:03:55.206723
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import JSONType

# revision identifiers, used by Alembic.
revision = "1b61e2aecb30"
down_revision = "e40889bed1ba"


def upgrade():
    op.create_table(
        "oauth",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("token", JSONType(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("oauth")
