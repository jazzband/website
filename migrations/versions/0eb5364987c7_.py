"""
Revision ID: 0eb5364987c7
Revises: cc0e3906ecfb
Create Date: 2016-04-22 20:40:24.233406
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eb5364987c7'
down_revision = 'cc0e3906ecfb'


def upgrade():
    op.create_table('managers',
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )


def downgrade():
    op.drop_table('managers')
