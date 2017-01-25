"""

Revision ID: 73d96d3120ff
Revises: 2c9e39e05b87
Create Date: 2017-11-06 18:14:34.532051
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '73d96d3120ff'
down_revision = '2c9e39e05b87'


def upgrade():
    op.alter_column('project_memberships', 'date_joined',
                    new_column_name='joined_at')
    op.drop_column('project_uploads', 'synced_at')
    op.add_column('project_uploads', sa.Column(
        'released_at', sa.DateTime(), nullable=True))
    op.alter_column('project_uploads', 'upload_time',
                    new_column_name='uploaded_at')


def downgrade():
    op.alter_column('project_uploads', 'uploaded_at',
                    new_column_name='upload_time')
    op.add_column('project_uploads',
        sa.Column('synced_at', postgresql.TIMESTAMP(),
                  autoincrement=False, nullable=False))
    op.drop_column('project_uploads', 'released_at')
    op.alter_column('project_memberships', 'joined_at',
                    new_column_name='date_joined')
