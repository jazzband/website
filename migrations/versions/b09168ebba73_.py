"""
Create provider:user_id index.

Revision ID: b09168ebba73
Revises: 1b61e2aecb30
Create Date: 2019-04-13 20:31:39.824633
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b09168ebba73"
down_revision = "1b61e2aecb30"


def upgrade():
    op.create_index("provider", "oauth", ["user_id"], unique=False)


def downgrade():
    op.drop_index("provider", table_name="oauth")
