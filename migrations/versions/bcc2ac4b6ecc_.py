"""

Revision ID: bcc2ac4b6ecc
Revises: 17164a7d1c2e
Create Date: 2017-09-29 20:53:22.786200
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bcc2ac4b6ecc"
down_revision = "17164a7d1c2e"


def upgrade():
    op.add_column(
        "project_uploads",
        sa.Column("form_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.drop_constraint(
        "project_uploads_signature_key", "project_uploads", type_="unique"
    )
    op.drop_column("project_uploads", "signature")


def downgrade():
    op.add_column(
        "project_uploads",
        sa.Column("signature", sa.TEXT(), autoincrement=False, nullable=False),
    )
    op.create_unique_constraint(
        "project_uploads_signature_key", "project_uploads", ["signature"]
    )
    op.drop_column("project_uploads", "form_data")
